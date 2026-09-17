import type { DashboardLossAnalysis, DashboardOEEHistory,
  DashboardSummary,
  DashboardOperational,
  Pallet,
  PalletConfig,
  PalletizeResult,
  Product,
  ProductionLine,
  Scan,
  ScanSimulationResult,
  PagedResult,
  PalletDetail,
  UserAccount,
  LoginResponse,
  UserRole,
  AuditLog,
  ProductionOrder,
  ProductionTarget,
  IndicatorThreshold,
  WorkShift,
  PlannedBreak,
  DowntimeEvent,
  WorkScheduleSummary,
  ReaderDiagnosticResponse, ReaderIntegrationStatus, PlcConfirmResponse, PlcCycleStatus, PlcIntegrationStatus, PlcModbusContract, PlcModbusCodecDiagnostic, PlcModbusHandshakeDiagnostic, PlcModbusSupervisionDiagnostic, PlcModbusReconciliationDiagnostic, PlcModbusSimulatorDiagnostic, PlcModbusPhysicalDiagnostic, PlcAutomaticProductionDiagnostic, PlcAutomaticOfflineCycleDiagnostic, PlcAutomaticOfflineCycleResponse, PlcResilienceValidationDiagnostic, PlcIndustrialDiagnostics, PlcOperationalHealthDiagnostic, PlcCommissioningReadinessDiagnostic, PlcCommissioningPlanDiagnostic, PlcCommissioningEvidenceDiagnostic, PlcCommissioningRehearsalDiagnostic,
  ReaderIngestResponse,
  RetestAttempt, RetestDiagnosticStatus, RetestSimulationResponse, RetestUnit,
} from '../types/domain'

const API_URL = import.meta.env.VITE_API_URL || (
  window.location.protocol === 'https:'
    ? '/api/v1'
    : `http://${window.location.hostname}:8000/api/v1`
)
const TOKEN_KEY = 'autopackline_token'

export function getStoredToken() { return localStorage.getItem(TOKEN_KEY) }
export function setStoredToken(token: string) { localStorage.setItem(TOKEN_KEY, token) }
export function clearStoredToken() { localStorage.removeItem(TOKEN_KEY) }
function authHeaders(): Record<string, string> { const token = getStoredToken(); return token ? { Authorization: `Bearer ${token}` } : {} }

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers)
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  Object.entries(authHeaders()).forEach(([key, value]) => headers.set(key, value))
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/login')) { clearStoredToken(); window.dispatchEvent(new Event('autopackline:unauthorized')) }
    const body = await response.json().catch(() => ({}))
    const detail = body?.detail
    let message = `Erro HTTP ${response.status}`
    if (typeof detail === 'string') message = detail
    else if (Array.isArray(detail)) message = detail.map((item) => item?.msg ?? JSON.stringify(item)).join(' | ')
    else if (detail && typeof detail === 'object') message = detail.message ?? JSON.stringify(detail)
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export function getHealth() {
  return request<{ status: string }>('/health')
}

export function getDbHealth() {
  return request<{ status: string; database: string }>('/health/db')
}

export function listProducts() {
  return request<Product[]>('/products')
}

export function createProduct(payload: Omit<Product, 'id'>) {
  return request<Product>('/products', { method: 'POST', body: JSON.stringify(payload) })
}

export function listLines() {
  return request<ProductionLine[]>('/lines')
}

export function createLine(payload: Omit<ProductionLine, 'id'>) {
  return request<ProductionLine>('/lines', { method: 'POST', body: JSON.stringify(payload) })
}

export function listPalletConfigs() {
  return request<PalletConfig[]>('/pallet-configs')
}

export function setPalletConfig(payload: { product_id: number; line_id: number; max_boxes: number }) {
  return request<PalletConfig>('/pallet-configs', { method: 'POST', body: JSON.stringify(payload) })
}


export function listIndicatorThresholds() {
  return request<IndicatorThreshold[]>('/indicator-thresholds')
}

export function setIndicatorThreshold(payload: {
  line_id:number; product_id:number|null;
  availability_warning:number; availability_critical:number;
  performance_warning:number; performance_critical:number;
  quality_warning:number; quality_critical:number;
  oee_warning:number; oee_critical:number;
}) {
  return request<IndicatorThreshold>('/indicator-thresholds', { method:'POST', body:JSON.stringify(payload) })
}

export function listProductionTargets() {
  return request<ProductionTarget[]>('/production-targets')
}

