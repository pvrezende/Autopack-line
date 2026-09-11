import { useCallback, useEffect, useMemo, useState } from 'react'
import { getOeeHistory } from '../services/api'
import type { DashboardOEEHistory, DashboardOEEHistoryPoint, Product, ProductionLine } from '../types/domain'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }
type RangePreset = '7' | '14' | '30'

function dateOnly(value: Date) {
  const y = value.getFullYear()
  const m = String(value.getMonth() + 1).padStart(2, '0')
  const d = String(value.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function rangeFor(days: number) {
  const end = new Date()
  const start = new Date(end)
  start.setDate(end.getDate() - (days - 1))
  return { date_from: dateOnly(start), date_to: dateOnly(end) }
}

function fmtDate(value: string) {
  const [y, m, d] = value.split('-')
  return `${d}/${m}/${y}`
}

function avg(points: DashboardOEEHistoryPoint[], field: keyof Pick<DashboardOEEHistoryPoint, 'availability_percent'|'performance_percent'|'quality_percent'|'oee_percent'>) {
  const values = points.map(p => p[field]).filter((v): v is number => typeof v === 'number')
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null
}

function pct(value: number | null) { return value == null ? '—' : `${value.toFixed(1)}%` }
function csvCell(value: string | number) {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}


export function OeeHistoryPanel({ products, lines, refreshKey }: Props) {
  const [preset, setPreset] = useState<RangePreset>('7')
  const [lineId, setLineId] = useState<number | ''>('')
  const [productId, setProductId] = useState<number | ''>('')
  const [data, setData] = useState<DashboardOEEHistory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [reportOpen, setReportOpen] = useState(false)
  const pageSize = 7

  useEffect(() => {
    if (lineId === '' && lines.length) setLineId(lines[0].id)
  }, [lines, lineId])

  const load = useCallback(async () => {
    if (lineId === '') return
    const range = rangeFor(Number(preset))
    setLoading(true); setError('')
    try {
      const result = await getOeeHistory({ line_id: lineId, product_id: productId === '' ? undefined : productId, ...range })
      setData(result); setPage(1)
    } catch (e) { setError((e as Error).message) }
    finally { setLoading(false) }
  }, [lineId, productId, preset])

  useEffect(() => { load() }, [load, refreshKey])

  const points = data?.points ?? []
  const ordered = useMemo(() => [...points].sort((a,b) => b.date.localeCompare(a.date)), [points])
  const totalPages = Math.max(1, Math.ceil(ordered.length / pageSize))
  const pagePoints = ordered.slice((page - 1) * pageSize, page * pageSize)
  const totalUnits = points.reduce((sum,p) => sum + p.palletized_units, 0)
  const totalScans = points.reduce((sum,p) => sum + p.total_scans, 0)
  const validScans = points.reduce((sum,p) => sum + p.valid_scans, 0)
  const averageOee = avg(points, 'oee_percent')
  const averageAvailability = avg(points, 'availability_percent')
  const averagePerformance = avg(points, 'performance_percent')
  const averageQuality = avg(points, 'quality_percent')
  const qualityAccum = totalScans ? validScans / totalScans * 100 : null
  const oeeDays = points.filter(p => p.oee_percent != null).length

  const selectedLine = lines.find(line => line.id === lineId)
  const selectedProduct = products.find(product => product.id === productId)
  const rangeLabel = `Últimos ${preset} dias`

  function exportCsv() {
    if (!data) return
    const linesCsv = [
      ['AUTOPACKLINE - Relatório de Indicadores / OEE'],
      ['Período', rangeLabel],
      ['Linha', selectedLine ? `${selectedLine.code} - ${selectedLine.name}` : '—'],
      ['Produto', selectedProduct ? selectedProduct.model : 'Todos'],
      [],
      ['OEE médio', pct(averageOee), 'Disponibilidade média', pct(averageAvailability), 'Performance média', pct(averagePerformance), 'Qualidade média', pct(averageQuality)],
      ['Qualidade acumulada', pct(qualityAccum), 'Produzido no período', totalUnits, 'Leituras válidas', validScans, 'Leituras totais', totalScans],
      [],
      ['Data','Disponibilidade','Performance','Qualidade','OEE','Produzido','Leituras válidas','Leituras totais'],
      ...ordered.map(point => [
        fmtDate(point.date), pct(point.availability_percent), pct(point.performance_percent), pct(point.quality_percent), pct(point.oee_percent), point.palletized_units, point.valid_scans, point.total_scans
      ])
    ]
    const content = '\ufeff' + linesCsv.map(row => row.map(csvCell).join(';')).join('\r\n')
    downloadBlob(new Blob([content], { type: 'text/csv;charset=utf-8' }), `autopackline_oee_${data.date_from}_${data.date_to}.csv`)
  }

  function printReport() {
    if (!data || !ordered.length) return
    setError('')
    setReportOpen(true)
    window.setTimeout(() => window.print(), 120)
  }

  return <section className="oee-history-panel panel">
    <div className="panel-title-row">
      <div><p className="eyebrow">INDICADORES</p><h2>Histórico de OEE</h2><p className="panel-subtitle">Compare Disponibilidade, Performance, Qualidade e OEE por dia.</p></div>
      <span className="badge success">dados calculados no MySQL</span>
    </div>

    <div className="oee-history-filters">
      <label>Período<select value={preset} onChange={e => setPreset(e.target.value as RangePreset)}><option value="7">Últimos 7 dias</option><option value="14">Últimos 14 dias</option><option value="30">Últimos 30 dias</option></select></label>
      <label>Linha<select value={lineId} onChange={e => setLineId(e.target.value ? Number(e.target.value) : '')}><option value="">Selecione</option>{lines.map(line => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}</select></label>
      <label>Produto<select value={productId} onChange={e => setProductId(e.target.value ? Number(e.target.value) : '')}><option value="">Todos</option>{products.map(product => <option key={product.id} value={product.id}>{product.model}</option>)}</select></label>
      <button className="primary" onClick={load} disabled={loading || lineId === ''}>{loading ? 'Calculando...' : 'Atualizar indicadores'}</button>
    </div>

    <div className="oee-history-actions">
      <button className="secondary" onClick={exportCsv} disabled={!data || !ordered.length}>Exportar CSV</button>
      <button className="secondary" onClick={printReport} disabled={!data || !ordered.length}>Imprimir relatório</button>
      <span>Exportação e impressão respeitam os filtros e incluem todo o período, não apenas a página visível.</span>
    </div>

    {error && <div className="message error">{error}</div>}

    <div className="oee-history-summary">
      <article><span>OEE médio</span><strong>{pct(averageOee)}</strong><small>{oeeDays} dia(s) com OEE completo</small></article>
      <article><span>Disponibilidade média</span><strong>{pct(averageAvailability)}</strong><small>tempo disponível / planejado</small></article>
      <article><span>Performance média</span><strong>{pct(averagePerformance)}</strong><small>produção real / teórica</small></article>
      <article><span>Qualidade média</span><strong>{pct(averageQuality)}</strong><small>média diária</small></article>
      <article><span>Qualidade acumulada</span><strong>{pct(qualityAccum)}</strong><small>{validScans}/{totalScans} leituras válidas</small></article>
      <article><span>Produzido no período</span><strong>{totalUnits}</strong><small>unidades paletizadas</small></article>
    </div>

    <div className="oee-history-table-wrap">
      <table className="oee-history-table">
        <thead><tr><th>Data</th><th>Disponibilidade</th><th>Performance</th><th>Qualidade</th><th>OEE</th><th>Produzido</th><th>Leituras</th></tr></thead>
        <tbody>{pagePoints.length ? pagePoints.map(point => <tr key={point.date}>
          <td data-label="Data"><strong>{fmtDate(point.date)}</strong></td>
          <td data-label="Disponibilidade">{pct(point.availability_percent)}</td>
          <td data-label="Performance">{pct(point.performance_percent)}</td>
          <td data-label="Qualidade">{pct(point.quality_percent)}</td>
          <td data-label="OEE"><span className={`oee-history-value ${point.oee_percent != null && point.oee_percent >= 85 ? 'good' : point.oee_percent != null && point.oee_percent < 60 ? 'low' : ''}`}>{pct(point.oee_percent)}</span></td>
          <td data-label="Produzido">{point.palletized_units}</td>
          <td data-label="Leituras">{point.valid_scans}/{point.total_scans}</td>
        </tr>) : <tr><td colSpan={7}>Nenhum dado encontrado para o período selecionado.</td></tr>}</tbody>
      </table>
    </div>

    <div className="pagination oee-history-pagination"><span>Mostrando {ordered.length ? (page-1)*pageSize+1 : 0}–{Math.min(page*pageSize, ordered.length)} de {ordered.length}</span><div><button className="secondary small" disabled={page <= 1} onClick={() => setPage(p => p-1)}>Anterior</button><strong>Página {page} de {totalPages}</strong><button className="secondary small" disabled={page >= totalPages} onClick={() => setPage(p => p+1)}>Próxima</button></div></div>
    {reportOpen && <div className="modal-backdrop report-backdrop oee-report-backdrop">
      <section className="detail-modal period-report oee-print-report">
        <div className="print-title">AUTOPACKLINE · RELATÓRIO GERENCIAL DE OEE</div>
        <div className="detail-head">
          <div>
            <p className="eyebrow">INDICADORES</p>
            <h3>Relatório de Indicadores / OEE</h3>
            <p>{rangeLabel} · {selectedLine ? `${selectedLine.code} - ${selectedLine.name}` : '—'} · {selectedProduct ? selectedProduct.model : 'Todos'}</p>
          </div>
          <div className="button-row">
            <button onClick={() => window.print()}>Imprimir / salvar PDF</button>
            <button className="secondary" onClick={() => setReportOpen(false)}>Fechar</button>
          </div>
        </div>

        <div className="oee-print-summary">
          <article><small>OEE médio</small><strong>{pct(averageOee)}</strong></article>
          <article><small>Disponibilidade média</small><strong>{pct(averageAvailability)}</strong></article>
          <article><small>Performance média</small><strong>{pct(averagePerformance)}</strong></article>
          <article><small>Qualidade média</small><strong>{pct(averageQuality)}</strong></article>
          <article><small>Qualidade acumulada</small><strong>{pct(qualityAccum)}</strong></article>
          <article><small>Produzido</small><strong>{totalUnits}</strong></article>
        </div>

        <div className="table-wrap oee-print-table-wrap">
          <table>
            <thead><tr><th>Data</th><th>Disponibilidade</th><th>Performance</th><th>Qualidade</th><th>OEE</th><th>Produzido</th><th>Leituras</th></tr></thead>
            <tbody>{ordered.map(point => <tr key={`print-${point.date}`}><td>{fmtDate(point.date)}</td><td>{pct(point.availability_percent)}</td><td>{pct(point.performance_percent)}</td><td>{pct(point.quality_percent)}</td><td>{pct(point.oee_percent)}</td><td>{point.palletized_units}</td><td>{point.valid_scans}/{point.total_scans}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>}

  </section>
}
