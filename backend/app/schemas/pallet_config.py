from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PalletConfigUpsert(BaseModel):
    product_id: int = Field(gt=0)
    line_id: int = Field(gt=0)
    max_boxes: int = Field(gt=0, le=10000)


class PalletConfigRead(BaseModel):
    id: int
    product_id: int
    line_id: int
    max_boxes: int
    active: bool
    valid_from: datetime
    valid_until: datetime | None
    model_config = ConfigDict(from_attributes=True)
