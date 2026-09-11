type Props = {
  backendStatus: string
  dbStatus: string
}

export function StatusCards({ backendStatus, dbStatus }: Props) {
  return (
    <div className="status-grid compact">
      <article><span>Frontend</span><strong className="ok">online</strong></article>
      <article><span>Backend</span><strong className={backendStatus === 'online' ? 'ok' : 'warn'}>{backendStatus}</strong></article>
      <article><span>Banco</span><strong className={dbStatus === 'online' ? 'ok' : 'warn'}>{dbStatus}</strong></article>
      <article><span>Integrações físicas</span><strong>simuladas</strong></article>
    </div>
  )
}
