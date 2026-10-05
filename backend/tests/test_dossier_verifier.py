"""Onda 0 Task 10 — gate material do verificador V3."""

import pytest

from app.core.analysis_verifier import (
    VerificationReportV3,
    decide_publication_status,
    verify_artifact_v3,
)
from app.core.schemas_v3 import ArtifactContentV3


def _artifact(**overrides):
    payload = {
        "schema_version": "3.0",
        "coverage": {"pages_total": 2, "pages_extracted": 2},
        "section_states": {
            "claims": {"status": "complete", "reason": "ok",
                       "coverage": {}, "pending_actions": []},
            "facts": {"status": "complete", "reason": "ok",
                      "coverage": {}, "pending_actions": []},
        },
        "claims": [{"id": "claim-1", "title": "Guarda", "source_refs": ["src-1"]}],
        "facts": [{"id": "f1", "statement": "X", "epistemic_status": "documented",
                   "source_refs": ["src-1"]}],
        "evidence": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "visuals": [],
    }
    payload.update(overrides)
    return ArtifactContentV3.model_validate(payload)


def test_completed_refused_with_unprocessed_page():
    art = _artifact(coverage={"pages_total": 3, "pages_extracted": 2,
                              "unprocessed_block_ids": ["b9"]})
    report = verify_artifact_v3(art, module_requirements=[])
    assert report.errors
    assert decide_publication_status(report, has_useful_content=True) != "completed"


def test_unsupported_source_is_material_error():
    art = _artifact(
        facts=[{"id": "f1", "statement": "X", "epistemic_status": "documented",
                "source_refs": ["src-ghost"]}],
        sources=[{"id": "src-1", "page_number": 1}],
    )
    report = verify_artifact_v3(art, module_requirements=[])
    assert any("src-ghost" in e for e in report.errors)


def test_missing_explicit_claim_blocks_completed():
    art = _artifact(
        coverage={"pages_total": 2, "pages_extracted": 2,
                  "explicit_claims_expected": 3, "explicit_claims_found": 1},
    )
    report = verify_artifact_v3(art, module_requirements=[])
    assert report.errors
    assert decide_publication_status(report, has_useful_content=True) != "completed"


def test_completed_requires_useful_content_not_just_passed_report():
    """Núcleo vazio nunca é 'completed', mesmo com gate aprovado (AC-01)."""
    report = VerificationReportV3(passed=True, errors=[])
    assert decide_publication_status(report, has_useful_content=True) == "completed"
    assert decide_publication_status(report, has_useful_content=False) == "failed"


def test_empty_section_without_reason_blocks_publication():
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        _artifact(section_states={
            "facts": {"status": "complete", "reason": "",
                      "coverage": {}, "pending_actions": []},
        })


def test_image_with_missing_source_blocks_publication():
    art = _artifact(
        visuals=[{"id": "vis-1", "document_id": "d1", "revision_id": "r1",
                  "page_number": 1, "source_ref": "src-ghost"}],
    )
    report = verify_artifact_v3(art, module_requirements=[])
    assert any("vis-1" in e or "src-ghost" in e for e in report.errors)


def test_structural_repair_never_invents_source_or_fact():
    from app.core.analysis_verifier import repair_artifact_v3

    art = _artifact()
    repaired, notes = repair_artifact_v3(art)
    assert repaired.coverage.explicit_claims_found == len(repaired.claims)
    assert all(f.source_refs == ["src-1"] for f in repaired.facts)
    assert not any("invent" in n.lower() for n in notes)
