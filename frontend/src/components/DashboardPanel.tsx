import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDashboardOperational, type DashboardFilters } from '../services/api'
import type { DashboardOperational, Product, ProductionLine } from '../types/domain'
import { formatLocalDateTime, formatLocalTime } from '../utils/dateTime'
import { periodRange, type PeriodFilter } from '../utils/dateRange'
import type { TraceabilityPreset } from './TraceabilityPanel'

type Period = PeriodFilter
type Props = {
  products: Product[]
  lines: ProductionLine[]
  refreshKey: number
  onOpenTraceability: (preset: TraceabilityPreset) => void
  canTraceability?: boolean
}

const emptyData: DashboardOperational = {
  summary: { total_scans: 0, valid_scans: 0, invalid_scans: 0, approval_rate: 0, open_pallets: 0, completed_pallets: 0, palletized_units: 0 },
  production_by_hour: [], scan_statuses: [], open_pallets: [], recent_occurrences: [], production_target: null, pace: null, efficiency: null, oee: null, indicator_alerts: null,
}

function formatDate(value: string) {
  return formatLocalDateTime(value)
}

export function DashboardPanel({ products, lines, refreshKey, onOpenTraceability, canTraceability = true }: Props) {
  const [draft, setDraft] = useState({ period: 'today' as Period, from: '', to: '', line_id: '', product_id: '', production_order: '' })
  const [filters, setFilters] = useState(draft)
  const [data, setData] = useState<DashboardOperational>(emptyData)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const query = useMemo<DashboardFilters>(() => ({
    line_id: filters.line_id ? Number(filters.line_id) : undefined,
    product_id: filters.product_id ? Number(filters.product_id) : undefined,
    production_order: filters.production_order.trim() || undefined,
    ...periodRange(filters.period, filters.from, filters.to),
  }), [filters])

  const load = useCallback(async () => {
    setLoading(true)
    try { setData(await getDashboardOperational(query)); setError('') }
    catch (err) { setError((err as Error).message) }
    finally { setLoading(false) }
  }, [query])

  useEffect(() => { load() }, [load, refreshKey])

  const maxHourly = Math.max(1, ...data.production_by_hour.map((item) => item.quantity))
  const maxStatus = Math.max(1, ...data.scan_statuses.map((item) => item.quantity))
  const selectedProduct = products.find((item) => item.id === Number(filters.product_id))
  const target = data.production_target
  const canCompareDaily = (filters.period === 'today' || filters.period === 'yesterday') && !!target?.daily_target
  const dailyTarget = target?.daily_target ?? null
  const realizedUnits = data.summary.palletized_units
  const dailyProgress = canCompareDaily && dailyTarget
    ? Math.min(999, realizedUnits / dailyTarget * 100)
    : null
  const remainingUnits = dailyProgress != null && dailyTarget != null ? Math.max(0, dailyTarget - realizedUnits) : null
  const targetSituation = dailyProgress == null ? 'Sem comparação diária' : dailyProgress >= 100 ? 'Meta atingida' : 'Em andamento'
  const pace = data.pace
  const paceLabel = pace?.status === 'ON_PACE' ? 'Dentro do ritmo' : pace?.status === 'BELOW_PACE' ? 'Abaixo do ritmo' : 'Aguardando dados'
  const paceClass = pace?.status === 'ON_PACE' ? 'pace-ok' : pace?.status === 'BELOW_PACE' ? 'pace-low' : 'pace-empty'
  const averageIntervalLabel = pace?.average_interval_seconds != null ? `${pace.average_interval_seconds.toFixed(0)} s` : '—'
  const pacePercentLabel = pace?.pace_percent != null ? `${pace.pace_percent.toFixed(1)}%` : '—'
  const efficiency = data.efficiency
  const oee = data.oee
  const alerts = data.indicator_alerts
  const alertLabel = (status?: string) => status === 'OK' ? 'OK' : status === 'WARNING' ? 'ATENÇÃO' : status === 'CRITICAL' ? 'CRÍTICO' : ''
  const alertClass = (status?: string) => status === 'OK' ? 'alert-ok' : status === 'WARNING' ? 'alert-warning' : status === 'CRITICAL' ? 'alert-critical' : ''
  const fmtMinutes = (value: number) => { const h = Math.floor(value / 60); const m = value % 60; return h > 0 ? `${h}h${String(m).padStart(2, '0')}` : `${m} min` }
  const efficiencyStatus = efficiency?.status === 'SELECT_LINE' ? 'Selecione uma linha' : efficiency?.status === 'SELECT_PERIOD' ? 'Selecione um período' : efficiency?.status === 'NO_SHIFT' ? 'Sem turno configurado' : efficiency?.status === 'NO_SCHEDULE_IN_PERIOD' ? 'Sem jornada no período' : ''

  function tracePreset(status?: string): TraceabilityPreset {
    return {
      period: filters.period,
      from: filters.from,
      to: filters.to,
      line_id: filters.line_id,
      status: status ?? '',
      ean: selectedProduct?.ean ?? '',
      production_order: filters.production_order,
    }
  }

  return (
    <section className="card-section dashboard-operational">
      <div className="section-heading">
        <div><p className="eyebrow">DASHBOARD</p><h2>Dashboard operacional</h2></div>
        <span className="badge">dados calculados no MySQL</span>
      </div>

      <div className="dashboard-filter-grid">
        <label>Período<select value={draft.period} onChange={(e) => setDraft({ ...draft, period: e.target.value as Period })}><option value="today">Hoje</option><option value="yesterday">Ontem</option><option value="24h">Últimas 24h</option><option value="7d">Últimos 7 dias</option><option value="month">Este mês</option><option value="custom">Data / período personalizado</option><option value="all">Todo período</option></select></label>
        <label>Linha<select value={draft.line_id} onChange={(e) => setDraft({ ...draft, line_id: e.target.value })}><option value="">Todas</option>{lines.map((line) => <option key={line.id} value={line.id}>{line.code} - {line.name}</option>)}</select></label>
        <label>Produto<select value={draft.product_id} onChange={(e) => setDraft({ ...draft, product_id: e.target.value })}><option value="">Todos</option>{products.map((product) => <option key={product.id} value={product.id}>{product.model}</option>)}</select></label>
        <label>OP<input value={draft.production_order} onChange={(e) => setDraft({ ...draft, production_order: e.target.value })} placeholder="Ex.: 000001275033" /></label>
        {draft.period === 'custom' && <><label>Data inicial<input type="date" value={draft.from} onChange={(e) => setDraft({ ...draft, from: e.target.value })} /></label><label>Data final<input type="date" min={draft.from || undefined} value={draft.to} onChange={(e) => setDraft({ ...draft, to: e.target.value })} /></label></>}
      </div>
      <div className="filter-actions"><button onClick={() => setFilters({ ...draft })}>{loading ? 'Atualizando...' : 'Aplicar filtros'}</button><button className="secondary" onClick={() => { const clean = { period: 'today' as Period, from: '', to: '', line_id: '', product_id: '', production_order: '' }; setDraft(clean); setFilters(clean) }}>Limpar filtros</button></div>
      {error && <div className="message error">{error}</div>}


      {filters.line_id && (
        <article className="production-target-strip performance-strip">
          <div className="target-title">
            <span>Meta aplicada</span>
            <strong>{target ? (target.source === 'PRODUCT' ? 'Produto específico' : 'Meta geral da linha') : 'Nenhuma meta configurada'}</strong>
            <small>{target ? 'Comparação calculada com os dados reais do período.' : 'Cadastre uma meta para habilitar o acompanhamento.'}</small>
          </div>
          {target ? <>
            <div><span>Meta/hora</span><strong>{target.hourly_target ?? '—'}</strong><small>unidades por hora</small></div>
            <div><span>Meta diária</span><strong>{target.daily_target ?? '—'}</strong><small>unidades planejadas</small></div>
            <div><span>Takt</span><strong>{target.takt_seconds != null ? `${Number(target.takt_seconds).toFixed(0)} s` : '—'}</strong><small>ritmo planejado</small></div>
            <div className="target-realized"><span>Produzido</span><strong>{realizedUnits}</strong><small>unidades paletizadas</small></div>
            <div className="target-pace"><span>Ritmo real médio</span><strong>{averageIntervalLabel}</strong><small>{pace && pace.sample_count >= 2 ? `entre ${pace.sample_count} unidades registradas` : 'mínimo de 2 unidades para calcular'}</small></div>
            <div className={`target-pace-status ${paceClass}`}><span>Ritmo × Takt</span><strong>{pacePercentLabel}</strong><small>{paceLabel}{pace?.difference_seconds != null ? ` · ${Math.abs(pace.difference_seconds).toFixed(0)} s ${pace.difference_seconds <= 0 ? 'mais rápido' : 'mais lento'}` : ''}</small></div>
            <div className={dailyProgress != null && dailyProgress >= 100 ? 'target-progress reached' : 'target-progress'}>
              <span>Atingimento</span>
              <strong>{dailyProgress != null ? `${dailyProgress.toFixed(1)}%` : '—'}</strong>
              <small>{dailyProgress != null ? `${targetSituation} · faltam ${remainingUnits} un.` : 'Selecione Hoje ou Ontem para comparar com a meta diária.'}</small>
            </div>
          </> : <p>Cadastre uma meta em Configurações para esta linha. Se houver uma meta específica do produto, ela terá prioridade sobre a meta geral da linha.</p>}
        </article>
      )}

      {filters.line_id && efficiency && (
        <article className="efficiency-strip">
          <div className="efficiency-title"><strong>Eficiência operacional</strong><small>{efficiency.status === 'OK' ? 'Tempo disponível ÷ tempo planejado' : efficiencyStatus}</small></div>
          <div><span>Jornada bruta</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.gross_scheduled_minutes) : '—'}</strong><small>turnos no período</small></div>
          <div><span>Pausas</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.planned_break_minutes) : '—'}</strong><small>planejadas</small></div>
          <div><span>Paradas planejadas</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.planned_downtime_minutes) : '—'}</strong><small>descontadas da jornada</small></div>
          <div><span>Tempo planejado</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.planned_production_minutes) : '—'}</strong><small>tempo previsto para produzir</small></div>
          <div className="efficiency-loss"><span>Paradas não planejadas</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.unplanned_downtime_minutes) : '—'}</strong><small>perda operacional</small></div>
          <div className="efficiency-available"><span>Tempo disponível</span><strong>{efficiency.status === 'OK' ? fmtMinutes(efficiency.available_minutes) : '—'}</strong><small>após as perdas</small></div>
          <div className={efficiency.operational_efficiency_percent != null && efficiency.operational_efficiency_percent >= 90 ? 'efficiency-result good' : 'efficiency-result'}><span>Eficiência</span><strong>{efficiency.operational_efficiency_percent != null ? `${efficiency.operational_efficiency_percent.toFixed(1)}%` : '—'}</strong><small>disponibilidade operacional</small></div>
        </article>
      )}

      {filters.line_id && oee && (
        <article className="oee-strip">
          <div className="oee-title"><strong>OEE</strong><small>Disponibilidade × Performance × Qualidade</small></div>
          <div className={alertClass(alerts?.availability?.status)}><span className="indicator-card-label">Disponibilidade {alertLabel(alerts?.availability?.status) && <b className={`indicator-state ${alertClass(alerts?.availability?.status)}`}>{alertLabel(alerts?.availability?.status)}</b>}</span><strong>{oee.availability_percent != null ? `${oee.availability_percent.toFixed(1)}%` : '—'}</strong><small>tempo disponível / planejado</small></div>
          <div className={alertClass(alerts?.performance?.status)}><span className="indicator-card-label">Performance {alertLabel(alerts?.performance?.status) && <b className={`indicator-state ${alertClass(alerts?.performance?.status)}`}>{alertLabel(alerts?.performance?.status)}</b>}</span><strong>{oee.performance_percent != null ? `${oee.performance_percent.toFixed(1)}%` : '—'}</strong><small>{oee.expected_units != null ? `${oee.actual_units} de ${oee.expected_units.toFixed(1)} un. teóricas` : 'requer Takt e tempo disponível'}</small></div>
          <div className={alertClass(alerts?.quality?.status)}><span className="indicator-card-label">Qualidade {alertLabel(alerts?.quality?.status) && <b className={`indicator-state ${alertClass(alerts?.quality?.status)}`}>{alertLabel(alerts?.quality?.status)}</b>}</span><strong>{oee.quality_percent != null ? `${oee.quality_percent.toFixed(1)}%` : '—'}</strong><small>{oee.quality_total_count > 0 ? `${oee.quality_good_count}/${oee.quality_total_count} leituras válidas` : 'sem leituras no período'}</small></div>
          <div className={`oee-result ${alertClass(alerts?.oee?.status)}`}><span className="indicator-card-label">OEE {alertLabel(alerts?.oee?.status) && <b className={`indicator-state ${alertClass(alerts?.oee?.status)}`}>{alertLabel(alerts?.oee?.status)}</b>}</span><strong>{oee.oee_percent != null ? `${oee.oee_percent.toFixed(1)}%` : '—'}</strong><small>{alerts?.status === 'NO_CONFIG' ? 'configure limites em Configurações' : oee.status === 'OK' ? 'índice consolidado' : oee.status === 'NO_QUALITY_DATA' ? 'aguardando dados de qualidade' : oee.status === 'NO_TARGET' ? 'configure uma meta/Takt' : 'dados insuficientes'}</small></div>
        </article>
      )}

      <div className="dashboard-metrics">
        <button className="metric-card" disabled={!canTraceability} onClick={() => canTraceability && onOpenTraceability(tracePreset())}><span>Leituras</span><strong>{data.summary.total_scans}</strong><small>{canTraceability ? 'ver rastreabilidade' : 'resumo do período'}</small></button>
        <button className="metric-card" disabled={!canTraceability} onClick={() => canTraceability && onOpenTraceability(tracePreset('VALID'))}><span>Leituras válidas</span><strong>{data.summary.valid_scans}</strong><small>{canTraceability ? 'ver válidas' : 'no período'}</small></button>
        <button className="metric-card alert" disabled={!canTraceability} onClick={() => canTraceability && onOpenTraceability(tracePreset('OCCURRENCES'))}><span>Ocorrências</span><strong>{data.summary.invalid_scans}</strong><small>{canTraceability ? 'ver problemas' : 'no período'}</small></button>
        <article className="metric-card"><span>Taxa de aprovação</span><strong>{data.summary.approval_rate.toFixed(1)}%</strong><small>válidas / leituras</small></article>
        <article className="metric-card"><span>Unidades paletizadas</span><strong>{data.summary.palletized_units}</strong><small>no período</small></article>
        <article className="metric-card"><span>Paletes abertos</span><strong>{data.summary.open_pallets}</strong><small>em montagem</small></article>
        <article className="metric-card"><span>Paletes completos</span><strong>{data.summary.completed_pallets}</strong><small>finalizados</small></article>
      </div>

      <div className="dashboard-grid-two">
        <article className="dashboard-widget">
          <div className="widget-head"><div><h3>Desempenho por hora</h3><p>Produção real por hora e acumulado do dia.{target?.hourly_target ? ` Meta configurada: ${target.hourly_target}/h.` : ''}</p></div></div>
          {data.production_by_hour.length === 0 ? <p className="empty-state">Nenhuma unidade paletizada neste período.</p> : <div className="hourly-chart">{data.production_by_hour.map((item) => {
            const rowStatus = item.hourly_achievement_percent == null ? '' : item.hourly_achievement_percent >= 100 ? 'hour-on-target' : 'hour-below-target'
            const primary = target?.hourly_target ? `${item.quantity}/${target.hourly_target} · ${item.hourly_achievement_percent?.toFixed(0)}%` : `${item.quantity}`
            const cumulative = target?.daily_target && item.daily_achievement_percent != null
              ? `Acum. ${item.cumulative_quantity}/${target.daily_target} · ${item.daily_achievement_percent.toFixed(1)}%`
              : `Acum. ${item.cumulative_quantity}`
            return <div className={`hour-row performance-hour-row ${rowStatus}`} key={item.hour}><span>{item.hour}</span><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(5, item.quantity / maxHourly * 100)}%` }} /></div><div className="hour-values"><strong>{primary}</strong><small>{cumulative}</small></div></div>
          })}</div>}
        </article>

        <article className="dashboard-widget">
          <div className="widget-head"><div><h3>Status das leituras</h3><p>Distribuição das validações do leitor.</p></div></div>
          <div className="status-chart">{data.scan_statuses.map((item) => <button key={item.status} className="status-chart-row" onClick={() => canTraceability && onOpenTraceability(tracePreset(item.status))} disabled={!canTraceability}><span className={`table-status ${item.status.toLowerCase()}`}>{item.status}</span><div className="bar-track"><div className={`bar-fill status-${item.status.toLowerCase()}`} style={{ width: `${item.quantity === 0 ? 0 : Math.max(6, item.quantity / maxStatus * 100)}%` }} /></div><strong>{item.quantity}</strong></button>)}</div>
        </article>
      </div>

      <div className="dashboard-grid-two">
        <article className="dashboard-widget">
          <div className="widget-head"><div><h3>Paletes em andamento</h3><p>Acompanhamento dos paletes abertos.</p></div><strong>{data.open_pallets.length}</strong></div>
          {data.open_pallets.length === 0 ? <p className="empty-state">Nenhum palete aberto para os filtros atuais.</p> : <div className="open-pallet-list">{data.open_pallets.map((pallet) => <div className="open-pallet" key={pallet.id}><div className="open-pallet-head"><div><strong>{pallet.pallet_code}</strong><span>{pallet.line_code} · {pallet.product_model}</span><small>OP {pallet.production_order}</small></div><b>{pallet.current_quantity}/{pallet.target_quantity}</b></div><div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(100, pallet.progress_percent)}%` }} /></div><small>{pallet.progress_percent.toFixed(0)}% preenchido · aberto em {formatDate(pallet.opened_at)}</small></div>)}</div>}
        </article>

        <article className="dashboard-widget">
          <div className="widget-head"><div><h3>Últimas ocorrências</h3><p>Eventos que exigem atenção operacional.</p></div>{canTraceability && data.recent_occurrences.length > 0 && <button className="link-button" onClick={() => onOpenTraceability(tracePreset('OCCURRENCES'))}>Ver todas</button>}</div>
          {data.recent_occurrences.length === 0 ? <p className="empty-state">Nenhuma ocorrência no período selecionado.</p> : <div className="occurrence-list">{data.recent_occurrences.map((item) => <button key={item.id} onClick={() => canTraceability && onOpenTraceability({ ...tracePreset(item.status), serial: item.serial_number ?? '' })} disabled={!canTraceability}><span>{formatLocalTime(item.scanned_at)}</span><span className={`table-status ${item.status.toLowerCase()}`}>{item.status}</span><strong>{item.serial_number ?? 'Sem serial'}</strong><span>{item.line_code}</span><p>{item.error_message ?? 'Ocorrência registrada'}</p></button>)}</div>}
        </article>
      </div>
    </section>
  )
}
