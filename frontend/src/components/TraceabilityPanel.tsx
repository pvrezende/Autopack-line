import { useCallback, useEffect, useMemo, useState } from 'react'
import { exportPalletsCsv, exportScansCsv, getPalletDetail, getScan, listPallets, listScans, type PalletFilters, type ScanFilters } from '../services/api'
import type { PagedResult, Pallet, PalletDetail, Product, ProductionLine, Scan } from '../types/domain'
import { formatLocalDateTime } from '../utils/dateTime'
import { periodLabel, periodRange, type PeriodFilter } from '../utils/dateRange'

export type TraceabilityPreset = { period?: PeriodFilter; from?: string; to?: string; line_id?: string; status?: string; serial?: string; ean?: string; production_order?: string }
type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number; preset?: TraceabilityPreset | null; presetKey?: number }
type Period = PeriodFilter

const emptyScans: PagedResult<Scan> = { items: [], total: 0, page: 1, page_size: 20, total_pages: 1 }
const emptyPallets: PagedResult<Pallet> = { items: [], total: 0, page: 1, page_size: 20, total_pages: 1 }

function formatDate(value: string) {
  return formatLocalDateTime(value)
}

function Pager({ page, totalPages, total, pageSize, onPage }: { page: number; totalPages: number; total: number; pageSize: number; onPage: (page: number) => void }) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)
  return <div className="pager"><span>Mostrando {start}–{end} de {total}</span><div><button className="secondary small" disabled={page <= 1} onClick={() => onPage(page - 1)}>Anterior</button><span>Página {page} de {totalPages}</span><button className="secondary small" disabled={page >= totalPages} onClick={() => onPage(page + 1)}>Próxima</button></div></div>
}

