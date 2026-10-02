"""Resultados de pesquisa e cálculo (Onda 0 Task 9).

Revision ID: 20261002_0013
Revises: 20261002_0012
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20261002_0013"
down_revision = "20261002_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "legal_research_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issue_id", sa.String(length=120), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("organ", sa.String(length=120), nullable=True),
        sa.Column("identifier", sa.String(length=255), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("consulted_at", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="partial"),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_legal_research_results_run", "legal_research_results", ["run_id"])

    op.create_table(
        "calculation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("formula", sa.String(length=120), nullable=False),
        sa.Column("formula_version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column("inputs", postgresql.JSONB(), nullable=True),
        sa.Column("result", sa.String(length=64), nullable=True),
        sa.Column("output_hash", sa.String(length=128), nullable=True),
        sa.Column("reproducible", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calculation_results_run", "calculation_results", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_calculation_results_run", table_name="calculation_results")
    op.drop_table("calculation_results")
    op.drop_index("ix_legal_research_results_run", table_name="legal_research_results")
    op.drop_table("legal_research_results")
