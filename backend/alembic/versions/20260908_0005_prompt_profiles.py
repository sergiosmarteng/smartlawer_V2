"""User prompt profiles for AI runs (C3/BL-020).

Revision ID: 20260908_0005
Revises: 20260908_0004
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260908_0005"
down_revision = "20260908_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("strategy_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prompt_profiles_user_id"),
        "prompt_profiles",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prompt_profiles_user_id"),
        table_name="prompt_profiles",
    )
    op.drop_table("prompt_profiles")
