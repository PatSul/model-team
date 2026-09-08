# Worker invocation and reporting

Paths below are relative to the plugin root unless shown as absolute.


Write the task and any patch under the current task's `work/` directory. Choose a
fresh artifact directory for every call; existing outputs are never overwritten.
Paths in `--files` and `--reference` are relative to `--repo`. Task/diff files can
be outside the repo. Use a trusted output location outside the source repo when
available; exclude artifacts from later diffs otherwise.

```bash
python3 /absolute/plugin/path/scripts/worker.py explore \
  --repo /absolute/repo --task-file /absolute/task/work/question.md \
  --files src/service.py src/handler.py --out /absolute/task/work/read-01

python3 /absolute/plugin/path/scripts/worker.py draft \
  --repo /absolute/repo --task-file /absolute/task/work/spec.md \
  --reference tests/test_orders.py --files src/users.py \
  --out /absolute/task/work/draft-01

python3 /absolute/plugin/path/scripts/worker.py review --risk high \
  --repo /absolute/repo --task-file /absolute/task/work/requirements-and-tests.md \
  --diff /absolute/task/work/change.patch --files src/service.py tests/test_service.py \
  --out /absolute/task/work/review-01
```

`challenge` uses the same task/file arguments without a required diff. Use
`--dry-run` to validate inputs and inspect the exact file manifest with no model
call. The default ceiling is 200,000 UTF-8 request bytes, 240 seconds, an 8,192
output-token setting, and a $2 CLI budget per call. The dollar and token settings
depend on provider/CLI enforcement and aren't a guaranteed billing ceiling.
Large requests fail without truncation; split by coherent component and preserve
cross-component contracts. Explicit overrides are available for measured needs.

The runner prints only status and artifact paths. Read `response.txt` for
exploration/drafts or `review.json` for critiques. `run.json` records source hashes,
requested model, provider-reported model usage/cost, elapsed time, and outcome.
Model reports are telemetry, not independent proof of the serving model. Check
actual model reports for unexpected routing. Do not use failed artifacts as results.

After a substantial task, run `scripts/report.py /absolute/task/work` from the plugin root to
aggregate worker usage, costs and failed calls. The report excludes the main
Codex session; combine it with host telemetry when available and mark it unknown
otherwise. A smaller host context alone does not establish savings. Delegate only
when avoided bulk work or an independent quality check justifies worker overhead.
Keep each worker's model stable during its call; routing separate workers avoids
switching the model of the long-lived lead conversation.

Workers receive only the supplied snapshot in their prompt, have built-in tools
disabled, empty MCP configuration, safe mode, and no saved conversation. They run
from a new private artifact directory, using existing CLI authentication. These
are CLI controls, not an OS sandbox. The helper doesn't read, display, or store
API key values. Explicit source selection and common credential-file rejection
reduce accidental disclosure; they are not a complete secret scanner.

This version offers skill-directed routing and bounded worker calls. It has no
host-wide read-blocking hook, automatic cost comparison, background scheduler, or
mandatory stop gate. Do not describe it as Spotify's enforced shunt or promise
90% savings. Add those only for a demonstrated need, with host tool coverage and
targeted-read exceptions tested first.
