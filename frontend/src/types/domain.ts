export type Product = {
  id: number
  sku: string
  ean: string | null
  model: string
  name: string
  capacity_btu: number | null
  active: boolean
}

export type ProductionLine = {
  id: number
  code: string
  name: string
  description: string | null
  active: boolean
}

export type PalletConfig = {
  id: number
  product_id: number
  line_id: number
  max_boxes: number
  active: boolean
  valid_from: string
  valid_until: string | null
}


export type ProductionTarget = {
  id: number
  line_id: number
  product_id: number | null
  hourly_target: number | null
  daily_target: number | null
  takt_seconds: number | null
  active: boolean
  valid_from: string
  valid_until: string | null
}

export type Scan = {
  id: number
  line_id: number
  production_unit_id: number | null
  raw_code: string
  code_type: string
  parsed_data: Record<string, string> | null
  serial_number: string | null
  ean: string | null
  production_order: string | null
  status: string
  error_code: string | null
  error_message: string | null
  scanned_at: string
}

export type ScanSimulationResult = {
  scan: Scan
  parsed: {
    raw_product_code: string
    model: string
    ean: string
    serial_number: string
    production_order: string
    url: string
  } | null
  unit_id: number | null
  product_id: number | null
  production_order_id: number | null
}

export type RetestAttempt = {
  id: number
  production_unit_id: number
  scan_event_id: number | null
  attempt_number: number
  decision: 'REJECTED' | 'APPROVED'
  source: 'SIMULATOR' | 'MES' | 'PLC' | 'OPERATOR'
  authorization_status: string
  reason_code: string | null
  reason_text: string | null
  idempotency_key: string
  counted_in_production: boolean
  details: Record<string, unknown> | null
  created_by_username: string | null
  created_at: string
}

export type RetestDiagnosticStatus = {
  stage: string
  real_retest_enabled: boolean
  simulator_enabled: boolean
  physical_plc_required: boolean
  mode: string
  safety_rules: string[]
  pending_definitions: string[]
  message: string
}

export type RetestSimulationResponse = {
  attempt: RetestAttempt
  replayed: boolean
  production_state_changed: boolean
  message: string
}

export type RetestUnit = {
  id: number
  serial_number: string
  unit_status: string
  product_id: number
  product_model: string
  product_name: string
  production_order_id: number
  production_order: string
  attempt_count: number
  last_decision: 'REJECTED' | 'APPROVED' | null
  created_at: string
}


export type ReaderIntegrationStatus = {
  mode: 'SIMULATOR' | 'PHYSICAL'
  ready: boolean
  hardware_connected: boolean
  active_adapter: string
  prepared_adapters: string[]
  supported_sources: Array<'SIMULATOR' | 'HID_USB' | 'PHYSICAL'>
  supported_code_types: string[]
  message: string
}

export type ReaderIngestResponse = {
  source: 'SIMULATOR' | 'HID_USB' | 'PHYSICAL'
  adapter: string
  accepted: boolean
  result: ScanSimulationResult
}

export type ReaderDiagnosticResponse = {
  source: 'SIMULATOR' | 'HID_USB' | 'PHYSICAL'
  adapter: string
  valid_format: boolean
  detected_type: string
  normalized_code: string
  length: number
  field_count: number
  parsed: { raw_product_code:string; model:string; ean:string; serial_number:string; production_order:string; url:string } | null
  error: string | null
  message: string
}


export type PlcModbusRegister = {
  address: string
  name: string
  data_type: string
  direction: 'PC_TO_PLC' | 'PLC_TO_PC'
  description: string
  status: 'DEFINED' | 'PENDING_AUTOMATION' | 'COMMISSIONING_ONLY'
}

