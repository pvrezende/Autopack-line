import { useCallback, useEffect, useMemo, useState } from 'react'
import { getLossAnalysis } from '../services/api'
import type { DashboardLossAnalysis, Product, ProductionLine } from '../types/domain'

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

function minutesLabel(value: number) {
  if (value < 60) return `${value} min`
  const h = Math.floor(value / 60)
  const m = value % 60
  return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h00`
}

export function LossAnalysisPanel({ products, lines, refreshKey }: Props) {
  const [preset, setPreset] = useState<RangePreset>('7')
  const [lineId, setLineId] = useState<number | ''>('')
  const [productId, setProductId] = useState<number | ''>('')
  const [data, setData] = useState<DashboardLossAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (lineId === '' && lines.length) setLineId(lines[0].id)
  }, [lines, lineId])

  const load = useCallback(async () => {
    if (lineId === '') return
    const range = rangeFor(Number(preset))
    setLoading(true); setError('')
    try {
      const result = await getLossAnalysis({ line_id: lineId, product_id: productId === '' ? undefined : productId, ...range })
      setData(result)
    } catch (e) { setError((e as Error).message) }
    finally { setLoading(false) }
  }, [lineId, productId, preset])

  useEffect(() => { load() }, [load, refreshKey])

  const topDowntime = useMemo(() => data?.downtime_reasons.slice(0, 8) ?? [], [data])
  const topScans = useMemo(() => data?.scan_reasons.slice(0, 8) ?? [], [data])

  return <section className="loss-analysis-panel panel">
    <div className="panel-title-row">
      <div><p className="eyebrow">INDICADORES</p><h2>Análise de perdas</h2><p className="panel-subtitle">Pareto de paradas e ocorrências de rastreabilidade para localizar as principais perdas do processo.</p></div>
      <span className="badge success">dados calculados no MySQL</span>
    </div>

    <div className="loss-analysis-filters">
      <label>Período<select value={preset} onChange={e => setPreset(e.target.value as RangePreset)}><option value="7">Últimos 7 dias</option><option value="14">Últimos 14 dias</option><option value="30">Últimos 30 dias</option></select></label>
      <label>Linha<select value={lineId} onChange={e => setLineId(e.target.value ? Number(e.target.value) : '')}><option value="">Selecione</option>{lines.map(line => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}</select></label>
      <label>Produto<select value={productId} onChange={e => setProductId(e.target.value ? Number(e.target.value) : '')}><option value="">Todos</option>{products.map(product => <option key={product.id} value={product.id}>{product.model}</option>)}</select></label>
      <button className="primary" onClick={load} disabled={loading || lineId === ''}>{loading ? 'Calculando...' : 'Atualizar perdas'}</button>
    </div>

    {error && <div className="message error">{error}</div>}

    <div className="loss-summary">
      <article><span>Tempo parado</span><strong>{minutesLabel(data?.total_downtime_minutes ?? 0)}</strong><small>planejado + não planejado</small></article>
      <article className="loss-warning"><span>Não planejado</span><strong>{minutesLabel(data?.unplanned_downtime_minutes ?? 0)}</strong><small>impacta disponibilidade</small></article>
      <article><span>Planejado</span><strong>{minutesLabel(data?.planned_downtime_minutes ?? 0)}</strong><small>retirado do tempo planejado</small></article>
      <article><span>Ocorrências de leitura</span><strong>{data?.scan_occurrences ?? 0}</strong><small>INVALID + REJECTED + DUPLICATE</small></article>
      <article><span>Rejected</span><strong>{data?.rejected_count ?? 0}</strong><small>regra de negócio</small></article>
      <article><span>Duplicate</span><strong>{data?.duplicate_count ?? 0}</strong><small>serial já registrado</small></article>
    </div>

    <div className="loss-grid">
      <section className="loss-card">
        <div className="loss-card-head"><div><h3>Pareto de paradas não planejadas</h3><p>Ordenado pelo tempo perdido.</p></div><strong>{data?.unplanned_downtime_minutes ?? 0} min</strong></div>
        <div className="loss-bars">
          {topDowntime.length ? topDowntime.map(item => <div className="loss-row" key={item.label}>
            <div className="loss-row-head"><span title={item.label}>{item.label}</span><strong>{minutesLabel(item.minutes)} · {item.percent.toFixed(1)}%</strong></div>
            <div className="loss-track"><i style={{ width: `${Math.max(3, item.percent)}%` }} /></div>
            <small>{item.occurrences} ocorrência(s)</small>
          </div>) : <p className="empty-note">Nenhuma parada não planejada no período.</p>}
        </div>
      </section>

      <section className="loss-card">
        <div className="loss-card-head"><div><h3>Pareto de ocorrências de leitura</h3><p>Principais motivos de perda de qualidade/rastreabilidade.</p></div><strong>{data?.scan_occurrences ?? 0}</strong></div>
        <div className="loss-bars scan-loss-bars">
          {topScans.length ? topScans.map(item => <div className="loss-row" key={item.label}>
            <div className="loss-row-head"><span title={item.label}>{item.label}</span><strong>{item.count} · {item.percent.toFixed(1)}%</strong></div>
            <div className="loss-track danger"><i style={{ width: `${Math.max(3, item.percent)}%` }} /></div>
          </div>) : <p className="empty-note">Nenhuma ocorrência de leitura no período.</p>}
        </div>
        {productId !== '' && <p className="loss-note">Ao filtrar por produto, ocorrências INVALID sem EAN identificado ficam fora do Pareto, pois não é possível atribuí-las com segurança a um produto.</p>}
      </section>
    </div>
  </section>
}
