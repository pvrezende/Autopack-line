import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDbHealth, getHealth, listIndicatorThresholds, listPalletConfigs, listProductionTargets } from '../services/api'
import type { IndicatorThreshold, PalletConfig, Product, ProductionLine, ProductionTarget } from '../types/domain'

type Props = { products: Product[]; lines: ProductionLine[]; refreshKey: number }
type Check = { label:string; ok:boolean; detail:string }

export function CoreValidationPanel({ products, lines, refreshKey }: Props) {
  const [lineId,setLineId]=useState<number|''>(''); const [productId,setProductId]=useState<number|''>('')
  const [health,setHealth]=useState(false); const [db,setDb]=useState(false)
  const [targets,setTargets]=useState<ProductionTarget[]>([]); const [pallets,setPallets]=useState<PalletConfig[]>([]); const [thresholds,setThresholds]=useState<IndicatorThreshold[]>([])
  const [loading,setLoading]=useState(false); const [error,setError]=useState('')
  useEffect(()=>{if(lineId===''&&lines.length)setLineId(lines[0].id)},[lines,lineId])
  useEffect(()=>{if(productId===''&&products.length)setProductId(products[0].id)},[products,productId])
  const load=useCallback(async()=>{setLoading(true);setError('');try{
    const [h,d,t,p,i]=await Promise.all([getHealth(),getDbHealth(),listProductionTargets(),listPalletConfigs(),listIndicatorThresholds()])
    setHealth(h.status==='ok'); setDb(d.status==='ok'); setTargets(t); setPallets(p); setThresholds(i)
  }catch(e){setError((e as Error).message);setHealth(false);setDb(false)}finally{setLoading(false)}},[])
  useEffect(()=>{load()},[load,refreshKey])
  const checks=useMemo<Check[]>(()=>{
    const line=lines.find(x=>x.id===lineId), product=products.find(x=>x.id===productId)
    const target=targets.find(x=>x.active&&x.line_id===lineId&&x.product_id===productId) ?? targets.find(x=>x.active&&x.line_id===lineId&&x.product_id==null)
    const pallet=pallets.find(x=>x.active&&x.line_id===lineId&&x.product_id===productId)
    const threshold=thresholds.find(x=>x.active&&x.line_id===lineId&&x.product_id===productId) ?? thresholds.find(x=>x.active&&x.line_id===lineId&&x.product_id==null)
    return [
      {label:'Backend',ok:health,detail:health?'API respondendo normalmente':'API indisponível'},
      {label:'Banco de dados',ok:db,detail:db?'MySQL acessível pelo backend':'MySQL indisponível'},
      {label:'Linha de produção',ok:!!line?.active,detail:line?.active?`${line.code} - ${line.name} ativa`:'Selecione uma linha ativa'},
      {label:'Produto',ok:!!product?.active,detail:product?.active?`${product.model} ativo`:'Selecione um produto ativo'},
      {label:'Meta de produção',ok:!!target,detail:target?`Meta ${target.product_id==null?'geral da linha':'específica do produto'} configurada`:'Cadastre meta/hora, meta diária ou takt'},
      {label:'Quantidade por palete',ok:!!pallet,detail:pallet?`${pallet.max_boxes} caixa(s) por palete`:'Cadastre a capacidade do palete para linha/produto'},
      {label:'Limites dos indicadores',ok:!!threshold,detail:threshold?`Limites ${threshold.product_id==null?'gerais da linha':'específicos do produto'} configurados`:'Cadastre limites de Disponibilidade, Performance, Qualidade e OEE'},
    ]
  },[health,db,lines,products,lineId,productId,targets,pallets,thresholds])
  const ready=checks.filter(c=>c.ok).length
  return <section className="core-validation panel">
    <div className="panel-title-row"><div><p className="eyebrow">FECHAMENTO DO NÚCLEO</p><h2>Validação de prontidão</h2><p className="panel-subtitle">Checklist automático antes das integrações físicas. Nenhum dado é alterado por esta tela.</p></div><span className={`badge ${ready===checks.length?'success':''}`}>{ready}/{checks.length} verificações OK</span></div>
    <div className="alerts-filters core-validation-filters"><label>Linha<select value={lineId} onChange={e=>setLineId(e.target.value?Number(e.target.value):'')}><option value="">Selecione</option>{lines.map(l=><option key={l.id} value={l.id}>{l.code} - {l.name}</option>)}</select></label><label>Produto<select value={productId} onChange={e=>setProductId(e.target.value?Number(e.target.value):'')}><option value="">Selecione</option>{products.map(p=><option key={p.id} value={p.id}>{p.model}</option>)}</select></label><button className="primary" onClick={load} disabled={loading}>{loading?'Verificando...':'Executar validação'}</button></div>
    {error&&<div className="message error">{error}</div>}
    <div className="validation-summary"><strong>{ready===checks.length?'Núcleo funcional pronto para avançar':'Existem pendências de configuração'}</strong><span>{ready===checks.length?'Os requisitos básicos estão disponíveis para iniciar a etapa de integração física.':'Resolva os itens pendentes em Configurações antes da integração física.'}</span></div>
    <div className="validation-grid">{checks.map(c=><article key={c.label} className={c.ok?'validation-ok':'validation-pending'}><div><strong>{c.label}</strong><span>{c.ok?'OK':'PENDENTE'}</span></div><p>{c.detail}</p></article>)}</div>
    <p className="executive-note">Esta validação consulta somente o estado atual do backend, MySQL e parâmetros editáveis. Ela não cria valores fixos e não modifica registros.</p>
  </section>
}
