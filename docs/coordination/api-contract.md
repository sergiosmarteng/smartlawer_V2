# SmartLawer V2 API Contract Snapshot

Last updated: 2026-05-12
Purpose: capture the current workspace contract between frontend routes and backend API routes for the stabilization effort.

## Current Workflow Summary

- Auth is centered on backend JWT login and `GET /users/me`.
- Private frontend routes are guarded by Next middleware plus `AuthGuard`.
- Upload uses `POST /documents/upload` and polls `GET /tasks/{document_id}`.
- Dashboard reads `GET /processes`.
- Analysis detail reads `GET /analysis/{analysis_id}` and downloads DOCX from `GET /analysis/{analysis_id}/docx`.
- Backend analysis and DOCX routes currently accept either `analysis_id` or the originating `document_id`.
- Legacy DOCX compatibility still exists at `GET /templates/{analysis_id}/generate`.
- The active ingestion worker uses Docling markdown when `DOCLING_ENABLED=1`, else raw text, and persists both.
- `process_pdf_task` calls `PDFExtractor.extract_text()` then `prepare_analysis_input()`: Docling markdown wins when available, `raw_text` is the fallback; both land on `documents.raw_text` / `documents.structured_markdown`.

## Auth And Session

| Frontend Surface | Method | Backend Route | Current Shape | Notes |
| --- | --- | --- | --- | --- |
| `/sign-in` | `POST` | `/api/v1/login/access-token` | Form-encoded `username`, `password` -> `{ access_token, token_type }` | `username` carries the email value |
| `/sign-up` | `POST` | `/api/v1/users/register` | JSON `{ username, email, password }` -> created user | Sign-up then immediately calls login |
| session restore | `GET` | `/api/v1/users/me` | Bearer token -> current user payload | Used by `AuthProvider` |

Frontend session behavior in the current workspace:

- Token is stored in `localStorage` as `access_token`.
- A mirror cookie `smartlawer_access_token` is written so `src/middleware.ts` can protect private routes.
- Protected path prefixes are `/dashboard`, `/upload`, `/analysis`, and `/user-profile`.
- `next` query parameters are respected on sign-in and sign-up redirects.

## Product Workflow Matrix

