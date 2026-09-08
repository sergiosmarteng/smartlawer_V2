# Worker Report — C4 Observability + RBAC (BL-018/024, issue #27)

## Task

- ID: BL-018 + BL-024 / #27
- Title: [C4] Observabilidade + RBAC/2FA/governança
- DoD: trilha de auditoria consultável.

## Scope

- `audit_events` (migration `20260908_0006`): user/event/entity/meta/timing.
  Best-effort helper `record_audit()` + `audit_document_completion()`
  (duration_ms, failure excerpt); raw user content never stored (LGPD).
- Hooks: register, login, upload (+batch items), template upload,
  docx.generated, prompt create/default/delete, chat.query (counts only),
  worker COMPLETED/FAILED.
- `GET /api/v1/audit` (own, filters; `scope=all` admin-only),
  `GET /api/v1/ops/summary` (admin: states, 24h counts, recent failures).
- RBAC: `role` column (`user` default) + `get_current_admin_user`;
  register ignores `role` (escalation test); grants via documented SQL.
- Frontend: `/audit` viewer page (nav + middleware protection).
- 2FA: DEFERRED by design (see below).

## Files Changed

- Backend: `models/audit_event.py` (NEW), migration `0006` (NEW),
  `core/audit.py` (NEW), `api/deps.py` (`get_current_admin_user`),
  `schemas/audit.py` (NEW), `api/routes/audit.py` (NEW), `main.py`,
  hooks in `users/auth/documents/templates/prompts/chat` routes +
  `tasks/document_tasks.py`, `tests/conftest.py`.
- `backend/tests/test_audit.py` — NEW (7 tests).
- Frontend: `pages/audit.tsx` (NEW), `Header.tsx`, `middleware.ts`,
  `types/workflow.ts`.

## Decisions

- Decision: full TOTP 2FA NOT implemented in this pass.
- Reason: real 2FA (enroll/verify/recover + login-contract change +
  frontend QR flow + new crypto dep + image rebuild) done halfway is
  security theater. Audit + RBAC + timing close the issue DoD; 2FA
  sketch: `pyotp` TOTP, `POST /auth/2fa/setup|enable|verify`, login
  step-up (`requires_2fa` + short-lived challenge token), backup codes
  hashed at rest, QR on `/user-profile`.
- Decision: admin grants out-of-band (SQL), no escalation endpoint.
- Reason: smallest privilege surface for the pilot phase.
- Decision: chat audit on the JSON route only (counts/scope, no query).
- Reason: session/DB access inside the SSE generator is fragile;
  LGPD forbids raw query storage anyway.

## Validation

- `pytest backend/tests` → **99 passed** (92 + 7), no regressions.
- `tsc` clean, targeted `next lint` clean.
- WSL live: migration auto-applied (head `20260908_0006`); flow 11/11
  (trail populates end-to-end incl. worker completion + timing,
  RBAC gates 403); B2 smoke re-passed **10/10**.
- Ops note: celery has no auto-reload — `compose restart worker` was
  required to pick up task code (first live run missed completions;
  green after restart).

## Handoff Notes

- Promote an admin: `UPDATE users SET role='admin' WHERE email='…';`
- `GET /ops/summary` + `scope=all` need that role.
- Commit: local only, no push (per implementation-plan rule 6).
