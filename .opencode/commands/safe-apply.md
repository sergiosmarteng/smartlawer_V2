---
description: Apply findings or planned changes safely with per-item verification, priority ordering, and dynamic skill selection
---

Use skill-orchestrator skill to classify each item. Determine the lead skill per item, supporting skills, guardrails, and verbosity before applying.

Apply findings or planned changes safely. When consuming review output, apply each finding's
recommended fix and regression test independently.

Use the `diff_summarizer` custom tool after each change to inspect the resulting diff, classify
per-file risk, and detect affected symbols.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]

Do not skip required code inspection or tests just to save tokens.
Do not summarize away security, schema, migration, or API contract details.

## Input

This command accepts:
- **Review findings** — output from `/review` or `/smart-review` containing items each with a Severity, File, Problem, Impact, Fix, and Test recommendation
- **Discovery recommendations** — output from `/discover` containing items each with a Name, Type, Priority, and Distinct Value
- **Planned changes** — a standalone description of changes to make (scope, files, risks, tests, validation commands, rollback)

When findings or recommendations are provided, treat each as a work item. Sort by priority (Critical → High → Medium → Low / Experimental) and apply in that order.

## Skill selection (per item)

Use skill-orchestrator to classify the item and determine lead, supporting, and guardrail skills.

When skill-orchestrator is unavailable, select the lead skill based on the item's type:

- security issue → `security-review`
- database/model/migration → `sqlalchemy-postgres`
- API/schema/contract → `fastapi-backend`
- UI/frontend → `nextjs-frontend`
- general defect → `testing-and-debugging`
- production/deployment risk → `production-readiness`

Supporting skills and guardrails: add only when the lead skill does not cover a specific area in the item.
Excluded: Reason: form for skills intentionally not used.

## Per-item workflow

For each item (in priority order):

1. Use skill-orchestrator to classify the item and determine lead skill, supporting skills, guardrails, and verbosity
2. Locate the affected file and understand the context
3. Apply the smallest safe fix scoped to this item
4. Run `diff_summarizer` on the resulting diff to inspect what changed
5. Add or update the recommended regression test
6. Run focused verification for this item
7. Report status before moving to the next item

If a fix introduces a new issue, stop and report before proceeding.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Requirements:

- inspect the diff after each change
- consume review findings or discovery recommendations
- sort findings by severity before applying
- select the lead skill per item based on issue type
- apply each finding independently
- add or update focused tests per finding
- run focused verification per finding
- run broader checks after all items pass
- report per-item and overall status

Do not:

- skip diff inspection
- make changes outside the approved scope
- batch findings into one unfocused change
- skip tests to save time
- skip verification steps
- claim success without running the planned validation commands

If verification fails:

- stop and report the failure
- do not apply additional speculative fixes
- identify the root cause before making further changes
- consider rollback steps from the original plan if this came from `/plan`

## Output format

**Input source:** [review findings / discovery recommendations / planned changes]

**Items resolved (in order applied):**

- [Severity/Priority] Title — File:
  Skill plan: Lead: Support: Guardrail: Excluded:
  Fix applied:
  Diff inspected:
  Test added:
  Verification:
  Status: [Pass / Fail]

...

**Skipped items:**

[Items not applied and why.]

**Broader verification:**

[Commands run and results after all items.]

**Status:**

[Pass or Fail with details.]

$ARGUMENTS
