# Integration Review Findings

## 2026-05-11

No P0 blockers were found in the in-flight stabilization set. The current risks are follow-up bugs and coverage gaps in the auth and workflow edges below.

1. Severity: Resolved
   The mirrored auth cookie survives the shared `401/403` path, so an expired or revoked JWT can still pass Next middleware on hard navigations until the client re-checks `/users/me`.
   References:
   - `src/lib/axios.ts:29-33`
   - `src/middleware.ts:18-31`
   - `src/components/auth/AuthProvider.tsx:63-65`
   Why it matters:
   - Protected routes stop being enforced consistently at the server edge after token expiry.
   - Users can re-enter `/dashboard`, `/upload`, `/analysis`, or `/user-profile` via refresh/back navigation and only get rejected after the client bootstraps.

   Resolution:
   - Fixed in the coordinator integration pass by clearing the mirrored cookie from `src/lib/axios.ts` alongside `localStorage`.

2. Severity: Resolved
   The backend now returns a structured `detail` payload for "analysis not ready", but the frontend error helper does not read `detail.message` or the attached workflow metadata. The analysis screen therefore degrades to a generic Axios 404 instead of surfacing the actionable queue state.
   References:
   - `backend/app/api/routes/workflow.py:185-193`
   - `src/lib/axios.ts:40-69`
   - `src/pages/analysis/[id].tsx:64-66`
   Why it matters:
   - The new backend contract carries `task_id`, `status`, and `status_detail`, but the UI currently drops that context.
   - This makes direct opens of `/analysis/{id}` during processing much harder to recover from and leaves the "not ready yet" path effectively untested in the frontend.

   Resolution:
   - Fixed in the coordinator integration pass by teaching the error helper to read `detail.message` and surfacing structured workflow metadata in `src/pages/analysis/[id].tsx`.

3. Severity: Resolved
   The auth page cross-links do not preserve `next`, so a user redirected to `/sign-in?next=/protected/path` loses the intended destination if they switch to sign-up and then complete registration.
   References:
   - `src/pages/sign-in/[[...index]].tsx:108-112`
   - `src/pages/sign-up/[[...index]].tsx:126-130`
   Why it matters:
   - BL-001 fixed `next` handling inside each page, but this branch still drops the redirect target during the common "I need an account first" path.

   Resolution:
   - Fixed in the coordinator integration pass by preserving `next` across sign-in/sign-up cross-links.

## Residual Risks

- Backend tests are healthy for route contracts, but they intentionally stub real multipart, Celery, LangChain/OpenAI, OCR, and `docxtpl` dependencies, so the suite still does not prove production-like integration behavior. Reference: `backend/tests/conftest.py:28-212`.
- I did not find a worker or test covering the "analysis exists but DOCX template file is missing/unreadable" path in a shared runtime. The backend now raises clearer errors there, but runtime evidence is still missing. References: `backend/app/api/routes/templates.py:91-100`, `backend/app/core/doc_generator.py:116-151`.
