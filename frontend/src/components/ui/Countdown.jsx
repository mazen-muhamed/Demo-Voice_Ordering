import { formatCountdown } from '../../utils/formatters'

// Shows mm:ss and changes color when time is running out.
function Countdown({ seconds, className = '' }) {
  if (seconds == null) {
    return <span className={`text-gray-400 ${className}`}>—</span>
  }
  const tone =
    seconds <= 30 ? 'text-red-600' : seconds <= 90 ? 'text-amber-600' : 'text-gray-900'
  return (
    <span className={`font-mono font-semibold tabular-nums ${tone} ${className}`}>
      {formatCountdown(seconds)}
    </span>
  )
}

export default Countdown
