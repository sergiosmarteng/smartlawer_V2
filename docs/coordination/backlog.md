# SmartLawer V2 Execution Backlog

Last updated: 2026-05-12

## Current Baseline

- The stabilized pilot path in the workspace is `auth -> upload -> task polling -> dashboard -> analysis -> DOCX download`.
- Frontend and backend contract work for BL-001, BL-005, BL-006, BL-007, and BL-009 has landed locally.
- The remaining pilot gate is no longer route-shape work; it is integrated runtime validation and closure of the still-missing product capabilities from the PRD.
- Docling is not active in the ingestion pipeline today. The current worker path remains `upload -> process_pdf_task -> PDFExtractor.extract_text() -> LegalAnalyzer.analyze_petition()`, with no intermediate Markdown persistence for AI consumption.

## Stabilization Carry-Over

| ID | Priority | Task | Suggested Owner | Depends On | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BL-001 | P0 | Consolidate JWT auth path in frontend and backend usage | Nash | none | completed | Delivery landed, follow-up fixes for mirrored auth cookie cleanup and `next` preservation were applied locally, and targeted validation passed. Final signoff still depends on integrated smoke. |
| BL-002 | P0 | Upload and task-status contract stabilization | Franklin | BL-001 | pending validation | Contract changes landed and `.env` tolerance improved on 2026-05-12, but a real shared runtime validation with the full backend stack is still required. |
| BL-005 | P1 | Dashboard processes listing on real backend data | Gibbs | BL-002 | completed | Frontend dashboard uses the live workflow contract. Final signoff still depends on integrated smoke. |
| BL-006 | P1 | Analysis detail rendering and DOCX download flow | Gibbs | BL-002 | completed | Frontend detail and download flow are aligned to `/analysis/{id}` and `/analysis/{id}/docx`, but final acceptance still needs a real completed analysis in one running environment. |
| BL-007 | P1 | Harden DOCX generation and download flow | Fermat | BL-002 | pending validation | Generator and analyzer hardening landed, but runtime validation with the active template and real temp-file permissions is still missing. |
| BL-008 | P1 | Re-enable auth protection on sensitive routes and verify consistency | Franklin | BL-001 | pending validation | Code-level protection is in place. Final verification should happen during the integrated auth and workflow smoke pass. |
| BL-009 | P1 | Stabilize backend tests for auth and workflow | Nietzsche | BL-001, BL-002, BL-008 | completed | Local route-level suite expanded and passing with `12 passed`. |
| BL-010 | P0 | Smoke verification and final integration report | reviewer/integration | BL-001, BL-002, BL-005, BL-006, BL-007, BL-008, BL-009 | pending | Checklist is prepared, but the integrated end-to-end smoke still needs execution in one environment. |

## Next Delivery Waves

| ID | Priority | Task | Suggested Owner | Depends On | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BL-011 | P0 | Normalize integrated runtime environment for pilot validation | platform/backend | BL-002, BL-009 | completed | Recipe landed 2026-09-08; live `compose up` 4/4 healthy on WSL dockerd 29.1.3, `/health` OK, alembic head `20260907_0003`, pgvector `0.8.6`. Resilience: `restart: unless-stopped` on all 4 services (verified live + smoke re-passed). See `reports/worker-b1-env.md` (addendum + resilience follow-up). Note: after an intentional `stop/kill`, re-run `up -d` (manual-stop flag). |
| BL-012 | P0 | Execute integrated pilot smoke and defect sweep | qa/integration | BL-010, BL-011 | completed | API happy path PASSED 10/10 first run 2026-09-08 via `docs/coordination/smoke-api.py` (register→JWT→upload→COMPLETED 5s→processes→analysis→DOCX). Zero API defects. Browser UI pass still manual follow-up. See `reports/worker-b2-smoke.md`. |
| BL-013 | P0 | Validate and harden real DOCX generation path | backend/qa | BL-007, BL-011 | completed | Proven 2026-09-08 in integrated env: `GET /analysis/{id}/docx` → 200, `PK` magic, 37151 bytes via active template path (inside B2 smoke). Browser-download confirmation left to manual UI pass. |
| BL-014 | P0 | Decide and codify public workflow identifiers | backend/frontend | BL-002, BL-012 | completed | Decided 2026-09-08: keep `task_id == document id` explicitly (single pipeline/analysis per document); codified in route docstrings, frontend polls canonical `taskStatusUrl`, contract updated. See `reports/worker-b4-identifiers.md`. |
| BL-015 | P0 | Implement template management MVP from the PRD | backend/frontend | BL-013 | planned | Add real DOCX template upload, listing, selection, and placeholder validation instead of relying only on `base_template.docx`. |
| BL-016 | P1 | Add Docling-based ingestion with Markdown persistence and fallback | backend/ai | BL-011, BL-012 | completed | Landed 2026-09-07 (A2): `DoclingExtractor` feature-flagged (`DOCLING_ENABLED`, default off), `documents.raw_text` + `structured_markdown` persisted via migration `20260907_0002`, analyzer prefers markdown, real-converter validation passed. See `reports/worker-a2-docling.md`. |
| BL-017 | P1 | Add document history, retention, and generated-file versioning | backend/frontend | BL-012, BL-015 | planned | Close the PRD gap around history, recovery, and generated-document tracking. |
| BL-018 | P1 | Add production observability and audit trail | platform/backend | BL-011, BL-012 | planned | Instrument workflow timing, queue failures, auth events, and analysis/DOCX outcome logs for supportability. |
| BL-019 | P1 | Move document artifacts to managed storage and formalize lifecycle rules | platform/backend | BL-013, BL-017 | planned | Replace purely local file assumptions with managed storage, cleanup rules, and recovery behavior appropriate for deployment. |
| BL-020 | P1 | Expose prompt customization and AI run settings | backend/frontend/product | BL-016 | planned | Add prompt/profile management requested by the PRD without regressing the stable default path. |
| BL-021 | P1 | Add batch processing for documents and generated defenses | backend/frontend | BL-017, BL-018 | planned | Support multi-document ingestion and grouped workflow monitoring. |
| BL-022 | P1 | Export analysis summaries in business-friendly formats | backend/frontend | BL-017 | planned | Add summarized exports distinct from the full defense DOCX flow. |
| BL-023 | P2 | Add jurisprudence enrichment to analysis results | ai/backend | BL-016, BL-020 | planned | Extend the analysis with related precedents and traceable legal references. |
| BL-024 | P2 | Add stronger security and governance controls | platform/backend/frontend | BL-018 | planned | Cover auditability, role-based access, and higher-assurance auth expectations from the PRD non-functional section. |

