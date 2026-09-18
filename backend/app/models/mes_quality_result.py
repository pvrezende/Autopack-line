from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MesQualityResult(Base):
    __tablename__ = "mes_quality_results"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    production_unit_id: Mapped[int | None] = mapped_column(ForeignKey("production_units.id"), nullable=True, index=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="SIMULATOR")
    external_event_id: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_username: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
