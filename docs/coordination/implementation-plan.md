# SmartLawer V2 Implementation Plan

Last updated: 2026-05-12
Scope: implementation plan for the remaining SmartLawer work based on the current codebase, `docs/product/PRD.md`, `docs/coordination/`, and the latest functional validation findings.

## Current Product State

- The current pilot flow is functionally shaped around `sign-in -> upload PDF -> task polling -> dashboard -> analysis detail -> DOCX download`.
- JWT auth, the workflow API contract, and the main frontend pages have already been stabilized enough for route-level validation and local type/lint/build checks.
- Backend route-level tests are healthy (`12 passed`), but they still rely on local test harness substitutes rather than the full runtime stack.
- The active ingestion pipeline is still `upload -> process_pdf_task -> PDFExtractor.extract_text() -> LegalAnalyzer.analyze_petition()`.
- OCR exists today through PyMuPDF plus Tesseract fallback in `PDFExtractor`, but Docling is not implemented and imported files are not being converted into persisted Markdown before they are sent to the AI layer.
- DOCX generation currently depends on a single managed template file, `backend/templates/base_template.docx`.

## Planning Assumptions And Gaps From The PRD

The PRD defines a broader product than the stabilized pilot currently delivers. The gaps below should remain visible while sequencing the next work:

- Real DOCX template upload, selection, and placeholder validation are still missing from the product flow even though template-driven defense generation is a PRD must-have.
- The product still lacks persistent history/versioning for generated documents, also called out in the PRD.
- Prompt customization, batch processing, analysis export, and jurisprudence enrichment are not yet implemented.
- Security and governance expectations from the PRD non-functional section, such as stronger auditability and role-aware controls, are not yet represented as product features.
- The current pilot assumes one default template is enough to validate the end-to-end workflow. That is acceptable for pilot closure, but it is not yet full PRD compliance.
- The current pilot also assumes the legacy raw-text extractor is sufficient until Docling is added behind a safe fallback path.

## Agent Execution Model

Each new agent should follow this handoff sequence before starting:

1. Read `docs/coordination/implementation-plan.md`.
2. Read `docs/coordination/backlog.md`.
3. Read the worker report(s) referenced by the backlog item being picked up.
4. Read `docs/coordination/acceptance-matrix.md` if the task closes or re-validates a stabilization item.
5. Write a new report under `docs/coordination/reports/` using `reports/TEMPLATE.md`.
6. **Commit local ao concluir a etapa (obrigatório, mínimo):** código + testes verdes + docs em commit local; sem push salvo pedido explícito do usuário.

Expected coordination behavior:

- Prefer one agent per backlog item or tightly coupled pair of items.
- When one agent finishes, the next agent should start from the previous report instead of re-discovering context.
- Any task that changes public workflow behavior must also refresh the relevant coordination docs before handoff.
- No stage is "done" without its local commit (rule 6 above); the commit hash goes into the worker report and `integration-log.md`.

## Phase 1: Pilot Closure And Runtime Proof

Goal: convert the stabilized code into a real, validated pilot path in one integrated environment.

Dependencies:

- BL-001 through BL-009 landed in the shared branch state
- an environment where frontend, backend, database, worker, Redis, OCR, and DOCX dependencies can run together

Primary backlog items:

- BL-011 Normalize integrated runtime environment for pilot validation
- BL-012 Execute integrated pilot smoke and defect sweep
- BL-013 Validate and harden real DOCX generation path
- BL-014 Decide and codify public workflow identifiers

Deliverables:

- one reproducible runtime recipe for local/shared validation
- one completed smoke report using `smoke-checklist.md`
- one defect sweep closing any blockers found in auth, upload, processing, dashboard, analysis, or DOCX download
- one final documented decision on whether task identifiers remain coupled to document identifiers

Definition of done:

- one user can complete `sign-in -> upload -> processing -> dashboard -> analysis -> DOCX download` without manual API intervention
- the backend runs with its real runtime dependencies rather than only the test harness substitutes
- `GET /tasks/{id}`, `GET /processes`, `GET /analysis/{id}`, and `GET /analysis/{id}/docx` are validated in the same environment
- pilot signoff evidence exists in coordination docs, not only in terminal output

