import { useEffect, useMemo, useState } from 'react'

import { createReworkOrder, getRetestStatus, listRetestHistory, searchRetestUnits, simulateRetest } from '../services/api'
import type { RetestAttempt, RetestDiagnosticStatus, RetestUnit } from '../types/domain'

const decisionLabel: Record<string, string> = { REJECTED: 'Reprovada', APPROVED: 'Aprovada' }
const authorizationLabel: Record<string, string> = {
  PENDING_PROCESS_DEFINITION: 'Regra de processo pendente',
  SIMULATED_AUTHORIZED: 'Reteste autorizado em simulação',
}
const unitStatusLabel: Record<string, string> = {
  SCANNED: 'Lida', VALIDATED: 'Validada', PALLETIZED: 'Paletizada', REJECTED: 'Reprovada',
}

export function RetestFoundationPanel() {
  const [status, setStatus] = useState<RetestDiagnosticStatus | null>(null)
  const [serial, setSerial] = useState('')
  const [search, setSearch] = useState('')
  const [units, setUnits] = useState<RetestUnit[]>([])
  const [history, setHistory] = useState<RetestAttempt[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const selectedUnit = useMemo(
    () => units.find(item => item.serial_number === serial.trim()) ?? null,
    [serial, units],
  )
  const hasRejected = history.some(item => item.decision === 'REJECTED')

  useEffect(() => {
    getRetestStatus().then(setStatus).catch(err => setError((err as Error).message))
    searchRetestUnits('', 20).then(setUnits).catch(err => setError((err as Error).message))
  }, [])

  async function runSearch() {
    setBusy(true); setError(''); setMessage('')
    try {
      const result = await searchRetestUnits(search.trim(), 20)
      setUnits(result)
      if (result.length === 0) setMessage('Nenhuma unidade encontrada para o filtro informado.')
    } catch (err) { setError((err as Error).message) }
    finally { setBusy(false) }
  }

  async function selectUnit(unit: RetestUnit) {
    setSerial(unit.serial_number)
    setHistory([]); setError(''); setMessage('')
    try { setHistory(await listRetestHistory(unit.serial_number)) }
    catch (err) { setError((err as Error).message) }
  }

  async function refreshHistory() {
    if (!selectedUnit) { setError('Selecione uma unidade existente na lista.'); return }
    try {
      setHistory(await listRetestHistory(selectedUnit.serial_number))
      setError(''); setMessage('Histórico atualizado com sucesso.')
    } catch (err) { setHistory([]); setError((err as Error).message) }
  }

  async function run(decision: 'REJECTED' | 'APPROVED') {
    if (!selectedUnit) { setError('Selecione uma unidade existente antes de simular.'); return }
    if (decision === 'APPROVED' && !hasRejected) { setError('A aprovação exige uma reprovação anterior.'); return }
    const action = decision === 'REJECTED' ? 'reprovação' : 'aprovação do reteste'
    if (!window.confirm(`Confirmar simulação de ${action} para ${selectedUnit.serial_number}?\n\nA produção e o palete não serão alterados.`)) return
    setBusy(true); setError(''); setMessage('')
    try {
      const result = await simulateRetest({
        serial_number: selectedUnit.serial_number,
        decision,
        authorized_for_retest: decision === 'APPROVED',
        reason_code: 'OFFLINE_VALIDATION',
        reason_text: 'Validação controlada da ETAPA 7.32',
        idempotency_key: `ui-${selectedUnit.serial_number}-${decision}-${Date.now()}`,
      })
      setMessage(result.message)
      setHistory(await listRetestHistory(selectedUnit.serial_number))
      setUnits(await searchRetestUnits(search.trim(), 20))
    } catch (err) { setError((err as Error).message) }
    finally { setBusy(false) }
  }

  async function openRework() {
    if (!selectedUnit) return
    const reason = window.prompt('Informe o motivo obrigatório da ordem de retrabalho:')?.trim()
    if (!reason) return
    setBusy(true); setError(''); setMessage('')
    try {
      const item = await createReworkOrder({ serial_number:selectedUnit.serial_number, reason })
      setMessage(`Ordem de retrabalho #${item.id} aberta e vinculada à unidade original.`)
    } catch (err) { setError((err as Error).message) }
    finally { setBusy(false) }
  }

  return <section className="panel retest-foundation-panel">
    <details>
      <summary>
        <span><strong>Reteste offline — consulta e simulação controlada</strong><small>Seleção de unidades, histórico auditável e proteção da produção</small></span>
        <span className="retest-summary-actions"><span className={`badge ${status?.real_retest_enabled ? 'warning' : 'success'}`}>{status?.real_retest_enabled ? 'REAL HABILITADO' : 'REAL BLOQUEADO'}</span><span className="retest-toggle" aria-hidden="true" /></span>
      </summary>
      <div className="retest-foundation-content">
        <div className="retest-status-strip">
          <span><small>ETAPA</small><strong>{status?.stage ?? '7.32'}</strong></span>
          <span><small>MODO</small><strong>{status?.mode ?? 'carregando...'}</strong></span>
          <span><small>SIMULADOR</small><strong>{status?.simulator_enabled ? 'LIBERADO' : 'BLOQUEADO'}</strong></span>
          <span><small>SOCKET FÍSICO</small><strong>NÃO UTILIZADO</strong></span>
        </div>
        <p>{status?.message}</p>
        <div className="retest-search-box">
          <label>Buscar por serial, OP ou modelo<input value={search} onChange={event => setSearch(event.target.value)} onKeyDown={event => { if (event.key === 'Enter') runSearch() }} placeholder="Ex.: ARC8814, 000001275033 ou HJFE12C2CG" /></label>
          <button className="secondary" disabled={busy} onClick={runSearch}>Buscar unidades</button>
        </div>
        <div className="retest-unit-list">
          {units.map(unit => <button key={unit.id} type="button" className={selectedUnit?.id === unit.id ? 'selected' : ''} onClick={() => selectUnit(unit)}>
            <strong>{unit.serial_number}</strong><span>{unit.product_model} · OP {unit.production_order}</span>
            <small>{unitStatusLabel[unit.unit_status] ?? unit.unit_status} · {unit.attempt_count} tentativa(s){unit.last_decision ? ` · última: ${decisionLabel[unit.last_decision]}` : ''}</small>
          </button>)}
        </div>
        {selectedUnit && <div className="retest-selected-unit">
          <span><small>SERIAL</small><strong>{selectedUnit.serial_number}</strong></span><span><small>PRODUTO</small><strong>{selectedUnit.product_model}</strong></span>
          <span><small>ORDEM DE PRODUÇÃO</small><strong>{selectedUnit.production_order}</strong></span><span><small>ESTADO PRESERVADO</small><strong>{unitStatusLabel[selectedUnit.unit_status] ?? selectedUnit.unit_status}</strong></span>
        </div>}
        <div className="retest-controls">
          <button className="secondary" disabled={busy || !selectedUnit} onClick={refreshHistory}>Atualizar histórico</button>
          <button className="danger" disabled={busy || !selectedUnit} onClick={() => run('REJECTED')}>Simular reprovação</button>
          <button className="primary" disabled={busy || !selectedUnit || !hasRejected} onClick={() => run('APPROVED')}>Simular reteste aprovado</button>
          <button className="secondary" disabled={busy || !selectedUnit || selectedUnit.unit_status !== 'PALLETIZED'} onClick={openRework}>Abrir retrabalho</button>
        </div>
        {selectedUnit && !hasRejected && <div className="message warning">A aprovação permanece bloqueada até existir uma reprovação anterior para esta unidade.</div>}
        {error && <div className="message error">{error}</div>}{message && <div className="message success">{message}</div>}
        <div className="retest-history">
          {history.length === 0 ? <small>Nenhuma tentativa registrada para a unidade selecionada.</small> : history.map(item => <div key={item.id}>
            <strong>#{item.attempt_number} · {decisionLabel[item.decision] ?? item.decision}</strong>
            <span>Simulador · {authorizationLabel[item.authorization_status] ?? item.authorization_status}</span>
            <small>{new Date(item.created_at).toLocaleString('pt-BR')} · não contabilizada na produção</small>
          </div>)}
        </div>
        <small>Limite provisório configurado: {status?.max_attempts ?? 2} tentativa(s). Unidade paletizada usa somente ordem de retrabalho.</small>
        <details className="compact-details"><summary>Regras de segurança e definições pendentes</summary>
          <div className="retest-rules"><ul>{status?.safety_rules.map(rule => <li key={rule}>{rule}</li>)}</ul><ul>{status?.pending_definitions.map(rule => <li key={rule}>{rule}</li>)}</ul></div>
        </details>
      </div>
    </details>
  </section>
}
