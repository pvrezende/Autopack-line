from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PalletRead(BaseModel):
    id: int
    pallet_code: str
    line_id: int
    product_id: int
    production_order_id: int
    target_quantity: int
    current_quantity: int
    status: str
    opened_at: datetime
    completed_at: datetime | None
    closed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class PalletizeRequest(BaseModel):
    line_id: int = Field(gt=0)
    production_unit_id: int = Field(gt=0)
    position: int | None = Field(default=None, gt=0)


class PalletizeResult(BaseModel):
    pallet: PalletRead
    production_unit_id: int
    sequence_number: int
    completed_now: bool


class PalletPage(BaseModel):
    items: list[PalletRead]
    total: int
    page: int
    page_size: int
    total_pages: int