export function TraceabilityPanel({ products, lines, refreshKey, preset, presetKey = 0 }: Props) {
  const [scanData, setScanData] = useState(emptyScans)
  const [palletData, setPalletData] = useState(emptyPallets)
  const [loadingScans, setLoadingScans] = useState(false)
  const [loadingPallets, setLoadingPallets] = useState(false)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState<{ kind: 'scan'; data: Scan } | { kind: 'pallet'; data: PalletDetail } | null>(null)
  const [traceSection, setTraceSection] = useState<'scans' | 'pallets'>('scans')
  const [periodReport, setPeriodReport] = useState<{ kind: 'scan'; items: Scan[]; title: string } | { kind: 'pallet'; items: Pallet[]; title: string } | null>(null)

  const [scanDraft, setScanDraft] = useState({ period: 'today' as Period, from: '', to: '', line_id: '', status: '', serial: '', ean: '', production_order: '', page_size: '8' })
  const [scanFilters, setScanFilters] = useState(scanDraft)
  const [scanPage, setScanPage] = useState(1)

  const [palletDraft, setPalletDraft] = useState({ period: 'today' as Period, from: '', to: '', line_id: '', product_id: '', status: '', pallet_code: '', production_order: '', page_size: '8' })
  const [palletFilters, setPalletFilters] = useState(palletDraft)
  const [palletPage, setPalletPage] = useState(1)

  useEffect(() => {
    if (!preset || presetKey === 0) return
    const next = {
      period: (preset.period ?? 'today') as Period,
      from: preset.from ?? '',
      to: preset.to ?? '',
      line_id: preset.line_id ?? '',
      status: preset.status ?? '',
      serial: preset.serial ?? '',
      ean: preset.ean ?? '',
      production_order: preset.production_order ?? '',
      page_size: '8',
    }
    setTraceSection('scans')
    setScanDraft(next)
    setScanFilters(next)
    setScanPage(1)
  }, [preset, presetKey])

  const scanQuery = useMemo<ScanFilters>(() => ({
    page: scanPage,
    page_size: Number(scanFilters.page_size),
    status: scanFilters.status || undefined,
    line_id: scanFilters.line_id ? Number(scanFilters.line_id) : undefined,
    serial: scanFilters.serial.trim() || undefined,
    ean: scanFilters.ean.trim() || undefined,
    production_order: scanFilters.production_order.trim() || undefined,
    ...periodRange(scanFilters.period, scanFilters.from, scanFilters.to),
  }), [scanFilters, scanPage])

  const palletQuery = useMemo<PalletFilters>(() => ({
    page: palletPage,
    page_size: Number(palletFilters.page_size),
    status: palletFilters.status || undefined,
    line_id: palletFilters.line_id ? Number(palletFilters.line_id) : undefined,
    product_id: palletFilters.product_id ? Number(palletFilters.product_id) : undefined,
    pallet_code: palletFilters.pallet_code.trim() || undefined,
    production_order: palletFilters.production_order.trim() || undefined,
    ...periodRange(palletFilters.period, palletFilters.from, palletFilters.to),
  }), [palletFilters, palletPage])

  const loadScans = useCallback(async () => {
    setLoadingScans(true)
    try { setScanData(await listScans(scanQuery)); setError('') } catch (err) { setError((err as Error).message) } finally { setLoadingScans(false) }
  }, [scanQuery])

  const loadPallets = useCallback(async () => {
    setLoadingPallets(true)
    try { setPalletData(await listPallets(palletQuery)); setError('') } catch (err) { setError((err as Error).message) } finally { setLoadingPallets(false) }
  }, [palletQuery])

  useEffect(() => { loadScans() }, [loadScans, refreshKey])
  useEffect(() => { loadPallets() }, [loadPallets, refreshKey])

  function applyScanFilters() { setScanPage(1); setScanFilters({ ...scanDraft }) }
  function clearScanFilters() { const clean = { period: 'today' as Period, from: '', to: '', line_id: '', status: '', serial: '', ean: '', production_order: '', page_size: '8' }; setScanDraft(clean); setScanFilters(clean); setScanPage(1) }
  function applyPalletFilters() { setPalletPage(1); setPalletFilters({ ...palletDraft }) }
  function download(blob: Blob, name: string) { const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); URL.revokeObjectURL(url) }
  async function exportScans() { try { download(await exportScansCsv({ ...scanQuery, page: undefined, page_size: undefined }), 'autopackline_leituras.csv') } catch (err) { setError((err as Error).message) } }
  async function exportPallets() { try { download(await exportPalletsCsv({ ...palletQuery, page: undefined, page_size: undefined }), 'autopackline_paletes.csv') } catch (err) { setError((err as Error).message) } }
  async function openScan(id: number) { try { setDetail({ kind: 'scan', data: await getScan(id) }) } catch (err) { setError((err as Error).message) } }
  async function openPallet(id: number) { try { setDetail({ kind: 'pallet', data: await getPalletDetail(id) }) } catch (err) { setError((err as Error).message) } }
  function clearPalletFilters() { const clean = { period: 'today' as Period, from: '', to: '', line_id: '', product_id: '', status: '', pallet_code: '', production_order: '', page_size: '8' }; setPalletDraft(clean); setPalletFilters(clean); setPalletPage(1) }

  async function fetchAllScans() {
    const filters = { ...scanQuery, page: undefined, page_size: undefined }
    const first = await listScans({ ...filters, page: 1, page_size: 100 })
    const items = [...first.items]
    for (let page = 2; page <= first.total_pages; page += 1) {
      const next = await listScans({ ...filters, page, page_size: 100 })
      items.push(...next.items)
    }
    return items
  }

  async function fetchAllPallets() {
    const filters = { ...palletQuery, page: undefined, page_size: undefined }
    const first = await listPallets({ ...filters, page: 1, page_size: 100 })
    const items = [...first.items]
    for (let page = 2; page <= first.total_pages; page += 1) {
      const next = await listPallets({ ...filters, page, page_size: 100 })
      items.push(...next.items)
    }
    return items
  }

  async function printFilteredScans() {
    try {
      const items = await fetchAllScans()
      setPeriodReport({ kind: 'scan', items, title: `Leituras — ${periodLabel(scanFilters.period, scanFilters.from, scanFilters.to)}` })
      window.setTimeout(() => window.print(), 180)
    } catch (err) { setError((err as Error).message) }
  }

  async function printFilteredPallets() {
    try {
      const items = await fetchAllPallets()
      setPeriodReport({ kind: 'pallet', items, title: `Paletes — ${periodLabel(palletFilters.period, palletFilters.from, palletFilters.to)}` })
      window.setTimeout(() => window.print(), 180)
    } catch (err) { setError((err as Error).message) }
  }

  return (
    <section className="card-section">
      <div className="section-heading"><div><p className="eyebrow">RASTREABILIDADE</p><h2>Histórico de produção</h2></div><span className="badge">filtros no MySQL</span></div>
      {error && <div className="message error">{error}</div>}
      <div className="section-tabs"><button className={traceSection === 'scans' ? 'active' : ''} onClick={() => setTraceSection('scans')}>Leituras <span>{scanData.total}</span></button><button className={traceSection === 'pallets' ? 'active' : ''} onClick={() => setTraceSection('pallets')}>Paletes <span>{palletData.total}</span></button></div>

      {traceSection === 'scans' && <div className="trace-block">
        <div className="trace-title"><div><h3>Leituras</h3><p>Consulte eventos válidos, rejeitados, inválidos e duplicados sem carregar todo o histórico.</p></div><strong>{scanData.total} registro(s)</strong></div>
        <div className="filter-grid">
          <label>Período<select value={scanDraft.period} onChange={(e) => setScanDraft({ ...scanDraft, period: e.target.value as Period })}><option value="today">Hoje</option><option value="yesterday">Ontem</option><option value="24h">Últimas 24h</option><option value="7d">Últimos 7 dias</option><option value="month">Este mês</option><option value="custom">Data / período personalizado</option><option value="all">Todo período</option></select></label>
          <label>Linha<select value={scanDraft.line_id} onChange={(e) => setScanDraft({ ...scanDraft, line_id: e.target.value })}><option value="">Todas</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}</select></label>
          <label>Status<select value={scanDraft.status} onChange={(e) => setScanDraft({ ...scanDraft, status: e.target.value })}><option value="">Todos</option><option value="OCCURRENCES">Ocorrências</option><option>VALID</option><option>INVALID</option><option>REJECTED</option><option>DUPLICATE</option></select></label>
          <label>Serial<input value={scanDraft.serial} onChange={(e) => setScanDraft({ ...scanDraft, serial: e.target.value })} placeholder="Ex.: ARC0626" /></label>
          <label>EAN<input value={scanDraft.ean} onChange={(e) => setScanDraft({ ...scanDraft, ean: e.target.value })} placeholder="EAN exato" /></label>
          <label>OP<input value={scanDraft.production_order} onChange={(e) => setScanDraft({ ...scanDraft, production_order: e.target.value })} placeholder="Ex.: 000001275033" /></label>
          {scanDraft.period === 'custom' && <><label>Data inicial<input type="date" value={scanDraft.from} onChange={(e) => setScanDraft({ ...scanDraft, from: e.target.value })} /></label><label>Data final<input type="date" min={scanDraft.from || undefined} value={scanDraft.to} onChange={(e) => setScanDraft({ ...scanDraft, to: e.target.value })} /></label></>}
          <label>Por página<select value={scanDraft.page_size} onChange={(e) => setScanDraft({ ...scanDraft, page_size: e.target.value })}><option value="8">8</option><option value="12">12</option><option value="20">20</option></select></label>
        </div>
        <div className="filter-actions"><button onClick={applyScanFilters}>Filtrar leituras</button><button className="secondary" onClick={clearScanFilters}>Limpar filtros</button><button className="secondary" onClick={exportScans}>Exportar CSV filtrado</button><button className="print-button" onClick={printFilteredScans}>Imprimir período filtrado</button></div>
        <div className="table-wrap compact-table"><table><thead><tr><th>Status</th><th>Serial</th><th>EAN</th><th>OP</th><th>Linha</th><th>Horário</th><th>Ações</th></tr></thead><tbody>
          {loadingScans && <tr><td colSpan={7}>Carregando...</td></tr>}
          {!loadingScans && scanData.items.length === 0 && <tr><td colSpan={7}>Nenhuma leitura encontrada com os filtros atuais.</td></tr>}
          {!loadingScans && scanData.items.map((scan) => <tr key={scan.id}><td><span className={`table-status ${scan.status.toLowerCase()}`}>{scan.status}</span></td><td>{scan.serial_number ?? scan.parsed_data?.serial_number ?? '—'}</td><td>{scan.ean ?? scan.parsed_data?.ean ?? '—'}</td><td>{scan.production_order ?? scan.parsed_data?.production_order ?? '—'}</td><td>{lines.find((l) => l.id === scan.line_id)?.code ?? scan.line_id}</td><td>{formatDate(scan.scanned_at)}</td><td><div className="row-actions"><button className="link-button" onClick={() => openScan(scan.id)}>Detalhes</button></div></td></tr>)}
        </tbody></table></div>
        <Pager page={scanData.page} totalPages={scanData.total_pages} total={scanData.total} pageSize={scanData.page_size} onPage={setScanPage} />
      </div>}

      {traceSection === 'pallets' && <div className="trace-block">
        <div className="trace-title"><div><h3>Paletes</h3><p>Filtre paletes por linha, produto, status, código, OP e período.</p></div><strong>{palletData.total} registro(s)</strong></div>
        <div className="filter-grid">
          <label>Período<select value={palletDraft.period} onChange={(e) => setPalletDraft({ ...palletDraft, period: e.target.value as Period })}><option value="today">Hoje</option><option value="yesterday">Ontem</option><option value="24h">Últimas 24h</option><option value="7d">Últimos 7 dias</option><option value="month">Este mês</option><option value="custom">Data / período personalizado</option><option value="all">Todo período</option></select></label>
          <label>Linha<select value={palletDraft.line_id} onChange={(e) => setPalletDraft({ ...palletDraft, line_id: e.target.value })}><option value="">Todas</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}</select></label>
          <label>Produto<select value={palletDraft.product_id} onChange={(e) => setPalletDraft({ ...palletDraft, product_id: e.target.value })}><option value="">Todos</option>{products.map((product) => <option key={product.id} value={product.id}>{product.model}</option>)}</select></label>
          <label>Status<select value={palletDraft.status} onChange={(e) => setPalletDraft({ ...palletDraft, status: e.target.value })}><option value="">Todos</option><option value="OPEN">OPEN</option><option value="FULL">FULL</option></select></label>
          <label>Código do palete<input value={palletDraft.pallet_code} onChange={(e) => setPalletDraft({ ...palletDraft, pallet_code: e.target.value })} placeholder="Ex.: PAL-" /></label>
          <label>OP<input value={palletDraft.production_order} onChange={(e) => setPalletDraft({ ...palletDraft, production_order: e.target.value })} placeholder="Número da OP" /></label>
          {palletDraft.period === 'custom' && <><label>Data inicial<input type="date" value={palletDraft.from} onChange={(e) => setPalletDraft({ ...palletDraft, from: e.target.value })} /></label><label>Data final<input type="date" min={palletDraft.from || undefined} value={palletDraft.to} onChange={(e) => setPalletDraft({ ...palletDraft, to: e.target.value })} /></label></>}
          <label>Por página<select value={palletDraft.page_size} onChange={(e) => setPalletDraft({ ...palletDraft, page_size: e.target.value })}><option value="8">8</option><option value="12">12</option><option value="20">20</option></select></label>
        </div>
        <div className="filter-actions"><button onClick={applyPalletFilters}>Filtrar paletes</button><button className="secondary" onClick={clearPalletFilters}>Limpar filtros</button><button className="secondary" onClick={exportPallets}>Exportar CSV filtrado</button><button className="print-button" onClick={printFilteredPallets}>Imprimir período filtrado</button></div>
        <div className="table-wrap compact-table"><table><thead><tr><th>Código</th><th>Produto</th><th>Linha</th><th>Qtd.</th><th>Status</th><th>Abertura</th><th>Ações</th></tr></thead><tbody>
          {loadingPallets && <tr><td colSpan={7}>Carregando...</td></tr>}
          {!loadingPallets && palletData.items.length === 0 && <tr><td colSpan={7}>Nenhum palete encontrado com os filtros atuais.</td></tr>}
          {!loadingPallets && palletData.items.map((pallet) => <tr key={pallet.id}><td>{pallet.pallet_code}</td><td>{products.find((p) => p.id === pallet.product_id)?.model ?? pallet.product_id}</td><td>{lines.find((l) => l.id === pallet.line_id)?.code ?? pallet.line_id}</td><td>{pallet.current_quantity}/{pallet.target_quantity}</td><td><span className={`table-status ${pallet.status.toLowerCase()}`}>{pallet.status}</span></td><td>{formatDate(pallet.opened_at)}</td><td><div className="row-actions"><button className="link-button" onClick={() => openPallet(pallet.id)}>Detalhes</button></div></td></tr>)}
        </tbody></table></div>
        <Pager page={palletData.page} totalPages={palletData.total_pages} total={palletData.total} pageSize={palletData.page_size} onPage={setPalletPage} />
      </div>}


      {periodReport && <div className="modal-backdrop report-backdrop" onClick={() => setPeriodReport(null)}><div className="detail-modal period-report" onClick={(e) => e.stopPropagation()}>
        <div className="print-title">AUTOPACKLINE — RELATÓRIO DE RASTREABILIDADE</div>
        <div className="detail-head"><div><p className="eyebrow">RELATÓRIO DO PERÍODO FILTRADO</p><h3>{periodReport.title}</h3><p>{periodReport.items.length} registro(s)</p></div><div className="button-row"><button onClick={() => window.print()}>Imprimir / salvar PDF</button><button className="secondary" onClick={() => setPeriodReport(null)}>Fechar</button></div></div>
        {periodReport.kind === 'scan' ? <div className="table-wrap"><table><thead><tr><th>Status</th><th>Serial</th><th>EAN</th><th>OP</th><th>Linha</th><th>Horário</th><th>Ocorrência</th></tr></thead><tbody>{periodReport.items.map(scan => <tr key={scan.id}><td>{scan.status}</td><td>{scan.serial_number ?? scan.parsed_data?.serial_number ?? '—'}</td><td>{scan.ean ?? scan.parsed_data?.ean ?? '—'}</td><td>{scan.production_order ?? scan.parsed_data?.production_order ?? '—'}</td><td>{lines.find(l => l.id === scan.line_id)?.code ?? scan.line_id}</td><td>{formatDate(scan.scanned_at)}</td><td>{scan.error_message ?? '—'}</td></tr>)}</tbody></table></div> : <div className="table-wrap"><table><thead><tr><th>Código</th><th>Produto</th><th>Linha</th><th>Qtd.</th><th>Status</th><th>Abertura</th><th>Conclusão</th></tr></thead><tbody>{periodReport.items.map(pallet => <tr key={pallet.id}><td>{pallet.pallet_code}</td><td>{products.find(p => p.id === pallet.product_id)?.model ?? pallet.product_id}</td><td>{lines.find(l => l.id === pallet.line_id)?.code ?? pallet.line_id}</td><td>{pallet.current_quantity}/{pallet.target_quantity}</td><td>{pallet.status}</td><td>{formatDate(pallet.opened_at)}</td><td>{pallet.completed_at ? formatDate(pallet.completed_at) : '—'}</td></tr>)}</tbody></table></div>}
      </div></div>}

      {detail && <div className="modal-backdrop" onClick={() => setDetail(null)}><div className="detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="print-title">AUTOPACKLINE — RASTREABILIDADE INDUSTRIAL</div>
        <div className="detail-head"><div><p className="eyebrow">RELATÓRIO DE RASTREABILIDADE</p><h3>{detail.kind === 'scan' ? `Leitura #${detail.data.id}` : detail.data.pallet_code}</h3></div><div className="button-row"><button className="secondary" onClick={() => setDetail(null)}>Fechar</button></div></div>
        {detail.kind === 'scan' ? <><div className="detail-grid"><div><span>Status</span><strong>{detail.data.status}</strong></div><div><span>Data/Hora</span><strong>{formatDate(detail.data.scanned_at)}</strong></div><div><span>Serial</span><strong>{detail.data.serial_number ?? detail.data.parsed_data?.serial_number ?? '—'}</strong></div><div><span>EAN</span><strong>{detail.data.ean ?? detail.data.parsed_data?.ean ?? '—'}</strong></div><div><span>OP</span><strong>{detail.data.production_order ?? detail.data.parsed_data?.production_order ?? '—'}</strong></div><div><span>Linha</span><strong>{lines.find(l => l.id === detail.data.line_id)?.code ?? detail.data.line_id}</strong></div><div><span>Motivo/ocorrência</span><strong>{detail.data.error_message ?? 'Sem ocorrência'}</strong></div><div><span>Código bruto</span><strong>{detail.data.raw_code}</strong></div></div></> : <><div className="detail-grid"><div><span>Status</span><strong>{detail.data.status}</strong></div><div><span>Linha</span><strong>{detail.data.line_code ?? detail.data.line_id}</strong></div><div><span>Produto/modelo</span><strong>{detail.data.product_model ?? detail.data.product_id}</strong></div><div><span>EAN</span><strong>{detail.data.product_ean ?? '—'}</strong></div><div><span>OP</span><strong>{detail.data.production_order ?? '—'}</strong></div><div><span>Lote</span><strong>{detail.data.lot_code ?? '—'}</strong></div><div><span>Quantidade</span><strong>{detail.data.current_quantity}/{detail.data.target_quantity}</strong></div><div><span>Abertura</span><strong>{formatDate(detail.data.opened_at)}</strong></div><div><span>Conclusão</span><strong>{detail.data.completed_at ? formatDate(detail.data.completed_at) : '—'}</strong></div></div><h3>Seriais do palete</h3><div className="table-wrap"><table><thead><tr><th>Seq.</th><th>Serial</th><th>Posição</th><th>Adicionado em</th></tr></thead><tbody>{detail.data.items.map(i => <tr key={i.production_unit_id}><td>{i.sequence_number}</td><td>{i.serial_number}</td><td>{i.position ?? '—'}</td><td>{formatDate(i.added_at)}</td></tr>)}</tbody></table></div></>}
      </div></div>}
    </section>
  )
}
