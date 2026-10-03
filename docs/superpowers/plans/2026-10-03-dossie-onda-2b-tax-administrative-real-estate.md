# Dossiê Jurídico — Onda 2B Implementation Plan (`tax` + `administrative` + `real_estate`)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar os módulos `tax@1.0.0`, `administrative@1.0.0` e `real_estate@1.0.0` sobre o pipeline Onda 0 + fundação 2A (`NormativeSource`, runner, flags), com competência datada, regra temporal versionada e cadeia registral verificável — fechando a Onda 2 com as 2 regressões multiarea da spec (§9).

**Architecture:** Três módulos independentes entre si (sem dependência funcional cruzada); todos consomem `ReconciledCaseData` + `NormativeSource` e produzem `module_results[module_id]` com `issue_assessments` referenciando fontes do artefato. Reuso: `run_module_analyses()`, `CalculationRegistry`, `research_issues()`, `validate_normative_source()`, `ModuleActivationsLine`. O tributário ancora a tabela de vigência/transição (reforma) no `effective_from/effective_to` do `NormativeSource`.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, SQLAlchemy, Alembic, Celery, PostgreSQL/JSONB, pytest, TypeScript, React, Next.js, vitest.

**Spec:** `docs/superpowers/specs/2026-10-02-dossie-onda-2-design.md` (§2, §5–§10)

**Pré-requisito:** Plano 2A implementado (`NormativeSource`, `DOSSIER_MODULE_CONTRACTS/CORPORATE`, wiring do orquestrador).

## Global Constraints

- Mesmas da 2A, mais: competência do ente, jurisdição e data explícitas antes de aplicar qualquer regra (§9.3).
- Fonte local ausente → limitação + pergunta ao advogado, nunca regra federal aproximada (§8).
- Norma/decisão local anexada pelo usuário continua documento do caso até verificação de autenticidade e vigência (§8).
- Reforma tributária exige tabela de vigência e produção de efeitos por tributo e período; texto consolidado atual nunca substitui a regra do fato pretérito (§5).
- Cálculos separados dos valores alegados/documentados; reproduzíveis (§9.4).
- Visual relevante abre em imagem e página original; ausência × falha de extração distintas (§9.5).
- Cada artefato conserva versões de módulo e catálogo normativo; reanálise cria novo run (§9.8).
- Falha de pesquisa oficial → `partial`/`blocked` preservando análise documental (§9.7).
- TDD, flags off por padrão, 1 commit por módulo, fixtures sem dados pessoais reais.

## Review Focus

- Tributo estadual/municipal sem fonte do ente → conclusão recusada, não alíquota vizinha (§5).
- Crédito tributário definitivo inferido de auto isolado (§5).
- Prescrição/decadência com marco ou causa suspensiva desconhecidos (§5).
- Notícia/denúncia/relatório preliminar tratado como sanção final (§6).
- Nulidade sem checar consequência e estágio; decisão administrativa × judicial (§6).
- Matrícula antiga como titularidade atual; posse × domínio × obrigacional (§7).
- Área divergente "corrigida" pela imagem; regularidade urbanística sem o ente (§7).
- Rito da Lei 14.133 presumido para qualquer caso pretérito/ente (§6).

---

## File Structure

### Backend (novos, por módulo `<id>` em {tax, administrative, real_estate})

- `backend/app/modules/<id>/__init__.py`, `module.py`, `checklist.py`
- `backend/tests/test_<id>_module.py`
- `backend/tests/fixtures/<id>_case_v3.json`
- `backend/evals/<id>_cases.json` (6 casos §9: completo, adverso, incompleto, multiarea, norma antiga, tabela/imagem)

### Backend (modificar)

- `backend/app/core/classification.py`: tuplas `administrative`, `real_estate` (verificar/estender `tax`)
- `backend/app/core/config.py`: `DOSSIER_MODULE_TAX/ADMINISTRATIVE/REAL_ESTATE = False`
- `backend/app/core/pipeline/orchestrator.py`: `_MODULE_FLAGS` + `_module_registry()` (+3)
- `src/components/dossier/sections/sections.tsx` (+ teste): cartões dos 3 módulos

### Integração final (novo)

- `backend/tests/test_onda2_regressions.py`: `contracts`+`tax` e `corporate`+`real_estate` sem duplicação (§9)

---

