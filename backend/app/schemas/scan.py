from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BarcodeParsed(BaseModel):
    raw_product_code: str
    model: str
    ean: str
    serial_number: str
    production_order: str
    url: str


class ScanSimulateRequest(BaseModel):
    line_id: int = Field(gt=0)
    raw_code: str = Field(min_length=1, max_length=2000)


class ScanRead(BaseModel):
    id: int
    line_id: int
    production_unit_id: int | None
    raw_code: str
    code_type: str
    parsed_data: dict | None
    serial_number: str | None
    ean: str | None
    production_order: str | None
    status: str
    error_code: str | None
    error_message: str | None
    scanned_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScanSimulationResult(BaseModel):
    scan: ScanRead
    parsed: BarcodeParsed | None
    unit_id: int | None
    product_id: int | None
    production_order_id: int | None


class ScanPage(BaseModel):
    items: list[ScanRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class TestQrResponse(BaseModel):
    raw_code: str
    serial_number: str
    production_order: str
    product_model: str
    ean: str
