---
description: Create a compact implementation plan before editing code
---

Create a compact implementation plan using the repository-navigation skill and relevant stack-specific skills.

Use the `repo_map` custom tool to generate a compact map of the repository structure, detect languages and frameworks, and identify relevant directories. Use `prompt_budget` to estimate context size of files that may need inspection.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/repo_map.py [path]
- python tools/prompt_budget.py --dir <path>

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Before writing any code, inspect:

- the entry point and related files
- existing similar features for patterns
- relevant models, schemas, routes, services, and tests

Include in the plan:

- scope: what will and will not be changed
- files likely affected
- risks: what could go wrong
- tests: what test files will be added or updated
- validation commands: exact commands to run after implementation
- rollback considerations: how to revert if the change fails
- migration considerations if applicable

Do not start editing until the plan is approved.

Return:

Plan:

Scope:
[What will change and what will not.]

Files likely affected:
[Path — reason.]

Risks:
[What could break and how to mitigate.]

Tests:
[Test files to add or update.]

Validation:
[Exact commands to run after implementation.]

Rollback:
[How to revert if needed.]
$ARGUMENTS
