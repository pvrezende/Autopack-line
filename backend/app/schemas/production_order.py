from datetime import datetime
from pydantic import BaseModel, Field


class ProductionOrderCreate(BaseModel):
    order_number: str = Field(min_length=1, max_length=50)
    product_id: int = Field(gt=0)
    line_id: int | None = Field(default=None, gt=0)
    lot_code: str | None = Field(default=None, max_length=100)
    planned_quantity: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)


class ProductionOrderUpdate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    line_id: int | None = Field(default=None, gt=0)
    lot_code: str | None = Field(default=None, max_length=100)
    planned_quantity: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)


class ProductionOrderRead(BaseModel):
    id: int
    order_number: str
    product_id: int
    product_model: str | None = None
    product_name: str | None = None
    line_id: int | None
    line_code: str | None = None
    line_name: str | None = None
    lot_code: str | None
    planned_quantity: int | None
    produced_quantity: int = 0
    scanned_quantity: int = 0
    progress_percent: float = 0
    open_pallets: int = 0
    completed_pallets: int = 0
    status: str
    source: str
    notes: str | None
    created_by_username: str | None
    started_by_username: str | None
    finished_by_username: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProductionOrderPage(BaseModel):
    items: list[ProductionOrderRead]
    total: int
    page: int
    page_size: int
    total_pages: int