## Onda B/C Issue Tracker (2026-09-08)

| Issue | Scope | Status | Notes |
| --- | --- | --- | --- |
| #18 A6 | PII masking + prompt-injection defense | completed | `reports/worker-a6-security.md`; 64 passed, gate PASSED |
| #19 B1 | Normalize integrated runtime (BL-011) | completed | 4/4 healthy + `/health` + alembic head + pgvector `0.8.6`, all live. `reports/worker-b1-env.md` |
| #20 B2 | Smoke end-to-end + defect sweep (BL-010/012) | completed | API 10/10 first run via `docs/coordination/smoke-api.py`; browser UI pass still manual. `reports/worker-b2-smoke.md` |
| #21 B3 | Validate real DOCX in integrated env (BL-013) | completed | Real 37KB DOCX (`PK`) from canonical route inside B2 smoke |
| #22 B4 | Workflow identifiers (BL-014) | completed | `task_id == document id` codified. `reports/worker-b4-identifiers.md` |
| #23 B5 | Frontend hygiene + archive microharness docs | completed | Shared types/hook, real upload progress, archive. `reports/worker-b5-hygiene.md` |
| #24 C1 | Template management MVP (BL-015) | ready for Session C | Constraints in `handoff-c1-template-mvp.md` (B owns migrations/B4) |

## Recommended Handoff Order

1. Finish BL-011 before spending more time on UI-only fixes.
2. Run BL-012 and BL-013 together in the same integrated environment so smoke evidence and DOCX evidence come from one runtime.
3. Resolve BL-014 before expanding the public workflow surface any further.
4. Treat BL-015 as the remaining PRD-level must-have that is still absent from the product flow.
5. Start BL-016 only after the pilot path is stable enough to benchmark extraction quality against the current extractor.
6. Keep BL-017 through BL-024 behind the pilot closure wave unless the user explicitly chooses to broaden scope earlier.

## Notes For Incoming Workers

- Read `implementation-plan.md` first for phase intent and definitions of done.
- Read `acceptance-matrix.md` before claiming closure on any stabilization item carried over from BL-001 through BL-010.
- Read `reports/worker-bl-001-auth.md` before touching auth-related frontend code.
- Read `reports/worker-bl-002-backend-contract.md` before touching upload, tasks, processes, analysis, or DOCX flows.
- Read `reports/worker-bl-007-docx-flow.md` before changing document generation behavior.
- Read `reports/worker-bl-009-tests.md` before changing backend tests or test bootstrap assumptions.
- Use `api-contract.md` as the current contract snapshot, but update it if BL-014 changes public identifiers or if BL-015 changes the template workflow.
- Append each landed task to `integration-log.md` so the next worker has a chronological handoff trail.
- Preserve the current fallback extractor while BL-016 is in flight; do not make Docling a hard dependency until quality and runtime costs are validated.
