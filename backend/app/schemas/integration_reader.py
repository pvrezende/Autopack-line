from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scan import ScanSimulationResult
from app.schemas.pallet import PalletRead


ReaderSource = Literal["SIMULATOR", "HID_USB", "PHYSICAL"]


class ReaderIntegrationStatus(BaseModel):
    mode: Literal["SIMULATOR", "PHYSICAL"]
    ready: bool
    hardware_connected: bool
    active_adapter: str
    prepared_adapters: list[str] = Field(default_factory=list)
    supported_sources: list[ReaderSource]
    supported_code_types: list[str]
    message: str


class ReaderIngestRequest(BaseModel):
    line_id: int = Field(gt=0)
    raw_code: str = Field(min_length=1, max_length=2000)
    source: ReaderSource = "SIMULATOR"
    code_type: str = Field(default="AUTO", max_length=30)


class ReaderIngestResponse(BaseModel):
    source: ReaderSource
    adapter: str
    accepted: bool
    result: ScanSimulationResult


class ReaderDiagnosticRequest(BaseModel):
    raw_code: str = Field(min_length=1, max_length=2000)
    source: ReaderSource = "SIMULATOR"


class ReaderDiagnosticResponse(BaseModel):
    source: ReaderSource
    adapter: str
    valid_format: bool
    detected_type: str
    normalized_code: str
    length: int
    field_count: int
    parsed: dict[str, str] | None = None
    error: str | None = None
    message: str


PlcSource = Literal["SIMULATOR", "PHYSICAL"]


class PlcIntegrationStatus(BaseModel):
    mode: Literal["SIMULATOR", "PHYSICAL"]
    ready: bool
    hardware_connected: bool
    active_adapter: str
    supported_sources: list[PlcSource]
    supported_signals: list[str]
    communication_state: str = "ONLINE"
    safe_state: bool = False
    timeout_next: bool = False
    timeout_seconds: int = 5
    timeouts_remaining: int = 0
    retry_max_attempts: int = 3
    retry_interval_seconds: int = 1
    last_retry_attempts: int = 0
    last_retry_error: str | None = None
    last_retry_exhausted: bool = False
    last_transition_at: str | None = None
    message: str


class PlcSimulatorControlRequest(BaseModel):
    action: Literal["DISCONNECT", "RECONNECT", "TIMEOUT_NEXT", "TIMEOUT_RETRY_CYCLE", "RESET"]


class PlcCycleStatusResponse(BaseModel):
    synchronized: bool
    state: str
    line_id: int
    production_unit_id: int
    production_order_id: int
    serial_number: str
    unit_status: str
    can_confirm: bool
    can_reject: bool
    message: str
    next_action: str
    pallet: PalletRead | None = None


class PlcConfirmRequest(BaseModel):
    line_id: int = Field(gt=0)
    production_unit_id: int = Field(gt=0)
    source: PlcSource = "SIMULATOR"
    signal: str = Field(default="PALLETIZE_CONFIRMED", max_length=60)
    rejection_reason: str | None = Field(default=None, max_length=200)


class PlcConfirmResponse(BaseModel):
    source: PlcSource
    adapter: str
    signal: str
    accepted: bool
    confirmation_status: str
    message: str
    error_code: str | None = None
    cycle_state: str
    pallet_completed: bool
    new_pallet_started: bool
    next_action: str
    result: "PalletizeResult | None" = None
    retry_attempts: int = 1
    retry_max_attempts: int = 1
    retry_exhausted: bool = False
    last_retry_error: str | None = None


from app.schemas.pallet import PalletizeResult
PlcConfirmResponse.model_rebuild()


class PlcAutomaticOfflineCycleRequest(BaseModel):
    line_id: int = Field(gt=0)
    raw_code: str = Field(min_length=1, max_length=2000)
    source: Literal["SIMULATOR", "HID_USB"] = "HID_USB"


class PlcAutomaticOfflineCycleResponse(BaseModel):
    accepted: bool
    stage: str
    message: str
    scan_status: str
    unit_id: int | None = None
    production_order_id: int | None = None
    plc_confirmation_status: str | None = None
    cycle_state: str | None = None
    next_action: str | None = None
    pallet_code: str | None = None
    pallet_quantity: int | None = None
    pallet_target: int | None = None
