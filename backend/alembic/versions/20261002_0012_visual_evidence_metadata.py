"""Metadados de evidência visual (Onda 0 Task 7).

Revision ID: 20261002_0012
Revises: 20261002_0011
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20261002_0012"
down_revision = "20261002_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_figures",
        sa.Column("kind", sa.String(length=30), nullable=False, server_default="other"),
    )
    op.add_column(
        "document_figures",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="unresolved"),
    )
    op.add_column("document_figures", sa.Column("sensitivity", postgresql.JSONB(), nullable=True))
    op.add_column("document_figures", sa.Column("storage_key", sa.String(length=512), nullable=True))
    op.add_column("document_figures", sa.Column("thumbnail_key", sa.String(length=512), nullable=True))
    op.add_column(
        "document_figures",
        sa.Column("requires_page_context", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("document_figures", "requires_page_context")
    op.drop_column("document_figures", "thumbnail_key")
    op.drop_column("document_figures", "storage_key")
    op.drop_column("document_figures", "sensitivity")
    op.drop_column("document_figures", "status")
    op.drop_column("document_figures", "kind")
