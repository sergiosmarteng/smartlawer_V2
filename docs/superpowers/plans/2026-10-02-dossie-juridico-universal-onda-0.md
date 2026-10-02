# Dossiê Jurídico Universal — Onda 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir a ponte legada que publica somente pedidos por um pipeline universal, verificável e multimodal que produza um dossiê útil para qualquer área jurídica.

**Architecture:** A Onda 0 mantém FastAPI, Celery, PostgreSQL/SQLAlchemy e Next.js, mas separa o processamento em estágios persistidos e retomáveis. O pipeline extrai objetos estruturados e imagens com fontes, reconcilia resultados, executa análise universal, verifica invariantes e só então publica atomicamente um artefato schema 3.0 consumido pelo frontend.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, SQLAlchemy, Alembic, Celery, PostgreSQL/JSONB, PyMuPDF/Docling, pytest, TypeScript, React, Next.js, Axios, Tailwind e Playwright/Jest conforme configuração existente.

**Spec:** `docs/superpowers/specs/2026-09-27-dossie-juridico-universal-design.md`

## Global Constraints

- O pipeline novo usa `schema_version = "3.0"`; schema 2.0 continua somente leitura e oferece reprocessamento.
- `coerce_legacy_analysis()` não pode produzir artefato 3.0 nem participar do caminho normal.
- Toda seção possui `SectionState` com `status`, `reason`, `coverage` e `pending_actions`; lista vazia sem explicação é inválida.
- Toda afirmação material possui fonte resolvível ou limitação explícita.
- Imagens são ligadas ao catálogo `DocumentFigure`; não criar catálogo visual concorrente.
- O frontend não deriva teses, estratégias, riscos ou argumentos a partir de pedidos.
- Falha de provedor, parsing, OCR, pesquisa ou cálculo nunca se torna `completed` automaticamente.
- Publicação é atômica, idempotente e impedida após cancelamento.
- Valores monetários usam strings decimais; cálculos finais usam `Decimal` e fórmulas versionadas.
- Consultas de casos, artefatos, fontes, imagens e exportações aplicam autorização por usuário e organização disponível.
- Logs e envelopes de erro não contêm documento, prompt integral, credencial, caminho interno ou stack trace.
- Todos os novos comportamentos são desenvolvidos com teste falhando primeiro.
- A Onda 0 entrega fallback universal para todas as áreas; módulos das Ondas 1–3 terão planos separados.

## Review Focus

- PDF com cabeçalho textual e corpo digitalizado: OCR deve considerar cobertura espacial e não concluir que a página já foi lida; coberto na Task 4.
- Documento substituído durante uma execução: o artefato deve permanecer ligado à revisão/hash do snapshot inicial; coberto na Task 2 e Task 11.
- Imagem com rotação e legenda fora do recorte: o visual deve abrir a página original e preservar coordenadas normalizadas; coberto na Task 7.
- Retry após cancelamento ou publicação: nenhuma tentativa tardia pode publicar ou sobrescrever o artefato; coberto na Task 3 e Task 11.
- Caso multiarea sem módulo especializado: deve receber núcleo universal útil, seções justificadas e limitação de especialização; coberto na Task 5 e Task 8.

---

## File Structure

### Backend

- `backend/app/core/schemas_v3.py`: contrato de domínio 3.0 e invariantes, sem dependência de HTTP ou banco.
- `backend/app/models/case.py`, `case_document.py`, `analysis_stage_run.py`: persistência de caso, documentos e checkpoints.
- `backend/app/crud/case.py`, `stage_run.py`: consultas autorizadas e transições de estágio.
- `backend/app/core/pipeline/contracts.py`: tipos de entrada/saída de estágio.
- `backend/app/core/pipeline/orchestrator.py`: única coordenação do pipeline universal.
- `backend/app/core/classification.py`: classificação multirrótulo e normalização.
- `backend/app/core/module_registry.py`: registro de módulos e fallback universal.
- `backend/app/core/structured_extractor.py`: extração de candidatos por lote.
- `backend/app/core/reconciler.py`: reconciliação global de todos os objetos.
- `backend/app/core/visual_evidence.py`: conversão de figuras existentes em evidência visual.
- `backend/app/core/universal_legal_analyzer.py`: análise jurídica transversal bilateral.
- `backend/app/core/report_composer.py`: composição determinística do artefato.
- `backend/app/core/analysis_verifier.py`: gate estrutural e material.
- `backend/app/api/routes/analysis_v2.py`: API de casos, runs, artefatos, fontes, visuais e versões.

### Frontend

- `src/types/dossier.ts`: tipos schema 3.0.
- `src/hooks/useDossier.ts`, `useAnalysisRun.ts`: acesso ao artefato e polling mensurável.
- `src/components/dossier/*`: header, navegação, estados, seções, fontes e galeria.
- `src/pages/analysis/v2/[id].tsx`: composição fina, sem regras de domínio.

---

### Task 1: Fixar a regressão e introduzir o contrato de domínio 3.0

**Files:**
- Create: `backend/app/core/schemas_v3.py`
- Create: `backend/tests/test_schemas_v3.py`
- Modify: `backend/app/core/schemas_v2.py`
- Test: `backend/tests/test_schemas_v3.py`

**Interfaces:**
- Consumes: tipos conceituais e invariantes das seções 5, 6, 7 e 10 da especificação.
- Produces: `ArtifactContentV3`, `SectionState`, `CoverageV3`, `SourceRefV3`, `VisualEvidence`, `validate_artifact_v3(artifact: ArtifactContentV3) -> list[str]`.

- [ ] **Step 1: Escrever testes falhos para o caso observado e invariantes do schema**

Criar testes com estes nomes e assertivas:

