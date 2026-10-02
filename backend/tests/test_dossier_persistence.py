"""Onda 0 Task 2 — persistência de casos, documentos do caso e estágios.

5 invariantes (plano §2):
- um documento não pode ser anexado a caso de outro usuário;
- o snapshot do run guarda ``case_id``, ``document_ids``, ``revision_ids`` e hashes;
- ``get_resume_point()`` retorna o primeiro estágio não concluído;
- substituir o arquivo depois do snapshot não altera ``revision_ids`` do run;
- ``(run_id, stage, attempt)`` é único em ``analysis_stage_runs``.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.crud.case import (
    CaseAccessError,
    attach_document,
    create_case,
    get_case,
)
from app.crud.stage_run import (
    StageAttemptConflictError,
    fail_stage,
    finish_stage,
    get_resume_point,
    start_stage,
)
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _make_document(db, *, user_id, file_path="orig.pdf", sha="sha-orig"):
    doc = Document(
        user_id=user_id,
        filename=file_path,
        file_path=file_path,
        content_type="application/pdf",
    )
    db.add(doc)
    db.flush()
    rev = DocumentRevision(
        document_id=doc.id,
        user_id=user_id,
        sha256=sha,
        pages_total=10,
    )
    db.add(rev)
    db.flush()
    return doc, rev


def test_document_cannot_attach_to_other_user_case(db_session, make_user):
    """Anexar documento alheio a um caso é proibido (AC-10 do spec universal)."""
    owner = make_user(email="owner@x.com", username="owner")
    intruder = make_user(email="intruder@x.com", username="intruder")

    case = create_case(db_session, user_id=owner.id, name="caso do owner")
    intruder_doc, _ = _make_document(db_session, user_id=intruder.id)

    with pytest.raises(CaseAccessError):
        attach_document(db_session, case=case, document=intruder_doc, role="petição")

    db_session.refresh(case)
    assert list(case.documents) == [], "caso do owner não pode ter documentos alheios"


def test_run_snapshot_persists_case_and_revisions_and_hashes(db_session, make_user):
    """Snapshot inclui case_id, document_ids, revision_ids e sha256."""
    user = make_user()
    case = create_case(db_session, user_id=user.id, name="caso A")
    doc_a, rev_a = _make_document(db_session, user_id=user.id, sha="sha-A")
    doc_b, rev_b = _make_document(db_session, user_id=user.id, sha="sha-B")
    attach_document(db_session, case=case, document=doc_a, role="petição")
    attach_document(db_session, case=case, document=doc_b, role="contestação")

    run = AnalysisRun(
        user_id=user.id,
        case_id=case.id,
        status=AnalysisRun.QUEUED,
        snapshot={
            "case_id": str(case.id),
            "document_ids": [str(doc_a.id), str(doc_b.id)],
            "revision_ids": [str(rev_a.id), str(rev_b.id)],
            "sha256": [rev_a.sha256, rev_b.sha256],
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    snap = run.snapshot
    assert snap["case_id"] == str(case.id)
    assert set(snap["document_ids"]) == {str(doc_a.id), str(doc_b.id)}
    assert set(snap["revision_ids"]) == {str(rev_a.id), str(rev_b.id)}
    assert sorted(snap["sha256"]) == ["sha-A", "sha-B"]


def test_get_resume_point_returns_first_incomplete_stage(db_session, make_user):
    """Retoma a partir do primeiro estágio sem finish_stage bem-sucedido."""
    user = make_user()
    case = create_case(db_session, user_id=user.id, name="caso B")
    doc, _ = _make_document(db_session, user_id=user.id)
    attach_document(db_session, case=case, document=doc, role="petição")
    run = AnalysisRun(
        user_id=user.id,
        case_id=case.id,
        status=AnalysisRun.RUNNING,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    ordered_stages = ["extraction", "classification", "reconciliation"]

    # Marca extraction e classification como concluídas; reconciliation fica aberta.
    s1 = start_stage(db_session, run=run, stage="extraction", attempt=1)
    finish_stage(db_session, stage_run=s1)
    s2 = start_stage(db_session, run=run, stage="classification", attempt=1)
    finish_stage(db_session, stage_run=s2)

    assert get_resume_point(db_session, run=run, ordered_stages=ordered_stages) == "reconciliation"


def test_substituting_file_after_snapshot_keeps_revision_ids(db_session, make_user):
    """Substituir o arquivo depois do snapshot não altera revision_ids do run."""
    user = make_user()
    case = create_case(db_session, user_id=user.id, name="caso C")
    doc, rev_original = _make_document(db_session, user_id=user.id, sha="sha-original")
    attach_document(db_session, case=case, document=doc, role="petição")

    run = AnalysisRun(
        user_id=user.id,
        case_id=case.id,
        status=AnalysisRun.QUEUED,
        snapshot={
            "case_id": str(case.id),
            "document_ids": [str(doc.id)],
            "revision_ids": [str(rev_original.id)],
            "sha256": [rev_original.sha256],
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    original_revision_ids = list(run.snapshot["revision_ids"])

    # Simula substituição: nova revisão surge no documento (upload diferente),
    # mas o snapshot não deve mudar.
    rev_new = DocumentRevision(
        document_id=doc.id,
        user_id=user.id,
        sha256="sha-novo",
        pages_total=12,
    )
    db_session.add(rev_new)
    db_session.commit()

    db_session.refresh(run)
    assert run.snapshot["revision_ids"] == original_revision_ids, (
        "snapshot do run não pode ser reescrito por nova revisão do documento"
    )
    assert "sha-novo" not in run.snapshot["sha256"]


def test_run_stage_attempt_unique(db_session, make_user):
    """(run_id, stage, attempt) é único em analysis_stage_runs."""
    user = make_user()
    case = create_case(db_session, user_id=user.id, name="caso D")
    doc, _ = _make_document(db_session, user_id=user.id)
    attach_document(db_session, case=case, document=doc, role="petição")
    run = AnalysisRun(
        user_id=user.id,
        case_id=case.id,
        status=AnalysisRun.RUNNING,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    start_stage(db_session, run=run, stage="extraction", attempt=1)

    with pytest.raises(StageAttemptConflictError):
        start_stage(db_session, run=run, stage="extraction", attempt=1)