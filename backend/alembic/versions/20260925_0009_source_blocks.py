"""Revisoes e blocos de fonte da extracao (V2 T03).

Revision ID: 20260925_0009
Revises: 20260925_0008
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260925_0009"
down_revision = "20260925_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("pages_total", sa.Integer(), nullable=True),
        sa.Column("origin", sa.String(length=255), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_revisions_document", "document_revisions", ["document_id"]
    )

    op.create_table(
        "source_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_uid", sa.String(length=32), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("page_label", sa.String(length=64), nullable=True),
        sa.Column("block_type", sa.String(length=30), nullable=False),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("bbox", postgresql.JSONB(), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("text_hash", sa.String(length=64), nullable=True),
        sa.Column("extraction_method", sa.String(length=40), nullable=True),
        sa.Column("quality_flags", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["revision_id"], ["document_revisions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_blocks_revision", "source_blocks", ["revision_id"]
    )
    op.create_index(
        "ix_source_blocks_page",
        "source_blocks",
        ["revision_id", "page_number"],
    )

    # Liga as figuras à revisão que as originou (V2 §6) — reaproveita o
    # catálogo existente, sem segundo catálogo concorrente.
    op.add_column(
        "document_figures",
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_figures_revision",
        "document_figures",
        "document_revisions",
        ["revision_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_document_figures_revision", "document_figures", type_="foreignkey"
    )
    op.drop_column("document_figures", "revision_id")
    op.drop_index("ix_source_blocks_page", table_name="source_blocks")
    op.drop_index("ix_source_blocks_revision", table_name="source_blocks")
    op.drop_table("source_blocks")
    op.drop_index(
        "ix_document_revisions_document", table_name="document_revisions"
    )
    op.drop_table("document_revisions")
