import { useCallback, useState } from 'react'
import { buildMockData } from '../data/mockSessions'
import { buildMockAgentResponses } from '../data/mockAgentResponses'
import { MOCK_MENU } from '../data/mockMenu'
import { useNow } from './useNow'
import { useSessionView } from './useSessionView'

// Demo mode only (open the app with ?mock=1). Returns the same shape as
// useLiveSessions, so the dashboard components do not care which one is used.

const MOCK_MENU_STATE = { status: 'ready', source: 'mock', categories: MOCK_MENU, error: null }

function createSnapshot() {
  const loadedAt = Date.now()
  const data = buildMockData(loadedAt)
  const sessions = data.sessions
    .map((session) => ({ ...session, received_at: loadedAt }))
    .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))
  return {
    sessions,
    eventsBySessionId: data.eventsBySessionId,
    agentResponses: buildMockAgentResponses(loadedAt),
    loadedAt,
  }
}

export function useMockSessions() {
  const [snapshot, setSnapshot] = useState(createSnapshot)
  const now = useNow()

  const view = useSessionView({
    sessions: snapshot.sessions,
    eventsBySessionId: snapshot.eventsBySessionId,
    now,
    initialSelectedId: snapshot.sessions[0]?.id ?? null,
  })

  const refresh = useCallback(() => setSnapshot(createSnapshot()), [])

  return {
    ...view,
    isMock: true,
    agentResponsesBySessionId: snapshot.agentResponses,
    connection: 'mock',
    menu: MOCK_MENU_STATE,
    lastUpdated: snapshot.loadedAt,
    refresh,
    now,
  }
}
