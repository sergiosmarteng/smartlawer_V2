# Rollback do Dossiê Universal V3 (Onda 0)

**Princípio:** artefatos V3 publicados são preservados; novas execuções
são desativadas; leitura continua sem perda de dados.

## 1. Desativar novas execuções

```bash
ssh smartlawer@<VPS>
cd /opt/smartlawer
# .env: DOSSIER_V3_ENABLED=false (mantém DOSSIER_V3_SHADOW_MODE=false)
docker compose -f docker-compose.prod.yml up -d --no-deps backend worker
```

## 2. Preservar artefatos V3

- Não rodar `alembic downgrade`: tabelas `cases`, `case_documents`,
  `analysis_stage_runs`, `legal_research_results`, `calculation_results`
  permanecem; leitura V2/V3 continua.
- Se reversão de schema for inevitável: backup antes + `downgrade -1`
  por revision (`0013` → `0012` → `0011`), conferindo `alembic current`.

## 3. Voltar ao fluxo V2

1. Retag: `docker tag smartlawer-backend:latest smartlawer-backend:before-v030`.
2. `docker compose -f docker-compose.prod.yml up -d --no-deps backend`
   com imagem `before-v020`/`before-v030` preservada.
3. Smoke: `docs/operacao/smoke-pos-deploy-2026-10-02.md` blocos A–K.

## 4. Pós-rollback

1. Abrir `docs/operacao/incidente-<data>.md` com bloco FAIL + evidência.
2. Corrigir causa em branch; novo deploy só após smoke PASS total.
3. Reativar V3 pelo runbook de rollout (§2 shadow runs primeiro).
