"""V2 T12 — chat coerente + exportação do artefato (aceite do plano)."""

from app.core import rag_answer
from app.core.action_plan import build_action_plan
from app.models.analysis import Analysis
from app.models.document import Document


def _scoped(db_session, make_user, requests):
    user = make_user()
    document = Document(
        user_id=user.id, filename="peca.pdf", file_path="/tmp/peca.pdf",
        content_type="application/pdf", status="completed",
    )
    db_session.add(document)
    db_session.flush()
    analysis = Analysis(
        document_id=document.id, summary="Resumo do caso",
        requests=requests, laws=["CLT art. 2"], evidence="fotos",
        defense_theses=["Tese A", "Tese B"],
    )
    db_session.add(analysis)
    db_session.commit()
    return user, document, analysis


def test_derived_citation_typed_not_primary():
    assert rag_answer.build_case_brief.__doc__ is not None
    import types

    analysis = types.SimpleNamespace(
        id="a1", summary="s", requests=["p1"], laws=[], defense_theses=[]
    )
    brief = rag_answer.build_case_brief("peca.pdf", analysis)
    assert "NÃO é prova" in brief
    citation = rag_answer.analysis_citation("d1", "peca.pdf", analysis)
    assert citation["ref"] == "[A]"
    assert citation["kind"] == "derived"
    assert "análise registrada" in citation["document_name"]


def test_global_query_uses_full_inventory_without_chunks(
    monkeypatch, db_session, make_user
):
    requests = [f"Pedido {i}" for i in range(1, 11)]
    user, document, _ = _scoped(db_session, make_user, requests)
    monkeypatch.setattr(rag_answer, "embed_query", lambda q: None)
    monkeypatch.setattr(
        rag_answer, "hybrid_search", lambda *a, **kw: []
    ) if hasattr(rag_answer, "hybrid_search") else None

    import app.core.retrieval as retrieval

    monkeypatch.setattr(retrieval, "fetch_vector_candidates", lambda *a, **kw: [])
    monkeypatch.setattr(retrieval, "fetch_fts_candidates", lambda *a, **kw: [])

    def forbidden(*a, **kw):
        raise AssertionError("inventário não usa LLM")

    monkeypatch.setattr(rag_answer, "complete", forbidden)
    result = rag_answer.answer_query(
        db_session, user_id=user.id, query="quais são todos os pedidos?",
        document_id=document.id,
    )
    assert result["inventory_based"] is True
    for i in range(1, 11):
        assert f"Pedido {i}" in result["answer"]
    assert result["citations"][0]["kind"] == "derived"


def test_action_plan_is_not_theses_copy():
    plan = build_action_plan(
        {"defense_theses": ["Tese A", "Tese B"], "requests": ["p1"], "laws": ["CLT"]}
    )
    assert plan.startswith("Plano de atuação")
    assert "Avaliar tese 1" in plan and "Avaliar tese 2" in plan
    assert "Tese A" not in plan


def _seed_artifact(client, db_session, make_user, auth_headers_for):
    from app.crud import run as run_crud

    user = make_user()
    document = Document(
        user_id=user.id, filename="p.pdf", file_path="/tmp/p.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    artifact = run_crud.publish_artifact(
        db_session, run=run,
        content={"schema_version": "2.0", "scope": {}, "coverage": {},
                 "claims": [{"id": "c1", "original_number": "8", "title": "Pensão",
                             "amount": {"value": "1400.00", "currency": "BRL"}}],
                 "theses": [{"represented_side": "neutral", "issue": "nexo",
                             "conclusion": "hipótese"}],
                 "limitations": [{"code": "MISSING_CCT", "message": "CCT ausente"}]},
        status="partial",
    )
    return user, artifact


def test_exports_preserve_limitations_and_refs(client, db_session, make_user, auth_headers_for):
    user, artifact = _seed_artifact(client, db_session, make_user, auth_headers_for)
    headers = auth_headers_for(user)
    requested = client.post(f"/api/v2/analyses/{artifact.id}/exports",
                            headers=headers, json={"mode": "complete"})
    assert requested.status_code == 202
    job = requested.json()
    assert job["job_id"] and job["download_url"]
    downloaded = client.get(f"/api/v2{job['download_url'].split('/api/v2')[1]}", headers=headers)
    assert downloaded.status_code == 200
    body = downloaded.text
    assert "Pensão" in body and "1400.00" in body
    assert "MISSING_CCT" in body and "CCT ausente" in body
    assert "## Índice de fontes" in body and "## Teses" in body
    executive = client.post(f"/api/v2/analyses/{artifact.id}/exports",
                            headers=headers, json={"mode": "executive"})
    exec_body = client.get(
        f"/api/v2{executive.json()['download_url'].split('/api/v2')[1]}", headers=headers
    ).text
    assert "## Teses" not in exec_body
    assert "MISSING_CCT" in exec_body  # alertas nos dois modos
    intruder = make_user(email="exp-int@example.com", username="exp-int")
    assert client.post(f"/api/v2/analyses/{artifact.id}/exports",
                       headers=auth_headers_for(intruder),
                       json={"mode": "complete"}).status_code == 404