```python
def test_v3_rejects_empty_section_without_reason():
    artifact = minimal_artifact(section_states={"facts": {"status": "complete", "reason": ""}})
    assert "facts" in " ".join(validate_artifact_v3(artifact))

def test_v3_requires_source_or_limitation_for_material_fact():
    artifact = minimal_artifact(facts=[{"id": "f1", "statement": "X", "epistemic_status": "documented"}])
    assert any("f1" in error for error in validate_artifact_v3(artifact))

def test_v3_case_fixture_contains_more_than_claims():
    artifact = ArtifactContentV3.model_validate(load_fixture("family_case_v3.json"))
    assert artifact.claims and artifact.facts and artifact.evidence
    assert artifact.section_states["facts"].status != "blocked"
```

Adicionar `backend/tests/fixtures/family_case_v3.json` com dados sintéticos, sem dados pessoais reais.

- [ ] **Step 2: Executar os testes e confirmar a falha**

Run: `cd backend && pytest tests/test_schemas_v3.py -q`

Expected: FAIL por módulo `app.core.schemas_v3` inexistente.

- [ ] **Step 3: Implementar os tipos exatos em `schemas_v3.py`**

Definir:

```python
ARTIFACT_SCHEMA_VERSION = "3.0"

class SectionCoverage(BaseModel): ...
class SectionState(BaseModel): ...
class AnalysisScope(BaseModel): ...
class ModuleActivation(BaseModel): ...
class Party(BaseModel): ...
class TimelineEvent(BaseModel): ...
class ClaimV3(BaseModel): ...
class FactV3(BaseModel): ...
class Controversy(BaseModel): ...
class EvidenceItemV3(BaseModel): ...
class VisualEvidence(BaseModel): ...
class LegalReferenceV3(BaseModel): ...
class ProceduralIssue(BaseModel): ...
class ThesisV3(BaseModel): ...
class CalculationV3(BaseModel): ...
class RiskV3(BaseModel): ...
class ActionItem(BaseModel): ...
class ClientQuestion(BaseModel): ...
class SourceRefV3(BaseModel): ...
class LimitationV3(BaseModel): ...
class CoverageV3(BaseModel): ...
class ExecutiveSummary(BaseModel): ...
class ArtifactContentV3(BaseModel): ...
def validate_artifact_v3(artifact: ArtifactContentV3) -> list[str]: ...
```

Usar os nomes e enumerações da especificação. Manter `schemas_v2.py` intacto para leitura legada e adicionar docstring deixando explícito que `coerce_legacy_analysis()` não é produtor V3.

- [ ] **Step 4: Executar testes de schema V2 e V3**

Run: `cd backend && pytest tests/test_schemas_v2.py tests/test_schemas_v3.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/schemas_v2.py backend/app/core/schemas_v3.py backend/tests/test_schemas_v3.py backend/tests/fixtures/family_case_v3.json
git commit -m "feat(dossie): define universal artifact schema v3"
```

### Task 2: Persistir casos, documentos do caso e checkpoints de estágio

**Files:**
- Create: `backend/app/models/case.py`
- Create: `backend/app/models/case_document.py`
- Create: `backend/app/models/analysis_stage_run.py`
- Create: `backend/app/crud/case.py`
- Create: `backend/app/crud/stage_run.py`
- Create: `backend/alembic/versions/20261002_0011_dossier_cases_stages.py`
- Create: `backend/tests/test_dossier_persistence.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/analysis_run.py`
- Modify: `backend/app/models/analysis_artifact.py`
- Test: `backend/tests/test_dossier_persistence.py`

**Interfaces:**
- Consumes: IDs de `User`, `Document`, `DocumentRevision` e estados existentes de `AnalysisRun`.
- Produces: `Case`, `CaseDocument`, `AnalysisStageRun`; `create_case`, `attach_document`, `start_stage`, `finish_stage`, `fail_stage`, `get_resume_point`.

- [ ] **Step 1: Escrever testes falhos de caso, snapshot e retomada**

Testar:

- um documento não pode ser anexado a caso de outro usuário;
- o snapshot do run guarda `case_id`, `document_ids`, `revision_ids` e hashes;
- `get_resume_point()` retorna o primeiro estágio não concluído;
- substituir o arquivo depois do snapshot não altera `revision_ids` do run;
- `(run_id, stage, attempt)` é único.

- [ ] **Step 2: Executar o arquivo de teste**

Run: `cd backend && pytest tests/test_dossier_persistence.py -q`

Expected: FAIL por modelos e funções inexistentes.

- [ ] **Step 3: Criar modelos e migration reversível**

Assinaturas obrigatórias:

```python
def create_case(db: Session, *, user_id: UUID, name: str | None = None) -> Case: ...
def attach_document(db: Session, *, case: Case, document: Document, role: str) -> CaseDocument: ...
def start_stage(db: Session, *, run: AnalysisRun, stage: str, attempt: int) -> AnalysisStageRun: ...
def finish_stage(db: Session, *, stage_run: AnalysisStageRun, metrics: dict | None = None) -> AnalysisStageRun: ...
def fail_stage(db: Session, *, stage_run: AnalysisStageRun, code: str, safe_message: str, retryable: bool) -> AnalysisStageRun: ...
def get_resume_point(db: Session, *, run: AnalysisRun, ordered_stages: list[str]) -> str | None: ...
```

Adicionar `case_id` a `analysis_runs` e `analysis_artifacts`; não remover `document_id` nesta onda para preservar compatibilidade.

- [ ] **Step 4: Executar migration em upgrade/downgrade e testes**

Run: `cd backend && alembic upgrade head && alembic downgrade 20260925_0010 && alembic upgrade head && pytest tests/test_dossier_persistence.py -q`

