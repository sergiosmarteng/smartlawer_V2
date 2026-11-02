# Sessão 2026-10-06 — Smoke VPS GO (wiring V3) + pacote piloto + purga BFG arquivada

> Checkpoint gerado por `/checkpoint`. Fonte de verdade: arquivos + git, nunca memória do chat.
> Arquivo referenciado por `docs/SESSION_STATE.json → resume_prompt_file`.

## Data

2026-10-06 (fecha trabalho iniciado em 2026-10-05 na VPS, in loco) — sessão retomada de `2026-10-04-onda-2b-implementada.md`.

## Objetivo

Transformar o núcleo V3 (Ondas 0–2, release 0.3.0) em análise **realmente produtiva em produção**: ligar o wiring LLM extract/analyze/stages no orquestrador (W-1/W-2/W-3), rodar o smoke pós-deploy na VPS, fechar o incidente do PAT exposto e montar o pacote do piloto (rubrica + holdout + revisor + agregador). Em paralelo, decidir sobre a purga do token no histórico git.

## O que foi feito (com caminhos e commits)

### 1. Smoke VPS 2026-10-05 — NAO-GO → GO

- Primeiro smoke: **NAO-GO** — wiring V3 de prod ausente e PAT ainda vivo em `docs/CLAUDE.md` (`323f9ab docs(state): smoke VPS 2026-10-05 NAO-GO`).
- Fix `4192fa0 fix(dossie): nucleo vazio nunca publica completed (AC-01, verdade vacuosa)`: análise sem núcleo não pode fechar `completed`.
- Wiring V3 implementado e implantado em produção:
  - `d73d09b` feat(wiring): adaptadores LLM produtivos para extract/analyze (W-1).
  - `5c2da15` feat(wiring): estágios reais sobre blocos da revisão no orquestrador (W-2).
  - `eb32699` feat(wiring): `reanalyze` despacha `process_run_task`; nova run em reprocessamento (W-3).
  - `7f3efb1` fix(wiring): schema explícito no prompt de extração + `batch_stats` sem conteúdo.
  - `5785539` fix(wiring): schema explícito na análise + `section_states` de todas as seções.
- Segundo smoke: **GO P/ PILOTO** — petição real de 35p → artefato schema 3.0 `completed` com 14 seções, 2 claims, 4 fatos, 19 fontes e 4 teses; `reanalyze` despacha de verdade; banco íntegro; docs de smoke removidos. Registrado em `07aa46d docs(state): smoke VPS GO - wiring V3 em prod com artefato 3.0 populado`.
- `43f1b44 docs(smoke): pins 0.3.0/migracao 0013/api + queries via run (validados ao vivo)` — `docs/operacao/smoke-pos-deploy-2026-10-02.md` atualizado com pins reais.

### 2. Incidente de segurança — PAT do GitHub

- `8b968a6 docs(state): PAT rotacionado, blocker de seguranca derrubado (parcial: deploy key VPS pendente)`.
- `0b15711 docs(security): remove PAT revogado de CLAUDE.md` e `caf9300 docs(security): PAT removido de CLAUDE.md sem reformatar (corrige diff ruidoso)` — token já revogado no GitHub; valor **não** registrado nos docs de sessão.

### 3. Pacote do piloto (rubrica + holdout + revisor + agregador)

- `ae5a8d1 feat(piloto): rubrica congelada v1 + agregador de metricas com teste`:
  - `docs/operacao/rubrica-piloto-v1.md` + `backend/evals/rubric_pilot_v1.toml` (parse por `tomllib` stdlib, sem dependência nova).
  - `backend/evals/pilot_metrics.py` + `backend/tests/test_pilot_metrics.py` (Go/non-go contra thresholds do TOML).
- `49740e0 feat(piloto): pacote piloto (rubrica v1 + holdout + revisor + agregador)`:
  - `docs/operacao/protocolo-holdout.md`, `docs/operacao/pacote-revisor.md`.
  - `docs/operacao/piloto-50-execucoes-2026-10-02.md`.

### 4. Purga BFG do token no histórico — **arquivada** (preparada, não executada)

- `cf5c1ec docs(runbooks): nota de force-push da purga BFG (hashes antes/depois, SEM push ainda)` — `docs/runbooks/nota-force-push-2026-10-06.md`.
- `0e4654e docs: purga arquivada como preparada-mas-nao-executada` (**HEAD atual**).
- Decisão 2026-10-06: **não** executar o force-push agora; reativar somente se auditoria solicitar. Mirror pronto em `%TEMP%\smartlawer_V2.git` (reexecutável pelo procedimento na nota).

### 5. Limpeza

- `10e4eb1 docs: formatação prettier canônica (sem mudança de conteúdo)`.

## Verificação (evidência)

