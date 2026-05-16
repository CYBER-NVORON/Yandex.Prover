from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_analysis_context_fields"
down_revision = "0001_create_analysis_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analysis_runs",
        sa.Column("has_regulation", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("has_benchmark", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("audience_knowledge_level", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column("analysis_runs", sa.Column("readiness_verdict", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_runs", "readiness_verdict")
    op.drop_column("analysis_runs", "audience_knowledge_level")
    op.drop_column("analysis_runs", "has_benchmark")
    op.drop_column("analysis_runs", "has_regulation")
