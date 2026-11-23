// Small helpers that work on "view-model" sessions
// (a backend-shaped session plus a `ui` object, see hooks/useMockSessions.js).

// The listener stores FreeSWITCH's call UUID in `caller_number`, so it is often
// not a phone number at all. Sessions created through the API can still hold a
// real number, so check the shape before choosing a label.
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function isCallId(value) {
  return UUID_PATTERN.test(value ?? '')
}

// Short name for a session row: "Call 1a2b3c4d" for a call UUID, otherwise the value.
export function getCallerLabel(session) {
  const value = session.caller_number
  return isCallId(value) ? `Call ${value.slice(0, 8)}` : value
}

// Total number of units in a cart (sum of quantities).
export function countItems(items) {
  return (items ?? []).reduce((sum, item) => sum + (item.quantity ?? 0), 0)
}

// KPI numbers are calculated from the sessions, not hardcoded.
export function getKpis(sessions) {
  const inState = (state) => sessions.filter((s) => s.ui.displayState === state)
  const sumTotals = (list) => list.reduce((sum, s) => sum + (s.total ?? 0), 0)

  const ordering = inState('ORDERING')
  const pending = inState('PENDING_CONFIRMATION')
  const confirmed = inState('CONFIRMED')

  const pendingCountdowns = pending
    .map((s) => s.ui.confirmationExpiresIn)
    .filter((seconds) => seconds != null)

  return {
    activeCount: ordering.length + pending.length,
    orderingCount: ordering.length,
    pendingCount: pending.length,
    nextConfirmationIn: pendingCountdowns.length ? Math.min(...pendingCountdowns) : null,
    confirmedCount: confirmed.length,
    confirmedValue: sumTotals(confirmed),
    // Active + confirmed orders (cancelled and expired sessions are left out).
    totalValue: sumTotals([...ordering, ...pending, ...confirmed]),
  }
}
