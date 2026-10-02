# Rollout do Dossiê Universal V3 (Onda 0)

**Status:** runbook operacional. **Pré-requisito:** smoke pós-deploy PASS
(`docs/operacao/smoke-pos-deploy-2026-10-02.md`) + piloto concluído com
veredito Go.

## 1. Migration

1. Backup: `pg_dump -Fc smartlawer > backup_before_v0.3.0.dump` + snapshot.
2. `alembic upgrade head` → esperado `20261002_0013` (head).
3. `alembic current` confirma; `SELECT COUNT(*) FROM cases` → 0.

## 2. Shadow runs

1. `DOSSIER_V3_ENABLED=false`, `DOSSIER_V3_SHADOW_MODE=true` no `.env` da VPS.
2. Reprocessar amostra interna autorizada (5 casos do corpus
   `backend/evals/universal_dossier_cases.json` + cópia autorizada do
   documento que originou o defeito §3.1).
3. Comparar cobertura, fontes, duração, custo e correções V2 × V3.
4. Critério: nenhum artefato V3 só com Pedidos; seções com conteúdo real
   ou estado justificado.

## 3. Amostra interna

1. `DOSSIER_V3_ALLOWED_USER_IDS=<ids internos>`; `DOSSIER_V3_MAX_CONCURRENT_RUNS=2`.
2. Liberar núcleo universal para 2 advogados internos (piloto §D+1).
3. Métricas diárias: % `completed/partial/blocked/failed`, seções vazias
   por motivo, cobertura de páginas/blocos, custo mediano por execução.

## 4. Limites e pausa

- Pausar se: >10% afirmações sem fonte, custo >2× cap, qualquer vazamento
  entre organizações, taxa de falha de OCR/provedor fora do limite.
- Pausa = `DOSSIER_V3_ENABLED=false` + `up --no-deps` (sem migração nova).

## 5. Expansão

1. Ativar módulos especializados um por vez (Ondas 1→2→3, cada um com
   corpus + gate próprios).
2. Fallback universal sempre ativo (§13.5).
3. Marcar versão `0.3.0` após Onda 0 estável em produção.
