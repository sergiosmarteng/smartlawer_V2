# SmartLawer V2 — Onda 0 do Dossiê Universal completa (2026-10-02)

## Dados

- **Data:** 2026-10-02 (sessão contínua, sem pausas entre tasks).
- **Continue de:** `.opencode/sessions/2026-10-02-fechamento-020.md` (git centralizado em `sergiosmarteng`, Tasks 1–3 da Onda 0 já pushed).
- **Plano:** `docs/superpowers/plans/2026-10-02-dossie-juridico-universal-onda-0.md` (Tasks 1–16).

## Decisão do usuário (verbatim)

- "sim! quero que continue sem necessidade me perguntar entre uma task e outra, até acabar a implementação da Onda completa."

## O que foi feito (16 tasks, 1 commit isolado cada, todos pushed)

| Task | Commit    | Conteúdo                                                                                                   |
| ---- | --------- | ---------------------------------------------------------------------------------------------------------- |
| 1    | `c6cc17f` | `schemas_v3.py` (23 tipos, `validate_artifact_v3`) + remove `FALLBACK_THESES` + 3 testes + fixture família |
| 2    | `7988776` | `Case`/`CaseDocument`/`AnalysisStageRun` + CRUDs + migration `0011` + 5 testes                             |
| 3    | `372c3f7` | `PIPELINE_STAGES` (12) + `calculate_progress` + `publish_artifact_v3` + 6 testes                           |
| 4    | `a9ee273` | `plan_revision_batches` + `page_needs_ocr` por cobertura + `extract_revision_inventory` + 6 testes         |
| 5    | `82af929` | `classification` multirrótulo + `module_registry` + `universal@1.0` + 6 testes                             |
| 6    | `bb357f9` | `structured_extractor` + `reconcile_extractions` + 7 testes                                                |
| 7    | `537b383` | `visual_evidence` + migration `0012` (metadados visuais) + 6 testes                                        |
| 8    | `5487f7d` | `universal_legal_analyzer` bilateral + `prompts.py` + 5 testes                                             |
| 9    | `189fc93` | `research_issues` + `execute_registered_calculation` + models + migration `0013` + 5 testes                |
| 10   | `1b74ced` | `verify_artifact_v3` + `decide_publication_status` + `report_composer` (sem IA) + 8 testes                 |
| 11   | `f6c7e48` | `orchestrator.run_universal_pipeline` + gate V3 em `document_tasks` (flag off por padrão) + 5 testes       |
| 12   | `8e3ee06` | API casos/visuais/versões/compare/resume + flags legacy + `resume_run` + 9 testes                          |
| 13   | `71d9ddd` | vitest + `dossier.ts` + `useDossier` + `useAnalysisRun` + 7 testes                                         |
| 14   | `20157e2` | `dossier/*` (8 componentes + seções) + página fina + 11 testes                                             |
| 15   | `484c2f9` | `artifact_diff` + `build_v3_report` + `approve_artifact` + `review-status` + 6 testes                      |
| 16   | `ce9577d` | flags/config + `audit` sanitize + `universal_gate` + corpus + e2e + rollout/rollback + 6 testes            |

## Evidência final (gate da Onda 0)

- `pytest tests/ -q -p no:warnings` → **298 passed**
- `python evals/run_gate.py` → **GATE PASSED**
- `python evals/run_gate.py --universal` → **UNIVERSAL GATE PASSED (5 cases)**
- `npm run test:unit` → **18 passed (3 files)**
- `npm run lint` → **clean**
- `npx tsc --noEmit` → **clean**
- `npm run build` → **OK**
- `npm run test:e2e` → **não executado** (sem browsers/ambiente de teste; spec faz skip sem `PLAYWRIGHT_BASE_URL`)
- `git push origin main` → `372c3f7..ce9577d`, `0 0` ahead/behind

## Decisões de compatibilidade (durante o loop)

1. `STAGE_ORDER` (8) preservado na API V2; `PIPELINE_STAGES` (12) canônico V3; `_progress` delega quando há `stage_runs`.
2. `publish_artifact` deriva `schema_version` do conteúdo (default 2.0) — V2 intacto, V3 persiste 3.0.
3. `transition_run` intocado; `resume_run` novo para reabertura explícita de `failed`.
4. `document_tasks` com gate `_use_v3_pipeline` (`DOSSIER_V3_ENABLED`, default false) — V2 inalterado até o piloto.
5. Teste `test_missing_dates...` ajustado para prover tese mínima (vazio com dados = rejeição, regra do plano).
6. `vitest.config.ts` com `esbuild.jsx: automatic` (JSX sem import React explícito).

## Andamento

### Feito

- [x] Onda 0 Tasks 1–16 implementadas, testadas e pushed.
- [x] Migrations `0011`/`0012`/`0013` reversíveis (cadeia linear verificada).
- [x] `SESSION_STATE.json` atualizado com verificação + próximos passos.

### Pendente (operador — fora desta sessão)

- [ ] PAT rotation (bloqueador pré-piloto).
- [ ] Migrations na VPS (`alembic upgrade head` → `20261002_0013`) com backup.
- [ ] Smoke pós-deploy (12 blocos) na VPS.
- [ ] Shadow runs + piloto 50 execuções.
- [ ] E2E contra ambiente de teste (`PLAYWRIGHT_BASE_URL` + browsers).

### Próximo (engenharia futura)

- [ ] Onda 1A (cível + família), 1B (trabalhista/consumidor/previdenciário), 2, 3 — um plano por grupo.

## Bloqueadores

- PAT exposto (segurança, pré-piloto).
- VPS inacessível desta estação.
- E2E sem ambiente de teste aqui.

## Riscos

- `DOSSIER_V3_ENABLED=false` por padrão: V3 só produz via orquestrador direto ou flag ligada — produção inalterada até decisão.
- Migrations 0011–0013 ainda não aplicadas em prod (só testadas em sqlite + cadeia Alembic).
- Cobertura `0/0` legada some apenas quando o pipeline V3 processar documentos reais (Task 11 pronta, aguardando flag + fila).

Para retomar: reabrir o opencode no mesmo diretório e rodar `/retomar`.
