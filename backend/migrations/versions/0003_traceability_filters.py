"""traceability indexed fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("scan_events", sa.Column("serial_number", sa.String(100), nullable=True))
    op.add_column("scan_events", sa.Column("ean", sa.String(20), nullable=True))
    op.add_column("scan_events", sa.Column("production_order", sa.String(50), nullable=True))
    op.execute("UPDATE scan_events SET serial_number = JSON_UNQUOTE(JSON_EXTRACT(parsed_data, '$.serial_number')) WHERE parsed_data IS NOT NULL")
    op.execute("UPDATE scan_events SET ean = JSON_UNQUOTE(JSON_EXTRACT(parsed_data, '$.ean')) WHERE parsed_data IS NOT NULL")
    op.execute("UPDATE scan_events SET production_order = JSON_UNQUOTE(JSON_EXTRACT(parsed_data, '$.production_order')) WHERE parsed_data IS NOT NULL")
    op.create_index("ix_scan_events_serial_number", "scan_events", ["serial_number"])
    op.create_index("ix_scan_events_ean", "scan_events", ["ean"])
    op.create_index("ix_scan_events_production_order", "scan_events", ["production_order"])
    op.create_index("ix_pallets_opened_at", "pallets", ["opened_at"])

def downgrade() -> None:
    op.drop_index("ix_pallets_opened_at", table_name="pallets")
    op.drop_index("ix_scan_events_production_order", table_name="scan_events")
    op.drop_index("ix_scan_events_ean", table_name="scan_events")
    op.drop_index("ix_scan_events_serial_number", table_name="scan_events")
    op.drop_column("scan_events", "production_order")
    op.drop_column("scan_events", "ean")
    op.drop_column("scan_events", "serial_number")
