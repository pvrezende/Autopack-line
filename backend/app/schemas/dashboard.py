from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_scans: int
    valid_scans: int
    invalid_scans: int
    approval_rate: float
    open_pallets: int
    completed_pallets: int
    palletized_units: int


class DashboardHourlyPoint(BaseModel):
    hour: str
    quantity: int
    cumulative_quantity: int = 0
    hourly_achievement_percent: float | None = None
    daily_achievement_percent: float | None = None


class DashboardStatusPoint(BaseModel):
    status: str
    quantity: int


class DashboardOpenPallet(BaseModel):
    id: int
    pallet_code: str
    line_id: int
    line_code: str
    product_id: int
    product_model: str
    production_order: str
    current_quantity: int
    target_quantity: int
    progress_percent: float
    opened_at: datetime


class DashboardOccurrence(BaseModel):
    id: int
    status: str
    serial_number: str | None
    line_id: int
    line_code: str
    error_message: str | None
    scanned_at: datetime


class DashboardProductionTarget(BaseModel):
    id: int
    line_id: int
    product_id: int | None
    source: str
    hourly_target: int | None
    daily_target: int | None
    takt_seconds: Decimal | None


class DashboardPaceMetrics(BaseModel):
    sample_count: int
    average_interval_seconds: float | None
    planned_takt_seconds: Decimal | None
    difference_seconds: float | None
    pace_percent: float | None
    status: str
    first_unit_at: datetime | None
    last_unit_at: datetime | None


class DashboardEfficiencyMetrics(BaseModel):
    status: str
    scope: str
    shift_count: int
    gross_scheduled_minutes: int
    planned_break_minutes: int
    planned_downtime_minutes: int
    planned_production_minutes: int
    unplanned_downtime_minutes: int
    available_minutes: int
    operational_efficiency_percent: float | None


class DashboardOEEMetrics(BaseModel):
    status: str
    availability_percent: float | None
    performance_percent: float | None
    quality_percent: float | None
    oee_percent: float | None
    actual_units: int
    expected_units: float | None
    quality_good_count: int
    quality_total_count: int
    quality_basis: str


class DashboardIndicatorClassification(BaseModel):
    metric: str
    value: float | None
    warning_threshold: float
    critical_threshold: float
    status: str


class DashboardIndicatorAlerts(BaseModel):
    status: str
    source: str | None
    threshold_id: int | None
    overall_status: str
    availability: DashboardIndicatorClassification | None = None
    performance: DashboardIndicatorClassification | None = None
    quality: DashboardIndicatorClassification | None = None
    oee: DashboardIndicatorClassification | None = None


class DashboardOperational(BaseModel):
    summary: DashboardSummary
    production_by_hour: list[DashboardHourlyPoint]
    scan_statuses: list[DashboardStatusPoint]
    open_pallets: list[DashboardOpenPallet]
    recent_occurrences: list[DashboardOccurrence]
    production_target: DashboardProductionTarget | None = None
    pace: DashboardPaceMetrics | None = None
    efficiency: DashboardEfficiencyMetrics | None = None
    oee: DashboardOEEMetrics | None = None
    indicator_alerts: DashboardIndicatorAlerts | None = None


class DashboardOEEHistoryPoint(BaseModel):
    date: str
    availability_percent: float | None
    performance_percent: float | None
    quality_percent: float | None
    oee_percent: float | None
    palletized_units: int
    total_scans: int
    valid_scans: int


class DashboardOEEHistory(BaseModel):
    line_id: int
    product_id: int | None
    date_from: str
    date_to: str
    points: list[DashboardOEEHistoryPoint]


class DashboardLossReasonPoint(BaseModel):
    label: str
    minutes: int
    occurrences: int
    percent: float


class DashboardScanLossPoint(BaseModel):
    label: str
    count: int
    percent: float


class DashboardLossAnalysis(BaseModel):
    line_id: int
    product_id: int | None
    date_from: str
    date_to: str
    planned_downtime_minutes: int
    unplanned_downtime_minutes: int
    total_downtime_minutes: int
    downtime_occurrences: int
    scan_occurrences: int
    invalid_count: int
    rejected_count: int
    duplicate_count: int
    downtime_reasons: list[DashboardLossReasonPoint]
    scan_reasons: list[DashboardScanLossPoint]
