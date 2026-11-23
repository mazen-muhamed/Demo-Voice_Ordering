import Card from '../ui/Card'
import EmptyState from '../ui/EmptyState'
import StatusBadge from '../ui/StatusBadge'
import { getDtmfActionLabel } from '../../utils/status'
import { formatClock, formatRelative } from '../../utils/formatters'

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#']

function DtmfHistory({ session, now, isMock }) {
  const history = session.dtmf_history ?? []
  const pressedKeys = new Set(history.flatMap((entry) => entry.digit.split('')))
  // Newest first. The original index keeps React keys stable.
  const entries = history.map((entry, index) => ({ ...entry, index })).reverse()

  return (
    <Card
      title="DTMF Activity"
      subtitle={isMock ? 'Keypad presses in this session (mock)' : 'Keypad presses in this session'}
    >
      {/* Current state */}
      <div className="flex flex-wrap items-center gap-5">
        <div
          role="img"
          aria-label={`Keypad. Keys pressed so far: ${
            [...pressedKeys].join(', ') || 'none'
          }`}
          className="grid w-36 grid-cols-3 gap-1.5"
        >
          {KEYS.map((key) => (
            <span
              key={key}
              className={`flex h-9 items-center justify-center rounded-lg border font-mono text-sm font-semibold ${
                pressedKeys.has(key)
                  ? 'border-purple-300 bg-purple-100 text-purple-700'
                  : 'border-gray-200 bg-gray-50 text-gray-400'
              }`}
            >
              {key}
            </span>
          ))}
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-xs font-medium tracking-wide text-gray-500 uppercase">
            Current input
          </p>
          <div className="rounded-xl border border-gray-200 bg-gray-50/60 p-3">
            <p className="text-xs text-gray-500">DTMF buffer</p>
            <p className="mt-0.5 font-mono text-lg font-semibold text-gray-900">
              {session.dtmf_buffer ? session.dtmf_buffer : <span className="text-gray-400">empty</span>}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {session.editing ? 'Edit mode is active' : 'Not in edit mode'}
            </p>
          </div>
          <p className="text-xs text-gray-400">Highlighted keys were pressed earlier.</p>
        </div>
      </div>

      {/* History */}
      <h3 className="mt-6 text-xs font-medium tracking-wide text-gray-500 uppercase">
        History (newest first)
      </h3>
      {entries.length === 0 ? (
        <div className="mt-3">
          <EmptyState
            icon="inbox"
            title="No keypad activity yet"
            description="This caller has not pressed any keys."
          />
        </div>
      ) : (
        <ol className="mt-3 space-y-2">
          {entries.map((entry) => (
            <li
              key={`${entry.at}-${entry.index}`}
              className="flex items-start gap-3 rounded-xl border border-gray-100 p-3"
            >
              <span className="min-w-10 rounded-lg bg-purple-50 px-2.5 py-1 text-center font-mono text-sm font-bold text-purple-700">
                {entry.digit}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">
                  {entry.action ? getDtmfActionLabel(entry.action) : 'No action recorded'}
                </p>
                <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500">
                  <span className="font-mono">{formatClock(entry.at)}</span>
                  <span>· {formatRelative(entry.at, now)}</span>
                  <span className="inline-flex items-center gap-1">
                    · state then: <StatusBadge state={entry.state} />
                  </span>
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

export default DtmfHistory
