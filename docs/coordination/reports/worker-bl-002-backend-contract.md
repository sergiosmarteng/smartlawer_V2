# Worker Report Template

## Task

- ID: BL-002 + BL-008
- Title: Stabilize backend workflow/status/document-generation contract and verify auth protection on sensitive routes

## Scope

- What was changed
  Stabilized the backend contract around `POST /api/v1/documents/upload`, `GET /api/v1/processes`, `GET /api/v1/tasks/{id}`, `GET /api/v1/analysis/{id}`, and `GET /api/v1/analysis/{id}/docx`.
  Added an explicit upload follow-up payload with `task_id` and `taskStatusUrl`.
  Normalized workflow-facing statuses to `PENDING`, `PROCESSING`, `COMPLETED`, and `FAILED`.
  Made analysis/detail and DOCX download resolution accept either `analysis_id` or `document_id`, which preserves frontend flows that fall back to task/document ids.
  Added richer workflow metadata such as `updated_at`, `completed_at`, `analysis_url`, and `docxDownloadUrl`.
  Hardened upload handling so queueing failures mark the document as failed and return `503` instead of silently leaving an orphaned pending upload.
- What was intentionally left untouched
  Did not change route registration, auth dependency plumbing outside the listed files, or frontend code.
  Did not change `backend/app/api/routes/users.py` because current protection is already consistent for the sensitive route: `GET /api/v1/users/me` remains protected, while `POST /api/v1/users/register` remains intentionally public.

## Files Changed

- `backend/app/api/routes/documents.py`
- `backend/app/api/routes/templates.py`
- `backend/app/api/routes/workflow.py`
- `backend/app/crud/document.py`
- `backend/app/models/document.py`
- `backend/app/schemas/workflow.py`
- `backend/app/tasks/document_tasks.py`
- `docs/coordination/reports/worker-bl-002-backend-contract.md`

## Decisions

- Decision:
  Keep the existing `/api/v1` workflow surface as the primary contract.
- Reason:
  The frontend already calls `/processes`, `/tasks/{id}`, `/analysis/{id}`, and `/analysis/{id}/docx`; stabilizing those avoids creating a second API surface.

- Decision:
  Return upload metadata from `POST /api/v1/documents/upload` instead of a bare document row.
- Reason:
  The frontend needs an immediate follow-up handle for polling. The response now includes both `id` and `task_id`, plus `taskStatusUrl`.

- Decision:
  Resolve analysis/docx requests by either `analysis_id` or `document_id`.
- Reason:
  The current frontend redirects with `analysis_id || taskId`, so the backend must tolerate either identifier to keep the flow reliable.

- Decision:
  Keep sensitive workflow and template routes protected with `deps.get_current_active_user`.
- Reason:
  Uploads, process lists, analysis detail, and generated documents are user-specific and should not be exposed cross-account.

## Validation

- Tests run:
  `python -c "import ast, pathlib; ..."` against all edited backend contract files
  `python -m compileall backend/app`
  `python -m pytest backend/tests/test_auth.py -q`
- Result:
  Static AST parsing passed for all edited files.
  `compileall` was blocked by workspace `__pycache__` permission errors.
  Runtime import / pytest bootstrap was blocked by environment dependencies outside this scope:
  first by `.env` extras when running from the repo root,
  then by missing `psycopg2` when running from `backend/`.

## Handoff Notes

- Follow-up items:
  Frontend can now rely on this upload response shape:

  ```json
  {
    "id": "document-uuid",
    "task_id": "document-uuid",
    "user_id": "user-uuid",
    "filename": "petition.pdf",
    "content_type": "application/pdf",
    "status": "PENDING",
    "status_detail": "Queued for processing",
    "uploaded_at": "2026-05-11T12:00:00Z",
    "taskStatusUrl": "/tasks/document-uuid",
    "analysis_id": null,
    "analysis_url": null,
    "docxDownloadUrl": null
  }
  ```

  Frontend can rely on this task polling shape:

  ```json
  {
    "task_id": "document-uuid",
    "document_id": "document-uuid",
    "title": "petition.pdf",
    "status": "PROCESSING",
    "progress": 35,
    "analysis_id": null,
    "status_detail": "Extracting text from PDF",
    "error_message": null,
    "created_at": "2026-05-11T12:00:00Z",
    "updated_at": "2026-05-11T12:00:10Z",
    "completed_at": null,
    "analysis_url": null,
    "docxDownloadUrl": null
  }
  ```

  Frontend can rely on this analysis detail shape:

  ```json
  {
    "id": "analysis-uuid",
    "document_id": "document-uuid",
    "documentName": "petition.pdf",
    "title": "petition.pdf",
    "summary": "....",
    "keyArguments": ["..."],
    "requests": ["..."],
    "laws": ["..."],
    "evidence": [],
    "defense_theses": ["..."],
    "status": "COMPLETED",
    "status_detail": "Analysis ready",
    "created_at": "2026-05-11T12:00:20Z",
    "completed_at": "2026-05-11T12:01:00Z",
    "generatedDefenseStrategy": "1. ...",
    "docxDownloadUrl": "/analysis/analysis-uuid/docx"
  }
  ```

  `GET /api/v1/analysis/{id}` now accepts either an `analysis_id` or the originating `document_id`.
  `GET /api/v1/analysis/{id}/docx` and `GET /api/v1/templates/{id}/generate` follow the same resolution rule.
  If a document exists but analysis is not ready, `GET /api/v1/analysis/{id}` returns `404` with a structured detail payload containing `task_id`, `status`, and `status_detail`.
  Sensitive routes verified as protected: `/api/v1/users/me`, `/api/v1/documents/*`, `/api/v1/processes`, `/api/v1/tasks/{id}`, `/api/v1/analysis/{id}`, `/api/v1/analysis/{id}/docx`, `/api/v1/templates/{id}/generate`.
- Risks or open questions:
  Runtime validation is still blocked until the backend environment is normalized:
  the root `.env` currently contains keys not accepted by `backend/app/core/config.py`,
  and the local Python environment is missing `psycopg2` for PostgreSQL-backed imports/tests.
