import Card from '../ui/Card'
import Countdown from '../ui/Countdown'
import EmptyState from '../ui/EmptyState'
import Icon from '../ui/Icon'
import StatusBadge from '../ui/StatusBadge'
import { countItems, getCallerLabel } from '../../utils/sessionHelpers'
import { STATE_ORDER, STATUS_CONFIG } from '../../utils/status'
import { formatCurrency, formatRelative, shortId } from '../../utils/formatters'

const FILTER_OPTIONS = [
  { value: 'ALL', label: 'All' },
  ...STATE_ORDER.map((state) => ({ value: state, label: STATUS_CONFIG[state].short })),
]

function SessionRow({ session, selected, now, onSelect }) {
  const { ui } = session
  const isPending = ui.displayState === 'PENDING_CONFIRMATION'
  const timerLabel = isPending ? 'Confirm in' : 'Expires in'
  const timerSeconds = isPending ? ui.confirmationExpiresIn : ui.expiresIn
  const itemCount = countItems(session.items)

  return (
    <button
      type="button"
      onClick={() => onSelect(session.id)}
      aria-pressed={selected}
      className={`w-full rounded-xl border p-4 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 ${
        selected
          ? 'border-purple-600 bg-purple-100/40 ring-2 ring-purple-200'
          : 'border-gray-200 bg-white hover:border-purple-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-gray-900">{getCallerLabel(session)}</p>
          <p className="font-mono text-xs text-gray-500">#{shortId(session.id)}</p>
        </div>
        <StatusBadge state={ui.displayState} />
      </div>

      <dl className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <div>
          <dt className="text-gray-500">Items</dt>
          <dd className="mt-0.5 font-semibold text-gray-900">{itemCount}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Total</dt>
          <dd className="mt-0.5 font-semibold text-gray-900">{formatCurrency(session.total)}</dd>
        </div>
        <div>
          <dt className="text-gray-500">{timerLabel}</dt>
          <dd className="mt-0.5">
            <Countdown seconds={timerSeconds} />
          </dd>
        </div>
      </dl>

      <p className="mt-2 text-xs text-gray-500">
        Last activity {formatRelative(session.updated_at, now)}
      </p>
    </button>
  )
}

function ActiveSessions({
  sessions,
  totalCount,
  stateCounts,
  selectedId,
  now,
  query,
  onQueryChange,
  stateFilter,
  onStateFilterChange,
  onResetFilters,
  onSelect,
  emptyState,
}) {
  return (
    <Card
      id="sessions"
      title="Active Sessions"
      subtitle={`Showing ${sessions.length} of ${totalCount} sessions`}
    >
      <div className="space-y-3">
        <label className="relative block">
          <span className="sr-only">Search by call ID, caller or session ID</span>
          <Icon
            name="search"
            className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-gray-400"
          />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search call ID, caller or session ID"
            className="w-full rounded-xl border border-gray-200 bg-gray-50 py-2.5 pr-3 pl-10 text-sm text-gray-900 placeholder:text-gray-400 focus:border-purple-600 focus:bg-white focus:ring-2 focus:ring-purple-200 focus:outline-none"
          />
        </label>

        <div role="group" aria-label="Filter by session state" className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((option) => {
            const active = stateFilter === option.value
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onStateFilterChange(option.value)}
                aria-pressed={active}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                  active
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {option.label}
                <span className={`ml-1.5 ${active ? 'text-purple-200' : 'text-gray-400'}`}>
                  {stateCounts[option.value] ?? 0}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="mt-4">
        {sessions.length === 0 && totalCount === 0 && emptyState ? (
          <EmptyState icon="inbox" title={emptyState.title} description={emptyState.description} />
        ) : sessions.length === 0 ? (
          <EmptyState
            icon="search"
            title="No sessions match"
            description="Try a different search term or state filter."
            action={
              <button
                type="button"
                onClick={onResetFilters}
                className="rounded-lg bg-purple-50 px-3 py-1.5 text-sm font-medium text-purple-700 hover:bg-purple-100"
              >
                Clear filters
              </button>
            }
          />
        ) : (
          <ul className="max-h-[640px] space-y-3 overflow-y-auto pr-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <SessionRow
                  session={session}
                  selected={session.id === selectedId}
                  now={now}
                  onSelect={onSelect}
                />
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  )
}

export default ActiveSessions