export function setProductionTarget(payload: {
  line_id: number
  product_id: number | null
  hourly_target: number | null
  daily_target: number | null
  takt_seconds: number | null
}) {
  return request('/production-targets', { method: 'POST', body: JSON.stringify(payload) })
}

export function generateTestQr(production_order_id: number) {
  return request<{ raw_code:string; serial_number:string; production_order:string; product_model:string; ean:string }>(`/scans/test-code?production_order_id=${production_order_id}`)
}

export function simulateScan(payload: { line_id: number; raw_code: string }) {
  return request<ScanSimulationResult>('/scans/simulate', { method: 'POST', body: JSON.stringify(payload) })
}

export function getRetestStatus() {
  return request<RetestDiagnosticStatus>('/retests/status')
}

export function listRetestHistory(serial_number: string) {
  return request<RetestAttempt[]>(`/retests?${queryString({ serial_number })}`)
}

export function searchRetestUnits(query = '', limit = 20) {
  return request<RetestUnit[]>(`/retests/units?${queryString({ query, limit })}`)
}

export function simulateRetest(payload: {
  serial_number: string
  decision: 'REJECTED' | 'APPROVED'
  authorized_for_retest: boolean
  reason_code?: string
  reason_text?: string
  idempotency_key: string
}) {
  return request<RetestSimulationResponse>('/retests/simulate', { method: 'POST', body: JSON.stringify(payload) })
}

export function getReaderIntegrationStatus() {
  return request<ReaderIntegrationStatus>('/integrations/reader/status')
}

export function diagnoseReaderCode(payload: { raw_code:string; source?:'SIMULATOR'|'HID_USB'|'PHYSICAL' }) {
  return request<ReaderDiagnosticResponse>('/integrations/reader/diagnose', {
    method: 'POST',
    body: JSON.stringify({ source: 'SIMULATOR', ...payload }),
  })
}

export function ingestReaderCode(payload: { line_id:number; raw_code:string; source?:'SIMULATOR'|'HID_USB'|'PHYSICAL'; code_type?:string }) {
  return request<ReaderIngestResponse>('/integrations/reader/ingest', {
    method: 'POST',
    body: JSON.stringify({ source: 'SIMULATOR', code_type: 'AUTO', ...payload }),
  })
}

export type ScanFilters = { page?: number; page_size?: number; status?: string; line_id?: number; serial?: string; ean?: string; production_order?: string; date_from?: string; date_to?: string }
export type PalletFilters = { page?: number; page_size?: number; status?: string; line_id?: number; product_id?: number; pallet_code?: string; production_order?: string; date_from?: string; date_to?: string }

function queryString<T extends object>(values: T) {
  const params = new URLSearchParams()
  Object.entries(values as Record<string, string | number | undefined>).forEach(([key, value]) => { if (value !== undefined && value !== '') params.set(key, String(value)) })
  return params.toString()
}

export function listScans(filters: ScanFilters = {}) {
  return request<PagedResult<Scan>>(`/scans?${queryString(filters)}`)
}

export function getPlcIntegrationStatus() {
  return request<PlcIntegrationStatus>('/integrations/plc/status')
}

export function getPlcModbusContract() {
  return request<PlcModbusContract>('/integrations/plc/modbus-contract')
}

export function getPlcRev02() {
  return request<import('../types/domain').PlcRev02Diagnostic>('/integrations/plc/rev02')
}

export function getPlcModbusCodec() {
  return request<PlcModbusCodecDiagnostic>('/integrations/plc/modbus-codec')
}

export function getPlcModbusHandshake() {
  return request<PlcModbusHandshakeDiagnostic>('/integrations/plc/modbus-handshake')
}

export function getPlcModbusSupervision() {
  return request<PlcModbusSupervisionDiagnostic>('/integrations/plc/modbus-supervision')
}

export function getPlcModbusReconciliation() {
  return request<PlcModbusReconciliationDiagnostic>('/integrations/plc/modbus-reconciliation')
}

export function getPlcModbusSimulator() {
  return request<PlcModbusSimulatorDiagnostic>('/integrations/plc/modbus-simulator')
}

export function getPlcModbusPhysical() {
  return request<PlcModbusPhysicalDiagnostic>('/integrations/plc/modbus-physical')
}

export function getPlcAutomaticProduction() {
  return request<PlcAutomaticProductionDiagnostic>('/integrations/plc/automatic-production')
}

