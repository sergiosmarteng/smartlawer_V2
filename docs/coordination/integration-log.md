# Integration Log

This file is append-only. Add one short entry per landed worker or coordinator merge step.

## 2026-05-11

### BL-001 landed

- Source: `reports/worker-bl-001-auth.md`
- Scope: consolidated frontend auth around backend JWT and `/users/me`
- Workspace impact:
  - login and sign-up now honor `next`
  - middleware protects `/dashboard`, `/upload`, `/analysis`, `/user-profile`
  - profile page reads backend user data
  - SuperTokens surface is now compatibility-only
- Follow-up carried forward:
  - clear mirrored auth cookie in the shared Axios 401/403 path
  - revisit cookie strategy if server-managed sessions are introduced

### DOC-001 landed

- Scope: created coordination docs for backlog, contract snapshot, and handoff logging
- Workspace impact:
  - `backlog.md` now reflects BL-001 as completed
  - `api-contract.md` captures the current workflow shape from the workspace
  - this log can now be extended as BL-002, BL-005, BL-006, BL-007, BL-008, and BL-009 land
- Assumptions to revisit:
  - upload/task contract after BL-002
  - final analysis payload after BL-006
  - sensitive route protection notes after BL-008

### BL-002 and BL-008 landed

- Source: `reports/worker-bl-002-backend-contract.md`
- Scope: stabilized backend workflow/status/document-generation contract and verified sensitive-route auth protection
- Workspace impact:
  - upload now returns explicit follow-up metadata including `task_id` and `taskStatusUrl`
  - workflow-facing statuses are normalized to `PENDING`, `PROCESSING`, `COMPLETED`, and `FAILED`
  - analysis and DOCX routes accept either `analysis_id` or `document_id`
  - sensitive routes were verified as protected across documents, workflow, and template download endpoints
- Follow-up carried forward:
  - BL-005, BL-006, and BL-007 should build on this backend contract rather than inventing new routes
  - runtime validation still depends on normalizing the backend environment and dependencies

### BL-009 landed

- Source: `reports/worker-bl-009-tests.md`
- Scope: stabilized backend tests for auth, documents, and workflow routes
- Workspace impact:
  - local route-level tests now use a disposable SQLite-backed harness
  - focused coverage exists for auth, upload validation, process listing, task status, analysis detail, and DOCX download
- Follow-up carried forward:
  - add a separate integration layer later for real Postgres, Redis, Celery, OCR, AI, and DOCX runtime dependencies

### BL-007 landed

- Source: `reports/worker-bl-007-docx-flow.md`
- Scope: hardened DOCX generation and improved fallback analysis data for document rendering
- Workspace impact:
  - document generation now normalizes mixed payload values before rendering the template
  - DOCX errors are clearer when template load, render, or save steps fail
  - analyzer fallback behavior is more likely to leave a renderable payload for `/analysis/{id}/docx`
- Follow-up carried forward:
  - keep future template placeholder expansion inside the normalization layer when possible
  - verify temp-file write assumptions in the deployment environment during final smoke

### QA smoke prep landed

- Source: `reports/worker-qa-smoke-prep.md`
- Scope: added a manual pilot smoke checklist and acceptance notes for the integrated v1 flow
- Workspace impact:
  - `smoke-checklist.md` now defines the operator path from auth through DOCX download
  - the stabilization report now references manual smoke expectations and open worker dependencies
- Follow-up carried forward:
  - re-run the checklist only after BL-007 DOCX hardening is merged in the shared environment
  - treat BL-009 backend-test stabilization as required evidence before pilot sign-off

### Integration review captured

- Source: `reports/worker-integration-review.md`
- Scope: reviewed the in-flight stabilization work across auth, frontend workflow, backend contract, DOCX generation, and route-level tests
- Workspace impact:
  - no code changes requested from review alone
  - coordinator findings are now consolidated in `review-findings.md`
  - the current branch has no P0 blockers recorded from this review pass
