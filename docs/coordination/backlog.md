# SmartLawer V2 Execution Backlog

## Active Queue

| ID | Priority | Task | Suggested Owner | Depends On | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BL-001 | P0 | Consolidate JWT auth path in frontend and backend usage | Nash | none | completed | Delivery landed, lint passed, and the mirrored cookie cleanup plus `next` preservation follow-up were applied locally. Acceptance is still partially validated pending integrated auth verification. See `acceptance-matrix.md` and `reports/worker-bl-001-auth.md`. |
| BL-002 | P0 | Upload and task-status contract stabilization | Franklin | BL-001 | blocked | Contract changes landed, but runtime acceptance is blocked by backend environment issues (`.env` parsing and missing `psycopg2`). See `acceptance-matrix.md` and `reports/worker-bl-002-backend-contract.md`. |
| BL-005 | P1 | Dashboard processes listing on real backend data | Gibbs | BL-002 | completed | Frontend dashboard now uses the live workflow contract; acceptance remains partially validated until integrated smoke. See `acceptance-matrix.md` and `reports/worker-bl-005-006-frontend-flow.md`. |
| BL-006 | P1 | Analysis detail rendering and docx download flow | Gibbs | BL-002 | completed | Frontend detail/download flow landed against `/analysis/{id}` and `/analysis/{id}/docx`; final signoff still needs a real completed analysis. See `acceptance-matrix.md` and `reports/worker-bl-005-006-frontend-flow.md`. |
| BL-007 | P1 | Harden DOCX generation and download flow | Fermat | BL-002 | completed | Hardening landed in generator and analyzer fallback paths; acceptance is still pending runtime DOCX validation. See `acceptance-matrix.md` and `reports/worker-bl-007-docx-flow.md`. |
| BL-008 | P1 | Re-enable auth protection on sensitive routes and verify consistency | Franklin | BL-001 | blocked | Sensitive routes were verified in code, but local runtime validation is blocked alongside BL-002. See `acceptance-matrix.md` and `reports/worker-bl-002-backend-contract.md`. |
| BL-009 | P1 | Stabilize backend tests for auth and workflow | Nietzsche | BL-001, BL-002, BL-008 | completed | Local route-level suite expanded; see `reports/worker-bl-009-tests.md` |
| DOC-001 | P1 | Organize handoff docs, API contract notes, and integration log | Locke | none | completed | Shared docs surface created for handoffs and incremental integration |
| BL-010 | P0 | Smoke verification and final integration report | reviewer/integration | all above | pending | Checklist is prepared, but the integrated end-to-end smoke still needs execution. See `acceptance-matrix.md` and `reports/worker-qa-smoke-prep.md`. |

## Handoff Order

1. BL-005 and BL-006 should start from the backend contract in `reports/worker-bl-002-backend-contract.md`.
2. BL-006 should preserve the identifier fallback behavior documented for `/analysis/{id}` and `/analysis/{id}/docx`.
3. BL-010 happens after the remaining UI and integration work lands.
4. Use `acceptance-matrix.md` as the current signoff surface for BL-001, BL-002, BL-005, BL-006, BL-007, BL-008, BL-009, and BL-010.

## Notes For Incoming Workers

- Read `reports/worker-bl-001-auth.md` before touching auth-related frontend code.
- Read `reports/worker-bl-002-backend-contract.md` before touching upload, tasks, processes, analysis, or DOCX flows.
- Read `reports/worker-bl-007-docx-flow.md` before changing document generation behavior.
- Read `reports/worker-bl-009-tests.md` before changing backend tests or test bootstrap assumptions.
- Use `api-contract.md` as the current contract snapshot, but expect BL-005 and BL-006 to refine frontend usage details.
- Check `acceptance-matrix.md` before claiming final closure on any stabilization backlog item.
- Append each landed task to `integration-log.md` so the next worker has a chronological handoff trail.
- Review `review-findings.md` to separate resolved follow-ups from still-open validation gaps.
