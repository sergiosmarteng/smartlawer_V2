---
description: Compress the current session context into a concise but complete working summary
---

Compress the current session context using token-saver and context-engineering skills.

Use the `context_compressor` custom tool to compress logs, errors, file paths, and commands while preserving exact errors and verification status. Use `prompt_budget` to estimate token counts before and after compression.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/context_compressor.py --file <path>
- python tools/prompt_budget.py --file <path>

Preserve exactly:

- task goal
- constraints and assumptions
- exact error messages and stack frames
- files changed and their paths
- files inspected and summaries
- commands run and their exit status
- decisions made and rejected alternatives
- verification status
- remaining risks and open questions
- next action

Do not invent information.
Do not keep exploration that led nowhere.
Do not keep redundant or repeated content.
Do not remove exact error messages, file paths, or commands.
Do not claim exact token counts — use estimates only.

Remove or summarize:

- repeated log patterns
- irrelevant exploration branches
- framework-internal stack frames
- verbose explanations of decisions
- information that has been superseded

Return:

Context:
[Compressed summary covering all preserved fields above.]

Next action:
[Single next step.]

$ARGUMENTS
