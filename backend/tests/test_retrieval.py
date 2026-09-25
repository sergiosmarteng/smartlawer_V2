"""Tests for A3: legal chunker, hybrid retrieval, rerank (Onda A - RAG)."""

import app.tasks.document_tasks as tasks
from app.core import retrieval
from app.core.legal_chunker import chunk_legal_text, estimate_tokens
from app.core.retrieval import rrf_fuse
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

PETITION = """PETICAO INICIAL

I - DOS FATOS
O autor alega inadimplemento contratual ocorrido em janeiro, com cobrancas indevidas em fatura.

Art. 1 O contrato firmado entre as partes estabelece o pagamento mensal ate o dia dez.
Paragrafo unico. O atraso superior a trinta dias autoriza a rescisao motivada.

Art. 2 Em caso de cobranca indevida, o valor deve ser restituido em dobro ao consumidor.
O paragrafo anterior aplica-se inclusive aos encargos acessorios da fatura.

II - DOS PEDIDOS
Requer a condenacao da re ao pagamento de dez mil reais por danos materiais e morais.
"""


def _make_chunk(db_session, make_user, content, index=0, user=None):
    user = user or make_user()
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
    chunk = DocumentChunk(
        document_id=document.id,
        user_id=user.id,
        chunk_index=index,
        content=content,
        embedding=[0.1, 0.2, 0.3],
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)
    return user, chunk


# --- Chunker -----------------------------------------------------------------


def test_chunker_never_splits_article_header_from_body():
    chunks = chunk_legal_text(PETITION, max_tokens=60, overlap_tokens=10)
    assert chunks, "expected at least one chunk"
    art2 = [c for c in chunks if "Art. 2" in c.content]
    assert art2, "Art. 2 header must survive chunking"
    assert any("restituido em dobro" in c.content for c in art2)


def test_chunker_respects_budget_and_counts_tokens():
    chunks = chunk_legal_text(PETITION, max_tokens=120, overlap_tokens=20)
    for chunk in chunks:
        assert chunk.token_count == estimate_tokens(chunk.content)
        assert chunk.token_count <= 120
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunker_overlap_links_consecutive_chunks():
    chunks = chunk_legal_text(PETITION, max_tokens=60, overlap_tokens=15)
    assert len(chunks) >= 2
    first_words = chunks[1].content.split()
    assert any(w in chunks[0].content for w in first_words[:8])


def test_chunker_empty_input():
    assert chunk_legal_text("") == []
    assert chunk_legal_text("   ") == []


# --- RRF ---------------------------------------------------------------------


def test_rrf_fuse_orders_by_score():
    # a: 1/62 + 1/61 beats x: 1/61 — presence in both lists wins.
    assert rrf_fuse([["x", "a"], ["a"]], k=60) == ["a", "x"]


def test_rrf_fuse_tie_breaks_by_first_seen():
    # a and c tie at 1/61; a seen first (vector list leads).
    assert rrf_fuse([["a", "b"], ["c"]], k=60) == ["a", "c", "b"]


def test_rrf_fuse_empty():
    assert rrf_fuse([[], []]) == []


# --- SQL shape (tenant-first) -------------------------------------------------


def test_candidate_queries_always_filter_tenant():
    for template in (
        retrieval.VECTOR_CANDIDATES_SQL,
        retrieval.FTS_CANDIDATES_SQL,
    ):
        assert "{tenant}" in template
    assert retrieval._TENANT_FILTER_PRIVATE == "user_id = :user_id"
    assert ":system_user_id" in retrieval._TENANT_FILTER_SHARED
    assert "<=>" in retrieval.VECTOR_CANDIDATES_SQL
    assert "to_tsvector('portuguese'" in retrieval.FTS_CANDIDATES_SQL
    # Keyless seed rows must never enter the vector branch.
    assert ":noop_model" in retrieval.VECTOR_CANDIDATES_SQL
    assert retrieval.NOOP_EMBEDDING_MODEL == "seed-noop"
    # V2 T04: document scope aplicado ANTES do ranking + NULL fora do ANN.
    for template in (
        retrieval.VECTOR_CANDIDATES_SQL,
        retrieval.FTS_CANDIDATES_SQL,
    ):
        assert ":document_id" in template
    assert "embedding IS NOT NULL" in retrieval.VECTOR_CANDIDATES_SQL


# --- Rerank fallback ------------------------------------------------------------


def test_rerank_disabled_keeps_order(monkeypatch):
    monkeypatch.setattr(retrieval.settings, "RERANK_ENABLED", False)
    candidates = [("id1", "texto 1"), ("id2", "texto 2")]
    assert retrieval.rerank("q", candidates, top_n=2) == ["id1", "id2"]


