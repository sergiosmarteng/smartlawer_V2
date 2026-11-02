# SmartLawer V2 — Sessão 2026-09-25 (checkpoint)

## Dados

- **Data:** 2026-09-25 (checkpoint atualizado ao final do ciclo)
- **Projeto:** SmartLawer V2 — legal-tech SaaS (RAG jurídico pt-BR)
- **Raiz do repo:** `...\Projetos protipos\SmartLawer_V2` (git; contém `smartlawer_V2/` como submódulo)
- **Código real:** `smartlawer_V2/` (submódulo) — backend FastAPI + Celery + pgvector + Redis, frontend Next.js
- **Produção:** `https://smartlawer.com.br/` (VPS Oracle 164.152.35.112, docker compose, SSL ECDSA válido até 23/12/2026)

## Objetivo da sessão

Continuidade do SmartLawer V2 após o ciclo 2026-09-24 (landing BL-028 publicada, chat fix dd80aee, Docling ativo) + **ciclo de análise de petições**: figuras da petição listadas/exibidas na página de análise e helpers de teste compatíveis com Celery real e stub.

## O que foi feito (registrado via git/docs)

### Ciclo anterior (já em produção)
- **Landing pública (BL-028)** — `smartlawer_V2/src/components/landing/` consumida por `src/pages/index.tsx`; identidade verde/marfim/dourado; verificação tsc/lint/build/prod OK; release note `smartlawer_V2/docs/implementation/landing-release-20260924.md`
- **Bug chat sem resposta (dd80aee)** — stream SSE sempre termina com `done` (`backend/app/api/routes/chat.py`) + erro visível no frontend (`src/pages/chat.tsx`)
- **Docling ativo** — A/B 645KB: markdown 99% dos caracteres, ~3min 1ª conversão; `libgl1 libglib2.0-0` no Dockerfile do worker; `DOCLING_ENABLED=true`
- **Conversão clara total (93c5284)**, auth single-worker/dual login (1ad37b8), embeddings provider-aware (20a2beb)

### Ciclo atual — 2026-09-25 (commits NOVOS no submódulo, ainda não bumped na raiz)
- **`ccf4fad` feat(figuras): listar e exibir figuras da petição na página de análise** (+842/-11, 14 arquivos)
  - Infra: migração `backend/alembic/versions/20260925_0007_document_figures.py` + model `backend/app/models/document_figure.py` + `crud/figure.py` (+72)
  - Extração: `backend/app/core/docling_extractor.py` (+201) — figuras extraídas durante Docling; `storage.py` (+20); task `backend/app/tasks/document_tasks.py` (+36)
  - API: `routes/documents.py` (+40), `routes/workflow.py` (+31), `schemas/workflow.py` (+11)
  - Frontend: `src/pages/analysis/[id].tsx` (+139) exibe as figuras; `src/types/workflow.ts` (+22)
  - Testes: `backend/tests/test_figures.py` (+186)
- **`cd9c8e5` fix(tests): helpers do pipeline compatíveis com Celery real e stub (.func/.run)**
  - `backend/tests/test_docling_extraction.py` (+12/-3) e `backend/tests/test_figures.py` (+31/-23): helpers expõem `.func`/`.run` para valer com Celery real e stub; mock de tarefa pontual em vez de pular o pipeline
- **Spec/local de apoio:** `tmp/analysis-spec/` com `petition-pages.json`, `petition-text.txt` e `source-03..06.png` (material da petição real usado no desenvolvimento/regressão)

### Estado git no checkpoint
- Raiz: último commit `cdf705e chore: bump smartlawer_V2 (landing clara + docling)` (24/09)
- Submódulo: HEAD `cd9c8e5` — **2 commits à frente do ponteiro na raiz** (` M smartlawer_V2`)
- `smartlawer_V2/docs/implementation/landing-release-20260924.md` ainda **untracked** no submódulo

## Decisões / constraints (verbatim)

- Landing **não promete** percentuais de produtividade nem cobertura integral de jurisprudência.
- Ativação/rollback: release note de 24/09 manda usar `docker compose -f docker-compose.prod.yml` com `--no-deps`; "Não foram executadas migrações nem reiniciados API, worker, banco ou Redis nesta entrega."
- Regra geral do projeto (CONSTITUTION): auditoria 100%; HITL — `ai_draft` + `requires_human_review`, proibição de protocolo automático; sem push/merge direto no GitHub para mudanças de landing (entrega via tar na VPS desta vez).
- `.env` não versionado (contém segredos; `.gitignore` como contenção — **PAT do GitHub ainda pendente de rotação**).
- Submódulo `smartlawer_V2` avança com bumps na raiz (`chore: bump smartlawer_V2 (...)`).
- Feature nova (figuras) segue o padrão do repo: migração alembic + model + crud + rota + task no worker + página Next; testes do pipeline devem rodar com Celery real E stub (helpers `.func`/`.run`).

## Andamento

### Feito
- [x] Landing pública no ar (BL-028) — prod validada (24/09)
- [x] Chat responde sempre (stream com `done` + erro visível) — dd80aee
- [x] Docling ativo em produção com fallback
- [x] **Figuras da petição: extração + API + página de análise** — ccf4fad (no submódulo)
- [x] **Testes do pipeline compatíveis com Celery real e stub** — cd9c8e5 (no submódulo)

### Pendente
- [ ] Bump na raiz dos 2 commits novos (ccf4fad, cd9c8e5) → `chore: bump smartlawer_V2 (figuras + testes celery)`
- [ ] Commit/registro do `docs/implementation/landing-release-20260924.md` (untracked no submódulo) + incluir no bump
- [ ] Rotacionar PAT do GitHub vazado + purgar histórico (`78c3e36`) — BL-024 still open
- [ ] Validar figuras em produção (análise de petição com figuras) após release
- [ ] Browser UI smoke integrado (smoke B2) — pendente operador

## Próximos passos (sugeridos)

1. Bump na raiz do submódulo: commit do `landing-release-20260924.md` + `chore: bump smartlawer_V2 (figuras + testes celery)` em `cdf705e`→`cd9c8e5`
2. Rotacionar o PAT do GitHub (novo token, remotes/deploy keys, purgar histórico do antigo)
3. Release + validação em produção da página de análise com figuras (e/ou smoke B2 manual no navegador)

## Bloqueadores

- Nenhum ativo. Docker não roda direto no Windows (regra: validações docker via WSL) — só afeta validações locais.

## Riscos

- PAT do GitHub vazado no histórico (segurança) — ação prioritária.
- Docling: ~3min para conversão na 1ª vez (lazy/low latency; otimização futura possível).
- Landing alterada sem merge no GitHub (árvores locais/VPS divergem do remoto — sync pendente no próximo bump).
- Migração `20260925_0007_document_figures` ainda não validada em produção (vai junto com o próx. bump/release).