from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class PalletItem(Base):
    __tablename__ = "pallet_items"
    __table_args__ = (
        UniqueConstraint("production_unit_id", name="uq_pallet_items_unit"),
        UniqueConstraint("pallet_id", "sequence_number", name="uq_pallet_item_sequence"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pallet_id: Mapped[int] = mapped_column(ForeignKey("pallets.id"), nullable=False, index=True)
    production_unit_id: Mapped[int] = mapped_column(ForeignKey("production_units.id"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
