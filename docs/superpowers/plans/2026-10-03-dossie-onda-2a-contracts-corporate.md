# Dossiê Jurídico — Onda 2A Implementation Plan (`contracts` + `corporate`)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar os módulos `contracts@1.0.0` e `corporate@1.0.0` sobre o pipeline Onda 0 + fundação Onda 1, com matrizes, comparador de versões, cálculos versionados e catálogo normativo verificável — sem alterar o contrato universal.

**Architecture:** Par coeso (spec §10): os dois módulos compartilham entidades, fatos, pedidos e fontes por IDs estáveis; o módulo primário não absorve o outro. Reuso total da Onda 0/1: `PIPELINE_STAGES`, `run_module_analyses()` (falha isolada), `LegalModuleRegistry.resolve(classification, enabled={...})`, `CalculationRegistry`, `research_issues()`, envelope `module_results[module_id]`, `ModuleActivationsLine` sobre abas universais.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, SQLAlchemy, Alembic, Celery, PostgreSQL/JSONB, pytest, TypeScript, React, Next.js, vitest.

**Spec:** `docs/superpowers/specs/2026-10-02-dossie-onda-2-design.md` (§2–§4, §8–§10)

## Global Constraints

- Nenhuma alteração silenciosa do schema 3.0; `module_results` já existe — extensão incompatível exigiria nova versão formal (spec §10).
- `coerce_legacy_analysis()` continua só-leitura; nenhuma tese genérica (reuso de `_is_generic`).
- Vínculo jurídico nunca afirmado por coocorrência de nomes; cláusula sem assinatura/versão nunca tratada como aceita; registro/publicidade nunca presumidos pelo nome do arquivo (§2).
- Comparador preserva texto original da cláusula e posição no documento (§4).
- Cálculos só com cláusula vigente, base, índice, termo e período; IA sugere regra cadastrada, nunca número final livre (§4, §8.10 Onda 0).
- Falha de um módulo vira `blocked` + limitação — nunca impede o dossiê universal nem o outro módulo do par.
- Logs e envelopes sem conteúdo jurídico, prompt, credencial, caminho interno ou stack trace.
- Todos os novos comportamentos com teste falhando primeiro; flags off por padrão.
- Nenhum dado pessoal real em fixtures/corpus.

## Review Focus

- Contrato societário que aciona `contracts` + `corporate`: entidades compartilhadas, sem duplicar eventos/pedidos; módulo primário não absorve o outro (§2).
- Minuta × aditivo × rescisão: diff preserva redação original e datas de vigência (§4).
- Cláusula ambígua sem assinatura: estado `partial`/`blocked` com diligência, nunca "aceita" (§2).
- CCT/casos Onda 1 coexistindo: `labor` continua verde (regressão obrigatória).

---

## File Structure

### Backend (novos)

- `backend/app/modules/contracts/__init__.py`, `module.py`, `checklist.py`
- `backend/app/modules/corporate/__init__.py`, `module.py`, `checklist.py`
- `backend/app/core/normative_source.py`: contrato `NormativeSource` compartilhado (§8)
- `backend/tests/test_contracts_module.py`, `test_corporate_module.py`, `test_onda2a_integration.py`
- `backend/tests/fixtures/contracts_case_v3.json`, `corporate_case_v3.json`
- `backend/evals/contracts_cases.json`, `corporate_cases.json` (6 casos §9 cada)

### Backend (modificar)

- `backend/app/core/classification.py`: tuplas `corporate` (+verificar/estender `contracts`)
- `backend/app/core/config.py`: `DOSSIER_MODULE_CONTRACTS`, `DOSSIER_MODULE_CORPORATE` (`False`)
- `backend/app/core/legal_research.py`: validar `NormativeSource` (bloqueia fonte não recuperada/ambígua/posterior)
- `backend/app/core/pipeline/orchestrator.py`: `_MODULE_FLAGS` + `_module_registry()` (+2)
- `src/components/dossier/sections/sections.tsx` (+ teste): cartões `module_results` onde pertinente

---

### Task 2A-0: Fundação — fonte normativa, classificação e flags

**Files:**

- Create: `backend/app/core/normative_source.py`
- Create: `backend/tests/test_normative_source.py`
- Modify: `backend/app/core/classification.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/legal_research.py`
- Test: `backend/tests/test_normative_source.py`

**Interfaces:**

- Consumes: §8 da spec.
- Produces: `NormativeSource`, `validate_normative_source(source, *, reference_date) -> list[str]`, áreas `corporate` (+`contracts` estendida se o corpus acusar).