export type PlcRev02Diagnostic = {
  stage: string
  reference: string
  status: string
  ladder: { file:string; revision:number; year:number; mmdd:number; compiled_in_ispsoft:boolean; validated_on_plc:boolean }
  connection: { host:string; port:number; unit_id:number; pc_ip:string; netmask:string; address_base:number; ascii_byte_order:string; physical_enabled:boolean; read_only_enabled:boolean; socket_opened:boolean }
  ranges: { pc_to_plc:string; plc_status:string; reader:string }
  identity_probe: Record<string, number>
  machine_states: Array<{ code:number; label:string }>
  recipes: Array<{ id:number; name:string; released:boolean }>
  reader: { architecture:string; state_codes:Record<string,string>; result_codes:Record<string,string>; feature_flags_initial_value:number; features:Record<string,boolean>; block_start:number; block_length:number; audit_source:string; sample_decode:Record<string,unknown> }
  retest: { authorized_flag:string; original_sequence:string; history_authority:string; deposited_unit_requires_rework:boolean }
  ab12: { text:string; words:string[]; confirmed_order:string }
  safety_gates: string[]
  message: string
}

export type PlcModbusContract = {
  stage: string
  status: 'PROPOSAL_NOT_IMPLEMENTED_IN_LADDER'
  plc: { manufacturer:string; model:string; role:string; protocol:string; tcp_port:number }
  network_proposal: { plc_ip:string; pc_ip:string; netmask:string; gateway:string | null; topology:string }
  timing: { poll_interval_ms:number; heartbeat_interval_ms:number; transport_timeout_ms:number; transport_retry_attempts:number; transport_retry_interval_ms:number; ack_timeout_ms:number; physical_cycle_timeout_ms:number; heartbeat_stale_ms:number; physical_cycle_timeout_allows_automatic_resend:boolean }
  write_range: string
  read_range: string
  write_registers: PlcModbusRegister[]
  read_registers: PlcModbusRegister[]
  normal_sequence: string[]
  reconnect_rules: string[]
  authority_rules: Record<string, string | boolean>
  pending_automation: string[]
  commissioning_validation: string[]
  message: string
}

export type PlcModbusCodecDiagnostic = {
  stage: string
  status: 'CODEC_READY_BYTE_ORDER_PENDING_COMMISSIONING'
  logical_addressing_only: boolean
  modbus_register_offset_applied: boolean
  ascii: {
    encoding: string
    accent_policy: string
    characters_per_register: number
    selected_byte_order: string | null
    selection_status: string
    ab12_probe: { text:string; HIGH_LOW:string[]; LOW_HIGH:string[] }
  }
  payload_flags: { serial_bit:number; ean_bit:number; op_bit:number; model_bit:number }
  sample_payload: Record<string, string | number>
  sample_write_registers_provisional_high_low: Array<{ address:string; value:number; hex:string }>
  sample_read_decode: {
    result_name:string
    machine_flags_word:number
    machine_flags: Record<string, boolean>
    completion_result_name:string
    place_confirm_source_name:string
    [key:string]: unknown
  }
  write_order: string[]
  safety_notes: string[]
  message: string
}


export type PlcModbusHandshakeDecision = {
  state: string
  may_send_new_unit: boolean
  may_write_payload: boolean
  may_trigger_command: boolean
  may_mark_palletized: boolean
  automatic_resend_allowed: boolean
  requires_intervention: boolean
  next_action: string
  reason: string
}

export type PlcModbusHandshakeDiagnostic = {
  stage: string
  status: 'HANDSHAKE_STATE_MACHINE_READY_OFFLINE'
  physical_connection_required: boolean
  automatic_operation_target: boolean
  states: string[]
  preconditions: string[]
  write_flow: string[]
  palletized_rule: string
  ack_is_not_palletized: boolean
  physical_cycle_timeout_auto_resend: boolean
  transport_retry_same_sequence: boolean
  new_unit_while_busy: boolean
  scenarios: Array<{ name:string; snapshot:Record<string, boolean | number>; decision:PlcModbusHandshakeDecision }>
  message: string
}

export type PlcModbusSupervisionDecision = {
  health: string
  may_accept_new_unit: boolean
  safe_state: boolean
  poll_due: boolean
  pc_heartbeat_due: boolean
  heartbeat_stale: boolean
  transport_retry_allowed: boolean
  transport_attempt: number
  requires_reconciliation: boolean
  next_action: string
  reason: string
}

