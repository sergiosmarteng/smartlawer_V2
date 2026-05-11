from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.models.document import Document
from app.models.user import User


def test_upload_document_returns_created_document_and_queues_task(
    client,
    make_user,
    auth_headers_for,
    monkeypatch,
    temp_dir,
):
    user = make_user()
    headers = auth_headers_for(user)

    from app.api.routes import documents

    queued = {}

    def fake_delay(document_id, file_path):
        queued["document_id"] = document_id
        queued["file_path"] = file_path

    monkeypatch.setattr(documents, "UPLOAD_DIRECTORY", str(temp_dir))
    monkeypatch.setattr(documents.process_pdf_task, "delay", fake_delay)

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files={"file": ("petition.pdf", b"%PDF-1.4 test content", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "petition.pdf"
    assert payload["status"] == "PENDING"
    assert payload["task_id"] == payload["id"]
    assert queued["document_id"] == payload["id"]
    assert Path(queued["file_path"]).exists()
    assert Path(queued["file_path"]).parent == temp_dir


def test_upload_document_rejects_non_pdf(client, make_user, auth_headers_for):
    user = make_user(email="pdf-check@example.com", username="pdf-check")

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers_for(user),
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed"


def test_get_user_documents_returns_only_current_user_documents(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    current_user = make_user(email="docs-owner@example.com", username="docs-owner")
    other_user = make_user(email="docs-other@example.com", username="docs-other")

    db_session.add_all(
        [
            Document(
                user_id=current_user.id,
                filename="current-user.pdf",
                file_path="/tmp/current-user.pdf",
                content_type="application/pdf",
                status="uploaded",
                uploaded_at=datetime.now(timezone.utc),
            ),
            Document(
                user_id=other_user.id,
                filename="other-user.pdf",
                file_path="/tmp/other-user.pdf",
                content_type="application/pdf",
                status="completed",
                uploaded_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/documents/", headers=auth_headers_for(current_user))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["filename"] == "current-user.pdf"
    assert payload[0]["user_id"] == str(current_user.id)