### Task 2B-0: Fundação — classificação e flags dos 3 módulos

**Files:**

- Modify: `backend/app/core/classification.py`
- Modify: `backend/app/core/config.py`
- Create: `backend/tests/test_onda2b_foundation.py`
- Test: novo + `tests/test_dossier_classification.py` (regressão)

**Interfaces:**

- Consumes: `NormativeSource` + `validate_normative_source()` (2A).
- Produces: áreas `administrative`, `real_estate` (+`tax` estendida se o corpus acusar), 3 flags.

- [ ] **Step 1: Escrever testes falhos**
  - "auto de infração de ICMS com ente estadual" → `tax` (não `contracts`).
  - "edital de licitação e contrato administrativo" → `administrative`.
  - "matrícula do imóvel e escritura" → `real_estate`.
  - Flags `DOSSIER_MODULE_TAX/ADMINISTRATIVE/REAL_ESTATE` existem e default `False`.
- [ ] **Step 2: FAIL esperado** (`pytest tests/test_onda2b_foundation.py -q`).
- [ ] **Step 3: Implementar** keywords + flags:
  - `administrative`: ("licitação", "licitacao", "edital", "pregão", "pregao", "contrato administrativo", "lei 14133", "lei 14.133", "auto de infração administrativa", "processo administrativo", "servidor público", "servidor publico").
  - `real_estate`: ("matrícula", "matricula", "escritura", "posse", "usucapião", "usucapiao", "condomínio", "condominio", "zoneamento", "averbação", "averbacao", "cartório de imóveis", "cartorio").
  - `tax`: estender com ("ICMS", "ISS", "IPTU", "ITBI", "IRPJ", "PIS", "COFINS", "auto de infração", "auto de infracao", "DER", "reforma tributária", "reforma tributaria").
- [ ] **Step 4: PASS + regressão** (`test_onda2b_foundation` + `test_dossier_classification`).
- [ ] **Step 5: Commit** — `git commit -m "feat(onda2): administrative/real_estate classification and flags (2B foundation)"`

### Task 2B-1: Módulo `tax@1.0.0`

**Files:** pacote `tax/`, `test_tax_module.py`, `tax_case_v3.json`, `tax_cases.json`.

**Interfaces:** `TaxModule` (`supported_areas=("tax",)`), `register_calculation_rules`, `TAX_SOURCES` (CTN, normas federais oficiais, + ente local por caso via `NormativeSource`).

- [ ] **Step 1: Testes falhos** (padrão Onda 1)
  - DESCRIPTOR + registry resolve `tax`.
  - 7 temas §5; competência/jurisdição/data explícitas antes da regra.
  - Gate: crédito definitivo de auto isolado → nunca `complete`.
  - Gate: prescrição/decadência sem marco/suspensiva → `blocked` com faltantes.
  - Gate: alíquota de outro município/estado → recusada (fonte do ente exigida).
  - Gate: reforma sem tabela de vigência/efeitos → `blocked`.
  - Cálculos por competência (`tributo_competencia@1.0`: base, alíquota, deduções, pagamentos, atualização, arredondamento auditáveis); sem parâmetros → `CalculationBlockedError`.
  - Runner não muta o núcleo.
- [ ] **Step 2: FAIL esperado.**
- [ ] **Step 3: Implementar** (`checklist.py` 7 dimensões, `module.py` com `assess_dimension` + gates §5, cálculo, fontes, `DESCRIPTOR`).
- [ ] **Step 4: Corpus + gate** (6 casos §9; `universal_gate` PASS; `analyze()` nos 6).
- [ ] **Step 5: Commit** — `git commit -m "feat(onda2): tax module with dated competence and corpus (2B)"`

### Task 2B-2: Módulo `administrative@1.0.0`

**Files:** pacote `administrative/`, `test_administrative_module.py`, fixture, `administrative_cases.json`.

**Interfaces:** `AdministrativeModule` (`supported_areas=("administrative",)`), `ADMINISTRATIVE_SOURCES` (Lei 14.133, normas do ente/órgão, edital/contrato do caso).

