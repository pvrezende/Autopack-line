import { useCallback, useEffect, useState } from 'react'

import { confirmMesNgRemoval, getMesQualityStatus, listMesQualityIncidents } from '../services/api'
import type { MesQualityIncident, MesQualityStatus, UserAccount } from '../types/domain'

export function MesQualityAlertsPanel({ user, refreshKey = 0 }:{ user:UserAccount; refreshKey?:number }) {
  const [status, setStatus] = useState<MesQualityStatus | null>(null)
  const [items, setItems] = useState<MesQualityIncident[]>([])
  const [error, setError] = useState('')
  const canResolve = user.role === 'ADMIN' || user.role === 'SUPERVISOR'

  const load = useCallback(async () => {
    try {
      const [nextStatus, nextItems] = await Promise.all([getMesQualityStatus(), listMesQualityIncidents()])
      setStatus(nextStatus); setItems(nextItems); setError('')
    } catch (err) { setError((err as Error).message) }
  }, [])

  useEffect(() => { load(); const timer = window.setInterval(load, 5000); return () => window.clearInterval(timer) }, [load, refreshKey])

  async function resolve(item:MesQualityIncident) {
    const note = window.prompt(`Confirme a retirada do serial ${item.serial_number}, palete ${item.pallet_code}, posição ${item.pallet_position}.\nInforme a observação:`)?.trim()
    if (!note) return
    try { await confirmMesNgRemoval(item.id, note); await load() }
    catch (err) { setError((err as Error).message) }
  }

  return <section className={`mes-quality-panel ${items.length ? 'has-ng' : ''}`}>
    <div className="mes-quality-heading">
      <div><p className="eyebrow">QUALIDADE MES</p><h2>{items.length ? `${items.length} NG aguardando retirada` : 'Nenhum NG pendente no palete'}</h2></div>
      <span className={`badge ${items.length ? 'warning' : 'success'}`}>{items.length ? 'PALETE SOB INSPEÇÃO' : 'LIBERADO'}</span>
    </div>
    <p>{status?.message ?? 'Carregando situação do MES...'}</p>
    {error && <div className="message error">{error}</div>}
    {items.map(item => <article className="mes-ng-item" key={item.id}>
      <strong>NG — retirar a unidade da posição {item.pallet_position}</strong>
      <span>Serial <b>{item.serial_number}</b> · Modelo {item.product_model} · OP {item.production_order}</span>
      <span>Palete <b>{item.pallet_code}</b> · ordem/posição <b>{item.pallet_position}</b></span>
      <small>A linha continua operando. O alerta só encerra após a retirada confirmada.</small>
      {canResolve && <button className="danger" onClick={() => resolve(item)}>Confirmar retirada do palete</button>}
    </article>)}
    <small>Modo: {status?.mode ?? '—'} · Conexão real Elgin: {status?.endpoint_configured ? 'configurada' : 'aguardando contrato'}</small>
  </section>
}
