"""V2 T11 — API do dossiê (aceite do plano)."""

from app.crud import run as run_crud
from app.models.document import Document


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="peca.pdf", file_path="/tmp/peca.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _seed_run_artifact(db_session, user, document):
    run = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="seed-1", snapshot={"module_id": "labor"},
    )
    artifact = run_crud.publish_artifact(
        db_session, run=run,
        content={"schema_version": "2.0", "scope": {"module": "labor"},
                 "coverage": {"pages_total": 2, "pages_extracted": 2},
                 "claims": [{"id": "claim-1", "title": "Pensão"},
                            {"id": "claim-2", "title": "Dano moral"}],
                 "sources": [], "limitations": []},
        status="partial",
    )
    ref = run_crud.add_source_reference(
        db_session, run=run, page_number=1, quote="trecho",
        verification_status="matched",
    )
    return run, artifact, ref


def test_create_run_is_idempotent_and_202(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    payload = {"document_ids": [str(document.id)], "module_id": "labor",
               "idempotency_key": "k1"}
    first = client.post("/api/v2/analysis-runs", headers=auth_headers_for(user), json=payload)
    assert first.status_code == 202
    second = client.post("/api/v2/analysis-runs", headers=auth_headers_for(user), json=payload)
    assert second.json()["run_id"] == first.json()["run_id"]
    status = client.get(first.json()["status_url"].replace("/api/v2", "/api/v2"),
                        headers=auth_headers_for(user))
    assert status.status_code == 200
    assert status.json()["status"] in ("queued", "running")


def test_run_status_reports_stages_and_progress(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    run, _, _ = _seed_run_artifact(db_session, user, document)
    resp = client.get(f"/api/v2/analysis-runs/{run.id}", headers=auth_headers_for(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["progress"] == 100
    assert len(body["stages"]) == 8
    assert body["artifact_id"] is not None


def test_artifact_etag_and_sections(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    _, artifact, _ = _seed_run_artifact(db_session, user, document)
    headers = auth_headers_for(user)
    first = client.get(f"/api/v2/analyses/{artifact.id}", headers=headers)
    assert first.status_code == 200
    assert first.headers.get("etag")
    cached = client.get(f"/api/v2/analyses/{artifact.id}", headers={**headers, "If-None-Match": first.headers["etag"]})
    assert cached.status_code == 304
    page1 = client.get(f"/api/v2/analyses/{artifact.id}/sections/claims?page=1&page_size=1", headers=headers)
    assert page1.json()["total"] == 2
    assert len(page1.json()["items"]) == 1
    overview = client.get(f"/api/v2/analyses/{artifact.id}/sections/overview", headers=headers)
    assert overview.json()["items"][0]["coverage"]["pages_total"] == 2
    bad = client.get(f"/api/v2/analyses/{artifact.id}/sections/nope", headers=headers)
    assert bad.status_code == 404
    assert bad.json()["detail"]["code"] == "NOT_FOUND"


def test_sources_resolve_with_auth(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    _, artifact, ref = _seed_run_artifact(db_session, user, document)
    headers = auth_headers_for(user)
    listing = client.get(f"/api/v2/analyses/{artifact.id}/sources", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["page_number"] == 1
    one = client.get(f"/api/v2/sources/{ref.id}", headers=headers)
    assert one.json()["document_id"] == str(document.id)
    intruder = make_user(email="v2-int@example.com", username="v2-int")
    denied = client.get(f"/api/v2/sources/{ref.id}", headers=auth_headers_for(intruder))
    assert denied.status_code == 404
    assert denied.json()["detail"]["code"] == "NOT_FOUND"


def test_cancel_idempotent_and_reanalyze_coexists(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    created = client.post("/api/v2/analysis-runs", headers=headers,
                          json={"document_ids": [str(document.id)]})
    run_id = created.json()["run_id"]
    cancel1 = client.post(f"/api/v2/analysis-runs/{run_id}/cancel", headers=headers)
    cancel2 = client.post(f"/api/v2/analysis-runs/{run_id}/cancel", headers=headers)
    assert cancel1.json()["status"] == "cancelled" == cancel2.json()["status"]

    _, artifact, _ = _seed_run_artifact(db_session, user, document)
    re = client.post(f"/api/v2/analyses/{artifact.id}/reanalyze", headers=headers)
    assert re.status_code == 202
    assert re.json()["run_id"] != str(artifact.run_id)


def test_review_event_conflict_is_409(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    run, artifact, _ = _seed_run_artifact(db_session, user, document)
    ok = client.post(f"/api/v2/analyses/{artifact.id}/review-events", headers=headers,
                     json={"target": "claims.claim-1", "reason": "ok",
                           "expected_version": run.version})
    assert ok.status_code == 201
    conflict = client.post(f"/api/v2/analyses/{artifact.id}/review-events", headers=headers,
                           json={"target": "x", "expected_version": 1})
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "VERSION_CONFLICT"
    history = client.get(f"/api/v2/analyses/{artifact.id}/review-events", headers=headers)
    assert len(history.json()) == 1


def test_runs_list_by_document(client, db_session, make_user, auth_headers_for):
    user, document = _document(db_session, make_user)
    headers = auth_headers_for(user)
    client.post("/api/v2/analysis-runs", headers=headers,
                json={"document_ids": [str(document.id)], "idempotency_key": "a"})
    client.post("/api/v2/analysis-runs", headers=headers,
                json={"document_ids": [str(document.id)], "idempotency_key": "b"})
    listing = client.get(f"/api/v2/analysis-runs?document_id={document.id}", headers=headers)
    assert len(listing.json()) == 2
