"""Chunks textuais persistem sem vetor (V2 T04).

Revision ID: 20260925_0010
Revises: 20260925_0009
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260925_0010"
down_revision = "20260925_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column("embedding_provider", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
    )
    # DROP NOT NULL no vetor (testes sqlite usam create_all dos models).
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding DROP NOT NULL")


def downgrade() -> None:
    # Reversível: remove primeiro as linhas só-texto, depois restaura NOT NULL.
    op.execute("DELETE FROM document_chunks WHERE embedding IS NULL")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding SET NOT NULL")
    op.drop_column("document_chunks", "embedding_dimensions")
    op.drop_column("document_chunks", "embedding_provider")
