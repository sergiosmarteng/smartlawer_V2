"""V2 T06 — esquemas e reconciliação (aceite do plano)."""

import pytest
from pydantic import ValidationError

from app.core.reconciler import normalize_claim_number, reconcile_claims
from app.core.schemas_v2 import (
    ArtifactContent,
    Claim,
    Coverage,
    Fact,
    Money,
    RelatedClaim,
    SourceRef,
    Thesis,
    coerce_legacy_analysis,
    validate_artifact,
)


def _claim(number: str, title: str, **kwargs) -> Claim:
    return Claim(id=f"claim-{number}", original_number=number, title=title, **kwargs)


def test_money_rejects_float_and_malformed():
    assert Money(literal="R$ 1.400,00", value="1400.00").currency == "BRL"
    assert Money(literal="valor incerto").value is None
    with pytest.raises(ValidationError):
        Money(literal="x", value=1400.00)  # float proibido (§8.4)
    with pytest.raises(ValidationError):
        Money(literal="x", value="1400,00")


def test_benchmark_13_claims_reconciled_with_relations():
    base = [
        ("1", "Benefício A (fundamento 1)", [RelatedClaim(claim_id="claim-3", relation="alternate")]),
        ("2", "Controle difuso", []),
        ("3", "Benefício A (fundamento 2)", [RelatedClaim(claim_id="claim-1", relation="alternate")]),
        ("4", "Requerimento processual", []),
        ("5", "Reparação material", [RelatedClaim(claim_id="claim-8", relation="overlaps")]),
        ("6", "Reparação moral", []),
        ("7", "Reparação estética", []),
        ("8", "Pensão mensal", [RelatedClaim(claim_id="claim-5", relation="overlaps")]),
        ("9", "Indenização coletiva", []),
        ("10", "Garantia da execução", [RelatedClaim(claim_id="claim-8", relation="procedural_accessory")]),
        ("11", "Rito processual", []),
        ("12", "Honorários", []),
        ("13", "Procedência total", []),
    ]
    # Duas ocorrências por lote (overlap T05) com fontes distintas.
    candidates = []
    for batch in ("batch-1", "batch-2"):
        for number, title, related in base:
            candidates.append(
                _claim(
                    number, title,
                    source_refs=[f"src-{number}-{batch}"],
                    related_claims=list(related),
                )
            )
    reconciled = reconcile_claims(candidates)
    assert len(reconciled) == 13
    by_number = {c.original_number: c for c in reconciled}
    assert set(by_number) == {str(n) for n in range(1, 14)}
    assert all(c.occurrences == 2 for c in reconciled)
    assert {r.claim_id for r in by_number["1"].related_claims} == {"claim-3"}
    assert by_number["1"].related_claims[0].relation == "alternate"
    assert by_number["10"].related_claims[0].relation == "procedural_accessory"
    # Fontes das duas ocorrências unidas, origem preservada.
    assert set(by_number["8"].source_refs) == {"src-8-batch-1", "src-8-batch-2"}


def test_conflicting_amounts_become_reviewable_issue():
    first = _claim(
        "5", "Reparação",
        amount=Money(literal="R$ 215.760,00", value="215760.00"),
        source_refs=["a"],
    )
    second = _claim(
        "5", "Reparação material detalhada",
        amount=Money(literal="R$ 200.000,00", value="200000.00"),
        source_refs=["b"],
    )
    (merged,) = reconcile_claims([first, second])
    assert merged.occurrences == 2
    assert any("divergente" in issue for issue in merged.issues)
    assert set(merged.source_refs) == {"a", "b"}


def test_normalize_claim_number():
    assert normalize_claim_number("Pedido 8") == "8"
    assert normalize_claim_number("item 13.") == "13"
    assert normalize_claim_number(None) is None
    assert normalize_claim_number("sem numero") is None


def test_validate_artifact_catches_dangling_and_out_of_range():
    artifact = ArtifactContent(
        coverage=Coverage(pages_total=35, pages_extracted=35),
        claims=[_claim("8", "Pensão", source_refs=["ghost"])],
        facts=[Fact(statement="Treinamento inexistente", epistemic_status="alleged")],
        theses=[
            Thesis(
                id="t1", issue="nexo", conclusion="hipótese",
                supporting_refs=["src-ok"], adverse_refs=[],
            )
        ],
        sources=[
            SourceRef(id="src-ok", page_number=99),
            SourceRef(id="src-bad", page_number=3),
        ],
    )
    violations = validate_artifact(artifact)
    assert any("ghost" in v for v in violations)  # fonte inexistente
    assert any("99" in v for v in violations)  # página fora do intervalo
    assert any("sem source_refs" in v for v in violations)  # fato material
    # Cobertura esperada x encontrada.
    artifact.coverage.explicit_claims_expected = 13
    assert any("13" in v for v in validate_artifact(artifact))


def test_legacy_coerce_is_honest_partial():
    legacy = {"summary": "s", "requests": ["pedido A", "pedido B"]}
    artifact = coerce_legacy_analysis(legacy, run_id="run-1")
    assert artifact.status == "partial"
    assert len(artifact.claims) == 2
    assert all(c.epistemic_status == "unknown" for c in artifact.claims)
    assert artifact.limitations[0].code == "LEGACY_UNVERIFIED"
    assert validate_artifact(artifact) == []
