from datetime import datetime, time
from pydantic import BaseModel, Field, model_validator


class WorkShiftCreate(BaseModel):
    line_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    active: bool = True


class WorkShiftUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    active: bool | None = None


class WorkShiftRead(BaseModel):
    id: int
    line_id: int
    line_code: str | None = None
    code: str
    name: str
    start_time: time
    end_time: time
    crosses_midnight: bool
    active: bool
    planned_minutes: int
    planned_break_minutes: int
    net_planned_minutes: int


class WorkShiftPage(BaseModel):
    items: list[WorkShiftRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlannedBreakCreate(BaseModel):
    shift_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    break_type: str = Field(default="BREAK", pattern="^(BREAK|MEAL|SETUP|OTHER)$")
    start_time: time
    end_time: time
    active: bool = True


class PlannedBreakUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    break_type: str | None = Field(default=None, pattern="^(BREAK|MEAL|SETUP|OTHER)$")
    start_time: time | None = None
    end_time: time | None = None
    active: bool | None = None


class PlannedBreakRead(BaseModel):
    id: int
    shift_id: int
    shift_code: str | None = None
    shift_name: str | None = None
    line_id: int | None = None
    line_code: str | None = None
    name: str
    break_type: str
    start_time: time
    end_time: time
    duration_minutes: int
    active: bool


class PlannedBreakPage(BaseModel):
    items: list[PlannedBreakRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class DowntimeCreate(BaseModel):
    line_id: int = Field(gt=0)
    production_order_id: int | None = Field(default=None, gt=0)
    shift_id: int | None = Field(default=None, gt=0)
    category: str = Field(default="UNPLANNED", pattern="^(PLANNED|UNPLANNED)$")
    reason: str = Field(min_length=1, max_length=150)
    started_at: datetime
    ended_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_period(self):
        if self.ended_at is not None and self.ended_at <= self.started_at:
            raise ValueError("O fim da parada deve ser posterior ao início")
        return self


class DowntimeClose(BaseModel):
    ended_at: datetime


class DowntimeRead(BaseModel):
    id: int
    line_id: int
    line_code: str | None = None
    production_order_id: int | None
    production_order: str | None = None
    shift_id: int | None
    shift_code: str | None = None
    category: str
    reason: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: int
    notes: str | None
    created_by_username: str | None
    closed_by_username: str | None


class DowntimePage(BaseModel):
    items: list[DowntimeRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkScheduleSummary(BaseModel):
    active_shifts: int
    active_planned_breaks: int
    open_downtimes: int
