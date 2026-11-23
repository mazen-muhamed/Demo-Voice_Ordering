import Icon from '../ui/Icon'
import { formatClock } from '../../utils/formatters'
import { getConnectionStatus } from '../../utils/status'

function Header({ status, lastUpdated, onRefresh }) {
  const config = getConnectionStatus(status)
  const isMock = status === 'mock'

  return (
    <header className="border-b border-gray-100 bg-white px-4 py-5 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">Live Monitor</h1>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${config.badge}`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} aria-hidden="true" />
              {config.label}
            </span>
          </div>
          <p className="mt-1 max-w-xl text-sm text-gray-500">
            Monitor active voice-ordering sessions and inspect each caller&rsquo;s order, keypad
            activity and timeline.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <p className="text-xs text-gray-500">
            Last updated{' '}
            {lastUpdated ? (
              <time
                dateTime={new Date(lastUpdated).toISOString()}
                className="font-mono font-medium text-gray-700"
              >
                {formatClock(lastUpdated)}
              </time>
            ) : (
              <span className="font-mono font-medium text-gray-700">—</span>
            )}
            {isMock && (
              <span className="block text-[11px] text-gray-400">Mock data, not live</span>
            )}
          </p>
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-purple-600/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <Icon name="refresh" className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
