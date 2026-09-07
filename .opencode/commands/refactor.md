---
description: Refactor existing code while preserving observable behavior
---

Refactor the specified feature using code-review, testing-and-debugging, and relevant stack-specific skills.

Use the `repo_map` custom tool to understand the repository structure and locate relevant files. Use `diff_summarizer` to inspect the diff after changes, classify per-file risk, and detect affected symbols.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/repo_map.py [path]
- python tools/diff_summarizer.py [--file <path> or --stdin]

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Goals:

- improve clarity
- remove proven duplication
- improve testability
- improve structure
- preserve public behavior

Before changing code:

1. Inspect all callers and consumers.
2. Identify the current public contract.
3. Add or confirm characterization tests.
4. Identify risks involving API responses, transactions, permissions, and state.

Constraints:

- do not change API contracts unless explicitly requested
- do not change database behavior unintentionally
- do not introduce unnecessary dependencies
- do not rewrite unrelated modules
- keep the patch reviewable

Run focused tests after meaningful steps and broader checks at completion.

Target:

$ARGUMENTS