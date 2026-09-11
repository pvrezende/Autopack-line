import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { createProductionOrder, listProductionOrders, transitionProductionOrder, updateProductionOrder } from '../services/api'
import type { Product, ProductionLine, ProductionOrder, UserAccount } from '../types/domain'
import { formatLocalDateTime } from '../utils/dateTime'

type Props = { products: Product[]; lines: ProductionLine[]; user: UserAccount; onChanged: () => void }
const statusLabel: Record<string, string> = { OPEN: 'ABERTA', ACTIVE: 'ATIVA', PAUSED: 'PAUSADA', COMPLETED: 'FINALIZADA', CANCELLED: 'CANCELADA' }

export function ProductionOrdersPanel({ products, lines, user, onChanged }: Props) {
  const [items, setItems] = useState<ProductionOrder[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [status, setStatus] = useState('')
  const [lineId, setLineId] = useState('')
  const [productId, setProductId] = useState('')
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<ProductionOrder | null>(null)
  const [form, setForm] = useState({ order_number: '', product_id: '', line_id: '', lot_code: '', planned_quantity: '', notes: '' })
  const canManage = user.role === 'ADMIN'
  const canOperate = user.role === 'ADMIN' || user.role === 'SUPERVISOR'

  async function load(targetPage = page) {
    try {
      const data = await listProductionOrders({ page: targetPage, page_size: 6, status: status || undefined, line_id: lineId ? Number(lineId) : undefined, product_id: productId ? Number(productId) : undefined, search: search || undefined })
      setItems(data.items); setTotal(data.total); setTotalPages(data.total_pages); setPage(data.page); setError('')
    } catch (e) { setError((e as Error).message) }
  }
  useEffect(() => { load(1) }, [])

  const activeCount = useMemo(() => items.filter(x => x.status === 'ACTIVE').length, [items])

  function resetForm() {
    setEditing(null); setForm({ order_number: '', product_id: '', line_id: '', lot_code: '', planned_quantity: '', notes: '' })
  }
  function edit(item: ProductionOrder) {
    setEditing(item); setForm({ order_number: item.order_number, product_id: String(item.product_id), line_id: item.line_id ? String(item.line_id) : '', lot_code: item.lot_code ?? '', planned_quantity: item.planned_quantity ? String(item.planned_quantity) : '', notes: item.notes ?? '' }); setFormOpen(true)
  }
  async function save(e: FormEvent) {
    e.preventDefault(); setError(''); setSuccess('')
    if (!form.product_id) { setError('Selecione o produto'); return }
    const payload = { product_id: Number(form.product_id), line_id: form.line_id ? Number(form.line_id) : undefined, lot_code: form.lot_code || undefined, planned_quantity: form.planned_quantity ? Number(form.planned_quantity) : undefined, notes: form.notes || undefined }
    try {
      if (editing) await updateProductionOrder(editing.id, payload)
      else {
        if (!form.order_number.trim()) { setError('Informe o número da OP'); return }
        await createProductionOrder({ order_number: form.order_number.trim(), ...payload })
      }
      setSuccess(editing ? 'OP atualizada com sucesso' : 'OP cadastrada com sucesso'); resetForm(); setFormOpen(false); await load(1); onChanged()
    } catch (e) { setError((e as Error).message) }
  }
  async function transition(item: ProductionOrder, action: 'start' | 'pause' | 'finish' | 'cancel') {
    const verbs = { start: 'iniciar', pause: 'pausar', finish: 'finalizar', cancel: 'cancelar' }
    if ((action === 'finish' || action === 'cancel') && !window.confirm(`Confirma ${verbs[action]} a OP ${item.order_number}?`)) return
    try { await transitionProductionOrder(item.id, action); setSuccess(`OP ${verbs[action]}: operação concluída`); setError(''); await load(page); onChanged() } catch (e) { setError((e as Error).message) }
  }

  return <section className="panel production-orders-panel">
    <div className="panel-heading"><div><p className="eyebrow">PRODUÇÃO</p><h2>Ordens de Produção (OP)</h2></div><div className="panel-heading-actions"><span className="badge success">{total} OP(s)</span>{canManage && <button className="secondary small" onClick={() => { if (formOpen) resetForm(); setFormOpen(v => !v) }}>☰ {formOpen ? 'Fechar cadastro' : 'Nova OP'}</button>}</div></div>
    {error && <div className="message error">{error}</div>}{success && <div className="message success">{success}</div>}

    {formOpen && canManage && <form className="op-form" onSubmit={save}>
      <div className="field"><label>Número da OP</label><input value={form.order_number} disabled={!!editing} onChange={e => setForm(v => ({...v, order_number:e.target.value}))} placeholder="Ex.: 000001275033" /></div>
      <div className="field"><label>Produto</label><select value={form.product_id} onChange={e => setForm(v => ({...v, product_id:e.target.value}))}><option value="">Selecione</option>{products.map(p => <option key={p.id} value={p.id}>{p.model} · {p.name}</option>)}</select></div>
      <div className="field"><label>Linha</label><select value={form.line_id} onChange={e => setForm(v => ({...v, line_id:e.target.value}))}><option value="">Sem linha definida</option>{lines.map(l => <option key={l.id} value={l.id}>{l.code} · {l.name}</option>)}</select></div>
      <div className="field"><label>Lote</label><input value={form.lot_code} onChange={e => setForm(v => ({...v, lot_code:e.target.value}))} /></div>
      <div className="field"><label>Quantidade planejada</label><input type="number" min="1" value={form.planned_quantity} onChange={e => setForm(v => ({...v, planned_quantity:e.target.value}))} /></div>
      <div className="field op-notes"><label>Observações</label><input value={form.notes} onChange={e => setForm(v => ({...v, notes:e.target.value}))} /></div>
      <div className="op-form-actions"><button className="primary" type="submit">{editing ? 'Salvar alterações' : 'Cadastrar OP'}</button>{editing && <button className="secondary" type="button" onClick={() => { resetForm(); setFormOpen(false) }}>Cancelar edição</button>}</div>
    </form>}

    <div className="op-filters">
      <div className="field"><label>Status</label><select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Todos</option><option value="OPEN">Aberta</option><option value="ACTIVE">Ativa</option><option value="PAUSED">Pausada</option><option value="COMPLETED">Finalizada</option><option value="CANCELLED">Cancelada</option></select></div>
      <div className="field"><label>Linha</label><select value={lineId} onChange={e=>setLineId(e.target.value)}><option value="">Todas</option>{lines.map(l=><option key={l.id} value={l.id}>{l.code}</option>)}</select></div>
      <div className="field"><label>Produto</label><select value={productId} onChange={e=>setProductId(e.target.value)}><option value="">Todos</option>{products.map(p=><option key={p.id} value={p.id}>{p.model}</option>)}</select></div>
      <div className="field"><label>Buscar OP</label><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Número da OP" /></div>
      <button className="primary" onClick={()=>load(1)}>Aplicar filtros</button><button className="secondary" onClick={()=>{setStatus('');setLineId('');setProductId('');setSearch('');setTimeout(()=>load(1),0)}}>Limpar</button>
    </div>

    <div className="op-summary"><span><strong>{activeCount}</strong> ativa(s) nesta página</span><span>A leitura QR agora exige OP <strong>ATIVA</strong>.</span></div>
    <div className="table-wrap"><table className="op-table"><thead><tr><th>OP</th><th>PRODUTO</th><th>LINHA</th><th>PLANEJADO</th><th>PRODUZIDO CONFIRMADO</th><th>PROGRESSO</th><th>STATUS</th><th>AÇÕES</th></tr></thead><tbody>
      {items.length === 0 && <tr><td colSpan={8}>Nenhuma OP encontrada.</td></tr>}
      {items.map(item => <tr key={item.id}><td><strong>{item.order_number}</strong><small>{item.lot_code ? `Lote ${item.lot_code}` : item.source}</small></td><td>{item.product_model ?? `#${item.product_id}`}<small>{item.product_name}</small></td><td>{item.line_code ?? '—'}</td><td>{item.planned_quantity ?? '—'}</td><td>{item.produced_quantity}<small>{item.scanned_quantity} leitura(s) válida(s)</small></td><td><div className="op-progress"><span style={{width:`${item.progress_percent}%`}}></span></div><small>{item.progress_percent}% · {item.open_pallets} aberto(s) / {item.completed_pallets} completo(s)</small></td><td><span className={`op-status ${item.status.toLowerCase()}`}>{statusLabel[item.status] ?? item.status}</span></td><td><div className="op-actions">{canManage && !['COMPLETED','CANCELLED'].includes(item.status) && <button className="secondary tiny" onClick={()=>edit(item)}>Editar</button>}{canOperate && ['OPEN','PAUSED'].includes(item.status) && <button className="primary tiny" onClick={()=>transition(item,'start')}>Iniciar</button>}{canOperate && item.status==='ACTIVE' && <button className="secondary tiny" onClick={()=>transition(item,'pause')}>Pausar</button>}{canOperate && !['COMPLETED','CANCELLED'].includes(item.status) && <button className="secondary tiny" onClick={()=>transition(item,'finish')}>Finalizar</button>}{canManage && !['COMPLETED','CANCELLED'].includes(item.status) && <button className="danger tiny" onClick={()=>transition(item,'cancel')}>Cancelar</button>}</div></td></tr>)}
    </tbody></table></div>
    <div className="pagination-row"><span>Mostrando até 6 por página · {total} registro(s)</span><div><button className="secondary small" disabled={page<=1} onClick={()=>load(page-1)}>Anterior</button><strong>Página {page} de {totalPages}</strong><button className="secondary small" disabled={page>=totalPages} onClick={()=>load(page+1)}>Próxima</button></div></div>
  </section>
}
