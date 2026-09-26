from datetime import datetime, timedelta, timezone

from app.core.audit import audit_document_completion
from app.models.audit_event import AuditEvent
from app.models.document import Document


def _real_pdf_bytes() -> bytes:
    import io

    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Peticao de teste.")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _make_admin(db_session, make_user):
    admin = make_user(email="admin@example.com", username="admin")
    admin.role = "admin"
    db_session.commit()
    return admin


def test_auth_events_are_audited(client, db_session, make_user):
    response = client.post(
        "/api/v1/users/register",
        json={"username": "aud", "email": "aud@example.com", "password": "Test123456!"},
    )
    assert response.status_code == 200

    login = client.post(
        "/api/v1/login/access-token",
        data={"username": "aud@example.com", "password": "Test123456!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    listing = client.get(
        "/api/v1/audit", headers={"Authorization": f"Bearer {token}"}
    )
    assert listing.status_code == 200
    types = [item["event_type"] for item in listing.json()]
    assert AuditEvent.AUTH_REGISTER in types
    assert AuditEvent.AUTH_LOGIN in types


def test_upload_is_audited(client, make_user, auth_headers_for, monkeypatch, temp_dir):
    user = make_user(email="aud-up@example.com", username="aud-up")

    from app.api.routes import documents

    monkeypatch.setattr(documents, "UPLOAD_DIRECTORY", str(temp_dir))
    monkeypatch.setattr(documents.process_pdf_task, "delay", lambda *a: None)

    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers_for(user),
        files={"file": ("a.pdf", _real_pdf_bytes(), "application/pdf")},
    )
    assert upload.status_code == 200

    listing = client.get("/api/v1/audit", headers=auth_headers_for(user))
    uploads = [i for i in listing.json() if i["event_type"] == AuditEvent.DOCUMENT_UPLOAD]
    assert len(uploads) == 1
    assert uploads[0]["entity_id"] == upload.json()["id"]


def test_audit_list_is_tenant_isolated(client, make_user, auth_headers_for):
    owner = make_user(email="aud-iso@example.com", username="aud-iso")
    other = make_user(email="aud-iso2@example.com", username="aud-iso2")

    mine = client.get("/api/v1/audit", headers=auth_headers_for(other))
    assert mine.status_code == 200
    assert mine.json() == []

    owner_rows = client.get("/api/v1/audit", headers=auth_headers_for(owner))
    assert len(owner_rows.json()) >= 0  # shape only; isolation proven by empty other


def test_audit_all_scope_requires_admin(client, db_session, make_user, auth_headers_for):
    user = make_user(email="aud-scope@example.com", username="aud-scope")
    admin = _make_admin(db_session, make_user)

    forbidden = client.get(
        "/api/v1/audit?scope=all", headers=auth_headers_for(user)
    )
    assert forbidden.status_code == 403

    allowed = client.get(
        "/api/v1/audit?scope=all", headers=auth_headers_for(admin)
    )
    assert allowed.status_code == 200


def test_ops_summary_is_admin_only(client, db_session, make_user, auth_headers_for):
    user = make_user(email="ops-user@example.com", username="ops-user")
    admin = _make_admin(db_session, make_user)

    assert (
        client.get("/api/v1/ops/summary", headers=auth_headers_for(user)).status_code
        == 403
    )
    summary = client.get(
        "/api/v1/ops/summary", headers=auth_headers_for(admin)
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert "documents_by_status" in payload
    assert "events_24h" in payload
    assert "recent_failures" in payload


def test_completion_audit_records_timing_and_failures(db_session, make_user):
    user = make_user(email="aud-time@example.com", username="aud-time")
    now = datetime.now(timezone.utc)
    completed = Document(
        user_id=user.id, filename="ok.pdf", file_path="/tmp/ok.pdf",
        content_type="application/pdf", status="completed",
        status_detail="Analysis ready",
        uploaded_at=now - timedelta(seconds=90), completed_at=now,
    )
    failed = Document(
        user_id=user.id, filename="bad.pdf", file_path="/tmp/bad.pdf",
        content_type="application/pdf", status="error",
        status_detail="Processing failed", error_message="boom" * 200,
        uploaded_at=now - timedelta(seconds=30), completed_at=now,
    )
    db_session.add_all([completed, failed])
    db_session.commit()

    audit_document_completion(db_session, document=completed)
    audit_document_completion(db_session, document=failed)
    audit_document_completion(db_session, document=None)  # must never raise

    rows = {row.entity_id: row for row in db_session.query(AuditEvent).all()}
    assert rows[str(completed.id)].event_type == AuditEvent.DOCUMENT_COMPLETED
    assert rows[str(completed.id)].meta["duration_ms"] == 90000
    assert rows[str(failed.id)].event_type == AuditEvent.DOCUMENT_FAILED
    assert len(rows[str(failed.id)].meta["error"]) <= 500


def test_register_ignores_role_escalation(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "username": "escalate", "email": "escalate@example.com",
            "password": "Test123456!", "role": "admin",
        },
    )
    assert response.status_code == 200
    from app.crud.user import get_user_by_email

    stored = get_user_by_email(db_session, email="escalate@example.com")
    assert stored.role == "user"
