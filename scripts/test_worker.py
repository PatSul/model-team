#!/usr/bin/env python3
"""Offline boundary and subprocess checks: python3 scripts/test_worker.py"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import tempfile
import time
from unittest.mock import patch

import worker
from report import summarize


def check():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        repo = root / "repo"
        repo.mkdir()
        source = repo / "file with spaces.py"
        source.write_text("def value():\n    return 42\n")
        task = root / "task.md"
        task.write_text("What does value return?")
        diff = root / "change.patch"
        diff.write_text("--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")
        args = argparse.Namespace(role="explore", risk="normal", worker="auto", model=None,
                                  repo=str(repo), task_file=str(task), files=[source.name],
                                  reference=None, diff=None, max_bytes=200000, timeout=5,
                                  budget_usd=2, dry_run=False, out=str(root / "run-ok"))
        assert worker.route("explore", "normal") == "deepseek"
        assert worker.route("draft", "high") == "opus"
        assert worker.route("review", "normal") == "sonnet"
        assert worker.route("challenge", "low") == "opus"
        assert worker.route("review", "normal", "opus") == "opus"
        prompt, provenance = worker.packet(args)
        assert "return 42" in prompt and provenance[0]["path"] == source.name
        draft_args = argparse.Namespace(**(vars(args) | {"role": "draft", "reference": source.name}))
        draft = json.loads(worker.packet(draft_args)[0].split("INPUT JSON:\n", 1)[1])
        assert draft["reference"] == source.name and len(draft["files"]) == 1
        original_hash = provenance[0]["sha256"]
        source.write_text("def value():\n    return 43\n")
        assert worker.packet(args)[1][0]["sha256"] != original_hash

        def rejects(**changes):
            candidate = argparse.Namespace(**(vars(args) | changes))
            try:
                worker.packet(candidate)
            except (ValueError, OSError):
                return
            raise AssertionError(f"Should reject: {changes}")

        rejects(max_bytes=3)
        rejects(role="draft")
        rejects(role="review")
        rejects(files=["../task.md"])
        (repo / "link.py").symlink_to(task)
        rejects(files=["link.py"])
        (repo / ".env").write_text("SAMPLE=value")
        rejects(files=[".env"])
        (repo / "key.txt").write_text("-----BEGIN PRIVATE KEY-----\nnot a real key")
        rejects(files=["key.txt"])
        (repo / "binary").write_bytes(b"a\x00b")
        rejects(files=["binary"])

        review = {"findings": [], "missing_context": ["Caller unavailable"]}
        success = {"is_error": False, "subtype": "success", "result": json.dumps(review)}
        assert worker.parse_result(json.dumps(success), "review")[0] == json.dumps(review)
        for bad in ({"is_error": True}, {"result": ""}, {"result": "no findings"},
                    {"result": '{"findings": []}'}):
            try:
                worker.parse_result(json.dumps(success | bad), "review")
            except ValueError:
                continue
            raise AssertionError("Invalid worker result accepted")

        fake = root / "fake-cli"
        fake.write_text("#!/usr/bin/env python3\nimport json,sys\nprompt=sys.stdin.read()\n"
                        "assert '--safe-mode' in sys.argv\n"
                        "assert sys.argv[sys.argv.index('--tools')+1] == ''\n"
                        "assert 'return 43' in prompt\n"
                        "print(json.dumps({'is_error': False, 'subtype':'success', 'result':'43',"
                        "'total_cost_usd':0.01,'modelUsage':{'fake':{'costBasis':'list'}},'usage':{'input_tokens':100,'output_tokens':2,"
                        "'cache_read_input_tokens':0,'cache_creation_input_tokens':0}}))\n")
        fake.chmod(0o700)
        with patch.object(worker.shutil, "which", return_value=str(fake)), contextlib.redirect_stdout(io.StringIO()):
            assert worker.execute(args) == 0
            assert (Path(args.out) / "response.txt").read_text() == "43\n"
            assert Path(args.out).stat().st_mode & 0o777 == 0o700
            try:
                worker.execute(args)
            except FileExistsError:
                pass
            else:
                raise AssertionError("Overwrote previous run")
            fake.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n")
            args.out, args.timeout = str(root / "run-timeout"), 0.05
            assert worker.execute(args) == 1
            assert json.loads((Path(args.out) / "run.json").read_text())["status"] == "timeout"
            child_pid = root / "child.pid"
            fake.write_text("#!/usr/bin/env python3\nimport subprocess,sys,time\nfrom pathlib import Path\n"
                            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(15)'],start_new_session=True)\n"
                            f"Path({str(child_pid)!r}).write_text(str(child.pid))\n"
                            "time.sleep(10)\n")
            args.out, args.timeout = str(root / "run-detached"), 0.3
            started = time.monotonic()
            try:
                assert worker.execute(args) == 1
                assert time.monotonic() - started < 3
                assert child_pid.exists(), "Detached pipe regression case was not exercised"
            finally:
                if child_pid.exists():
                    try:
                        os.kill(int(child_pid.read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            fake.write_text("#!/usr/bin/env python3\nprint('not json')\n")
            args.out, args.timeout = str(root / "run-invalid"), 5
            assert worker.execute(args) == 1
            assert not (Path(args.out) / "response.txt").exists()
        with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "synthetic-test-value"}):
            assert "AWS_SECRET_ACCESS_KEY" not in worker.environment("opus")
        report = summarize(root)
        assert report["worker_runs"] == 4 and report["runs_with_unknown_cost"] == 3
        assert report["known_reported_cost_usd"] == 0.01
        assert report["known_usage_tokens"]["input_tokens"] == 100
        record = root / "run-ok" / "run.json"
        unpriced = json.loads(record.read_text())
        unpriced["reported_model_usage"]["fake"]["costBasis"] = "unknown"
        record.write_text(json.dumps(unpriced))
        report = summarize(root)
        assert report["known_reported_cost_usd"] == 0 and report["runs_with_unknown_cost"] == 4
    print("All offline checks passed")


if __name__ == "__main__":
    check()
