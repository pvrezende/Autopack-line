import { useState, type FormEvent } from 'react'
import { changePassword } from '../services/api'

export function PasswordModal({ onClose }: { onClose: () => void }) {
  const [current, setCurrent] = useState(''); const [next, setNext] = useState(''); const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState(''); const [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault(); setError(''); setMessage('')
    if (next !== confirm) { setError('A confirmação da nova senha não confere'); return }
    try { await changePassword(current, next); setMessage('Senha alterada com sucesso'); setCurrent(''); setNext(''); setConfirm('') }
    catch (err) { setError((err as Error).message) }
  }
  return <div className="modal-backdrop"><form className="account-modal" onSubmit={submit}>
    <div className="section-heading"><div><p className="eyebrow">SEGURANÇA</p><h2>Alterar minha senha</h2></div><button type="button" className="secondary" onClick={onClose}>Fechar</button></div>
    <label>Senha atual<input type="password" value={current} onChange={e => setCurrent(e.target.value)} required /></label>
    <label>Nova senha<input type="password" minLength={8} value={next} onChange={e => setNext(e.target.value)} required /></label>
    <label>Confirmar nova senha<input type="password" minLength={8} value={confirm} onChange={e => setConfirm(e.target.value)} required /></label>
    {error && <div className="message error">{error}</div>}{message && <div className="message success">{message}</div>}
    <button className="primary">Salvar nova senha</button>
  </form></div>
}
