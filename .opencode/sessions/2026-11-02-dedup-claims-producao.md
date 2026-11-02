# 2026-11-02 — Onda A em produção + dedup de claims

**Projeto:** SmartLawer_V2
**HEAD:** `94f1a2f` (== `origin/main`, working tree limpo)
**Natureza:** deploy + correção determinística no reconciliador. Nenhuma migration nova (head alembic `20261002_0013`). Nenhuma dependência nova.

## 1. Objetivo

1. Confirmar em produção que o corte fixo de 4.000 chars era a causa do bloqueador de recall.
2. Medir custo/tokens reais da run (a telemetria da Onda A passou a gravar `usage`).
3. Reduzir a duplicação de claims entre lotes sobrepostos sem fundir pedidos distintos.

## 2. O que foi feito

### 2.1 Deploy da Onda A na VPS

- Sequência de deploy na VPS (`/opt/smartlawer`), com backup `pg_dump` e imagens `smartlawer-api:pre-ondaA` / `smartlawer-worker:pre-ondaA` para rollback:
  1. `7c830a6` — Onda A (extrator, telemetria, teto de lotes);
  2. `ad8f990` — dedup v1 (não reduziu nada: 19 → 19);
  3. `2df7871` — dedup v2 (número autoritativo + promoção de grupo): 19 → 17;
  4. `94f1a2f` — apenas docs; checkout atualizado sem rebuild.
- Verificado no fechamento: `git rev-parse HEAD` em `/opt/smartlawer` = `94f1a2f`; containers construídos a partir de `2df7871`; API healthy, worker reiniciado, `alembic current` = `20261002_0013`, site 200, sem erro nos logs.
- Prova de que a dedup está no ar: inspeção do código dentro do container (promoção presente) e a reanálise seguinte produziu 17 claims em vez de 19.
- Cobertura do prompt nos blocos reais de produção (petição 35p, 1.084 blocos): **74,3% → 97,6%** após corrigir a contabilidade do marcador de bloco (`7c830a6`).

### 2.2 Recall confirmado em produção

Reanálise de `real_pi4.pdf` (35p, 1.084 blocos), run `f1e9b83d`, artefato `27458429`:

| Métrica            | Antes | Depois |
| ------------------ | ----- | ------ |
| claims             | 2     | **19** |
| fatos              | 4     | **13** |
| evidências         | 2     | **3**  |
| referências legais | 4     | **19** |

Telemetria gravada pela primeira vez em produção: `{calls: 4, prompt_tokens: 47.640, completion_tokens: 9.915, tokens_total: 57.555, duration_s: 112,79, batches_planned: 3, batches_failed: 0, chars_omitted: 2.178, cost: unavailable}`.

### 2.3 Dedup de claims no reconciliador

Arquivos: `backend/app/core/reconciler.py` + `backend/tests/test_reconciler_dedup.py` (commits `ad8f990` e `2df7871`).

- Agrupamento por título literal (`title:<casefold>`) criava um pedido novo a cada paráfrase entre lotes sobrepostos.
- Regra nova: normaliza acento/caixa/pontuação, descarta palavras vazias e aberturas de pedido, e só funde quando um conjunto de tokens **contém** o outro.
- Número original é autoritativo: pedidos com números diferentes nunca se fundem; claim sem número tenta um grupo numerado compatível e claim numerado promove um grupo sem número que contenha o mesmo pedido.
- ID de grupo estável (`gN`), união de `source_refs`, soma de ocorrências, título mais longo preservado; fatos deduplicados por `statement` normalizado mantendo autor separado.
- Singular/plural incluídos na comparação (`dano/danos`, `material/materiais`, `moral/morais`).

### 2.4 Medição da dedup

- Execução nova da mesma petição: **19 → 17 claims**.
- Re-reconciliando os 17 claims armazenados: **16**.
- 300 permutações de ordem/divisão de lotes: **sempre 16** — a regra é estável; a diferença 17 × 16 vem do modelo reescrever títulos, não da reconciliação.
- Residuais são sinônimos (`moral` × `extrapatrimonial`, `normativa` × `prevista em CCT`): exigem julgamento semântico, não regra lexical.

