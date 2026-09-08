# Worker Report — B4 Workflow Identifiers (2026-09-08)

## Scope

BL-014 + issue #22: decidir e codificar os identificadores públicos do workflow.

## Decision

**Manter `document id == task id` explicitamente.** Um documento possui
exatamente um pipeline de processamento e no máximo uma `Analysis`
(`UNIQUE` em `document_id`); um ID de task Celery separado exigiria
tabela de rastreio sem benefício no piloto. Reavaliar se batch (BL-021)
ou multi-análise por documento surgirem.

## Changes

- `backend/app/api/routes/documents.py`: docstring da regra de identidade
  no `upload_document`; `taskStatusUrl` documentado como URL canônica de
  polling (relativa à raiz da API `/api/v1`).
- `backend/app/api/routes/workflow.py`: docstring da regra no
  `get_task_status` (404 cross-user como anti-oráculo).
- `src/pages/upload.tsx`: polling usa `taskStatusUrl` da resposta via
  `normalizeApiPath`, com fallback para `/tasks/{id}`.
- Tests: `taskStatusUrl == /tasks/{id}` no upload; novo teste de
  identidade (`task_id == document_id`) + 404 cross-user.

## Validation

- `pytest tests/test_documents.py tests/test_workflow.py`: 9 passed.
- `npx tsc --noEmit`: limpo. `eslint src/pages/upload.tsx`: limpo.
