---
description: Create a handoff summary for continuing in a new OpenCode session
---

Create a handoff summary using context-engineering skill so a new session can continue without reading prior conversation.

Use the `context_compressor` custom tool to compress session logs, errors, and file paths while preserving exact errors, commands, and verification status. Use `prompt_budget` to estimate context size of files that need to be described.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/context_compressor.py --file <path>
- python tools/prompt_budget.py --dir <path>

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.
Do not claim exact token counts — use estimates only.

Include:

- goal
- current state of the work
- files changed and their paths
- important facts discovered
- commands run and results
- test results and verification status
- next steps in priority order
- warnings and remaining risks
- any environment or configuration requirements

Do not:
- omit commands that need to be re-run
- assume the next session has prior knowledge
- leave unresolved questions undocumented

Return:

Handoff summary:

Goal:
[Single sentence.]

Current state:
[What has been done and what remains.]

Files changed:
[Path — one-line change summary.]

Important facts:
[Key findings, decisions, error messages, configuration.]

Commands run:
[Command — exit status — summary of output.]

Test results:
[What passed, what failed, what is untested.]

Next steps:
[Ordered list with the first step to take.]

Warnings:
[Anything that could cause failure or confusion.]

$ARGUMENTS
