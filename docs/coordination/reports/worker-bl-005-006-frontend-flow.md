# Worker Report

## Task

- ID: `BL-005 + BL-006`
- Title: Align main frontend workflow pages with the live backend workflow contract

## Scope

- What was changed
  - Reworked the upload, dashboard, and analysis-detail pages to use the active backend routes: `/documents/upload`, `/tasks/{id}`, `/processes`, `/analysis/{id}`, and `/analysis/{id}/docx`.
  - Added cleaner handling for loading, empty, error, and success states across the workflow pages.
  - Refined `Header`, `Sidebar`, `layout`, and `src/lib/axios.ts` so the workflow area uses the same auth-aware navigation and a more consistent dark visual shell.
  - Added frontend-side normalization for backend payload aliases such as `documentName`, `keyArguments`, `generatedDefenseStrategy`, and `docxDownloadUrl`.
- What was intentionally left untouched
  - No backend code was edited.
  - No auth provider internals were changed beyond consuming the existing `AuthProvider`.
  - No routes outside the files listed in the assignment were changed.

## Files Changed

- `src/pages/upload.tsx`
- `src/pages/dashboard.tsx`
- `src/pages/analysis/[id].tsx`
- `src/components/Header.tsx`
- `src/components/Sidebar.tsx`
- `src/components/layout.tsx`
- `src/lib/axios.ts`
- `docs/coordination/reports/worker-bl-005-006-frontend-flow.md`

## Decisions

- Decision: Treat the upload response `id` as the polling identifier.
- Reason: `POST /documents/upload` currently returns `DocumentResponse`, not a dedicated `task_id`. The workflow endpoint accepts the document UUID at `GET /tasks/{id}`.

- Decision: Keep dashboard rows without `analysis_id` non-clickable.
- Reason: `/processes` can legitimately return documents that are still processing and do not yet have an analysis detail route.

- Decision: Normalize both camelCase and snake_case analysis payload fields in the frontend.
- Reason: The current backend schema uses aliased fields, but concurrent backend work could still expose snake_case responses during transitions.

- Decision: Use the backend-provided DOCX path when available and fall back to `/analysis/{id}/docx`.
- Reason: This preserves compatibility with the live workflow route while keeping the frontend resilient if the backend later starts returning a fully qualified download path.

## Validation

- Tests run: `npx next lint --file src/pages/upload.tsx --file src/pages/dashboard.tsx --file src/pages/analysis/[id].tsx --file src/components/Header.tsx --file src/components/Sidebar.tsx --file src/components/layout.tsx --file src/lib/axios.ts`
- Result: Passed

## Handoff Notes

- Follow-up items:
  - Backend dependency: `/analysis/{id}` returns `404 "Analysis not ready"` until an `Analysis` row exists. The dashboard and upload flow now account for that by waiting for `analysis_id`.
  - Backend dependency: `/processes` is user-scoped and may return completed, pending, or failed documents with `status_detail`; UI now surfaces that field directly.
  - Backend dependency: `/analysis/{id}/docx` is the active download route for the detail page, replacing the old template-generation assumption.
- Risks or open questions:
  - The upload page assumes the backend continues using document UUIDs as task identifiers. If workflow ownership later moves to a separate queue id, the upload response contract will need to expose it explicitly.
  - The dark workflow shell now wraps these pages, but `Footer` still uses the older light treatment because it was outside this task's ownership.
