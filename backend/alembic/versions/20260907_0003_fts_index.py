"""Portuguese FTS index for hybrid retrieval (A3).

Revision ID: 20260907_0003
Revises: 20260907_0002
Create Date: 2026-09-07
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260907_0003"
down_revision = "20260907_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_content_fts "
        "ON document_chunks USING gin "
        "(to_tsvector('portuguese', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_content_fts")
