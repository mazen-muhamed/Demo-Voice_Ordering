import { useCallback, useEffect, useMemo, useReducer, useState } from 'react'
import { fetchMenu } from '../services/api'
import { startMonitorSocket } from '../services/monitorSocket'
import { initialLiveState, liveReducer } from '../utils/liveSessions'
import { useNow } from './useNow'
import { useSessionActions } from './useSessionActions'
import { useSessionView } from './useSessionView'

// Real mode: sessions come from the backend WebSocket, the menu from REST.
// Returns the same shape as useMockSessions.

const MENU_LOADING = { status: 'loading', source: 'backend', categories: [], error: null }

export function useLiveSessions() {
  const [live, dispatch] = useReducer(liveReducer, initialLiveState)
  const [connection, setConnection] = useState('connecting')
  const [menu, setMenu] = useState(MENU_LOADING)
  const [connectKey, setConnectKey] = useState(0)
  const now = useNow()
  const isConnected = connection === 'connected'

  useEffect(() => {
    return startMonitorSocket({
      onStatus: setConnection,
      onMessage: (message) => {
        const receivedAt = Date.now()
        if (message.type === 'snapshot') {
          dispatch({ type: 'snapshot', sessions: message.sessions, receivedAt })
        } else {
          dispatch({ type: 'event', message, receivedAt })
        }
      },
    })
  }, [connectKey])

  // Loads the menu at start, on Refresh, and again whenever the socket reconnects.
  useEffect(() => {
    let cancelled = false
    fetchMenu()
      .then((categories) => {
        if (!cancelled) setMenu({ status: 'ready', source: 'backend', categories, error: null })
      })
      .catch((error) => {
        if (!cancelled) {
          setMenu({ status: 'error', source: 'backend', categories: [], error: error.message })
        }
      })
    return () => {
      cancelled = true
    }
  }, [connectKey, isConnected])

  // Newest calls first. Sorting by creation time keeps rows from jumping around.
  const sessions = useMemo(
    () =>
      Object.values(live.sessions).sort(
        (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
      ),
    [live.sessions],
  )

  const view = useSessionView({ sessions, eventsBySessionId: live.events, now })

  // Every REST action returns the full updated session. Show it right away;
  // the WebSocket then adds the matching timeline event.
  const applySession = useCallback((session) => {
    dispatch({ type: 'session', session, receivedAt: Date.now() })
  }, [])
  const actions = useSessionActions(applySession)

  // Refresh = reconnect (gets a new snapshot) and reload the menu.
  const refresh = useCallback(() => {
    setConnection('connecting')
    setConnectKey((key) => key + 1)
  }, [])

  return {
    ...view,
    isMock: false,
    actions,
    agentResponsesBySessionId: live.agentResponses,
    connection,
    menu,
    lastUpdated: live.lastMessageAt,
    refresh,
    now,
  }
}
