import Card from '../ui/Card'
import {
  cancelSession,
  confirmSession,
  editSession,
  requestConfirmation,
} from '../../services/api'

// Which buttons exist in which state. This mirrors the backend rules in
// voice_ordering/app/modules/orders/fsm.py and service.py:
//   ORDERING             -> request confirmation (needs items), cancel
//   PENDING_CONFIRMATION -> confirm, back to editing, cancel
//   CONFIRMED / CANCELLED / EXPIRED -> nothing can change any more
const BUTTON_STYLES = {
  primary: 'bg-purple-600 text-white hover:bg-purple-600/90',
  secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
  danger: 'bg-red-50 text-red-700 hover:bg-red-100',
}

function getButtons(session) {
  if (session.state === 'ORDERING') {
    const isEmpty = (session.items ?? []).length === 0
    return [
      {
        id: 'request',
        label: 'Request confirmation',
        style: 'primary',
        disabled: isEmpty,
        hint: isEmpty ? 'Add at least one item first' : undefined,
        success: 'Confirmation requested',
        send: () => requestConfirmation(session.id),
      },
      {
        id: 'cancel',
        label: 'Cancel order',
        style: 'danger',
        confirmText: 'Cancel this order? This cannot be undone.',
        success: 'Order cancelled',
        send: () => cancelSession(session.id),
      },
    ]
  }

  if (session.state === 'PENDING_CONFIRMATION') {
    return [
      {
        id: 'confirm',
        label: 'Confirm order',
        style: 'primary',
        success: 'Order confirmed',
        send: () => confirmSession(session.id),
      },
      {
        id: 'edit',
        label: 'Back to editing',
        style: 'secondary',
        success: 'Order reopened for editing',
        send: () => editSession(session.id),
      },
      {
        id: 'cancel',
        label: 'Cancel order',
        style: 'danger',
        confirmText: 'Cancel this order? This cannot be undone.',
        success: 'Order cancelled',
        send: () => cancelSession(session.id),
      },
    ]
  }

  return []
}

function SessionActions({ session, actions }) {
  const buttons = getButtons(session)
  const { pending, feedback, run } = actions
  // The session timer ran out in the browser. The backend will reject actions.
  const timedOut = session.ui.timedOutLocally
  const message = feedback && feedback.sessionId === session.id ? feedback : null

  function handleClick(button) {
    if (button.confirmText && !window.confirm(button.confirmText)) return
    run(session.id, button.success, button.send)
  }

  return (
    <Card
      title="Session Actions"
      subtitle="These buttons change the live session on the backend"
    >
      {buttons.length === 0 || timedOut ? (
        <p className="text-sm text-gray-500">
          {timedOut
            ? 'This session has timed out, so it can no longer be changed.'
            : 'This session is finished, so it can no longer be changed.'}
        </p>
      ) : (
        <div className="flex flex-wrap gap-3">
          {buttons.map((button) => (
            <button
              key={button.id}
              type="button"
              disabled={pending || button.disabled}
              title={button.hint}
              onClick={() => handleClick(button)}
              className={`rounded-xl px-4 py-2 text-sm font-semibold shadow-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 disabled:cursor-not-allowed disabled:opacity-50 ${
                BUTTON_STYLES[button.style]
              }`}
            >
              {button.label}
            </button>
          ))}
        </div>
      )}

      {pending && <p className="mt-3 text-sm text-gray-500">Sending request…</p>}

      {message && (
        <p
          role={message.type === 'error' ? 'alert' : 'status'}
          className={`mt-3 rounded-lg px-3 py-2 text-sm ${
            message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
          }`}
        >
          {message.message}
        </p>
      )}
    </Card>
  )
}

export default SessionActions