export function getPlcAutomaticOfflineCycle() {
  return request<PlcAutomaticOfflineCycleDiagnostic>('/integrations/plc/automatic-offline-cycle')
}

export function getPlcResilienceValidation() {
  return request<PlcResilienceValidationDiagnostic>('/integrations/plc/resilience-validation')
}

export function getPlcIndustrialDiagnostics() {
  return request<PlcIndustrialDiagnostics>('/integrations/plc/industrial-diagnostics')
}

export function getPlcOperationalHealth() {
  return request<PlcOperationalHealthDiagnostic>('/integrations/plc/operational-health')
}

export function getPlcCommissioningReadiness() {
  return request<PlcCommissioningReadinessDiagnostic>('/integrations/plc/commissioning-readiness')
}

export function getPlcCommissioningPlan() {
  return request<PlcCommissioningPlanDiagnostic>('/integrations/plc/commissioning-plan')
}

export function getPlcCommissioningEvidence() {
  return request<PlcCommissioningEvidenceDiagnostic>('/integrations/plc/commissioning-evidence')
}

export function getPlcCommissioningRehearsal() {
  return request<PlcCommissioningRehearsalDiagnostic>('/integrations/plc/commissioning-rehearsal')
}

export function runPlcAutomaticOfflineCycle(payload: { line_id:number; raw_code:string; source:'SIMULATOR'|'HID_USB' }) {
  return request<PlcAutomaticOfflineCycleResponse>('/integrations/plc/automatic-offline-cycle', { method:'POST', body:JSON.stringify(payload) })
}

export function controlPlcSimulator(action: 'DISCONNECT' | 'RECONNECT' | 'TIMEOUT_NEXT' | 'TIMEOUT_RETRY_CYCLE' | 'RESET') {
  return request<PlcIntegrationStatus>('/integrations/plc/simulator-control', { method: 'POST', body: JSON.stringify({ action }) })
}

export function getPlcCycleStatus(line_id:number, production_unit_id:number) {
  return request<PlcCycleStatus>(`/integrations/plc/cycle?line_id=${line_id}&production_unit_id=${production_unit_id}`)
}

export function getPlcLatestCycle(line_id:number, production_order_id:number) {
  return request<PlcCycleStatus | null>(`/integrations/plc/latest-cycle?line_id=${line_id}&production_order_id=${production_order_id}`)
}

export function confirmPlcPalletization(payload: { line_id:number; production_unit_id:number; source?:'SIMULATOR'|'PHYSICAL'; signal?:string; rejection_reason?:string }) {
  return request<PlcConfirmResponse>('/integrations/plc/confirm', {
    method: 'POST', body: JSON.stringify(payload),
  })
}

// Endpoint legado preservado para compatibilidade com telas/integrações anteriores.
export function palletize(payload: { line_id: number; production_unit_id: number }) {
  return request<PalletizeResult>('/pallets/palletize', { method: 'POST', body: JSON.stringify(payload) })
}

export function listPallets(filters: PalletFilters = {}) {
  return request<PagedResult<Pallet>>(`/pallets?${queryString(filters)}`)
}

export function getDashboardSummary() {
  return request<DashboardSummary>('/dashboard/summary')
}

export type DashboardFilters = { line_id?: number; product_id?: number; production_order?: string; date_from?: string; date_to?: string }

export function getDashboardOperational(filters: DashboardFilters = {}) {
  return request<DashboardOperational>(`/dashboard/operational?${queryString(filters)}`)
}

export function getScan(id: number) {
  return request<Scan>(`/scans/${id}`)
}

export function getPalletDetail(id: number) {
  return request<PalletDetail>(`/pallets/${id}`)
}

export async function exportScansCsv(filters: ScanFilters = {}) {
  const response = await fetch(`${API_URL}/scans/export.csv?${queryString(filters)}`, { headers: authHeaders() })
  if (!response.ok) throw new Error(`Erro HTTP ${response.status}`)
  return response.blob()
}

export async function exportPalletsCsv(filters: PalletFilters = {}) {
  const response = await fetch(`${API_URL}/pallets/export.csv?${queryString(filters)}`, { headers: authHeaders() })
  if (!response.ok) throw new Error(`Erro HTTP ${response.status}`)
  return response.blob()
}


export function login(username: string, password: string) {
  return request<LoginResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
}

export function getMe() { return request<UserAccount>('/auth/me') }