Expected: comandos encerram com código 0 e testes PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models backend/app/crud/case.py backend/app/crud/stage_run.py backend/alembic/versions/20261002_0011_dossier_cases_stages.py backend/tests/test_dossier_persistence.py
git commit -m "feat(dossie): persist cases and pipeline stages"
```

### Task 3: Tornar transições, progresso e publicação honestos

**Files:**
- Modify: `backend/app/models/analysis_run.py`
- Modify: `backend/app/crud/run.py`
- Modify: `backend/app/api/routes/analysis_v2.py`
- Create: `backend/tests/test_dossier_run_state.py`
- Test: `backend/tests/test_analysis_runs.py`
- Test: `backend/tests/test_dossier_run_state.py`

**Interfaces:**
- Consumes: `AnalysisStageRun` e ordem de estágios da Task 2.
- Produces: `calculate_progress(run, stage_runs) -> ProgressSnapshot`, `publish_artifact_v3(...) -> AnalysisArtifact`.

- [ ] **Step 1: Escrever testes falhos de progresso e publicação**

Cobrir:

- estágio `extraction` nunca retorna 100%;
- progresso usa documentos/páginas/lotes/verificações concluídos;
- run cancelado rejeita retry tardio;
- run já publicado rejeita segunda publicação;
- `completed` exige `stage == publication` e relatório aprovado;
- artefato V3 salva `schema_version == "3.0"`.

- [ ] **Step 2: Executar testes focados**

Run: `cd backend && pytest tests/test_dossier_run_state.py tests/test_analysis_runs.py -q`

Expected: FAIL nas novas assertivas.

- [ ] **Step 3: Implementar máquina de estados e progresso**

Definir `PIPELINE_STAGES` em `backend/app/core/pipeline/contracts.py`:

```python
PIPELINE_STAGES = (
    "ingestion", "extraction", "classification", "coverage_planning",
    "structured_extraction", "reconciliation", "legal_analysis",
    "legal_research", "calculations", "verification", "composition",
    "publication",
)
```

`publish_artifact_v3(db, *, run, artifact, report, expected_version)` valida cancelamento, versão, estágio final e status do verificador na mesma transação.

- [ ] **Step 4: Executar testes de runs e API existentes**

Run: `cd backend && pytest tests/test_dossier_run_state.py tests/test_analysis_runs.py tests/test_analysis_v2.py -q`

Expected: PASS, incluindo compatibilidade V2.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/analysis_run.py backend/app/crud/run.py backend/app/api/routes/analysis_v2.py backend/app/core/pipeline/contracts.py backend/tests/test_dossier_run_state.py backend/tests/test_analysis_runs.py
git commit -m "feat(dossie): enforce honest run state and publication"
```

### Task 4: Garantir inventário integral, OCR seletivo e fontes por bloco

**Files:**
- Modify: `backend/app/core/extraction.py`
- Modify: `backend/app/core/coverage_planner.py`
- Modify: `backend/app/crud/extraction.py`
- Create: `backend/tests/test_dossier_extraction.py`
- Test: `backend/tests/test_extraction.py`
- Test: `backend/tests/test_coverage_planner.py`

**Interfaces:**
- Consumes: `DocumentRevision`, `SourceBlock`, limites de configuração e arquivo original.
- Produces: `ExtractionInventory`, `ExtractionPage`, `plan_revision_batches(...)`, referências estáveis por `block_uid`.

- [ ] **Step 1: Escrever testes falhos de cobertura adversarial**

Testar:

- 35 páginas e pedidos no final entram no plano;
- cabeçalho textual com corpo-imagem marca `needs_ocr=True`;
- página rotacionada preserva `rotation` e bbox normalizado;
- todos os blocos aparecem em lote ou `unprocessed_block_ids`;
- blocos de revisões diferentes nunca se misturam;
- orçamento excedido produz estado parcial acionável, não corte silencioso.

- [ ] **Step 2: Executar os testes de extração**

Run: `cd backend && pytest tests/test_dossier_extraction.py tests/test_extraction.py tests/test_coverage_planner.py -q`

Expected: FAIL nos novos cenários.

- [ ] **Step 3: Implementar contratos e planejamento por revisão**

Assinaturas:

```python
def extract_revision_inventory(file_path: str, revision_id: str) -> ExtractionInventory: ...
def page_needs_ocr(*, text_blocks: list[dict], image_blocks: list[dict], page_area: float) -> bool: ...
def plan_revision_batches(blocks: list[SourceBlockInput], *, max_batch_tokens: int, overlap_blocks: int, max_batches: int) -> CoveragePlan: ...
```

Persistir método, qualidade, rotação, bbox e hash. Não depender de `text[:N]` no pipeline V3.

- [ ] **Step 4: Executar testes focados e regressão de figuras**

Run: `cd backend && pytest tests/test_dossier_extraction.py tests/test_extraction.py tests/test_coverage_planner.py tests/test_figures.py tests/test_docling_extraction.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/extraction.py backend/app/core/coverage_planner.py backend/app/crud/extraction.py backend/tests/test_dossier_extraction.py
git commit -m "feat(dossie): inventory every page and source block"
```

### Task 5: Classificar áreas e selecionar módulos com fallback universal

**Files:**
- Create: `backend/app/core/classification.py`
- Create: `backend/app/core/module_registry.py`
- Create: `backend/app/modules/universal/__init__.py`
- Create: `backend/app/modules/universal/module.py`
- Create: `backend/tests/test_dossier_classification.py`
- Modify: `backend/app/modules/__init__.py`
- Test: `backend/tests/test_labor_module.py`

**Interfaces:**
- Consumes: amostra estruturada de blocos e overrides do snapshot.
- Produces: `ClassificationResult`, `LegalModule`, `LegalModuleRegistry.resolve(classification) -> list[LegalModule]`.

