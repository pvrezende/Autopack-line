"""persisted PLC transaction/reconciliation state

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plc_transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("production_order_id", sa.BigInteger(), sa.ForeignKey("production_orders.id"), nullable=False),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=False),
        sa.Column("request_sequence", sa.Integer(), nullable=False),
        sa.Column("command", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PERSISTED_PENDING"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("ack_sequence", sa.Integer(), nullable=True),
        sa.Column("result_code", sa.Integer(), nullable=True),
        sa.Column("completed_sequence", sa.Integer(), nullable=True),
        sa.Column("completion_result", sa.Integer(), nullable=True),
        sa.Column("pallet_sequence", sa.Integer(), nullable=True),
        sa.Column("boxes_on_pallet", sa.Integer(), nullable=True),
        sa.Column("reconciliation_status", sa.String(length=60), nullable=True),
        sa.Column("last_error", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("production_unit_id", name="uq_plc_transactions_production_unit"),
    )
    op.create_index("ix_plc_transactions_line_id", "plc_transactions", ["line_id"])
    op.create_index("ix_plc_transactions_production_order_id", "plc_transactions", ["production_order_id"])
    op.create_index("ix_plc_transactions_production_unit_id", "plc_transactions", ["production_unit_id"])
    op.create_index("ix_plc_transactions_status", "plc_transactions", ["status"])
    op.create_index("ix_plc_transactions_line_status", "plc_transactions", ["line_id", "status"])
    op.create_index("ix_plc_transactions_request_sequence", "plc_transactions", ["request_sequence"])


def downgrade() -> None:
    op.drop_table("plc_transactions")