export type PlcModbusSupervisionDiagnostic = {
  stage: string
  status: 'COMMUNICATION_SUPERVISION_READY_OFFLINE'
  physical_connection_required: boolean
  automatic_operation_target: boolean
  polling: { range:string; interval_ms:number; continuous:boolean }
  pc_heartbeat: { register:string; interval_ms:number; counter:string }
  plc_heartbeat: { register:string; expected_interval_ms:number; stale_after_ms:number; rule:string }
  transport: { timeout_ms:number; retry_attempts:number; retry_interval_ms:number; same_request_sequence:boolean }
  safe_rules: string[]
  health_states: string[]
  scenarios: Array<{ name:string; snapshot:Record<string, boolean | number | null>; decision:PlcModbusSupervisionDecision }>
  message: string
}


export type PlcModbusReconciliationDecision = {
  outcome: string
  may_write: boolean
  may_create_new_sequence: boolean
  may_mark_palletized: boolean
  same_request_sequence_required: boolean
  requires_operator: boolean
  next_action: string
  reason: string
}

export type PlcModbusReconciliationDiagnostic = {
  stage: string
  status: 'PERSISTENCE_IDEMPOTENCY_RECONCILIATION_READY_OFFLINE'
  physical_connection_required: boolean
  mysql_table: string
  persist_before_write: boolean
  stable_identity: string
  restart_rule: string
  reconnect_read_first: string[]
  idempotency_rules: string[]
  scenarios: Array<{ name:string; persisted:Record<string, string | number>; plc:Record<string, boolean | number>; decision:PlcModbusReconciliationDecision }>
  message: string
}

export type PlcModbusSimulatorDiagnostic = {
  stage: string
  status: 'FULL_REGISTER_SIMULATOR_READY_OFFLINE'
  physical_connection_required: boolean
  adapter: string
  logical_register_range: string
  socket_opened: boolean
  modbus_offset_applied: boolean
  byte_order_for_test_only: string
  capabilities: string[]
  sample_flow: {
    request_sequence: number
    after_command: { phase:string; ack_sequence:number; result:string }
    during_cycle: { phase:string; busy:boolean }
    after_completion: { phase:string; completed_sequence:number; completion:string; boxes_on_pallet:number }
  }
  pending_commissioning: string[]
  pending_automation: string[]
  message: string
}

export type PlcModbusPhysicalDiagnostic = {
  stage: string
  status: 'PHYSICAL_ADAPTER_CONFIGURED_DISABLED'
  adapter: string
  transport: string
  role: string
  target: { host:string; port:number; unit_id:number; poll_interval_ms:number; heartbeat_interval_ms:number; transport_timeout_ms:number; retry_attempts:number; retry_interval_ms:number; ack_timeout_ms:number; cycle_timeout_ms:number }
  write_range: string
  read_range: string
  write_order: string[]
  reconnect_read_first: string[]
  physical_enabled_by_config: boolean
  activation_allowed: boolean
  socket_opened: boolean
  connection_attempted: boolean
  safe_default: boolean
  pending_automation: string[]
  pending_commissioning: string[]
  activation_gates: string[]
  message: string
}


export type PlcAutomaticProductionDiagnostic = {
  stage: string
  status: 'AUTONOMOUS_PRODUCTION_ENGINE_READY_OFFLINE'
  physical_connection_required: boolean
  operator_required_normal_flow: boolean
  reader_default_target: string
  validation_mode_target: string
  automatic_flow: string[]
  safety_rules: string[]
  states: string[]
  scenarios: Array<{ name:string; snapshot:Record<string, boolean | number | null>; decision:Record<string, boolean | string> }>
  integration_next_stage: string
  message: string
}

export type PlcIntegrationStatus = {
  mode: 'SIMULATOR' | 'PHYSICAL'
  ready: boolean
  hardware_connected: boolean
  active_adapter: string
  supported_sources: Array<'SIMULATOR' | 'PHYSICAL'>
  supported_signals: string[]
  communication_state: 'ONLINE' | 'DISCONNECTED'
  safe_state: boolean
  timeout_next: boolean
  timeout_seconds: number
  timeouts_remaining: number
  retry_max_attempts: number
  retry_interval_seconds: number
  last_retry_attempts: number
  last_retry_error: string | null
  last_retry_exhausted: boolean
  last_transition_at: string | null
  message: string
}

