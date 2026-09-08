"""Versioned DOCX generation history (C2/BL-017).

Revision ID: 20260908_0004
Revises: 20260907_0003
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260908_0004"
down_revision = "20260907_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generated_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id", "version", name="uq_generated_analysis_version"),
    )
    op.create_index(
        op.f("ix_generated_documents_analysis_id"),
        "generated_documents",
        ["analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_generated_documents_analysis_id"),
        table_name="generated_documents",
    )
    op.drop_table("generated_documents")
