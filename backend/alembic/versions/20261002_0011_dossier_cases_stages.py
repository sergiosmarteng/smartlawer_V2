"""Caso jurídico + checkpoints de estágio do pipeline V3 (Onda 0 Task 2).

Revision ID: 20261002_0011
Revises: 20260925_0010
Create Date: 2026-10-02

Adiciona:
- ``cases`` e ``case_documents`` (agrupador jurídico, autorização estrita).
- ``analysis_stage_runs`` (checkpoint por estágio com ``(run_id, stage, attempt)`` único).
- Coluna ``case_id`` em ``analysis_runs`` e ``analysis_artifacts`` (nullable,
  não remove ``document_id`` — compatibilidade V2 preservada).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20261002_0011"
down_revision = "20260925_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) cases + case_documents.
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("area", sa.String(length=60), nullable=True),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cases_user", "cases", ["user_id"])

    op.create_table(
        "case_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=60), nullable=False, server_default="documento"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id", "document_id", name="uq_case_documents_case_document"
        ),
    )
    op.create_index("ix_case_documents_case", "case_documents", ["case_id"])
    op.create_index("ix_case_documents_document", "case_documents", ["document_id"])

    # 2) analysis_stage_runs.
    op.create_table(
        "analysis_stage_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage", sa.String(length=60), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="running",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("error_code", sa.String(length=60), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retryable", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], ["analysis_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "stage", "attempt", name="uq_stage_run_stage_attempt"
        ),
    )
    op.create_index("ix_analysis_stage_runs_run", "analysis_stage_runs", ["run_id"])

    # 3) case_id em analysis_runs e analysis_artifacts.
    op.add_column(
        "analysis_runs",
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_analysis_runs_case_id",
        "analysis_runs",
        "cases",
        ["case_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_analysis_runs_case", "analysis_runs", ["case_id"])

    op.add_column(
        "analysis_artifacts",
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_analysis_artifacts_case_id",
        "analysis_artifacts",
        "cases",
        ["case_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_analysis_artifacts_case", "analysis_artifacts", ["case_id"])


def downgrade() -> None:
    # Reversão na ordem inversa.
    op.drop_index("ix_analysis_artifacts_case", table_name="analysis_artifacts")
    op.drop_constraint(
        "fk_analysis_artifacts_case_id", "analysis_artifacts", type_="foreignkey"
    )
    op.drop_column("analysis_artifacts", "case_id")

    op.drop_index("ix_analysis_runs_case", table_name="analysis_runs")
    op.drop_constraint(
        "fk_analysis_runs_case_id", "analysis_runs", type_="foreignkey"
    )
    op.drop_column("analysis_runs", "case_id")

    op.drop_index("ix_analysis_stage_runs_run", table_name="analysis_stage_runs")
    op.drop_table("analysis_stage_runs")

    op.drop_index("ix_case_documents_document", table_name="case_documents")
    op.drop_index("ix_case_documents_case", table_name="case_documents")
    op.drop_table("case_documents")

    op.drop_index("ix_cases_user", table_name="cases")
    op.drop_table("cases")