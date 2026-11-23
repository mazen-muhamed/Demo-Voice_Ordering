import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import KpiCards from './components/dashboard/KpiCards'
import ActiveSessions from './components/dashboard/ActiveSessions'
import SessionDetails from './components/dashboard/SessionDetails'
import OrderItems from './components/dashboard/OrderItems'
import SessionActions from './components/dashboard/SessionActions'
import AgentResponses from './components/dashboard/AgentResponses'
import DtmfHistory from './components/dashboard/DtmfHistory'
import EventTimeline from './components/dashboard/EventTimeline'
import MenuReference from './components/dashboard/MenuReference'
import { useLiveSessions } from './hooks/useLiveSessions'
import { useMockSessions } from './hooks/useMockSessions'

// Real backend data is the default. Open the app with ?mock=1 for demo mode.
const USE_MOCK = new URLSearchParams(window.location.search).get('mock') === '1'
const useSessions = USE_MOCK ? useMockSessions : useLiveSessions

const EMPTY_STATES = {
  connecting: {
    title: 'Connecting to the backend…',
    description: 'Waiting for the first session snapshot.',
  },
  connected: {
    title: 'No active sessions',
    description: 'New calls will appear here as soon as they start.',
  },
  disconnected: {
    title: 'Backend unreachable',
    description: 'Retrying automatically. Make sure the backend is running.',
  },
}

function App() {
  const {
    sessions,
    filteredSessions,
    stateCounts,
    selectedSession,
    selectedEvents,
    selectSession,
    clearSelection,
    query,
    setQuery,
    stateFilter,
    setStateFilter,
    resetFilters,
    isMock,
    actions,
    agentResponsesBySessionId,
    connection,
    menu,
    lastUpdated,
    refresh,
    now,
  } = useSessions()

  return (
    <div className="min-h-screen bg-canvas lg:p-4">
      <div className="flex min-h-screen flex-col bg-canvas lg:min-h-[calc(100vh-2rem)] lg:flex-row lg:overflow-clip lg:rounded-3xl lg:border lg:border-gray-200 lg:shadow-xl">
        <Sidebar />

        <div className="flex min-w-0 flex-1 flex-col">
          <Header status={connection} lastUpdated={lastUpdated} onRefresh={refresh} />

          <main className="flex-1 space-y-6 bg-canvas p-4 sm:p-6">
            {connection === 'disconnected' && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                Cannot reach the backend. Retrying automatically. The data below is the last
                information received and may be out of date.
              </div>
            )}

            <KpiCards sessions={sessions} />

            <div className="grid gap-6 xl:grid-cols-12">
              <div className="xl:col-span-5">
                <ActiveSessions
                  sessions={filteredSessions}
                  totalCount={sessions.length}
                  stateCounts={stateCounts}
                  selectedId={selectedSession?.id ?? null}
                  now={now}
                  query={query}
                  onQueryChange={setQuery}
                  stateFilter={stateFilter}
                  onStateFilterChange={setStateFilter}
                  onResetFilters={resetFilters}
                  onSelect={selectSession}
                  emptyState={isMock ? null : EMPTY_STATES[connection]}
                />
              </div>

              <div className="space-y-6 xl:col-span-7">
                <SessionDetails
                  session={selectedSession}
                  now={now}
                  isMock={isMock}
                  onClear={clearSelection}
                />
                {selectedSession && (
                  <>
                    {/* Actions only exist in real mode. Mock data has no backend to call. */}
                    {!isMock && <SessionActions session={selectedSession} actions={actions} />}
                    <OrderItems session={selectedSession} actions={isMock ? null : actions} />
                  </>
                )}
                <AgentResponses
                  session={selectedSession}
                  responses={
                    selectedSession ? (agentResponsesBySessionId[selectedSession.id] ?? []) : []
                  }
                  isMock={isMock}
                />
                {selectedSession && (
                  <>
                    <div className="grid gap-6 lg:grid-cols-2">
                      <DtmfHistory session={selectedSession} now={now} isMock={isMock} />
                      <EventTimeline events={selectedEvents} now={now} isMock={isMock} />
                    </div>
                  </>
                )}
              </div>
            </div>

            <MenuReference menu={menu} />

            {isMock && (
              <p className="pb-2 text-center text-xs text-gray-400">
                Demo Mode · All data on this page is mock data.
              </p>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

export default App