- Follow-up carried forward:
  - clear the mirrored auth cookie on the shared `401/403` path
  - surface structured "analysis not ready" metadata on the frontend
  - preserve `next` across sign-in/sign-up cross-navigation

### Coordinator validation and follow-up fixes

- Source: coordinator local integration pass
- Scope: addressed the review findings that could be closed without reopening larger architecture work
- Workspace impact:
  - shared Axios `401/403` cleanup now removes the mirrored auth cookie as well as `localStorage`
  - sign-in and sign-up cross-links now preserve `next`
  - the analysis page now surfaces structured "analysis not ready" metadata from the backend
  - local validation passed with `npx tsc --noEmit`, targeted `next lint`, and `pytest backend/tests -q --basetemp C:\tmp\pytest-final -p no:cacheprovider`
- Follow-up carried forward:
  - BL-007 still needs a real DOCX runtime download check
  - BL-010 still needs the integrated manual smoke execution

## 2026-09-08

### C4 landed — observability + RBAC (Onda C)

- Source: `reports/worker-c4-audit-rbac.md`
- Scope: issue #27 / BL-018 + BL-024 (DoD: trilha consultável)
- Workspace impact:
  - NEW `audit_events` (migration `20260908_0006`, live); best-effort hooks on auth/upload/generate/template/prompt/chat/worker-completion (timing + failure excerpts, no raw user content)
  - `GET /audit` (own + filters, `scope=all` admin) + `GET /ops/summary` (admin); `role` gate + escalation guard; `/audit` page
  - 2FA deferred with design sketch (half-2FA = security theater)
  - validation: 7 new tests (suite 99 passed), tsc/eslint clean, WSL live 11/11, B2 re-passed 10/10
- Follow-up carried forward:
  - promote admins via SQL (`UPDATE users SET role='admin' …`); rotate leaked PAT (still open)

### C3 landed — prompts/batch/summary exports (Onda C)

- Source: `reports/worker-c3-prompts-batch-export.md`
- Scope: issue #26 / BL-020 + BL-021 + BL-022 (each capability tested)
- Workspace impact:
  - NEW `prompt_profiles` (migration `20260908_0005`, live) + CRUD-lite + default wiring into the worker (legacy prompt byte-identical without profile); `/prompts` page
  - `POST /documents/batch-upload` (≤10, `{items, errors}`); upload page multi-select follows first item
  - `GET /analysis/{id}/summary.md` + UI button
  - validation: 11 new tests (suite 92 passed; one docling-stub signature update), tsc/eslint clean, WSL live 7/7, B2 re-passed 10/10
- Follow-up carried forward:
  - worker profile guidance needs real AI keys for end-to-end prompt proof (unit-covered only)

### C2 landed — history/retention/managed storage (Onda C)

- Source: `reports/worker-c2-versions.md`
- Scope: issue #25 / BL-017 + BL-019; versioned DOCX generations + lifecycle
- Workspace impact:
  - NEW `generated_documents` (migration `20260908_0004`, auto-applied live); every generate persists a versioned copy under managed `uploads/generated/` + `GENERATED_KEEP_LATEST` retention; persistence never fails downloads
  - NEW `GET /analysis/{id}/versions` + `/versions/{v}` (tenant-checked recovery); versions picker on analysis page
  - validation: 5 new tests (suite 81 passed), tsc/eslint clean, WSL live 7/7, B2 smoke re-passed 10/10
- Follow-up carried forward:
  - retention trim proven live only at default KEEP=10 (KEEP=2 path in sqlite tests)
  - import-time `datetime.now()` latent bug remains in 4 other models

### C1 landed — template management MVP (Onda C)

