from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    line_id: Mapped[int | None] = mapped_column(ForeignKey("production_lines.id"), nullable=True, index=True)
    lot_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    planned_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="LOCAL")
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    started_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    finished_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
