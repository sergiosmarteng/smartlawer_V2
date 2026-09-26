# Release 0.2.0 — análise jurídica V2 (deploy VPS)

`smartlawer_V2` tag `v0.2.0` (merge `8b3ab0e`). Dossiê jurídico verificável
+ módulo trabalhista no fluxo Nova análise. Sem promessas de percentuais,
cobertura integral ou êxito; sem protocolo/prazos automáticos.

## O que muda (resumo)

- Fim do sucesso fictício: sem provedor de IA, a análise falha com
  `PROVIDER_UNAVAILABLE` explícito (antes: teses genéricas como `COMPLETED`).
- Execuções versionadas (`analysis_runs/artifacts`), extração página/bloco
  por revisão, cobertura sem corte fixo, busca com escopo pré-ranking,
  API `/api/v2` + página `/analysis/v2/[id]`, chat com `[A]` derivada e
  inventário global, exports do artefato, exclusão rastreável, limites.
- Migrações **0008–0010** (aditivas; 0010 libera `embedding` NULL).
  Aplicadas automaticamente no startup da API (`upgrade head`).
- Compatibilidade V1 mantida (projeção legada + `generatedDefenseStrategy`
  agora como plano de atuação).

## Verificação pré-deploy (executada, exit 0)

- `python -m pytest tests/ -q` → 212 passed.
- `npx tsc --noEmit`, `npm run lint`, `npm run build` → OK (rota `/analysis/v2/[id]`).
- Benchmark sintético 30 casos: 10/10 portões; piloto real pendente
  (rubrica de 2 advogados, holdout, 50 execuções p/ custo).

## Procedimento na VPS (`/opt/smartlawer`)

0. **Backup**: `pg_dump` do banco + snapshot do volume `smartlawer_pgdata`.
   Testar restore em cópia antes de migrar (exigência §21).
1. Preservar imagens atuais:
   `docker tag smartlawer-api:latest smartlawer-api:before-v020` (idem
   worker/frontend). Copiar `.env` para `/home/ubuntu/smartlawer-backups/v020/`
   (nunca versionar, nunca sobrescrever o da VPS).
2. Entregar `smartlawer-0.2.0.tar` (git archive da tag) e extrair sobre `/opt/smartlawer`,
   preservando `.env` e `enable-ssl.sh`.
3. `sudo docker compose -f docker-compose.prod.yml build api worker frontend`.
4. Subir com dependências mínimas e conferir migração:
   `sudo docker compose -f docker-compose.prod.yml up -d --no-deps api`
   depois `docker exec smartlawer-api alembic -c /app/alembic.ini current`
   (esperado: head `20260925_0010`).
5. `sudo docker compose -f docker-compose.prod.yml up -d --no-deps worker frontend`.
6. Smoke: `/health` → login → upload PDF → acompanhar task → abrir dossiê V2
   (pedidos, Ver fonte, revisão) → chat com citação → export Markdown →
   `/ops/summary` (limites visíveis).

## Atenções

- **Sem chave de IA, análises falham alto** (comportamento novo e correto).
  Confirme `OPENAI/GEMINI/OPENROUTER_API_KEY` + `DOCLING_ENABLED` no `.env` da VPS.
- Docling: ~3 min na 1ª conversão; concorrência do worker = 2 (medir antes de ampliar).
- Rollback: retaggear `*:before-v020` como `latest` e recriar serviços com
  `--no-deps --force-recreate`; downgrade `alembic downgrade -1` (0010 remove
  linhas só-texto) somente se necessário; nunca com jobs ativos.
- Não anunciar "análise completa": piloto (advogados + holdout) ainda pendente.
