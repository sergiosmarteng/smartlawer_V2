from app.core import retrieval
from app.core.precedents import (
    CORPUS_VERSION,
    PRECEDENTS,
    SYSTEM_MATTER_ID,
    SYSTEM_USER_ID,
    ensure_precedents,
    precedent_content,
    precedent_label,
)
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def _seed(db_session, **kwargs):
    return ensure_precedents(db_session, **kwargs)


def test_seed_is_idempotent_and_complete(db_session):
    first = _seed(db_session)
    assert first["status"] == "seeded"
    assert first["count"] == len(PRECEDENTS)

    second = _seed(db_session)
    assert second["status"] == "up-to-date"

    rows = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .all()
    )
    assert len(rows) == len(PRECEDENTS)
    assert {row.embedding_model_version for row in rows} == {
        f"seed:{CORPUS_VERSION}:text-embedding-3-small"
    }


def test_seed_uses_real_vectors_when_embed_fn_given(db_session):
    result = _seed(
        db_session,
        embed_fn=lambda texts: [[0.1] * 1536 for _ in texts],
    )
    assert result["vectors"] == "real"
    row = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .first()
    )
    assert row.embedding_model == "text-embedding-3-small"


def test_seed_labels_and_content():
    assert precedent_label(PRECEDENTS[0]).startswith("[Jurisprudência] STF")
    assert "algemas" in precedent_content(PRECEDENTS[0])
    assert len(PRECEDENTS) >= 6


def _system_chunk_ids(db_session):
    return [
        str(row.id)
        for row in db_session.query(DocumentChunk)
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .order_by(DocumentChunk.chunk_index)
        .all()
    ]


def test_shared_corpus_visible_but_foreign_chunks_hidden(
    monkeypatch, db_session, make_user
):
    from app.core.retrieval import hybrid_search

    user = make_user(email="prec-a@example.com", username="prec-a")
    other = make_user(email="prec-b@example.com", username="prec-b")
    _seed(db_session)

    foreign_doc = Document(
        user_id=other.id, filename="privado.pdf", file_path="/tmp/priv.pdf",
        content_type="application/pdf", status="completed",
    )
    db_session.add(foreign_doc)
    db_session.flush()
    foreign_chunk = DocumentChunk(
        document_id=foreign_doc.id, user_id=other.id, chunk_index=0,
        content="conteudo estritamente confidencial xyzzy",
        embedding=[0.0] * 1536,
    )
    db_session.add(foreign_chunk)
    db_session.commit()

    system_ids = _system_chunk_ids(db_session)
    monkeypatch.setattr(
        retrieval, "fetch_vector_candidates", lambda *a, **kw: []
    )
    monkeypatch.setattr(
        retrieval, "fetch_fts_candidates",
        lambda *a, **kw: system_ids + [str(foreign_chunk.id)],
    )

    hits = hybrid_search(
        db_session, user_id=user.id, query_text="uso de algemas lícito",
        query_embedding=None,
    )
    owners = {str(row.user_id) for row in hits}
    assert str(SYSTEM_USER_ID) in owners
    assert str(other.id) not in owners
    assert any("algemas" in row.content for row in hits)


def test_document_scoped_search_excludes_shared_corpus(
    monkeypatch, db_session, make_user
):
    from app.core.retrieval import hybrid_search

    user = make_user(email="prec-c@example.com", username="prec-c")
    _seed(db_session)

    doc = Document(
        user_id=user.id, filename="meu.pdf", file_path="/tmp/meu.pdf",
        content_type="application/pdf", status="completed",
    )
    db_session.add(doc)
    db_session.flush()
    own_chunk = DocumentChunk(
        document_id=doc.id, user_id=user.id, chunk_index=0,
        content="minha petição particular sobre algemas de prisão",
        embedding=[0.0] * 1536,
    )
    db_session.add(own_chunk)
    db_session.commit()

    system_ids = _system_chunk_ids(db_session)
    monkeypatch.setattr(
        retrieval, "fetch_vector_candidates", lambda *a, **kw: []
    )
    monkeypatch.setattr(
        retrieval, "fetch_fts_candidates",
        lambda *a, **kw: system_ids + [str(own_chunk.id)],
    )

    hits = hybrid_search(
        db_session, user_id=user.id, query_text="algemas",
        query_embedding=None, document_id=doc.id,
    )
    assert [str(row.id) for row in hits] == [str(own_chunk.id)]


def test_candidate_sql_keeps_closed_tenant_allowlist():
    assert "user_id = :user_id" in retrieval._TENANT_FILTER_PRIVATE
    assert "user_id = :user_id" in retrieval._TENANT_FILTER_SHARED
    assert ":system_user_id" in retrieval._TENANT_FILTER_SHARED
    rendered_fts = retrieval.FTS_CANDIDATES_SQL.format(
        tenant=retrieval._TENANT_FILTER_SHARED
    )
    assert ":system_user_id" in rendered_fts
    assert ":noop_model" in retrieval.VECTOR_CANDIDATES_SQL


def test_precedents_endpoints_list_and_admin_seed(
    client, db_session, make_user, auth_headers_for
):
    user = make_user(email="prec-ep@example.com", username="prec-ep")
    admin = make_user(email="prec-adm@example.com", username="prec-adm")
    admin.role = "admin"
    db_session.commit()

    listing = client.get("/api/v1/precedents", headers=auth_headers_for(user))
    assert listing.status_code == 200
    assert len(listing.json()) == len(PRECEDENTS)
    assert listing.json()[0]["label"].startswith("[Jurisprudência]")

    forbidden = client.post("/api/v1/precedents/seed", headers=auth_headers_for(user))
    assert forbidden.status_code == 403

    seeded = client.post("/api/v1/precedents/seed", headers=auth_headers_for(admin))
    assert seeded.status_code == 200
    assert seeded.json()["count"] == len(PRECEDENTS)

    rows = (
        db_session.query(DocumentChunk)
        .filter(DocumentChunk.matter_id == SYSTEM_MATTER_ID)
        .count()
    )
    assert rows == len(PRECEDENTS)
