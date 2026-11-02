# Sessão 2026-10-04 — Onda 2B implementada e verificada + release 0.3.0 (tax@1.0.0 + administrative@1.0.0 + real_estate@1.0.0)

> Checkpoint gerado por `/checkpoint`. Fonte de verdade: arquivos + git, nunca memória do chat.

## Data

2026-10-04 (implementação + release) — sessão retomada de `2026-10-04-onda-2a-implementada.md`.

## Objetivo

Fechar a Onda 2 do Dossie Universal implementando `tax@1.0.0`, `administrative@1.0.0` e `real_estate@1.0.0` sobre a fundação 2A (`NormativeSource`, runner, flags), com competência datada, regra temporal versionada e cadeia registral verificável, e subir o release **0.3.0** — conforme `docs/superpowers/plans/2026-10-03-dossie-onda-2b-tax-administrative-real-estate.md` e spec §5–§10.

## O que foi feito (com caminhos e commits)

1. **Foundation 2B** — `backend/app/core/classification.py` (áreas `administrative` + `real_estate`, `tax` estendida com ICMS/ISS/IPTU/ITBI/IRPJ/PIS/COFINS/reforma) + flags `DOSSIER_MODULE_TAX/ADMINISTRATIVE/REAL_ESTATE=False` em `backend/app/core/config.py` + `backend/tests/test_onda2b_foundation.py` — commit `22ea805`.
2. **Módulo tax@1.0.0** — `backend/app/modules/tax/module.py` + `checklist.py` + `backend/evals/tax_cases.json` + `backend/tests/test_tax_module.py` (competência datada; reforma exige tabela de vigência/efeitos ancorada em `effective_from/effective_to` do `NormativeSource`; alíquota de outro ente recusada; prescrição/decadência sem marco → blocked) — commit `b0d8066`.
3. **Módulo administrative@1.0.0** — `backend/app/modules/administrative/module.py` + `checklist.py` + `backend/evals/administrative_cases.json` + `backend/tests/test_administrative_module.py` (notícia/denúncia/relatório preliminar ≠ sanção final; Lei 14.133 só com regime verificado, sem presunção a caso pretérito/ente) — commit `6e69650`.
4. **Módulo real_estate@1.0.0** — `backend/app/modules/real_estate/module.py` + `checklist.py` + `backend/evals/real_estate_cases.json` + `backend/tests/test_real_estate_module.py` (matrícula antiga ≠ titularidade atual, exige certidão atual; posse × domínio × obrigacional; área nunca "corrigida" pela imagem) — commit `d065992`.
5. **Integração 2B** — `backend/app/core/pipeline/orchestrator.py` (`_MODULE_FLAGS` + `_module_registry()` +3) + `backend/tests/test_onda2_regressions.py` (contracts+tax e corporate+real_estate sem duplicação, §9) + `src/components/dossier/sections/sections.tsx` (`ModuleResultsCards` generic) + `src/components/dossier/__tests__/DossierPage.test.tsx` (cartões contracts/tax/administrative/real_estate) — commit `d585691`.
6. **Release 0.3.0** — bump `3cbaca2` + tag **v0.3.0** + `docs/SESSION_STATE.json` atualizado em `d659778` (**HEAD atual**). 7 commits na 2B; `git status` limpo exceto `.opencode/MEMORY.md` (learnings) e untracked de sessão/`output/`/`tmp/`.

## Verificação (evidência)

- Suite 2B + regressões re-executada neste checkpoint: **27 passed in 15.46s** (`test_onda2b_foundation` + `test_tax_module` + `test_administrative_module` + `test_real_estate_module` + `test_onda2_regressions`).
- Total coletado: **387** funções `test_` em `backend/tests/` (release registrou "387 pytest, gates verdes").
- Corpus 2B: `backend/evals/{tax,administrative,real_estate}_cases.json` (6 casos §9 cada); universal gate PASS no release 0.3.0.
- UI: `DossierPage.test.tsx` assere os 4 cartões de módulo 2A/2B renderizando; cards genéricos via `ModuleResultsCards`.
- Sem migration nova: head alembic permanece `20261002_0013` (Onda 1/2A/2B inteiras no JSONB do artefato).
- vitest/eslint/tsc/build: registrados verdes no checkpoint anterior (não re-executado nesta estação); E2E Playwright não executado.

