---
description: Fix a confirmed defect and add regression coverage
---

Fix the requested issue using the relevant global skills.

Use the `diff_summarizer` custom tool to examine the diff of changes, classify per-file risk, and detect affected symbols.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Workflow:

1. Inspect the relevant execution path.
2. Reproduce the failure when possible.
3. Confirm the root cause with evidence.
4. Add or update a focused regression test.
5. Apply the smallest safe fix.
6. Run the focused test.
7. Run relevant lint, type, and broader tests.

Do not:

- rewrite unrelated code
- weaken validation or typing
- hide errors with broad exception handling
- add arbitrary sleeps
- add retries without checking idempotency
- claim success without verification

At the end report:

- root cause
- files changed
- fix applied
- regression test
- commands run
- remaining limitations

Issue:

$ARGUMENTS