// Egyptian pound. Amounts are shown as received (no conversion), e.g. "250.00 EGP".
const currencyFormatter = new Intl.NumberFormat('en-EG', {
  style: 'currency',
  currency: 'EGP',
})

export function formatCurrency(value) {
  const amount = Number.isFinite(value) ? value : 0
  // Keep only the number parts and put the currency code after the amount.
  const number = currencyFormatter
    .formatToParts(amount)
    .filter((part) => part.type !== 'currency' && part.type !== 'literal')
    .map((part) => part.value)
    .join('')
  return `${number}\u00A0EGP`
}

// Accepts an ISO string, a timestamp or a Date.
export function formatClock(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// 125 -> "02:05". Returns an em dash when there is no timer.
export function formatCountdown(totalSeconds) {
  if (totalSeconds == null) return '—'
  const safe = Math.max(0, Math.floor(totalSeconds))
  const minutes = String(Math.floor(safe / 60)).padStart(2, '0')
  const seconds = String(safe % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

// "just now", "42s ago", "6m ago", "2h ago"
export function formatRelative(value, now) {
  if (!value) return '—'
  const diff = Math.floor((now - Date.parse(value)) / 1000)
  if (Number.isNaN(diff)) return '—'
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

export function shortId(id) {
  return id ? id.slice(0, 8) : '—'
}
