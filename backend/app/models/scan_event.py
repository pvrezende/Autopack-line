from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class ScanEvent(Base):
    __tablename__ = "scan_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"), nullable=False, index=True)
    production_unit_id: Mapped[int | None] = mapped_column(ForeignKey("production_units.id"), nullable=True, index=True)
    raw_code: Mapped[str] = mapped_column(Text, nullable=False)
    code_type: Mapped[str] = mapped_column(String(30), nullable=False, default="QR")
    parsed_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    ean: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    production_order: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
