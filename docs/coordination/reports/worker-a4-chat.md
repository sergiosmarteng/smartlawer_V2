# Worker Report — A4 Grounded Chat (2026-09-07)

## Scope

GitHub issue #16: chat com streaming SSE + UI com citações clicáveis, tenant server-side.

## Changes (backend)

- `backend/app/schemas/chat.py` (new): `ChatRequest` (query 3–2000 chars, `document_id` opcional, `top_k`), `Citation` (ref/chunk/documento/página/excerpt), `ChatResponse`.
- `backend/app/core/rag_answer.py` (new): `SYSTEM_PROMPT` grounded (só trechos, `[N]` obrigatório, "não encontrei" explícito); `build_grounded_prompt()`; `complete()`/`complete_stream()` via OpenAI-compat (openai/openrouter); `answer_query()` (retrieve → generate → cite); `_to_citations()`; `is_configured()` gate.
- `backend/app/api/routes/chat.py` (new): `POST /api/v1/chat` (JSON) + `POST /api/v1/chat/stream` (SSE `token`/`done+citations`/`error`); auth `get_current_active_user`; tenant sempre do JWT; escopo opcional `document_id` validado com `get_document_for_user` (404 cross-user, 422 inválido); 503 sem chave; 502 em falha de geração.
- `backend/app/core/retrieval.py`: `hybrid_search()` ganhou `document_id` opcional.
- `backend/app/core/config.py`: `CHAT_MODEL=gpt-4-turbo`; `app/main.py` registra o router.
- `backend/tests/test_chat.py` (new, 8 tests): auth exigido, 503 sem chave, resposta grounded + citação completa, SSE tokens + `done`, fallback sem chunks, 404 cross-tenant, 422 inválido, prompt numerado.

## Changes (frontend)

- `src/pages/chat.tsx` (new): chat streaming via `fetch` + `AbortController`, parse SSE progressivo, painel de fontes clicáveis → `/analysis/{document_id}`, aviso "IA-DRAFT/revise".
- `Sidebar.tsx` + `Header.tsx`: link "Legal chat"; `middleware.ts`: `/chat` protegido.
- Fix incidental: `onClick={logout}` → `onClick={() => logout()}` (2 erros TS2322 pré-existentes).

## Validation

- `pytest tests/ -q`: **47 passed** (39 antes + 8 novos).
- `npx tsc --noEmit`: limpo. `npx eslint` nos 4 arquivos alterados: limpo.
- `npm run lint` full trava no ambiente (>5min) — pendência de infra, fora do escopo A4.
- Live LLM/SSE contra API real pendente de chave (comportamento 503 coberto em teste).

## Notes for next worker (A5)

- Golden set + gate RAGAS ainda ausentes; `complete()`/`complete_stream()` são os seams para o juiz.
- `rerank()` nunca exercitado live; incluir no golden quando houver `COHERE_API_KEY`.
