from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MesQualityResultCreate(BaseModel):
    serial_number: str = Field(min_length=1, max_length=100)
    result: Literal["OK", "NG"]
    external_event_id: str | None = Field(default=None, max_length=150)
    tested_at: datetime | None = None
    raw_payload: dict | None = None


class RemovalConfirmation(BaseModel):
    note: str = Field(min_length=3, max_length=1000)
