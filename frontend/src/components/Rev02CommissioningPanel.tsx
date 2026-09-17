import { useEffect, useState } from 'react'
import { getPlcRev02 } from '../services/api'
import type { PlcRev02Diagnostic } from '../types/domain'

export function Rev02CommissioningPanel() {
  const [data, setData] = useState<PlcRev02Diagnostic | null>(null)
  const [error, setError] = useState('')

  useEffect(() => { getPlcRev02().then(setData).catch(err => setError((err as Error).message)) }, [])

  return <section className="panel rev02-panel">
    <details open>
      <summary><span><strong>Contrato Modbus Rev.02 — preparação para comunicação real</strong><small>D700–D779 + leitor D800–D879 · Ladder Rev.04</small></span><span className="retest-summary-actions"><span className="badge warning">FÍSICO BLOQUEADO</span><span className="retest-toggle" /></span></summary>
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
