import { useState, type FormEvent } from 'react'
import { login, setStoredToken } from '../services/api'
import type { UserAccount } from '../types/domain'

export function LoginPanel({ onLogin }: { onLogin: (user: UserAccount) => void }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const result = await login(username, password)
      setStoredToken(result.access_token)
      onLogin(result.user)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }

  return <div className="login-page">
    <form className="login-card" onSubmit={submit}>
      <div className="login-brand"><span className="brand-mark">A</span><div><strong>AUTOPACKLINE</strong><small>Rastreabilidade industrial</small></div></div>
      <div><p className="eyebrow">ACESSO AO SISTEMA</p><h1>Entrar</h1><p>Use seu usuário e senha para acessar a operação.</p></div>
      <label>Usuário<input value={username} onChange={e => setUsername(e.target.value)} autoFocus autoComplete="username" /></label>
      <label>Senha<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" /></label>
      {error && <div className="message error">{error}</div>}
      <button className="primary" disabled={busy}>{busy ? 'Entrando...' : 'Entrar'}</button>
      <small className="login-help">Acesso controlado por perfil: Operador, Supervisor ou Administrador.</small>
    </form>
  </div>
}
