---
description: Review code with one lead review skill and only necessary supporting skills to reduce overlap and verbosity.
---

Use skill-orchestrator skill first. Determine the review type from the target and produce a review plan, then perform the review.

Use the `diff_summarizer` custom tool to summarize git diffs with per-file risk classification, symbol detection, and skill/test suggestions.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/diff_summarizer.py [--file <path> or --stdin]

## Review Type Determination

Analyze the target and determine the review type:

- `general` — mixed changes, multiple layers
- `security` — touches auth, authorization, user input, file upload, secrets, PII, external APIs, or AI/LLM output
- `production` — touches deployment, release, configuration, migrations, or infrastructure
- `database` — touches models, queries, migrations, or connection configuration
- `frontend` — touches UI components, pages, or user-facing behavior
- `api` — touches routes, schemas, or service contracts

## Skill Selection

Select exactly one lead skill:

| Review Type | Lead Skill |
|-------------|------------|
| general | `code-review` |
| security | `security-review` |
| production | `production-readiness` |
| database | `code-review` with `sqlalchemy-postgres` as support |
| frontend | `code-review` with `nextjs-frontend` as support |
| api | `code-review` with `fastapi-backend` as support |

Use support skills only for files actually touched. Do not run full security review unless security-sensitive areas are involved. Do not run production-readiness review unless deployment, release, config, or migration behavior is involved.

## Finding Rules

Report only:
- confirmed defect
- realistic risk
- missing test for changed behavior
- compatibility break
- security issue
- production blocker

Do not report style-only issues. Keep output compact.

## Output Format

**Review mode:** [general / security / production / database / frontend / api]
**Lead skill:** [name]
**Supporting skills:** [names or none]
**Excluded skills:** [names]

**Findings:**
- [Severity] Title
  Location:
  Evidence:
  Impact:
  Fix:
  Test:
- [Severity] Title
  ...

**Not reviewed:**
[Areas intentionally excluded and why.]

**Verification:**
[Commands or checks to confirm fixes.]

Target:
$ARGUMENTS
