# Incidente 26/09/2026 — `gemini-2.5-flash` aposentado pelo Google

## Sintoma

Uploads falhando com `PROVIDER_UNAVAILABLE` (3 documentos, comportamento
correto do T01: falhou alto em vez de tese genérica).

## Causa (logs do worker, não é crédito/chave)

`Error 404: This model models/gemini-2.5-flash is no longer available to
new users.` O modelo lista em `/models`, mas não serve para chaves novas.

## Correção (VPS, 26/09)

- `CHAT_MODEL=gemini-3.8-flash` no `.env` (modelo recomendado pelo próprio
  Google; testado com 1 chamada de 7 tokens antes da troca).
- Restart rolante de `api` + `worker` (`--no-deps`, sem tocar o frontend).
- 3 documentos reenfileirados via `process_pdf_task.delay` → todos
  `completed` + `Analysis ready`, sem novos erros.

## Lições

- Ancorar modelo por nome exige vigilância de aposentadoria; avaliar
  `gemini-flash-latest` (flutuante) x pin fixo + alerta de 404 de modelo.
- `nginx -s reload` no proxy após qualquer recreate de frontend/api
  (DNS interno muda com o IP do container).
