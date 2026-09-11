import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { createUser, deleteUser, listAuditLogs, listUsers, updateUser } from '../services/api'
import type { AuditLog, UserAccount, UserRole } from '../types/domain'
import { formatLocalDateTime } from '../utils/dateTime'
import { isDateInPeriod, type PeriodFilter } from '../utils/dateRange'

const actionLabel: Record<string, string> = {
  LOGIN: 'Login', LOGIN_FAILED: 'Falha de login', USER_CREATED: 'Usuário criado', USER_UPDATED: 'Usuário alterado', USER_DELETED: 'Usuário excluído',
  PASSWORD_CHANGED: 'Senha alterada', SCAN_EXECUTED: 'Leitura executada', PALLETIZE_CONFIRMED: 'Paletização confirmada',
  LINE_CREATED: 'Linha criada', PALLET_CONFIG_CHANGED: 'Configuração de palete', PRODUCTION_TARGET_CHANGED: 'Meta alterada',
}

export function UserManagementPanel({ currentUser }: { currentUser: UserAccount }) {
  const [users, setUsers] = useState<UserAccount[]>([])
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [form, setForm] = useState({ username: '', full_name: '', password: '', role: 'OPERATOR' as UserRole })
  const [editing, setEditing] = useState<UserAccount | null>(null)
  const [editForm, setEditForm] = useState({ username: '', full_name: '', role: 'OPERATOR' as UserRole, active: true })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [userPage, setUserPage] = useState(1)
  const [auditPage, setAuditPage] = useState(1)
  const [adminToolsOpen, setAdminToolsOpen] = useState(false)
  const [auditPeriod, setAuditPeriod] = useState<PeriodFilter>('today')
  const [auditFrom, setAuditFrom] = useState('')
  const [auditTo, setAuditTo] = useState('')
  const userPageSize = 3
  const auditPageSize = 4

  async function refresh() {
    try {
      const [u, l] = await Promise.all([listUsers(), listAuditLogs(500)])
      setUsers(u); setLogs(l); setError('')
    } catch (e) { setError((e as Error).message) }
  }

  useEffect(() => { refresh() }, [])

  const filteredLogs = useMemo(() => logs.filter(log => isDateInPeriod(log.created_at, auditPeriod, auditFrom, auditTo)), [logs, auditPeriod, auditFrom, auditTo])
  const userTotalPages = Math.max(1, Math.ceil(users.length / userPageSize))
  const auditTotalPages = Math.max(1, Math.ceil(filteredLogs.length / auditPageSize))
  const visibleUsers = users.slice((userPage - 1) * userPageSize, userPage * userPageSize)
  const visibleLogs = filteredLogs.slice((auditPage - 1) * auditPageSize, auditPage * auditPageSize)

  useEffect(() => { if (userPage > userTotalPages) setUserPage(userTotalPages) }, [userPage, userTotalPages])
  useEffect(() => { if (auditPage > auditTotalPages) setAuditPage(auditTotalPages) }, [auditPage, auditTotalPages])
  useEffect(() => { setAuditPage(1) }, [auditPeriod, auditFrom, auditTo])

  async function add(e: FormEvent) {
    e.preventDefault(); setMessage('')
    try {
      await createUser(form)
      setForm({ username: '', full_name: '', password: '', role: 'OPERATOR' })
      setMessage('Usuário criado com sucesso')
      await refresh()
    } catch (err) { setError((err as Error).message) }
  }

  function openEdit(user: UserAccount) {
    setEditing(user)
    setEditForm({ username: user.username, full_name: user.full_name, role: user.role, active: user.active })
    setError(''); setMessage('')
  }

  async function saveEdit(e: FormEvent) {
    e.preventDefault()
    if (!editing) return
    try {
      const saved = await updateUser(editing.id, editForm)
      setEditing(null)
      setMessage(`Dados de ${saved.username} atualizados com sucesso`)
      await refresh()
    } catch (err) { setError((err as Error).message) }
  }

  async function change(user: UserAccount, patch: { role?: UserRole; active?: boolean }) {
    try { await updateUser(user.id, patch); await refresh() } catch (err) { setError((err as Error).message) }
  }

  async function resetPassword(user: UserAccount) {
    const password = window.prompt(`Nova senha para ${user.username} (mínimo 8 caracteres):`)
    if (!password) return
    try {
      await updateUser(user.id, { password })
      setMessage(`Senha de ${user.username} redefinida`)
      await refresh()
    } catch (err) { setError((err as Error).message) }
  }

  async function removeUser(user: UserAccount) {
    if (user.id === currentUser.id) return
    const confirmed = window.confirm(
      `Excluir definitivamente o usuário "${user.full_name}" (${user.username})?\n\nO histórico de auditoria será preservado.`
    )
    if (!confirmed) return
    try {
      await deleteUser(user.id)
      setMessage(`Usuário ${user.username} excluído com sucesso`)
      await refresh()
    } catch (err) { setError((err as Error).message) }
  }

  return <section className="users-panel">
    <div className="section-heading"><div><p className="eyebrow">ADMINISTRAÇÃO</p><h2>Usuários e perfis</h2></div><span className="pill success">controle de acesso ativo</span></div>
    {error && <div className="message error">{error}</div>}{message && <div className="message success">{message}</div>}
    <div className="admin-tools">
      <button type="button" className="admin-tools-toggle" onClick={() => setAdminToolsOpen(open => !open)} aria-expanded={adminToolsOpen}>
        <span className="mini-hamburger" aria-hidden="true"><i></i><i></i><i></i></span>
        <span><strong>Novo usuário e permissões por perfil</strong><small>{adminToolsOpen ? 'Ocultar cadastros e perfis' : 'Clique para abrir cadastros e perfis'}</small></span>
        <b>{adminToolsOpen ? '−' : '+'}</b>
      </button>
      {adminToolsOpen && <div className="user-grid admin-tools-content">
        <form className="config-card" onSubmit={add} autoComplete="off"><h3>Novo usuário</h3>
          <label>Nome completo<input name="new-full-name" autoComplete="off" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} required /></label>
          <label>Usuário<input name="new-username" autoComplete="off" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required /></label>
          <label>Senha inicial<input name="new-password" autoComplete="new-password" type="password" minLength={8} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /></label>
          <label>Perfil<select value={form.role} onChange={e => setForm({ ...form, role: e.target.value as UserRole })}><option value="OPERATOR">Operador</option><option value="SUPERVISOR">Supervisor</option><option value="ADMIN">Administrador</option></select></label>
          <button className="primary">Cadastrar usuário</button>
        </form>
        <div className="config-card permission-card"><h3>Permissões por perfil</h3>
          <div><strong>Operador</strong><span>Dashboard e Operação</span></div><div><strong>Supervisor</strong><span>Dashboard, Indicadores, Operação, OPs, Jornada, Rastreabilidade e Diagnóstico</span></div><div><strong>Administrador</strong><span>Acesso total, Configurações, Usuários e Diagnóstico</span></div>
        </div>
      </div>}
    </div>

    <div className="user-table-wrap"><h3>Usuários cadastrados</h3><table><thead><tr><th>Usuário</th><th>Nome</th><th>Perfil</th><th>Status</th><th>Último acesso</th><th>Ações</th></tr></thead><tbody>{visibleUsers.map(u => <tr key={u.id}>
      <td><strong>{u.username}</strong>{u.id === currentUser.id && <small> você</small>}</td>
      <td>{u.full_name}</td>
      <td><select value={u.role} disabled={u.id === currentUser.id} onChange={e => change(u, { role: e.target.value as UserRole })}><option value="OPERATOR">Operador</option><option value="SUPERVISOR">Supervisor</option><option value="ADMIN">Administrador</option></select></td>
      <td><span className={`table-status ${u.active ? 'valid' : 'invalid'}`}>{u.active ? 'ATIVO' : 'INATIVO'}</span></td>
      <td>{u.last_login_at ? formatLocalDateTime(u.last_login_at) : 'Nunca'}</td>
      <td><div className="inline-actions"><button className="secondary small" onClick={() => openEdit(u)}>Editar</button><button className="secondary small" onClick={() => resetPassword(u)}>Redefinir senha</button><button className="secondary small" disabled={u.id === currentUser.id} onClick={() => change(u, { active: !u.active })}>{u.active ? 'Desativar' : 'Ativar'}</button><button className="danger small" disabled={u.id === currentUser.id} title={u.id === currentUser.id ? 'Você não pode excluir seu próprio usuário' : 'Excluir usuário'} onClick={() => removeUser(u)}>Excluir</button></div></td>
    </tr>)}</tbody></table><div className="panel-pager"><span>{users.length} usuário(s)</span><div><button className="secondary small" disabled={userPage <= 1} onClick={() => setUserPage(p => p - 1)}>Anterior</button><strong>Página {userPage} de {userTotalPages}</strong><button className="secondary small" disabled={userPage >= userTotalPages} onClick={() => setUserPage(p => p + 1)}>Próxima</button></div></div></div>

    <div className="audit-wrap"><div className="widget-head"><div><h3>Auditoria</h3><p>Consulte as ações por data sem perder o histórico dos dias anteriores.</p></div><button className="secondary small" onClick={refresh}>Atualizar</button></div>
      <div className="audit-date-filters">
        <label>Período<select value={auditPeriod} onChange={e => setAuditPeriod(e.target.value as PeriodFilter)}><option value="today">Hoje</option><option value="yesterday">Ontem</option><option value="24h">Últimas 24h</option><option value="7d">Últimos 7 dias</option><option value="month">Este mês</option><option value="custom">Data / período personalizado</option><option value="all">Todo período</option></select></label>
        {auditPeriod === 'custom' && <><label>Data inicial<input type="date" value={auditFrom} onChange={e => setAuditFrom(e.target.value)} /></label><label>Data final<input type="date" min={auditFrom || undefined} value={auditTo} onChange={e => setAuditTo(e.target.value)} /></label></>}
      </div>
      <table><thead><tr><th>Data/Hora</th><th>Usuário</th><th>Ação</th><th>Entidade</th><th>ID</th></tr></thead><tbody>{visibleLogs.map(l => <tr key={l.id}><td>{formatLocalDateTime(l.created_at)}</td><td>{l.username ?? '—'}</td><td>{actionLabel[l.action] ?? l.action}</td><td>{l.entity_type ?? '—'}</td><td>{l.entity_id ?? '—'}</td></tr>)}{visibleLogs.length === 0 && <tr><td colSpan={5}>Nenhum evento encontrado no período selecionado.</td></tr>}</tbody></table><div className="panel-pager"><span>{filteredLogs.length} evento(s) no período</span><div><button className="secondary small" disabled={auditPage <= 1} onClick={() => setAuditPage(p => p - 1)}>Anterior</button><strong>Página {auditPage} de {auditTotalPages}</strong><button className="secondary small" disabled={auditPage >= auditTotalPages} onClick={() => setAuditPage(p => p + 1)}>Próxima</button></div></div></div>

    {editing && <div className="modal-backdrop" onMouseDown={() => setEditing(null)}>
      <form className="account-modal user-edit-modal" onSubmit={saveEdit} onMouseDown={e => e.stopPropagation()}>
        <div className="widget-head"><div><p className="eyebrow">ADMINISTRAÇÃO</p><h3>Editar usuário</h3></div><button type="button" className="secondary small" onClick={() => setEditing(null)}>Fechar</button></div>
        <label>Nome completo<input value={editForm.full_name} onChange={e => setEditForm({ ...editForm, full_name: e.target.value })} required minLength={3} /></label>
        <label>Usuário<input value={editForm.username} onChange={e => setEditForm({ ...editForm, username: e.target.value })} required minLength={3} pattern="[A-Za-z0-9._-]+" /></label>
        <label>Perfil<select value={editForm.role} disabled={editing.id === currentUser.id} onChange={e => setEditForm({ ...editForm, role: e.target.value as UserRole })}><option value="OPERATOR">Operador</option><option value="SUPERVISOR">Supervisor</option><option value="ADMIN">Administrador</option></select></label>
        <label className="user-active-check"><input type="checkbox" checked={editForm.active} disabled={editing.id === currentUser.id} onChange={e => setEditForm({ ...editForm, active: e.target.checked })} /><span>Usuário ativo</span></label>
        {editing.id === currentUser.id && <p className="form-note">Por segurança, seu próprio perfil de Administrador e seu status ativo não podem ser removidos nesta tela.</p>}
        <div className="inline-actions"><button type="submit" className="primary">Salvar alterações</button><button type="button" className="secondary" onClick={() => setEditing(null)}>Cancelar</button></div>
      </form>
    </div>}
  </section>
}
