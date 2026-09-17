"""ETAPA 7.31 - historico controlado de tentativas de reteste

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retest_attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=False),
        sa.Column("scan_event_id", sa.BigInteger(), sa.ForeignKey("scan_events.id"), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="SIMULATOR"),
        sa.Column("authorization_status", sa.String(length=40), nullable=False, server_default="PENDING_PROCESS_DEFINITION"),
        sa.Column("reason_code", sa.String(length=80), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("counted_in_production", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_by_username", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("production_unit_id", "attempt_number", name="uq_retest_attempt_unit_number"),
        sa.UniqueConstraint("idempotency_key", name="uq_retest_attempt_idempotency"),
    )
    op.create_index("ix_retest_attempts_production_unit_id", "retest_attempts", ["production_unit_id"])
    op.create_index("ix_retest_attempts_scan_event_id", "retest_attempts", ["scan_event_id"])
    op.create_index("ix_retest_attempts_decision", "retest_attempts", ["decision"])
    op.create_index("ix_retest_attempts_source", "retest_attempts", ["source"])
    op.create_index("ix_retest_attempts_created_at", "retest_attempts", ["created_at"])


def downgrade() -> None:
    op.drop_table("retest_attempts")
