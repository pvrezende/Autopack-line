import { parseUtcTimestamp } from './dateTime'

export type PeriodFilter = 'today' | 'yesterday' | '24h' | '7d' | 'month' | 'custom' | 'all'

function utcDbValue(date: Date) {
  return date.toISOString().slice(0, 19)
}

function localDayStart(date: Date) {
  const value = new Date(date)
  value.setHours(0, 0, 0, 0)
  return value
}

function localDayEnd(date: Date) {
  const value = new Date(date)
  value.setHours(23, 59, 59, 999)
  return value
}

function localDate(value: string, endOfDay = false) {
  if (!value) return undefined
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) return undefined
  const date = new Date(year, month - 1, day)
  return endOfDay ? localDayEnd(date) : localDayStart(date)
}

export function periodRange(period: PeriodFilter, from: string, to: string) {
  if (period === 'all') return {}
  const now = new Date()

  if (period === '24h') {
    return { date_from: utcDbValue(new Date(now.getTime() - 24 * 60 * 60 * 1000)), date_to: utcDbValue(now) }
  }
  if (period === '7d') {
    const start = localDayStart(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6))
    return { date_from: utcDbValue(start), date_to: utcDbValue(localDayEnd(now)) }
  }
  if (period === 'month') {
    const start = localDayStart(new Date(now.getFullYear(), now.getMonth(), 1))
    return { date_from: utcDbValue(start), date_to: utcDbValue(localDayEnd(now)) }
  }
  if (period === 'yesterday') {
    const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1)
    return { date_from: utcDbValue(localDayStart(yesterday)), date_to: utcDbValue(localDayEnd(yesterday)) }
  }
  if (period === 'today') {
    return { date_from: utcDbValue(localDayStart(now)), date_to: utcDbValue(localDayEnd(now)) }
  }

  const start = localDate(from)
  const end = localDate(to || from, true)
  return {
    date_from: start ? utcDbValue(start) : undefined,
    date_to: end ? utcDbValue(end) : undefined,
  }
}

export function periodLabel(period: PeriodFilter, from: string, to: string) {
  if (period === 'today') return 'Hoje'
  if (period === 'yesterday') return 'Ontem'
  if (period === '24h') return 'Últimas 24 horas'
  if (period === '7d') return 'Últimos 7 dias'
  if (period === 'month') return 'Este mês'
  if (period === 'all') return 'Todo o período'
  if (!from && !to) return 'Período personalizado'
  if (from && (!to || to === from)) return `Data ${formatDateOnly(from)}`
  return `${from ? formatDateOnly(from) : 'início'} até ${to ? formatDateOnly(to) : 'agora'}`
}

export function formatDateOnly(value: string) {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  return `${day}/${month}/${year}`
}

export function isDateInPeriod(value: string, period: PeriodFilter, from: string, to: string) {
  if (period === 'all') return true
  const date = parseUtcTimestamp(value)
  if (Number.isNaN(date.getTime())) return false
  const range = periodRange(period, from, to)
  const start = range.date_from ? new Date(`${range.date_from}Z`).getTime() : Number.NEGATIVE_INFINITY
  const end = range.date_to ? new Date(`${range.date_to}Z`).getTime() : Number.POSITIVE_INFINITY
  return date.getTime() >= start && date.getTime() <= end
}