| Frontend Route | Method | Backend Route | Expected Response Fields | Status |
| --- | --- | --- | --- | --- |
| `/upload` | `POST` | `/api/v1/documents/upload` | `id`, `task_id`, `status`, `taskStatusUrl`, optional `analysis_id` | Implemented in backend and consumed in frontend |
| `/upload` polling | `GET` | `/api/v1/tasks/{task_id}` | `status`, `progress`, optional `analysis_id`, `status_detail`, `error_message` | Implemented in backend and consumed in frontend |
| `/dashboard` | `GET` | `/api/v1/processes` | `id`, `title`, `status`, optional `analysis_id`, `status_detail` | Implemented in backend and consumed in frontend |
| `/analysis/[id]` | `GET` | `/api/v1/analysis/{analysis_id}` | `id`, `documentName`, `summary`, `keyArguments`, `requests`, `laws`, `defense_theses`, `generatedDefenseStrategy`, `docxDownloadUrl` | Implemented in backend and consumed in frontend |
| `/analysis/[id]` download | `GET` | `/api/v1/analysis/{analysis_id}/docx` | DOCX file response | Implemented in backend and consumed in frontend |
| `/analysis/[id]` template picker | `GET`/`POST` | `/api/v1/templates` (list own / upload DOCX) | `[{id, name, placeholders[], unsupportedPlaceholders[], created_at}]` | Implemented (C1); upload discovers Jinja roots, warns on unsupported |
| `/analysis/[id]` download | `GET` | `/api/v1/analysis/{analysis_id}/docx?template_id={uuid}` | DOCX rendered with the user template; 404 unknown/foreign template; 422 `unsupported_placeholders` | Implemented (C1); omitted `template_id` keeps the base-template path |
| `/analysis/[id]` versions | `GET` | `/api/v1/analysis/{analysis_id}/versions` | `[{version, template_id, created_at, downloadUrl}]` newest first | Implemented (C2) |
| `/analysis/[id]` versions | `GET` | `/api/v1/analysis/{analysis_id}/versions/{version}` | Versioned DOCX file; 404 unknown version/missing file | Implemented (C2); every generate records a version |
| `/prompts` | `GET`/`POST` | `/api/v1/prompts` (list own / create) | `[{id, name, strategy_prompt, is_default, created_at}]` | Implemented (C3) |
| `/prompts` | `PATCH`/`DELETE` | `/api/v1/prompts/{id}/default`, `/api/v1/prompts/{id}` | Switch default / delete own (404 foreign) | Implemented (C3) |
| `/upload` batch | `POST` | `/api/v1/documents/batch-upload` (≤10 PDFs) | `{items[], errors[]}` per-file tolerance | Implemented (C3) |
| `/analysis/[id]` summary | `GET` | `/api/v1/analysis/{analysis_id}/summary.md` | Markdown download | Implemented (C3) |
| `/audit` | `GET` | `/api/v1/audit?event_type=&entity_id=&limit=&scope=` | Own trail (`scope=all` admin-only, 403 otherwise) | Implemented (C4) |
| ops | `GET` | `/api/v1/ops/summary` | States, 24h counts, recent failures (admin-only) | Implemented (C4) |
| `/precedents` | `GET` | `/api/v1/precedents` | Shared corpus labels (any authed user) | Implemented (C5) |
| `/precedents` | `POST` | `/api/v1/precedents/seed` | (Re)seed shared corpus (admin-only) | Implemented (C5) |
| `/chat` | `POST` | `/api/v1/chat` | `{ answer, citations[{ref, chunk_id, document_id, document_name, page_start, excerpt}], suggested_questions[≤3], model }` | Implemented (A4); 503 without AI key; follow-ups added (chat-scope) |
| `/chat` streaming | `POST` | `/api/v1/chat/stream` | SSE `token` frames + final `done` with `citations` + `suggested_questions` | Implemented (A4); tenant from JWT, optional `document_id` scope (404 cross-user); UI sends scope from the history listbox |
| compatibility only | `GET` | `/api/v1/templates/{analysis_id}/generate` | DOCX file response | Keep until callers are fully migrated |

## Response Shape Notes

### Upload Submission

- Backend schema uses camel aliases for:
  - `taskStatusUrl`
  - `docxDownloadUrl`
- The stabilized response now returns both `id` and `task_id`; both currently point to the document UUID.
- **BL-014 decision (codified 2026-09-08): `task_id == document id == id` by design** — one document owns exactly one pipeline (single `Analysis` per document). `taskStatusUrl` (`/tasks/{id}`, API-root-relative) is the canonical polling URL; the frontend prefers it with `/tasks/{id}` fallback.
- Frontend consumes `taskStatusUrl` for polling (no longer constructs the URL from `id` only).
- The route only accepts `application/pdf`, stores the original PDF on disk, and hands that file path to the background worker.

### Task Status

- Status normalization in backend maps document states into:
  - `PENDING`
  - `PROCESSING`
  - `COMPLETED`
  - `FAILED`
- Frontend also tolerates `STARTED`, `RETRY`, `SUCCESS`, `DONE`, `FAILURE`, and `ERROR`.
- `analysis_id` is the handoff point from polling to the analysis page.

### Extraction And AI Input

- `process_pdf_task` is the active ingestion worker.
- The worker calls `PDFExtractor.extract_text(file_path=file_path)` and receives a plain string, then `prepare_analysis_input()` tries Docling markdown when `DOCLING_ENABLED=1`.
- `PDFExtractor` uses PyMuPDF text extraction first and Tesseract OCR as fallback for low-text pages (Docker now ships `tesseract-ocr-por` + `-eng`).
- The persisted `documents.raw_text` and `documents.structured_markdown` feed `LegalAnalyzer.analyze_petition(markdown or raw_text)`.

### Process List

- `GET /processes` is the dashboard source of truth.
- Items without `analysis_id` remain queue entries.
- Backend also returns `analysis_url` and `docxDownloadUrl`, though the dashboard currently links by `analysis_id`.

### Analysis Detail

