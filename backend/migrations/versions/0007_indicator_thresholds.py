"""indicator thresholds for alerts and classifications

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "indicator_thresholds",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("availability_warning", sa.Numeric(5, 2), nullable=False),
        sa.Column("availability_critical", sa.Numeric(5, 2), nullable=False),
        sa.Column("performance_warning", sa.Numeric(5, 2), nullable=False),
        sa.Column("performance_critical", sa.Numeric(5, 2), nullable=False),
        sa.Column("quality_warning", sa.Numeric(5, 2), nullable=False),
        sa.Column("quality_critical", sa.Numeric(5, 2), nullable=False),
        sa.Column("oee_warning", sa.Numeric(5, 2), nullable=False),
        sa.Column("oee_critical", sa.Numeric(5, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("valid_from", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_indicator_thresholds_line", "indicator_thresholds", ["line_id"])
    op.create_index("ix_indicator_thresholds_product", "indicator_thresholds", ["product_id"])
    op.create_index("ix_indicator_thresholds_active", "indicator_thresholds", ["active"])


def downgrade() -> None:
    op.drop_table("indicator_thresholds")
