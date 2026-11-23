import Card from '../ui/Card'
import Countdown from '../ui/Countdown'
import EmptyState from '../ui/EmptyState'
import StatusBadge from '../ui/StatusBadge'
import { formatClock, formatCurrency, formatRelative } from '../../utils/formatters'
import { ACTIVE_STATES } from '../../utils/status'
import { getCallerLabel, isCallId } from '../../utils/sessionHelpers'

function Field({ label, hint, tone = 'default', children }) {
  const tones = {
    default: 'border-gray-200 bg-gray-50/60',
    warning: 'border-amber-200 bg-amber-50',
  }
  return (
    <div className={`rounded-xl border p-3 ${tones[tone]}`}>
      <dt className="text-xs font-medium text-gray-500">{label}</dt>
      <dd className="mt-1 text-base font-semibold text-gray-900">{children}</dd>
      {hint && <p className="mt-0.5 text-xs text-gray-500">{hint}</p>}
    </div>
  )
}

function SessionDetails({ session, now, isMock, onClear }) {
  if (!session) {
    return (
      <Card title="Session Details">
        <EmptyState
          icon="activity"
          title="No session selected"
          description="Select a session from the list to see its order, keypad activity and timeline."
        />
      </Card>
    )
  }

  const { ui } = session
  const isPending = ui.displayState === 'PENDING_CONFIRMATION'

  let expiryHint = 'No active timer'
  if (session.expires_at && ACTIVE_STATES.includes(ui.displayState)) {
    expiryHint = `Expires at ${formatClock(session.expires_at)}`
  } else if (session.expires_at && ui.displayState === 'EXPIRED') {
    expiryHint = `Expired at ${formatClock(session.expires_at)}`
  }

  return (
    <Card
      title="Session Details"
      subtitle={isMock ? 'Selected session (mock data)' : 'Selected session'}
      action={
        <button
          type="button"
          onClick={onClear}
          className="rounded-lg px-2.5 py-1 text-sm font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-800"
        >
          Clear selection
        </button>
      }
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium tracking-wide text-gray-500 uppercase">
            {isCallId(session.caller_number) ? 'Call' : 'Caller'}
          </p>
          <p className="text-2xl font-bold text-gray-900">{getCallerLabel(session)}</p>
          {isCallId(session.caller_number) && (
            <p className="mt-0.5 text-xs text-gray-500">
              Call ID{' '}
              <span className="font-mono break-all text-gray-700">{session.caller_number}</span>
            </p>
          )}
        </div>
        <div className="text-right">
          <StatusBadge state={ui.displayState} />
          <p className="mt-1 font-mono text-[11px] text-gray-400">state: {session.state}</p>
        </div>
      </div>

      <p className="mt-3 text-xs text-gray-500">
        Session ID <span className="font-mono break-all text-gray-700">{session.id}</span>
      </p>

      {ui.timedOutLocally && (
        <p className="mt-3 rounded-lg bg-gray-100 px-3 py-2 text-xs text-gray-600">
          {isMock
            ? 'The session timer reached zero, so the demo now shows this session as expired. Refresh to restore the mock data.'
            : 'The session timer reached zero. It is shown as expired now; the backend marks it expired within a few seconds.'}
        </p>
      )}

      <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Created" hint={formatRelative(session.created_at, now)}>
          <span className="font-mono">{formatClock(session.created_at)}</span>
        </Field>
        <Field label="Last updated" hint={formatRelative(session.updated_at, now)}>
          <span className="font-mono">{formatClock(session.updated_at)}</span>
        </Field>
        <Field label="Order total">{formatCurrency(session.total)}</Field>
        <Field label="Session expires in" hint={expiryHint}>
          <Countdown seconds={ui.expiresIn} />
        </Field>
        {isPending && (
          <Field
            label="Confirmation expires in"
            tone="warning"
            hint={
              ui.confirmationExpiresIn === 0
                ? 'Confirmation window elapsed'
                : `Ends at ${formatClock(session.confirmation_expires_at)}`
            }
          >
            <Countdown seconds={ui.confirmationExpiresIn} />
          </Field>
        )}
        <Field
          label="Input mode"
          hint={`DTMF buffer: ${session.dtmf_buffer ? session.dtmf_buffer : 'empty'}`}
        >
          {session.editing ? 'Edit mode' : 'Order mode'}
        </Field>
      </dl>
    </Card>
  )
}

export default SessionDetails
