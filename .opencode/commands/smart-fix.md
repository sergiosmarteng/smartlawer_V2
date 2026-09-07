---
description: Fix a bug using the minimum necessary skills, focused verification, and overlap-controlled output.
---

Use skill-orchestrator skill to classify the task. Determine the lead skill, supporting skills, guardrails, and verbosity before fixing.

Use the `diff_summarizer` custom tool to summarize the diff of changes, classify per-file risk, and detect affected symbols.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]

## Skill Selection

Lead skill: `testing-and-debugging`.

Add a stack-specific supporting skill based on files touched:
- `fastapi-backend` — route handlers, DI, auth dependencies
- `sqlalchemy-postgres` — models, queries, sessions, migrations
- `nextjs-frontend` — server/client components, data fetching, caching

Add `security-review` as guardrail only when the bug involves:
- authentication
- authorization
- secrets
- file upload
- SQL
- shell commands
- external URLs
- user or tenant data

Add `production-readiness` as guardrail only when the fix changes:
- deployment
- configuration
- migrations
- background jobs
- observability
- resource limits

## Rules

- Do not rewrite unrelated code.
- Do not output full checklists.
- Add or update focused regression tests.
- Run focused verification first.
- Broader checks only if relevant.

## Output Format

**Skill plan:**
- Lead skill: testing-and-debugging
- Supporting skills: [names or none]
- Guardrail skills: [names or none]
- Skills intentionally not used: [names]
- Verbosity: concise

**Root cause:**
[What caused the defect, with evidence.]

**Fix:**
[Smallest safe change applied.]

**Files changed:**
[Path — summary of change.]

**Regression test:**
[Test file and what it covers.]

**Verification:**
[Commands run and their results.]

**Skipped broader checks:**
[What was intentionally skipped and why.]

**Remaining risk:**
[What could still go wrong.]

$ARGUMENTS
