from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PlcTransaction(Base):
    """Persisted Modbus handshake state for restart/reconnect reconciliation.

    This table is intentionally independent from the physical Modbus adapter.  It
    stores the stable REQUEST_SEQUENCE and payload identity before any write to
    the PLC, so a process restart can resume/reconcile without creating a second
    identity for the same production unit.
    """

    __tablename__ = "plc_transactions"
    __table_args__ = (
        Index("ix_plc_transactions_line_status", "line_id", "status"),
        Index("ix_plc_transactions_request_sequence", "request_sequence"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"), nullable=False, index=True)
    production_order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id"), nullable=False, index=True)
    production_unit_id: Mapped[int] = mapped_column(ForeignKey("production_units.id"), nullable=False, unique=True, index=True)

    request_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    command: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PERSISTED_PENDING", index=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    ack_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_result: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pallet_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    boxes_on_pallet: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reconciliation_status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
