from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PalletQualityIncident(Base):
    __tablename__ = "pallet_quality_incidents"
    __table_args__ = (UniqueConstraint("quality_result_id", name="uq_quality_incident_result"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    quality_result_id: Mapped[int] = mapped_column(ForeignKey("mes_quality_results.id"), nullable=False, index=True)
    production_unit_id: Mapped[int] = mapped_column(ForeignKey("production_units.id"), nullable=False, index=True)
    pallet_id: Mapped[int] = mapped_column(ForeignKey("pallets.id"), nullable=False, index=True)
    pallet_item_id: Mapped[int] = mapped_column(ForeignKey("pallet_items.id"), nullable=False, index=True)
    pallet_position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING_REMOVAL", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
