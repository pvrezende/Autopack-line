import { useEffect, useRef, useState } from 'react'
import { BrowserMultiFormatReader } from '@zxing/browser'
import { confirmPlcPalletization, controlPlcSimulator, diagnoseReaderCode, generateTestQr, getPlcCycleStatus, getPlcIntegrationStatus, getPlcModbusContract, getPlcModbusCodec, getPlcModbusHandshake, getPlcModbusSupervision, getPlcModbusReconciliation, getPlcModbusSimulator, getPlcModbusPhysical, probePlcModbusPhysicalReadOnly, getPlcAutomaticProduction, getPlcAutomaticOfflineCycle, getPlcResilienceValidation, getPlcIndustrialDiagnostics, getPlcOperationalHealth, getPlcCommissioningReadiness, getPlcCommissioningPlan, getPlcCommissioningEvidence, getPlcCommissioningRehearsal, runPlcAutomaticOfflineCycle, getPlcLatestCycle, getReaderIntegrationStatus, ingestReaderCode, listProductionOrders, tickPlcExternalSimulator } from '../services/api'
import type { PalletizeResult, PlcConfirmResponse, PlcCycleStatus, PlcIntegrationStatus, PlcModbusContract, PlcModbusCodecDiagnostic, PlcModbusHandshakeDiagnostic, PlcModbusSupervisionDiagnostic, PlcModbusReconciliationDiagnostic, PlcModbusSimulatorDiagnostic, PlcModbusPhysicalDiagnostic, PlcAutomaticProductionDiagnostic, PlcAutomaticOfflineCycleDiagnostic, PlcAutomaticOfflineCycleResponse, PlcResilienceValidationDiagnostic, PlcIndustrialDiagnostics, PlcOperationalHealthDiagnostic, PlcCommissioningReadinessDiagnostic, PlcCommissioningPlanDiagnostic, PlcCommissioningEvidenceDiagnostic, PlcCommissioningRehearsalDiagnostic, PlcExternalRuntimeResult, ProductionLine, ProductionOrder, ReaderDiagnosticResponse, ReaderIntegrationStatus, ScanSimulationResult } from '../types/domain'

const REAL_QR = ''
const PLC_CONTEXT_KEY = 'autopackline.plc-cycle-context-v1'

type Props = {
  lines: ProductionLine[]
  onChanged: () => Promise<void>
  refreshKey?: number
  view?: 'operation' | 'diagnostics'
}

type DetectedCode = { text: string; format: string }