## Phase 2: Complete The Remaining PRD Must-Haves

Goal: close the remaining core product gaps that are still below the PRD baseline even after the pilot flow is stable.

Dependencies:

- Phase 1 complete
- stable contract for identifiers and integrated file generation

Primary backlog items:

- BL-015 Implement template management MVP from the PRD
- BL-016 Add Docling-based ingestion with Markdown persistence and fallback

Deliverables:

- template upload, listing, selection, and validation flow exposed in product UX and backend APIs
- placeholder discovery or validation so unsupported templates fail clearly before generation
- feature-flagged Docling ingestion path that converts imported files into structured Markdown plus metadata before AI analysis
- persisted conversion artifacts so downstream agents or workers can inspect the extracted Markdown that the AI actually received

Definition of done:

- a user can choose between a stored template and an uploaded template for defense generation
- the system can explain template incompatibility before or during generation with actionable feedback
- Docling can be turned on for supported documents without breaking the current extractor fallback
- the analysis layer can consume Markdown-derived content and the conversion output is persisted for inspection

Docling status at plan time:

- Not implemented in the active pipeline.
- Not persisting `.md` conversion outputs today.
- Should be introduced as an additive path, not a replacement-first rewrite.

## Phase 3: Operational Hardening For Pilot Expansion

Goal: make the product supportable beyond a narrow pilot by improving storage, observability, and recovery behavior.

Dependencies:

- Phase 1 complete
- template and Docling decisions stable enough to define artifact lifecycle rules

Primary backlog items:

- BL-017 Add document history, retention, and generated-file versioning
- BL-018 Add production observability and audit trail
- BL-019 Move document artifacts to managed storage and formalize lifecycle rules

Deliverables:

- history view and backend tracking for generated documents and re-downloadable artifacts
- storage/lifecycle policy for uploaded PDFs, extracted Markdown, analysis outputs, and generated DOCX files
- operational dashboards or structured logs for queue failures, runtime timings, and auth-sensitive events

Definition of done:

- operators can answer what was uploaded, what was generated, and what failed for a user without digging through ad hoc logs
- generated-document history survives beyond the request that created it
- runtime incidents in OCR, AI analysis, queue processing, and DOCX generation are observable and traceable

## Phase 4: Product Expansion After Core Stability

Goal: deliver the higher-value PRD enhancements after the pilot path and operational base are stable.

Dependencies:

- Phases 1 through 3 complete
- enough workflow telemetry to know where quality improvements matter most

Primary backlog items:

- BL-020 Expose prompt customization and AI run settings
- BL-021 Add batch processing for documents and generated defenses
- BL-022 Export analysis summaries in business-friendly formats
- BL-023 Add jurisprudence enrichment to analysis results
- BL-024 Add stronger security and governance controls

Deliverables:

- configurable AI prompts or profiles with sensible defaults and guardrails
- batch upload/processing and grouped monitoring
- executive-style analysis exports separate from the final defense DOCX
- richer legal analysis with precedent support
- stronger product controls for governance-sensitive customers

Definition of done:

- each added capability has clear user-facing value, test coverage, and operational ownership
- new features do not bypass the stabilized workflow contract or the handoff documentation process

## Recommended Sequencing For Incoming Agents

1. Assign one platform/backend agent to BL-011.
2. As soon as BL-011 reports a runnable environment, assign one QA/integration agent to BL-012 and one backend agent to BL-013.
3. If BL-012 uncovers identifier confusion, assign BL-014 immediately before any new feature work.
4. After pilot closure, split Phase 2 into:
   - one template-flow agent for BL-015
   - one ingestion/AI agent for BL-016
5. Only after those are stable should the next wave fan out into BL-017 through BL-019.

## Explicit Answer On Docling

At the time of this plan, Docling is not implemented in the active SmartLawer pipeline and the system is not converting imported documents into `.md` artifacts for the AI flow.

What exists today:

- PDF text extraction via PyMuPDF
- OCR fallback via Tesseract when native text is insufficient
- raw extracted text sent into `LegalAnalyzer`

What still needs to be built:

- a Docling adapter or service integration
- Markdown and metadata persistence for each imported document
- routing of the Markdown output into the AI analysis step
- fallback behavior and quality comparison against the current extractor
