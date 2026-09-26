"""Contrato estruturado V2: tipos de domínio + invariantes (T06, §8).

Formalizado em Pydantic (gera o JSON Schema do frontend em T11).
IDs simbólicos; nulos nunca viram conteúdo inventado (§8.3).
"""

import re
from typing import Literal

from pydantic import BaseModel, Field, StrictStr, field_validator

ARTIFACT_SCHEMA_VERSION = "2.0"

EpistemicStatus = Literal[
    "alleged", "documented", "admitted", "disputed", "inferred", "unknown"
]
ClaimRelation = Literal[
    "alternate", "subsidiary", "cumulative", "overlaps", "procedural_accessory"
]
PresenceStatus = Literal["examined", "mentioned_not_located", "proposed"]
VerificationStatus = Literal["matched", "unverified", "insufficient", "contradictory"]
RepresentedSide = Literal["claimant", "respondent", "neutral"]
ReviewStatus = Literal["pending", "in_review", "approved", "rejected"]

_DECIMAL_RE = re.compile(r"^\d+\.\d{2}$")


class Money(BaseModel):
    """Valor monetário: string decimal exata; ambíguo = literal + nulo (§8.4)."""

    literal: str
    value: StrictStr | None = Field(default=None, description="Ex.: '1400.00'")
    currency: str = "BRL"

    @field_validator("value")
    @classmethod
    def _decimal_string(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _DECIMAL_RE.fullmatch(v):
            raise ValueError(f"valor monetário deve ser string decimal 'NNNN.CC': {v!r}")
        return v


class RelatedClaim(BaseModel):
    claim_id: str
    relation: ClaimRelation


class Claim(BaseModel):
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
    related_claims: list[RelatedClaim] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    epistemic_status: EpistemicStatus = "alleged"
    occurrences: int = 1
    issues: list[str] = Field(default_factory=list)


class Fact(BaseModel):
    statement: str
    asserted_by: str = "unknown"
    epistemic_status: EpistemicStatus = "alleged"
    source_refs: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str
    kind: str
    presence_status: PresenceStatus = "mentioned_not_located"
    location_refs: list[str] = Field(default_factory=list)
    propositions_supported: list[str] = Field(default_factory=list)
    limitations: str | None = None
    authenticity_status: str | None = None
    requested_action: str | None = None


class LegalReference(BaseModel):
    id: str
    instrument: str | None = None
    article: str | None = None
    literal_citation: str
    normalized_citation: str | None = None
    verification_status: VerificationStatus = "unverified"
    source_ref: str | None = None


class Thesis(BaseModel):
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


class Risk(BaseModel):
    issue: str
    impact: str
    uncertainty: str | None = None
    supporting_refs: list[str] = Field(default_factory=list)
    mitigation: str | None = None
    review_owner: str | None = None


class Calculation(BaseModel):
    id: str
    formula: str
    formula_version: str = "1.0"
    inputs: dict = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    result: str | None = None
    rounding: str = "half_up_centavos"
    scenario: str | None = None


class SourceRef(BaseModel):
    id: str
    kind: str = "document"
    revision_id: str | None = None
    page_number: int | None = None
    block_id: str | None = None
    quote: str | None = None
    verification_status: VerificationStatus = "unverified"


class Coverage(BaseModel):
    pages_total: int = 0
    pages_extracted: int = 0
    unprocessed_block_ids: list[str] = Field(default_factory=list)
    explicit_claims_expected: int | None = None
    explicit_claims_found: int = 0


class Limitation(BaseModel):
    code: str
    affected_claim_ids: list[str] = Field(default_factory=list)
    message: str


class ArtifactContent(BaseModel):
    """Conteúdo validado do AnalysisArtifact (schema 2.0, §8.3)."""

    schema_version: str = ARTIFACT_SCHEMA_VERSION
    run_id: str | None = None
    module: dict = Field(default_factory=lambda: {"id": "general", "version": "1.0"})
    status: str = "partial"
    review_status: ReviewStatus = "pending"
    scope: dict = Field(default_factory=dict)
    coverage: Coverage = Field(default_factory=Coverage)
    claims: list[Claim] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    legal_references: list[LegalReference] = Field(default_factory=list)
    theses: list[Thesis] = Field(default_factory=list)
    calculations: list[Calculation] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    limitations: list[Limitation] = Field(default_factory=list)


def validate_artifact(
    artifact: ArtifactContent,
    *,
    pages_total: int | None = None,
) -> list[str]:
    """Invariantes §8.4. Retorna violações (vazio = válido)."""
    violations: list[str] = []
    known_sources = {s.id for s in artifact.sources}
    if pages_total is None:
        pages_total = artifact.coverage.pages_total

    def check_refs(owner: str, refs: list[str]) -> None:
        for ref in refs:
            if ref not in known_sources:
                violations.append(f"{owner}: fonte inexistente {ref!r}")

    for claim in artifact.claims:
        check_refs(f"claim {claim.id}", claim.source_refs)
        check_refs(f"claim {claim.id}/factual", claim.factual_basis_refs)
        check_refs(f"claim {claim.id}/legal", claim.legal_basis_refs)
        check_refs(f"claim {claim.id}/evidence", claim.evidence_refs)
    for index, fact in enumerate(artifact.facts):
        check_refs(f"fact[{index}]", fact.source_refs)
        if fact.epistemic_status != "unknown" and not fact.source_refs:
            violations.append(f"fact[{index}]: afirmação material sem source_refs")
    for thesis in artifact.theses:
        check_refs(f"thesis {thesis.id}/supporting", thesis.supporting_refs)
        check_refs(f"thesis {thesis.id}/adverse", thesis.adverse_refs)
    for risk in artifact.risks:
        check_refs(f"risk {risk.issue}", risk.supporting_refs)
    for source in artifact.sources:
        if (
            source.page_number is not None
            and pages_total
            and not 1 <= source.page_number <= pages_total
        ):
            violations.append(
                f"source {source.id}: página {source.page_number} fora de 1..{pages_total}"
            )
    expected = artifact.coverage.explicit_claims_expected
    if expected is not None and expected != len(artifact.claims):
        violations.append(
            f"cobertura: esperados {expected} pedidos, encontrados {len(artifact.claims)}"
        )
    return violations


def coerce_legacy_analysis(ai_data: dict, *, run_id: str | None = None) -> ArtifactContent:
    """Ponte V1→V2: análise legada vira artefato mínimo honesto.

    Sem fontes localizadas: tudo ``unknown`` + limitação explícita.
    Nunca ressuscita estratégia genérica como tese validada.
    """
    claims = [
        Claim(
            id=f"legacy-claim-{index}",
            title=str(item)[:200],
            epistemic_status="unknown",
        )
        for index, item in enumerate(ai_data.get("requests", []) or [], start=1)
    ]
    return ArtifactContent(
        run_id=run_id,
        module={"id": "general", "version": "1.0"},
        status="partial",
        coverage=Coverage(explicit_claims_found=len(claims)),
        claims=claims,
        limitations=[
            Limitation(
                code="LEGACY_UNVERIFIED",
                message=(
                    "Análise legada sem fontes localizadas; requer "
                    "reprocessamento no pipeline V2."
                ),
            )
        ],
    )