export function changePassword(current_password: string, new_password: string) {
  return request<{status: string}>('/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) })
}

export function listUsers() { return request<UserAccount[]>('/users') }

export function createUser(payload: { username: string; full_name: string; password: string; role: UserRole }) {
  return request<UserAccount>('/users', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateUser(id: number, payload: { username?: string; full_name?: string; password?: string; role?: UserRole; active?: boolean }) {
  return request<UserAccount>(`/users/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
}

export function deleteUser(id: number) {
  return request<void>(`/users/${id}`, { method: 'DELETE' })
}

export function listAuditLogs(limit = 100) { return request<AuditLog[]>(`/audit-logs?limit=${limit}`) }


export type ProductionOrderFilters = { page?: number; page_size?: number; status?: string; line_id?: number; product_id?: number; search?: string }
export function listProductionOrders(filters: ProductionOrderFilters = {}) {
  return request<PagedResult<ProductionOrder>>(`/production-orders?${queryString(filters)}`)
}
export function createProductionOrder(payload: { order_number: string; product_id: number; line_id?: number; lot_code?: string; planned_quantity?: number; notes?: string }) {
  return request<ProductionOrder>('/production-orders', { method: 'POST', body: JSON.stringify(payload) })
}
export function updateProductionOrder(id: number, payload: { product_id?: number; line_id?: number; lot_code?: string; planned_quantity?: number; notes?: string }) {
  return request<ProductionOrder>(`/production-orders/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
}
export function transitionProductionOrder(id: number, action: 'start' | 'pause' | 'finish' | 'cancel') {
  return request<ProductionOrder>(`/production-orders/${id}/${action}`, { method: 'POST' })
}



export function getOeeHistory(filters: { line_id:number; product_id?:number; date_from:string; date_to:string }) {
  return request<DashboardOEEHistory>(`/dashboard/oee-history?${queryString(filters)}`)
}


export function getLossAnalysis(filters: { line_id:number; product_id?:number; date_from:string; date_to:string }) {
  return request<DashboardLossAnalysis>(`/dashboard/loss-analysis?${queryString(filters)}`)
}

export type WorkShiftFilters = { page?: number; page_size?: number; line_id?: number; active?: boolean }
export type PlannedBreakFilters = { page?: number; page_size?: number; shift_id?: number; active?: boolean }
export type DowntimeFilters = { page?: number; page_size?: number; line_id?: number; status?: string; category?: string }

export function getWorkScheduleSummary() { return request<WorkScheduleSummary>('/work-schedules/summary') }
export function listWorkShifts(filters: WorkShiftFilters = {}) { return request<PagedResult<WorkShift>>(`/work-schedules/shifts?${queryString(filters)}`) }
export function createWorkShift(payload: { line_id:number; code:string; name:string; start_time:string; end_time:string; active?:boolean }) { return request<WorkShift>('/work-schedules/shifts', { method:'POST', body:JSON.stringify(payload) }) }
export function updateWorkShift(id:number, payload: Partial<{ code:string; name:string; start_time:string; end_time:string; active:boolean }>) { return request<WorkShift>(`/work-schedules/shifts/${id}`, { method:'PUT', body:JSON.stringify(payload) }) }
export function listPlannedBreaks(filters: PlannedBreakFilters = {}) { return request<PagedResult<PlannedBreak>>(`/work-schedules/breaks?${queryString(filters)}`) }
export function createPlannedBreak(payload: { shift_id:number; name:string; break_type:string; start_time:string; end_time:string; active?:boolean }) { return request<PlannedBreak>('/work-schedules/breaks', { method:'POST', body:JSON.stringify(payload) }) }
export function updatePlannedBreak(id:number, payload: Partial<{ name:string; break_type:string; start_time:string; end_time:string; active:boolean }>) { return request<PlannedBreak>(`/work-schedules/breaks/${id}`, { method:'PUT', body:JSON.stringify(payload) }) }
export function listDowntimes(filters: DowntimeFilters = {}) { return request<PagedResult<DowntimeEvent>>(`/work-schedules/downtimes?${queryString(filters)}`) }
export function createDowntime(payload: { line_id:number; production_order_id?:number; shift_id?:number; category:string; reason:string; started_at:string; ended_at?:string; notes?:string }) { return request<DowntimeEvent>('/work-schedules/downtimes', { method:'POST', body:JSON.stringify(payload) }) }
export function closeDowntime(id:number, ended_at:string) { return request<DowntimeEvent>(`/work-schedules/downtimes/${id}/close`, { method:'POST', body:JSON.stringify({ ended_at }) }) }
