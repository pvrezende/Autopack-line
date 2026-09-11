"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("ean", sa.String(length=14), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("capacity_btu", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
        sa.UniqueConstraint("ean", name="uq_products_ean"),
    )
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_ean", "products", ["ean"])
    op.create_index("ix_products_model", "products", ["model"])

    op.create_table(
        "production_lines",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_production_lines_code"),
    )
    op.create_index("ix_production_lines_code", "production_lines", ["code"])


def downgrade() -> None:
    op.drop_index("ix_production_lines_code", table_name="production_lines")
    op.drop_table("production_lines")
    op.drop_index("ix_products_model", table_name="products")
    op.drop_index("ix_products_ean", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
