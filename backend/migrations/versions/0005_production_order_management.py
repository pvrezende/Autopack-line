"""production order management

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("production_orders", sa.Column("line_id", sa.BigInteger(), nullable=True))
    op.add_column("production_orders", sa.Column("notes", sa.String(length=500), nullable=True))
    op.add_column("production_orders", sa.Column("created_by_username", sa.String(length=80), nullable=True))
    op.add_column("production_orders", sa.Column("started_by_username", sa.String(length=80), nullable=True))
    op.add_column("production_orders", sa.Column("finished_by_username", sa.String(length=80), nullable=True))
    op.create_foreign_key("fk_production_orders_line", "production_orders", "production_lines", ["line_id"], ["id"])
    op.create_index("ix_orders_line", "production_orders", ["line_id"])
    # Preserva OPs históricas já observadas pelo scanner e tenta inferir a linha usada.
    op.execute("""
        UPDATE production_orders po
        LEFT JOIN (
            SELECT pu.production_order_id, MIN(se.line_id) AS line_id
            FROM production_units pu
            JOIN scan_events se ON se.production_unit_id = pu.id
            GROUP BY pu.production_order_id
        ) x ON x.production_order_id = po.id
        SET po.line_id = x.line_id
        WHERE po.line_id IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_orders_line", table_name="production_orders")
    op.drop_constraint("fk_production_orders_line", "production_orders", type_="foreignkey")
    op.drop_column("production_orders", "finished_by_username")
    op.drop_column("production_orders", "started_by_username")
    op.drop_column("production_orders", "created_by_username")
    op.drop_column("production_orders", "notes")
    op.drop_column("production_orders", "line_id")
