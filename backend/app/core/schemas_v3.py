"""Dossiê Universal — contrato de domínio V3 (Onda 0 Task 1).

Schema version: 3.0.

Invariantes verificadas por ``validate_artifact_v3``:
- Toda seção do dossiê expõe ``SectionState`` com ``status``/``reason``/
  ``coverage``/``pending_actions`` (spec universal §6.4).
- Fato material (``epistemic_status != "unknown"``) tem ao menos uma fonte
  ou limitação explícita (§5.1, §6.3.5).
- ``source_refs`` apontados por fatos/teses/riscos/provas existem em
  ``artifact.sources`` (idêntico ao invariant V2 §8.4).
- ``coverage.pages_total`` é não-negativo e cobre as páginas referenciadas
  em cada fonte.
- Nenhuma tese genérica é publicada pelo pipeline novo (defeito D01 da
  spec universal; FALLBACK_THESES removido em Onda 0 Task 1).

Arquivo sem dependência de HTTP ou banco. Importável por backend e pelos
tipos TypeScript gerados (ver ``smartlawer_V2/src/types/dossier.ts`` em
Task 13 da Onda 0).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator


ARTIFACT_SCHEMA_VERSION = "3.0"


# Estados compartilhados (spec universal §5.1 e §6.3/§6.4).
ArtifactStatus = Literal["completed", "partial", "blocked", "failed"]
ReviewStatus = Literal["pending", "in_review", "approved", "rejected"]
SectionStatus = Literal["complete", "partial", "blocked", "not_applicable"]
EpistemicStatus = Literal[
    "alleged", "documented", "admitted", "disputed", "inferred", "unknown"
]
VerificationStatus = Literal["matched", "partial", "insufficient", "contradictory", "unverified"]
RepresentedSide = Literal["claimant", "respondent", "third_party", "neutral"]
ClaimRelation = Literal[
    "alternate", "subsidiary", "cumulative", "overlaps", "procedural_accessory"
]
DateKind = Literal[
    "fact", "issuance", "protocol", "knowledge", "publication", "approximate"
]
VisualKind = Literal[
    "photo", "screenshot", "diagram", "table", "signature", "stamp", "page", "other"
]
VisualStatus = Literal["examined", "unresolved", "irrelevant", "extraction_failed"]
EvidenceKind = Literal["documental", "testemunhal", "pericial", "digital", "material", "pretendida"]
EvidencePresence = Literal["examined", "mentioned_not_located", "proposed", "unavailable"]
ModuleActivationStatus = Literal["active", "fallback", "blocked"]
RiskKind = Literal["juridico", "probatorio", "processual", "financeiro", "operacional"]


class _Strict(BaseModel):
    """Base com ``extra='forbid'`` para detectar payload errado cedo."""

    model_config = ConfigDict(extra="forbid")


class Money(BaseModel):
    """Valor monetário em string decimal ``NNNN.CC``. Idem V2."""

    model_config = ConfigDict(extra="forbid")

    literal: str
    value: StrictStr | None = None
    currency: str = "BRL"


class SectionCoverage(_Strict):
    items_expected: int | None = None
    items_found: int = 0
    items_verified: int = 0


class SectionState(_Strict):
    """Estado obrigatório de cada seção do dossiê (spec universal §6.4).

    Lista vazia sem ``reason`` é inválida; ``validate_artifact_v3`` detecta.
    """

    status: SectionStatus
    reason: str = Field(min_length=1, description="Motivo do estado; nunca vazio.")
    coverage: SectionCoverage = Field(default_factory=SectionCoverage)
    pending_actions: list[str] = Field(default_factory=list)

    @field_validator("reason")
    @classmethod
    def _non_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason não pode ser vazio")
        return v


class AnalysisScope(_Strict):
    document_ids: list[str] = Field(default_factory=list)
    case_id: str | None = None
    represented_side: RepresentedSide = "neutral"
    objective: str | None = None
    reference_date: str | None = None
    area_overrides: list[str] = Field(default_factory=list)


class ModuleActivation(_Strict):
    module_id: str
    module_version: str = "1.0.0"
    status: ModuleActivationStatus = "active"
    reason: str = ""


class IssueAssessment(_Strict):
    """Avaliação de questão especializada (Onda 1, spec §2).

    ``issue_key`` estável e versionado; alteração de regra gera nova
    versão do módulo. Refs apontam a fontes do artefato (página/região).
    """

    issue_key: str
    status: SectionStatus = "complete"
    conclusion: str = ""
    factual_refs: list[str] = Field(default_factory=list)
    supporting_source_refs: list[str] = Field(default_factory=list)
    adverse_source_refs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    related_claim_ids: list[str] = Field(default_factory=list)
    action_ids: list[str] = Field(default_factory=list)


class ModuleResult(_Strict):
    """Envelope de módulo especializado (Onda 1, spec §2).

    Extensão opcional formal do schema 3.0: o módulo acrescenta objetos
    e verificações ao núcleo sem substituir fatos, pedidos ou fontes.
    """

    module_id: str
    module_version: str = "1.0.0"
    status: str = "complete"
    reason: str = ""
    issue_assessments: list[IssueAssessment] = Field(default_factory=list)
    calculation_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CoverageV3(_Strict):
    pages_total: int = Field(default=0, ge=0)
    pages_extracted: int = Field(default=0, ge=0)
    unprocessed_block_ids: list[str] = Field(default_factory=list)
    explicit_claims_expected: int | None = None
    explicit_claims_found: int = 0

    @field_validator("pages_extracted")
    @classmethod
    def _pages_le_total(cls, v: int, info) -> int:
        total = info.data.get("pages_total", 0)
        if v > total:
            raise ValueError("pages_extracted não pode exceder pages_total")
        return v


class Party(_Strict):
    id: str
    name: str
    kind: str = "person"
    role_material: str | None = None
    role_procedural: str | None = None
    represented_side: RepresentedSide = "neutral"
    identifiers: dict = Field(default_factory=dict)
    representatives: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class TimelineEvent(_Strict):
    id: str
    date: str
    date_kind: DateKind = "fact"
    description: str
    parties: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class ClaimV3(_Strict):
    id: str
    original_number: str | None = None
    title: str
    category: str = "other"
    requested_relief: str | None = None
    factual_basis_refs: list[str] = Field(default_factory=list)
    legal_basis_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    amount: Money | None = None
    recurrence: str | None = None
    period: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    related_claims: list["RelatedClaimV3"] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    epistemic_status: EpistemicStatus = "alleged"
    occurrences: int = 1
    issues: list[str] = Field(default_factory=list)


class RelatedClaimV3(_Strict):
    claim_id: str
    relation: ClaimRelation


class FactV3(_Strict):
    id: str
    statement: str
    asserted_by: str = "unknown"
    epistemic_status: EpistemicStatus = "alleged"
    source_refs: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)


class Controversy(_Strict):
    id: str
    description: str
    fact_ids: list[str] = Field(default_factory=list)
    status: str = "open"


class EvidenceItemV3(_Strict):
    id: str
    kind: EvidenceKind = "documental"
    presence_status: EvidencePresence = "mentioned_not_located"
    location_refs: list[str] = Field(default_factory=list)
    propositions_supported: list[str] = Field(default_factory=list)
    limitations: str | None = None
    authenticity_status: VerificationStatus | None = None
    requested_action: str | None = None


class NormalizedRegion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)


class VisualQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution: str = "unknown"
    rotation: int = 0
    cropped: bool = False


class VisualEvidence(_Strict):
    """Imagem como evidência (spec universal §7)."""

    id: str
    document_id: str
    revision_id: str
    page_number: int = Field(ge=1)
    region: NormalizedRegion | None = None
    kind: VisualKind = "other"
    status: VisualStatus = "unresolved"
    storage_key: str = ""
    thumbnail_key: str = ""
    caption_original: str | None = None
    description: str = ""
    relevance: str = ""
    sensitivity: list[str] = Field(default_factory=list)
    quality: VisualQuality = Field(default_factory=VisualQuality)
    related_fact_ids: list[str] = Field(default_factory=list)
    related_claim_ids: list[str] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)
    related_thesis_ids: list[str] = Field(default_factory=list)
    source_ref: str = ""


class LegalReferenceV3(_Strict):
    id: str
    instrument: str | None = None
    article: str | None = None
    literal_citation: str
    normalized_citation: str | None = None
    verification_status: VerificationStatus = "unverified"
    source_ref: str | None = None
    external_source: dict | None = None


class ProceduralIssue(_Strict):
    id: str
    issue: str
    status: SectionStatus = "complete"
    conclusion: str = ""
    source_refs: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)


class ThesisV3(_Strict):
    id: str
    represented_side: RepresentedSide = "neutral"
    issue: str
    conclusion: str
    factual_premises: list[str] = Field(default_factory=list)
    legal_premises: list[str] = Field(default_factory=list)
    supporting_refs: list[str] = Field(default_factory=list)
    adverse_refs: list[str] = Field(default_factory=list)
    counterargument: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    requested_evidence: list[str] = Field(default_factory=list)
    action: str | None = None
    limitations: str | None = None


class CalculationV3(_Strict):
    id: str
    formula: str
    formula_version: str = "1.0.0"
    inputs: dict = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    result: str | None = None
    rounding: str = "half_up_centavos"
    scenario: str | None = None


class RiskV3(_Strict):
    id: str
    issue: str
    impact: str
    uncertainty: str | None = None
    supporting_refs: list[str] = Field(default_factory=list)
    mitigation: str | None = None
    review_owner: str | None = None
    kind: RiskKind = "juridico"


class ActionItem(_Strict):
    id: str
    description: str
    priority: Literal["high", "medium", "low"] = "medium"
    responsible: str = ""
    deadline_hint: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    related_fact_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class ClientQuestion(_Strict):
    id: str
    question: str
    context: str = ""
    source_refs: list[str] = Field(default_factory=list)


class SourceRefV3(_Strict):
    """Referência resolvível (doc/página/bloco/região) — spec universal §10.1."""

    id: str
    kind: str = "document"
    revision_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    block_id: str | None = None
    region: NormalizedRegion | None = None
    quote: str | None = None
    verification_status: VerificationStatus = "unverified"
    url: str | None = None


class LimitationV3(_Strict):
    code: str
    affected_claim_ids: list[str] = Field(default_factory=list)
    affected_section: str | None = None
    message: str


class ExecutiveSummary(_Strict):
    narrative: str = ""
    central_question: str = ""
    main_claims: list[str] = Field(default_factory=list)
    economic_exposure: str | None = None
    key_facts: list[str] = Field(default_factory=list)
    key_evidence: list[str] = Field(default_factory=list)
    key_theses: list[str] = Field(default_factory=list)
    priority_risks: list[str] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


# Resolução tardia do forward ref RelatedClaimV3 em ClaimV3.
ClaimV3.model_rebuild()


# Seções reconhecidas (spec universal §6.3 + plano §1 seção 6).
RECOGNIZED_SECTIONS = (
    "executive_summary",
    "parties",
    "events",
    "claims",
    "facts",
    "controversies",
    "evidence",
    "visuals",
    "legal_references",
    "procedural_issues",
    "theses",
    "calculations",
    "risks",
    "action_plan",
    "client_questions",
    "sources",
    "limitations",
    "review",
)


class ArtifactContentV3(BaseModel):
    """Artefato publicado no schema 3.0 (Onda 0)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = ARTIFACT_SCHEMA_VERSION
    run_id: str | None = None
    case_id: str | None = None
    status: ArtifactStatus = "partial"
    review_status: ReviewStatus = "pending"
    scope: AnalysisScope = Field(default_factory=AnalysisScope)
    module_activations: list[ModuleActivation] = Field(default_factory=list)
    module_results: dict[str, ModuleResult] = Field(default_factory=dict)
    coverage: CoverageV3 = Field(default_factory=CoverageV3)
    section_states: dict[str, SectionState] = Field(default_factory=dict)
    executive_summary: ExecutiveSummary | None = None
    parties: list[Party] = Field(default_factory=list)
    events: list[TimelineEvent] = Field(default_factory=list)
    claims: list[ClaimV3] = Field(default_factory=list)
    facts: list[FactV3] = Field(default_factory=list)
    controversies: list[Controversy] = Field(default_factory=list)
    evidence: list[EvidenceItemV3] = Field(default_factory=list)
    visuals: list[VisualEvidence] = Field(default_factory=list)
    legal_references: list[LegalReferenceV3] = Field(default_factory=list)
    procedural_issues: list[ProceduralIssue] = Field(default_factory=list)
    theses: list[ThesisV3] = Field(default_factory=list)
    calculations: list[CalculationV3] = Field(default_factory=list)
    risks: list[RiskV3] = Field(default_factory=list)
    action_plan: list[ActionItem] = Field(default_factory=list)
    client_questions: list[ClientQuestion] = Field(default_factory=list)
    sources: list[SourceRefV3] = Field(default_factory=list)
    limitations: list[LimitationV3] = Field(default_factory=list)