- Source: `reports/worker-c1-templates.md`
- Scope: issue #24 / BL-015; upload/list/select/validate for DOCX templates
- Workspace impact:
  - backend: `POST`+`GET /api/v1/templates`, `?template_id=` on both DOCX routes (404 foreign, 422 naming `unsupported_placeholders`); stdlib Jinja discovery (split-run/loop/filter aware) in `DocxGenerator`; B4 dual-lookup + default base path preserved
  - incidental 1-line fix: `Template.created_at` import-time default → per-row (same latent bug noted in 4 other models, left for follow-up)
  - frontend: template picker + `.docx` upload + 422 surfacing on the analysis page; `UserTemplate` shared type
  - validation: 11 new tests (suite 76 passed), tsc/eslint clean, WSL live 12/12, B2 smoke re-passed 10/10
- Follow-up carried forward:
  - template DELETE/detail endpoints deferred (MVP minimum)
  - close #24 with the report link; #19/#20/#21 still OPEN (evidence local, needs comment + close)

### B1 resilience — restart policy on all services (Onda B)

- Source: `reports/worker-b1-env.md` (resilience follow-up)
- Scope: `docker-compose.yml` only change — `restart: unless-stopped` on api/worker/db/redis
- Workspace impact:
  - `config` valid; `up -d` recreated 4/4 `healthy`; policy confirmed via `docker inspect`; `/health` OK
  - B2 smoke re-ran PASSED 10/10 on the final recipe (fresh-user isolation held)
  - Windows sleep-on-AC is already `never`; WSL poweroffs track host idle — policy covers daemon/WSL reboots
  - caveat: after intentional `stop/kill`, re-run `up -d` (daemon manual-stop flag)
- Follow-up carried forward:
  - operator end-to-end daemon test still open (needs WSL sudo): `sudo systemctl restart docker` → stack must return alone

### B1 completed — all-healthy live stack on WSL (Onda B)

- Source: `reports/worker-b1-env.md` (completion addendum)
- Scope: issue #19 / BL-011; `docker compose up -d` on native WSL dockerd 29.1.3
- Workspace impact:
  - api/db/redis/worker all `healthy` (stable 4+ min); `/health` OK; `celery inspect ping` → pong
  - alembic full chain at startup, head `20260907_0003`; live pgvector `0.8.6`, `raw_text`/`structured_markdown` columns, HNSW + FTS indexes
  - no app-code changes; recipe file untouched since the partial landing
- Follow-up carried forward:
  - WSL guest poweroffs on host idle kill `dockerd`; stack has no `restart:` policy (recommend `restart: unless-stopped` or keep host awake during validation)
  - B2 smoke ran immediately on this stack (see below)

### B2 landed — API pilot smoke PASSED 10/10 (Onda B)

- Source: `reports/worker-b2-smoke.md`
- Scope: issues #20/#21 / BL-012 + BL-013; API happy path on the live B1 stack
- Workspace impact:
  - NEW `docs/coordination/smoke-api.py`: stdlib-only, self-generates a text PDF; PASSED 10/10 first run (register → JWT → upload → COMPLETED ~5s → processes → analysis → DOCX 37KB `PK`)
  - `task_id == id` + canonical `taskStatusUrl` hold live (B4 contract proven at runtime)
  - no app-code changes
- Follow-up carried forward:
  - browser UI pass still manual (needs `npm run dev` + operator session before pilot signoff)
  - leaked GitHub PAT found tracked in `.env` (committed in `78c3e36`, present on `origin/main`) — rotate the token and purge history; `.env` added to `.gitignore` as containment only

### B5 landed — frontend hygiene + microharness docs archived (Onda B)

- Source: `reports/worker-b5-hygiene.md`
- Scope: issue #23; shared types/hook, real upload progress, archive
- Workspace impact:
  - `src/types/workflow.ts` (NEW): 6 contract interfaces + status helpers; kills 5 inline interfaces + 2 status-Set copies across upload/dashboard/analysis pages
  - `src/hooks/useTaskPolling.ts` (NEW): scheduler with unmount cleanup; page state machines unchanged
  - upload POST uses `onUploadProgress` (real 1–20% byte band); checkpoint dot lights at upload-accepted (≥24)
  - `docs/{TASKS,CHANGELOG}.md` → `docs/archive/microharness-*` + README (nothing referenced them)
  - validation: `tsc` clean, targeted `next lint` clean, `next build` compiled + static export OK (process exit hangs on this machine, artifacts prove success), `pytest` 65 passed
