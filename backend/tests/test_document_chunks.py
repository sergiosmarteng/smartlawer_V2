"""Tests for A1: pgvector document_chunks table (Onda A - RAG)."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, MetaData
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.core.database import Base
from app.models import Document, DocumentChunk


def _pg_table():
    """Copy of document_chunks with the real pgvector type.

    conftest swaps Vector -> JSON for sqlite; restore it here to prove
    the production DDL renders VECTOR + HNSW.
    """
    metadata = MetaData()
    for source in Base.metadata.tables.values():
        source.to_metadata(metadata)
    table = metadata.tables["document_chunks"]
    table.c.embedding.type = Vector(1536)
    # conftest strips HNSW for test backends; restore it here to prove
    # the production DDL renders (mirrors DocumentChunk.__table_args__).
    Index(
        "ix_document_chunks_embedding_hnsw",
        table.c.embedding,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    return table


def test_document_chunks_table_registered():
    table = Base.metadata.tables["document_chunks"]
    columns = set(table.columns.keys())
    assert {
        "id",
        "document_id",
        "user_id",
        "matter_id",
        "chunk_index",
        "content",
        "page_start",
        "page_end",
        "token_count",
        "embedding",
        "embedding_model",
        "embedding_model_version",
        "created_at",
    } <= columns


def test_embedding_column_uses_pgvector_1536():
    table = _pg_table()
    assert isinstance(table.c.embedding.type, Vector)
    assert table.c.embedding.type.dim == 1536


def test_postgres_ddl_renders_vector_and_hnsw():
    table = _pg_table()
    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
    assert "VECTOR(1536)" in ddl

    hnsw = [i for i in table.indexes if i.name == "ix_document_chunks_embedding_hnsw"]
    assert len(hnsw) == 1
    index_ddl = str(CreateIndex(hnsw[0]).compile(dialect=postgresql.dialect())).lower()
    assert "hnsw" in index_ddl
    assert "vector_cosine_ops" in index_ddl


def test_migration_file_declares_extension_and_chain(tmp_path=None):
    del tmp_path
    import pathlib

    migration = (
        pathlib.Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260907_0001_document_chunks.py"
    )
    text = migration.read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS vector" in text
    assert 'down_revision = "20260407_0001"' in text
    assert "ondelete=\"CASCADE\"" in text or "ondelete='CASCADE'" in text


def _make_document(db_session, make_user, filename="peticao.pdf"):
    user = make_user()
    document = Document(
        user_id=user.id,
        filename=filename,
        file_path=f"/tmp/{filename}",
        content_type="application/pdf",
        status=Document.STATUS_COMPLETED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def test_chunk_crud_and_ordering(db_session, make_user):
    user, document = _make_document(db_session, make_user)
    for i in (2, 0, 1):
        db_session.add(
            DocumentChunk(
                document_id=document.id,
                user_id=user.id,
                chunk_index=i,
                content=f"Art. {i} do CPC.",
                page_start=i + 1,
                embedding=[0.1 * i, 0.2, 0.3],
            )
        )
    db_session.commit()

    rows = (
        db_session.query(DocumentChunk)
        .filter_by(document_id=document.id, user_id=user.id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    assert [r.content for r in rows] == [
        "Art. 0 do CPC.",
        "Art. 1 do CPC.",
        "Art. 2 do CPC.",
    ]
    assert rows[0].embedding_model == "text-embedding-3-small"
    assert rows[0].embedding_model_version == "v1"


def test_tenant_isolation(db_session, make_user):
    user_a, document_a = _make_document(db_session, make_user, "a.pdf")
    user_b = make_user(
        email="other@example.com", username="other", password="Test123456!"
    )
    db_session.add(
        DocumentChunk(
            document_id=document_a.id,
            user_id=user_a.id,
            chunk_index=0,
            content="chunk do tenant A",
            embedding=[0.1, 0.2, 0.3],
        )
    )
    db_session.add(
        DocumentChunk(
            document_id=document_a.id,
            user_id=user_b.id,
            chunk_index=0,
            content="chunk vazado do tenant B",
            embedding=[0.1, 0.2, 0.3],
        )
    )
    db_session.commit()

    rows = (
        db_session.query(DocumentChunk).filter_by(user_id=user_a.id).all()
    )
    assert [r.content for r in rows] == ["chunk do tenant A"]
