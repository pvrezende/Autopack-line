from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class IndicatorThreshold(Base):
    __tablename__ = "indicator_thresholds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("production_lines.id"), nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)

    availability_warning: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    availability_critical: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    performance_warning: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    performance_critical: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    quality_warning: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    quality_critical: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    oee_warning: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    oee_critical: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
