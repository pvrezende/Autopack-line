"""work schedules, planned breaks and downtime

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_shifts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("crosses_midnight", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("line_id", "code", name="uq_work_shift_line_code"),
    )
    op.create_index("ix_work_shifts_line", "work_shifts", ["line_id"])
    op.create_index("ix_work_shifts_active", "work_shifts", ["active"])

    op.create_table(
        "planned_breaks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("shift_id", sa.BigInteger(), sa.ForeignKey("work_shifts.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("break_type", sa.String(30), nullable=False, server_default="BREAK"),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_planned_breaks_shift", "planned_breaks", ["shift_id"])
    op.create_index("ix_planned_breaks_active", "planned_breaks", ["active"])

    op.create_table(
        "downtime_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("line_id", sa.BigInteger(), sa.ForeignKey("production_lines.id"), nullable=False),
        sa.Column("production_order_id", sa.BigInteger(), sa.ForeignKey("production_orders.id"), nullable=True),
        sa.Column("shift_id", sa.BigInteger(), sa.ForeignKey("work_shifts.id"), nullable=True),
        sa.Column("category", sa.String(30), nullable=False, server_default="UNPLANNED"),
        sa.Column("reason", sa.String(150), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_by_username", sa.String(80), nullable=True),
        sa.Column("closed_by_username", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_downtime_line", "downtime_events", ["line_id"])
    op.create_index("ix_downtime_order", "downtime_events", ["production_order_id"])
    op.create_index("ix_downtime_shift", "downtime_events", ["shift_id"])
    op.create_index("ix_downtime_status", "downtime_events", ["status"])
    op.create_index("ix_downtime_started_at", "downtime_events", ["started_at"])


def downgrade() -> None:
    op.drop_table("downtime_events")
    op.drop_table("planned_breaks")
    op.drop_table("work_shifts")