- [ ] **Step 1: Escrever testes falhos**
  - `NormativeSource` exige `instrument_id`, `provision_id`, `jurisdiction`, `effective_from`, `retrieved_at`, URL oficial, trecho.
  - Fonte posterior ao fato como fundamento histórico → violação.
  - Fonte ambígua/não recuperada → violação (nunca confirmação).
  - `classify_blocks` com "contrato social, sócios e quotas" → `corporate`; com "cláusula de reajuste e multa" → `contracts`.
- [ ] **Step 2: Executar e confirmar FAIL**
  - Run: `cd backend && pytest tests/test_normative_source.py -q`
  - Expected: FAIL (módulo inexistente + áreas ausentes).
- [ ] **Step 3: Implementar**
  - `NormativeSource(BaseModel)`: `instrument_id`, `provision_id`, `jurisdiction`, `effective_from`, `effective_to | None`, `retrieved_at`, `url`, `hash | None`, `version | None`, `excerpt`.
  - `validate_normative_source()`: violações para URL ausente/não-oficial, `effective_from` posterior ao fato, `retrieved_at` ausente, trecho vazio.
  - `research_issues()` passa a anexar validação normativa quando `source.normative` presente (sem quebrar chamadas antigas).
  - Keywords `corporate`: ("contrato social", "estatuto", "sócio", "sócios", "acionista", "quota", "assembleia", "ata", "recuperação judicial", "falência", "CNPJ", "administrador").
  - Flags `DOSSIER_MODULE_CONTRACTS/CORPORATE = False`.
- [ ] **Step 4: Executar testes + regressão de classificação**
  - Run: `cd backend && pytest tests/test_normative_source.py tests/test_dossier_classification.py -q`
  - Expected: PASS.
- [ ] **Step 5: Commit**
  - `git add backend/app/core/normative_source.py backend/app/core/classification.py backend/app/core/config.py backend/app/core/legal_research.py backend/tests/test_normative_source.py`
  - `git commit -m "feat(onda2): normative source contract and corporate classification (2A foundation)"`

### Task 2A-1: Módulo `contracts@1.0.0`

**Files:**

- Create: `backend/app/modules/contracts/__init__.py`
- Create: `backend/app/modules/contracts/module.py`
- Create: `backend/app/modules/contracts/checklist.py`
- Create: `backend/tests/test_contracts_module.py`
- Create: `backend/tests/fixtures/contracts_case_v3.json`
- Create: `backend/evals/contracts_cases.json`
- Test: `backend/tests/test_contracts_module.py`

**Interfaces:**

- Consumes: `ReconciledCaseData`, `ClassificationResult`, `NormativeSource`, `CalculationRegistry`.
- Produces: `ContractsModule` (`module_id="contracts"`, `version="1.0.0`, `supported_areas=("contracts",)`, `analyze(case_data) -> ModuleResult`), `register_calculation_rules(registry)`, `CONTRACTS_SOURCES`.

- [ ] **Step 1: Escrever testes falhos** (padrão `test_family_module.py`)
  - DESCRIPTOR: `module_id/version/supported_areas`, `calculation_rules`, `research_sources`, `evaluation_cases`.
  - Registry resolve classificação `contracts` → `ContractsModule`.
  - Matriz 6 temas §4 (`formacao`, `versoes`, `prestacao`, `financeiro`, `descumprimento`, `risco`) com `issue_key` estável e refs a fontes reais.
  - Gate: reajuste/multa sem cláusula vigente+base+índice+termo+período → `blocked` listando faltantes (nunca número).
  - Gate: validade/abusividade em abstrato sem relação material → `partial`, nunca conclusão.
  - Versões: minuta×aditivo preservam texto original e posição (diff sem perder redação).
  - Cálculo `reajuste_contratual@1.0` reproduzível; sem parâmetros → `CalculationBlockedError` listando faltantes.
  - Runner não muta o núcleo.
- [ ] **Step 2: Executar e confirmar FAIL** (`pytest tests/test_contracts_module.py -q`).
- [ ] **Step 3: Implementar** `checklist.py` (6 dimensões + keywords), `module.py` (`assess_dimension` com gates §4, `ContractsModule.analyze`, `reajuste_contratual`, `register_calculation_rules`, `CONTRACTS_SOURCES` = CC + legislação especial confirmada + instrumento do caso, `DESCRIPTOR`), `__init__.py`.
- [ ] **Step 4: Corpus + gate** — `evals/contracts_cases.json` (completo, adverso, incompleto, multiarea contracts+corporate, norma antiga, tabela/imagem); `universal_gate.py` PASS nos 6; `analyze()` roda nos 6 sem exceção.
  - Run: `cd backend && python evals/universal_gate.py evals/contracts_cases.json`
  - Expected: `passed: true, total: 6`.
