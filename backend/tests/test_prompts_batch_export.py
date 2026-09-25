from datetime import datetime, timezone

from app.core.ai_engine import LegalAnalyzer
from app.crud.prompt import get_default_strategy_prompt
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.prompt_profile import PromptProfile


PDF_BYTES = b"%PDF-1.4 test content"


def _pdf_file(name="doc.pdf"):
    return (name, PDF_BYTES, "application/pdf")


def _make_analysis(db_session, make_user, *, email="c3-owner@example.com",
                   username="c3-owner"):
    user = make_user(email=email, username=username)
    document = Document(
        user_id=user.id,
        filename="c3.pdf",
        file_path="/tmp/c3.pdf",
        content_type="application/pdf",
        status="completed",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()
    analysis = Analysis(
        document_id=document.id,
        summary="Resumo C3",
        requests=["Pedido A"],
        laws=["CPC art. 1"],
        evidence="prova X",
        defense_theses=["Tese 1", "Tese 2"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return user, analysis


# --- prompt profiles (BL-020) ---


def test_build_prompt_text_keeps_legacy_default():
    analyzer = LegalAnalyzer()
    legacy = analyzer.build_prompt_text("TEXTO")
    assert "Orientacao adicional" not in legacy
    assert "TEXTO DA PETICAO:\nTEXTO" in legacy

    long_text = "x" * 25000
    truncated = analyzer.build_prompt_text(long_text)
    assert "x" * 20000 in truncated
    assert "x" * 20001 not in truncated


def test_build_prompt_text_injects_profile_guidance():
    analyzer = LegalAnalyzer()
    out = analyzer.build_prompt_text("TEXTO", strategy_prompt="  Enfatize preliminares. ")
    assert "Orientacao adicional do perfil: Enfatize preliminares." in out
    assert "TEXTO DA PETICAO:\nTEXTO" in out


def test_analyze_petition_accepts_strategy_prompt_kwarg(monkeypatch):
    import json as _json

    from app.core import ai_engine as _engine

    analyzer = LegalAnalyzer()
    # Configura provedor fake para exercitar o caminho real de análise.
    analyzer.api_key = "test-key"
    analyzer.model = "test-model"

    captured = {}

    class _FakeMessage:
        content = _json.dumps(
            {
                "summary": "resumo guiado",
                "requests": ["pedido 1"],
                "laws": ["CPC art. 1"],
                "evidence": "prova X",
                "defense_theses": ["tese real 1"],
            }
        )

    class _FakeChoice:
        message = _FakeMessage()

    class _FakeCompletions:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][1]["content"]
            return type("Resp", (), {"choices": [_FakeChoice()]})()

    class _FakeChat:
        completions = _FakeCompletions()

    analyzer.client = type("Client", (), {"chat": _FakeChat()})()
    result = analyzer.analyze_petition("Algum texto", strategy_prompt="guia")
    assert isinstance(result, dict)
    assert result["kind"] == "analysis"
    assert result["summary"] == "resumo guiado"
    assert "guia" in captured["prompt"]

    # Sem provedor: falha explicada (V2 T01), nunca fallback genérico.
    monkeypatch.setattr(_engine, "resolve_chat_config", lambda: None)
    bare = LegalAnalyzer()
    try:
        bare.analyze_petition("Algum texto", strategy_prompt="guia")
    except _engine.ProviderUnavailableError as exc:
        assert exc.code == "PROVIDER_UNAVAILABLE"
    else:
        raise AssertionError("deveria falhar sem provedor configurado")


def test_default_strategy_prompt_lookup(db_session, make_user):
    user = make_user(email="prof-lookup@example.com", username="prof-lookup")
    assert get_default_strategy_prompt(db_session, user_id=user.id) is None

    db_session.add(
        PromptProfile(user_id=user.id, name="p1", strategy_prompt="guia 1")
    )
    db_session.add(
        PromptProfile(
            user_id=user.id, name="p2", strategy_prompt="  guia 2  ",
            is_default=True,
        )
    )
    db_session.commit()
    assert (
        get_default_strategy_prompt(db_session, user_id=user.id) == "guia 2"
    )


def test_prompt_crud_and_default_switch(client, db_session, make_user, auth_headers_for):
    user = make_user(email="prof-crud@example.com", username="prof-crud")
    headers = auth_headers_for(user)

    first = client.post(
        "/api/v1/prompts",
        headers=headers,
        json={"name": "Conciso", "strategy_prompt": "Seja conciso."},
    )
    assert first.status_code == 200
    assert first.json()["is_default"] is False

    second = client.post(
        "/api/v1/prompts",
        headers=headers,
        json={"name": "Agressivo", "strategy_prompt": "Ataque.", "is_default": True},
    )
    assert second.json()["is_default"] is True

    listing = client.get("/api/v1/prompts", headers=headers)
    by_name = {item["name"]: item for item in listing.json()}
    assert by_name["Agressivo"]["is_default"] is True
    assert by_name["Conciso"]["is_default"] is False

    switch = client.patch(
        f"/api/v1/prompts/{first.json()['id']}/default", headers=headers
    )
    assert switch.status_code == 200
    assert switch.json()["is_default"] is True
    assert (
        db_session.query(PromptProfile)
        .filter(PromptProfile.name == "Agressivo")
        .one()
        .is_default
        is False
    )


def test_prompt_routes_reject_bad_input_and_foreign_access(
    client, db_session, make_user, auth_headers_for
):
    user = make_user(email="prof-bad@example.com", username="prof-bad")
    other = make_user(email="prof-other@example.com", username="prof-other")

    assert (
        client.post(
            "/api/v1/prompts", headers=auth_headers_for(user),
            json={"name": "", "strategy_prompt": "x"},
        ).status_code
        in (400, 422)
    )
    assert (
        client.post(
            "/api/v1/prompts", headers=auth_headers_for(user),
            json={"name": "ok", "strategy_prompt": "x" * 2001},
        ).status_code
        == 422
    )

    foreign = PromptProfile(user_id=other.id, name="alheio", strategy_prompt="y")
    db_session.add(foreign)
    db_session.commit()

    assert (
        client.patch(
            f"/api/v1/prompts/{foreign.id}/default",
            headers=auth_headers_for(user),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/prompts/{foreign.id}", headers=auth_headers_for(user)
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/prompts/{foreign.id}", headers=auth_headers_for(other)
        ).status_code
        == 204
    )


# --- batch upload (BL-021) ---


def test_batch_upload_queues_each_pdf(
    client, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user = make_user(email="batch-ok@example.com", username="batch-ok")

    from app.api.routes import documents

    queued = []
    monkeypatch.setattr(documents, "UPLOAD_DIRECTORY", str(temp_dir))
    monkeypatch.setattr(
        documents.process_pdf_task, "delay",
        lambda document_id, file_path: queued.append(document_id),
    )

    response = client.post(
        "/api/v1/documents/batch-upload",
        headers=auth_headers_for(user),
        files=[
            ("files", _pdf_file("a.pdf")),
            ("files", _pdf_file("b.pdf")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["errors"] == []
    assert [item["task_id"] for item in payload["items"]] == queued
    assert all(item["task_id"] == item["id"] for item in payload["items"])


def test_batch_upload_tolerates_rejected_files(
    client, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user = make_user(email="batch-mix@example.com", username="batch-mix")

    from app.api.routes import documents

    monkeypatch.setattr(documents, "UPLOAD_DIRECTORY", str(temp_dir))
    monkeypatch.setattr(documents.process_pdf_task, "delay", lambda *a: None)

    response = client.post(
        "/api/v1/documents/batch-upload",
        headers=auth_headers_for(user),
        files=[
            ("files", _pdf_file("good.pdf")),
            ("files", ("notes.txt", b"nope", "text/plain")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["filename"] == "good.pdf"
    assert len(payload["errors"]) == 1
    assert payload["errors"][0]["filename"] == "notes.txt"


def test_batch_upload_enforces_file_limit(
    client, make_user, auth_headers_for
):
    user = make_user(email="batch-limit@example.com", username="batch-limit")
    response = client.post(
        "/api/v1/documents/batch-upload",
        headers=auth_headers_for(user),
        files=[("files", _pdf_file(f"{i}.pdf")) for i in range(11)],
    )
    assert response.status_code == 400


# --- summary export (BL-022) ---


def test_summary_markdown_download(client, db_session, make_user, auth_headers_for):
    user, analysis = _make_analysis(db_session, make_user)
    response = client.get(
        f"/api/v1/analysis/{analysis.id}/summary.md",
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "summary.md" in response.headers["content-disposition"]
    body = response.text
    assert body.startswith("# Resumo da analise — c3.pdf")
    assert "Resumo C3" in body
    assert "## Pedidos" in body and "Pedido A" in body
    assert "## Fundamentacao legal" in body and "CPC art. 1" in body
    assert "## Provas" in body and "prova X" in body
    assert "## Teses defensivas" in body and "Tese 2" in body


def test_summary_markdown_is_tenant_isolated(
    client, db_session, make_user, auth_headers_for
):
    user, analysis = _make_analysis(
        db_session, make_user,
        email="c3-sum@example.com", username="c3-sum",
    )
    intruder = make_user(email="c3-sum-int@example.com", username="c3-sum-int")
    assert (
        client.get(
            f"/api/v1/analysis/{analysis.id}/summary.md",
            headers=auth_headers_for(intruder),
        ).status_code
        == 404
    )
