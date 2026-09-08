# Worker Report — C1 Template Management MVP (BL-015, issue #24)

## Task

- ID: BL-015 / #24
- Title: [C1] Template management MVP

## Scope

- Backend: `POST /api/v1/templates` (upload), `GET /api/v1/templates`
  (list own, newest first), `?template_id=` on both DOCX generate routes
  with ownership check + pre-render placeholder validation.
- Discovery: `DocxGenerator.discover_placeholders()` — pure stdlib
  (zipfile + regex over all `word/*.xml` parts, split-`<w:t>`-run aware,
  loop/set targets + filters + Jinja keywords/tests excluded).
- Frontend: template picker section on the analysis page (dropdown +
  `.docx` upload + incompatibility surfacing); default path untouched.
- Tests: `backend/tests/test_templates.py` (11 new: discovery units,
  upload/list/generate/422/404-cross-user).

## Files Changed

- `backend/app/core/doc_generator.py` — `SUPPORTED_CONTEXT_KEYS`,
  `discover_placeholders`, `unsupported_placeholders` (+ regex helpers).
- `backend/app/schemas/template.py` — NEW `TemplateResponse`
  (`unsupportedPlaceholders` camel alias).
- `backend/app/api/routes/templates.py` — upload/list endpoints,
  `template_id` on `/{analysis_id}/generate` (B4 dual-lookup preserved).
- `backend/app/api/routes/workflow.py` — forwards `template_id` on the
  canonical `/analysis/{id}/docx`.
- `backend/app/models/template.py` — one-line fix: `created_at` default
  was import-time `datetime.now()` (all rows identical); now per-row.
- `src/types/workflow.ts` — `UserTemplate`,
  `TemplateIncompatibilityDetail`.
- `src/pages/analysis/[id].tsx` — template picker + upload + 422 display.

## Decisions

- Decision: stdlib discovery instead of python-docx (which IS installed).
- Reason: identical behavior in Windows sqlite tests and the container,
  zero new dependencies; validated exact against tricky inputs.
- Decision: upload ACCEPTS incompatible templates, generate REJECTS (422).
- Reason: DoD wants the error named BEFORE opaque failure; warning at
  upload time + enforcement at generate time covers both.
- Decision: no new migration (Template table already migrated; Python-side
  default change needs no DDL).
- Decision: no template DELETE/detail endpoints (MVP minimum per handoff).

## Validation

- `pytest backend/tests` → **76 passed** (65 before + 11 new), no regressions.
- `npx tsc --noEmit` clean; targeted `next lint` clean on both changed files.
- WSL live (rule 7): C1 script 12/12 — upload good/bad, list isolation +
  newest-first, custom-template render (real 1599B DOCX), 422 naming
  `{{numero_processo}}`, default + legacy routes byte-intact.
- B2 smoke re-ran **10/10** after all backend changes (default-path guard).

## Handoff Notes

- Live C1 script lives in Temp (`sl_c1.py`); key flows are covered by
  `test_templates.py` for CI.
- Follow-up (out of scope, pre-existing): same import-time
  `datetime.now()` default in `analysis/document/document_chunk/user`
  models — dashboard/process ordering can tie; one-line fix each when
  convenient.
- Commit: local only, no push (per implementation-plan rule 6).