- [ ] **Step 1: Escrever testes falhos de multirrótulo e fallback**

Testar classificação determinística normalizada para:

- família + processo civil;
- contrato + tributário;
- assunto desconhecido retorna `primary_area="general"`;
- override humano prevalece e fica auditável;
- registry sempre inclui `universal@1.0`;
- módulo ausente gera `ModuleActivation(status="fallback")`.

- [ ] **Step 2: Executar o teste**

Run: `cd backend && pytest tests/test_dossier_classification.py -q`

Expected: FAIL por módulos inexistentes.

- [ ] **Step 3: Implementar interfaces**

```python
class ClassificationResult(BaseModel):
    primary_area: str
    related_areas: list[str]
    document_types: list[str]
    procedure: str | None
    phase: str | None
    source: Literal["model", "human_override", "fallback"]
    confidence: float | None

class LegalModule(Protocol):
    module_id: str
    version: str
    supported_areas: tuple[str, ...]
    def requirements(self) -> ModuleRequirements: ...

class LegalModuleRegistry:
    def register(self, module: LegalModule) -> None: ...
    def resolve(self, classification: ClassificationResult) -> list[LegalModule]: ...
```

A classificação por modelo deverá receber saída estruturada validada; erro usa fallback `general`, não encerra o pipeline.

- [ ] **Step 4: Executar testes universal e trabalhista existente**

Run: `cd backend && pytest tests/test_dossier_classification.py tests/test_labor_module.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/classification.py backend/app/core/module_registry.py backend/app/modules backend/tests/test_dossier_classification.py
git commit -m "feat(dossie): add multiarea module registry"
```

### Task 6: Extrair e reconciliar objetos estruturados por lote

**Files:**
- Create: `backend/app/core/structured_extractor.py`
- Modify: `backend/app/core/reconciler.py`
- Create: `backend/tests/test_structured_extractor.py`
- Create: `backend/tests/test_dossier_reconciler.py`

**Interfaces:**
- Consumes: `CoveragePlan`, `SourceBlockInput`, `ClassificationResult` e provedor estruturado.
- Produces: `BatchExtraction`, `extract_batch(...)`, `reconcile_extractions(...) -> ReconciledCaseData`.

- [ ] **Step 1: Escrever testes falhos de extração e conflitos**

Testar:

- saída inválida do modelo falha somente o lote e registra código seguro;
- cada objeto extraído mantém `source_refs` dos blocos;
- pedido repetido une ocorrências e fontes;
- valores divergentes não são sobrescritos e geram controvérsia;
- fatos com redação semelhante, mas autores distintos, permanecem separados;
- prompt injection presente no bloco é tratado como texto documental;
- lote sobreposto não duplica objeto reconciliado.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_structured_extractor.py tests/test_dossier_reconciler.py -q`

Expected: FAIL por interfaces inexistentes.

- [ ] **Step 3: Implementar extração com resposta estruturada e reconciliação**

```python
def extract_batch(batch: PlannedBatch, *, provider: StructuredProvider, context: ExtractionContext) -> BatchExtraction: ...
def reconcile_extractions(extractions: list[BatchExtraction]) -> ReconciledCaseData: ...
```

O prompt de sistema declara o documento como dado não confiável. O parser aceita somente o schema de `BatchExtraction`; nunca tenta recuperar JSON com `eval` ou regex permissiva.

- [ ] **Step 4: Executar testes novos e reconciliador anterior**

Run: `cd backend && pytest tests/test_structured_extractor.py tests/test_dossier_reconciler.py tests/test_schemas_v3.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/structured_extractor.py backend/app/core/reconciler.py backend/tests/test_structured_extractor.py backend/tests/test_dossier_reconciler.py
git commit -m "feat(dossie): extract and reconcile sourced case data"
```

### Task 7: Integrar imagens e páginas-fonte ao artefato

**Files:**
- Modify: `backend/app/models/document_figure.py`
- Modify: `backend/app/crud/figure.py`
- Create: `backend/app/core/visual_evidence.py`
- Create: `backend/alembic/versions/20261002_0012_visual_evidence_metadata.py`
- Create: `backend/tests/test_visual_evidence.py`
- Modify: `backend/tests/test_figures.py`

**Interfaces:**
- Consumes: `DocumentFigure`, `DocumentRevision`, `SourceBlock` e `ReconciledCaseData`.
- Produces: `build_visual_evidence(...) -> list[VisualEvidence]`, render seguro de miniatura e página.

- [ ] **Step 1: Escrever testes falhos do contrato visual**

Cobrir:

- bbox normalizado respeita rotação;
- figura mantém `document_id`, `revision_id`, página e source ref;
- legenda fora do recorte força `requires_page_context=True`;
- lista vazia com blocos de imagem vira `extraction_failed`, não “sem imagens”;
- visual sensível inicia oculto;
- documento de outro usuário não pode resolver miniatura ou página.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_visual_evidence.py tests/test_figures.py -q`

Expected: FAIL nos novos contratos.

- [ ] **Step 3: Implementar metadados e conversão sem duplicar catálogo**

```python
def build_visual_evidence(
    *, figures: list[DocumentFigure], blocks: list[SourceBlock], links: VisualLinks
) -> list[VisualEvidence]: ...

def normalize_region(*, bbox: dict, page_width: float, page_height: float, rotation: int) -> NormalizedRegion: ...
```

Guardar chaves opacas de storage, nunca caminho absoluto no payload.

- [ ] **Step 4: Verificar migration e testes visuais**

Run: `cd backend && alembic upgrade head && pytest tests/test_visual_evidence.py tests/test_figures.py tests/test_docling_extraction.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/document_figure.py backend/app/crud/figure.py backend/app/core/visual_evidence.py backend/alembic/versions/20261002_0012_visual_evidence_metadata.py backend/tests/test_visual_evidence.py backend/tests/test_figures.py
git commit -m "feat(dossie): promote document images to sourced evidence"
```