- Smoke VPS 2026-10-05 re-executado in loco: **GO** — artefato 3.0 com 14 seções / 2 claims / 4 fatos / 19 fontes / 4 teses; `reanalyze` despacha; banco íntegro (evidência registrada em `docs/operacao/smoke-pos-deploy-2026-10-02.md` + commit `07aa46d`).
- Head alembic intacto: **`20261002_0013`** (nenhuma migration nova em wiring/piloto).
- Contagem textual de `def test_` em `backend/tests/*.py`: **410** (crescimento vs 387 do release 0.3.0, inclui `test_pilot_metrics.py`). **Suíte pytest NÃO re-executada neste checkpoint** — não alegar verde sem rodar.
- Segurança: `git log -S '<token>' --all --oneline` deve ser vazio na cópia local (purga BFG aplicada só ao mirror temporário, conforme a nota).
- `docs/CLAUDE.md` sem token real (substituído por `<rotacionado-no-GitHub>`).
- Estado git: HEAD `0e4654e`; `main` vs `schinasergio/master` **ahead 133 / behind 2**; tags existentes: v0.1.1, v0.2.0, v0.3.0 (v0.3.0 continua a última).

## Decisões / constraints do usuário (verbatim onde crítico)

- "Purga BFG ARQUIVADA como preparada-mas-não-executada; reativar só se auditor solicitar" — force-push só com confirmação explícita.
- "Nunca versionar segredo; `.env` nunca versionado" e token exposto deve ser revogado + removido do arquivo (incidente 2026-10-04).
- "Auditoria 100% + HITL: `ai_draft`/`requires_human_review`; proibição de protocolo automático (CONSTITUTION)".
- "Auditoria 100%" mantida; "não anunciar 'análise completa'": piloto ainda pendente.
- "Rollback/ativação somente via `docker compose -f docker-compose.prod.yml` com `--no-deps`".
- "Rollout de um módulo por vez": `DOSSIER_V3_ENABLED=false` e `DOSSIER_MODULE_<ID>=false` por padrão.
- "Sem chave de IA, análises falham alto (PROVIDER_UNAVAILABLE) — comportamento correto".
- `CHAT_MODEL=gemini-3.8-flash` em prod (gemini-2.5-flash aposentado).

## Andamento (feito vs pendente)

- **Feito**: núcleo V3 produtivo em prod (wiring W-1/W-2/W-3) e smoke GO; incidente do PAT tratado (revogado + removido; purga de histórico arquivada); pacote do piloto pronto (rubrica v1 + holdout + revisor + agregador); HEAD `0e4654e`.
- **Pendente**: aplicar migrations na VPS (head `20261002_0013`, com `pg_dump` antes); operador rodar o smoke formal por blocos A–K; gate jurídico humano por módulo (2 revisores/área); shadow runs V3 + piloto 50 execuções; habilitar `DOSSIER_MODULE_<ID>` um por vez; planejar Onda 3; deploy key VPS (parte pendente da rotação).

## Próximos passos

1. Recrutar/acionar revisores e iniciar **piloto 50 execuções** com o pacote pronto (`docs/operacao/pacote-revisor.md`, `protocolo-holdout.md`, rubrica v1).
2. Operador (in loco, VPS): `pg_dump` + conferir migrations (head `20261002_0013`) + rodar smoke formal blocos A–K (`docs/operacao/smoke-pos-deploy-2026-10-02.md`).
3. Gate jurídico humano por módulo da Onda 2 (ordem sugerida contracts → corporate → tax → administrative → real_estate), depois habilitar flags uma a uma; após Go + gates, planejar Onda 3.

## Bloqueadores

- Calibragem pendente: **2 claims extraídos vs 11 do legado** na mesma peça — recall de extração a medir no piloto.
- Gate jurídico humano por módulo pendente (2 revisores por área, processo fora da máquina).
- E2E Playwright não executado (sem browsers/ambiente de teste).
- Deploy key VPS pendente (rotação do PAT parcialmente concluída).
- Purga BFG arquivada (não executada; só reativar por solicitação de auditoria).

## Riscos

- Anunciar "análise completa" antes do piloto = capacidade sem evidência.
- `main` ahead 133 / behind 2 de `schinasergio/master`: divergência pode exigir merge/rebase antes do próximo push.
- Se a purga BFG for executada, todos os clones (VPS/WSL/devs) e backups precisam de reset obrigatório (ver nota), senão histórico diverge.
- Recalls baixos de extração (2 vs 11) podem reprovar o piloto sem que o defeito esteja no núcleo.

## Arquivos de referência

- Smoke: `docs/operacao/smoke-pos-deploy-2026-10-02.md`
- Nota de purga/force-push: `docs/runbooks/nota-force-push-2026-10-06.md`
- Rotação PAT: `docs/runbooks/rotacao-pat-2026-10-02.md`
- Piloto: `docs/operacao/rubrica-piloto-v1.md`, `protocolo-holdout.md`, `pacote-revisor.md`, `piloto-50-execucoes-2026-10-02.md`
- Agregador: `backend/evals/pilot_metrics.py`, `backend/evals/rubric_pilot_v1.toml`, `backend/tests/test_pilot_metrics.py`
- Estado anterior: `.opencode/sessions/2026-10-04-onda-2b-implementada.md`
