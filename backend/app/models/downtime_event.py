from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class DowntimeEvent(Base):
    __tablename__ = "downtime_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"), nullable=False, index=True)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id"), nullable=True, index=True)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("work_shifts.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="UNPLANNED", index=True)
    reason: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    closed_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
