"""Persist raw_text + structured_markdown on documents (A2 Docling).

Revision ID: 20260907_0002
Revises: 20260907_0001
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260907_0002"
down_revision = "20260907_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("raw_text", sa.Text(), nullable=True))
    op.add_column(
        "documents", sa.Column("structured_markdown", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("documents", "structured_markdown")
    op.drop_column("documents", "raw_text")
