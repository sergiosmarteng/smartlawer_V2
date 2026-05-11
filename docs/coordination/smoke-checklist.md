# SmartLawer V2 Pilot Smoke Checklist

Last updated: 2026-05-11
Owner: QA coordination
Scope: manual smoke coverage for the pilot flow `sign-up/sign-in -> upload -> task polling -> dashboard -> analysis -> docx download`

## Use This Checklist When

- BL-001, BL-002, BL-005, and BL-006 are merged into the shared branch.
- The integrated environment has API, worker, database, and frontend running together.
- A real test PDF is available for upload.

## Current Dependencies

- Pending worker dependency: `BL-007` should confirm DOCX generation/download hardening before pilot sign-off.
- Pending worker dependency: `BL-009` should stabilize backend tests before this checklist is treated as release evidence.
- Integration dependency: the coordinator still needs to verify that the landed frontend and backend contract changes are running in the same environment.

## Pre-Flight Setup

- Confirm the active auth flow is the backend JWT path, not a parallel provider flow.
- Confirm the upload worker/queue is processing jobs.
- Confirm the sample PDF is a supported file type and not password-protected.
- Confirm the browser can download files locally.
- Confirm you have one fresh user account available for sign-up testing or one known-good account for sign-in testing.

## Smoke Steps

### 1. Sign-Up / Sign-In

- Open `/sign-up` and create a fresh user account.
- Expected:
  - Registration completes without a fatal UI error.
  - The app either signs the user in directly or sends them cleanly into the supported sign-in flow.
  - Protected routes redirect anonymous users to `/sign-in` with the original destination preserved in `next`.
- Open `/sign-in` and authenticate with the pilot account.
- Expected:
  - Login succeeds against the backend JWT flow.
  - Refreshing the page keeps the session usable.
  - Opening `/dashboard`, `/upload`, `/analysis/<id>`, or `/user-profile` no longer redirects while authenticated.

### 2. Upload

- Go to `/upload`.
- Submit one valid PDF.
- Expected:
  - Upload completes without a page crash.
  - The UI shows the document filename and a task/progress state instead of hanging silently.
  - A follow-up polling cycle begins automatically.
  - If the backend returns an immediate failure, the UI surfaces the failure message clearly.

### 3. Task Polling

- Keep the upload page open until processing finishes or fails.
- Expected:
  - Status values move through the normalized workflow states: `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`.
  - `status_detail` updates as work advances and is visible to the user.
  - Failed jobs show a readable error path instead of a stuck spinner.
  - Completed jobs expose a valid next step to view analysis data.

### 4. Dashboard

- Open `/dashboard` after the upload is queued and again after it completes.
- Expected:
  - The uploaded document appears in the current user's list.
  - The row shows a real status from the backend, not placeholder data.
  - Rows without `analysis_id` stay non-clickable or clearly unavailable.
  - Once analysis is ready, the dashboard links to the correct analysis detail page.
  - No data from another user account is visible.

### 5. Analysis Detail

- Open the analysis from the dashboard link.
- Expected:
  - The analysis page loads real backend data instead of mock content.
  - The page tolerates either camelCase or snake_case aliases already normalized by the frontend.
  - Summary/strategy sections render without crashing even if fallback content is sparse.
  - If the analysis is not ready yet, the user sees a clear waiting/error state rather than a broken page.

### 6. DOCX Download

- Trigger the DOCX download from the analysis page.
- Expected:
  - The request uses the canonical analysis download route.
  - The download starts without an auth error loop.
  - The downloaded file has a valid `.docx` extension and opens successfully in a DOCX-compatible editor.
  - The file content matches the uploaded case at a basic sanity-check level.

## Acceptance Notes

- Treat the smoke run as passed only if one full happy-path user can complete the entire flow without manual API intervention.
- AI output quality is not a smoke blocker when the environment is intentionally using fallback analysis mode; availability and stability are the focus here.
- Any `FAILED` processing state, broken redirect, missing dashboard row, blank analysis page, or unreadable DOCX should block pilot sign-off.
- Record each defect with:
  - timestamp
  - user account used
  - uploaded filename
  - last visible workflow state
  - screenshot or API response snippet if available

## Post-Run Notes To Capture

- Total time from upload start to analysis-ready state.
- Whether refresh/navigation preserved auth and workflow state correctly.
- Whether the dashboard and analysis pages stayed consistent after processing completed.
- Whether DOCX download succeeded on the first try.
