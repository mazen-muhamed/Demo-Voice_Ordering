import Card from '../ui/Card'
import EmptyState from '../ui/EmptyState'
import Icon from '../ui/Icon'
import { getEventStyle } from '../../utils/status'
import { formatClock, formatRelative } from '../../utils/formatters'

function EventTimeline({ events, now, isMock }) {
  // Newest first, so operators see the latest activity at the top.
  const sorted = [...(events ?? [])].sort((a, b) => Date.parse(b.at) - Date.parse(a.at))

  return (
    <Card
      title="Session Timeline"
      subtitle={
        isMock
          ? 'Mock events, newest first'
          : 'Events received since this page connected, newest first'
      }
    >
      {sorted.length === 0 ? (
        <EmptyState
          icon="clock"
          title="No events yet"
          description="Events for this session will appear here."
        />
      ) : (
        <ol className="relative space-y-5 border-l border-gray-200 pl-6">
          {sorted.map((event) => {
            const style = getEventStyle(event.type)
            return (
              <li key={event.id} className="relative">
                <span
                  className={`absolute top-0 -left-9 flex h-6 w-6 items-center justify-center rounded-full text-white ring-4 ring-white ${style.dot}`}
                >
                  <Icon name={style.icon} className="h-3.5 w-3.5" />
                </span>
                <p dir="auto" className="text-sm font-medium text-gray-900">
                  {event.message}
                </p>
                <p className="mt-0.5 text-xs text-gray-500">
                  <span className="font-mono">{formatClock(event.at)}</span> ·{' '}
                  {formatRelative(event.at, now)}
                </p>
              </li>
            )
          })}
        </ol>
      )}
    </Card>
  )
}

export default EventTimeline
