"""Onda 0 Task 16 — isolamento e segurança do dossiê V3."""

from app.crud import run as run_crud
from app.models.document import Document


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p16.pdf", file_path="/tmp/p16.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _content():
    return {
        "schema_version": "3.0",
        "claims": [{"id": "claim-1", "title": "Guarda"}],
        "facts": [],
        "evidence": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "visuals": [{"id": "vis-1", "storage_key": "opaque-vis-1",
                     "thumbnail_key": "opaque-thumb-1"}],
    }


def test_cross_access_returns_404(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    intruder = make_user(email="i16@x.com", username="i16")
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_content(), status="partial")
    headers = auth_headers_for(intruder)
    assert client.get(f"/api/v2/analyses/{artifact.id}", headers=headers).status_code == 404
    assert client.get(f"/api/v2/analyses/{artifact.id}/visuals", headers=headers).status_code == 404
    assert client.get(f"/api/v2/analyses/{artifact.id}/versions", headers=headers).status_code == 404
    export = client.post(f"/api/v2/analyses/{artifact.id}/exports",
                         headers=headers, json={"mode": "complete"})
    assert export.status_code == 404
