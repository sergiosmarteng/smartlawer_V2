"""Onda 0 Task 12 — API universal V3 (casos, visuais, versões, resume)."""

from app.crud import run as run_crud
from app.models.document import Document


def _document(db_session, make_user, name="p12.pdf"):
    user = make_user()
    document = Document(
        user_id=user.id, filename=name, file_path=f"/tmp/{name}",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _v3_content(**overrides):
    base = {
        "schema_version": "3.0",
        "section_states": {
            "claims": {"status": "complete", "reason": "ok",
                       "coverage": {}, "pending_actions": []},
        },
        "coverage": {"pages_total": 2, "pages_extracted": 2},
        "claims": [{"id": "claim-1", "title": "Guarda"}],
        "facts": [],
        "evidence": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "visuals": [{"id": "vis-1", "page_number": 1,
                     "storage_key": "opaque-vis-1", "thumbnail_key": "opaque-thumb-1"}],
        "limitations": [],
    }
    base.update(overrides)
    return base


def test_create_and_read_case(client, db_session, make_user, auth_headers_for):
    user, _ = _document(db_session, make_user)
    headers = auth_headers_for(user)
    created = client.post("/api/v2/cases", headers=headers, json={"name": "Caso A"})
    assert created.status_code == 201
    case_id = created.json()["id"]
    got = client.get(f"/api/v2/cases/{case_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Caso A"


def test_attach_own_document_and_reject_foreign(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    intruder = make_user(email="i12@x.com", username="i12")
    headers = auth_headers_for(user)
    case_id = client.post("/api/v2/cases", headers=headers, json={}).json()["id"]
    ok = client.post(f"/api/v2/cases/{case_id}/documents", headers=headers,
                     json={"document_id": str(document.id), "role": "petição"})
    assert ok.status_code == 201
    denied = client.post(f"/api/v2/cases/{case_id}/documents",
                         headers=auth_headers_for(intruder),
                         json={"document_id": str(document.id)})
    assert denied.status_code == 404


def test_create_run_with_snapshot_and_filter(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    case_id = client.post("/api/v2/cases", headers=headers, json={}).json()["id"]
    created = client.post("/api/v2/analysis-runs", headers=headers, json={
        "document_ids": [str(document.id)], "case_id": case_id,
        "represented_side": "claimant", "objective": "revisão",
        "reference_date": "2026-10-02", "idempotency_key": "v3-k1",
    })
    assert created.status_code == 202
    listing = client.get(f"/api/v2/analysis-runs?case_id={case_id}", headers=headers)
    assert listing.status_code == 200
    assert any(r["run_id"] == created.json()["run_id"] for r in listing.json())


def test_section_with_section_state(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_v3_content(), status="partial")
    resp = client.get(f"/api/v2/analyses/{artifact.id}/sections/claims", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_visuals_list_without_internal_paths(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_v3_content(), status="partial")
    resp = client.get(f"/api/v2/analyses/{artifact.id}/visuals", headers=headers)
    assert resp.status_code == 200
    assert resp.json()[0]["storage_key"] == "opaque-vis-1"
    assert "file_path" not in resp.json()[0]


def test_versions_and_compare(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    run1 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    art1 = run_crud.publish_artifact(
        db_session, run=run1, content=_v3_content(), status="partial")
    run2 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    content2 = _v3_content(claims=[{"id": "claim-1", "title": "Guarda"},
                                   {"id": "claim-2", "title": "Alimentos"}])
    art2 = run_crud.publish_artifact(
        db_session, run=run2, content=content2, status="partial")
    versions = client.get(f"/api/v2/analyses/{art2.id}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()) == 2
    compare = client.get(
        f"/api/v2/analyses/{art2.id}/compare?against={art1.id}", headers=headers)
    assert compare.status_code == 200
    assert compare.json()["added"] == ["claim-2"]


def test_resume_only_for_resumable(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    failed = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(db_session, run=failed, status="failed")
    ok = client.post(f"/api/v2/analysis-runs/{failed.id}/resume", headers=headers)
    assert ok.status_code == 202
    assert ok.json()["status"] == "queued"
    done = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(db_session, run=done, status="completed",
                            stage="publication")
    conflict = client.post(f"/api/v2/analysis-runs/{done.id}/resume", headers=headers)
    assert conflict.status_code == 409


def test_other_user_ids_return_404(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run, content=_v3_content(), status="partial")
    intruder = make_user(email="j12@x.com", username="j12")
    headers = auth_headers_for(intruder)
    assert client.get(f"/api/v2/analyses/{artifact.id}", headers=headers).status_code == 404
    assert client.get(f"/api/v2/analyses/{artifact.id}/visuals", headers=headers).status_code == 404


def test_error_envelope_has_no_secrets(client, db_session, make_user, auth_headers_for):
    user, _ = _document(db_session, make_user)
    resp = client.get(
        "/api/v2/analyses/00000000-0000-0000-0000-000000000000",
        headers=auth_headers_for(user),
    )
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert detail["code"] == "NOT_FOUND"
    blob = str(resp.json()).lower()
    assert "traceback" not in blob and "prompt" not in blob