export type PlcCycleStatus = {
  synchronized: boolean
  state: 'AWAITING_PLC' | 'PALLETIZED' | 'PLC_REJECTED' | 'CONTEXT_MISMATCH' | 'BLOCKED_UNIT_STATE'
  line_id: number
  production_unit_id: number
  production_order_id: number
  serial_number: string
  unit_status: string
  can_confirm: boolean
  can_reject: boolean
  message: string
  next_action: 'AGUARDAR_RETORNO_CLP' | 'AGUARDAR_PROXIMA_UNIDADE' | 'INICIAR_NOVO_PALETE' | 'SELECIONAR_LINHA_CORRETA' | 'REVISAR_ESTADO_UNIDADE'
  pallet: Pallet | null
}

export type PlcConfirmResponse = {
  source: 'SIMULATOR' | 'PHYSICAL'
  adapter: string
  signal: string
  accepted: boolean
  confirmation_status: 'CONFIRMED' | 'REJECTED_BY_PLC' | 'DUPLICATE_BLOCKED' | 'OUT_OF_SEQUENCE' | 'TIMEOUT' | 'COMMUNICATION_UNAVAILABLE' | 'RETRIES_EXHAUSTED'
  message: string
  error_code: string | null
  cycle_state: 'NEW_PALLET_STARTED' | 'PALLET_IN_PROGRESS' | 'PALLET_COMPLETED' | 'PLC_REJECTED' | 'DUPLICATE_BLOCKED' | 'OUT_OF_SEQUENCE' | 'COMMUNICATION_SAFE_STATE'
  pallet_completed: boolean
  new_pallet_started: boolean
  next_action: 'AGUARDAR_PROXIMA_UNIDADE' | 'INICIAR_NOVO_PALETE' | 'REVISAR_SINAL_CLP' | 'MANTER_CICLO' | 'REVISAR_SEQUENCIA' | 'AGUARDAR_COMUNICACAO_CLP'
  result: PalletizeResult | null
  retry_attempts: number
  retry_max_attempts: number
  retry_exhausted: boolean
  last_retry_error: string | null
}

export type Pallet = {
  id: number
  pallet_code: string
  line_id: number
  product_id: number
  production_order_id: number
  target_quantity: number
  current_quantity: number
  status: string
  opened_at: string
  completed_at: string | null
  closed_at: string | null
}

export type PalletizeResult = {
  pallet: Pallet
  production_unit_id: number
  sequence_number: number
  completed_now: boolean
}


export type IndicatorThreshold = {
  id: number
  line_id: number
  product_id: number | null
  availability_warning: number
  availability_critical: number
  performance_warning: number
  performance_critical: number
  quality_warning: number
  quality_critical: number
  oee_warning: number
  oee_critical: number
  active: boolean
  valid_from: string
  valid_until: string | null
}

export type DashboardIndicatorClassification = {
  metric: 'AVAILABILITY' | 'PERFORMANCE' | 'QUALITY' | 'OEE'
  value: number | null
  warning_threshold: number
  critical_threshold: number
  status: 'OK' | 'WARNING' | 'CRITICAL' | 'NO_DATA'
}

export type DashboardIndicatorAlerts = {
  status: 'OK' | 'NO_CONFIG' | 'SELECT_LINE'
  source: 'PRODUCT' | 'LINE' | null
  threshold_id: number | null
  overall_status: 'OK' | 'WARNING' | 'CRITICAL' | 'NO_DATA' | 'NO_CONFIG'
  availability?: DashboardIndicatorClassification | null
  performance?: DashboardIndicatorClassification | null
  quality?: DashboardIndicatorClassification | null
  oee?: DashboardIndicatorClassification | null
}

export type DashboardSummary = {
  total_scans: number
  valid_scans: number
  invalid_scans: number
  approval_rate: number
  open_pallets: number
  completed_pallets: number
  palletized_units: number
}

