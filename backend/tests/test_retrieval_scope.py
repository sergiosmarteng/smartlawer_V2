"""V2 T04 — texto independente do vetor (aceite do plano)."""

import app.tasks.document_tasks as tasks
from app.core import retrieval
from app.core.embeddings import embedding_space, validate_query_embedding, validate_vectors
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

PETITION = "Requer a condenacao ao pagamento de danos morais. " * 20


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id,
        filename="p.pdf",
        file_path="/tmp/p.pdf",
        content_type="application/pdf",
        status=Document.STATUS_COMPLETED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def test_document_scope_reaches_candidates_before_ranking(
    monkeypatch, db_session, make_user
):
    user, document = _document(db_session, make_user)
    seen = {}

    def fake_vector(db, **kw):
        seen["vector"] = kw
        return []

    def fake_fts(db, **kw):
        seen["fts"] = kw
        return []

    monkeypatch.setattr(retrieval, "fetch_vector_candidates", fake_vector)
    monkeypatch.setattr(retrieval, "fetch_fts_candidates", fake_fts)
    retrieval.hybrid_search(
        db_session,
        user_id=user.id,
        query_text="danos morais",
        query_embedding=[0.1] * retrieval.settings.EMBEDDING_DIMENSIONS,
        document_id=document.id,
    )
    assert str(seen["vector"]["document_id"]) == str(document.id)
    assert str(seen["fts"]["document_id"]) == str(document.id)


def test_invalid_query_embedding_degrades_to_fts(monkeypatch, db_session, make_user):
    user, _ = _document(db_session, make_user)

    def forbidden(db, **kw):
        raise AssertionError("ANN não pode rodar com vetor inválido")

    monkeypatch.setattr(retrieval, "fetch_vector_candidates", forbidden)
    monkeypatch.setattr(retrieval, "fetch_fts_candidates", lambda db, **kw: [])
    assert (
        retrieval.hybrid_search(
            db_session, user_id=user.id, query_text="x",
            query_embedding=[0.1, 0.2],  # dimensão errada
        )
        == []
    )
    assert validate_query_embedding([0.1, 0.2]) is False
    assert validate_query_embedding([0.1] * retrieval.settings.EMBEDDING_DIMENSIONS) is True


def test_cardinality_mismatch_persists_text_only(monkeypatch, db_session, make_user):
    _, document = _document(db_session, make_user)
    # Propositalmente menos vetores que textos (sem zip silencioso).
    monkeypatch.setattr(
        tasks, "embed_texts", lambda texts: [[0.1] * 1536 for _ in texts[:-1]]
    )
    stored = tasks.index_document_chunks(str(document.id), PETITION)
    assert stored >= 1
    rows = db_session.query(DocumentChunk).filter_by(document_id=document.id).all()
    assert len(rows) == stored
    assert all(r.embedding is None for r in rows)


def test_nan_vector_rejected_without_crash(monkeypatch, db_session, make_user):
    _, document = _document(db_session, make_user)
    bad = [[float("nan")] * retrieval.settings.EMBEDDING_DIMENSIONS]
    monkeypatch.setattr(tasks, "embed_texts", lambda texts: bad * len(texts))
    stored = tasks.index_document_chunks(str(document.id), PETITION)
    rows = db_session.query(DocumentChunk).filter_by(document_id=document.id).all()
    assert len(rows) == stored
    assert all(r.embedding is None for r in rows)
    assert validate_vectors(["a"], bad) is False


def test_text_only_chunk_found_by_degraded_search(monkeypatch, db_session, make_user):
    user, document = _document(db_session, make_user)
    monkeypatch.setattr(tasks, "embed_texts", lambda texts: None)
    stored = tasks.index_document_chunks(str(document.id), PETITION)
    assert stored >= 1
    chunk_id = (
        db_session.query(DocumentChunk).filter_by(document_id=document.id).first().id
    )
    monkeypatch.setattr(
        retrieval, "fetch_fts_candidates", lambda db, **kw: [str(chunk_id)]
    )
    rows = retrieval.hybrid_search(
        db_session, user_id=user.id, query_text="danos morais",
        query_embedding=None,
    )
    assert [str(r.id) for r in rows] == [str(chunk_id)]


def test_embedding_space_identifies_generation():
    space = embedding_space()
    assert set(space) == {"provider", "model", "version", "dimensions"}
    assert space["dimensions"] == retrieval.settings.EMBEDDING_DIMENSIONS