def validate_artifact_v3(artifact: ArtifactContentV3) -> list[str]:
    """Invariantes do schema 3.0. Retorna violações (vazio = válido).

    Cobre:
    - SectionState obrigatória por seção, com ``reason`` não-vazio.
    - Fato material com ``source_refs`` ou limitação explícita.
    - ``source_refs`` apontando para fontes existentes.
    - Página de cada fonte dentro de ``coverage.pages_total``.
    - Cobertura de pedidos esperados.
    """
    errors: list[str] = []
    known_sources = {s.id for s in artifact.sources}

    # (1) SectionState obrigatória por seção conhecida presente no artefato.
    for section in RECOGNIZED_SECTIONS:
        state = artifact.section_states.get(section)
        if state is None:
            continue
        if not state.reason or not state.reason.strip():
            errors.append(
                f"section '{section}': SectionState sem reason (spec §6.4)"
            )

    # (2) Fato material: precisa de source_refs ou limitação explícita.
    limitation_fact_ids = {
        lim.affected_section
        for lim in artifact.limitations
        if lim.code and lim.affected_section == "facts"
    }
    for fact in artifact.facts:
        if fact.epistemic_status == "unknown":
            continue
        if fact.source_refs:
            for ref in fact.source_refs:
                if ref not in known_sources:
                    errors.append(f"fact {fact.id}: source_ref inexistente {ref!r}")
        elif fact.id not in limitation_fact_ids and not any(
            lim.affected_claim_ids and fact.id in lim.affected_claim_ids
            for lim in artifact.limitations
        ):
            errors.append(
                f"fact {fact.id}: afirmação material sem source_refs ou limitação"
            )

    # (3) source_refs de teses, riscos, provas devem existir.
    for thesis in artifact.theses:
        for ref in [*thesis.supporting_refs, *thesis.adverse_refs]:
            if ref not in known_sources:
                errors.append(f"thesis {thesis.id}: fonte inexistente {ref!r}")
    for risk in artifact.risks:
        for ref in risk.supporting_refs:
            if ref not in known_sources:
                errors.append(f"risk {risk.id}: fonte inexistente {ref!r}")
    for evidence in artifact.evidence:
        for ref in evidence.location_refs:
            if ref not in known_sources:
                errors.append(f"evidence {evidence.id}: fonte inexistente {ref!r}")

    # (4) Página de cada fonte dentro do intervalo de coverage.
    for source in artifact.sources:
        if (
            source.page_number is not None
            and artifact.coverage.pages_total
            and not 1 <= source.page_number <= artifact.coverage.pages_total
        ):
            errors.append(
                f"source {source.id}: página {source.page_number} "
                f"fora de 1..{artifact.coverage.pages_total}"
            )

    # (5) Pedidos explícitos: esperados x encontrados.
    expected = artifact.coverage.explicit_claims_expected
    if expected is not None and expected != len(artifact.claims):
        errors.append(
            f"cobertura: esperados {expected} pedidos, "
            f"encontrados {len(artifact.claims)}"
        )

    # (6) Módulos (Onda 1, spec §2): refs das avaliações resolvem a fontes.
    for module_id, result in (artifact.module_results or {}).items():
        for assessment in result.issue_assessments:
            for ref in [*assessment.supporting_source_refs, *assessment.adverse_source_refs]:
                if ref not in known_sources:
                    errors.append(
                        f"module {module_id}/{assessment.issue_key}: "
                        f"fonte inexistente {ref!r}"
                    )

    return errors


__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "ArtifactContentV3",
    "AnalysisScope",
    "ClaimRelation",
    "ClaimV3",
    "ClientQuestion",
    "CalculationV3",
    "Controversy",
    "CoverageV3",
    "EvidenceItemV3",
    "ExecutiveSummary",
    "FactV3",
    "LegalReferenceV3",
    "LimitationV3",
    "IssueAssessment",
    "ModuleActivation",
    "ModuleResult",
    "NormalizedRegion",
    "Party",
    "ProceduralIssue",
    "RECOGNIZED_SECTIONS",
    "RelatedClaimV3",
    "RiskV3",
    "SectionCoverage",
    "SectionState",
    "SourceRefV3",
    "ThesisV3",
    "TimelineEvent",
    "VisualEvidence",
    "VisualQuality",
    "ActionItem",
    "validate_artifact_v3",
]