## 3. Evidência re-executada neste checkpoint

- `python -m pytest backend/tests/test_reconciler_dedup.py backend/tests/test_dossier_reconciler.py -q` → **16 passed, 0 failed** (8,69s).
- `git status -sb` → working tree limpo; `git rev-parse HEAD` == `git rev-parse origin/main` == `94f1a2f`.
- A suíte completa de 441 testes é a evidência do commit `2df7871`; **não foi re-executada integralmente neste checkpoint** (apenas os 16 testes do reconciler).

## 4. Decisões e constraints

- Contenção de tokens é conservadora por construção: fundir pedidos distintos é pior que duplicar.
- Sinônimos que não se contêm não entram em regra lexical; candidato natural ao primitivo `choice` do Jev, após ganho medido em pt-BR.
- Modelo não precificado grava `cost: unavailable` em vez de custo inventado; o teto duro passa a ser `MAX_RUN_TOKENS`.
- Constraints vigentes preservadas em `docs/SESSION_STATE.json` (`active_constraints`), incluindo: auditoria 100% + HITL, proibição de protocolo automático, `.env` nunca versionado, flags de módulo off por padrão, piloto não declara % de êxito.

## 5. Andamento

**Feito**

- Onda A deployada e recall confirmado em produção.
- Telemetria de tokens/duração/lotes ativa; custo USD ainda indisponível.
- Dedup lexical implementada, testada e medida; HEAD publicado no `origin/main`.

**Pendente**

- Definir `LLM_PRICES_JSON` no `.env` da VPS para o custo sair de `unavailable` e o `MAX_RUN_USD` voltar a proteger.
- Revisar com o usuário os valores de `COVERAGE_MAX_BATCHES` e `MAX_RUN_TOKENS` em produção.
- Dedup semântica dos sinônimos residuais (Jev `choice` ou normalização determinística).
- Piloto de 50 execuções com revisores; gates jurídicos por módulo; shadow runs V3.
- Rotação do PAT: deploy key da VPS ainda pendente.

## 6. Bloqueadores

- Custo em USD não calculável para `gemini-3.8-flash` até definir `LLM_PRICES_JSON`.
- Sinônimos residuais de claims exigem julgamento semântico.
- Gate jurídico humano por módulo (2 revisores por área) é processo fora da máquina.
- E2E Playwright não executado (sem browsers/ambiente de teste).

## 7. Riscos

- ~~Estado da VPS divergente do repositório~~ — **resolvido**: `git rev-parse HEAD` em `/opt/smartlawer` = `94f1a2f` e os containers foram construídos de `2df7871`. A dedup está no ar (17 claims na reanálise seguinte). O que resta é manter `head` e `deployed_head` separados no `SESSION_STATE.json` para não repetir a dúvida.
- **17 × 16:** os dois números medem coisas diferentes (run nova × re-reconciliação dos claims armazenados); não tratar como regressão.
- **Jev:** economia e calibração em pt-BR ainda não validadas; `state` não é tratado como hostil pelo provedor.
- **Cobertura:** 2.178 chars omitidos e marcados na run de produção; parcialidade precisa continuar explícita no artefato.

## 8. Próximos passos

1. Definir `LLM_PRICES_JSON` no `.env` da VPS e validar que `usage.cost` deixa de ser `unavailable` e que `MAX_RUN_USD` volta a proteger.
2. Decidir com o usuário `COVERAGE_MAX_BATCHES` e `MAX_RUN_TOKENS` para documentos grandes (parcialidade explícita vs teto).
3. Avaliar os sinônimos residuais com o Jev apenas após medir ganho em pt-BR; caso contrário, manter 16 e registrar a limitação.
4. Retomar o pacote do piloto (50 execuções) e os gates jurídicos por módulo.
