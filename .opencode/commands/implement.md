---
description: Implement a new feature using existing project conventions
---

Implement this feature using the relevant global skills.

Use the `repo_map` custom tool to map the repository structure, identify relevant files, and detect existing conventions before writing code. Use `prompt_budget` to estimate context size of files that will be inspected.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/repo_map.py [path]
- python tools/prompt_budget.py --dir <path>

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Before coding:

1. Inspect the repository architecture.
2. Find related features and reusable abstractions.
3. Confirm installed framework and dependency versions.
4. Identify affected APIs, models, schemas, UI, permissions, migrations, and tests.
5. Define the smallest implementation consistent with the existing architecture.

Requirements:

- preserve unrelated behavior
- validate untrusted input
- enforce authentication and authorization
- handle errors and edge cases
- keep transaction boundaries explicit
- avoid duplicate abstractions
- add focused tests
- update documentation where necessary

After implementation run:

- focused tests
- lint
- type checking
- relevant broader tests
- production build when applicable

Report changed files and verification results.

Feature:

$ARGUMENTS