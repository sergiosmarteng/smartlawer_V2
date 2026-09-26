"""V2 T10 — verificador e publicação (aceite do plano)."""

from app.core.analysis_verifier import (
    compose_executive_summary,
    decide_status,
    repair_once,
    verify,
)
from app.core.schemas_v2 import (
    ArtifactContent,
    Claim,
    Coverage,
    Fact,
    SourceRef,
    Thesis,
)
from app.crud import run as run_crud
from app.models.document import Document


def _valid_artifact() -> ArtifactContent:
    return ArtifactContent(
        coverage=Coverage(pages_total=35, pages_extracted=35),
        claims=[Claim(id="claim-8", original_number="8", title="Pensão", source_refs=["s1"])],
        facts=[Fact(statement="Evento em 30/05/2018", asserted_by="autor", source_refs=["s1"])],
        theses=[
            Thesis(id="t1", issue="nexo", conclusion="hipótese condicionada",
                   supporting_refs=["s1"], adverse_refs=[])
        ],
        sources=[SourceRef(id="s1", page_number=34)],
    )


def test_valid_artifact_completes_and_publishes(db_session, make_user):
    user = make_user()
    document = Document(user_id=user.id, filename="p.pdf", file_path="/tmp/p.pdf",
                        content_type="application/pdf", status="uploaded")
    db_session.add(document)
    db_session.commit()

    artifact = _valid_artifact()
    report = verify(artifact, calculations=[{"id": "c1", "formula": "sum_parcels",
                                            "formula_version": "1.0", "result": "10.00"}])
    assert report.passed and report.errors == []
    assert decide_status(report) == "completed"

    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    published = run_crud.publish_artifact(
        db_session, run=run, content=artifact.model_dump(), status=decide_status(report)
    )
    assert published.status == "completed"
    summary = compose_executive_summary(artifact, report)
    assert summary["status"] == "completed"
    assert summary["claims_total"] == 1


def test_material_error_blocks_completeness_with_actionable_pending():
    artifact = _valid_artifact()
    artifact.claims[0].source_refs = ["ghost"]
    artifact.coverage.unprocessed_block_ids = ["b007"]
    report = verify(artifact)
    assert not report.passed
    assert decide_status(report) == "partial"
    assert any("ghost" in e for e in report.errors)
    assert report.pending_actions  # nenhuma omissão silenciosa
    summary = compose_executive_summary(artifact, report)
    assert summary["status"] == "partial"


def test_empty_core_fails_without_useful_content():
    artifact = ArtifactContent()
    report = verify(artifact)
    assert not report.passed
    assert decide_status(report, has_useful_content=False) == "failed"
    assert decide_status(report) == "partial"


def test_repair_once_fixes_structure_never_invents():
    artifact = _valid_artifact()
    artifact.coverage.explicit_claims_found = 0
    repaired, repairs = repair_once(artifact)
    assert repairs
    assert repaired.coverage.explicit_claims_found == 1
    # Fontes ausentes NÃO são inventadas pela reparação: viram aviso.
    repaired.claims[0].source_refs = []
    report = verify(repaired)
    assert any("claim-8" in w for w in report.warnings)
    assert repaired.theses[0].supporting_refs == ["s1"]


def test_invalid_calculation_blocks():
    artifact = _valid_artifact()
    report = verify(artifact, calculations=[{"id": "c9", "result": None}])
    assert not report.passed
    assert any("c9" in e for e in report.errors)
