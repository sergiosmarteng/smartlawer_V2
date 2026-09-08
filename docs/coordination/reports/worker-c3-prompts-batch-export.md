# Worker Report — C3 Prompts/Batch/Exports (BL-020/021/022, issue #26)

## Task

- ID: BL-020 + BL-021 + BL-022 / #26
- Title: [C3] Prompts customizáveis + lote + exports
- DoD: cada capability com teste.

## Scope

- Prompt profiles: `prompt_profiles` (migration `20260908_0005`),
  CRUD-lite (`POST`/`GET`/`PATCH /{id}/default`/`DELETE /{id}`),
  default guidance prepended to the analyzer prompt via
  `build_prompt_text()`; worker loads the owner's default profile.
  No-profile path is byte-identical to the legacy prompt.
- Batch: `POST /api/v1/documents/batch-upload` (≤10 PDFs, per-file
  tolerance → `{items, errors}`); each item queues its own pipeline and
  is monitored via dashboard/tasks; upload page supports multi-select
  and follows the first item through the existing polling machine.
- Exports: `GET /api/v1/analysis/{id}/summary.md` (Markdown download:
  summary/requests/laws/evidence/theses) + "Summary (.md)" button.
- Frontend: `/prompts` manager page (nav + middleware protection).

## Files Changed

- Backend: `models/prompt_profile.py` (NEW), migration `0005` (NEW),
  `core/ai_engine.py` (`BASE_INSTRUCTIONS`, `build_prompt_text`,
  `analyze_petition(..., strategy_prompt)`), `crud/prompt.py` (NEW),
  `tasks/document_tasks.py` (default-profile wiring),
  `schemas/prompt.py` (NEW), `api/routes/prompts.py` (NEW),
  `api/routes/documents.py` (`_store_and_queue` refactor + batch),
  `api/routes/workflow.py` (`summary.md`), `schemas/workflow.py`
  (`BatchUpload*`), `main.py` (router), `tests/conftest.py` (import).
- `backend/tests/test_prompts_batch_export.py` — NEW (11 tests).
- `backend/tests/test_docling_extraction.py` — stub updated to the new
  `analyze_petition` signature (same intent, records strategy kwarg).
- Frontend: `upload.tsx` (batch), `analysis/[id].tsx` (summary button),
  `pages/prompts.tsx` (NEW), `Header.tsx` (nav), `middleware.ts`
  (protection), `types/workflow.ts` (3 types).

## Decisions

- Decision: guidance as prepended text, not template surgery.
- Reason: zero regression surface on the default path (verified
  byte-identical); observable via unit test without AI keys.
- Decision: batch tolerance with 200 + `{items, errors}` (not 207).
- Reason: simpler frontend contract; per-file states stay explicit.
- Decision: full tiny CRUD for profiles (incl. delete).
- Reason: a profile without delete is a dead-end UX.

## Validation

- `pytest backend/tests` → **92 passed** (81 + 11), no regressions
  (one docling-stub signature update, intent preserved).
- `tsc` clean, targeted `next lint` clean.
- WSL live: migration auto-applied (head `20260908_0005`); flow 7/7
  (CRUD, default switch, delete 204, batch 2/2 COMPLETED, summary.md
  content-checked); B2 smoke re-passed **10/10**.

## Handoff Notes

- Worker profile wiring is live-proven implicitly (batch docs COMPLETED
  through the wired path with no default profile → legacy prompt).
- Frontend batch follows the first item; the rest via dashboard.
- Commit: local only, no push (per implementation-plan rule 6).
