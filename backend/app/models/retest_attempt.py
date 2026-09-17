from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RetestAttempt(Base):
    __tablename__ = "retest_attempts"
    __table_args__ = (
        UniqueConstraint("production_unit_id", "attempt_number", name="uq_retest_attempt_unit_number"),
        UniqueConstraint("idempotency_key", name="uq_retest_attempt_idempotency"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    production_unit_id: Mapped[int] = mapped_column(ForeignKey("production_units.id"), nullable=False, index=True)
    scan_event_id: Mapped[int | None] = mapped_column(ForeignKey("scan_events.id"), nullable=True, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="SIMULATOR", index=True)
    authorization_status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING_PROCESS_DEFINITION")
    reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    counted_in_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)
