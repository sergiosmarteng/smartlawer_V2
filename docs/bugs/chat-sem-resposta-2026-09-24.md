# Bug: chat jurídico sem resposta — causa raiz e fix

**Data:** 2026-09-24
**Arquivo:** `docs/bugs/chat-sem-resposta-2026-09-24.md`
**Goal:** Diagnosticar por que o chat jurídico não responde nada e fazê-lo responder.

## Sintoma

Página `/chat` exibe bolha do assistente presa em `…` (texto vazio), sem erro visível,
mesmo com request `POST /api/v1/chat/stream` retornando `HTTP 200`.
Frontend nunca preenche `text`, `citations` ou banner de erro.

## Hipóteses investigadas

1. `503` sem chave de IA (`_require_ai`) — descartado como causa do "vazio":
   retorna HTTP 503 que o frontend exibe como `HTTP 503` (não vazio).
2. `401/403` token ausente/expirado — exibe "Sessão expirada" / redirect `/sign-in` (não vazio).
3. `422` query <3 chars / `document_id` inválido — frontend valida antes; chamada direta retorna 422 visível.
4. Fallback "sem base" (`FALLBACK_NO_BASIS`) — retorna token visível, não vazio.
5. **Confirmada:** exceção no LLM dentro de `event_stream` emite só `{"error": ...}` sem `done`,
   e o frontend ignora `error` (só lê `token`/`done`) — bolha fica vazia para sempre.

## Evidência

### ANTES (reprodução via TestClient, `complete_stream` raising `RuntimeError("boom llm")`)

```
[REPRO-ANTES] HTTP 200
[REPRO-ANTES] SSE bruto:
data: {"error": "Falha ao gerar resposta"}

[REPRO-ANTES] eventos parseados: [{'error': 'Falha ao gerar resposta'}]
[REPRO-ANTES] frontend text='' done=False citations=None error_ignorado='Falha ao gerar resposta'
[REPRO-ANTES] bolha exibida='…' -> BUG: fica em … vazio
```

- Backend: `backend/app/api/routes/chat.py:167-170` (antes) — `except` fazia
  `yield _sse({"error": ...}); return` sem `done`.
- Frontend: `src/pages/chat.tsx:138-151` (antes) — loop só tratava `token`/`done`,
  `error` era silenciosamente descartado; `text` recomputado do zero a cada chunk
  permanecia `''` → render `'…'` (`chat.tsx:259`).

### DEPOIS (mesmo cenário, após fix)

```
[VERIFY-DEPOIS] HTTP 200 em 0.02s
[VERIFY-DEPOIS] SSE bruto:
data: {"error": "Falha ao gerar resposta"}

data: {"done": true, "citations": [{"ref": "[1]", ...}], "suggested_questions": [], "ai_draft": true, "requires_human_review": true}

[VERIFY-DEPOIS] text='' error='Falha ao gerar resposta' done=True visivel='Falha ao gerar resposta' <30s=True
```

- Critério (a): resposta não-vazia (`error` visível como texto) em 0.02s <30s.
- Critério (b): `test_workflow.py + test_versions.py` (rotas `/processes`, `/tasks/{id}`,
  `/analysis/{id}`, `/analysis/{id}/docx`) seguem 11 passed antes e depois.
  Nota: rotas literais `/analise` e `/nova-analise` **não existem** no backend;
  `Nova análise` é label do menu para `/upload` (`Sidebar.tsx:11`, `Header.tsx:13`),
  e análise é `/analysis/{id}` (frontend) / `/api/v1/analysis/{id}` (backend).

## Fix

Mínimo, sem mudar modelo/prompt/UI:

1. `backend/app/api/routes/chat.py` — no `except` do `event_stream`, após `error`
   emitir também evento terminal `done: True` (com `citations` já calculadas,
   `suggested_questions: []`). Garante que todo stream termina com `done`.
2. `src/pages/chat.tsx` — tratar `event.error`: guarda em `streamError`,
   se `text` vazio preenche bolha com a mensagem de erro (nunca deixa `''`),
   ao final faz `setError(streamError)` para banner visível.
3. `backend/tests/test_chat.py::test_chat_stream_llm_failure_emits_error_and_done`
   — regressão: falha do LLM emite 1 `error` + 1 `done`, visível não-vazio.

Fora de escopo (não feito): reformular UI, trocar modelo, melhorar prompt.

## Prevenção

- Contrato de stream: **todo** caminho de `event_stream` deve terminar com exatamente
  um `{"done": True, ...}` — adicionar assert/lint futuro ou teste que conta `done==1`
  em todos os cenários (sucesso, fallback, block, erro).
- Frontend: `parseSseEvents` deve ter branch explícita para `error` (nunca `if token/done`
  sem `else`). Considerar tipar eventos SSE (`type StreamEvent = {token?...} | {error...} | {done...}`)
  para o compilador acusar evento ignorado.
- Observabilidade: log de `Falha no streaming` já existe; adicionar métrica/contador
  de `error` emitidos para alertar antes do usuário reclamar de "chat mudo".
- Teste de contrato frontend/backend: teste que simula o loop do `chat.tsx`
  (recomputa `text` a partir dos eventos) e falha se bolha final for `''`.
