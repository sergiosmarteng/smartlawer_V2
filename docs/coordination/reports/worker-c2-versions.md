# Worker Report — C2 History/Retention/Storage (BL-017/019, issue #25)

## Task

- ID: BL-017 + BL-019 / #25
- Title: [C2] Histórico/retenção/versionamento + storage
- DoD: recuperação de versão anterior funcional.

## Scope

- New `generated_documents` table (migration `20260908_0004`):
  user/document/analysis/template refs, `file_path`, monotonic `version`
  (unique per analysis), per-row `created_at`.
- Every generate (both DOCX routes) persists a versioned copy under managed
  `uploads/generated/{document_id}/` (compose bind-mount → survives
  recreation) + retention trim to `GENERATED_KEEP_LATEST` (default 10;
  Settings + compose + `.env.example`). Persistence never fails downloads.
- Endpoints: `GET /analysis/{id}/versions` (newest first),
  `GET /analysis/{id}/versions/{version}` (recovery download).
- Frontend: "Previous versions" picker on the analysis page (auto-refresh
  after each download).

## Files Changed

- `backend/app/models/generated_document.py` — NEW; wired in `models/__init__.py`.
- `backend/alembic/versions/20260908_0004_generated_documents.py` — NEW.
- `backend/app/core/config.py` — `GENERATED_KEEP_LATEST`.
- `backend/app/api/routes/versions.py` — NEW list/download (tenant-checked).
- `backend/app/main.py` — router registered (`/api/v1`).
- `backend/app/api/routes/templates.py` — `_persist_generation` + retention;
  `_build_docx_file_response` serves the managed copy.
- `backend/app/schemas/workflow.py` — `GeneratedVersionResponse`.
- `docker-compose.yml`, `.env.example` — new env key.
- `backend/tests/test_versions.py` — NEW (5 tests); conftest model import.
- `src/types/workflow.ts` + `src/pages/analysis/[id].tsx` — versions UI.

## Decisions

- Decision: new migration (single-session now; no parallel Session C active).
- Reason: history needs a real table; chain verified offline + live.
- Decision: retention enforced synchronously post-generate, best-effort.
- Reason: no scheduler infra for MVP; never blocks the download.
- Decision: template DELETE/detail still deferred (C1 carry-over).

## Validation

- `pytest backend/tests` → **81 passed** (76 + 5), no regressions.
- `tsc` clean, targeted `next lint` clean (one exhaustive-deps warning fixed).
- WSL live: migration auto-applied on api restart (head `20260908_0004`);
  flow 7/7 (3 generates → versions [3,2,1], v1 recovery bytes-valid,
  cross-user 404); managed files confirmed on host bind mount;
  B2 smoke re-passed **10/10**.

## Handoff Notes

- Retention live-covered only at default KEEP=10 (trim path proven in
  sqlite test with KEEP=2).
- Same import-time `datetime.now()` latent bug remains in
  analysis/document/document_chunk/user models (ordering ties).
- Commit: local only, no push (per implementation-plan rule 6).
