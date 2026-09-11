import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDashboardOperational } from '../services/api'
import type { DashboardIndicatorClassification, DashboardOperational, Product, ProductionLine } from '../types/domain'
import { periodRange } from '../utils/dateRange'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }

type AlertItem = {
  key: string
  title: string
  status: 'OK' | 'WARNING' | 'CRITICAL' | 'NO_DATA'
  value: number | null
  warning: number
  critical: number
  recommendation: string
}

const labels: Record<string, string> = {
  AVAILABILITY: 'Disponibilidade',
  PERFORMANCE: 'Performance',
  QUALITY: 'Qualidade',
  OEE: 'OEE',
}

const recommendations: Record<string, string> = {
  AVAILABILITY: 'Verifique paradas não planejadas, disponibilidade da linha e causas de indisponibilidade.',
  PERFORMANCE: 'Compare ritmo real × Takt, produção por hora e possíveis microparadas ou perdas de velocidade.',
  QUALITY: 'Analise REJECTED, DUPLICATE e INVALID na rastreabilidade para localizar as principais perdas de qualidade.',
  OEE: 'Priorize o pior componente entre Disponibilidade, Performance e Qualidade antes de atuar no OEE consolidado.',
}

function classifyText(status: AlertItem['status']) {
  if (status === 'CRITICAL') return 'CRÍTICO'
  if (status === 'WARNING') return 'ATENÇÃO'
  if (status === 'OK') return 'OK'
  return 'SEM DADOS'
}

function toAlert(metric?: DashboardIndicatorClassification | null): AlertItem | null {
  if (!metric) return null
  return {
    key: metric.metric,
    title: labels[metric.metric] ?? metric.metric,
    status: metric.status,
    value: metric.value,
    warning: metric.warning_threshold,
    critical: metric.critical_threshold,
    recommendation: recommendations[metric.metric] ?? 'Verifique os dados operacionais relacionados a este indicador.',
  }
}