## Decisões / constraints do usuário (verbatim onde crítico)

- "Rollout de um módulo por vez": `DOSSIER_V3_ENABLED=false` e `DOSSIER_MODULE_<ID>=false` por padrão; produção inalterada até gate próprio + piloto.
- "Fonte local ausente → limitação + pergunta ao advogado, nunca regra federal aproximada (§8)" — tributo estadual/municipal sem fonte do ente = conclusão recusada.
- "Reforma tributária exige tabela de vigência e produção de efeitos por tributo e período; texto consolidado atual nunca substitui a regra do fato pretérito (§5)".
- "Competência do ente, jurisdição e data explícitas antes de aplicar qualquer regra (§9.3)".
- "Nenhuma alteração silenciosa do schema 3.0; extensão incompatível exigiria nova versão formal (spec §10)".
- "Falha de módulo vira blocked + limitação — nunca impede o dossie universal nem o outro módulo do par".
- "Notícia/denúncia/relatório preliminar tratado como sanção final" e "matrícula antiga como titularidade atual" são proibidos (§6/§7).
- ".env nunca versionado; PAT do GitHub ainda pendente de rotacao".

## Andamento (feito vs pendente)

- **Feito**: Onda 2 completa — 2A (contracts+corporate) + 2B (tax+administrative+real_estate) + regressões cruzadas + cards de ativação; release 0.3.0 (tag v0.3.0, HEAD `d659778`); 387 pytest; 10 flags de módulo off por padrão.
- **Pendente**: rotação do PAT; migrations + smoke na VPS (in loco); gates jurídicos humanos por módulo (2 revisores/área); shadow runs V3 + piloto 50 execuções; habilitar flags uma a uma (ordem sugerida contracts → corporate → tax → administrative → real_estate); Onda 3.

## Próximos passos

1. Operador: rotação do PAT do GitHub (VPS → SSH deploy key; dev → fine-grained PAT) conforme `docs/runbooks/rotacao-pat-2026-10-02.md`; conferir remote `schinasergio` (https, auth falha com "Invalid username or token").
2. Operador (in loco, VPS): `pg_dump` + aplicar migrations (head `20261002_0013` — 2B não adicionou migration) + smoke pós-deploy 12 blocos A–K (`docs/operacao/smoke-pos-deploy-2026-10-02.md`).
3. Gate jurídico humano por módulo da Onda 2 (spec §9): 2 revisores da especialidade — precisão factual, cobertura, temporalidade, pertinência normativa, utilidade da ação; sem % de êxito.
4. Shadow runs V3 + piloto 50 execuções; habilitar `DOSSIER_MODULE_<ID>` um por vez após gate próprio.
5. Após piloto Go + gates jurídicos: planejar Onda 3.

## Bloqueadores

- PAT do GitHub exposto em `78c3e36` ainda sem rotação (segurança pré-piloto); remote https `schinasergio` rejeita auth.
- VPS não acessível desta estação (Windows) — deploy/smoke rodados in loco.
- E2E Playwright não executado (sem browsers/ambiente de teste).
- Gate jurídico humano por módulo pendente (2 revisores por área, processo fora da máquina).

## Riscos

- Habilitar flags antes do gate jurídico/piloto = anunciar capacidade sem evidência (viola "não anunciar análise completa").
- Alíquota/prazo aproximado de outro ente em caso 2B = falso positivo tributário (gate recusa, manter).
- Regressão silenciosa do schema 3.0 se próxima onda estender contrato sem nova versão formal.
- Checkpoint anterior (d659778) atualizou só o campo `status` do SESSION_STATE.json — `git_state.head`/`next_steps` ficaram stale e foram corrigidos neste checkpoint.

## Arquivos de referência

- Plano 2B: `docs/superpowers/plans/2026-10-03-dossie-onda-2b-tax-administrative-real-estate.md`
- Plano 2A: `docs/superpowers/plans/2026-10-03-dossie-onda-2a-contracts-corporate.md`
- Spec: `docs/superpowers/specs/2026-10-02-dossie-onda-2-design.md`
- Runbook PAT: `docs/runbooks/rotacao-pat-2026-10-02.md` · Smoke: `docs/operacao/smoke-pos-deploy-2026-10-02.md`
