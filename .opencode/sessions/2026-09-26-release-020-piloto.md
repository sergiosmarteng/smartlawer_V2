# SmartLawer V2 — Release 0.2.0 + hotfixes em prod (2026-09-26)

## Data / sessão
- Data: 2026-09-26 (checkpoint `/checkpoint`).
- Continue de: `.opencode/sessions/2026-09-25-analise-v2-t01.md` (épico V2 T01–T14, branch `feat/analise-juridica-v2`) e `2026-09-25-smartlawer-landing-chat-checkpoint.md`.

## Objetivo
Concluir o épico "análise jurídica V2" (T01–T14), publicar release 0.2.0 na VPS com rollback planejado e deixar o fluxo pronto para validação do operador e piloto real.

## O que foi feito (com caminhos)
- **Épico V2 mergeado**: `8b3ab0e` Merge `feat/analise-juridica-v2` → `main` (submódulo `smartlawer_V2/`); tag anotada `v0.2.0`; bump no root `eeae7b3 chore: bump smartlawer_V2 (release 0.2.0 analise juridica V2)`. Constraint de branching cumprida ("bump na raiz só no merge").
- **Release notes / procedimento VPS**: `smartlawer_V2/docs/implementation/release-0.2.0-vps.md` (commit `2c84ce7`) — backup pg_dump+snapshot, retag `before-v020`, `up --no-deps`, `alembic current` esperado `20260925_0010`, smoke checklist.
- **Incidente de modelo**: `01fc4ef` docs — `gemini-2.5-flash` aposentado; `CHAT_MODEL=gemini-3.8-flash` em prod.
- **Hotfix dossiê V2 (severidade alta)**: `4b79b20` Merge `fix/dossie-v2-document-id` — página legada liga `/analysis/v2/<document_id>?document_id=…` (routeId = document_id, não artifact_id); fix em `src/pages/analysis/v2/[id].tsx`: `resolveByDocument()` também no `catch` do fetch (404 com document_id resolve a última run publicada). Doc: `smartlawer_V2/docs/bugs/dossie-v2-document-id-20260926.md`. Contrato verde: `test_analysis_v2.py` 8 passed + `tsc`/`lint`/`build` 0.
- **Fix upload**: `6073b17` copy PT-BR por etapa com spinner de andamento (`src/pages/upload.tsx`, `backend/tests/test_upload_copy.py`).
- **Verificação pré-release 0.2.0 (exit 0)**: pytest 212 passed; `npx tsc --noEmit`, `lint`, `build` OK; benchmark sintético 30 casos 10/10 portões.
- Submódulo `main` atual: `fae6dfb`; root `main` em `eeae7b3`.

## Decisões / constraints do usuário (verbatim)
- "Landing não promete percentuais de produtividade nem cobertura integral de jurisprudência"
- "Rollback/ativação somente via docker compose -f docker-compose.prod.yml com --no-deps (release note 2026-09-24)"
- "Auditoria 100% + HITL: ai_draft/requires_human_review; proibição de protocolo automático (CONSTITUTION)"
- ".env nunca versionado; PAT do GitHub ainda pendente de rotação"
- "Testes do pipeline devem rodar com Celery real E stub (helpers .func/.run)"
- "V2 em feature branch feat/analise-juridica-v2; main do submódulo segue deployável; bump na raiz só no merge" — **cumprida** (merge em 2026-09-26)
- Novas (release 0.2.0): "Sem chave de IA, análises falham alto (PROVIDER_UNAVAILABLE) — comportamento novo e correto; conferir OPENAI/GEMINI/OPENROUTER_API_KEY + DOCLING_ENABLED no .env da VPS"; "Não anunciar 'análise completa': piloto (advogados + holdout) ainda pendente"; "CHAT_MODEL=gemini-3.8-flash em prod (gemini-2.5-flash aposentado)".

## Andamento
- Feito: épico T01–T14 (dossiê verificável + módulo trabalhista + API `/api/v2` + página `/analysis/v2/[id]`) → release 0.2.0 publicado; hotfix dossiê e fix upload em prod; verificação pré-deploy exit 0.
- Pendente: validação do operador no navegador; piloto real; rotação do PAT; smoke formal pós-deploy (conferir `alembic current` = `20260925_0010`).

## Próximos passos
1. Usuário valida no navegador: botão "Abrir dossiê V2" em qualquer documento analisado + copy PT-BR do upload (spinner) em prod.
2. Piloto real: rubrica 2 advogados + holdout + 50 execuções (controle de custo/limites).
3. Rotacionar PAT vazado (`78c3e36`) e purgar histórico.
4. Smoke formal do release na VPS conforme `release-0.2.0-vps.md` (backup já feito; conferir head de migração).

## Bloqueadores
- Nenhum ativo. Validação humana (passo 1) é pré-requisito para o piloto.

## Riscos
- Custo do piloto (50 execuções): medir antes de ampliar; worker concorrência = 2 (Docling ~3min na 1ª conversão).
- PAT exposto no histórico ainda sem rotação — janela de risco ativa.
- Falhas altas se chave de IA ausente no `.env` da VPS (comportamento novo e correto).