export function OperationalAlertsPanel({ products, lines, refreshKey }: Props) {
  const [lineId, setLineId] = useState<number | ''>('')
  const [productId, setProductId] = useState<number | ''>('')
  const [data, setData] = useState<DashboardOperational | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (lineId === '' && lines.length) setLineId(lines[0].id)
  }, [lines, lineId])

  const load = useCallback(async () => {
    if (lineId === '') return
    const range = periodRange('today', '', '')
    setLoading(true); setError('')
    try {
      const result = await getDashboardOperational({
        line_id: lineId,
        product_id: productId === '' ? undefined : productId,
        ...range,
      })
      setData(result)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [lineId, productId])

  useEffect(() => { load() }, [load, refreshKey])

  const alerts = useMemo(() => {
    const source = data?.indicator_alerts
    if (!source || source.status !== 'OK') return [] as AlertItem[]
    return [source.availability, source.performance, source.quality, source.oee]
      .map(toAlert)
      .filter((item): item is AlertItem => Boolean(item))
  }, [data])

  const priorities = useMemo(
    () => alerts.filter(item => item.status === 'CRITICAL' || item.status === 'WARNING')
      .sort((a, b) => (a.status === b.status ? 0 : a.status === 'CRITICAL' ? -1 : 1)),
    [alerts],
  )

  const counts = useMemo(() => ({
    critical: alerts.filter(item => item.status === 'CRITICAL').length,
    warning: alerts.filter(item => item.status === 'WARNING').length,
    ok: alerts.filter(item => item.status === 'OK').length,
    noData: alerts.filter(item => item.status === 'NO_DATA').length,
  }), [alerts])

  const sourceLabel = data?.indicator_alerts?.source === 'PRODUCT'
    ? 'limites específicos do produto'
    : data?.indicator_alerts?.source === 'LINE'
      ? 'limites gerais da linha'
      : 'sem configuração aplicável'

  return <section className="operational-alerts-panel panel">
    <div className="panel-title-row">
      <div>
        <p className="eyebrow">INDICADORES</p>
        <h2>Central de alertas operacionais</h2>
        <p className="panel-subtitle">Prioriza os indicadores fora da meta usando exclusivamente os limites configurados no sistema.</p>
      </div>
      <span className="badge success">dados calculados no MySQL</span>
    </div>

    <div className="alerts-filters">
      <label>Linha<select value={lineId} onChange={e => setLineId(e.target.value ? Number(e.target.value) : '')}>
        <option value="">Selecione</option>{lines.map(line => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}
      </select></label>
      <label>Produto<select value={productId} onChange={e => setProductId(e.target.value ? Number(e.target.value) : '')}>
        <option value="">Todos</option>{products.map(product => <option key={product.id} value={product.id}>{product.model}</option>)}
      </select></label>
      <div className="alerts-scope"><span>Período</span><strong>Hoje</strong><small>{sourceLabel}</small></div>
      <button className="primary" onClick={load} disabled={loading || lineId === ''}>{loading ? 'Atualizando...' : 'Atualizar alertas'}</button>
    </div>

    {error && <div className="message error">{error}</div>}

    {data?.indicator_alerts?.status === 'NO_CONFIG' && <div className="message warning">Nenhum limite configurado para esta combinação. Cadastre os limites em Configurações → Limites e alertas dos indicadores.</div>}
    {data?.indicator_alerts?.status === 'SELECT_LINE' && <div className="message warning">Selecione uma linha para avaliar os alertas.</div>}

    <div className="alerts-summary">
      <article className="alert-summary critical"><span>Críticos</span><strong>{counts.critical}</strong><small>ação imediata</small></article>
      <article className="alert-summary warning"><span>Atenção</span><strong>{counts.warning}</strong><small>acompanhar tendência</small></article>
      <article className="alert-summary ok"><span>Dentro da meta</span><strong>{counts.ok}</strong><small>sem alerta</small></article>
      <article className="alert-summary"><span>Sem dados</span><strong>{counts.noData}</strong><small>não classificado</small></article>
    </div>

    <div className="alerts-indicator-grid">
      {alerts.map(item => <article key={item.key} className={`indicator-alert-card status-${item.status.toLowerCase()}`}>
        <div className="indicator-alert-head"><span>{item.title}</span><b>{classifyText(item.status)}</b></div>
        <strong className="indicator-alert-value">{item.value == null ? '—' : `${item.value.toFixed(1)}%`}</strong>
        <small>Atenção abaixo de {item.warning.toFixed(1)}% · Crítico abaixo de {item.critical.toFixed(1)}%</small>
      </article>)}
    </div>

    <div className="alerts-priority-grid">
      <section className="alerts-priority-card">
        <div className="alerts-section-head"><div><h3>Prioridades de ação</h3><p>Indicadores ordenados por severidade.</p></div><strong>{priorities.length}</strong></div>
        {priorities.length ? <div className="priority-list">{priorities.map((item, index) => <article key={item.key}>
          <span className={`priority-rank ${item.status.toLowerCase()}`}>{index + 1}</span>
          <div><div className="priority-title"><strong>{item.title}</strong><b>{classifyText(item.status)}</b></div><p>{item.recommendation}</p></div>
        </article>)}</div> : <p className="empty-note">Nenhum indicador em atenção ou crítico para os filtros atuais.</p>}
      </section>

      <section className="alerts-priority-card">
        <div className="alerts-section-head"><div><h3>Contexto operacional de hoje</h3><p>Dados que ajudam na investigação do alerta.</p></div></div>
        <div className="alerts-context-grid">
          <div><span>Leituras</span><strong>{data?.summary.total_scans ?? 0}</strong></div>
          <div><span>Ocorrências</span><strong>{data?.summary.invalid_scans ?? 0}</strong></div>
          <div><span>Unidades paletizadas</span><strong>{data?.summary.palletized_units ?? 0}</strong></div>
          <div><span>Paradas não planejadas</span><strong>{data?.efficiency ? `${data.efficiency.unplanned_downtime_minutes} min` : '—'}</strong></div>
        </div>
        <p className="alerts-context-note">Use Histórico de OEE e Análise de perdas para aprofundar a causa antes de alterar metas ou limites.</p>
      </section>
    </div>
  </section>
}
