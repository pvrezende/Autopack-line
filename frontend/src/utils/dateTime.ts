const APP_TIME_ZONE = import.meta.env.VITE_TIME_ZONE ?? 'America/Manaus'

/**
 * O backend e o MySQL trabalham em UTC. Alguns campos DateTime chegam sem
 * sufixo de fuso (ex.: 2026-08-10T18:45:25). Nesses casos, acrescentamos Z
 * para que o navegador interprete o valor como UTC antes de exibir no fuso
 * operacional configurado.
 */
export function parseUtcTimestamp(value: string) {
  const normalized = /Z$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`
  return new Date(normalized)
}

export function formatLocalDateTime(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: APP_TIME_ZONE,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(parseUtcTimestamp(value))
}

export function formatLocalTime(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: APP_TIME_ZONE,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(parseUtcTimestamp(value))
}
