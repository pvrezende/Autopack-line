from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PlcReaderEvent(Base):
    __tablename__ = "plc_reader_events"
    __table_args__ = (UniqueConstraint("reader_sequence", name="uq_plc_reader_events_sequence"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    reader_sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reader_result: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    scan_event_id: Mapped[int | None] = mapped_column(ForeignKey("scan_events.id"), nullable=True, index=True)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
