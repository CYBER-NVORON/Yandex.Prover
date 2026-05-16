from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_create_analysis_runs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("material_type", sa.Text(), nullable=False),
        sa.Column("audience_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("provider_name", sa.Text(), nullable=True),
        sa.Column("provider_model", sa.Text(), nullable=True),
        sa.Column("provider_response_id", sa.Text(), nullable=True),
        sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("persuasiveness_score", sa.Integer(), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_runs_created_at_desc", "analysis_runs", ["created_at"])
    op.create_index("ix_analysis_runs_persuasiveness_score", "analysis_runs", ["persuasiveness_score"])


def downgrade() -> None:
    op.drop_index("ix_analysis_runs_persuasiveness_score", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_created_at_desc", table_name="analysis_runs")
    op.drop_table("analysis_runs")