- [ ] **Step 1: Testes falhos**
  - DESCRIPTOR + registry resolve `administrative`.
  - 6 temas §6 (ente/agente, ato, processo, licitação, contrato público, responsabilização).
  - Gate: notícia/denúncia/relatório preliminar ≠ sanção final.
  - Gate: nulidade sem consequência/estágio → `partial`, nunca conclusão.
  - Gate: decisão administrativa × judicial distinguidas.
  - Gate: Lei 14.133 só com regime verificado (sem presunção p/ caso pretérito/ente).
  - Reajuste/reequilíbrio/multa só com cláusula+fato+período+índice, senão `CalculationBlockedError`.
- [ ] **Step 2–5:** mesmo ciclo (implementar, corpus 6 + gate, commit `feat(onda2): administrative module ... (2B)`).

### Task 2B-3: Módulo `real_estate@1.0.0`

**Files:** pacote `real_estate/`, `test_real_estate_module.py`, fixture, `real_estate_cases.json`.

**Interfaces:** `RealEstateModule` (`supported_areas=("real_estate",)`), `REAL_ESTATE_SOURCES` (CC, Lei 6.015, normas especiais do instrumento).

- [ ] **Step 1: Testes falhos**
  - DESCRIPTOR + registry resolve `real_estate`.
  - 6 temas §7 (imóvel, direito, registro, negócio, conflito, urbanismo).
  - Gate: titularidade atual de matrícula antiga → nunca `complete` (exigir certidão atual).
  - Gate: posse × domínio × obrigacional distinguidos.
  - Gate: regularidade urbanística sem o ente → `blocked`.
  - Gate: área divergente nunca "corrigida" pela imagem.
  - Parcelas/mora/rateio só com contrato+pagamentos+índices, senão `CalculationBlockedError`.
  - Visual de matrícula/planta referenciado por chave opaca (sem path).
- [ ] **Step 2–5:** mesmo ciclo (commit `feat(onda2): real_estate module ... (2B)`).

### Task 2B-4: Regressões cruzadas + rollout da Onda 2

**Files:**

- Create: `backend/tests/test_onda2_regressions.py`
- Modify: `backend/app/core/pipeline/orchestrator.py` (wiring 2B, espelhar 2A-3)
- Modify: `src/components/dossier/sections/sections.tsx` (+ teste UI)
- Test: novo + `tests/test_dossier_modules_pipeline.py` + `test_onda2a_integration.py` (regressões)

- [ ] **Step 1: Testes falhos**
  - `contracts`+`tax`: um fato/pedido reconciliado gera um único objeto + resultados específicos por módulo (§9.6).
  - `corporate`+`real_estate` (imóvel em recuperação): idem, sem duplicar valores.
  - Flags off por módulo → `module_results` sem a chave e universal intacto.
  - Falha de pesquisa oficial → `partial`/`blocked` com análise documental útil (§9.7).
  - UI: cartões dos 5 módulos Onda 2; fallback declara motivo.
- [ ] **Step 2: FAIL esperado.**
- [ ] **Step 3: Implementar** wiring + cartões.
- [ ] **Step 4: Gates**
  - Run: `cd backend && pytest tests/test_onda2_regressions.py -q`
  - Run: `cd backend && pytest tests/ -q -p no:warnings`
  - Run: `cd backend && python evals/run_gate.py --universal`
  - Run: gates dos 5 corpus Onda 2 (`universal_gate.py` em cada JSON)
  - Run: `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`
  - Expected: tudo código 0.
- [ ] **Step 5: Commit** — `git commit -m "feat(onda2): cross-module regressions and rollout wiring (2B integration)"`

## Final Verification (2B = Onda 2 completa)

- [ ] `cd backend && pytest tests/test_tax_module.py tests/test_administrative_module.py tests/test_real_estate_module.py tests/test_onda2_regressions.py -q`
- [ ] `cd backend && pytest tests/ -q -p no:warnings` (regressão total incl. Onda 0/1/2A)
- [ ] `cd backend && python evals/run_gate.py --universal` + 3 corpus 2B no `universal_gate`
- [ ] `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`
- [ ] Gate jurídico humano por módulo (2 revisores da especialidade: precisão factual, cobertura, temporalidade, pertinência normativa, utilidade da ação — §9, sem % de êxito)
- [ ] Shadow runs + flag individual por módulo (ordem sugerida: contracts → corporate → tax → administrative → real_estate, um por vez)
- [ ] Confirmar: nenhum arquivo sensível/untracked estranho nos commits; `git status` limpo salvo `output/`, `tmp/`, sessions