export type DashboardHourlyPoint = {
  hour: string
  quantity: number
  cumulative_quantity: number
  hourly_achievement_percent: number | null
  daily_achievement_percent: number | null
}
export type DashboardStatusPoint = { status: string; quantity: number }
export type DashboardOpenPallet = {
  id: number
  pallet_code: string
  line_id: number
  line_code: string
  product_id: number
  product_model: string
  production_order: string
  current_quantity: number
  target_quantity: number
  progress_percent: number
  opened_at: string
}
export type DashboardOccurrence = {
  id: number
  status: string
  serial_number: string | null
  line_id: number
  line_code: string
  error_message: string | null
  scanned_at: string
}
export type DashboardProductionTarget = {
  id: number
  line_id: number
  product_id: number | null
  source: 'PRODUCT' | 'LINE'
  hourly_target: number | null
  daily_target: number | null
  takt_seconds: number | null
}
export type DashboardPaceMetrics = {
  sample_count: number
  average_interval_seconds: number | null
  planned_takt_seconds: number | null
  difference_seconds: number | null
  pace_percent: number | null
  status: 'NO_DATA' | 'ON_PACE' | 'BELOW_PACE'
  first_unit_at: string | null
  last_unit_at: string | null
}

export type DashboardEfficiencyMetrics = {
  status: 'OK' | 'SELECT_LINE' | 'SELECT_PERIOD' | 'NO_SHIFT' | 'NO_SCHEDULE_IN_PERIOD'
  scope: 'LINE_PERIOD'
  shift_count: number
  gross_scheduled_minutes: number
  planned_break_minutes: number
  planned_downtime_minutes: number
  planned_production_minutes: number
  unplanned_downtime_minutes: number
  available_minutes: number
  operational_efficiency_percent: number | null
}

export type DashboardOEEMetrics = {
  status: 'OK' | 'NO_AVAILABILITY' | 'NO_TARGET' | 'NO_PRODUCTION_TIME' | 'NO_QUALITY_DATA'
  availability_percent: number | null
  performance_percent: number | null
  quality_percent: number | null
  oee_percent: number | null
  actual_units: number
  expected_units: number | null
  quality_good_count: number
  quality_total_count: number
  quality_basis: 'TRACEABILITY_VALID_SCANS'
}

export type DashboardOperational = {
  summary: DashboardSummary
  production_by_hour: DashboardHourlyPoint[]
  scan_statuses: DashboardStatusPoint[]
  open_pallets: DashboardOpenPallet[]
  recent_occurrences: DashboardOccurrence[]
  production_target: DashboardProductionTarget | null
  pace: DashboardPaceMetrics | null
  efficiency: DashboardEfficiencyMetrics | null
  oee: DashboardOEEMetrics | null
  indicator_alerts: DashboardIndicatorAlerts | null
}


export type PagedResult<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type PalletItemDetail = {
  sequence_number: number
  position: number | null
  added_at: string
  production_unit_id: number
  serial_number: string
}

export type PalletDetail = Pallet & {
  production_order: string | null
  lot_code: string | null
  product_model: string | null
  product_ean: string | null
  line_code: string | null
  items: PalletItemDetail[]
}

export type UserRole = 'OPERATOR' | 'SUPERVISOR' | 'ADMIN'
export type UserAccount = {
  id: number
  username: string
  full_name: string
  role: UserRole
  active: boolean
  last_login_at: string | null
  created_at: string
}
export type LoginResponse = {
  access_token: string
  token_type: string
  user: UserAccount
}
export type AuditLog = {
  id: number
  user_id: number | null
  username: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  created_at: string
}

export type ProductionOrderStatus = 'OPEN' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED'
export type ProductionOrder = {
  id: number
  order_number: string
  product_id: number
  product_model: string | null
  product_name: string | null
  line_id: number | null
  line_code: string | null
  line_name: string | null
  lot_code: string | null
  planned_quantity: number | null
  produced_quantity: number
  scanned_quantity: number
  progress_percent: number
  open_pallets: number
  completed_pallets: number
  status: ProductionOrderStatus
  source: string
  notes: string | null
  created_by_username: string | null
  started_by_username: string | null
  finished_by_username: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  updated_at: string
}

export type WorkShift = {
  id: number; line_id: number; line_code: string | null; code: string; name: string;
  start_time: string; end_time: string; crosses_midnight: boolean; active: boolean;
  planned_minutes: number; planned_break_minutes: number; net_planned_minutes: number;
}
export type PlannedBreak = {
  id: number; shift_id: number; shift_code: string | null; shift_name: string | null;
  line_id: number | null; line_code: string | null; name: string; break_type: 'BREAK'|'MEAL'|'SETUP'|'OTHER';
  start_time: string; end_time: string; duration_minutes: number; active: boolean;
}
export type DowntimeEvent = {
  id: number; line_id: number; line_code: string | null; production_order_id: number | null; production_order: string | null;
  shift_id: number | null; shift_code: string | null; category: 'PLANNED'|'UNPLANNED'; reason: string; status: 'OPEN'|'CLOSED';
  started_at: string; ended_at: string | null; duration_minutes: number; notes: string | null;
  created_by_username: string | null; closed_by_username: string | null;
}
export type WorkScheduleSummary = { active_shifts: number; active_planned_breaks: number; open_downtimes: number }


