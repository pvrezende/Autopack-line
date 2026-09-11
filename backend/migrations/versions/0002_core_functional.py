"""core functional schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_pallet_configs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("max_boxes", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("valid_from", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("product_id", "line_id", "valid_from", name="uq_pallet_config_version"),
    )
    op.create_index("ix_pallet_configs_product", "product_pallet_configs", ["product_id"])
    op.create_index("ix_pallet_configs_line", "product_pallet_configs", ["line_id"])

    op.create_table(
        "production_targets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("hourly_target", sa.Integer(), nullable=True),
        sa.Column("daily_target", sa.Integer(), nullable=True),
        sa.Column("takt_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("valid_from", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_targets_line", "production_targets", ["line_id"])
    op.create_index("ix_targets_product", "production_targets", ["product_id"])

    op.create_table(
        "production_orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("lot_code", sa.String(100), nullable=True),
        sa.Column("planned_quantity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("source", sa.String(30), nullable=False, server_default="LOCAL"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("order_number", name="uq_production_orders_number"),
    )
    op.create_index("ix_orders_number", "production_orders", ["order_number"])
    op.create_index("ix_orders_product", "production_orders", ["product_id"])
    op.create_index("ix_orders_lot", "production_orders", ["lot_code"])
    op.create_index("ix_orders_status", "production_orders", ["status"])

    op.create_table(
        "production_units",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("serial_number", sa.String(100), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("production_order_id", sa.BigInteger(), sa.ForeignKey("production_orders.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="SCANNED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("serial_number", name="uq_production_units_serial"),
    )
    op.create_index("ix_units_serial", "production_units", ["serial_number"])
    op.create_index("ix_units_product", "production_units", ["product_id"])
    op.create_index("ix_units_order", "production_units", ["production_order_id"])
    op.create_index("ix_units_status", "production_units", ["status"])

    op.create_table(
        "scan_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=True),
        sa.Column("raw_code", sa.Text(), nullable=False),
        sa.Column("code_type", sa.String(30), nullable=False, server_default="QR"),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("scanned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_scans_line", "scan_events", ["line_id"])
    op.create_index("ix_scans_unit", "scan_events", ["production_unit_id"])
    op.create_index("ix_scans_status", "scan_events", ["status"])
    op.create_index("ix_scans_scanned_at", "scan_events", ["scanned_at"])

    op.create_table(
        "pallets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("pallet_code", sa.String(100), nullable=False),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("product_id", sa.BigInteger(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("production_order_id", sa.BigInteger(), sa.ForeignKey("production_orders.id"), nullable=False),
        sa.Column("target_quantity", sa.Integer(), nullable=False),
        sa.Column("current_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("opened_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("pallet_code", name="uq_pallets_code"),
    )
    op.create_index("ix_pallets_code", "pallets", ["pallet_code"])
    op.create_index("ix_pallets_line", "pallets", ["line_id"])
    op.create_index("ix_pallets_product", "pallets", ["product_id"])
    op.create_index("ix_pallets_order", "pallets", ["production_order_id"])
    op.create_index("ix_pallets_status", "pallets", ["status"])

    op.create_table(
        "pallet_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("pallet_id", sa.BigInteger(), sa.ForeignKey("pallets.id"), nullable=False),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("production_unit_id", name="uq_pallet_items_unit"),
        sa.UniqueConstraint("pallet_id", "sequence_number", name="uq_pallet_item_sequence"),
    )
    op.create_index("ix_pallet_items_pallet", "pallet_items", ["pallet_id"])
    op.create_index("ix_pallet_items_unit", "pallet_items", ["production_unit_id"])


def downgrade() -> None:
    op.drop_table("pallet_items")
    op.drop_table("pallets")
    op.drop_table("scan_events")
    op.drop_table("production_units")
    op.drop_table("production_orders")
    op.drop_table("production_targets")
    op.drop_table("product_pallet_configs")
