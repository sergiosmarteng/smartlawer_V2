"""Onda 0 Task 15 — revisão versionada, comparação e exportação."""

import pytest

from app.crud import run as run_crud
from app.models.document import Document


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p15.pdf", file_path="/tmp/p15.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _content(**overrides):
    base = {
        "schema_version": "3.0",
        "claims": [{"id": "claim-1", "title": "Guarda"}],
        "facts": [],
        "evidence": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "visuals": [{"id": "vis-1", "page_number": 1,
                     "storage_key": "opaque-vis-1",
                     "thumbnail_key": "opaque-thumb-1"}],
        "limitations": [],
    }
    base.update(overrides)
    return base


def test_correction_preserves_before_after_authorship_reason_version(
    db_session, make_user
):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_content(), status="partial")
    event = run_crud.add_review_event(
        db_session, artifact=artifact, reviewer_id=user.id,
        target="claims.claim-1", before={"title": "Guarda"},
        after={"title": "Guarda compartilhada"}, reason="precisar o pedido",
    )
    assert event.before == {"title": "Guarda"}
    assert event.after == {"title": "Guarda compartilhada"}
    assert str(event.reviewer_id) == str(user.id)
    assert event.reason == "precisar o pedido"
    assert event.source_version == "3.0"


def test_concurrent_version_returns_409(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_content(), status="partial")
    resp = client.post(
        f"/api/v2/analyses/{artifact.id}/review-events",
        headers=auth_headers_for(user),
        json={"target": "x", "expected_version": 1},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "VERSION_CONFLICT"


def test_approval_requires_authorized_user_and_no_material_blocks(
    db_session, make_user
):
    from app.crud.run import ReviewApprovalError, approve_artifact

    user, document = _document(db_session, make_user)
    intruder = make_user(email="i15@x.com", username="i15")
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_content(), status="partial")
    with pytest.raises(ReviewApprovalError):
        approve_artifact(db_session, artifact=artifact, reviewer_id=intruder.id)
    blocked = _content(section_states={
        "facts": {"status": "blocked", "reason": "OCR pendente",
                  "coverage": {}, "pending_actions": ["Refazer OCR"]},
    })
    run2 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    art2 = run_crud.publish_artifact(
        db_session, run=run2, content=blocked, status="partial")
    with pytest.raises(ReviewApprovalError):
        approve_artifact(db_session, artifact=art2, reviewer_id=user.id)
    approved = approve_artifact(db_session, artifact=artifact, reviewer_id=user.id)
    assert approved.review_status == "approved"


def test_compare_identifies_add_remove_change_by_stable_id():
    from app.core.artifact_diff import compare_artifacts

    before = {"claims": [{"id": "c1", "title": "A"}, {"id": "c2", "title": "B"}]}
    after = {"claims": [{"id": "c2", "title": "B2"}, {"id": "c3", "title": "C"}]}
    diff = compare_artifacts(before, after)
    assert diff.added["claims"] == ["c3"]
    assert diff.removed["claims"] == ["c1"]
    assert diff.changed["claims"] == ["c2"]


def test_same_version_mode_generates_same_job_and_report(
    client, db_session, make_user, auth_headers_for
):
    from app.core.v2_export import build_v3_report

    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_content(), status="partial")
    first = client.post(f"/api/v2/analyses/{artifact.id}/exports",
                        headers=headers, json={"mode": "complete"})
    second = client.post(f"/api/v2/analyses/{artifact.id}/exports",
                         headers=headers, json={"mode": "complete"})
    assert first.json()["job_id"] == second.json()["job_id"]
    content = _content()
    assert build_v3_report(content, mode="complete", review_events=[]) == \
        build_v3_report(content, mode="complete", review_events=[])


def test_report_includes_image_refs_without_expiring_url():
    from app.core.v2_export import build_v3_report

    report = build_v3_report(_content(), mode="complete", review_events=[])
    assert "opaque-vis-1" in report
    assert "http" not in report.replace("https://", "")