export type DashboardOEEHistoryPoint = {
  date: string
  availability_percent: number | null
  performance_percent: number | null
  quality_percent: number | null
  oee_percent: number | null
  palletized_units: number
  total_scans: number
  valid_scans: number
}

export type DashboardOEEHistory = {
  line_id: number
  product_id: number | null
  date_from: string
  date_to: string
  points: DashboardOEEHistoryPoint[]
}


export type DashboardLossReasonPoint = {
  label: string
  minutes: number
  occurrences: number
  percent: number
}

export type DashboardScanLossPoint = {
  label: string
  count: number
  percent: number
}

export type DashboardLossAnalysis = {
  line_id: number
  product_id: number | null
  date_from: string
  date_to: string
  planned_downtime_minutes: number
  unplanned_downtime_minutes: number
  total_downtime_minutes: number
  downtime_occurrences: number
  scan_occurrences: number
  invalid_count: number
  rejected_count: number
  duplicate_count: number
  downtime_reasons: DashboardLossReasonPoint[]
  scan_reasons: DashboardScanLossPoint[]
}


export type PlcAutomaticOfflineCycleDiagnostic = {
  stage: string
  status: 'AUTOMATIC_READER_TO_SIMULATOR_READY_OFFLINE'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  reader_sources: string[]
  validation_requires_operator: boolean
  plc_target: string
  flow: string[]
  safety: string[]
  message: string
}


export type PlcResilienceScenario = {
  name: string
  category: string
  expected_state: string
  observed_state: string
  passed: boolean
  safety_result: string
  next_action: string
}

export type PlcResilienceValidationDiagnostic = {
  stage: string
  status: 'RESILIENCE_FAILURE_MATRIX_VALIDATED_OFFLINE' | 'RESILIENCE_VALIDATION_ATTENTION'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  scenario_count: number
  passed_count: number
  failed_count: number
  all_passed: boolean
  categories: string[]
  invariants: string[]
  scenarios: PlcResilienceScenario[]
  message: string
}


export type PlcIndustrialDiagnosticEvent = {
  id: number
  created_at: string | null
  action: string
  category: string
  severity: 'INFO' | 'WARNING' | 'ERROR'
  description: string
  username: string | null
  entity_type: string | null
  entity_id: string | null
  line_id: number | null
  production_order_id: number | null
  production_unit_id: number | null
  request_sequence: number | null
  cycle_state: string | null
  confirmation_status: string | null
  error_code: string | null
  message: string | null
  details: Record<string, unknown>
}

export type PlcIndustrialPendingTransaction = {
  transaction_id: number
  line_id: number
  production_order_id: number
  production_unit_id: number
  request_sequence: number
  status: string
  reconciliation_status: string | null
  last_error: string | null
  updated_at: string | null
}

export type PlcIndustrialDiagnostics = {
  stage: string
  status: 'INDUSTRIAL_DIAGNOSTICS_READY_OFFLINE'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  persistent_store: string
  catalog_size: number
  recent_event_count: number
  pending_transaction_count: number
  severity_counts: { INFO:number; WARNING:number; ERROR:number }
  category_counts: Record<string, number>
  recent_events: PlcIndustrialDiagnosticEvent[]
  pending_transactions: PlcIndustrialPendingTransaction[]
  retention_note: string
  safety: string[]
  message: string
}

export type PlcAutomaticOfflineCycleResponse = {
  accepted: boolean
  stage: string
  message: string
  scan_status: string
  unit_id: number | null
  production_order_id: number | null
  plc_confirmation_status: string | null
  cycle_state: string | null
  next_action: string | null
  pallet_code: string | null
  pallet_quantity: number | null
  pallet_target: number | null
}


