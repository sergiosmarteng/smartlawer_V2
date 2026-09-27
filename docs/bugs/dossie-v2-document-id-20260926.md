# Bug: dossiê V2 abre 404 quando o id da rota é um document_id

Data: 2026-09-26. Severidade: alta (botão "Abrir dossiê V2" quebrado).

## Sintoma

`GET /analysis/v2/<document_id>?document_id=<document_id>` exibe
"Request failed with status code 404" (print do usuário, rota
`/analysis/v2/b55967d2-…?document_id=b55967d2-…`).

## Causa raiz

A página legada liga `/analysis/v2/${analysis.documentId}?document_id=…`,
ou seja, o `routeId` é um **document_id**, não um `artifact_id`.
A página V2 tentava `GET /api/v2/analyses/{routeId}` e, no 404, mostrava
erro direto — o ramo de fallback por `document_id` só existia quando
`routeId` vinha vazio, caso que nunca ocorre com esse link.

## Reprodução (log antes)

`GET /api/v2/analyses/<document_id>` → `404 {"detail": {"code": "NOT_FOUND"}}`
enquanto `GET /api/v2/analysis-runs?document_id=<id>` retorna a run com
`artifact_id` publicado (teste
`test_document_id_as_artifact_id_is_404_but_runs_resolve`).

## Fix

`src/pages/analysis/v2/[id].tsx`: fallback `resolveByDocument()` também no
`catch` do fetch do artefato — 404 com `document_id` resolve a última
execução publicada; sem run, mensagem honesta orienta reenvio.

## Depois

Contrato verde (`test_analysis_v2.py` 8 passed) + `tsc`/`lint`/`build` 0.
Validação no navegador pendente do operador (abrir dossiê de qualquer
documento analisado).
