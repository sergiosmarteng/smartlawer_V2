# Worker Report — A5 Eval Gate + HITL (2026-09-07)

## Scope

GitHub issue #17: golden set 30 questões, métricas, gate CI faithfulness ≥ 0.85, human-in-the-loop.

## Changes

- `backend/evals/golden_legal.json` (new): 30 itens PT-BR (g01–g24 fundamentados, a01–a06 abstenção) com `expected_terms` e categorias.
- `backend/evals/corpus_fixture.json` (new): 12 trechos sintéticos que fundamentam g01–g24; nada cobre a01–a06.
- `backend/app/core/eval_scoring.py` (new): scorer determinístico sem LLM-judge — `context_recall`, `answer_relevancy`, `faithfulness` (fração de claims com `[N]`; recall 0 exige abstenção explícita, senão 0); `split_sentences` com proteção de abreviaturas (Art., §, nº…) e fusão de `[N]` órfão; `gate_passed()` média ≥ 0.85.
- `backend/evals/run_gate.py` (new): retriever keyword com threshold de abstenção (overlap < 2 → []), stub student grounded + abstenção, saída `GATE PASSED/FAILED` + exit code para CI. Contrato permite trocar retriever/student pelos reais sem mudar o gate.
- `backend/tests/test_eval_gate.py` (new, 10 tests): 30 itens/6 abstenções, gate passa grounded, gate falha sem citações, falha sem abstenção, units do scorer e abreviaturas.
- HITL: `ChatResponse.ai_draft` + `requires_human_review` (sempre true, incl. eventos SSE `done`); `docs/coordination/human-in-the-loop.md` (4 gates + reviewer checklist + proibição de protocolo automático).
- CI (`.github/workflows/ci.yml`): Postgres → `pgvector/pgvector:pg15`; etapa `python backend/evals/run_gate.py`.
- Correção de portabilidade: `conftest.py` remove índice HNSW do metadata de teste (test DBs sem extensão); `test_document_chunks` recria o HNSW na cópia de DDL.

## Validation

- `pytest tests/ -q`: **57 passed** (47 antes + 10 novos).
- `python backend/evals/run_gate.py`: `items=30 mean_faithfulness=0.967 GATE PASSED`.
- `ci.yml` parseado OK.
- g09 permanece imperfeito (0.0): miss legítimo de retrieval — a citação da lei está em c08, o retriever keyword ranqueou c03. Canário para o híbrido real com embeddings (A3) melhorar; documentado, não escondido.

## Notes for next worker (Onda B)

- Upgrade path: LLM-as-a-judge pode substituir o interior de `score_item` sem mudar o contrato do gate.
- Live pgvector/FTS/Cohere/LLM continuam pendentes de Docker + chaves (B1).