- Backend schema is camel-oriented but the current page tolerates both camel and snake case for:
  - `documentName` or `document_name`
  - `keyArguments` or `key_arguments`
  - `generatedDefenseStrategy` or `generated_defense_strategy`
  - `docxDownloadUrl` or `docx_download_url`
- This tolerance is useful while BL-006 is still in flight.
- If a document exists but its analysis is not ready yet, `GET /analysis/{id}` returns `404` with structured detail containing `task_id`, `status`, and `status_detail`.

### DOCX Generation

- BL-007 hardened generation at the renderer boundary instead of changing route payloads.
- The current assumption is that `backend/templates/base_template.docx` remains compatible with normalized values for:
  - `summary`
  - `requests`
  - `laws`
  - `defense_theses`
  - `evidence`
- Analyzer fallback behavior now aims to keep enough structured data available for DOCX download even when provider-backed parsing fails.

### Template Management (C1/BL-015)

- `POST /api/v1/templates` (multipart `file` + optional `name`): persists the DOCX under the uploads volume, discovers Jinja roots (stdlib zip scan, split-run aware, loop vars/filters/keywords excluded), stores `placeholders`; incompatible roots are REPORTED (`unsupportedPlaceholders`), not rejected.
- `GET /api/v1/templates`: own templates, newest first.
- `GET /api/v1/analysis/{id}/docx?template_id={uuid}` (and legacy `/templates/{id}/generate`): 404 for unknown/foreign templates; 422 with `unsupported_placeholders` + `supported_keys` before any opaque render failure. Supported roots: `summary, requests, laws, evidence, defense_theses, generatedDefenseStrategy, analysis_json`.
- Omitted `template_id` keeps the `base_template.docx` path byte-identical (B2 smoke guard).
- Incidental fix: `Template.created_at` default was `datetime.now()` evaluated once at import (all rows shared one timestamp); now per-row lambda. Same latent bug exists in `analysis/document/document_chunk/user` — left for a follow-up.

### Generated-File History And Storage Lifecycle (C2/BL-017 + BL-019)

- Every successful generate persists a versioned copy under the managed
  `uploads/generated/{document_id}/` dir (compose bind-mount — survives
  container recreation) and records `generated_documents`
  (`analysis_id` + monotonically increasing `version`, unique).
- Retention: `GENERATED_KEEP_LATEST` (default 10, env/compose/`.env.example`)
  trims older files + rows after each generate; persistence never fails the
  download (falls back to the ephemeral render).

### Jurisprudence Corpus (C5/BL-023)

- 6 curated precedents live as `document_chunks` of a fixed system user
  (one system Document each → `[Jurisprudência] …` citation labels);
  retrieval allowlist = caller + system (scoped chat stays private-only).
- Auto-seed on API boot (`PRECEDENTS_AUTO_SEED`); keyless seeds carry
  noop vectors (FTS-visible, vector-excluded) and upgrade on reseed.
- Golden g31/g32 + corpus c13/c14 keep the eval gate green (0.969).

### AI Providers (live-LLM wiring)

- `AI_PROVIDER`: `openai` (direct) | `openrouter` (gateway, pinned model) |
  `gemini` (Google OpenAI-compatible endpoint, honors `CHAT_MODEL`).
  `openai` branch now honors `CHAT_MODEL` too (default `gpt-4-turbo`,
  behavior unchanged unless overridden).
- Embeddings stay on the OpenAI client; without an OpenAI key, retrieval
  degrades to FTS-only by design (proven in tests + live).

## Known Gaps And Assumptions

- BL-005 may change how much of the dashboard uses `analysis_url` and `docxDownloadUrl` directly.
- BL-006 may tighten the analysis payload and remove some camel/snake fallback handling once the shape is stable.
- BL-008 reported that sensitive workflow and template routes are protected; keep that assumption unless route registration changes again.
- The shared Axios 401/403 handler still clears `localStorage` but does not yet clear the mirrored auth cookie; BL-001 called this out as a follow-up.
- Docling remains a planned integration, not a current capability. See `docs/coordination/docling-status.md` for the current assessment and the minimum viable integration recommendation.