- [ ] **Step 5: Commit**
  - `git commit -m "feat(onda2): contracts module with matrix, gates and corpus (2A)"`

### Task 2A-2: Módulo `corporate@1.0.0`

**Files:** espelho da 2A-1 com `corporate` (`matrix` 7 temas §3; `corporate_case_v3.json`; `corporate_cases.json`; `test_corporate_module.py`).

**Interfaces:** `CorporateModule` (`supported_areas=("corporate",)`), `register_calculation_rules`, `CORPORATE_SOURCES` (CC, Lei das S.A., Lei 11.101, atos oficiais de registro).

- [ ] **Step 1: Escrever testes falhos**
  - DESCRIPTOR + registry resolve `corporate`.
  - 7 temas §3 com refs; grafo de entidades/poderes versionado por IDs estáveis.
  - Gate: responsabilidade pessoal/controle/fraude só por posição → nunca `complete` sem conduta+prova.
  - Gate: quórum sem composição+regra vigente → `blocked`.
  - Gate: pedido × deferimento × concessão de recuperação distintos.
  - Cálculo `participacao_societaria@1.0` (quotas documentadas) e `rateio_cenario@1.0`; avaliação econômica sem método+dados → `CalculationBlockedError`.
  - Runner não muta o núcleo.
- [ ] **Step 2: FAIL esperado.**
- [ ] **Step 3: Implementar** (mesmo esqueleto da 2A-1; `assess_dimension` com gates §3).
- [ ] **Step 4: Corpus + gate** (6 casos §9; `universal_gate` PASS; `analyze()` nos 6).
- [ ] **Step 5: Commit** — `git commit -m "feat(onda2): corporate module with matrix, gates and corpus (2A)"`

### Task 2A-3: Integração do par + apresentação + rollout

**Files:**

- Create: `backend/tests/test_onda2a_integration.py`
- Modify: `backend/app/core/pipeline/orchestrator.py` (`_MODULE_FLAGS`, `_module_registry`)
- Modify: `src/components/dossier/sections/sections.tsx` (+ `__tests__/DossierPage.test.tsx`)
- Test: novos + `tests/test_dossier_modules_pipeline.py` (regressão)

**Interfaces:**

- Consumes: pipeline Onda 0/1 intacto.
- Produces: par coeso atrás de flags individuais; cartões `module_results` nas abas.

- [ ] **Step 1: Escrever testes falhos**
  - Contrato societário multiarea: `module_results` tem `contracts` + `corporate`; fatos/pedidos/partes sem duplicação; primário não absorve o outro.
  - Flags off → `module_results == {}` e universal intacto.
  - Falha de um módulo do par não derruba o outro nem o universal.
  - UI: `module_results` do par renderizam cartões; fallback declara motivo.
- [ ] **Step 2: FAIL esperado.**
- [ ] **Step 3: Implementar** wiring do orquestrador + cartões (espelhar `ModuleActivationsLine`).
- [ ] **Step 4: Gates**
  - Run: `cd backend && pytest tests/test_onda2a_integration.py tests/test_dossier_modules_pipeline.py -q`
  - Run: `cd backend && pytest tests/ -q -p no:warnings` (regressão total)
  - Run: `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`
  - Expected: tudo código 0.
- [ ] **Step 5: Commit** — `git commit -m "feat(onda2): wire contracts+corporate behind flags with cards (2A integration)"`

## Final Verification (2A)

- [ ] `cd backend && pytest tests/test_contracts_module.py tests/test_corporate_module.py tests/test_normative_source.py tests/test_onda2a_integration.py -q`
- [ ] `cd backend && pytest tests/ -q -p no:warnings`
- [ ] `cd backend && python evals/run_gate.py --universal && python evals/universal_gate.py evals/contracts_cases.json && python evals/universal_gate.py evals/corporate_cases.json`
- [ ] `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`
- [ ] Gate jurídico humano por módulo (2 revisores: precisão factual, cobertura, temporalidade, pertinência normativa, utilidade — §9, sem % de êxito)
- [ ] Shadow runs + flag individual por módulo antes de liberar
