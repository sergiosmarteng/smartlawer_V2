# 2026-11-01 — Validação do plano Jev + Onda A

**Base:** `44be75d` (nada commitado nesta sessão)
**Natureza:** replanejamento + correções determinísticas. Nenhuma dependência nova.

## 1. O que foi validado (Jev / TypeSafe System One)

Método: DNS + `docs.typesafe.ai` (API reference, primitivas, modelos, erros, jaggedness) + verificação de 13 afirmações da spec contra o código real por subagente de leitura. **Não houve chamada autenticada** (sem `TYPESAFE_API_KEY`), então o formato é doc-verificado, não 200-verificado.

| Premissa                              | Veredito                                                                |
| ------------------------------------- | ----------------------------------------------------------------------- |
| Jev existe                            | SIM — `api.typesafe.ai` resolve; endpoint `POST /v1/systemone`          |
| Preço US$ 0,042/Mtok in, saída grátis | SIM — tabela oficial de modelos                                         |
| Economia −55/−65%                     | NÃO — recalculada em −46% in / −36% out / −56% chamadas                 |
| Economia mensurável hoje              | NÃO — V3 não gravava `usage`; `MAX_RUN_USD` não existia no código       |
| Limiares "calibrados"                 | NÃO — inglês é o idioma primário do treino                              |
| `jev_provider.py` da spec funciona    | NÃO — `choice`/`score` usam `criteria`, não `options`/`min`/`max` (422) |
| Jev como guardrail de injection       | RISCO — docs: `state` não é tratado como hostil                         |
| LGPD neutra                           | NÃO — ZDR é enterprise; DPA precisa ser assinado                        |

Detalhe completo: `docs/superpowers/plans/2026-11-01-jev-plan-revisado-validacao.md`.

## 2. Onda A executada

Motivo: sem telemetria não há como provar economia; e o corte de 4.000 chars era suspeito de causar o bloqueador de recall.

1. `structured_extractor`: `block_text[:4000]` → `build_prompt_window` com o orçamento do planejador (8.000 tokens ≈ 32.000 chars). Truncamento, se ocorrer, preserva início e fim, marca a omissão e devolve `text_coverage`.
2. `pipeline/orchestrator`: `COVERAGE_MAX_BATCHES` passa a valer no caminho real (antes `max_batches=None` desligava o teto e `check_budget` era código morto). Parcialidade vira limitação explícita no artefato.
3. Telemetria: `llm_providers` e `ai_engine` acumulam `response.usage` (antes descartado); `run.usage` é gravado no caminho V3 com tokens, modelo, custo estimado, duração e contagem de lotes.
4. `MAX_RUN_USD` implementado de fato: guarda a cada lote e antes da análise, com tabela de preços sobrescrevível (`LLM_PRICES_JSON`). Modelo não precificado **não bloqueia** e grava `cost: unavailable`.
5. `merge_v1_usage_into_run`: a chamada V1 duplicada passa a aparecer em `usage.v1_legacy` — sem isso a comparação de economia sairia inflada a favor do V3.

## 3. Evidência

- `pytest backend/tests` → **426 passed, 0 failed**, exit 0 (8m36s). Baseline era 415; +11 testes novos.
- `python backend/evals/run_gate.py` → **GATE PASSED** (items=32, mean_faithfulness=0.969, threshold=0.85).
- Nenhum teste existente foi alterado. Uma falha intermediária (`test_real_stages`) foi diagnosticada e corrigida na causa: eu aplicava o orçamento de _agrupamento_ como limite de _contexto_.

## 3.1 Medição de recall na petição real (35 páginas)

Corpus: `tmp/analysis-spec/petition-pages.json` (35 páginas, 54.816 chars, ~17.459 tokens). Provedor: `gemini-3-flash-preview` (o de produção). Mesmo modelo, mesma temperatura, mesmo prompt de sistema — só muda o texto enviado.

