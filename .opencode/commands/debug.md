---
description: Investigate and identify the root cause of a bug
---

Investigate this bug using testing-and-debugging skill and the relevant stack-specific skills.

Use the `diff_summarizer` custom tool to examine recent diffs, classify per-file risk, and detect affected symbols. Use `repo_map` to navigate the repository and find relevant files.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]
- python tools/repo_map.py [path]

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Do not modify code until sufficient evidence identifies the likely root cause.

Trace:

- entry point
- callers
- state transitions
- database operations
- async operations
- external services
- frontend consumers
- relevant tests

Separate:

- symptom
- trigger
- root cause
- contributing conditions

Return:

1. Confirmed root cause or clearly labeled hypotheses
2. Evidence
3. Exact failing path
4. Affected files
5. Smallest safe fix
6. Regression-test plan

Bug:

$ARGUMENTS