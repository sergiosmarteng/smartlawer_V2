---
description: Review the requested code without modifying it
---

Review the requested code using the relevant global skills.

Use the `diff_summarizer` custom tool to summarize git diffs with per-file risk classification, symbol detection, and skill/test suggestions.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

Inspect related files, callers, tests, schemas, models, migrations, and API consumers before reporting findings.

Focus on:

- correctness
- security
- authorization
- transaction safety
- async and concurrency issues
- edge cases
- API compatibility
- performance
- missing regression tests

Report only evidence-based findings.

For each finding include:

1. Severity
2. File and location
3. Problem
4. Realistic impact
5. Smallest safe fix
6. Regression-test recommendation

Do not edit files.
Do not report formatting or personal style preferences.

Target:

$ARGUMENTS