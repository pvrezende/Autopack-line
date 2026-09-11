from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductionTargetUpsert(BaseModel):
    line_id: int = Field(gt=0)
    product_id: int | None = Field(default=None, gt=0)
    hourly_target: int | None = Field(default=None, gt=0)
    daily_target: int | None = Field(default=None, gt=0)
    takt_seconds: Decimal | None = Field(default=None, gt=0)


class ProductionTargetRead(BaseModel):
    id: int
    line_id: int
    product_id: int | None
    hourly_target: int | None
    daily_target: int | None
    takt_seconds: Decimal | None
    active: bool
    valid_from: datetime
    valid_until: datetime | None
    model_config = ConfigDict(from_attributes=True)
