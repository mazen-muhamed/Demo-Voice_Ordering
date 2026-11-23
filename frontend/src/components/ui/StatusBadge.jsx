import { getStatus } from '../../utils/status'

function StatusBadge({ state, className = '' }) {
  const status = getStatus(state)
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset ${status.badge} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} aria-hidden="true" />
      {status.label}
    </span>
  )
}

export default StatusBadge