export function OperationPanel({ lines, onChanged, refreshKey = 0, view = 'operation' }: Props) {
  const [lineId, setLineId] = useState('')
  const [rawCode, setRawCode] = useState(REAL_QR)
  const [activeOrders, setActiveOrders] = useState<ProductionOrder[]>([])
  const [selectedOrderId, setSelectedOrderId] = useState('')
  const [ordersLoading, setOrdersLoading] = useState(false)
  const [result, setResult] = useState<ScanSimulationResult | null>(null)
  const [palletResult, setPalletResult] = useState<PalletizeResult | null>(null)
  const [plcCycle, setPlcCycle] = useState<{state:string; nextAction:string; newPalletStarted:boolean} | null>(null)
  const [plcFeedback, setPlcFeedback] = useState<PlcConfirmResponse | null>(null)
  const [plcSync, setPlcSync] = useState<PlcCycleStatus | null>(null)
  const [plcSyncLoading, setPlcSyncLoading] = useState(false)
  const [plcSyncError, setPlcSyncError] = useState('')
  const [plcRestoredFromDb, setPlcRestoredFromDb] = useState(false)
  const [plcSubmitting, setPlcSubmitting] = useState(false)
  const [plcControlLoading, setPlcControlLoading] = useState(false)
  const [error, setError] = useState('')
  const [cameraOpen, setCameraOpen] = useState(false)
  const [cameraMessage, setCameraMessage] = useState('')
  const [lastDetected, setLastDetected] = useState<DetectedCode | null>(null)
  const [startingCamera, setStartingCamera] = useState(false)
  const [readerIntegration, setReaderIntegration] = useState<ReaderIntegrationStatus | null>(null)
  const [readerIntegrationError, setReaderIntegrationError] = useState('')
  const [plcIntegration, setPlcIntegration] = useState<PlcIntegrationStatus | null>(null)
  const [plcIntegrationError, setPlcIntegrationError] = useState('')
  const [externalRuntime, setExternalRuntime] = useState<PlcExternalRuntimeResult | null>(null)
  const [modbusContract, setModbusContract] = useState<PlcModbusContract | null>(null)
  const [modbusContractError, setModbusContractError] = useState('')
  const [modbusCodec, setModbusCodec] = useState<PlcModbusCodecDiagnostic | null>(null)
  const [modbusCodecError, setModbusCodecError] = useState('')
  const [modbusHandshake, setModbusHandshake] = useState<PlcModbusHandshakeDiagnostic | null>(null)
  const [modbusHandshakeError, setModbusHandshakeError] = useState('')
  const [modbusSupervision, setModbusSupervision] = useState<PlcModbusSupervisionDiagnostic | null>(null)
  const [modbusSupervisionError, setModbusSupervisionError] = useState('')
  const [modbusReconciliation, setModbusReconciliation] = useState<PlcModbusReconciliationDiagnostic | null>(null)
  const [modbusReconciliationError, setModbusReconciliationError] = useState('')
  const [modbusSimulator, setModbusSimulator] = useState<PlcModbusSimulatorDiagnostic | null>(null)
  const [modbusSimulatorError, setModbusSimulatorError] = useState('')
  const [modbusPhysical, setModbusPhysical] = useState<PlcModbusPhysicalDiagnostic | null>(null)
  const [modbusPhysicalError, setModbusPhysicalError] = useState('')
  const [modbusPhysicalLoading, setModbusPhysicalLoading] = useState(false)
  const [automaticProduction, setAutomaticProduction] = useState<PlcAutomaticProductionDiagnostic | null>(null)
  const [automaticProductionError, setAutomaticProductionError] = useState('')
  const [automaticCycle722, setAutomaticCycle722] = useState<PlcAutomaticOfflineCycleDiagnostic | null>(null)
  const [automaticCycle722Error, setAutomaticCycle722Error] = useState('')
  const [automaticCycleResult, setAutomaticCycleResult] = useState<PlcAutomaticOfflineCycleResponse | null>(null)
  const [resilience723, setResilience723] = useState<PlcResilienceValidationDiagnostic | null>(null)
  const [resilience723Error, setResilience723Error] = useState('')
  const [industrial724, setIndustrial724] = useState<PlcIndustrialDiagnostics | null>(null)
  const [industrial724Error, setIndustrial724Error] = useState('')
  const [health725, setHealth725] = useState<PlcOperationalHealthDiagnostic | null>(null)
  const [health725Error, setHealth725Error] = useState('')
  const [readiness726, setReadiness726] = useState<PlcCommissioningReadinessDiagnostic | null>(null)
  const [readiness726Error, setReadiness726Error] = useState('')
  const [commissioningPlan727, setCommissioningPlan727] = useState<PlcCommissioningPlanDiagnostic | null>(null)
  const [commissioningPlan727Error, setCommissioningPlan727Error] = useState('')
  const [commissioningEvidence728, setCommissioningEvidence728] = useState<PlcCommissioningEvidenceDiagnostic | null>(null)
  const [commissioningEvidence728Error, setCommissioningEvidence728Error] = useState('')
  const [commissioningRehearsal729, setCommissioningRehearsal729] = useState<PlcCommissioningRehearsalDiagnostic | null>(null)
  const [commissioningRehearsal729Error, setCommissioningRehearsal729Error] = useState('')
  const [hidCaptureEnabled, setHidCaptureEnabled] = useState(false)
  const [hidBuffer, setHidBuffer] = useState('')
  const [hidAutoValidate, setHidAutoValidate] = useState(true)
  const [hidMessage, setHidMessage] = useState('')
  const [pendingSource, setPendingSource] = useState<'SIMULATOR' | 'HID_USB'>('SIMULATOR')
  const [diagnostic, setDiagnostic] = useState<ReaderDiagnosticResponse | null>(null)
  const [diagnosticLoading, setDiagnosticLoading] = useState(false)
  const [testQrLoading, setTestQrLoading] = useState(false)
  const [openReaderPanel, setOpenReaderPanel] = useState<'hid' | 'diagnostic' | 'last' | 'plc' | 'contract' | 'codec' | 'handshake' | 'supervision' | 'reconciliation' | 'simulator719' | 'physical720' | 'automatic721' | 'automatic722' | 'resilience723' | 'industrial724' | 'health725' | 'readiness726' | 'commissioning727' | 'evidence728' | 'rehearsal729' | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const controlsRef = useRef<{ stop: () => void } | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const animationRef = useRef<number | null>(null)
  const readerRef = useRef(new BrowserMultiFormatReader())
  const detectorRef = useRef<any>(null)
  const detectorBusyRef = useRef(false)
  const decodedRef = useRef(false)
  const hidInputRef = useRef<HTMLInputElement | null>(null)
  const externalTickBusyRef = useRef(false)

  const liveCameraAvailable = window.isSecureContext && Boolean(navigator.mediaDevices?.getUserMedia)
  const secureScannerUrl = `https://${window.location.hostname}:5174`

  useEffect(() => () => stopCameraStream(), [])

  useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem(PLC_CONTEXT_KEY)
      if (!raw) return
      const saved = JSON.parse(raw) as { lineId?: string; selectedOrderId?: string; unitId?: number }
      if (!saved.lineId || !saved.unitId) return
      setLineId(saved.lineId)
      if (saved.selectedOrderId) setSelectedOrderId(saved.selectedOrderId)
      setOpenReaderPanel('plc')
      void refreshPlcCycle(saved.lineId, saved.unitId)
    } catch {
      window.sessionStorage.removeItem(PLC_CONTEXT_KEY)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    getReaderIntegrationStatus()
      .then((data) => { if (!cancelled) { setReaderIntegration(data); setReaderIntegrationError('') } })
      .catch((err) => { if (!cancelled) setReaderIntegrationError((err as Error).message) })
    return () => { cancelled = true }
  }, [view])

  useEffect(() => {
    if (view !== 'operation' || !lineId) { setExternalRuntime(null); return }
    let cancelled = false
    const poll = async () => {
      if (externalTickBusyRef.current) return
      externalTickBusyRef.current = true
      try {
        const data = await tickPlcExternalSimulator(Number(lineId))
        if (!cancelled) {
          setExternalRuntime(data)
          if (["COMPLETED_PLACED", "COMPLETED_REJECTED", "COMPLETED_ABORTED"].includes(data.result)) await onChanged()
        }
      } catch (err) {
        if (!cancelled) setExternalRuntime({ result: 'API_ERROR', message: (err as Error).message })
      } finally { externalTickBusyRef.current = false }
    }
    void poll()
    const timer = window.setInterval(() => { void poll() }, 250)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [view, lineId, onChanged])

  useEffect(() => {
    let cancelled = false
    getPlcIntegrationStatus()
      .then((data) => { if (!cancelled) { setPlcIntegration(data); setPlcIntegrationError('') } })
      .catch((err) => { if (!cancelled) setPlcIntegrationError((err as Error).message) })
    return () => { cancelled = true }
  }, [view])

  useEffect(() => {
    if (view !== 'diagnostics') return
    let cancelled = false
    getPlcModbusContract()
      .then((data) => { if (!cancelled) { setModbusContract(data); setModbusContractError('') } })
      .catch((err) => { if (!cancelled) setModbusContractError((err as Error).message) })
    return () => { cancelled = true }
  }, [view])

  useEffect(() => {
    if (view !== 'diagnostics') return
    let cancelled = false
    getPlcModbusCodec()
      .then((data) => { if (!cancelled) { setModbusCodec(data); setModbusCodecError('') } })
      .catch((err) => { if (!cancelled) setModbusCodecError((err as Error).message) })
    return () => { cancelled = true }
  }, [view])

  useEffect(() => {
    if (view !== 'diagnostics') return
    let cancelled = false
    getPlcModbusHandshake()
      .then((data) => { if (!cancelled) { setModbusHandshake(data); setModbusHandshakeError('') } })
      .catch((err) => { if (!cancelled) setModbusHandshakeError((err as Error).message) })
    getPlcModbusSupervision()
      .then((data) => { if (!cancelled) { setModbusSupervision(data); setModbusSupervisionError('') } })
      .catch((err) => { if (!cancelled) setModbusSupervisionError((err as Error).message) })
    getPlcModbusReconciliation()
      .then((data) => { if (!cancelled) { setModbusReconciliation(data); setModbusReconciliationError('') } })
      .catch((err) => { if (!cancelled) setModbusReconciliationError((err as Error).message) })
    getPlcModbusSimulator()
      .then((data) => { if (!cancelled) { setModbusSimulator(data); setModbusSimulatorError('') } })
      .catch((err) => { if (!cancelled) setModbusSimulatorError((err as Error).message) })
    getPlcModbusPhysical()
      .then((data) => { if (!cancelled) { setModbusPhysical(data); setModbusPhysicalError('') } })
      .catch((err) => { if (!cancelled) setModbusPhysicalError((err as Error).message) })
    getPlcAutomaticProduction()
      .then((data) => { if (!cancelled) { setAutomaticProduction(data); setAutomaticProductionError('') } })
      .catch((err) => { if (!cancelled) setAutomaticProductionError((err as Error).message) })
    getPlcAutomaticOfflineCycle()
      .then((data) => { if (!cancelled) { setAutomaticCycle722(data); setAutomaticCycle722Error('') } })
      .catch((err) => { if (!cancelled) setAutomaticCycle722Error((err as Error).message) })
    getPlcResilienceValidation()
      .then((data) => { if (!cancelled) { setResilience723(data); setResilience723Error('') } })
      .catch((err) => { if (!cancelled) setResilience723Error((err as Error).message) })
    getPlcIndustrialDiagnostics()
      .then((data) => { if (!cancelled) { setIndustrial724(data); setIndustrial724Error('') } })
      .catch((err) => { if (!cancelled) setIndustrial724Error((err as Error).message) })
    getPlcOperationalHealth()
      .then((data) => { if (!cancelled) { setHealth725(data); setHealth725Error('') } })
      .catch((err) => { if (!cancelled) setHealth725Error((err as Error).message) })
    getPlcCommissioningReadiness()
      .then((data) => { if (!cancelled) { setReadiness726(data); setReadiness726Error('') } })
      .catch((err) => { if (!cancelled) setReadiness726Error((err as Error).message) })
    getPlcCommissioningPlan()
      .then((data) => { if (!cancelled) { setCommissioningPlan727(data); setCommissioningPlan727Error('') } })
      .catch((err) => { if (!cancelled) setCommissioningPlan727Error((err as Error).message) })
    getPlcCommissioningEvidence()
      .then((data) => { if (!cancelled) { setCommissioningEvidence728(data); setCommissioningEvidence728Error('') } })
      .catch((err) => { if (!cancelled) setCommissioningEvidence728Error((err as Error).message) })
    getPlcCommissioningRehearsal()
      .then((data) => { if (!cancelled) { setCommissioningRehearsal729(data); setCommissioningRehearsal729Error('') } })
      .catch((err) => { if (!cancelled) setCommissioningRehearsal729Error((err as Error).message) })
    return () => { cancelled = true }
  }, [view])

  useEffect(() => {
    let cancelled = false
    async function loadActiveOrders() {
      if (!lineId) { setActiveOrders([]); setSelectedOrderId(''); return }
      setOrdersLoading(true)
      try {
        const data = await listProductionOrders({ page: 1, page_size: 50, status: 'ACTIVE', line_id: Number(lineId) })
        if (cancelled) return
        setActiveOrders(data.items)
        setSelectedOrderId((current) => {
          if (current && data.items.some((item) => String(item.id) === current)) return current
          return data.items.length === 1 ? String(data.items[0].id) : ''
        })
      } catch (err) {
        if (!cancelled) setError((err as Error).message)
      } finally { if (!cancelled) setOrdersLoading(false) }
    }
    void loadActiveOrders()
    return () => { cancelled = true }
  }, [lineId, refreshKey])

  // ETAPA 7.10.4 — sincronização automática da tela operacional.
  // Enquanto a tela de Operação estiver aberta, consulta periodicamente a OP ativa
  // para refletir mudanças confirmadas no MySQL (produzido, paletes etc.) sem F5.
  useEffect(() => {
    if (!lineId) return
    let cancelled = false
    let running = false

    const syncOperationState = async () => {
      if (running || cancelled) return
      running = true
      try {
        const data = await listProductionOrders({ page: 1, page_size: 50, status: 'ACTIVE', line_id: Number(lineId) })
        if (!cancelled) setActiveOrders(data.items)

        const unitId = plcSync?.production_unit_id
        if (unitId && !cancelled) {
          try {
            const cycle = await getPlcCycleStatus(Number(lineId), unitId)
            if (!cancelled) setPlcSync(cycle)
          } catch {
            // Falha transitória de atualização não deve interromper a operação.
            // O próximo ciclo de sincronização tentará novamente.
          }
        }
      } catch {
        // O status online/offline geral já é exibido no cabeçalho.
        // Mantém os últimos dados válidos e tenta novamente automaticamente.
      } finally {
        running = false
      }
    }

    void syncOperationState()
    const timer = window.setInterval(() => { void syncOperationState() }, 2000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [lineId, plcSync?.production_unit_id])

  const selectedOrder = activeOrders.find((item) => String(item.id) === selectedOrderId) ?? null

  useEffect(() => {
    let cancelled = false
    async function restoreCycleFromDatabase() {
      if (!lineId || !selectedOrderId) return
      setPlcSyncLoading(true)
      setPlcSyncError('')
      try {
        const data = await getPlcLatestCycle(Number(lineId), Number(selectedOrderId))
        if (cancelled || !data) return
        setPlcSync(data)
        setPlcRestoredFromDb(true)
        setResult(null)
        setPlcFeedback(null)
        setPalletResult(null)
        setRawCode('')
        window.sessionStorage.setItem(PLC_CONTEXT_KEY, JSON.stringify({ lineId, selectedOrderId, unitId: data.production_unit_id }))
        setOpenReaderPanel('plc')
      } catch (err) {
        if (!cancelled) setPlcSyncError((err as Error).message)
      } finally {
        if (!cancelled) setPlcSyncLoading(false)
      }
    }
    void restoreCycleFromDatabase()
    return () => { cancelled = true }
  }, [lineId, selectedOrderId])

  function codeProductionOrder(code: string) {
    const fields = code.trim().split(';')
    return fields.length >= 4 ? fields[3].trim() : ''
  }

  function stopCameraStream() {
    decodedRef.current = true
    if (animationRef.current != null) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
    controlsRef.current?.stop()
    controlsRef.current = null
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
  }

  function acceptDetectedCode(text: string, format?: string) {
    const normalized = text.trim()
    if (!normalized || decodedRef.current) return
    decodedRef.current = true
    stopCameraStream()
    setCameraOpen(false)
    setRawCode(normalized)
    setPendingSource('SIMULATOR')
    setLastDetected({ text: normalized, format: format || 'Código detectado' })
    setOpenReaderPanel('last')
    setCameraMessage(`Código detectado e preenchido automaticamente (${format || 'formato identificado'}). Confira o conteúdo e toque em “Validar leitura”.`)
    setResult(null)
    setPalletResult(null)
    setPlcFeedback(null)
    setError('')
  }

  async function createNativeDetector() {
    const BarcodeDetectorCtor = (window as any).BarcodeDetector
    if (!BarcodeDetectorCtor) return null
    try {
      const wanted = ['qr_code', 'ean_13', 'ean_8', 'code_128', 'code_39', 'codabar', 'itf', 'data_matrix', 'aztec', 'upc_a', 'upc_e']
      const supported = typeof BarcodeDetectorCtor.getSupportedFormats === 'function'
        ? await BarcodeDetectorCtor.getSupportedFormats()
        : wanted
      const formats = wanted.filter((format) => supported.includes(format))
      return new BarcodeDetectorCtor(formats.length ? { formats } : undefined)
    } catch {
      try { return new BarcodeDetectorCtor() } catch { return null }
    }
  }

  function startNativeDetectionLoop(detector: any) {
    const tick = async () => {
      if (decodedRef.current || !videoRef.current) return
      if (videoRef.current.readyState >= 2 && !detectorBusyRef.current) {
        detectorBusyRef.current = true
        try {
          const codes = await detector.detect(videoRef.current)
          if (codes?.length) {
            // Se houver mais de um código na etiqueta, prioriza QR e depois o conteúdo mais completo.
            const ordered = [...codes].sort((a: any, b: any) => {
              const aq = a.format === 'qr_code' ? 1 : 0
              const bq = b.format === 'qr_code' ? 1 : 0
              if (aq !== bq) return bq - aq
              return String(b.rawValue || '').length - String(a.rawValue || '').length
            })
            const best = ordered[0]
            if (best?.rawValue) {
              acceptDetectedCode(String(best.rawValue), String(best.format || 'Código detectado').toUpperCase())
              return
            }
          }
        } catch {
          // Um frame pode falhar por movimento/foco; o loop continua no próximo frame.
        } finally {
          detectorBusyRef.current = false
        }
      }
      if (!decodedRef.current) animationRef.current = requestAnimationFrame(tick)
    }
    animationRef.current = requestAnimationFrame(tick)
  }

  async function startZxingFallback() {
    try {
      const controls = await readerRef.current.decodeFromConstraints(
        {
          audio: false,
          video: {
            facingMode: { ideal: 'environment' },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        },
        videoRef.current!,
        (decoded) => {
          if (!decoded) return
          acceptDetectedCode(decoded.getText(), decoded.getBarcodeFormat().toString())
        },
      )
      controlsRef.current = controls
      setCameraMessage('Scanner ativo. Aponte para o QR Code ou código de barras; o conteúdo será preenchido automaticamente assim que for reconhecido.')
    } catch (err) {
      stopCameraStream()
      setCameraOpen(false)
      setCameraMessage(`Não foi possível abrir a câmera ao vivo: ${(err as Error).message}`)
    }
  }

  async function startLiveCamera() {
    setError('')
    setResult(null)
    setPalletResult(null)
    setLastDetected(null)
    setCameraMessage('')
    decodedRef.current = false

    if (!liveCameraAvailable) {
      setCameraMessage('A leitura contínua precisa de HTTPS para o navegador liberar a câmera ao vivo. Abra a versão segura do AUTOPACKLINE pelo botão abaixo.')
      return
    }

    setStartingCamera(true)
    setCameraOpen(true)
    await new Promise((resolve) => window.setTimeout(resolve, 80))

    try {
      const detector = await createNativeDetector()
      detectorRef.current = detector

      if (detector) {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            facingMode: { ideal: 'environment' },
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        })
        streamRef.current = stream
        const video = videoRef.current!
        video.srcObject = stream
        await video.play()

        const track = stream.getVideoTracks()[0]
        try {
          const capabilities = (track as any).getCapabilities?.()
          if (capabilities?.focusMode?.includes?.('continuous')) {
            await track.applyConstraints({ advanced: [{ focusMode: 'continuous' }] } as any)
          }
        } catch { /* alguns celulares não expõem controle de foco */ }

        setCameraMessage('Scanner rápido ativo. Mantenha o código dentro da moldura; ao reconhecer, o AUTOPACKLINE preenche o campo automaticamente.')
        startNativeDetectionLoop(detector)
      } else {
        await startZxingFallback()
      }
    } catch (err) {
      stopCameraStream()
      setCameraOpen(false)
      setCameraMessage(`Não foi possível abrir a câmera ao vivo: ${(err as Error).message}`)
    } finally {
      setStartingCamera(false)
    }
  }

  function stopLiveCamera() {
    stopCameraStream()
    setCameraOpen(false)
    setCameraMessage('Scanner fechado.')
  }

  async function refreshPlcCycle(lineValue: string | number, unitId: number) {
    if (!lineValue || !unitId) return
    setPlcSyncLoading(true)
    setPlcSyncError('')
    try {
      const data = await getPlcCycleStatus(Number(lineValue), unitId)
      setPlcSync(data)
      return data
    } catch (err) {
      setPlcSyncError((err as Error).message)
      return null
    } finally {
      setPlcSyncLoading(false)
    }
  }

  async function submitReaderCode(code: string, source: 'SIMULATOR' | 'HID_USB') {
    setError(''); setPalletResult(null)
    if (plcSync?.state === 'AWAITING_PLC') {
      setError(`A unidade ${plcSync.serial_number} ainda aguarda retorno do CLP. Finalize o ACK/NACK e a confirmação antes de validar uma nova unidade.`)
      setOpenReaderPanel('plc')
      return false
    }
    const normalized = code.trim()
    if (!lineId) { setError('Selecione uma linha.'); return false }
    if (!selectedOrder) { setError('Selecione uma OP ativa antes de validar a leitura.'); return false }
    if (!normalized) { setError('Leia ou informe um código antes de validar.'); return false }
    const qrOrder = codeProductionOrder(normalized)
    if (qrOrder && qrOrder !== selectedOrder.order_number) {
      setError(`O código pertence à OP ${qrOrder}, mas a operação selecionada é ${selectedOrder.order_number}.`)
      return false
    }
    if (plcSync) {
      setPlcSync(null)
      setPlcSyncError('')
      window.sessionStorage.removeItem(PLC_CONTEXT_KEY)
    }
    try {
      const integration = await ingestReaderCode({ line_id: Number(lineId), raw_code: normalized, source, code_type: 'AUTO' })
      setResult(integration.result)
      setPlcRestoredFromDb(false)
      setPlcFeedback(null)
      if (integration.result.scan.status === 'VALID' && integration.result.unit_id) {
        window.sessionStorage.setItem(PLC_CONTEXT_KEY, JSON.stringify({ lineId, selectedOrderId: String(selectedOrder.id), unitId: integration.result.unit_id }))
        await refreshPlcCycle(lineId, integration.result.unit_id)
        setOpenReaderPanel('plc')
      }
      await onChanged()
      const refreshed = await listProductionOrders({ page: 1, page_size: 50, status: 'ACTIVE', line_id: Number(lineId) })
      setActiveOrders(refreshed.items)
      return true
    } catch (err) { setError((err as Error).message); return false }
  }

  async function scan() {
    await submitReaderCode(rawCode, pendingSource)
  }

  async function diagnoseCurrentCode() {
    setDiagnosticLoading(true)
    setError('')
    try {
      const data = await diagnoseReaderCode({ raw_code: rawCode, source: pendingSource })
      setDiagnostic(data)
      setOpenReaderPanel('diagnostic')
    } catch (err) {
      setDiagnostic(null)
      setError((err as Error).message)
    } finally {
      setDiagnosticLoading(false)
    }
  }

  function activateHidCapture() {
    setOpenReaderPanel('hid')
    setHidCaptureEnabled(true)
    setHidMessage('Captura HID/USB ativa. Mantenha este campo focado e faça a leitura; leitores em modo teclado normalmente finalizam com ENTER.')
    window.setTimeout(() => hidInputRef.current?.focus(), 60)
  }

  function disableHidCapture() {
    setHidCaptureEnabled(false)
    setHidBuffer('')
    setHidMessage('Captura HID/USB pausada.')
  }

  async function acceptHidBuffer() {
    const normalized = hidBuffer.trim()
    if (!normalized) return
    setRawCode(normalized)
    setPendingSource('HID_USB')
    setLastDetected({ text: normalized, format: 'HID / USB (teclado)' })
    setResult(null)
    setPalletResult(null)
    setPlcFeedback(null)
    setError('')
    setHidBuffer('')
    setHidMessage('Código recebido pelo adaptador HID/USB e copiado para “Conteúdo capturado”.')
    if (hidAutoValidate) {
      try {
        if (!lineId || !selectedOrder) {
          setHidMessage('Código recebido, mas é necessário ter linha e OP ativa selecionadas.')
        } else {
          const qrOrder = codeProductionOrder(normalized)
          if (qrOrder && qrOrder !== selectedOrder.order_number) {
            setError(`O código pertence à OP ${qrOrder}, mas a operação selecionada é ${selectedOrder.order_number}.`)
            setHidMessage('Código recebido, porém bloqueado por divergência de OP.')
          } else {
            const auto = await runPlcAutomaticOfflineCycle({ line_id:Number(lineId), raw_code:normalized, source:'HID_USB' })
            setAutomaticCycleResult(auto)
            setHidMessage(auto.accepted ? 'Ciclo automático offline concluído sem clique do operador.' : `Ciclo automático bloqueado: ${auto.message}`)
            await onChanged()
            const refreshed = await listProductionOrders({ page:1, page_size:50, status:'ACTIVE', line_id:Number(lineId) })
            setActiveOrders(refreshed.items)
          }
        }
      } catch (err) {
        setError((err as Error).message)
        setHidMessage('Falha no ciclo automático offline; nenhuma ação manual foi assumida.')
      }
    }
    window.setTimeout(() => hidInputRef.current?.focus(), 60)
  }

  async function sendPlcSignal(signal: 'PALLETIZE_CONFIRMED' | 'PALLETIZE_REJECTED') {
    const unitId = result?.unit_id ?? plcSync?.production_unit_id
    if (!unitId || !lineId || plcSubmitting) return
    setError('')
    setPlcSubmitting(true)
    try {
      const response = await confirmPlcPalletization({
        line_id: Number(lineId),
        production_unit_id: unitId,
        source: 'SIMULATOR',
        signal,
        rejection_reason: signal === 'PALLETIZE_REJECTED' ? 'NACK simulado para teste de retorno operacional' : undefined,
      })
      setPlcFeedback(response)
      if (response.result) {
        setPalletResult(response.result)
        setPlcCycle({ state: response.cycle_state, nextAction: response.next_action, newPalletStarted: response.new_pallet_started })
        await onChanged()
        // Atualiza imediatamente e agenda novas sincronizações curtas. Isso cobre
        // qualquer pequeno atraso entre a confirmação do ciclo e a consulta agregada da OP,
        // sem exigir F5 ou clique manual em "Atualizar dados".
        const refreshOrders = async () => {
          try {
            const refreshed = await listProductionOrders({ page: 1, page_size: 50, status: 'ACTIVE', line_id: Number(lineId) })
            setActiveOrders(refreshed.items)
          } catch {
            // O polling automático continuará tentando a cada 2 s.
          }
        }
        await refreshOrders()
        window.setTimeout(() => { void refreshOrders() }, 500)
        window.setTimeout(() => { void refreshOrders() }, 1500)
      }
      const integrationStatus = await getPlcIntegrationStatus()
      setPlcIntegration(integrationStatus)
      await refreshPlcCycle(lineId, unitId)
    } catch (err) { setError((err as Error).message) }
    finally { setPlcSubmitting(false) }
  }

  async function controlSimulator(action: 'DISCONNECT' | 'RECONNECT' | 'TIMEOUT_NEXT' | 'TIMEOUT_RETRY_CYCLE' | 'RESET') {
    if (plcControlLoading) return
    setPlcControlLoading(true)
    setError('')
    setPlcFeedback(null)
    try {
      const status = await controlPlcSimulator(action)
      setPlcIntegration(status)

      // ETAPA 7.13.2 — o botão "Simular falha até esgotar retentativas"
      // representa um cenário completo, não apenas o preparo das falhas.
      // Depois de armar os timeouts, dispara imediatamente o retorno do CLP
      // para que o backend execute process_with_retry(), consuma 1/3, 2/3 e
      // 3/3 e finalize em RETRIES_EXHAUSTED sem exigir um segundo clique.
      if (action === 'TIMEOUT_RETRY_CYCLE') {
        await sendPlcSignal('PALLETIZE_CONFIRMED')
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setPlcControlLoading(false)
    }
  }

  async function probePhysicalReadOnly() {
    setModbusPhysicalLoading(true)
    setModbusPhysicalError('')
    try {
      setModbusPhysical(await probePlcModbusPhysicalReadOnly())
    } catch (err) {
      setModbusPhysicalError((err as Error).message)
    } finally {
      setModbusPhysicalLoading(false)
    }
  }

  return (
    <section className={`card-section operation-card mobile-operation-card ${view === 'diagnostics' ? 'diagnostics-card' : ''}`}>
      <div className="section-heading operation-heading">
        <div><p className="eyebrow">{view === 'diagnostics' ? 'ÁREA TÉCNICA' : 'OPERAÇÃO'}</p><h2>{view === 'diagnostics' ? 'Manutenção e Diagnóstico' : 'Produção e rastreabilidade'}</h2></div>
        <div className="operation-badges">
          <span className={`badge ${liveCameraAvailable ? 'green' : 'amber'}`}>{liveCameraAvailable ? 'scanner ao vivo disponível' : 'scanner requer HTTPS'}</span>
          <span className={`badge ${plcIntegration?.ready ? 'green' : 'amber'}`}>{plcIntegration?.communication_state === 'DISCONNECTED' ? 'CLP simulado desconectado' : plcIntegration?.timeout_next ? `${plcIntegration.timeouts_remaining || 1} falha(s) armada(s)` : plcIntegration?.hardware_connected ? 'CLP conectado' : 'CLP simulado preparado'}</span>
        </div>
      </div>

      <div className="reader-integration-card">
        <div>
          <span className="reader-integration-kicker">CAMADA DE INTEGRAÇÃO DO LEITOR</span>
          <strong>{readerIntegration?.ready ? 'Pronta para receber leituras' : 'Verificando integração...'}</strong>
          <small>{readerIntegration?.message ?? (readerIntegrationError || 'Consultando backend...')}</small>
        </div>
        <div className="reader-integration-status">
          <span className={`badge ${readerIntegration?.ready ? 'green' : 'amber'}`}>{readerIntegration?.active_adapter ?? '—'}</span>
          {readerIntegration?.prepared_adapters?.includes('HID_KEYBOARD_V1') && <span className="badge green">HID_KEYBOARD_V1 preparado</span>}
          <span className={`badge ${readerIntegration?.hardware_connected ? 'green' : 'amber'}`}>{readerIntegration?.hardware_connected ? 'hardware conectado' : 'sem leitor físico'}</span>
        </div>
      </div>

      {view === 'diagnostics' && <>
      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'contract' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'contract' ? null : 'contract')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Contrato Modbus TCP real — Delta AS228T-A</strong><small>{modbusContract?.message ?? modbusContractError ?? 'Carregando contrato técnico...'}</small></span>
        <span className="badge green">REV.02 · LADDER REV.04</span>
        <b>{openReaderPanel === 'contract' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'contract' && <div className="operation-accordion-content plc-integration-card">
        {modbusContract ? <>
          <div className="reader-diagnostic-grid">
            <div><span>CLP</span><strong>{modbusContract.plc.manufacturer} {modbusContract.plc.model}</strong></div>
            <div><span>Protocolo</span><strong>{modbusContract.plc.protocol} · porta {modbusContract.plc.tcp_port}</strong></div>
            <div><span>PC → CLP</span><strong>{modbusContract.write_range}</strong></div>
            <div><span>CLP → PC</span><strong>{modbusContract.read_range}</strong></div>
          </div>
          <div className="plc-retry-summary">
            <span><strong>IP CLP:</strong> {modbusContract.network_proposal.plc_ip}</span>
            <span><strong>IP PC:</strong> {modbusContract.network_proposal.pc_ip}</span>
            <span><strong>Polling:</strong> {modbusContract.timing.poll_interval_ms} ms</span>
            <span><strong>Heartbeat:</strong> {modbusContract.timing.heartbeat_interval_ms / 1000} s</span>
            <span><strong>ACK:</strong> {modbusContract.timing.ack_timeout_ms / 1000} s</span>
            <span><strong>Ciclo físico:</strong> {modbusContract.timing.physical_cycle_timeout_ms / 1000} s</span>
          </div>
          <div className="message warning"><strong>Comunicação física protegida.</strong> A Rev.04 está definida, mas o socket permanece desabilitado até compilação no ISPSoft e validação segura na máquina. Timeout físico não autoriza reenvio automático.</div>
          <div className="reader-diagnostic-grid">
            <div><span>Pendências automação</span><strong>{modbusContract.pending_automation.length}</strong><small>{modbusContract.pending_automation.join(', ')}</small></div>
            <div><span>Somente comissionamento</span><strong>{modbusContract.commissioning_validation.length}</strong><small>{modbusContract.commissioning_validation.join(', ')}</small></div>
          </div>
          <small>Regra de confirmação real: somente registrar PALLETIZED quando D760 = REQUEST_SEQUENCE e D761 = 1. Capacidade do palete no modo real vem do CLP/IHM em D759.</small>
        </> : <div className="message error">{modbusContractError || 'Contrato não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'codec' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'codec' ? null : 'codec')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Codec Modbus Rev.02 — UINT16 / WORD / ASCII</strong><small>{modbusCodec?.message ?? modbusCodecError ?? 'Carregando codec técnico...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'codec' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'codec' && <div className="operation-accordion-content plc-integration-card">
        {modbusCodec ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Endereçamento</span><strong>D700–D779 + D800–D879</strong><small>offset físico configurável; validação em campo pendente</small></div>
            <div><span>ASCII</span><strong>{modbusCodec.ascii.characters_per_register} caracteres / registrador</strong><small>{modbusCodec.ascii.accent_policy}</small></div>
            <div><span>Byte order</span><strong>PENDENTE AB12</strong><small>não fixado antes do comissionamento</small></div>
            <div><span>Ordem de escrita</span><strong>{modbusCodec.write_order.join(' → ')}</strong><small>payload antes do disparo</small></div>
          </div>
          <div className="message warning">
            <strong>Teste de byte order para a fábrica:</strong> AB12 · HIGH_LOW = {modbusCodec.ascii.ab12_probe.HIGH_LOW.join(', ')} · LOW_HIGH = {modbusCodec.ascii.ab12_probe.LOW_HIGH.join(', ')}. Nenhuma das duas opções foi assumida como definitiva.
          </div>
          <div className="reader-diagnostic-grid">
            <div><span>D705 · flags</span><strong>serial b0 · EAN b1 · OP b2 · modelo b3</strong></div>
            <div><span>D755 · bits</span><strong>READY/BUSY/FAULT + estado do ciclo</strong></div>
            <div><span>Resultado simulado</span><strong>{modbusCodec.sample_read_decode.result_name}</strong></div>
            <div><span>Confirmação física</span><strong>{modbusCodec.sample_read_decode.place_confirm_source_name}</strong></div>
          </div>
          <div className="plc-retry-summary">
            <span><strong>AB12 HIGH_LOW:</strong> {modbusCodec.ascii.ab12_probe.HIGH_LOW.join(' · ')}</span>
            <span><strong>AB12 LOW_HIGH:</strong> {modbusCodec.ascii.ab12_probe.LOW_HIGH.join(' · ')}</span>
            <span><strong>Offset Modbus:</strong> PENDENTE COMISSIONAMENTO</span>
          </div>
          <small>{modbusCodec.safety_notes.join(' ')}</small>
        </> : <div className="message error">{modbusCodecError || 'Codec não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'handshake' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'handshake' ? null : 'handshake')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Handshake Modbus real — máquina de estados</strong><small>{modbusHandshake?.message ?? modbusHandshakeError ?? 'Carregando máquina de estados...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'handshake' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'handshake' && <div className="operation-accordion-content plc-integration-card">
        {modbusHandshake ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Objetivo</span><strong>Operação automática</strong><small>sem operador no handshake normal</small></div>
            <div><span>Pré-condições</span><strong>READY=1 · BUSY=0 · FAULT=0</strong><small>comunicação ativa e fora de manutenção</small></div>
            <div><span>ACK</span><strong>NÃO paletiza</strong><small>D752/D753 apenas confirmam recebimento/aceite</small></div>
            <div><span>PALLETIZED</span><strong>D760 = SEQ · D761 = 1</strong><small>única condição de confirmação física</small></div>
          </div>
          <div className="message success"><strong>Fluxo automático:</strong> {modbusHandshake.write_flow.join(' → ')}</div>
          <div className="reader-diagnostic-grid">
            <div><span>BUSY=1</span><strong>bloqueia nova unidade</strong></div>
            <div><span>Retry transporte</span><strong>mesma REQUEST_SEQUENCE</strong></div>
            <div><span>Timeout físico</span><strong>sem reenvio automático</strong></div>
            <div><span>Reconexão</span><strong>reconciliar antes de escrever</strong></div>
          </div>
          <div className="plc-retry-summary">
            <span><strong>Estados modelados:</strong> {modbusHandshake.states.length}</span>
            <span><strong>Conexão física nesta etapa:</strong> NÃO</span>
            <span><strong>Meta:</strong> operação autônoma</span>
          </div>
          <small>Esta etapa formaliza decisões do fluxo real. Os botões manuais do simulador continuam somente como ferramentas de diagnóstico enquanto o adaptador físico não está comissionado.</small>
        </> : <div className="message error">{modbusHandshakeError || 'Handshake não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'supervision' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'supervision' ? null : 'supervision')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Supervisão Modbus — heartbeat / polling / comunicação</strong><small>{modbusSupervision?.message ?? modbusSupervisionError ?? 'Carregando supervisão de comunicação...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'supervision' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'supervision' && <div className="operation-accordion-content plc-integration-card">
        {modbusSupervision ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Polling CLP</span><strong>D750–D779 · {modbusSupervision.polling.interval_ms} ms</strong><small>D800–D879 condicionado ao D777</small></div>
            <div><span>Heartbeat PC</span><strong>D701 · {modbusSupervision.pc_heartbeat.interval_ms / 1000} s</strong><small>contador UINT16 incremental</small></div>
            <div><span>Heartbeat CLP</span><strong>D751 · stale em {modbusSupervision.plc_heartbeat.stale_after_ms / 1000} s</strong><small>sem alteração bloqueia produção</small></div>
            <div><span>Transporte Modbus</span><strong>{modbusSupervision.transport.retry_attempts} tentativas · timeout {modbusSupervision.transport.timeout_ms / 1000} s</strong><small>intervalo {modbusSupervision.transport.retry_interval_ms / 1000} s</small></div>
          </div>
          <div className="message success"><strong>Meta:</strong> supervisão automática 24/7, sem operador no fluxo normal. Comunicação não confiável bloqueia novas unidades.</div>
          <div className="reader-diagnostic-grid">
            <div><span>Estados modelados</span><strong>{modbusSupervision.health_states.length}</strong><small>{modbusSupervision.health_states.join(' · ')}</small></div>
            <div><span>Retry transporte</span><strong>mesma REQUEST_SEQUENCE</strong><small>não duplica unidade</small></div>
            <div><span>Reconexão</span><strong>reconciliar antes de escrever</strong><small>D752/D754/D757/D758/D760/D761</small></div>
            <div><span>Conexão física</span><strong>NÃO nesta etapa</strong><small>simulação/diagnóstico offline</small></div>
          </div>
          <div className="plc-retry-summary">
            <span><strong>Polling:</strong> 4 leituras/s</span>
            <span><strong>Heartbeat:</strong> 1 atualização/s</span>
            <span><strong>Stale:</strong> 5 s sem mudança</span>
            <span><strong>Falha segura:</strong> bloqueia nova leitura</span>
          </div>
          <small>{modbusSupervision.safe_rules.join(' ')}</small>
        </> : <div className="message error">{modbusSupervisionError || 'Supervisão não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'reconciliation' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'reconciliation' ? null : 'reconciliation')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Persistência e reconciliação — restart / idempotência</strong><small>{modbusReconciliation?.message ?? modbusReconciliationError ?? 'Carregando regras de persistência...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'reconciliation' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'reconciliation' && <div className="operation-accordion-content plc-integration-card">
        {modbusReconciliation ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Persistência</span><strong>MySQL · {modbusReconciliation.mysql_table}</strong><small>antes de qualquer escrita no CLP</small></div>
            <div><span>Identidade estável</span><strong>REQUEST_SEQUENCE</strong><small>mesma unidade nunca recebe outra sequência</small></div>
            <div><span>Restart</span><strong>reconciliar antes de escrever</strong><small>nenhum envio cego após reinicialização</small></div>
            <div><span>PALLETIZED</span><strong>D760=SEQ · D761=1</strong><small>registrar no máximo uma vez</small></div>
          </div>
          <div className="message success"><strong>Regra central:</strong> persistir a identidade/payload antes do primeiro write. Após restart ou reconexão, ler o estado do CLP e decidir sem criar uma nova REQUEST_SEQUENCE.</div>
          <div className="reader-diagnostic-grid">
            <div><span>Leitura antes de escrever</span><strong>{modbusReconciliation.reconnect_read_first.join(' / ')}</strong></div>
            <div><span>CLP ainda BUSY</span><strong>continuar aguardando</strong><small>não reenviar</small></div>
            <div><span>CLP não conhece SEQ</span><strong>reenviar mesma sequência</strong><small>mesmo payload</small></div>
            <div><span>Conflito de sequência</span><strong>bloquear automaticamente</strong><small>não adivinhar estado</small></div>
          </div>
          <div className="plc-retry-summary">
            <span><strong>Cenários testados:</strong> {modbusReconciliation.scenarios.length}</span>
            <span><strong>Persist before write:</strong> {modbusReconciliation.persist_before_write ? 'SIM' : 'NÃO'}</span>
            <span><strong>Conexão física:</strong> NÃO nesta etapa</span>
          </div>
          <small>{modbusReconciliation.idempotency_rules.join(' ')}</small>
        </> : <div className="message error">{modbusReconciliationError || 'Reconciliação não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'simulator719' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'simulator719' ? null : 'simulator719')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Simulador CLP — contrato Rev.02 completo</strong><small>{modbusSimulator?.message ?? modbusSimulatorError ?? 'Carregando simulador lógico...'}</small></span>
        <span className="badge green">SIMULADOR</span>
        <b>{openReaderPanel === 'simulator719' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'simulator719' && <div className="operation-accordion-content plc-integration-card">
        {modbusSimulator ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Mapa simulado</span><strong>{modbusSimulator.logical_register_range}</strong><small>registradores lógicos em memória</small></div>
            <div><span>Adaptador</span><strong>{modbusSimulator.adapter}</strong><small>sem socket físico</small></div>
            <div><span>ACK exemplo</span><strong>SEQ {modbusSimulator.sample_flow.after_command.ack_sequence}</strong><small>{modbusSimulator.sample_flow.after_command.result}</small></div>
            <div><span>Conclusão exemplo</span><strong>{modbusSimulator.sample_flow.after_completion.completion}</strong><small>D760={modbusSimulator.sample_flow.after_completion.completed_sequence}</small></div>
          </div>
          <div className="message success"><strong>Fluxo exercitado:</strong> COMMAND → ACK → BUSY → D760/D761, com extensão de diagnóstico D764–D779 e leitor D800–D879. A etapa permanece 100% offline.</div>
          <div className="plc-retry-summary">
            <span><strong>Socket físico:</strong> {modbusSimulator.socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</span>
            <span><strong>Capacidades:</strong> {modbusSimulator.capabilities.length}</span>
            <span><strong>Pendências fábrica:</strong> {modbusSimulator.pending_commissioning.length}</span>
            <span><strong>Pendências automação:</strong> {modbusSimulator.pending_automation.length}</span>
          </div>
          <div className="plc-control-actions">
            {plcIntegration?.communication_state === 'DISCONNECTED'
              ? <button type="button" className="secondary" disabled={plcControlLoading} onClick={() => { void controlSimulator('RECONNECT') }}>{plcControlLoading ? 'Processando...' : 'Reconectar simulador'}</button>
              : <button type="button" className="secondary" disabled={plcControlLoading || plcSubmitting} onClick={() => { void controlSimulator('DISCONNECT') }}>Simular desconexão</button>}
            <button type="button" className="secondary" disabled={plcControlLoading || plcSubmitting || plcIntegration?.communication_state === 'DISCONNECTED'} onClick={() => { void controlSimulator('TIMEOUT_NEXT') }}>Simular 1 timeout + recuperação automática</button>
            <button type="button" className="secondary" disabled={plcControlLoading || plcSubmitting || plcIntegration?.communication_state === 'DISCONNECTED'} onClick={() => { void controlSimulator('TIMEOUT_RETRY_CYCLE') }}>Simular falha até esgotar retentativas</button>
            <button type="button" className="secondary" disabled={plcControlLoading || plcSubmitting} onClick={() => { void controlSimulator('RESET') }}>Restaurar comunicação</button>
          </div>
          <small>Byte order usado no exemplo é somente de teste; AB12 e offset continuam pendentes para o comissionamento.</small>
        </> : <div className="message error">{modbusSimulatorError || 'Simulador lógico não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'physical720' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'physical720' ? null : 'physical720')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Adaptador Modbus TCP real — configuração segura</strong><small>{modbusPhysical?.message ?? modbusPhysicalError ?? 'Carregando configuração física...'}</small></span>
        <span className={`badge ${modbusPhysical?.activation_allowed ? 'green' : 'amber'}`}>{modbusPhysical?.activation_allowed ? 'LEITURA LIBERADA' : 'BLOQUEADO'}</span>
        <b>{openReaderPanel === 'physical720' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'physical720' && <div className="operation-accordion-content plc-integration-card">
        {modbusPhysical ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Adaptador real</span><strong>{modbusPhysical.adapter}</strong><small>{modbusPhysical.transport} · {modbusPhysical.role}</small></div>
            <div><span>Destino preparado</span><strong>{modbusPhysical.target.host}:{modbusPhysical.target.port}</strong><small>CLP Delta AS228T-A</small></div>
            <div><span>Mapa</span><strong>{modbusPhysical.write_range} → / ← {modbusPhysical.read_range}</strong><small>contrato lógico preservado</small></div>
            <div><span>Socket físico</span><strong>{modbusPhysical.socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>tentativa: {modbusPhysical.connection_attempted ? 'SIM' : 'NÃO'}</small></div>
          </div>
          <div className={`message ${modbusPhysical.activation_allowed ? 'success' : 'warning'}`}><strong>{modbusPhysical.activation_allowed ? 'Sondagem somente leitura disponível.' : 'Bloqueio de segurança ativo.'}</strong> {modbusPhysical.message}</div>
          <div className="plc-retry-summary">
            <span><strong>Feature flag:</strong> {modbusPhysical.physical_enabled_by_config ? 'ATIVA' : 'DESATIVADA'}</span>
            <span><strong>Ativação permitida:</strong> {modbusPhysical.activation_allowed ? 'SIM' : 'NÃO'}</span>
            <span><strong>Pendências automação:</strong> {modbusPhysical.pending_automation.length}</span>
            <span><strong>Pendências comissionamento:</strong> {modbusPhysical.pending_commissioning.length}</span>
          </div>
          <div className="plc-control-actions">
            <button type="button" className="secondary" disabled={!modbusPhysical.activation_allowed || modbusPhysicalLoading} onClick={() => { void probePhysicalReadOnly() }}>{modbusPhysicalLoading ? 'Lendo identidade...' : 'Testar identidade Rev.04 (somente leitura)'}</button>
          </div>
          {modbusPhysical.probe && <small>Resultado da sondagem: {modbusPhysical.probe} · conexão: {modbusPhysical.connected ? 'OK' : 'não estabelecida'}</small>}
          <small>Escrita preparada: {modbusPhysical.write_order.join(' → ')}. Reconexão lê primeiro {modbusPhysical.reconnect_read_first.join(' / ')}.</small>
        </> : <div className="message error">{modbusPhysicalError || 'Configuração do adaptador físico não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'automatic721' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'automatic721' ? null : 'automatic721')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Motor de produção automática — sem operador</strong><small>{automaticProduction?.message ?? automaticProductionError ?? 'Carregando motor autônomo...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'automatic721' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'automatic721' && <div className="operation-accordion-content plc-integration-card">
        {automaticProduction ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Fluxo normal</span><strong>SEM OPERADOR</strong><small>decisões automáticas do ciclo</small></div>
            <div><span>Leitor quando livre</span><strong>{automaticProduction.reader_default_target}</strong><small>aguarda próximo QR/barcode</small></div>
            <div><span>Validação</span><strong>AUTOMÁTICA</strong><small>ao receber código completo</small></div>
            <div><span>Conexão física</span><strong>NÃO</strong><small>motor exercitado offline</small></div>
          </div>
          <div className="message success"><strong>Fluxo-alvo:</strong> {automaticProduction.automatic_flow.join(' → ')}</div>
          <div className="plc-retry-summary">
            <span><strong>Estados modelados:</strong> {automaticProduction.states.length}</span>
            <span><strong>Cenários:</strong> {automaticProduction.scenarios.length}</span>
            <span><strong>Operador no fluxo normal:</strong> {automaticProduction.operator_required_normal_flow ? 'SIM' : 'NÃO'}</span>
            <span><strong>Próxima integração:</strong> 7.22</span>
          </div>
          <small>Regras-chave: uma unidade por linha; BUSY e comunicação ruim bloqueiam nova leitura; ACK não paletiza; somente D760=SEQ + D761=1 confirma produção.</small>
        </> : <div className="message error">{automaticProductionError || 'Motor automático não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'automatic722' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'automatic722' ? null : 'automatic722')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Integração automática — leitor → motor → CLP simulado</strong><small>{automaticCycle722?.message ?? automaticCycle722Error ?? 'Carregando integração automática...'}</small></span>
        <span className="badge green">OFFLINE</span>
        <b>{openReaderPanel === 'automatic722' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'automatic722' && <div className="operation-accordion-content plc-integration-card">
        {automaticCycle722 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Operador para validar</span><strong>{automaticCycle722.validation_requires_operator ? 'SIM' : 'NÃO'}</strong><small>ENTER do HID dispara o fluxo</small></div>
            <div><span>Fontes</span><strong>{automaticCycle722.reader_sources.join(' / ')}</strong></div>
            <div><span>Destino nesta etapa</span><strong>{automaticCycle722.plc_target}</strong><small>CLP real não é acessado</small></div>
            <div><span>Socket físico</span><strong>{automaticCycle722.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong></div>
          </div>
          <div className="message success"><strong>Fluxo integrado:</strong> {automaticCycle722.flow.join(' → ')}</div>
          <div className="plc-retry-summary">
            <span><strong>HID automático:</strong> ATIVO por padrão</span>
            <span><strong>Conexão física:</strong> NÃO</span>
            <span><strong>Próximo QR:</strong> liberado após resultado</span>
          </div>
          {automaticCycleResult && <div className={`message ${automaticCycleResult.accepted ? 'success' : 'warning'}`}><strong>Último ciclo automático:</strong> {automaticCycleResult.scan_status} · {automaticCycleResult.plc_confirmation_status ?? 'sem envio ao PLC'} · {automaticCycleResult.message}{automaticCycleResult.pallet_code ? ` · ${automaticCycleResult.pallet_code} ${automaticCycleResult.pallet_quantity}/${automaticCycleResult.pallet_target}` : ''}</div>}
          <small>{automaticCycle722.safety.join(' ')}</small>
        </> : <div className="message error">{automaticCycle722Error || 'Integração automática não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'resilience723' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'resilience723' ? null : 'resilience723')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Validação de resiliência — falhas / timeout / reconexão</strong><small>{resilience723?.message ?? resilience723Error ?? 'Carregando matriz de resiliência...'}</small></span>
        <span className={`badge ${resilience723?.all_passed ? 'green' : 'amber'}`}>VALIDADO OFFLINE</span>
        <b>{openReaderPanel === 'resilience723' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'resilience723' && <div className="operation-accordion-content plc-integration-card">
        {resilience723 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Cenários</span><strong>{resilience723.scenario_count}</strong><small>falhas exercitadas offline</small></div>
            <div><span>Aprovados</span><strong>{resilience723.passed_count}/{resilience723.scenario_count}</strong><small>{resilience723.all_passed ? 'matriz íntegra' : 'há cenário com atenção'}</small></div>
            <div><span>Falhas da matriz</span><strong>{resilience723.failed_count}</strong><small>resultado esperado: 0</small></div>
            <div><span>Socket físico</span><strong>{resilience723.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>continua sem CLP real</small></div>
          </div>
          <div className={`message ${resilience723.all_passed ? 'success' : 'warning'}`}><strong>Resultado:</strong> {resilience723.all_passed ? 'TODOS OS CENÁRIOS DE RESILIÊNCIA PASSARAM' : 'REVISAR CENÁRIOS COM FALHA'}</div>
          <div className="plc-retry-summary">
            {resilience723.scenarios.map((scenario) => <span key={scenario.name}><strong>{scenario.category}:</strong> {scenario.passed ? 'OK' : 'FALHOU'} · {scenario.observed_state}</span>)}
          </div>
          <small>Invariantes: {resilience723.invariants.join(' ')}</small>
        </> : <div className="message error">{resilience723Error || 'Matriz de resiliência não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'industrial724' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'industrial724' ? null : 'industrial724')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Logs, auditoria e diagnóstico industrial</strong><small>{industrial724?.message ?? industrial724Error ?? 'Carregando diagnóstico industrial...'}</small></span>
        <span className="badge green">AUDITORIA ATIVA</span>
        <b>{openReaderPanel === 'industrial724' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'industrial724' && <div className="operation-accordion-content plc-integration-card">
        {industrial724 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Catálogo monitorado</span><strong>{industrial724.catalog_size}</strong><small>eventos industriais classificados</small></div>
            <div><span>Eventos recentes</span><strong>{industrial724.recent_event_count}</strong><small>janela de diagnóstico</small></div>
            <div><span>Transações pendentes</span><strong>{industrial724.pending_transaction_count}</strong><small>exigem reconciliação/fechamento</small></div>
            <div><span>Socket físico</span><strong>{industrial724.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>diagnóstico continua offline</small></div>
          </div>
          <div className="message success"><strong>Persistência:</strong> {industrial724.persistent_store}</div>
          <div className="plc-retry-summary">
            <span><strong>INFO:</strong> {industrial724.severity_counts.INFO}</span>
            <span><strong>WARNING:</strong> {industrial724.severity_counts.WARNING}</span>
            <span><strong>ERROR:</strong> {industrial724.severity_counts.ERROR}</span>
          </div>
          {industrial724.recent_events.length > 0 ? <div className="industrial-event-list">
            {industrial724.recent_events.slice(0, 6).map((event) => <div key={event.id} className={`industrial-event-row severity-${event.severity.toLowerCase()}`}>
              <span><strong>{event.severity} · {event.category}</strong><small>{event.action}</small></span>
              <span>{event.confirmation_status || event.cycle_state || event.description}</span>
            </div>)}
          </div> : <div className="message">Nenhum evento industrial foi gravado neste banco novo ainda. Os próximos ciclos e testes alimentarão este histórico automaticamente.</div>}
          <small>{industrial724.retention_note}</small>
        </> : <div className="message error">{industrial724Error || 'Diagnóstico industrial não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'health725' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'health725' ? null : 'health725')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Health-check operacional e autodiagnóstico</strong><small>{health725?.message ?? health725Error ?? 'Carregando autodiagnóstico...'}</small></span>
        <span className={`badge ${health725?.status === 'HEALTHY_OFFLINE' ? 'green' : 'amber'}`}>SAÚDE OPERACIONAL</span>
        <b>{openReaderPanel === 'health725' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'health725' && <div className="operation-accordion-content plc-integration-card">
        {health725 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Checks</span><strong>{health725.check_count}</strong><small>componentes supervisionados</small></div>
            <div><span>Aprovados</span><strong>{health725.passed_count}/{health725.check_count}</strong><small>health-check atual</small></div>
            <div><span>Bloqueantes</span><strong>{health725.blocking_count}</strong><small>esperado: 0 no modo simulado</small></div>
            <div><span>Socket físico</span><strong>{health725.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>CLP real continua protegido</small></div>
          </div>
          <div className={`message ${health725.status === 'HEALTHY_OFFLINE' ? 'success' : 'warning'}`}><strong>Estado:</strong> {health725.status} · Nova unidade simulada: {health725.accept_new_simulated_unit ? 'LIBERADA' : 'BLOQUEADA'}</div>
          <div className="plc-retry-summary">
            <span><strong>FRONTEND:</strong> ONLINE · tela renderizada</span>
            {health725.checks.map((item) => <span key={item.name}><strong>{item.name}:</strong> {item.status}{item.blocking ? ' · BLOQUEANTE' : ''}</span>)}
          </div>
          <small>{health725.safety.join(' ')}</small>
        </> : <div className="message error">{health725Error || 'Autodiagnóstico operacional não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'readiness726' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'readiness726' ? null : 'readiness726')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Gate de prontidão pré-comissionamento</strong><small>{readiness726?.message ?? readiness726Error ?? 'Carregando gate de prontidão...'}</small></span>
        <span className={`badge ${readiness726?.offline_development_allowed ? 'green' : 'amber'}`}>PRONTIDÃO</span>
        <b>{openReaderPanel === 'readiness726' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'readiness726' && <div className="operation-accordion-content plc-integration-card">
        {readiness726 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Checklist</span><strong>{readiness726.ready_count}/{readiness726.checklist_count}</strong><small>itens seguros/prontos</small></div>
            <div><span>Bloqueios reais</span><strong>{readiness726.real_blocker_count}</strong><small>impedem comissionamento real</small></div>
            <div><span>Pendências automação</span><strong>{readiness726.pending_automation_count}</strong><small>dependem do ladder/tabelas</small></div>
            <div><span>Socket físico</span><strong>{readiness726.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>CLP real protegido</small></div>
          </div>
          <div className={`message ${readiness726.offline_development_allowed ? 'success' : 'warning'}`}><strong>Offline:</strong> {readiness726.offline_development_allowed ? 'PODE CONTINUAR' : 'ATENÇÃO'} · Comissionamento real: {readiness726.real_commissioning_allowed ? 'LIBERADO' : 'BLOQUEADO'}</div>
          <div className="plc-retry-summary">
            {readiness726.checklist.map((item) => <span key={item.code}><strong>{item.category} · {item.title}:</strong> {item.status}{item.blocking_real ? ' · BLOQUEIA REAL' : ''}</span>)}
          </div>
          <div className="message"><strong>Próximo foco offline:</strong> {readiness726.next_offline_focus}</div>
          <small><strong>Gate de fábrica:</strong> {readiness726.factory_gate}</small>
        </> : <div className="message error">{readiness726Error || 'Gate de prontidão não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'commissioning727' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'commissioning727' ? null : 'commissioning727')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Plano de comissionamento — sequência e evidências</strong><small>{commissioningPlan727?.message ?? commissioningPlan727Error ?? 'Carregando plano de comissionamento...'}</small></span>
        <span className={`badge ${commissioningPlan727?.status === 'PLAN_READY_OFFLINE' ? 'green' : 'amber'}`}>PLANO TÉCNICO</span>
        <b>{openReaderPanel === 'commissioning727' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'commissioning727' && <div className="operation-accordion-content plc-integration-card">
        {commissioningPlan727 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Plano</span><strong>{commissioningPlan727.step_count}</strong><small>passos ordenados</small></div>
            <div><span>Prontos offline</span><strong>{commissioningPlan727.ready_count}</strong><small>podem ser preparados agora</small></div>
            <div><span>Aguardando automação/fábrica</span><strong>{commissioningPlan727.wait_automation_count + commissioningPlan727.wait_factory_count}</strong><small>não executar antecipadamente</small></div>
            <div><span>Socket físico</span><strong>{commissioningPlan727.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>permanece protegido</small></div>
          </div>
          <div className={`message ${commissioningPlan727.real_release_allowed ? 'success' : 'warning'}`}><strong>Execução real:</strong> {commissioningPlan727.real_release_allowed ? 'LIBERADA PELO GATE' : 'BLOQUEADA PELO GATE'} · Plano offline: {commissioningPlan727.status === 'PLAN_READY_OFFLINE' ? 'PRONTO' : 'ATENÇÃO'}</div>
          <div className="industrial-event-list">
            {commissioningPlan727.steps.map((step) => <div key={step.code} className="industrial-event-row">
              <span><strong>{step.order}. {step.title}</strong><small>{step.phase} · {step.status}{step.requires_machine ? ' · MÁQUINA NECESSÁRIA' : ''}</small></span>
              <span>{step.evidence}</span>
            </div>)}
          </div>
          <div className="message"><strong>Regra de execução:</strong> {commissioningPlan727.execution_rule}</div>
          <small><strong>STOP:</strong> {commissioningPlan727.stop_rule}</small>
        </> : <div className="message error">{commissioningPlan727Error || 'Plano de comissionamento não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'evidence728' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'evidence728' ? null : 'evidence728')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Pacote de evidências — checklist de comissionamento</strong><small>{commissioningEvidence728?.message ?? commissioningEvidence728Error ?? 'Carregando manifesto de evidências...'}</small></span>
        <span className={`badge ${commissioningEvidence728?.status === 'EVIDENCE_PACKAGE_READY_OFFLINE' ? 'green' : 'amber'}`}>EVIDÊNCIAS</span>
        <b>{openReaderPanel === 'evidence728' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'evidence728' && <div className="operation-accordion-content plc-integration-card">
        {commissioningEvidence728 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Evidências</span><strong>{commissioningEvidence728.evidence_count}</strong><small>uma por passo da 7.27</small></div>
            <div><span>Preparadas offline</span><strong>{commissioningEvidence728.prepared_count}</strong><small>baseline/checks disponíveis</small></div>
            <div><span>Aguardando automação/fábrica</span><strong>{commissioningEvidence728.wait_automation_count + commissioningEvidence728.wait_factory_count}</strong><small>não marcar como concluídas</small></div>
            <div><span>Socket físico</span><strong>{commissioningEvidence728.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>continua protegido</small></div>
          </div>
          <div className="message success"><strong>Manifesto:</strong> PREPARADO OFFLINE · Evidência física: SOMENTE DURANTE COMISSIONAMENTO AUTORIZADO</div>
          <div className="industrial-event-list">
            {commissioningEvidence728.offline_snapshot.map((item) => <div key={item.code} className="industrial-event-row"><span><strong>{item.label}</strong><small>{item.code}</small></span><span>{item.value}</span></div>)}
          </div>
          <div className="industrial-event-list">
            {commissioningEvidence728.items.map((item) => <div key={item.code} className="industrial-event-row">
              <span><strong>{item.order}. {item.title}</strong><small>{item.phase} · {item.state}{item.requires_machine ? ' · MÁQUINA NECESSÁRIA' : ''}</small></span>
              <span>{item.expected_evidence}</span>
            </div>)}
          </div>
          <div className="message"><strong>Critério de aceite:</strong> {commissioningEvidence728.acceptance_rule}</div>
          <small><strong>Registro mínimo:</strong> {commissioningEvidence728.required_fields.join(' · ')}. {commissioningEvidence728.retention_rule}</small>
        </> : <div className="message error">{commissioningEvidence728Error || 'Pacote de evidências não disponível.'}</div>}
      </div>}

      <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'rehearsal729' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'rehearsal729' ? null : 'rehearsal729')}>
        <span className="config-hamburger">☰</span>
        <span><strong>Ensaio geral pré-comissionamento — dry-run offline</strong><small>{commissioningRehearsal729?.message ?? commissioningRehearsal729Error ?? 'Carregando ensaio geral...'}</small></span>
        <span className={`badge ${commissioningRehearsal729?.status === 'REHEARSAL_READY_OFFLINE' ? 'green' : 'amber'}`}>ENSAIO OFFLINE</span>
        <b>{openReaderPanel === 'rehearsal729' ? '−' : '+'}</b>
      </button>
      {openReaderPanel === 'rehearsal729' && <div className="operation-accordion-content plc-integration-card">
        {commissioningRehearsal729 ? <>
          <div className="reader-diagnostic-grid">
            <div><span>Checks</span><strong>{commissioningRehearsal729.check_count}</strong><small>prontidão consolidada</small></div>
            <div><span>PASS</span><strong>{commissioningRehearsal729.pass_count}</strong><small>sem falha offline</small></div>
            <div><span>FAIL</span><strong>{commissioningRehearsal729.fail_count}</strong><small>esperado: 0</small></div>
            <div><span>Socket físico</span><strong>{commissioningRehearsal729.physical_socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong><small>CLP real protegido</small></div>
          </div>
          <div className={`message ${commissioningRehearsal729.fail_count === 0 ? 'success' : 'error'}`}><strong>Resultado:</strong> {commissioningRehearsal729.status} · Execução real: {commissioningRehearsal729.real_execution_allowed ? 'LIBERADA' : 'AINDA BLOQUEADA'}</div>
          <div className="industrial-event-list">
            {commissioningRehearsal729.checks.map((item) => <div key={item.code} className="industrial-event-row"><span><strong>{item.label}</strong><small>{item.code}</small></span><span>{item.result} · {item.detail}</span></div>)}
          </div>
          <div className="plc-retry-summary">
            <span><strong>Passos do roteiro:</strong> {commissioningRehearsal729.step_count}</span>
            <span><strong>Dry-run pronto:</strong> {commissioningRehearsal729.dry_run_ready_count}</span>
            <span><strong>Aguardando automação:</strong> {commissioningRehearsal729.wait_automation_count}</span>
            <span><strong>Aguardando fábrica:</strong> {commissioningRehearsal729.wait_factory_count}</span>
          </div>
          <div className="message"><strong>Handoff de fábrica:</strong> {commissioningRehearsal729.factory_handoff}</div>
          <small><strong>STOP:</strong> {commissioningRehearsal729.stop_rule}</small>
        </> : <div className="message error">{commissioningRehearsal729Error || 'Ensaio geral não disponível.'}</div>}
      </div>}
      </>}

      {view === 'operation' && <div className="operation-grid">
        {externalRuntime && externalRuntime.result !== 'DISABLED' && <div className={`message ${['ERROR','COMMUNICATION_LOST','INTERVENTION','MACHINE_BLOCKED','RECIPE_BLOCKED','API_ERROR'].includes(externalRuntime.result) ? 'warning' : 'success'}`}>
          <strong>CLP-Simulator Modbus · {externalRuntime.result}</strong> — {externalRuntime.message}
          {externalRuntime.communication && <small> D754={externalRuntime.communication.machine_state} · palete {externalRuntime.communication.pallet_sequence} · {externalRuntime.communication.boxes_on_pallet}/{externalRuntime.communication.pallet_capacity} · heartbeat {externalRuntime.communication.plc_heartbeat}</small>}
        </div>}
        <div className="operation-inputs">
          <div className="operation-context-grid">
            <label>Linha<select value={lineId} onChange={(e) => { setLineId(e.target.value); setResult(null); setPalletResult(null); setPlcSync(null); setPlcRestoredFromDb(false); setPlcFeedback(null); window.sessionStorage.removeItem(PLC_CONTEXT_KEY); setError('') }}><option value="">Selecione a linha</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} · {line.name}</option>)}</select></label>
            <label>OP ativa<select value={selectedOrderId} disabled={!lineId || ordersLoading} onChange={(e) => { setSelectedOrderId(e.target.value); setResult(null); setPalletResult(null); setPlcSync(null); setPlcRestoredFromDb(false); setPlcFeedback(null); window.sessionStorage.removeItem(PLC_CONTEXT_KEY); setError('') }}><option value="">{ordersLoading ? 'Carregando OPs...' : activeOrders.length ? 'Selecione a OP' : 'Nenhuma OP ativa'}</option>{activeOrders.map((order) => <option key={order.id} value={order.id}>{order.order_number} · {order.product_model ?? order.product_name ?? 'Produto'}</option>)}</select></label>
          </div>

          {selectedOrder ? (
            <div className="active-order-card">
              <div><span>OP EM PRODUÇÃO</span><strong>{selectedOrder.order_number}</strong><small>{selectedOrder.line_code} · {selectedOrder.product_model ?? selectedOrder.product_name ?? 'Produto'}</small></div>
              <div className="active-order-progress"><strong>{selectedOrder.produced_quantity} / {selectedOrder.planned_quantity ?? '—'}</strong><span>produzido confirmado</span><div className="op-progress"><i style={{ width: `${selectedOrder.progress_percent}%` }} /></div><small>{selectedOrder.progress_percent}% concluído · {selectedOrder.scanned_quantity} leitura(s) válida(s) · {selectedOrder.open_pallets} palete(s) aberto(s)</small></div>
            </div>
          ) : lineId && !ordersLoading ? <div className="message warning">Não existe OP ATIVA para esta linha. Inicie uma OP em “Ordens de Produção” antes de operar.</div> : null}

          <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'hid' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'hid' ? null : 'hid')}>
            <span className="config-hamburger">☰</span>
            <span><strong>USB / HID — Leitor em modo teclado</strong><small>{hidCaptureEnabled ? 'Captura ativa · preparado para receber código + ENTER' : 'Captura pausada · abra para ativar ou testar sem leitor físico'}</small></span>
            <span className={`badge ${hidCaptureEnabled ? 'green' : 'amber'}`}>{hidCaptureEnabled ? 'ATIVO' : 'PAUSADO'}</span>
            <b>{openReaderPanel === 'hid' ? '−' : '+'}</b>
          </button>
          {openReaderPanel === 'hid' && <div className={`hid-reader-card operation-accordion-content ${hidCaptureEnabled ? 'active' : ''}`}>
            <div className="hid-reader-controls">
              <label className="hid-reader-input-label">Entrada HID / USB
                <input
                  ref={hidInputRef}
                  type="text"
                  value={hidBuffer}
                  disabled={!hidCaptureEnabled}
                  autoComplete="off"
                  placeholder={hidCaptureEnabled ? 'Aguardando leitura... (ou cole o QR e pressione Enter)' : 'Ative a captura HID/USB'}
                  onChange={(e) => setHidBuffer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      void acceptHidBuffer()
                    }
                  }}
                />
              </label>
              <div className="hid-reader-actions">
                {!hidCaptureEnabled
                  ? <button type="button" className="secondary" onClick={activateHidCapture}>Ativar captura HID/USB</button>
                  : <button type="button" className="secondary" onClick={disableHidCapture}>Pausar captura</button>}
                <label className="hid-auto-toggle"><input type="checkbox" checked={hidAutoValidate} onChange={(e) => setHidAutoValidate(e.target.checked)} /> Validar automaticamente ao receber ENTER</label>
              </div>
            </div>
            {hidMessage && <small className="hid-reader-message">{hidMessage}</small>}
          </div>}

          <label>Conteúdo capturado<textarea rows={4} value={rawCode} onChange={(e) => { setRawCode(e.target.value); setPendingSource('SIMULATOR'); setDiagnostic(null) }} /></label>

          <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'diagnostic' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'diagnostic' ? null : 'diagnostic')}>
            <span className="config-hamburger">☰</span>
            <span><strong>Diagnóstico do leitor</strong><small>{diagnostic ? (diagnostic.valid_format ? 'Formato reconhecido · diagnóstico disponível' : 'Conteúdo requer revisão') : 'Confira o conteúdo recebido sem gravar leitura no MySQL'}</small></span>
            {diagnostic && <span className={`badge ${diagnostic.valid_format ? 'green' : 'amber'}`}>{diagnostic.valid_format ? 'OK' : 'REVISAR'}</span>}
            <b>{openReaderPanel === 'diagnostic' ? '−' : '+'}</b>
          </button>
          {openReaderPanel === 'diagnostic' && <div className="operation-accordion-content reader-diagnostic-wrapper">
            <div className="reader-diagnostic-actions">
              <button type="button" className="secondary" disabled={diagnosticLoading || !rawCode.trim()} onClick={() => { void diagnoseCurrentCode() }}>
                {diagnosticLoading ? 'Analisando conteúdo...' : 'Diagnosticar conteúdo'}
              </button>
              <small>Diagnóstico não grava leitura, unidade, palete ou auditoria. Serve para conferir exatamente o que o leitor entregou.</small>
            </div>

            {diagnostic && (
              <div className={`reader-diagnostic-card ${diagnostic.valid_format ? 'valid' : 'invalid'}`}>
                <div className="reader-diagnostic-head">
                  <div><span>DIAGNÓSTICO DO LEITOR</span><strong>{diagnostic.valid_format ? 'Formato produtivo reconhecido' : 'Conteúdo recebido com formato não reconhecido'}</strong></div>
                  <span className={`badge ${diagnostic.valid_format ? 'green' : 'amber'}`}>{diagnostic.valid_format ? 'OK' : 'REVISAR'}</span>
                </div>
                <div className="reader-diagnostic-grid">
                  <div><span>Origem</span><strong>{diagnostic.source}</strong></div>
                  <div><span>Adaptador</span><strong>{diagnostic.adapter}</strong></div>
                  <div><span>Tipo detectado</span><strong>{diagnostic.detected_type}</strong></div>
                  <div><span>Campos / caracteres</span><strong>{diagnostic.field_count} / {diagnostic.length}</strong></div>
                </div>
                {diagnostic.parsed && <dl className="reader-diagnostic-parsed">
                  <div><dt>Produto bruto</dt><dd>{diagnostic.parsed.raw_product_code}</dd></div>
                  <div><dt>EAN</dt><dd>{diagnostic.parsed.ean}</dd></div>
                  <div><dt>Serial</dt><dd>{diagnostic.parsed.serial_number}</dd></div>
                  <div><dt>OP</dt><dd>{diagnostic.parsed.production_order}</dd></div>
                  <div className="full"><dt>URL</dt><dd>{diagnostic.parsed.url}</dd></div>
                </dl>}
                {diagnostic.error && <p className="reader-diagnostic-error">{diagnostic.error}</p>}
                <small>{diagnostic.message}</small>
              </div>
            )}
          </div>}

          <div className="mobile-scan-actions live-first-actions">
            <button type="button" className="scan-live-primary" disabled={startingCamera || cameraOpen} onClick={() => { void startLiveCamera() }}>
              {startingCamera ? 'Abrindo câmera...' : cameraOpen ? 'Scanner ativo...' : '▣ Iniciar scanner ao vivo'}
            </button>
            <button type="button" onClick={scan} disabled={!selectedOrder}>Validar leitura</button>
            <button className="secondary" type="button" disabled={testQrLoading || !selectedOrder} onClick={async () => {
              if (!selectedOrder) { setError('Selecione uma OP ativa antes de gerar o QR de teste.'); return }
              setTestQrLoading(true); setError('')
              try {
                const testQr = await generateTestQr(selectedOrder.id)
                setRawCode(testQr.raw_code); setPendingSource('SIMULATOR'); setLastDetected(null); setDiagnostic(null); setResult(null); setPalletResult(null)
                setCameraMessage(`QR de teste novo gerado. Serial: ${testQr.serial_number}`)
              } catch (err) { setError((err as Error).message) }
              finally { setTestQrLoading(false) }
            }}>{testQrLoading ? 'Gerando QR...' : 'Usar QR de teste'}</button>
          </div>

          {!liveCameraAvailable && (
            <div className="secure-camera-box">
              <strong>Para leitura automática no celular</strong>
              <span>Você está em <code>{window.location.protocol}//{window.location.host}</code>. A câmera contínua do navegador exige um contexto seguro (HTTPS).</span>
              <a className="button-link" href={secureScannerUrl}>Abrir AUTOPACKLINE seguro →</a>
              <small>Na primeira abertura do HTTPS, o navegador pode exibir um aviso do certificado de desenvolvimento.</small>
            </div>
          )}

          {cameraMessage && <div className="message info camera-message">{cameraMessage}</div>}
          {error && <div className="message error">{error}</div>}

          {cameraOpen && (
            <div className="camera-panel live-scanner-panel">
              <div className="camera-panel-head"><strong>Scanner automático</strong><button type="button" className="secondary small" onClick={stopLiveCamera}>Fechar</button></div>
              <div className="camera-frame"><video ref={videoRef} autoPlay muted playsInline /></div>
              <div className="scanner-instructions">Aproxime o QR/barcode até ocupar boa parte da moldura. Não tire foto. Assim que o código for reconhecido, o campo “Conteúdo capturado” será preenchido automaticamente.</div>
            </div>
          )}

          {lastDetected && <>
            <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'last' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'last' ? null : 'last')}>
              <span className="config-hamburger">☰</span>
              <span><strong>Último código detectado</strong><small>{lastDetected.format}</small></span>
              <span className="candidate-ok">✓</span>
              <b>{openReaderPanel === 'last' ? '−' : '+'}</b>
            </button>
            {openReaderPanel === 'last' && <div className="scan-candidate detected-result operation-accordion-content" role="status">
              <div className="candidate-value">{lastDetected.text}</div>
              <div className="candidate-actions">
                <button type="button" className="secondary" onClick={() => { void startLiveCamera() }}>Ler outro código</button>
              </div>
            </div>}
          </>}
        </div>

        <div className="readout">
          <h3>Resultado da leitura</h3>{selectedOrder && <div className="operation-order-mini"><span>OP selecionada</span><strong>{selectedOrder.order_number}</strong></div>}
          {!result && !plcSync && <p className="muted">Aguardando validação.</p>}
          {!result && plcSync && <div className="plc-restored-context"><strong>{plcRestoredFromDb ? 'Ciclo restaurado diretamente do MySQL' : 'Ciclo restaurado após atualização da página'}</strong><span>Serial {plcSync.serial_number} · unidade #{plcSync.production_unit_id} · {plcSync.state === 'AWAITING_PLC' ? 'aguardando retorno do CLP' : plcSync.state === 'PALLETIZED' ? 'já sincronizada/paletizada' : plcSync.state}</span></div>}
          {result && <>
            <div className={`scan-status ${result.scan.status.toLowerCase()}`}>{result.scan.status}</div>
            {result.parsed && <dl>
              <div><dt>Modelo</dt><dd>{result.parsed.model}</dd></div>
              <div><dt>EAN</dt><dd>{result.parsed.ean}</dd></div>
              <div><dt>Serial</dt><dd>{result.parsed.serial_number}</dd></div>
              <div><dt>OP</dt><dd>{result.parsed.production_order}</dd></div>
            </dl>}
            {result.scan.error_message && <p className="error-text">{result.scan.error_message}</p>}
          </>}
          {((result?.scan.status === 'VALID' && result.unit_id) || plcSync) && <>
            <button type="button" className={`config-toggle operation-accordion-toggle ${openReaderPanel === 'plc' ? 'active' : ''}`} onClick={() => setOpenReaderPanel(openReaderPanel === 'plc' ? null : 'plc')}>
              <span className="config-hamburger">☰</span>
              <span><strong>CLP / confirmação de paletização</strong><small>{plcIntegration?.message ?? plcIntegrationError ?? 'Verificando camada do CLP...'}</small></span>
              <span className={`badge ${plcIntegration?.ready ? 'green' : 'amber'}`}>{plcIntegration?.active_adapter ?? '—'}</span>
              <b>{openReaderPanel === 'plc' ? '−' : '+'}</b>
            </button>
            {openReaderPanel === 'plc' && <div className="operation-accordion-content plc-integration-card">
              <div className={`plc-sync-state ${plcSync?.state === 'AWAITING_PLC' ? 'waiting' : plcSync?.state === 'PALLETIZED' ? 'ok' : plcSync?.state === 'PLC_REJECTED' ? 'rejected' : plcSync ? 'error' : ''}`}>
                <div><span>SINCRONIZAÇÃO DO CICLO</span><strong>{plcSyncLoading ? 'Consultando MySQL...' : plcSync?.state === 'AWAITING_PLC' ? 'AGUARDANDO RETORNO DO CLP' : plcSync?.state === 'PALLETIZED' ? 'UNIDADE JÁ SINCRONIZADA' : plcSync?.state === 'PLC_REJECTED' ? 'UNIDADE REJEITADA PELO CLP' : plcSync?.state ?? '—'}</strong></div>
                {plcSync && <><small>{plcSync.message}</small><small>Serial: <strong>{plcSync.serial_number}</strong> · Estado da unidade: <strong>{plcSync.unit_status}</strong></small></>}
                {plcSyncError && <small>{plcSyncError}</small>}
              </div>
              <div className="reader-diagnostic-grid">
                <div><span>Modo</span><strong>{plcIntegration?.mode ?? '—'}</strong></div>
                <div><span>Hardware</span><strong>{plcIntegration?.hardware_connected ? 'CONECTADO' : 'NÃO CONECTADO'}</strong></div>
                <div><span>Adaptador</span><strong>{plcIntegration?.active_adapter ?? '—'}</strong></div>
                <div><span>Sinal</span><strong>PALLETIZE_CONFIRMED</strong></div>
              </div>
              <div className={`plc-communication-state ${plcIntegration?.communication_state === 'DISCONNECTED' || plcIntegration?.timeout_next ? 'warning' : 'ok'}`}>
                <div><span>COMUNICAÇÃO CLP</span><strong>{plcIntegration?.communication_state === 'DISCONNECTED' ? 'DESCONECTADO · ESTADO SEGURO' : plcIntegration?.timeout_next ? 'ONLINE · PRÓXIMO RETORNO EM TIMEOUT' : 'ONLINE'}</strong></div>
                <small>Timeout: {plcIntegration?.timeout_seconds ?? '—'} s · retentativas: {plcIntegration?.retry_max_attempts ?? '—'} · intervalo: {plcIntegration?.retry_interval_seconds ?? '—'} s. Sem ACK aceito, nenhuma unidade entra no palete.</small>
                <div className="plc-retry-summary">
                  <span><strong>Último ciclo:</strong> {plcIntegration?.last_retry_attempts ? `${plcIntegration.last_retry_attempts}/${plcIntegration.retry_max_attempts}` : '—'}</span>
                  <span><strong>Último erro:</strong> {plcIntegration?.last_retry_error ?? '—'}</span>
                  <span><strong>Estado:</strong> {plcIntegration?.last_retry_exhausted ? 'RETENTATIVAS ESGOTADAS' : 'pronto'}</span>
                </div>
              </div>
              <div className="plc-signal-actions">
                <button type="button" disabled={!plcIntegration?.ready || plcSubmitting || plcSyncLoading || plcSync?.can_confirm === false} onClick={() => { void sendPlcSignal('PALLETIZE_CONFIRMED') }}>
                  {plcSubmitting ? 'Processando retorno...' : plcSync?.state === 'PALLETIZED' ? 'Confirmação já sincronizada ✓' : 'Confirmar paletização (ACK simulado)'}
                </button>
                <button type="button" className="secondary" disabled={!plcIntegration?.ready || plcSubmitting || plcSyncLoading || plcSync?.can_reject === false} onClick={() => { void sendPlcSignal('PALLETIZE_REJECTED') }}>Simular rejeição (NACK)</button>
              </div>
              <small>ACK confirma a paletização. NACK rejeita definitivamente a unidade atual, não a grava no palete e libera a próxima leitura. Retentativas automáticas são usadas somente para timeout de comunicação.</small>
              {plcFeedback && <div className={`plc-feedback ${plcFeedback.confirmation_status === 'CONFIRMED' ? 'ok' : plcFeedback.confirmation_status === 'DUPLICATE_BLOCKED' || plcFeedback.confirmation_status === 'OUT_OF_SEQUENCE' || plcFeedback.confirmation_status === 'TIMEOUT' || plcFeedback.confirmation_status === 'COMMUNICATION_UNAVAILABLE' || plcFeedback.confirmation_status === 'RETRIES_EXHAUSTED' ? 'warning' : 'rejected'}`}>
                <strong>{plcFeedback.confirmation_status === 'CONFIRMED' ? 'ACK PROCESSADO' : plcFeedback.confirmation_status === 'DUPLICATE_BLOCKED' ? 'DUPLICIDADE BLOQUEADA' : plcFeedback.confirmation_status === 'OUT_OF_SEQUENCE' ? 'FORA DE SEQUÊNCIA' : plcFeedback.confirmation_status === 'TIMEOUT' ? 'TIMEOUT DE COMUNICAÇÃO' : plcFeedback.confirmation_status === 'COMMUNICATION_UNAVAILABLE' ? 'COMUNICAÇÃO INDISPONÍVEL' : plcFeedback.confirmation_status === 'RETRIES_EXHAUSTED' ? 'RETENTATIVAS ESGOTADAS' : 'NACK / REJEIÇÃO'}</strong>
                <span>{plcFeedback.message}</span>
                {plcFeedback.error_code && <small>Código: {plcFeedback.error_code}</small>}
                <small>Retentativas: {plcFeedback.retry_attempts}/{plcFeedback.retry_max_attempts}{plcFeedback.retry_exhausted ? ' · limite esgotado' : ''}</small>
              </div>}
            </div>}
          </>}
          {!palletResult && plcSync?.pallet && <div className="pallet-result synced"><strong>{plcSync.pallet.pallet_code}</strong><span>{plcSync.pallet.current_quantity} / {plcSync.pallet.target_quantity} caixas</span><span>Estado recuperado do MySQL · {plcSync.pallet.status === 'FULL' ? 'Palete completo' : 'Palete em montagem'}</span></div>}
          {palletResult && <div className="pallet-result"><strong>{palletResult.pallet.pallet_code}</strong><span>{palletResult.pallet.current_quantity} / {palletResult.pallet.target_quantity} caixas</span><span>{palletResult.completed_now ? 'Palete completo' : 'Palete em montagem'}</span>{plcCycle && <><span><strong>Estado do ciclo:</strong> {plcCycle.state === 'PALLET_COMPLETED' ? 'PALETE CONCLUÍDO' : plcCycle.state === 'NEW_PALLET_STARTED' ? 'NOVO PALETE INICIADO' : 'PALETE EM MONTAGEM'}</span>{plcCycle.newPalletStarted && <span><strong>Transição:</strong> novo palete criado automaticamente para esta unidade</span>}<span><strong>Próxima ação:</strong> {plcCycle.nextAction === 'INICIAR_NOVO_PALETE' ? 'próxima unidade abrirá um novo palete' : 'aguardar próxima unidade'}</span></>}</div>}
        </div>
      </div>}

      {view === 'operation' && <details className="operation-help-details">
        <summary>Como funciona a operação</summary>
        <p className="note mobile-reading-note"><strong>Fluxo operacional:</strong> selecione a linha e uma OP ATIVA. O AUTOPACKLINE bloqueia códigos de outra OP antes de enviar a leitura ao backend. <strong>USB/HID:</strong> ative a captura, mantenha o campo focado e leia o código; o ENTER final copia o conteúdo automaticamente. <strong>Leitura móvel:</strong> abra o scanner ao vivo e apenas aponte a câmera. Ao detectar um QR/barcode, o valor é colocado automaticamente em “Conteúdo capturado”; depois você decide quando tocar em “Validar leitura”.</p>
      </details>}
    </section>
  )
}
