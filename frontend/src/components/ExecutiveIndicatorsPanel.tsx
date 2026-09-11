import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDashboardOperational, getOeeHistory } from '../services/api'
import type { DashboardIndicatorClassification, DashboardOEEHistory, DashboardOperational, Product, ProductionLine } from '../types/domain'
import { periodRange } from '../utils/dateRange'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }
type Metric = { key:string; label:string; current:DashboardIndicatorClassification|null; historyKey:'availability_percent'|'performance_percent'|'quality_percent'|'oee_percent' }
const statusLabel = (s?: string) => s === 'CRITICAL' ? 'CRÍTICO' : s === 'WARNING' ? 'ATENÇÃO' : s === 'OK' ? 'OK' : 'SEM DADOS'
const fmt = (v:number|null|undefined) => v == null ? '—' : `${v.toFixed(1)}%`

export function ExecutiveIndicatorsPanel({ products, lines, refreshKey }: Props) {
  const [lineId,setLineId]=useState<number|''>(''); const [productId,setProductId]=useState<number|''>('')
  const [current,setCurrent]=useState<DashboardOperational|null>(null); const [history,setHistory]=useState<DashboardOEEHistory|null>(null)
  const [loading,setLoading]=useState(false); const [error,setError]=useState('')
  useEffect(()=>{ if(lineId==='' && lines.length) setLineId(lines[0].id) },[lines,lineId])
  const load=useCallback(async()=>{ if(lineId==='') return; setLoading(true); setError(''); try {
    const now=new Date(), start=new Date(); start.setDate(now.getDate()-6)
    const dateOnly=(d:Date)=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    const [op,hist]=await Promise.all([
      getDashboardOperational({line_id:lineId,product_id:productId===''?undefined:productId,...periodRange('today','','')}),
      getOeeHistory({line_id:lineId,product_id:productId===''?undefined:productId,date_from:dateOnly(start),date_to:dateOnly(now)})
    ]); setCurrent(op); setHistory(hist)
  } catch(e){setError((e as Error).message)} finally{setLoading(false)} },[lineId,productId])
  useEffect(()=>{load()},[load,refreshKey])
  const a=current?.indicator_alerts
  const metrics:Metric[]=[
    {key:'availability',label:'Disponibilidade',current:a?.availability??null,historyKey:'availability_percent'},
    {key:'performance',label:'Performance',current:a?.performance??null,historyKey:'performance_percent'},
    {key:'quality',label:'Qualidade',current:a?.quality??null,historyKey:'quality_percent'},
    {key:'oee',label:'OEE',current:a?.oee??null,historyKey:'oee_percent'},
  ]
  const executive=useMemo(()=>metrics.map(m=>{
    const vals=(history?.points??[]).map(p=>p[m.historyKey]).filter((v):v is number=>v!=null)
    const avg=vals.length?vals.reduce((x,y)=>x+y,0)/vals.length:null
    return {...m,avg,days:vals.length}
  }),[history,a])
  const priorities=executive.filter(m=>m.current?.status==='CRITICAL'||m.current?.status==='WARNING')
  const overall=a?.overall_status ?? 'NO_DATA'
  return <section className="executive-panel panel">
    <div className="panel-title-row"><div><p className="eyebrow">INDICADORES</p><h2>Resumo executivo</h2><p className="panel-subtitle">Visão consolidada para decisão: situação de hoje, média dos últimos 7 dias e prioridades operacionais.</p></div><span className="badge success">dados calculados no MySQL</span></div>
    <div className="alerts-filters executive-filters">
      <label>Linha<select value={lineId} onChange={e=>setLineId(e.target.value?Number(e.target.value):'')}><option value="">Selecione</option>{lines.map(l=><option key={l.id} value={l.id}>{l.code} - {l.name}</option>)}</select></label>
      <label>Produto<select value={productId} onChange={e=>setProductId(e.target.value?Number(e.target.value):'')}><option value="">Todos</option>{products.map(p=><option key={p.id} value={p.id}>{p.model}</option>)}</select></label>
      <div className={`executive-overall status-${String(overall).toLowerCase()}`}><span>Situação geral de hoje</span><strong>{statusLabel(overall)}</strong></div>
      <button className="primary" onClick={load} disabled={loading||lineId===''}>{loading?'Atualizando...':'Atualizar resumo'}</button>
    </div>
    {error&&<div className="message error">{error}</div>}
    {a?.status==='NO_CONFIG'&&<div className="message warning">Configure os limites dos indicadores para habilitar a classificação executiva.</div>}
    <div className="executive-metrics">{executive.map(m=><article key={m.key} className={`executive-metric status-${(m.current?.status??'NO_DATA').toLowerCase()}`}><div><span>{m.label}</span><b>{statusLabel(m.current?.status)}</b></div><strong>{fmt(m.current?.value)}</strong><p>Média 7 dias: <b>{fmt(m.avg)}</b> · {m.days} dia(s) com dado</p></article>)}</div>
    <div className="executive-grid">
      <section className="executive-card"><div className="alerts-section-head"><div><h3>Prioridades de hoje</h3><p>Itens que exigem acompanhamento conforme os limites cadastrados.</p></div><strong>{priorities.length}</strong></div>{priorities.length?<ol className="executive-priorities">{priorities.map(m=><li key={m.key}><div><strong>{m.label}</strong><span className={`trend-status status-${m.current!.status.toLowerCase()}`}>{statusLabel(m.current!.status)}</span></div><p>Atual {fmt(m.current!.value)} · atenção abaixo de {fmt(m.current!.warning_threshold)} · crítico abaixo de {fmt(m.current!.critical_threshold)}</p></li>)}</ol>:<p className="empty-note">Nenhuma prioridade aberta pelos indicadores configurados.</p>}</section>
      <section className="executive-card"><div className="alerts-section-head"><div><h3>Contexto de produção</h3><p>Resumo operacional do período de hoje.</p></div></div><div className="executive-context"><div><span>Produzido</span><strong>{current?.summary.palletized_units??0}</strong></div><div><span>Leituras válidas</span><strong>{current?.summary.valid_scans??0}/{current?.summary.total_scans??0}</strong></div><div><span>Ocorrências</span><strong>{current?.summary.invalid_scans??0}</strong></div><div><span>Eficiência</span><strong>{fmt(current?.efficiency?.operational_efficiency_percent)}</strong></div><div><span>Paradas não planejadas</span><strong>{current?.efficiency?`${current.efficiency.unplanned_downtime_minutes} min`:'—'}</strong></div><div><span>Paletes abertos</span><strong>{current?.summary.open_pallets??0}</strong></div></div></section>
    </div>
    <p className="executive-note">Este resumo não altera metas, limites ou registros históricos. Use as demais abas de Indicadores para investigar cada resultado em detalhe.</p>
  </section>
}
