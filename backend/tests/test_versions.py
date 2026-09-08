from datetime import datetime, timezone
from pathlib import Path

from app.models.analysis import Analysis
from app.models.document import Document
from app.models.generated_document import GeneratedDocument


def _make_analysis(db_session, make_user, *, email="c2-owner@example.com",
                   username="c2-owner"):
    user = make_user(email=email, username=username)
    document = Document(
        user_id=user.id,
        filename="c2.pdf",
        file_path="/tmp/c2.pdf",
        content_type="application/pdf",
        status="completed",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()
    analysis = Analysis(
        document_id=document.id,
        summary="Resumo C2",
        requests=["Pedido A"],
        laws=["CPC art. 1"],
        evidence="prova",
        defense_theses=["Tese 1"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return user, analysis


def _stub_renderer(monkeypatch, temp_dir):
    """Fake generate_defense writing distinct bytes per call; returns paths."""
    from app.api.routes import templates as templates_routes

    calls = []

    def fake_generate(analysis_dict, template_path):
        index = len(calls) + 1
        out = temp_dir / f"render-{index}.docx"
        out.write_bytes(f"docx-version-{index}".encode())
        calls.append({"template_path": template_path, "path": str(out)})
        return str(out)

    monkeypatch.setattr(
        templates_routes.DocxGenerator,
        "generate_defense",
        staticmethod(fake_generate),
    )
    return calls


def test_generate_records_versions_and_recovers_previous(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(db_session, make_user)
    _stub_renderer(monkeypatch, temp_dir)

    from app.api.routes import templates as templates_routes

    monkeypatch.setattr(templates_routes, "GENERATED_DIR", str(temp_dir / "gen"))

    for _ in range(2):
        response = client.get(
            f"/api/v1/analysis/{analysis.id}/docx",
            headers=auth_headers_for(user),
        )
        assert response.status_code == 200

    listing = client.get(
        f"/api/v1/analysis/{analysis.id}/versions",
        headers=auth_headers_for(user),
    )
    assert listing.status_code == 200
    payload = listing.json()
    assert [item["version"] for item in payload] == [2, 1]
    assert payload[0]["downloadUrl"] == f"/analysis/{analysis.id}/versions/2"
    assert payload[0]["template_id"] is None

    first = client.get(
        f"/api/v1/analysis/{analysis.id}/versions/1",
        headers=auth_headers_for(user),
    )
    assert first.status_code == 200
    assert first.content == b"docx-version-1"
    assert ".docx" in first.headers["content-disposition"]


def test_retention_keeps_only_latest_n(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(
        db_session, make_user, email="c2-ret@example.com", username="c2-ret"
    )
    _stub_renderer(monkeypatch, temp_dir)

    from app.api.routes import templates as templates_routes
    from app.core.config import settings

    gen_dir = temp_dir / "gen-ret"
    monkeypatch.setattr(templates_routes, "GENERATED_DIR", str(gen_dir))
    monkeypatch.setattr(settings, "GENERATED_KEEP_LATEST", 2)

    for _ in range(3):
        assert (
            client.get(
                f"/api/v1/analysis/{analysis.id}/docx",
                headers=auth_headers_for(user),
            ).status_code
            == 200
        )

    rows = (
        db_session.query(GeneratedDocument)
        .filter(GeneratedDocument.analysis_id == analysis.id)
        .order_by(GeneratedDocument.version)
        .all()
    )
    assert [row.version for row in rows] == [2, 3]
    assert not list(gen_dir.rglob("*_v1.docx"))
    assert Path(rows[0].file_path).exists()


def test_versions_are_tenant_isolated(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(
        db_session, make_user, email="c2-vic@example.com", username="c2-vic"
    )
    intruder = make_user(email="c2-int@example.com", username="c2-int")
    _stub_renderer(monkeypatch, temp_dir)

    from app.api.routes import templates as templates_routes

    monkeypatch.setattr(templates_routes, "GENERATED_DIR", str(temp_dir / "gen-iso"))

    assert (
        client.get(
            f"/api/v1/analysis/{analysis.id}/docx",
            headers=auth_headers_for(user),
        ).status_code
        == 200
    )

    assert (
        client.get(
            f"/api/v1/analysis/{analysis.id}/versions",
            headers=auth_headers_for(intruder),
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/analysis/{analysis.id}/versions/1",
            headers=auth_headers_for(intruder),
        ).status_code
        == 404
    )


def test_download_missing_version_or_file_returns_404(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(
        db_session, make_user, email="c2-miss@example.com", username="c2-miss"
    )
    missing = client.get(
        f"/api/v1/analysis/{analysis.id}/versions/9",
        headers=auth_headers_for(user),
    )
    assert missing.status_code == 404

    db_session.add(
        GeneratedDocument(
            user_id=user.id,
            document_id=analysis.document_id,
            analysis_id=analysis.id,
            template_id=None,
            file_path=str(temp_dir / "gone.docx"),
            version=1,
        )
    )
    db_session.commit()

    gone = client.get(
        f"/api/v1/analysis/{analysis.id}/versions/1",
        headers=auth_headers_for(user),
    )
    assert gone.status_code == 404
    assert "no longer available" in gone.json()["detail"]


def test_persist_failure_still_serves_download(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(
        db_session, make_user, email="c2-fail@example.com", username="c2-fail"
    )
    _stub_renderer(monkeypatch, temp_dir)

    from app.api.routes import templates as templates_routes

    blocker = temp_dir / "blocker"
    blocker.write_bytes(b"not a directory")
    monkeypatch.setattr(templates_routes, "GENERATED_DIR", str(blocker))

    response = client.get(
        f"/api/v1/analysis/{analysis.id}/docx",
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    assert response.content == b"docx-version-1"
