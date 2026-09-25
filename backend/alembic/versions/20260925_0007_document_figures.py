"""Figuras extraídas dos documentos (Docling + fitz fallback).

Revision ID: 20260925_0007
Revises: 20260908_0006
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260925_0007"
down_revision = "20260908_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_figures",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("bbox", postgresql.JSONB(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_figures_document", "document_figures", ["document_id"]
    )
    op.create_index(
        "ix_document_figures_user", "document_figures", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_document_figures_user", table_name="document_figures")
    op.drop_index("ix_document_figures_document", table_name="document_figures")
    op.drop_table("document_figures")
