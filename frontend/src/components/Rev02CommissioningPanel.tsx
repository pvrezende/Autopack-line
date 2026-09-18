import { useEffect, useState } from 'react'
import { exportPlcTransactionsCsv, getPlcExternalSimulator, getPlcRev02, probePlcExternalSimulator } from '../services/api'
import type { PlcExternalSimulatorDiagnostic, PlcRev02Diagnostic } from '../types/domain'

export function Rev02CommissioningPanel() {
  const [data, setData] = useState<PlcRev02Diagnostic | null>(null)
  const [error, setError] = useState('')
  const [external, setExternal] = useState<PlcExternalSimulatorDiagnostic | null>(null)
  const [externalError, setExternalError] = useState('')
  const [probing, setProbing] = useState(false)

  useEffect(() => {
    getPlcRev02().then(setData).catch(err => setError((err as Error).message))
    getPlcExternalSimulator().then(setExternal).catch(err => setExternalError((err as Error).message))
  }, [])

  async function probeExternal() {
    setProbing(true); setExternalError('')
    try { setExternal(await probePlcExternalSimulator()) }
    catch (err) { setExternalError((err as Error).message) }
    finally { setProbing(false) }
  }

  async function exportTransactions() {
    try {
      const blob = await exportPlcTransactionsCsv()
      const url = URL.createObjectURL(blob); const link = document.createElement('a')
      link.href = url; link.download = 'autopackline_transacoes_modbus.csv'; link.click(); URL.revokeObjectURL(url)
    } catch (err) { setExternalError((err as Error).message) }
  }

  return <section className="panel rev02-panel">
    <div className="external-simulator-card">
      <div className="external-simulator-heading">
        <span><strong>Teste Modbus com o CLP-Simulator</strong><small>Leitura real pela rede local, sem dados mockados e sem escrever no CLP físico.</small></span>
        <span className={`badge ${external?.connected ? 'green' : 'amber'}`}>{external?.connected ? 'CONECTADO' : 'AGUARDANDO TESTE'}</span>
      </div>
      {externalError && <div className="message error">{externalError}</div>}
      {external && <>
        <div className="reader-diagnostic-grid">
          <div><span>Perfil</span><strong>{external.enabled ? 'HABILITADO' : 'DESABILITADO'}</strong><small>{external.adapter}</small></div>
          <div><span>Destino Modbus</span><strong>{external.target.host}:{external.target.port}</strong><small>Unit ID {external.target.unit_id}</small></div>
          <div><span>Último teste</span><strong>{external.probe ?? 'AINDA NÃO EXECUTADO'}</strong><small>{external.identity_valid === false ? 'identidade incompatível' : external.connection_attempted ? 'conexão solicitada pelo usuário' : 'nenhum socket foi aberto'}</small></div>
          <div><span>Segurança</span><strong>{external.write_enabled ? 'ESCRITA HABILITADA' : 'SOMENTE LEITURA'}</strong><small>CLP físico {external.physical_plc_enabled ? 'habilitado' : 'bloqueado'}</small></div>
        </div>
        <div className="external-simulator-actions">
          <button disabled={probing || !external.enabled} onClick={probeExternal}>{probing ? 'Lendo registradores...' : 'Testar conexão e leitura Modbus'}</button>
          <button className="secondary" onClick={exportTransactions}>Exportar transações Modbus</button>
          <small>Primeiro publique um código na seção SR-1000 do CLP-Simulator. Depois volte aqui e clique neste botão.</small>
        </div>
        {external.connected && <div className="message success"><strong>Comunicação confirmada.</strong> {external.probe} · Heartbeat {external.handshake?.plc_heartbeat ?? '—'} · Máquina {external.handshake?.machine_state_text ?? '—'}.</div>}
        {external.reader && <div className="external-reader-result">
          <strong>Última leitura SR-1000 recebida via Modbus</strong>
          <div className="reader-diagnostic-grid">
            <div><span>Resultado</span><strong>{external.reader.result_name}</strong><small>sequência {external.reader.sequence}</small></div>
            <div><span>Serial</span><strong>{external.reader.serial || '—'}</strong></div>
            <div><span>EAN</span><strong>{external.reader.ean || '—'}</strong></div>
            <div><span>Ordem / modelo</span><strong>{external.reader.production_order || '—'} / {external.reader.model || '—'}</strong></div>
          </div>
          <code>{external.reader.raw}</code>
        </div>}
      </>}
      {!external && !externalError && <p>Carregando configuração do simulador...</p>}
    </div>

    <details>
      <summary><span><strong>Detalhes do contrato Modbus Rev.02</strong><small>D700–D779 + leitor D800–D879 · Ladder Rev.04</small></span><span className="retest-summary-actions"><span className="badge warning">FÍSICO BLOQUEADO</span><span className="retest-toggle" /></span></summary>
      <div className="rev02-content">
        {error && <div className="message error">{error}</div>}
        {!data ? !error && <p>Carregando contrato Rev.02...</p> : <>
          <div className="retest-status-strip">
            <span><small>ETAPA</small><strong>{data.stage}</strong></span>
            <span><small>CLP</small><strong>{data.connection.host}:{data.connection.port}</strong></span>
            <span><small>UNIT ID</small><strong>{data.connection.unit_id}</strong></span>
            <span><small>SOCKET</small><strong>{data.connection.socket_opened ? 'ABERTO' : 'NÃO ABERTO'}</strong></span>
          </div>
          <div className="message success"><strong>Preparação offline ativa.</strong> {data.message}</div>
          <div className="reader-diagnostic-grid">
            <div><span>Ladder de referência</span><strong>Rev.{data.ladder.revision} · {data.ladder.file}</strong><small>D750={data.identity_probe.D750} · D764={data.identity_probe.D764} · D765={data.identity_probe.D765} · D766={data.identity_probe.D766}</small></div>
            <div><span>Rede reservada</span><strong>PC {data.connection.pc_ip}/24</strong><small>CLP {data.connection.host} · máscara {data.connection.netmask}</small></div>
            <div><span>Mapa principal</span><strong>{data.ranges.pc_to_plc} / {data.ranges.plc_status}</strong><small>endereço base configurável: {data.connection.address_base}</small></div>
            <div><span>Bloco SR-1000</span><strong>{data.ranges.reader}</strong><small>auditoria: {data.reader.audit_source}</small></div>
            <div><span>Teste ASCII</span><strong>{data.ab12.text} = {data.ab12.words.join(' / ')}</strong><small>{data.ab12.confirmed_order} · configurável até validação física</small></div>
            <div><span>Reteste no CLP</span><strong>{data.retest.authorized_flag} + {data.retest.original_sequence}</strong><small>histórico e autorização: {data.retest.history_authority}</small></div>
          </div>
          <details className="compact-details"><summary>Estados oficiais da máquina ({data.machine_states.length})</summary><div className="rev02-chip-grid">{data.machine_states.map(item => <span key={item.code}><strong>{item.code}</strong>{item.label}</span>)}</div></details>
          <details className="compact-details"><summary>Receitas e liberação física</summary><div className="rev02-chip-grid">{data.recipes.map(item => <span key={item.id} className={item.released ? 'released' : 'pending'}><strong>{item.id}</strong>{item.name}<small>{item.released ? 'LIBERADA' : 'AGUARDA VALIDAÇÃO'}</small></span>)}</div></details>
          <details className="compact-details"><summary>Capacidades anunciadas por D777</summary><div className="rev02-chip-grid">{Object.entries(data.reader.features).map(([name, active]) => <span key={name} className={active ? 'released' : 'pending'}><strong>{active ? 'ATIVA' : 'INATIVA'}</strong>{name}</span>)}</div><small>Com D777=3, zeros do leitor não são tratados como leituras reais.</small></details>
          <details className="compact-details"><summary>Gates para habilitar a leitura física</summary><ul className="rev02-gates">{data.safety_gates.map(gate => <li key={gate}>{gate}</li>)}</ul></details>
        </>}
      </div>
    </details>
  </section>
}
