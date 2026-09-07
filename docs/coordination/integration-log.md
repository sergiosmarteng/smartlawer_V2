# Integration Log

This file is append-only. Add one short entry per landed worker or coordinator merge step.

## 2026-05-11

### BL-001 landed

- Source: `reports/worker-bl-001-auth.md`
- Scope: consolidated frontend auth around backend JWT and `/users/me`
- Workspace impact:
  - login and sign-up now honor `next`
  - middleware protects `/dashboard`, `/upload`, `/analysis`, `/user-profile`
  - profile page reads backend user data
  - SuperTokens surface is now compatibility-only
- Follow-up carried forward:
  - clear mirrored auth cookie in the shared Axios 401/403 path
  - revisit cookie strategy if server-managed sessions are introduced

### DOC-001 landed

- Scope: created coordination docs for backlog, contract snapshot, and handoff logging
- Workspace impact:
  - `backlog.md` now reflects BL-001 as completed
  - `api-contract.md` captures the current workflow shape from the workspace
  - this log can now be extended as BL-002, BL-005, BL-006, BL-007, BL-008, and BL-009 land
- Assumptions to revisit:
  - upload/task contract after BL-002
  - final analysis payload after BL-006
  - sensitive route protection notes after BL-008

### BL-002 and BL-008 landed

- Source: `reports/worker-bl-002-backend-contract.md`
- Scope: stabilized backend workflow/status/document-generation contract and verified sensitive-route auth protection
- Workspace impact:
  - upload now returns explicit follow-up metadata including `task_id` and `taskStatusUrl`
  - workflow-facing statuses are normalized to `PENDING`, `PROCESSING`, `COMPLETED`, and `FAILED`
  - analysis and DOCX routes accept either `analysis_id` or `document_id`
  - sensitive routes were verified as protected across documents, workflow, and template download endpoints
- Follow-up carried forward:
  - BL-005, BL-006, and BL-007 should build on this backend contract rather than inventing new routes
  - runtime validation still depends on normalizing the backend environment and dependencies

### BL-009 landed

- Source: `reports/worker-bl-009-tests.md`
- Scope: stabilized backend tests for auth, documents, and workflow routes
- Workspace impact:
  - local route-level tests now use a disposable SQLite-backed harness
  - focused coverage exists for auth, upload validation, process listing, task status, analysis detail, and DOCX download
- Follow-up carried forward:
  - add a separate integration layer later for real Postgres, Redis, Celery, OCR, AI, and DOCX runtime dependencies

### BL-007 landed

- Source: `reports/worker-bl-007-docx-flow.md`
- Scope: hardened DOCX generation and improved fallback analysis data for document rendering
- Workspace impact:
  - document generation now normalizes mixed payload values before rendering the template
  - DOCX errors are clearer when template load, render, or save steps fail
  - analyzer fallback behavior is more likely to leave a renderable payload for `/analysis/{id}/docx`
- Follow-up carried forward:
  - keep future template placeholder expansion inside the normalization layer when possible
  - verify temp-file write assumptions in the deployment environment during final smoke

### QA smoke prep landed

- Source: `reports/worker-qa-smoke-prep.md`
- Scope: added a manual pilot smoke checklist and acceptance notes for the integrated v1 flow
- Workspace impact:
  - `smoke-checklist.md` now defines the operator path from auth through DOCX download
  - the stabilization report now references manual smoke expectations and open worker dependencies
- Follow-up carried forward:
  - re-run the checklist only after BL-007 DOCX hardening is merged in the shared environment
  - treat BL-009 backend-test stabilization as required evidence before pilot sign-off

### Integration review captured

- Source: `reports/worker-integration-review.md`
- Scope: reviewed the in-flight stabilization work across auth, frontend workflow, backend contract, DOCX generation, and route-level tests
- Workspace impact:
  - no code changes requested from review alone
  - coordinator findings are now consolidated in `review-findings.md`
  - the current branch has no P0 blockers recorded from this review pass
- Follow-up carried forward:
  - clear the mirrored auth cookie on the shared `401/403` path
  - surface structured "analysis not ready" metadata on the frontend
  - preserve `next` across sign-in/sign-up cross-navigation

### Coordinator validation and follow-up fixes

- Source: coordinator local integration pass
- Scope: addressed the review findings that could be closed without reopening larger architecture work
- Workspace impact:
  - shared Axios `401/403` cleanup now removes the mirrored auth cookie as well as `localStorage`
  - sign-in and sign-up cross-links now preserve `next`
  - the analysis page now surfaces structured "analysis not ready" metadata from the backend
  - local validation passed with `npx tsc --noEmit`, targeted `next lint`, and `pytest backend/tests -q --basetemp C:\tmp\pytest-final -p no:cacheprovider`
- Follow-up carried forward:
  - BL-007 still needs a real DOCX runtime download check
  - BL-010 still needs the integrated manual smoke execution

## 2026-09-07

### A1 landed — pgvector migration + document_chunks table (Onda A RAG)

- Scope: vector foundation for legal RAG; no retrieval/generation yet
- Workspace impact:
  - new `document_chunks` table: `document_id` (CASCADE), `user_id` tenant FK, `matter_id`, `chunk_index`, `content`, pages, token count, `embedding VECTOR(1536)`, `embedding_model/_version`, HNSW cosine index + tenant/matter indexes
  - alembic `20260407_0001 -> 20260907_0001` renders offline-verified SQL (`CREATE EXTENSION vector`, `VECTOR(1536)`, `USING hnsw ... vector_cosine_ops`)
  - `db` image `postgres:15-alpine -> pgvector/pgvector:pg15`; `pgvector==0.5.0` pinned; embedding settings in `config.py`
  - `REQUIRED_TABLES` repair covers `document_chunks`; sqlite tests map `VECTOR -> JSON`
  - suite: `18 passed` (12 existing + 6 new in `tests/test_document_chunks.py`: DDL, CRUD/ordering, tenant isolation)
- Follow-up carried forward:
  - A2 Docling ingestion writing into `document_chunks`; live pgvector validation needs Docker daemon running (was down on dev machine)
