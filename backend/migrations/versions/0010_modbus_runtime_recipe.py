"""runtime Modbus simulator and product recipe mapping

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("plc_recipe_id", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("plc_recipe_released", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_products_plc_recipe_id", "products", ["plc_recipe_id"])
    op.add_column("plc_transactions", sa.Column("reader_sequence", sa.Integer(), nullable=True))
    op.add_column("plc_transactions", sa.Column("raw_reader_data", sa.String(length=2000), nullable=True))
    op.create_index("ix_plc_transactions_reader_sequence", "plc_transactions", ["reader_sequence"])
    op.create_table(
        "plc_reader_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("reader_sequence", sa.Integer(), nullable=False),
        sa.Column("reader_result", sa.Integer(), nullable=False),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(length=40), nullable=False),
        sa.Column("scan_event_id", sa.BigInteger(), sa.ForeignKey("scan_events.id"), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("reader_sequence", name="uq_plc_reader_events_sequence"),
    )
    op.create_index("ix_plc_reader_events_reader_sequence", "plc_reader_events", ["reader_sequence"])
    op.create_index("ix_plc_reader_events_processing_status", "plc_reader_events", ["processing_status"])
    op.create_index("ix_plc_reader_events_scan_event_id", "plc_reader_events", ["scan_event_id"])
    op.create_index("ix_plc_reader_events_created_at", "plc_reader_events", ["created_at"])
    op.create_table(
        "rework_orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("original_production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="OPEN"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by_username", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rework_orders_original_production_unit_id", "rework_orders", ["original_production_unit_id"])
    op.create_index("ix_rework_orders_status", "rework_orders", ["status"])
    op.create_index("ix_rework_orders_created_at", "rework_orders", ["created_at"])


def downgrade() -> None:
    op.drop_table("rework_orders")
    op.drop_table("plc_reader_events")
    op.drop_index("ix_plc_transactions_reader_sequence", table_name="plc_transactions")
    op.drop_column("plc_transactions", "raw_reader_data")
    op.drop_column("plc_transactions", "reader_sequence")
    op.drop_index("ix_products_plc_recipe_id", table_name="products")
    op.drop_column("products", "plc_recipe_released")
    op.drop_column("products", "plc_recipe_id")