**Determinístico (sem LLM):** o planejador gera **3 lotes**, não os 12 que a spec do Jev supunha.

|                               | texto que chega ao extrator                                  |
| ----------------------------- | ------------------------------------------------------------ |
| Antes (`[:4000]` por lote)    | 12.000 chars = **~19% do texto dos lotes**                   |
| Depois (janela por orçamento) | 59.954 chars = **~96%**, com 2.460 chars omitidos e marcados |

**Com LLM (6 chamadas, 26.432 tokens de entrada):**

| Métrica (após reconciliação) | Antes | Depois |
| ---------------------------- | ----- | ------ |
| claims                       | 5     | **18** |
| fatos                        | 15    | 15     |
| evidências                   | 3     | 4      |
| referências legais           | 6     | 10     |

Os 18 claims são pedidos distintos e reais: gratuidade de justiça, danos materiais, extrapatrimoniais, morais, estéticos, pensão vitalícia, honorários sucumbenciais, declaração incidental de inconstitucionalidade, controle difuso, notificação da reclamada. Há 1–2 sobreposições por paráfrase (a dedup é igualdade exata), então o número honesto é ~15–18 — contra os 11 do legado.

**Conclusão:** a hipótese estava certa. O corte de 4.000 chars era a causa do bloqueador "2 claims vs 11". Resultado salvo em `tmp/analysis-spec/recall-comparison-2026-11-01.json`.

## 3.2 Dois defeitos achados durante a medição

1. **`build_prompt_window` duplicava o texto.** Convertia tokens→chars com fator fixo 4, mas `estimate_tokens` usa tiktoken (~3,1 chars/token em português). A "janela" head+tail saía maior que o original: o prompt recebia 121% do documento, com o miolo repetido. Corrigido medindo a razão chars/token no próprio texto; se não há o que omitir, devolve intacto. Teste de regressão em `test_coverage_planner.py`.
2. **`MAX_RUN_USD` ficava inerte em produção.** O modelo `gemini-3-flash-preview` não está na tabela de preços, então `cost_known=False` e o guarda nunca bloqueava. Adicionado `MAX_RUN_TOKENS` (teto duro, independente de preço). Sem isso, o teto seria decorativo justamente no provedor que roda em produção.

## 4. Decisões tomadas

- Orçamento do extrator = limite do modelo (`COVERAGE_MAX_BATCH_TOKENS`), não o alvo de agrupamento (`max_batch_tokens`), porque o planejador permite bloco único maior que o alvo.
- `check_budget` mantido: é API de falha dura, usada por testes. O cap do caminho real vem de `plan_revision_batches` (parcialidade registrada, não exceção).
- Modelo não precificado = custo `None`. Preferimos custo ausente a custo inventado.

## 5. Pendências

- Commits e push concluídos em 2026-11-02: 45aec80..c69d28b no origin/main (inclui as 8 notas de sessão antigas, varridas antes de entrar).
- Medir recall no corpus do smoke: a hipótese de causa raiz dos "2 claims vs 11" agora está corrigida e medida localmente (5 → 18), mas falta reconfirmar com `SourceBlock` real na VPS.
- Onda B (Jev): depende de `TYPESAFE_API_KEY`; gate explícito — sem ganho medido em pt-BR, parar.
- O telemetria ainda não cobre tokens de embedding/rerank Cohere.

## 6. Correções à spec externa (para quem for implementar depois)

- `core/orchestrator.py` é, na prática, `core/pipeline/orchestrator.py`.
- Dedup de fatos é igualdade exata de `(statement, asserted_by)`, não substring.
- `classification.py` é keyword matching, não regex — e retorna `source="model"` sem modelo.
- O gate de RAG é estrutural (presença de citação `[N]`), não juiz semântico.
- "Dupla execução V1+V3" subestima: são `1 + N lotes + 1` chamadas.
- 11 vs 10 módulos não é contradição: 10 especializados + `universal`.
