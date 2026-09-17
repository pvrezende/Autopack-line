from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RetestDecision = Literal["REJECTED", "APPROVED"]
RetestSource = Literal["SIMULATOR", "MES", "PLC", "OPERATOR"]


class RetestAttemptRead(BaseModel):
    id: int
    production_unit_id: int
    scan_event_id: int | None
    attempt_number: int
    decision: str
    source: str
    authorization_status: str
    reason_code: str | None
    reason_text: str | None
    idempotency_key: str
    counted_in_production: bool
    details: dict | None
    created_by_username: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RetestSimulationRequest(BaseModel):
    serial_number: str = Field(min_length=1, max_length=100)
    decision: RetestDecision
    authorized_for_retest: bool = False
    reason_code: str | None = Field(default=None, max_length=80)
    reason_text: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=4, max_length=120)


class RetestSimulationResponse(BaseModel):
    attempt: RetestAttemptRead
    replayed: bool
    production_state_changed: bool = False
    message: str


class RetestDiagnosticStatus(BaseModel):
    stage: str
    real_retest_enabled: bool
    simulator_enabled: bool
    physical_plc_required: bool
    mode: str
    safety_rules: list[str]
    pending_definitions: list[str]
    message: str


class RetestUnitRead(BaseModel):
    id: int
    serial_number: str
    unit_status: str
    product_id: int
    product_model: str
    product_name: str
    production_order_id: int
    production_order: str
    attempt_count: int
    last_decision: str | None = None
    created_at: datetime
