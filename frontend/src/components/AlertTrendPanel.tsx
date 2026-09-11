import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDashboardOperational, getOeeHistory } from '../services/api'
import type { DashboardIndicatorClassification, DashboardOEEHistory, Product, ProductionLine } from '../types/domain'
import { periodRange } from '../utils/dateRange'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }
type MetricKey = 'availability_percent' | 'performance_percent' | 'quality_percent' | 'oee_percent'
type Status = 'OK' | 'WARNING' | 'CRITICAL' | 'NO_DATA'

const metricConfig: Array<{ key: MetricKey; source: 'availability'|'performance'|'quality'|'oee'; label: string }> = [
  { key: 'availability_percent', source: 'availability', label: 'Disponibilidade' },
  { key: 'performance_percent', source: 'performance', label: 'Performance' },
  { key: 'quality_percent', source: 'quality', label: 'Qualidade' },
  { key: 'oee_percent', source: 'oee', label: 'OEE' },
]

function classify(value: number | null, threshold?: DashboardIndicatorClassification | null): Status {
  if (value == null || !threshold) return 'NO_DATA'
  if (value < threshold.critical_threshold) return 'CRITICAL'
  if (value < threshold.warning_threshold) return 'WARNING'
  return 'OK'
}
function label(status: Status) { return status === 'CRITICAL' ? 'CRÍTICO' : status === 'WARNING' ? 'ATENÇÃO' : status === 'OK' ? 'OK' : '—' }
function fmtDate(value: string) { const [y,m,d] = value.split('-'); return `${d}/${m}/${y}` }

export function AlertTrendPanel({ products, lines, refreshKey }: Props) {
  const [days, setDays] = useState(7)
  const [lineId, setLineId] = useState<number | ''>('')
  const [productId, setProductId] = useState<number | ''>('')
  const [history, setHistory] = useState<DashboardOEEHistory | null>(null)
  const [thresholds, setThresholds] = useState<Record<string, DashboardIndicatorClassification> | null>(null)
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { if (lineId === '' && lines.length) setLineId(lines[0].id) }, [lines, lineId])

  const load = useCallback(async () => {
    if (lineId === '') return
    setLoading(true); setError('')
    try {
      const end = new Date(); const start = new Date(); start.setDate(end.getDate() - (days - 1))
      const dateOnly = (d: Date) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
      const range = periodRange('today', '', '')
      const [hist, current] = await Promise.all([
        getOeeHistory({ line_id: lineId, product_id: productId === '' ? undefined : productId, date_from: dateOnly(start), date_to: dateOnly(end) }),
        getDashboardOperational({ line_id: lineId, product_id: productId === '' ? undefined : productId, ...range }),
      ])
      setHistory(hist)
      const a = current.indicator_alerts
      if (a?.status === 'OK' && a.availability && a.performance && a.quality && a.oee) {
        setThresholds({ availability:a.availability, performance:a.performance, quality:a.quality, oee:a.oee })
        setSource(a.source === 'PRODUCT' ? 'limites específicos do produto' : 'limites gerais da linha')
      } else { setThresholds(null); setSource('sem configuração aplicável') }
    } catch (e) { setError((e as Error).message) } finally { setLoading(false) }
  }, [days, lineId, productId])
  useEffect(() => { load() }, [load, refreshKey])

  const rows = useMemo(() => (history?.points ?? []).map(point => ({
    point,
    statuses: metricConfig.map(m => classify(point[m.key], thresholds?.[m.source])),
  })), [history, thresholds])

  const summary = useMemo(() => metricConfig.map((metric, index) => ({
    label: metric.label,
    critical: rows.filter(r => r.statuses[index] === 'CRITICAL').length,
    warning: rows.filter(r => r.statuses[index] === 'WARNING').length,
    ok: rows.filter(r => r.statuses[index] === 'OK').length,
  })), [rows])

  return <section className="alert-trend-panel panel">
    <div className="panel-title-row"><div><p className="eyebrow">INDICADORES</p><h2>Tendência dos alertas</h2><p className="panel-subtitle">Mostra em quais dias cada indicador ficou OK, em atenção ou crítico usando os limites configurados.</p></div><span className="badge success">histórico calculado no MySQL</span></div>
    <div className="alerts-filters trend-filters">
      <label>Período<select value={days} onChange={e => setDays(Number(e.target.value))}><option value={7}>Últimos 7 dias</option><option value={14}>Últimos 14 dias</option><option value={30}>Últimos 30 dias</option></select></label>
      <label>Linha<select value={lineId} onChange={e => setLineId(e.target.value ? Number(e.target.value) : '')}><option value="">Selecione</option>{lines.map(l => <option key={l.id} value={l.id}>{l.code} - {l.name}</option>)}</select></label>
      <label>Produto<select value={productId} onChange={e => setProductId(e.target.value ? Number(e.target.value) : '')}><option value="">Todos</option>{products.map(p => <option key={p.id} value={p.id}>{p.model}</option>)}</select></label>
      <button className="primary" onClick={load} disabled={loading || lineId === ''}>{loading ? 'Atualizando...' : 'Atualizar tendência'}</button>
    </div>
    <p className="trend-source">Classificação histórica com <strong>{source}</strong>. Os limites atuais são aplicados aos valores históricos sem alterar os registros do período.</p>
    {error && <div className="message error">{error}</div>}
    {!thresholds && <div className="message warning">Configure os limites da linha/produto em Configurações para classificar o histórico.</div>}
    <div className="trend-summary">{summary.map(item => <article key={item.label}><strong>{item.label}</strong><span><b className="critical-text">{item.critical}</b> crítico(s)</span><span><b className="warning-text">{item.warning}</b> atenção</span><span><b className="ok-text">{item.ok}</b> OK</span></article>)}</div>
    <div className="trend-table-wrap"><table className="trend-table"><thead><tr><th>Data</th>{metricConfig.map(m => <th key={m.key}>{m.label}</th>)}<th>Produzido</th><th>Leituras</th></tr></thead><tbody>{rows.map(({point,statuses}) => <tr key={point.date}><td><strong>{fmtDate(point.date)}</strong></td>{statuses.map((s,i) => <td key={metricConfig[i].key}><span className={`trend-status status-${s.toLowerCase()}`}>{label(s)}</span></td>)}<td>{point.palletized_units}</td><td>{point.valid_scans}/{point.total_scans}</td></tr>)}</tbody></table></div>
  </section>
}