- Follow-up carried forward:
  - B1 live `up` healthy-state + B2 smoke + B3 DOCX proof all belong to WSL sessions (rule 7 — no docker on Windows)

### B1 landed — normalized integrated runtime recipe (Onda B)

- Source: `reports/worker-b1-env.md`
- Scope: issue #19 / BL-011; compose env parity, worker boot, healthchecks
- Workspace impact:
  - `docker-compose.yml`: shared `x-backend-env` (all Settings keys), optional `.env`, worker `-A app.worker:celery_app`, worker `inspect ping` healthcheck, `start_period`, parametrized ports
  - `.env.example` rewritten (was Clerk-only/stale); `Dockerfile` gains `PYTHONDONTWRITEBYTECODE`/`PYTHONUNBUFFERED`
  - `compose config` valid; backend image BUILD completed on daemon 29.1.2
  - `handoff-c1-template-mvp.md` published: Session C ownership + constraints (B owns migrations/B4-decision/contract-ack)
- Follow-up carried forward:
  - container-start evidence pending daemon recovery (wedged on multi-GB unpack; restart issued) — B2 resume steps in report
  - Session B owns alembic migrations while Onda B/C run in parallel

### A6 landed — PII masking + prompt-injection defense (Onda A RAG)

## 2026-09-07

### A1 landed — pgvector migration + document_chunks table (Onda A RAG)

- Scope: vector foundation for legal RAG; no retrieval/generation yet
- Workspace impact:
  - new `document_chunks` table: `document_id` (CASCADE), `user_id` tenant FK, `matter_id`, `chunk_index`, `content`, pages, token count, `embedding VECTOR(1536)`, `embedding_model/_version`, HNSW cosine index + tenant/matter indexes
  - alembic `20260407_0001 -> 20260907_0001` renders offline-verified SQL (`CREATE EXTENSION vector`, `VECTOR(1536)`, `USING hnsw ... vector_cosine_ops`)
  - `db` image `postgres:15-alpine -> pgvector/pgvector:pg15`; `pgvector==0.5.0` pinned; embedding settings in `config.py`
  - `REQUIRED_TABLES` repair covers `document_chunks`; sqlite tests map `VECTOR -> JSON`
  - suite: `18 passed` (12 existing + 6 new in `tests/test_document_chunks.py`: DDL, CRUD/ordering, tenant isolation)
- Follow-up carried forward:
  - A2 Docling ingestion writing into `document_chunks`; live pgvector validation needs Docker daemon running (was down on dev machine)

### A2 landed — Docling ingestion feature-flagged (Onda A RAG)

- Source: `reports/worker-a2-docling.md`
- Scope: BL-016 + issue #14; minimum viable Docling per `docling-status.md`
- Workspace impact:
  - `DoclingExtractor.extract_markdown()` (lazy singleton, never raises) wired via `prepare_analysis_input()`: markdown wins when `DOCLING_ENABLED=1`, else `raw_text` fallback
  - `documents.raw_text` + `structured_markdown` persisted (migration `20260907_0002`)
  - `docling==2.94.0` pinned; Dockerfile gains `tesseract-ocr-por/-eng`
  - suite: `24 passed` (18 before + 6 new); real-converter validation passed on dev machine
  - docs: `docling-status.md`, `api-contract.md`, `backlog.md` BL-016 → completed
- Follow-up carried forward:
  - A3 chunker + embedding service to fill `document_chunks`; live Docker/pgvector validation still pending

### A3 landed — hybrid retrieval (Onda A RAG)