### Task 8: Produzir análise jurídica universal bilateral

**Files:**
- Create: `backend/app/core/universal_legal_analyzer.py`
- Create: `backend/app/modules/universal/prompts.py`
- Create: `backend/tests/test_universal_legal_analyzer.py`

**Interfaces:**
- Consumes: `ReconciledCaseData`, módulos resolvidos, polo, objetivo e data de referência.
- Produces: `UniversalAnalysis` com questões processuais, teses, riscos, ações, perguntas e limitações.

- [ ] **Step 1: Escrever testes falhos de análise bilateral**

Testar:

- polo do requerido ainda produz elementos adversos;
- tese referencia premissas e fontes existentes;
- assunto sem módulo retorna análise universal e limitação `SPECIALIZATION_UNAVAILABLE`;
- ausência de datas bloqueia conclusão de prescrição, mas cria pergunta/ação;
- resposta vazia ou genérica do provedor é rejeitada;
- nenhuma tese é copiada de `FALLBACK_THESES`.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_universal_legal_analyzer.py -q`

Expected: FAIL por analisador inexistente.

- [ ] **Step 3: Implementar análise estruturada**

```python
def analyze_universal_case(
    data: ReconciledCaseData,
    *,
    modules: list[LegalModule],
    represented_side: str,
    objective: str | None,
    reference_date: date,
    provider: StructuredProvider,
) -> UniversalAnalysis: ...
```

Separar prompts por responsabilidade; o resultado deve validar IDs e refs contra `ReconciledCaseData`.

- [ ] **Step 4: Executar testes de análise e segurança RAG**

Run: `cd backend && pytest tests/test_universal_legal_analyzer.py tests/test_security_rag.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/universal_legal_analyzer.py backend/app/modules/universal/prompts.py backend/tests/test_universal_legal_analyzer.py
git commit -m "feat(dossie): add bilateral universal legal analysis"
```

### Task 9: Integrar pesquisa jurídica e cálculos determinísticos

**Files:**
- Modify: `backend/app/core/legal_research.py`
- Modify: `backend/app/core/calculations.py`
- Create: `backend/app/models/legal_research_result.py`
- Create: `backend/app/models/calculation_result.py`
- Create: `backend/alembic/versions/20261002_0013_research_calculation_results.py`
- Create: `backend/tests/test_dossier_research_calculations.py`
- Test: `backend/tests/test_legal_research.py`
- Test: `backend/tests/test_calculations.py`

**Interfaces:**
- Consumes: questões jurídicas e cálculos solicitados pelo núcleo/módulos.
- Produces: `research_issues(...) -> ResearchBatchResult`, `execute_registered_calculation(...) -> CalculationV3`.

- [ ] **Step 1: Escrever testes falhos de origem e reprodutibilidade**

Cobrir:

- fonte citada no documento e pesquisada pelo sistema permanecem separadas;
- pesquisa indisponível produz resultado parcial sem apagar análise documental;
- resultado guarda URL, órgão, data de consulta e trecho;
- fórmula desconhecida é bloqueada;
- `Decimal` e arredondamento `half_up_centavos` reproduzem o resultado;
- duas execuções com mesmas entradas geram mesmo conteúdo/hash.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_dossier_research_calculations.py tests/test_legal_research.py tests/test_calculations.py -q`

Expected: FAIL nas novas interfaces.

- [ ] **Step 3: Implementar persistência e serviços**

```python
def research_issues(issues: list[ResearchIssue], *, sources: list[AuthorizedSource], reference_date: date) -> ResearchBatchResult: ...
def execute_registered_calculation(request: CalculationRequest, *, registry: CalculationRegistry) -> CalculationV3: ...
```

Não adicionar scraping ou fonte não aprovada nesta tarefa.

- [ ] **Step 4: Executar migration e testes**

Run: `cd backend && alembic upgrade head && pytest tests/test_dossier_research_calculations.py tests/test_legal_research.py tests/test_calculations.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/legal_research.py backend/app/core/calculations.py backend/app/models/legal_research_result.py backend/app/models/calculation_result.py backend/alembic/versions/20261002_0013_research_calculation_results.py backend/tests/test_dossier_research_calculations.py
git commit -m "feat(dossie): add sourced research and deterministic calculations"
```

### Task 10: Verificar e compor o artefato sem geração livre final

**Files:**
- Modify: `backend/app/core/analysis_verifier.py`
- Create: `backend/app/core/report_composer.py`
- Create: `backend/tests/test_dossier_verifier.py`
- Create: `backend/tests/test_report_composer.py`
- Test: `backend/tests/test_verifier.py`

**Interfaces:**
- Consumes: dados reconciliados, análise, pesquisa, cálculos, visuais e cobertura.
- Produces: `VerificationReportV3`, `verify_artifact_v3(...)`, `compose_artifact(...) -> ArtifactContentV3`.

- [ ] **Step 1: Escrever testes falhos do gate material**

Testar:

- `completed` é recusado com página/bloco não processado;
- fonte existente, mas sem suporte, gera erro/aviso material;
- pedido explícito ausente impede `completed`;
- seção vazia sem razão impede publicação;
- imagem com source inexistente impede publicação;
- reparo estrutural não inventa fonte nem fato;
- composer apenas reorganiza objetos e gera resumo por regras determinísticas.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_dossier_verifier.py tests/test_report_composer.py tests/test_verifier.py -q`

Expected: FAIL nas novas funções.

- [ ] **Step 3: Implementar verificador e composer**

```python
def verify_artifact_v3(artifact: ArtifactContentV3, *, module_requirements: list[ModuleRequirements]) -> VerificationReportV3: ...
def compose_artifact(inputs: CompositionInputs) -> ArtifactContentV3: ...
def decide_publication_status(report: VerificationReportV3, *, has_useful_content: bool) -> Literal["completed", "partial", "blocked", "failed"]: ...
```

Nenhuma chamada de IA em `report_composer.py`.

- [ ] **Step 4: Executar testes de schema e verificador**

Run: `cd backend && pytest tests/test_schemas_v3.py tests/test_dossier_verifier.py tests/test_report_composer.py tests/test_verifier.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/analysis_verifier.py backend/app/core/report_composer.py backend/tests/test_dossier_verifier.py backend/tests/test_report_composer.py
git commit -m "feat(dossie): verify and compose universal artifacts"
```

### Task 11: Orquestrar o pipeline V3 e retirar a ponte legada do caminho normal

**Files:**
- Create: `backend/app/core/pipeline/__init__.py`
- Create: `backend/app/core/pipeline/orchestrator.py`
- Modify: `backend/app/tasks/document_tasks.py`
- Create: `backend/tests/test_dossier_pipeline.py`
- Modify: `backend/tests/test_analysis_states.py`

**Interfaces:**
- Consumes: serviços e contratos das Tasks 2–10.
- Produces: `run_universal_pipeline(db, *, run_id: UUID) -> AnalysisArtifact | None`; task Celery delegando ao orquestrador.

- [ ] **Step 1: Escrever teste de integração que reproduz e elimina o defeito**

Criar fixture com pedidos, fatos, provas, referência jurídica e imagem. Assertar:

```python
artifact = run_pipeline_fixture(...)
assert artifact.schema_version == "3.0"
assert artifact.content["claims"]
assert artifact.content["facts"]
assert artifact.content["evidence"]
assert artifact.content["legal_references"]
assert artifact.content["visuals"]
assert artifact.content["coverage"]["pages_total"] > 0
assert artifact.status in {"completed", "partial"}
```

Também testar retry a partir do primeiro estágio incompleto, documento alterado após snapshot, cancelamento antes da publicação e falha de um lote.

- [ ] **Step 2: Executar testes do pipeline**

Run: `cd backend && pytest tests/test_dossier_pipeline.py tests/test_analysis_states.py -q`

Expected: FAIL porque a task ainda chama `coerce_legacy_analysis()`.

- [ ] **Step 3: Implementar o orquestrador e trocar a task**

```python
def run_universal_pipeline(db: Session, *, run_id: UUID) -> AnalysisArtifact | None: ...
```

O orquestrador executa `PIPELINE_STAGES`, persiste checkpoints e publica somente depois do verificador. `process_pdf_task` pode manter a projeção V1 para compatibilidade, mas a produção V3 não lê o resultado V1 e não chama `coerce_legacy_analysis()`.

- [ ] **Step 4: Executar regressão completa do backend**

Run: `cd backend && pytest -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/pipeline backend/app/tasks/document_tasks.py backend/tests/test_dossier_pipeline.py backend/tests/test_analysis_states.py
git commit -m "feat(dossie): run universal pipeline instead of legacy coercion"
```

### Task 12: Completar API de casos, artefatos, fontes, imagens e versões

**Files:**
- Modify: `backend/app/schemas/analysis_v2.py`
- Modify: `backend/app/api/routes/analysis_v2.py`
- Modify: `backend/app/core/storage.py`
- Create: `backend/tests/test_dossier_api_v3.py`
- Modify: `backend/tests/test_analysis_v2.py`

**Interfaces:**
- Consumes: persistência e artefatos V3 das Tasks anteriores.
- Produces: endpoints da seção 11 da especificação e envelopes seguros.

- [ ] **Step 1: Escrever testes de contrato e autorização**

Cobrir:

- criar e ler caso;
- anexar documento próprio e rejeitar documento alheio;
- criar run com snapshot completo;
- filtrar runs por `case_id` e `document_id`;
- obter seção com seu `SectionState`;
- listar e resolver fontes;
- listar visual, miniatura e render da página por URL temporária;
- versões e comparação;
- resume somente para `blocked`/`failed` retomável;
- IDs de outro usuário retornam 404;
- erro não contém prompt, caminho, segredo ou stack trace.

- [ ] **Step 2: Executar testes da API**

Run: `cd backend && pytest tests/test_dossier_api_v3.py tests/test_analysis_v2.py -q`

Expected: FAIL nos endpoints novos.

- [ ] **Step 3: Implementar schemas HTTP e endpoints**

Preservar as rotas V2 existentes e adicionar casos, visuais, versões, comparação e resume. `GET /analyses/{id}` devolve schema 2.0 ou 3.0 conforme artefato; se 2.0, inclui `legacy=true` e `reanalyze_available=true`.

- [ ] **Step 4: Executar testes de API, auth e exclusão**

Run: `cd backend && pytest tests/test_dossier_api_v3.py tests/test_analysis_v2.py tests/test_auth.py tests/test_ops_deletion.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/analysis_v2.py backend/app/api/routes/analysis_v2.py backend/app/core/storage.py backend/tests/test_dossier_api_v3.py backend/tests/test_analysis_v2.py
git commit -m "feat(dossie): expose universal dossier API"
```

### Task 13: Criar contratos e hooks do frontend

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `vitest.config.ts`
- Create: `src/test/setup.ts`
- Create: `src/types/dossier.ts`
- Create: `src/hooks/useDossier.ts`
- Create: `src/hooks/useAnalysisRun.ts`
- Modify: `src/types/workflow.ts`
- Create: `src/hooks/__tests__/useDossier.test.tsx`
- Create: `src/hooks/__tests__/useAnalysisRun.test.tsx`

**Interfaces:**
- Consumes: respostas HTTP da Task 12.
- Produces: `DossierArtifactV3`, `useDossier({artifactId, documentId})`, `useAnalysisRun(runId)`.

- [ ] **Step 1: Escrever testes falhos dos hooks**

Primeiro adicionar `vitest`, `jsdom`, `@testing-library/react` e `@testing-library/jest-dom` como dependências de desenvolvimento; criar o script `"test:unit": "vitest run"`, configurar alias `@` para `src` e carregar `src/test/setup.ts` no ambiente `jsdom`.

Testar:

- route ID de documento resolve último artefato publicado;
- schema 2.0 mostra estado legado e ação de reprocessamento;
- ETag/304 preserva conteúdo anterior;
- polling para em estado terminal;
- progresso de extração não aparece como 100%;
- erro seguro do backend vira mensagem em português sem detalhes técnicos.

- [ ] **Step 2: Executar testes**

Run: `npm run test:unit -- src/hooks/__tests__/useDossier.test.tsx src/hooks/__tests__/useAnalysisRun.test.tsx`

Expected: FAIL por arquivos inexistentes.

- [ ] **Step 3: Implementar tipos e hooks**

```typescript
export function useDossier(input: { artifactId?: string; documentId?: string }): UseDossierResult;
export function useAnalysisRun(runId?: string): UseAnalysisRunResult;
```

Centralizar resolução/fetch; nenhum componente de apresentação faz chamada direta à API.

- [ ] **Step 4: Executar typecheck e testes**

Run: `npm run test:unit -- src/hooks/__tests__/useDossier.test.tsx src/hooks/__tests__/useAnalysisRun.test.tsx && npx tsc --noEmit`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json vitest.config.ts src/test/setup.ts src/types/dossier.ts src/types/workflow.ts src/hooks/useDossier.ts src/hooks/useAnalysisRun.ts src/hooks/__tests__
git commit -m "feat(dossie): add typed dossier data hooks"
```

