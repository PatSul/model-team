#!/usr/bin/env python3
"""Summarize worker telemetry; excludes the host Codex session and actual billing."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path


def summarize(root):
    statuses, totals = Counter(), Counter()
    cost, unknown_cost, unknown_usage, invalid = 0.0, 0, 0, 0
    for path in Path(root).rglob("run.json"):
        try:
            run = json.loads(path.read_text())
            if not isinstance(run, dict) or run.get("contract_version") != 1:
                raise ValueError("Not a Model Team run")
            status = run.get("status")
            if not isinstance(status, str):
                raise ValueError("Missing status")
        except (OSError, ValueError):
            invalid += 1
            continue
        statuses[status] += 1
        value = run.get("reported_cost_usd")
        models = run.get("reported_model_usage")
        known_basis = (isinstance(models, dict) and bool(models)
                       and all(isinstance(m, dict) and m.get("costBasis") == "list" for m in models.values()))
        if known_basis and type(value) in (int, float) and math.isfinite(value) and value >= 0:
            cost += value
        else:
            unknown_cost += 1
        usage = run.get("usage")
        keys = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        if isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in keys):
            totals.update({k: usage[k] for k in keys})
        else:
            unknown_usage += 1
    return {"worker_runs": sum(statuses.values()), "statuses": dict(statuses),
            "known_reported_cost_usd": round(cost, 6), "runs_with_unknown_cost": unknown_cost,
            "known_usage_tokens": dict(totals), "runs_with_unknown_usage": unknown_usage,
            "unreadable_or_unrecognized_records": invalid,
            "scope": "Worker telemetry only. CLI cost estimates may differ from billing. Host usage excluded. No savings baseline measured."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory containing this task's worker runs")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error("root must be an existing directory")
    print(json.dumps(summarize(args.root), indent=2))
