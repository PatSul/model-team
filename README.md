# Model Team

A local Codex plugin for collaborating with Claude and DeepSeek. The existing
Codex task is the harness: no separate app or server is required for this version.

| Responsibility | Default |
| --- | --- |
| Own requirements, edits, tests, final decisions | Current Codex model |
| Bulk source reading and predictable generation | Existing `deepseek` CLI, V4 Flash |
| Ordinary independent review | `claude --model sonnet` |
| Design challenge and high-risk reasoning/review | `claude --model opus` |

Defaults are editable at invocation with `--worker` and `--model`; they are a
practical starting policy, not benchmark rankings. Your current Codex model stays
unchanged. DeepSeek is optional: use `--worker sonnet` for those jobs instead.
Only use a provider for code it is authorized to receive.

For substantial work: understand → challenge the plan when useful → implement and
test → independent review → verify findings → at most two correction/review passes.
The lead records unresolved dissent and never treats missing review as approval.
Workers receive explicit snapshots and return artifacts; Codex applies changes.

## Use this source package

Read `skills/model-team/SKILL.md` in a Codex task and ask:

> Use Model Team to implement this change, with Claude challenging the plan and
> independently reviewing the result. Use DeepSeek only for routine bulk work.

For an unpacked package that is not installed, give Codex the absolute path to
that SKILL.md. For persistent discovery, register the package with your personal
Codex plugin marketplace using the plugin-creator installation workflow. This
deliverable does not modify your installed plugins or global settings.

Python 3.10+ is the only runtime dependency. Each selected worker CLI must already
be installed and authenticated. This machine's `deepseek` wrapper obtains its own
key from macOS Keychain; the plugin never extracts it. Other DeepSeek installations
need a Claude Code-compatible `deepseek` wrapper accepting the same flags.

```bash
python3 scripts/worker.py --help
python3 scripts/test_worker.py
python3 scripts/report.py /absolute/path/to/task/work
```

Calls have input, timeout, and CLI budget settings. Source hashes, model reports,
token counters, durations, and status are saved in new private run directories.
The usage report counts only workers. It excludes unknown model pricing rather
than treating a CLI's fallback price as accurate, and does not include the host
Codex session. Dollar estimates are not authoritative bills or subscription usage.

## What this implements

The [Spotify article](https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90)
motivates cheaper bulk work while preserving frontier reasoning. This plugin adds
independent challenges, bounded reviews, and evidence-based adjudication.

The [Sharbel A. video](https://www.youtube.com/watch?v=kHtOSJRUkLs) motivates
measuring context and delegation overhead. Its published description includes a
report-only setup audit. We adopted per-call usage records and aggregate reporting;
we did not run that global configuration audit or change your scheduled jobs.

This release uses skill-directed routing. It does not install Spotify-style
large-read blocking hooks or a mandatory completion gate. Those would require
tested coverage of the host's tools and exceptions for targeted reads. The review
loop limit is skill guidance; per-call input/time limits are implemented in code.
There is no promise of 90% savings or unlimited usage. CLI tool restrictions are
not an OS sandbox. Common secret-file checks are not a complete secret scanner.

A separate app becomes useful if you need durable unattended queues, shared
budgets enforced across tasks, or a live multi-run dashboard. None is necessary
to use the collaboration workflow above.

See [Claude cost guidance](https://code.claude.com/docs/en/costs),
[prompt caching](https://code.claude.com/docs/en/prompt-caching), and
[cost telemetry limitations](https://code.claude.com/docs/en/agent-sdk/cost-tracking)
for provider-specific details. In current Claude documentation, model switches
invalidate that model's cache; changing effort alone does not.

The [RoboNuggets Agentic OS video](https://www.youtube.com/watch?v=8NSyI-npJCU)
provides a useful four-part organization: skills, memory, routines, and apps.
Here, the main skill is kept compact with invocation details in a reference;
task memory stores decisions and evidence pointers; the development routine is
bounded; and the existing Codex interface displays artifacts. This is an
adaptation of the video's framework, not adoption of a new platform or an
industry certification. No extra scheduler, cloud agent, or memory database is
required for these additions.
