import { useCallback, useMemo, useState } from 'react'
import { ACTIVE_STATES, STATE_ORDER } from '../utils/status'

// Shared by the live and mock hooks: live countdown values, search, state
// filter and selection. Input sessions use the backend session shape plus a
// `received_at` timestamp (when this browser received the session).

function toViewModel(session, now) {
  const elapsedSeconds = (now - (session.received_at ?? now)) / 1000
  const secondsLeft = (value) =>
    value == null ? null : Math.max(0, Math.floor(value - elapsedSeconds))

  const isActive = ACTIVE_STATES.includes(session.state)
  const isPending = session.state === 'PENDING_CONFIRMATION'
  const expiresIn = isActive ? secondsLeft(session.expires_in_seconds) : null
  const confirmationIn = isPending ? secondsLeft(session.confirmation_expires_in_seconds) : null

  // When a timer reaches zero the backend marks the session EXPIRED within a
  // few seconds. Show it as expired right away instead of waiting for that.
  const timedOut = isActive && (expiresIn === 0 || confirmationIn === 0)
  const displayState = timedOut ? 'EXPIRED' : session.state

  return {
    ...session,
    ui: {
      displayState,
      timedOutLocally: timedOut,
      expiresIn,
      confirmationExpiresIn: timedOut ? null : confirmationIn,
    },
  }
}

function matchesQuery(session, query) {
  const q = query.trim().toLowerCase()
  if (!q) return true
  if (session.caller_number.toLowerCase().includes(q)) return true
  if (session.id.toLowerCase().includes(q)) return true
  const digits = q.replace(/\D/g, '')
  return digits !== '' && session.caller_number.replace(/\D/g, '').includes(digits)
}

export function useSessionView({ sessions, eventsBySessionId, now, initialSelectedId = null }) {
  const [selectedId, setSelectedId] = useState(initialSelectedId)
  const [query, setQuery] = useState('')
  const [stateFilter, setStateFilter] = useState('ALL')

  const viewSessions = useMemo(
    () => sessions.map((session) => toViewModel(session, now)),
    [sessions, now],
  )

  const stateCounts = useMemo(() => {
    const counts = { ALL: viewSessions.length }
    STATE_ORDER.forEach((state) => {
      counts[state] = viewSessions.filter((s) => s.ui.displayState === state).length
    })
    return counts
  }, [viewSessions])

  const filteredSessions = useMemo(
    () =>
      viewSessions.filter(
        (s) =>
          (stateFilter === 'ALL' || s.ui.displayState === stateFilter) &&
          matchesQuery(s, query),
      ),
    [viewSessions, stateFilter, query],
  )

  // If the selected session is gone, this is null and the empty state shows.
  const selectedSession = viewSessions.find((s) => s.id === selectedId) ?? null
  const selectedEvents = selectedSession ? (eventsBySessionId[selectedSession.id] ?? []) : []

  const resetFilters = useCallback(() => {
    setQuery('')
    setStateFilter('ALL')
  }, [])

  const clearSelection = useCallback(() => setSelectedId(null), [])

  return {
    sessions: viewSessions,
    filteredSessions,
    stateCounts,
    selectedSession,
    selectedEvents,
    selectSession: setSelectedId,
    clearSelection,
    query,
    setQuery,
    stateFilter,
    setStateFilter,
    resetFilters,
  }
}
