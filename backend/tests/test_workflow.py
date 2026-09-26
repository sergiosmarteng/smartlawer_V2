from datetime import datetime, timedelta, timezone

from app.models.analysis import Analysis
from app.models.document import Document


def test_list_processes_returns_normalized_statuses_and_user_scope(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    current_user = make_user(email="workflow-owner@example.com", username="workflow-owner")
    other_user = make_user(email="workflow-other@example.com", username="workflow-other")

    older_document = Document(
        user_id=current_user.id,
        filename="older.pdf",
        file_path="/tmp/older.pdf",
        content_type="application/pdf",
        status="completed",
        status_detail="Analysis ready",
        uploaded_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    newer_document = Document(
        user_id=current_user.id,
        filename="newer.pdf",
        file_path="/tmp/newer.pdf",
        content_type="application/pdf",
        status="processing",
        status_detail="Extracting text from PDF",
        uploaded_at=datetime.now(timezone.utc),
    )
    foreign_document = Document(
        user_id=other_user.id,
        filename="foreign.pdf",
        file_path="/tmp/foreign.pdf",
        content_type="application/pdf",
        status="uploaded",
        uploaded_at=datetime.now(timezone.utc),
    )

    db_session.add_all([older_document, newer_document, foreign_document])
    db_session.flush()
    db_session.add(
        Analysis(
            document_id=older_document.id,
            summary="Ready",
            requests=["Request 1"],
            laws=["Law 1"],
            evidence={"type": "contract"},
            defense_theses=["Thesis 1"],
        )
    )
    db_session.commit()

    response = client.get("/api/v1/processes", headers=auth_headers_for(current_user))

    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload] == ["newer.pdf", "older.pdf"]
    assert payload[0]["status"] == "PROCESSING"
    assert payload[0]["analysis_id"] is None
    assert payload[1]["status"] == "COMPLETED"
    assert payload[1]["analysis_id"] is not None


def test_task_status_returns_progress_and_links(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    user = make_user(email="task-status@example.com", username="task-status")
    document = Document(
        user_id=user.id,
        filename="status.pdf",
        file_path="/tmp/status.pdf",
        content_type="application/pdf",
        status="processing",
        status_detail="Generating legal analysis",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()

    analysis = Analysis(
        document_id=document.id,
        summary="Status ready",
        requests=["Pedido"],
        laws=["Art. 1"],
        evidence={"pages": [1, 2]},
        defense_theses=["Negar pedido"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(document)
    db_session.refresh(analysis)

    response = client.get(
        f"/api/v1/tasks/{document.id}",
        headers=auth_headers_for(user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PROCESSING"
    assert payload["progress"] == 75
    assert payload["analysis_id"] == str(analysis.id)
    assert payload["analysis_url"] == f"/analysis/{analysis.id}"
    assert payload["docxDownloadUrl"] == f"/analysis/{analysis.id}/docx"


def test_task_status_uses_document_identity_and_blocks_cross_user(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    owner = make_user(email="identity-owner@example.com", username="identity-owner")
    intruder = make_user(
        email="identity-intruder@example.com",
        username="identity-intruder",
        password="Test123456!",
    )
    document = Document(
        user_id=owner.id,
        filename="identity.pdf",
        file_path="/tmp/identity.pdf",
        content_type="application/pdf",
        status="processing",
        status_detail="Extracting text from PDF",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.commit()

    own = client.get(
        f"/api/v1/tasks/{document.id}",
        headers=auth_headers_for(owner),
    )
    assert own.status_code == 200
    assert own.json()["task_id"] == own.json()["document_id"] == str(document.id)

    foreign = client.get(
        f"/api/v1/tasks/{document.id}",
        headers=auth_headers_for(intruder),
    )
    assert foreign.status_code == 404


def test_analysis_detail_returns_generated_strategy(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    user = make_user(email="analysis-detail@example.com", username="analysis-detail")
    document = Document(
        user_id=user.id,
        filename="analysis.pdf",
        file_path="/tmp/analysis.pdf",
        content_type="application/pdf",
        status="completed",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()

    analysis = Analysis(
        document_id=document.id,
        summary="Resumo da analise",
        requests=["Improcedencia"],
        laws=["CPC art. 330"],
        evidence={"attachments": ["contrato"]},
        defense_theses=["Inépcia da inicial", "Ausência de prova mínima"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    response = client.get(
        f"/api/v1/analysis/{analysis.id}",
        headers=auth_headers_for(user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["documentName"] == "analysis.pdf"
    # V2 T12/D06: plano de atuação, não cópia das teses.
    strategy = payload["generatedDefenseStrategy"]
    assert strategy.startswith("Plano de atuação")
    assert "Avaliar tese 1" in strategy and "Avaliar tese 2" in strategy
    assert "Inépcia da inicial" not in strategy.splitlines()[0]
    assert payload["defense_theses"] == ["Inépcia da inicial", "Ausência de prova mínima"]
    assert payload["docxDownloadUrl"] == f"/analysis/{analysis.id}/docx"


def test_analysis_docx_download_returns_file_response(
    client,
    db_session,
    make_user,
    auth_headers_for,
    monkeypatch,
    temp_dir,
):
    user = make_user(email="docx-download@example.com", username="docx-download")
    document = Document(
        user_id=user.id,
        filename="download.pdf",
        file_path="/tmp/download.pdf",
        content_type="application/pdf",
        status="completed",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()

    analysis = Analysis(
        document_id=document.id,
        summary="Docx ready",
        requests=["Pedido de improcedência"],
        laws=["CC art. 421"],
        evidence={"attachments": []},
        defense_theses=["Boa-fé objetiva"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    generated_file = temp_dir / "generated.docx"
    generated_file.write_bytes(b"docx-bytes")

    from app.api.routes import templates

    monkeypatch.setattr(
        templates.DocxGenerator,
        "generate_defense",
        staticmethod(lambda analysis_dict, template_path: str(generated_file)),
    )

    response = client.get(
        f"/api/v1/analysis/{analysis.id}/docx",
        headers=auth_headers_for(user),
    )

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert "attachment;" in response.headers["content-disposition"]
    assert ".docx" in response.headers["content-disposition"]
    assert response.content == b"docx-bytes"


def test_task_status_returns_404_for_other_users_document(
    client,
    db_session,
    make_user,
    auth_headers_for,
):
    owner = make_user(email="task-owner@example.com", username="task-owner")
    intruder = make_user(email="task-intruder@example.com", username="task-intruder")
    document = Document(
        user_id=owner.id,
        filename="owner-only.pdf",
        file_path="/tmp/owner-only.pdf",
        content_type="application/pdf",
        status="uploaded",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    response = client.get(
        f"/api/v1/tasks/{document.id}",
        headers=auth_headers_for(intruder),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