def test_rerank_without_key_keeps_order(monkeypatch):
    monkeypatch.setattr(retrieval.settings, "RERANK_ENABLED", True)
    monkeypatch.setattr(retrieval.settings, "COHERE_API_KEY", "")
    candidates = [("id1", "texto 1"), ("id2", "texto 2")]
    assert retrieval.rerank("q", candidates, top_n=1) == ["id1"]


# --- hybrid_search on sqlite (fusion + tenant barrier) --------------------------


def test_hybrid_search_fuses_and_enforces_tenant(
    monkeypatch, db_session, make_user
):
    user, chunk_a = _make_chunk(db_session, make_user, "cobranca indevida", index=0)
    other = make_user(
        email="leak@example.com", username="leak", password="Test123456!"
    )
    _, chunk_leak = _make_chunk(
        db_session, make_user, "cobranca indevida", index=0, user=other
    )

    monkeypatch.setattr(
        retrieval, "fetch_vector_candidates", lambda *a, **kw: [str(chunk_a.id)]
    )
    monkeypatch.setattr(
        retrieval,
        "fetch_fts_candidates",
        # Malicious/buggy FTS pretending the other tenant's chunk matched:
        lambda *a, **kw: [str(chunk_leak.id), str(chunk_a.id)],
    )

    rows = retrieval.hybrid_search(
        db_session,
        user_id=user.id,
        query_text="cobranca indevida",
        query_embedding=[0.1] * retrieval.settings.EMBEDDING_DIMENSIONS,
        top_k=6,
    )
    assert [str(r.id) for r in rows] == [str(chunk_a.id)]


def test_hybrid_search_degrades_to_fts_without_embedding(
    monkeypatch, db_session, make_user
):
    user, chunk_a = _make_chunk(db_session, make_user, "dano moral", index=0)

    def forbidden(**kw):
        raise AssertionError("vector search must not run without embedding")

    monkeypatch.setattr(retrieval, "fetch_vector_candidates", forbidden)
    monkeypatch.setattr(
        retrieval, "fetch_fts_candidates", lambda *a, **kw: [str(chunk_a.id)]
    )

    rows = retrieval.hybrid_search(
        db_session,
        user_id=user.id,
        query_text="dano moral",
        query_embedding=None,
    )
    assert [str(r.id) for r in rows] == [str(chunk_a.id)]


def test_hybrid_search_empty_returns_empty(monkeypatch, db_session, make_user):
    user = make_user()
    monkeypatch.setattr(retrieval, "fetch_vector_candidates", lambda *a, **kw: [])
    monkeypatch.setattr(retrieval, "fetch_fts_candidates", lambda *a, **kw: [])
    assert (
        retrieval.hybrid_search(
            db_session,
            user_id=user.id,
            query_text="nada",
            query_embedding=[0.1] * retrieval.settings.EMBEDDING_DIMENSIONS,
        )
        == []
    )


# --- Worker indexing ------------------------------------------------------------


def test_index_document_chunks_persists_and_is_idempotent(
    monkeypatch, db_session, make_user
):
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

    monkeypatch.setattr(
        tasks,
        "embed_texts",
        lambda texts: [[0.1] * retrieval.settings.EMBEDDING_DIMENSIONS for _ in texts],
    )

    first = tasks.index_document_chunks(str(document.id), PETITION)
    assert first >= 1
    rows = (
        db_session.query(DocumentChunk)
        .filter_by(document_id=document.id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    assert len(rows) == first
    assert all(str(r.user_id) == str(user.id) for r in rows)
    assert rows[0].embedding_model == "text-embedding-3-small"
    assert all(r.embedding is not None for r in rows)

    second = tasks.index_document_chunks(str(document.id), PETITION)
    assert second == first
    assert (
        db_session.query(DocumentChunk)
        .filter_by(document_id=document.id)
        .count()
        == first
    )


def test_index_document_chunks_persists_text_without_embeddings(
    monkeypatch, db_session, make_user
):
    """V2 T04: sem embeddings, o texto persiste (FTS degradada)."""
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

    monkeypatch.setattr(tasks, "embed_texts", lambda texts: None)
    stored = tasks.index_document_chunks(str(document.id), PETITION)
    assert stored >= 1
    rows = (
        db_session.query(DocumentChunk)
        .filter_by(document_id=document.id)
        .all()
    )
    assert len(rows) == stored
    assert all(r.embedding is None for r in rows)
    assert all(r.content for r in rows)
