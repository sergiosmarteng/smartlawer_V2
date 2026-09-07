---
description: Audit whether the current task is wasting context and identify improvements
---

Audit the current session context using token-saver and context-engineering skills.

Use the `prompt_budget` custom tool to estimate character and token sizes of files and directories. Use `context_compressor` to identify what would be preserved or lost during compression.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/prompt_budget.py --file <path>
- python tools/prompt_budget.py --dir <path>
- python tools/context_compressor.py --file <path>

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

Identify:

- irrelevant files that were read but not needed
- repeated outputs or redundant explanations
- oversized logs or full-file dumps
- stale assumptions that no longer apply
- missing critical context that should be loaded
- skills loaded but not needed for the current step
- generated or transient files read unnecessarily

For each waste item found, include:

- what was wasted
- estimated impact on context (do not claim exact token counts)
- how to avoid it going forward

Return:

Waste found:
[List of items with impact estimates.]

Missing context:
[Critical information that should be loaded.]

Next minimal reads:
[The smallest set of files or commands needed to fill gaps.]

$ARGUMENTS
