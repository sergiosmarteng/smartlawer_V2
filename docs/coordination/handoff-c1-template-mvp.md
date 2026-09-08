# Handoff — C1 Template Management MVP (BL-015, issue #24) — for parallel session

> Ownership split with Session B (see worker-b1-env.md): Session B owns
> `docker-compose.yml`, `.env*`, `backend/Dockerfile`, alembic migrations,
> `integration-log.md` merges and the B4 identifier decision. Session C owns
> the files below. Do not touch B-owned files without explicit ack.

## Goal

Real DOCX template upload, listing, selection, and placeholder validation
instead of relying only on `backend/templates/base_template.docx`.
PRD: §"Upload e processamento de templates DOCX" + "Geração automatizada
de defesas" (upload, placeholder discovery, keep formatting, fill + export).

## Starting state (verified 2026-09-08)

- `backend/app/models/template.py` — `Template` table EXISTS and is migrated
  (`templates`: user-scoped `name`, `file_path`, `placeholders` JSONB).
  No new migration expected; if you need schema changes, STOP and
  coordinate with Session B (single migration owner).
- `backend/app/api/routes/templates.py` — only
  `GET /api/v1/templates/{analysis_id}/generate`, hardcoded to
  `BASE_TEMPLATE_PATH`. No upload/list/select/validate endpoints yet.
- `backend/app/core/doc_generator.py` — `DocxGenerator.generate_defense`
  with normalization layer (see worker-bl-007-docx-flow.md); keep template
  placeholder expansion inside the normalization layer.
- Frontend `src/` — NO template UI exists yet (nothing references
  "template"). New screens needed (list + upload + select on analysis page).
- Identifier assumption is UNDECIDED (B4/BL-014, Session B owns it):
  `_get_owned_analysis` currently accepts analysis_id OR document_id.
  C1 must preserve that dual behavior and must NOT change identifier
  semantics. If B4 resolves mid-flight, Session B will notify.

## Suggested build order

1. Backend: `POST /api/v1/templates` (upload DOCX, persist file, extract +
   store `placeholders`), `GET /api/v1/templates` (own templates),
   placeholder validation with actionable errors (which `{{keys}}` are
   missing/unsupported vs. the analysis payload keys).
2. Wire selection into generation: `GET .../generate?template_id=` defaulting
   to `base_template.docx` (never break the default path — BL-013/B2 smoke
   depends on it).
3. Frontend: template list + upload + per-analysis selection.
4. Tests: route-level (follow `backend/tests/test_documents.py` patterns,
   sqlite harness in `conftest.py`); keep `pytest backend/tests -q` green.

## Definition of done

- User can upload a DOCX template, list own templates, select one for
  generation, and gets a clear error naming incompatible placeholders
  BEFORE generation fails opaquely.
- Default `base_template.docx` path still works (B2 smoke guard).
- `docs/coordination/api-contract.md` updated IFF routes change (needs
  Session B ack — it owns contract snapshot consistency during Onda B).
- Report per `reports/TEMPLATE.md` + local commit (no push without user ask).

## Validation note

Integrated runtime is Session B's deliverable (B1). Build against the
sqlite route harness; run live validation (upload → select → DOCX download
in compose) only after B1 reports the environment healthy.
