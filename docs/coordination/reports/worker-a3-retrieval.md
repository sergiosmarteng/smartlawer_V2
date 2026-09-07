# Worker Report — A3 Hybrid Retrieval (2026-09-07)

## Scope

GitHub issue #15: chunker jurídico + embedding service + retrieval híbrido (vetor + FTS + RRF) + rerank opcional. Preenche `document_chunks` (A1) a partir do texto de análise (A2).

## Changes

- `backend/app/core/legal_chunker.py` (new): `chunk_legal_text()` — unidades indivisíveis por estrutura legal (Art./§/Súmula/EMENTA/seções), packing guloso até 1000 tokens, overlap de 150 tokens, fallback por sentenças para unidades gigantes. `estimate_tokens()` usa tiktoken se presente, senão heurística chars/4.
- `backend/app/core/embeddings.py` (new): `embed_texts()`/`embed_query()` via API OpenAI (`text-embedding-3-small`, batch), `is_configured()`; retorna `None` sem chave/pacote para o worker pular indexação sem falhar.
- `backend/app/core/retrieval.py` (new): `VECTOR_CANDIDATES_SQL` (cosseno `<=>`) + `FTS_CANDIDATES_SQL` (`to_tsvector portuguese`), ambos com `user_id` pré-filtrado; `rrf_fuse()` pura (k=60, desempate first-seen); `rerank()` Cohere `rerank-3` opcional com fallback silencioso; `hybrid_search()` com dupla barreira de tenant (SQL + Python) e degradação para FTS-only sem embedding.
- `backend/app/tasks/document_tasks.py`: `index_document_chunks()` idempotente (delete+insert) chamado após COMPLETED, blindado por try/except no task.
- `backend/alembic/versions/20260907_0003_fts_index.py` (new): índice GIN `to_tsvector('portuguese', content)`; cadeia `...0002 -> 20260907_0003` verificada via offline `--sql`.
- `backend/app/core/config.py`: `EMBEDDING_BATCH_SIZE`, `RETRIEVAL_CANDIDATE_K=30`, `RETRIEVAL_TOP_K=6`, `RRF_K=60`, `RERANK_ENABLED=False`, `COHERE_API_KEY`, `COHERE_RERANK_MODEL`.
- `backend/requirements.txt`: `cohere==7.1.1`.
- `backend/tests/test_retrieval.py` (new, 15 tests): chunker (Art. nunca separado do corpo, budget, overlap, vazio), RRF (score + tie-break + vazio), SQL tenant-first, rerank fallback, `hybrid_search` fusão + barreira de tenant + FTS-only + vazio, indexação (persiste, idempotente, skip sem embeddings).

## Validation

- `pytest tests/ -q`: **39 passed** (24 antes + 15 novos).
- Offline `--sql`: `CREATE INDEX ... USING gin (to_tsvector('portuguese', content))` confirmado.
- Live pgvector/FTS/Cohere ainda pendente de Docker + chaves (daemon down).

## Notes for next worker (A4)

- `hybrid_search()` pronto para o chat SSE; A4 adiciona endpoint + UI com citações.
- `rerank()` implementado mas nunca exercitado live (sem `COHERE_API_KEY`); A5 deve incluir rerank no golden set quando houver chave.
