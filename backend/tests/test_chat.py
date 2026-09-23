"""Tests for A4: grounded chat with citations (Onda A - RAG)."""

import json

from app.api.routes import chat as chat_route
from app.core import rag_answer
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def _make_doc_with_chunk(db_session, make_user, content, **user_kw):
    user = make_user(**user_kw)
    document = Document(
        user_id=user.id,
        filename="contrato.pdf",
        file_path="/tmp/contrato.pdf",
        content_type="application/pdf",
        status=Document.STATUS_COMPLETED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    chunk = DocumentChunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=0,
        content=content,
        page_start=2,
        embedding=[0.1, 0.2, 0.3],
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)
    return user, document, chunk


def _sse_events(text):
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


def test_chat_requires_auth(client):
    assert client.post("/api/v1/chat", json={"query": "abc"}).status_code in (
        401,
        403,
    )
    assert client.post("/api/v1/chat/stream", json={"query": "abc"}).status_code in (
        401,
        403,
    )


def test_chat_unavailable_without_key(client, db_session, make_user, auth_headers_for):
    user = make_user()
    response = client.post(
        "/api/v1/chat",
        json={"query": "qual o prazo?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 503


def test_chat_returns_grounded_answer_with_citations(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user, document, chunk = _make_doc_with_chunk(
        db_session, make_user, "O prazo para contestacao e de 15 dias."
    )
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(rag_answer, "embed_query", lambda _q: [0.1, 0.2, 0.3])
    monkeypatch.setattr(
        "app.core.retrieval.hybrid_search", lambda *a, **kw: [chunk]
    )
    monkeypatch.setattr(
        rag_answer,
        "complete",
        lambda _p, system=None: ("O prazo e de 15 dias [1].", "gpt-4-turbo"),
    )

    response = client.post(
        "/api/v1/chat",
        json={"query": "qual o prazo para contestacao?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "O prazo e de 15 dias [1]."
    assert payload["ai_draft"] is True
    assert payload["requires_human_review"] is True
    assert len(payload["citations"]) == 1
    citation = payload["citations"][0]
    assert citation["ref"] == "[1]"
    assert citation["document_id"] == str(document.id)
    assert citation["document_name"] == "contrato.pdf"
    assert citation["page_start"] == 2
    assert "15 dias" in citation["excerpt"]


def test_chat_stream_tokens_then_citations(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user, _document, chunk = _make_doc_with_chunk(
        db_session, make_user, "O prazo para contestacao e de 15 dias."
    )
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(chat_route, "embed_query", lambda _q: [0.1])
    monkeypatch.setattr(chat_route, "hybrid_search", lambda *a, **kw: [chunk])

    def fake_stream(_prompt, system=None):
        yield "O prazo ", "gpt-4-turbo"
        yield "e de 15 dias [1].", "gpt-4-turbo"

    monkeypatch.setattr(rag_answer, "complete_stream", fake_stream)

    response = client.post(
        "/api/v1/chat/stream",
        json={"query": "qual o prazo?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    events = _sse_events(response.text)
    tokens = "".join(e["token"] for e in events if "token" in e)
    assert tokens == "O prazo e de 15 dias [1]."
    done = [e for e in events if e.get("done")]
    assert len(done) == 1
    assert len(done[0]["citations"]) == 1
    assert done[0]["citations"][0]["ref"] == "[1]"


def test_chat_no_chunks_returns_fallback(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user = make_user()
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(rag_answer, "embed_query", lambda _q: None)
    monkeypatch.setattr("app.core.retrieval.hybrid_search", lambda *a, **kw: [])

    response = client.post(
        "/api/v1/chat",
        json={"query": "pergunta sem base?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"] == []
    assert "Não encontrei fundamento" in payload["answer"]


def test_chat_cross_user_document_scope_is_404(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    owner, document, _chunk = _make_doc_with_chunk(
        db_session,
        make_user,
        "conteudo sigiloso",
        email="owner@example.com",
        username="owner",
    )
    intruder = make_user(
        email="intruder@example.com",
        username="intruder",
        password="Test123456!",
    )
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)

    response = client.post(
        "/api/v1/chat",
        json={"query": "o que diz o documento?", "document_id": str(document.id)},
        headers=auth_headers_for(intruder),
    )
    assert response.status_code == 404


def test_chat_invalid_document_id_is_422(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user = make_user()
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    response = client.post(
        "/api/v1/chat",
        json={"query": "o que diz?", "document_id": "not-a-uuid"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 422


def test_grounded_prompt_numbers_contexts():
    prompt = rag_answer.build_grounded_prompt(
        "prazo?", [("id1", "texto um"), ("id2", "texto dois")]
    )
    assert "[1] texto um" in prompt
    assert "[2] texto dois" in prompt
    assert "prazo?" in prompt


class _FakeCompletions:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    def create(self, **_kwargs):
        if self._error is not None:
            raise self._error
        message = type("Message", (), {"content": self._content})()
        choice = type("Choice", (), {"message": message})()
        return type("Response", (), {"choices": [choice]})()


class _FakeChat:
    def __init__(self, content=None, error=None):
        self.completions = _FakeCompletions(content, error)


class _FakeClient:
    def __init__(self, content=None, error=None):
        self.chat = _FakeChat(content, error)


def test_suggest_followups_parses_and_caps_at_three(monkeypatch):
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    content = (
        "1. Qual a conclusao sobre o prazo?\n"
        "2) Que estrategia de defesa cabe aqui?\n"
        "- Que ponto do caso elucidar primeiro?\n"
        "4. Pergunta excedente que deve cair\n"
        "Qual a conclusao sobre o prazo?"
    )
    monkeypatch.setattr(
        rag_answer, "_chat_client", lambda: (_FakeClient(content), "fake-model")
    )
    suggestions = rag_answer.suggest_followups("prazo?", "O prazo e de 15 dias [1].")
    assert suggestions == [
        "Qual a conclusao sobre o prazo?",
        "Que estrategia de defesa cabe aqui?",
        "Que ponto do caso elucidar primeiro?",
    ]


def test_suggest_followups_empty_on_llm_failure(monkeypatch):
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(
        rag_answer,
        "_chat_client",
        lambda: (_FakeClient(error=RuntimeError("boom")), "fake-model"),
    )
    assert rag_answer.suggest_followups("prazo?", "resposta") == []


def test_suggest_followups_empty_when_unconfigured_or_blank(monkeypatch):
    monkeypatch.setattr(rag_answer, "is_configured", lambda: False)
    assert rag_answer.suggest_followups("prazo?", "resposta") == []
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    assert rag_answer.suggest_followups("prazo?", "   ") == []


def test_chat_response_carries_suggested_questions(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user, _document, chunk = _make_doc_with_chunk(
        db_session, make_user, "O prazo para contestacao e de 15 dias."
    )
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(rag_answer, "embed_query", lambda _q: [0.1, 0.2, 0.3])
    monkeypatch.setattr(
        "app.core.retrieval.hybrid_search", lambda *a, **kw: [chunk]
    )
    monkeypatch.setattr(
        rag_answer,
        "complete",
        lambda _p, system=None: ("O prazo e de 15 dias [1].", "gpt-4-turbo"),
    )
    monkeypatch.setattr(
        rag_answer,
        "suggest_followups",
        lambda _q, _a: ["Que estrategia de defesa cabe aqui?"],
    )

    response = client.post(
        "/api/v1/chat",
        json={"query": "qual o prazo para contestacao?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    assert response.json()["suggested_questions"] == [
        "Que estrategia de defesa cabe aqui?"
    ]


def test_chat_stream_done_event_carries_suggested_questions(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    user, _document, chunk = _make_doc_with_chunk(
        db_session, make_user, "O prazo para contestacao e de 15 dias."
    )
    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(chat_route, "embed_query", lambda _q: [0.1])
    monkeypatch.setattr(chat_route, "hybrid_search", lambda *a, **kw: [chunk])
    monkeypatch.setattr(
        rag_answer,
        "complete_stream",
        lambda _p, system=None: iter([("ok [1].", "gpt-4-turbo")]),
    )
    monkeypatch.setattr(
        rag_answer,
        "suggest_followups",
        lambda _q, _a: ["Qual a conclusao sobre o prazo?"],
    )

    response = client.post(
        "/api/v1/chat/stream",
        json={"query": "qual o prazo?"},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    done = [e for e in _sse_events(response.text) if e.get("done")]
    assert len(done) == 1
    assert done[0]["suggested_questions"] == ["Qual a conclusao sobre o prazo?"]


def test_counsel_prompt_frames_case_and_keeps_data_boundary():
    brief = (
        "DOCUMENTO: reclamatoria.pdf\n"
        "RESUMO DOS FATOS (análise registrada — cite como [A]):\n"
        "Acidente com trituradora sem trava de segurança.\n"
    )
    prompt = rag_answer.build_counsel_prompt(
        "qual a tese de defesa?", [("id1", "trecho do caso")], brief
    )
    assert "sócio sênior" in rag_answer.COUNSEL_SYSTEM_PROMPT
    assert "40 anos" in rag_answer.COUNSEL_SYSTEM_PROMPT
    assert "estratégia" in rag_answer.COUNSEL_SYSTEM_PROMPT.lower()
    assert "ANÁLISE REGISTRADA DO CASO (referência [A])" in prompt
    assert "[1] trecho do caso" in prompt
    assert "TRECHOS RECUPERADOS" in prompt

    briefless = rag_answer.build_counsel_prompt("resumo do caso?", [], "")
    assert "SEM TRECHOS RECUPERADOS" in briefless
    assert "PERGUNTA DO ADVOGADO" in briefless


def test_chat_answers_from_analysis_brief_when_no_chunks(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    from app.models.analysis import Analysis

    user, document, _chunk = _make_doc_with_chunk(
        db_session, make_user, "texto qualquer"
    )
    db_session.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).delete()
    analysis = Analysis(
        document_id=document.id,
        summary="Reclamatoria por acidente de trabalho com trituradora sem trava.",
        requests=["indenizacao por danos materiais"],
        laws=["Art. 927 CC"],
        defense_theses=["culpa exclusiva da vitima"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(rag_answer, "embed_query", lambda _q: None)
    monkeypatch.setattr(
        "app.core.retrieval.hybrid_search", lambda *a, **kw: []
    )
    captured = {}

    def fake_complete(prompt, system=None):
        captured["prompt"] = prompt
        captured["system"] = system
        return ("Tese: culpa exclusiva da vitima [A].", "gpt-4-turbo")

    monkeypatch.setattr(rag_answer, "complete", fake_complete)
    monkeypatch.setattr(rag_answer, "suggest_followups", lambda _q, _a: [])

    response = client.post(
        "/api/v1/chat",
        json={
            "query": "qual a melhor tese de defesa?",
            "document_id": str(document.id),
        },
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("Tese:")
    assert "Não encontrei fundamento" not in payload["answer"]
    # Case brief grounded the prompt, counsel persona drove the system.
    assert "RESUMO DOS FATOS" in captured["prompt"]
    assert "trituradora" in captured["prompt"]
    assert captured["system"] == rag_answer.COUNSEL_SYSTEM_PROMPT
    # Synthetic [A] citation links to the analysis page.
    assert len(payload["citations"]) == 1
    citation = payload["citations"][0]
    assert citation["ref"] == "[A]"
    assert citation["document_id"] == str(document.id)
    assert "análise registrada" in citation["document_name"]


def test_chat_stream_analysis_brief_fallback(
    monkeypatch, client, db_session, make_user, auth_headers_for
):
    from app.models.analysis import Analysis

    user, document, _chunk = _make_doc_with_chunk(
        db_session, make_user, "texto qualquer"
    )
    db_session.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).delete()
    db_session.add(
        Analysis(document_id=document.id, summary="Caso trabalhista com dano moral.")
    )
    db_session.commit()

    monkeypatch.setattr(rag_answer, "is_configured", lambda: True)
    monkeypatch.setattr(chat_route, "embed_query", lambda _q: None)
    monkeypatch.setattr(chat_route, "hybrid_search", lambda *a, **kw: [])
    monkeypatch.setattr(
        rag_answer,
        "complete_stream",
        lambda _p, system=None: iter([("Estrategia [A].", "gpt-4-turbo")]),
    )
    monkeypatch.setattr(rag_answer, "suggest_followups", lambda _q, _a: [])

    response = client.post(
        "/api/v1/chat/stream",
        json={"query": "monte a estrategia", "document_id": str(document.id)},
        headers=auth_headers_for(user),
    )
    assert response.status_code == 200
    events = _sse_events(response.text)
    tokens = "".join(e["token"] for e in events if "token" in e)
    assert tokens == "Estrategia [A]."
    done = [e for e in events if e.get("done")]
    assert len(done) == 1
    assert [c["ref"] for c in done[0]["citations"]] == ["[A]"]
