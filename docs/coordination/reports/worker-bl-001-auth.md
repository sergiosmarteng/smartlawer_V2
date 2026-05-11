# Worker Report Template

## Task

- ID: BL-001
- Title: Consolidate the SmartLawer frontend auth path around the backend JWT flow

## Scope

- What was changed
  Consolidated the frontend session flow around `/api/v1/login/access-token` and `/api/v1/users/me`, updated guarded route handling, removed misleading SuperTokens behavior from the supported auth surface, and fixed auth-page/profile UX issues caused by the mixed setup.
- What was intentionally left untouched
  Backend auth routes, non-auth frontend pages, and the shared Axios interceptor were left unchanged to respect worker scope and concurrent edits elsewhere.

## Files Changed

- `src/components/auth/AuthProvider.tsx`
- `src/components/auth/AuthGuard.tsx`
- `src/components/auth/SuperTokensProvider.tsx`
- `src/components/auth/SuperSignInButton.tsx`
- `src/components/auth/index.ts`
- `src/pages/sign-in/[[...index]].tsx`
- `src/pages/sign-up/[[...index]].tsx`
- `src/pages/user-profile/[[...index]].tsx`
- `src/middleware.ts`
- `docs/coordination/reports/worker-bl-001-auth.md`

## Decisions

- Decision:
  Keep the frontend auth model centered on the backend JWT token and current-user endpoint.
- Reason:
  Those endpoints already exist and are enough to drive login, registration bootstrap, and session restoration without a parallel auth provider.

- Decision:
  Mirror the JWT from `localStorage` into a lightweight cookie for middleware checks.
- Reason:
  Next.js middleware cannot read `localStorage`, so a cookie mirror was needed to protect private routes consistently on hard navigations.

- Decision:
  Do not use middleware to redirect authenticated users away from `/sign-in` and `/sign-up`.
- Reason:
  The existing Axios interceptor still clears only `localStorage` on 401/403, so redirecting solely from the cookie could create stale-cookie loops until that shared layer is updated.

- Decision:
  Keep `SuperTokensProvider` as a no-op compatibility wrapper and make `SuperSignInButton` point into the JWT flow.
- Reason:
  This removes misleading behavior without breaking existing imports during the broader auth cleanup.

## Validation

- Tests run:
  `npm run lint -- --file src/components/auth/AuthProvider.tsx --file src/components/auth/AuthGuard.tsx --file src/components/auth/SuperTokensProvider.tsx --file src/components/auth/SuperSignInButton.tsx --file src/components/auth/index.ts --file src/pages/sign-in/[[...index]].tsx --file src/pages/sign-up/[[...index]].tsx --file src/pages/user-profile/[[...index]].tsx --file src/middleware.ts`
- Result:
  Passed.

## Handoff Notes

- Follow-up items:
  Update the shared Axios 401/403 handler to clear the mirrored auth cookie in addition to `localStorage`.
- Follow-up items:
  If future work introduces refresh tokens or server-set cookies, replace the client-written cookie mirror with an HttpOnly session cookie.
- Risks or open questions:
  Middleware currently checks only for token presence, not token validity; invalid tokens still fall back to `AuthGuard` after the client validates `/users/me`.