export type PlcOperationalHealthCheck = {
  name: string
  status: string
  ok: boolean
  blocking: boolean
  detail: string
}

export type PlcOperationalHealthDiagnostic = {
  stage: string
  status: 'HEALTHY_OFFLINE' | 'DEGRADED_OFFLINE'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  check_count: number
  passed_count: number
  failed_count: number
  blocking_count: number
  accept_new_simulated_unit: boolean
  real_machine_release_allowed: boolean
  checks: PlcOperationalHealthCheck[]
  safety: string[]
  message: string
}


export type PlcCommissioningReadinessItem = {
  code: string
  title: string
  category: string
  status: string
  detail: string
  blocking_real: boolean
}

export type PlcCommissioningReadinessDiagnostic = {
  stage: string
  status: 'READY_FOR_OFFLINE_CONTINUATION' | 'OFFLINE_ATTENTION'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  offline_development_allowed: boolean
  real_commissioning_allowed: boolean
  checklist_count: number
  ready_count: number
  real_blocker_count: number
  pending_automation_count: number
  pending_commissioning_count: number
  pending_automation: string[]
  pending_commissioning: string[]
  checklist: PlcCommissioningReadinessItem[]
  next_offline_focus: string
  factory_gate: string
  message: string
}


export type PlcCommissioningPlanStep = {
  code: string
  order: number
  title: string
  phase: 'OFFLINE' | 'AUTOMATION' | 'FACTORY'
  status: 'READY' | 'BLOCKED' | 'WAIT_AUTOMATION' | 'WAIT_FACTORY'
  detail: string
  evidence: string
  requires_machine: boolean
}

export type PlcCommissioningPlanDiagnostic = {
  stage: string
  status: 'PLAN_READY_OFFLINE' | 'OFFLINE_ATTENTION'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  real_release_allowed: boolean
  step_count: number
  ready_count: number
  wait_automation_count: number
  wait_factory_count: number
  blocked_count: number
  steps: PlcCommissioningPlanStep[]
  execution_rule: string
  stop_rule: string
  next_offline_focus: string
  message: string
}


export type PlcCommissioningEvidenceItem = {
  code: string
  order: number
  title: string
  phase: 'OFFLINE' | 'AUTOMATION' | 'FACTORY'
  state: 'PREPARED' | 'WAIT_AUTOMATION' | 'WAIT_FACTORY' | 'BLOCKED'
  expected_evidence: string
  capture_template: string
  requires_machine: boolean
}

export type PlcCommissioningEvidenceDiagnostic = {
  stage: string
  status: 'EVIDENCE_PACKAGE_READY_OFFLINE' | 'OFFLINE_ATTENTION'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  real_execution_allowed: boolean
  evidence_count: number
  prepared_count: number
  wait_automation_count: number
  wait_factory_count: number
  blocked_count: number
  offline_snapshot: { code:string; label:string; value:string }[]
  items: PlcCommissioningEvidenceItem[]
  required_fields: string[]
  acceptance_rule: string
  retention_rule: string
  next_offline_focus: string
  message: string
}


export type PlcCommissioningRehearsalCheck = {
  code: string
  label: string
  result: 'PASS' | 'WAIT' | 'FAIL'
  detail: string
}

export type PlcCommissioningRehearsalStep = {
  code: string
  order: number
  title: string
  phase: 'OFFLINE' | 'AUTOMATION' | 'FACTORY'
  state: 'DRY_RUN_READY' | 'WAIT_AUTOMATION' | 'WAIT_FACTORY' | 'BLOCKED'
  expected_evidence: string
  requires_machine: boolean
}

export type PlcCommissioningRehearsalDiagnostic = {
  stage: string
  status: 'REHEARSAL_READY_OFFLINE' | 'REHEARSAL_ATTENTION'
  physical_connection_required: boolean
  physical_socket_opened: boolean
  real_execution_allowed: boolean
  check_count: number
  pass_count: number
  wait_count: number
  fail_count: number
  checks: PlcCommissioningRehearsalCheck[]
  step_count: number
  dry_run_ready_count: number
  wait_automation_count: number
  wait_factory_count: number
  steps: PlcCommissioningRehearsalStep[]
  execution_sequence: string[]
  stop_rule: string
  factory_handoff: string
  message: string
}