- Source: `reports/worker-a3-retrieval.md`
- Scope: issue #15; chunker jurídico + embeddings + híbrido vetor/FTS/RRF + rerank opcional
- Workspace impact:
  - `legal_chunker` (Art./§/Súmula-aware, 1000/150 tokens), `embeddings` (OpenAI batch, skip sem chave), `retrieval.hybrid_search` (tenant pré-filtrado + dupla barreira, FTS-only fallback)
  - worker indexa chunks idempotente após COMPLETED, sem nunca falhar o task
  - migração `20260907_0003` (GIN FTS português); `cohere==7.1.1`; suite: `39 passed` (24 antes + 15 novos)
- Follow-up carried forward:
  - A4 chat SSE + UI citações; live pgvector/FTS/Cohere pendente de Docker + chaves

### A5 landed — eval gate + human-in-the-loop (Onda A RAG)

- Source: `reports/worker-a5-eval.md`
- Scope: issue #17; golden 30 + gate 0.85 + HITL
- Workspace impact:
  - `evals/` (golden, corpus, `run_gate.py` exit-code p/ CI) + `eval_scoring` determinístico (faithfulness/relevância/recall, abstenção correta = 1.0)
  - gate atual: `mean_faithfulness=0.967 PASSED`; g09 documentado como miss de retrieval (canário p/ híbrido real)
  - HITL: `ai_draft` + `requires_human_review` na API/SSE + runbook com 4 gates e proibição de protocolo automático
  - CI: imagem `pgvector:pg15` + etapa do gate; conftest remove HNSW em test DBs (portabilidade)
  - suite: `57 passed` (47 antes + 10 novos)
- Follow-up carried forward:
  - Onda B (B1 ambiente integrado); upgrade LLM-judge futuro sem mudar o contrato

### B4 landed — workflow identifiers codified (Onda B)

- Source: `reports/worker-b4-identifiers.md`
- Scope: BL-014 + issue #22
- Workspace impact:
  - decisão: manter `task_id == document id` explicitamente (single pipeline/analysis)
  - docstrings nas rotas, frontend usa `taskStatusUrl` canônico, contrato atualizado
  - teste de identidade + 404 cross-user; `tsc`/eslint limpos
- Follow-up carried forward:
  - B1 validação WSL retomada: usuário liberou disco (C: 4.4GB → 73GB).
    db/redis healthy, extensão vector 0.8.6 verificada. Retry do build da
    API no daemon WSL nativo; smoke B2 na sequência.

### A6 landed — PII masking + prompt-injection defense (Onda A RAG)

- Source: `reports/worker-a6-security.md`
- Scope: issue #18; PII masking em logs/traces, classificacao de input, separacao instrucao/dado
- Workspace impact:
  - `security_rag` deterministico (CPF/CNPJ/email/telefone/OAB/CNJ + classifier PT/EN com safe-harbor) sem dependencias novas
  - prompt grounded isola trechos como DADOS; query maliciosa bloqueada antes de retrieval/LLM (non-stream + stream), sem vazar PII em logs
  - suite: `64 passed` (57 antes + 7 novos); eval gate segue `PASSED`
- Follow-up carried forward:
  - Onda B (B1 ambiente integrado); redacao de PII em excerpts fica p/ B2/C4 se LGPD exigir; upgrade LLM-judge futuro sem mudar o contrato

### A4 landed — grounded chat com citações (Onda A RAG)

- Source: `reports/worker-a4-chat.md`
- Scope: issue #16; `POST /api/v1/chat` + `/chat/stream` (SSE), tenant do JWT, `document_id` opcional validado
- Workspace impact:
  - `rag_answer` grounded (`[N]` obrigatório, fallback "não encontrei"); citações estruturadas com página/excerpt
  - frontend `/chat` streaming + fontes clicáveis → `/analysis/{id}`; nav + middleware atualizados
  - suite: `47 passed` (39 antes + 8 novos); `tsc` limpo; eslint limpo nos alterados
  - fix incidental: 2 erros TS2322 pré-existentes no Header (`logout` handler)
- Follow-up carried forward:
  - A5 golden + RAGAS; live LLM/SSE com chave real; `npm run lint` full trava no ambiente