### Task 14: Implementar a interface completa e a galeria visual

**Files:**
- Create: `src/components/dossier/DossierHeader.tsx`
- Create: `src/components/dossier/DossierTabs.tsx`
- Create: `src/components/dossier/SectionStateBanner.tsx`
- Create: `src/components/dossier/SourceViewer.tsx`
- Create: `src/components/dossier/VisualGallery.tsx`
- Create: `src/components/dossier/VisualViewer.tsx`
- Create: `src/components/dossier/sections/*.tsx`
- Create: `src/components/dossier/__tests__/DossierPage.test.tsx`
- Modify: `src/pages/analysis/v2/[id].tsx`

**Interfaces:**
- Consumes: `DossierArtifactV3` e hooks da Task 13.
- Produces: página acessível com todas as seções da especificação, fontes e galeria.

- [ ] **Step 1: Escrever testes falhos da experiência**

Cobrir:

- visão geral mostra áreas, cobertura, riscos e ações;
- todas as abas renderizam conteúdo real ou motivo do estado vazio;
- fato exibe estado epistêmico e abre fonte;
- imagem abre ampliada e oferece “Ver na página original”;
- item sensível inicia oculto;
- galeria filtra por documento, página, tipo e status;
- navegação de tabs funciona por teclado;
- nenhum painel deriva tese a partir de `claims`;
- artefato parcial exibe pendências antes de aprovação.

- [ ] **Step 2: Executar teste da página**

Run: `npm run test:unit -- src/components/dossier/__tests__/DossierPage.test.tsx`

Expected: FAIL por componentes inexistentes.

- [ ] **Step 3: Implementar componentes focados e reduzir a página a composição**

Cada arquivo de seção recebe `{artifact, sectionState, onOpenSource, onOpenVisual}`. Não duplicar conversores `asArray`/`asText`; normalizar no hook e manter escape padrão do React.

- [ ] **Step 4: Executar testes, lint, typecheck e build**

Run: `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`

Expected: todos os comandos encerram com código 0.

- [ ] **Step 5: Commit**

```bash
git add src/components/dossier src/pages/analysis/v2/[id].tsx
git commit -m "feat(dossie): render complete universal dossier"
```

### Task 15: Completar revisão, comparação e exportação reproduzível

**Files:**
- Modify: `backend/app/api/routes/analysis_v2.py`
- Modify: `backend/app/core/v2_export.py`
- Modify: `backend/app/crud/run.py`
- Create: `backend/app/core/artifact_diff.py`
- Create: `backend/tests/test_dossier_review_export.py`
- Modify: `src/components/dossier/sections/ReviewSection.tsx`

**Interfaces:**
- Consumes: artefatos V3 imutáveis, eventos de revisão e visuais.
- Produces: `compare_artifacts(before, after) -> ArtifactDiff`, status de revisão autorizado e exportação estável.

- [ ] **Step 1: Escrever testes falhos de revisão e versão**

Testar:

