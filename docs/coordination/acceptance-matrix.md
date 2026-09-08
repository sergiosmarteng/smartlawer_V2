# SmartLawer V2 Acceptance Matrix

Last updated: 2026-05-11

## Status Legend

- `implemented`: delivered and validated enough to satisfy the backlog item itself
- `partially validated`: delivered with limited validation, but still needs integrated confirmation
- `blocked`: acceptance cannot be closed because required local/runtime validation is currently blocked
- `pending validation`: implementation or validation evidence is not yet sufficient for signoff

## Stabilization Backlog

| ID | Scope | Acceptance Status | Evidence | Signoff Notes |
| --- | --- | --- | --- | --- |
| BL-001 | Consolidate JWT auth path in frontend/backend usage | partially validated | `reports/worker-bl-001-auth.md`; targeted frontend lint passed; coordinator follow-up fixes landed | Auth flow landed and the stale auth-cookie plus `next` cross-link follow-ups were closed locally, but final signoff still needs an integrated login/session verification pass. |
| BL-002 | Stabilize upload, task-status, process, and analysis backend contract | blocked | `reports/worker-bl-002-backend-contract.md`; static AST parsing passed | Runtime acceptance is blocked until the backend environment is normalized enough to run local API validation without `.env` parsing issues and missing `psycopg2`. |
| BL-005 | Dashboard processes listing on real backend data | partially validated | `reports/worker-bl-005-006-frontend-flow.md`; targeted `next lint` passed | Dashboard now targets the stabilized contract, but acceptance still depends on integrated verification against a runnable `/processes` backend. |
| BL-006 | Analysis detail rendering and DOCX download flow | partially validated | `reports/worker-bl-005-006-frontend-flow.md`; targeted `next lint` passed; coordinator follow-up fixes landed | The page is wired to `/analysis/{id}` and `/analysis/{id}/docx`, and the "analysis not ready" path now surfaces backend metadata. Final acceptance still needs a real completed analysis and downloadable DOCX in one environment. |
| BL-007 | Harden DOCX generation and download flow | pending validation | `reports/worker-bl-007-docx-flow.md`; Python source compilation passed | Code hardening landed, but this item cannot be marked complete until local runtime validation confirms `/analysis/{id}/docx` produces a usable file with the active template and temp-write permissions. |
| BL-008 | Re-enable auth protection on sensitive routes and verify consistency | blocked | `reports/worker-bl-002-backend-contract.md`; protected-route review completed | Code-level verification is in place, but local API validation is still blocked by the same backend environment issues affecting BL-002. |
| BL-009 | Stabilize backend tests for auth and workflow | implemented | `reports/worker-bl-009-tests.md`; `12 passed` on `pytest backend/tests -q --basetemp C:\\tmp\\pytest-bl009-all` | Route-level local test coverage is stable. Separate integration coverage for real Postgres/Celery/OCR/AI remains future work, not a blocker for this backlog item itself. |
| BL-010 | Smoke verification and final integration report | pending validation | `reports/worker-qa-smoke-prep.md`; `smoke-checklist.md` prepared | The checklist exists, but the manual end-to-end smoke has not been executed on a fully integrated environment yet. |
| BL-011 | Normalize integrated runtime environment for pilot validation | partially validated | `reports/worker-b1-env.md`; `docker compose config` valid; backend image build completed | Recipe landed (env parity, worker boot, healthchecks). Final acceptance needs `docker compose up` all-healthy + `/health` evidence, pending daemon recovery — resume steps in report. |

## Final Signoff Gate

Final stabilization signoff is still gated by:

1. Local runtime validation for BL-002 and BL-008 after backend environment normalization.
2. End-to-end DOCX generation validation for BL-007.
3. Coordinator-run smoke execution and report closure for BL-010.
