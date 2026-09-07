# SmartLawer_V2 90-Day SaaS Plan

Date: April 7, 2026
Goal: Move SmartLawer_V2 from prototype to a production-ready SaaS foundation for the Brazilian legal market.

## Outcomes by Day 90

1. Stable end-to-end workflow:
- Upload petition -> extraction -> AI analysis -> defense draft generation -> download/history.

2. Production baseline:
- Auth unified, API contracts stable, migrations and CI/CD working, observability in place.

3. Compliance and trust baseline:
- LGPD operations, audit trail, retention controls, incident playbook.

4. Commercial SaaS baseline:
- Multi-tenant model, plans/limits, billing-ready foundation, support operations.

## Team Assumption (Lean)

- 1 Backend Engineer
- 1 Frontend Engineer
- 1 Full-stack/Integration Engineer
- 1 DevOps/SRE (part-time)
- 1 Product/QA (part-time)
- 1 Legal domain reviewer (part-time)

## Phase Plan (13 Weeks)

## Weeks 1-2: Stabilization and Contract Freeze

Objectives:
- Resolve frontend/backend mismatches.
- Pick one auth strategy and remove split implementations.
- Establish reliable local and CI execution.

Deliverables:
1. API contract document + OpenAPI lock.
2. Unified endpoint paths in frontend and backend.
3. Passing baseline tests and lint in CI.
4. Alembic migration strategy finalized and first migration baseline generated.

Exit criteria:
- User can authenticate, upload, view processing status, view analysis with no mocked calls.

## Weeks 3-4: Core Workflow Completion (MVP)

Objectives:
- Finish missing backend routes and task lifecycle.
- Implement robust task status polling and result retrieval.

Deliverables:
1. `analyses` endpoints completed.
2. `tasks` endpoints completed (status/progress/result).
3. Template CRUD flow completed.
4. Generated documents history + secure download endpoint.

Exit criteria:
- End-to-end happy path works in staging with real data.

## Weeks 5-6: Docling Integration (Phased)

Objectives:
- Integrate Docling in extraction pipeline with safe fallback.
- Benchmark impact on legal documents.

Deliverables:
1. Feature-flagged Docling extraction adapter in worker.
2. Structured conversion outputs persisted (markdown/json metadata).
3. Prompt updates to consume structured input.
4. Benchmark report with quality and latency comparisons.

Exit criteria:
- Docling path meets quality threshold and can be enabled gradually.

## Weeks 7-8: Security, LGPD, and Reliability Baseline

Objectives:
- Implement production security controls and compliance operations.

Deliverables:
1. Secret management and key rotation policy.
2. RBAC hardening and route protection coverage.
3. Immutable audit logs for sensitive actions.
4. Data retention/deletion workflow and DSAR operational endpoints.
5. Incident response runbook and alerting.

Exit criteria:
- Internal security checklist passed; LGPD operational process documented and test-run.

## Weeks 9-10: SaaS Core (Tenancy, Plans, Billing Readiness)

Objectives:
- Build commercial foundation for real clients.

Deliverables:
1. Tenant model and data isolation rules.
2. Subscription plans/limits (documents, storage, users, AI credits).
3. Billing integration foundation (provider adapter + invoice metadata pipeline).
4. Admin console basics (usage, limits, account state).

Exit criteria:
- One tenant can be onboarded with plan limits enforced.

## Weeks 11-12: Observability, Performance, and Beta Hardening

Objectives:
- Prepare for pilot clients with operational confidence.

Deliverables:
1. Metrics dashboards (API latency, queue depth, extraction errors, LLM failures).
2. Error monitoring and tracing.
3. Load/performance tests on representative legal workloads.
4. Backup/restore and disaster recovery drill.

Exit criteria:
- SLOs defined and monitored in staging; runbooks validated.

## Week 13: Launch Readiness and Pilot Rollout

Objectives:
- Execute controlled go-live with early adopters.

Deliverables:
1. Go-live checklist signed off.
2. Pilot onboarding kit (support, training, FAQ, legal disclaimers).
3. Post-launch KPI dashboard (adoption, quality, failures, churn signals).

Exit criteria:
- 5 to 15 pilot users onboarded and actively processing real cases.

## Prioritized Backlog (Must-Have)

1. API and UI contract unification.
2. Auth unification (single provider + clear token/session model).
3. Task lifecycle endpoints and robust status state machine.
4. Docling integration with fallback and metrics.
5. Multi-tenant data model and isolation enforcement.
6. Security hardening and audit logs.
7. CI/CD with automated quality gates.
8. Observability and on-call runbooks.

## Suggested KPIs for 90 Days

Product:
- End-to-end completion rate >= 95%.
- Median petition processing time <= 3 minutes (target corpus dependent).

Quality:
- >= 20% improvement in legal reviewer score after Docling integration.
- < 3% critical extraction failures.

Reliability:
- API uptime >= 99.5% in pilot period.
- Mean time to detect (MTTD) incidents < 10 minutes.

Business:
- Pilot weekly active usage >= 70%.
- First paid conversion readiness package complete.

## Risks and Mitigations

1. Scope overload
- Mitigation: strict weekly scope gates and backlog freeze per sprint.

2. Infra cost growth (OCR + conversion + LLM)
- Mitigation: queue controls, caching, plan limits, workload profiling.

3. Compliance delays
- Mitigation: treat LGPD operations as product features, not documentation only.

4. Quality drift from model/provider changes
- Mitigation: pinned model strategy + regression corpus + evaluator review loop.

## Day-90 Readiness Checklist

1. End-to-end legal flow tested in staging and pilot.
2. Security and compliance controls operational.
3. Tenant and plan controls active.
4. Monitoring, alerting, backups, and incident runbooks proven.
5. Pilot clients onboarded with support process running.

## Immediate Next 7 Days

1. Freeze and fix API contracts.
2. Remove auth duality and select one path.
3. Implement task status endpoints and UI wiring.
4. Start Docling proof-of-value benchmark on a curated legal corpus.
