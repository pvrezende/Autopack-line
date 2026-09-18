"""Rev.03 reader contract and MES quality containment

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-18
"""
from alembic import op
import sqlalchemy as sa


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pallets", sa.Column("quality_status", sa.String(length=30), nullable=False, server_default="CLEAR"))
    op.create_index("ix_pallets_quality_status", "pallets", ["quality_status"])
    op.create_table(
        "mes_quality_results",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=True),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="SIMULATOR"),
        sa.Column("external_event_id", sa.String(length=150), nullable=True, unique=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tested_at", sa.DateTime(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_by_username", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mes_quality_results_serial_number", "mes_quality_results", ["serial_number"])
    op.create_index("ix_mes_quality_results_production_unit_id", "mes_quality_results", ["production_unit_id"])
    op.create_index("ix_mes_quality_results_result", "mes_quality_results", ["result"])
    op.create_index("ix_mes_quality_results_created_at", "mes_quality_results", ["created_at"])
    op.create_table(
        "pallet_quality_incidents",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("quality_result_id", sa.BigInteger(), sa.ForeignKey("mes_quality_results.id"), nullable=False),
        sa.Column("production_unit_id", sa.BigInteger(), sa.ForeignKey("production_units.id"), nullable=False),
        sa.Column("pallet_id", sa.BigInteger(), sa.ForeignKey("pallets.id"), nullable=False),
        sa.Column("pallet_item_id", sa.BigInteger(), sa.ForeignKey("pallet_items.id"), nullable=False),
        sa.Column("pallet_position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING_REMOVAL"),
        sa.Column("detected_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_username", sa.String(length=80), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.UniqueConstraint("quality_result_id", name="uq_quality_incident_result"),
    )
    for name in ("quality_result_id", "production_unit_id", "pallet_id", "pallet_item_id", "status"):
        op.create_index(f"ix_pallet_quality_incidents_{name}", "pallet_quality_incidents", [name])


def downgrade() -> None:
    op.drop_table("pallet_quality_incidents")
    op.drop_table("mes_quality_results")
    op.drop_index("ix_pallets_quality_status", table_name="pallets")
    op.drop_column("pallets", "quality_status")
