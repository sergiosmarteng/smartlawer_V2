# Sessão 2026-10-04 — Onda 2A implementada e verificada (contracts@1.0.0 + corporate@1.0.0)

> Checkpoint gerado por `/checkpoint`. Fonte de verdade: arquivos + git, nunca memória do chat.

## Data

2026-10-04 (implementação) — sessão retomada de `2026-10-04-onda-2-planejada.md`.

## Objetivo

Implementar a Onda 2A do Dossie Universal (foundation normativa + módulos `contracts` e `corporate` + integração atrás de flags) conforme `docs/superpowers/plans/2026-10-03-dossie-onda-2a-contracts-corporate.md`, com teste falhando primeiro e flags `off` por padrão.

## O que foi feito (com caminhos)

1. **Foundação 2A** — `backend/app/core/normative_source.py` (contrato `NormativeSource`: campos obrigatórios, proibição de norma posterior como fundamento histórico, fonte ambígua/não recuperada = violation; `classify_corporate_and_contracts`), commit `bf9efcf`.
2. **Módulo contracts@1.0.0** — `backend/app/modules/contracts/module.py` + corpus `backend/evals/contracts_cases.json` + testes `backend/tests/test_contracts_module.py` (6 temas com refs reais; reajuste sem parâmetros = blocked; sem validade em abstrato; diff de versão preserva texto/posição originais; cálculo reprodutível), commit `802d3bb`.
3. **Módulo corporate@1.0.0** — `backend/app/modules/corporate/module.py` + corpus `backend/evals/corporate_cases.json` + testes `backend/tests/test_corporate_module.py` (7 temas; sem responsabilidade pessoal por posição; estágios de recuperação; participação/cenário calculados), commit `6f23668`.
4. **Integração do par** — `backend/app/core/pipeline/orchestrator.py` + `backend/app/core/pipeline/contracts.py` + `backend/tests/test_onda2a_integration.py` (3 invariantes, ver aprendizados), atrás das flags `DOSSIER_MODULE_CONTRACTS`/`DOSSIER_MODULE_CORPORATE`, commit `eb8001b`.
5. **Estado** — commit docs `71cc811` (HEAD atual). 5 commits no total da 2A; `git status` limpo exceto `.opencode/MEMORY.md` modificado (learnings) e arquivos untracked de sessão/`output/`/`tmp/`.

## Verificação (evidência)

- pytest: **360 testes** coletados em `backend/tests/` (count de `def test_/async def test_`; SESSION_STATE registra "360 passed").
- Gates da Onda 1 intactos após 2A (regressão via suite, sem alteração de schema 3.0 — sem migration nova).
- HEAD `71cc811`, origin `git@github-smarteng:sergiosmarteng/smartlawer_V2.git` (push não re-verificado desta estação Windows).

## Decisões / constraints do usuário (verbatim onde crítico)

- "Rollout de um módulo por vez": `DOSSIER_V3_ENABLED=false` e `DOSSIER_MODULE_<ID>=false` por padrão; produção inalterada até gate próprio + piloto.
- "Nenhuma alteração silenciosa do schema 3.0; extensão incompatível exigiria nova versão formal (spec §10)".
- "Falha de um módulo vira blocked + limitação - nunca impede o dossie universal nem o outro módulo do par".
- "Onda 2A e par coeso: entidades/fatos/pedidos/fontes compartilhados por IDs estaveis; modulo primario nao absorve o outro".
- "Calculos so com clausula vigente, base, indice, termo e periodo; IA sugere regra cadastrada, nunca numero final livre".
- ".env nunca versionado; PAT do GitHub ainda pendente de rotacao".

## Andamento (feito vs pendente)

- **Feito**: foundação 2A, contracts@1.0.0, corporate@1.0.0, integração atrás de flags, corpus 7 casos por módulo, 360 pytest verdes.
- **Pendente**: Onda 2B (tax + administrative + real_estate) — planejada, não iniciada; rotulação PAT; migrations + smoke na VPS; shadow runs V3 + piloto 50 execuções; gate jurídico por módulo (2 revisores/área); Onda 3.

## Próximos passos

1. Operador: rotação do PAT do GitHub (bloqueador de segurança pré-piloto) e conferir remote `schinasergio` (https, auth falha com "Invalid username or token").
2. Operador: migrations na VPS (head `20261002_0013`) com `pg_dump` antes + smoke pós-deploy (12 blocos A–K) — in loco, VPS não acessível desta estação.
3. Implementar Onda 2B conforme `docs/superpowers/plans/2026-10-03-dossie-onda-2b-tax-administrative-real-estate.md` (mesmo padrão: teste primeiro, flags off, reusar `normative_source` + envelope/registry).
4. Shadow runs V3 + piloto 50 execuções; habilitar `DOSSIER_MODULE_<ID>` um por vez após gate próprio.

## Bloqueadores

- PAT do GitHub exposto em `78c3e36` ainda sem rotação (segurança pré-piloto); remote https `schinasergio` rejeita auth.
- VPS não acessível desta estação (Windows) — deploy/smoke rodados in loco.
- E2E Playwright não executado (sem browsers/ambiente de teste).
- Gate jurídico humano por módulo pendente (2 revisores por área, processo fora da máquina).

## Riscos

- Habilitar módulos antes do gate jurídico/piloto = anunciar capacidade sem evidência (viola constraint "não anunciar análise completa").
- Regressão silenciosa do schema 3.0 se 2B estender contrato sem nova versão formal.
- Falso positivo de cálculo se 2B afrouxar a regra "cláusula vigente + parâmetros determinados".

## Arquivos de referência

- Plano 2A: `docs/superpowers/plans/2026-10-03-dossie-onda-2a-contracts-corporate.md`
- Plano 2B: `docs/superpowers/plans/2026-10-03-dossie-onda-2b-tax-administrative-real-estate.md`
- Spec: `docs/superpowers/specs/2026-10-02-dossie-onda-2-design.md`