- correção preserva before/after, autoria, motivo e versão;
- versão concorrente retorna 409;
- aprovação exige usuário autorizado e ausência de bloqueios materiais;
- comparação identifica adição, remoção e alteração por ID estável;
- mesma versão/modo gera mesmo job ID e mesmo relatório;
- relatório inclui referências das imagens sem incorporar URL expirada.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_dossier_review_export.py tests/test_chat_exports_v2.py -q`

Expected: FAIL nas novas funções.

- [ ] **Step 3: Implementar diff, revisão e exportação**

```python
def compare_artifacts(before: ArtifactContentV3, after: ArtifactContentV3) -> ArtifactDiff: ...
def build_v3_report(artifact: ArtifactContentV3, *, mode: Literal["executive", "complete"], review_events: list[ReviewEvent]) -> str: ...
```

Aplicar eventos como nova versão/projeção, nunca mutar `AnalysisArtifact.content` publicado.

- [ ] **Step 4: Executar backend e teste da seção de revisão**

Run: `cd backend && pytest tests/test_dossier_review_export.py tests/test_chat_exports_v2.py -q`

Run: `npm run test:unit -- src/components/dossier/__tests__/DossierPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/analysis_v2.py backend/app/core/v2_export.py backend/app/core/artifact_diff.py backend/app/crud/run.py backend/tests/test_dossier_review_export.py src/components/dossier/sections/ReviewSection.tsx
git commit -m "feat(dossie): add versioned review compare and export"
```

### Task 16: Adicionar telemetria segura, avaliação e rollout da Onda 0

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `playwright.config.ts`
- Create: `tests/e2e/dossier-v3.spec.ts`
- Modify: `backend/app/core/audit.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/evals/run_gate.py`
- Create: `backend/evals/universal_dossier_cases.json`
- Create: `backend/tests/test_dossier_observability.py`
- Create: `backend/tests/test_dossier_security.py`
- Create: `docs/operations/dossier-v3-rollout.md`
- Create: `docs/operations/dossier-v3-rollback.md`

**Interfaces:**
- Consumes: métricas de estágio, artefato, revisão e configurações anteriores.
- Produces: eventos seguros, gate de avaliação, feature flags e runbooks.

- [ ] **Step 1: Escrever testes falhos de segurança e métricas**

Adicionar `@playwright/test` como dependência de desenvolvimento e o script `"test:e2e": "playwright test"`. Configurar `playwright.config.ts` para usar `PLAYWRIGHT_BASE_URL`, sem credenciais fixas no repositório.

Cobrir:

- logs não contêm trecho, prompt, chave, path ou stack;
- métricas incluem páginas, blocos, imagens, lotes, fontes, duração e status por seção;
- prompt injection em documento não modifica instruções do pipeline;
- acesso cruzado a artefato/fonte/visual/export retorna 404;
- feature flag desativada mantém leitura V2 e não cria V3;
- gate falha para artefato só com pedidos ou com fontes inválidas.

- [ ] **Step 2: Executar testes**

Run: `cd backend && pytest tests/test_dossier_observability.py tests/test_dossier_security.py -q`

Expected: FAIL nos novos controles.

- [ ] **Step 3: Implementar telemetria, flags e corpus de avaliação**

Adicionar configurações:

```python
DOSSIER_V3_ENABLED: bool = False
DOSSIER_V3_SHADOW_MODE: bool = False
DOSSIER_V3_ALLOWED_USER_IDS: str = ""
DOSSIER_V3_MAX_CONCURRENT_RUNS: int = 2
```

O corpus contém somente conteúdo sintético ou anonimizado e cobre casos de família, cível, contrato, trabalhista e assunto sem módulo.

- [ ] **Step 4: Executar todos os gates**

Run: `cd backend && pytest -q && python evals/run_gate.py`

Run: `npm run test:unit && npm run lint && npx tsc --noEmit && npm run build`

Expected: todos os comandos encerram com código 0; gate rejeita fixture degradada e aprova corpus válido.

- [ ] **Step 5: Implementar E2E autenticado do Dossiê V3**

`tests/e2e/dossier-v3.spec.ts` deve usar usuário e fixture criados por setup de teste, nunca credenciais de produção. Cobrir upload, progresso, seções, fonte, imagem/página original, revisão, comparação e exportação.

Run: `npm run test:e2e -- tests/e2e/dossier-v3.spec.ts`

Expected: PASS contra ambiente de teste com `DOSSIER_V3_ENABLED=true`.

- [ ] **Step 6: Documentar rollout e rollback**

`dossier-v3-rollout.md` deve descrever migration, shadow runs, amostra interna, métricas, limites, expansão e critério de pausa. `dossier-v3-rollback.md` deve preservar artefatos V3, desativar novas execuções e manter leitura sem perda de dados.

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json playwright.config.ts tests/e2e/dossier-v3.spec.ts backend/app/core/audit.py backend/app/core/config.py backend/evals backend/tests/test_dossier_observability.py backend/tests/test_dossier_security.py docs/operations/dossier-v3-rollout.md docs/operations/dossier-v3-rollback.md
git commit -m "feat(dossie): gate and roll out universal dossier v3"
```

## Final Verification

- [ ] Executar migrations em banco limpo e cópia de staging.
- [ ] Executar `cd backend && pytest -q`.
- [ ] Executar `cd backend && python evals/run_gate.py`.
- [ ] Executar `npm run test:unit`.
- [ ] Executar `npm run lint`.
- [ ] Executar `npx tsc --noEmit`.
- [ ] Executar `npm run build`.
- [ ] Executar `npm run test:e2e -- tests/e2e/dossier-v3.spec.ts` no ambiente de teste.
- [ ] Reprocessar em staging uma cópia autorizada do documento que originou o defeito e confirmar que Pedidos não é a única seção preenchida.
- [ ] Confirmar que nenhuma alteração não relacionada ou arquivo sensível entrou nos commits.

## Planos posteriores

Depois da Onda 0 estabilizada, criar um plano por módulo ou grupo coeso, nesta ordem:

1. Onda 1A: Cível/processo civil e Família/sucessões.
2. Onda 1B: Trabalhista, Consumidor e Previdenciário.
3. Onda 2: Empresarial/societário, Contratos, Tributário, Administrativo e Imobiliário.
4. Onda 3: Penal/processo penal, Ambiental, Eleitoral, Constitucional, Propriedade Intelectual e Proteção de Dados.

Cada plano especializado deverá declarar checklists, regras processuais, cálculos, fontes autorizadas, corpus jurídico, métricas e gate próprio, sem alterar o contrato universal salvo nova versão formal.
