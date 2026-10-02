# MEMORY — SmartLawer V2

> Atualizado pela skill `learning-loop` via `/checkpoint`. Aprendizados do projeto, sem segredos.

| Data | Aprendizado |
|---|---|
| 2026-09-25 | Chat SSE: o frontend só lê `token`/`done`; toda exceção no LLM dentro do `event_stream` deve emitir `done` final ou a bolha fica `…` para sempre — erro do backend nunca deve deixar o stream aberto. |
| 2026-09-25 | Deploy landing: entrega por tar na VPS (`/opt/smartlawer`) + retag da imagem anterior (`smartlawer-frontend:before-landing-20260924`) para rollback; não reiniciar API/worker/banco/Redis em entrega só de frontend. |
| 2026-09-25 | Docling A/B (645KB PDF): markdown ≈99% dos caracteres, porém ~3min na 1ª conversão (lazy). Fallback `raw_text` deve sempre permanecer ativo; `libgl1 libglib2.0-0` são dependências de sistema necessárias no Dockerfile do worker. |
| 2026-09-25 | Embeddings provider-aware: gates de config (`is_configured`) e clientes devem respeitar o provider ativo (`AI_PROVIDER=gemini`); verificar sempre o resolvedor de modelo antes de assumir OpenAI/OpenRouter. |
| 2026-09-25 | Docker não roda no Windows do dev — validações de runtime usam WSL (regra 7). |
| 2026-09-25 | Figuras de petição: extração via `docling_extractor` grava em tabela própria `document_figures` (migração alembic `20260925_0007`); página `analysis/[id].tsx` lista/exibe; material de regressão em `tmp/analysis-spec/` (pages JSON + PNGs da petição). |
| 2026-09-25 | Testes Celery: helpers do pipeline expõem `.func`/`.run` para valer com Celery real e stub — mockar a tarefa pontual, não pular o pipeline inteiro. |
| 2026-09-26 | Link legado vs API nova: página antiga passa `document_id` como `routeId` em `/analysis/v2/[id]`; fix é manter o fallback (`resolveByDocument()`) **no `catch` do fetch**, não só quando o param vem vazio (bug `dossie-v2-document-id`). |
| 2026-09-26 | Release de épico em submódulo: merge `feat/*` → `main` do submódulo + tag anotada (`v0.2.0`) + bump na raiz `chore: bump smartlawer_V2 (...)`; procedimento VPS documentado antes do deploy (pg_dump+snapshot, retag `before-v020`, `up --no-deps`, `alembic current` = head esperado). |
| 2026-09-26 | Modelo LLM aposentado (`gemini-2.5-flash`) → pinar novo (`CHAT_MODEL=gemini-3.8-flash`) e registrar incidente em docs/release notes; confira o resolvedor de modelo antes do deploy. |
| 2026-09-26 | Falha alta sem chave de IA é comportamento correto (PROVIDER_UNAVAILABLE, sem sucesso fictício): checklist pré-deploy inclui conferir chaves IA + `DOCLING_ENABLED` no `.env` da VPS; não anunciar "análise completa" antes do piloto. |
| 2026-09-26 | Uploads longos (Docling ~3min): copy PT-BR por etapa com spinner de andamento (`src/pages/upload.tsx`) evita percepção de travamento; o progresso honesto é parte da UX. |