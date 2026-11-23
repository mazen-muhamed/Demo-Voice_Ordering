import Icon from '../ui/Icon'
import { getKpis } from '../../utils/sessionHelpers'
import { formatCountdown, formatCurrency } from '../../utils/formatters'

// The backend keeps no history. It only sends the sessions that are live right
// now, and then events while this page is open. So "confirmed" below means
// confirmed while this page was open, not all-time or today.
function KpiCards({ sessions }) {
  const kpis = getKpis(sessions)

  const cards = [
    {
      label: 'Active Sessions',
      value: kpis.activeCount,
      hint: `${kpis.orderingCount} ordering · ${kpis.pendingCount} pending`,
      icon: 'activity',
    },
    {
      label: 'Pending Confirmations',
      value: kpis.pendingCount,
      hint:
        kpis.nextConfirmationIn == null
          ? 'No callers waiting'
          : `Next window ends in ${formatCountdown(kpis.nextConfirmationIn)}`,
      icon: 'clock',
    },
    {
      label: 'Confirmed This View',
      value: kpis.confirmedCount,
      hint: `Worth ${formatCurrency(kpis.confirmedValue)} · since this page opened`,
      icon: 'checkCircle',
    },
    {
      label: 'Order Value This View',
      value: formatCurrency(kpis.totalValue),
      hint: 'Active + confirmed since this page opened',
      icon: 'currency',
    },
  ]

  return (
    <section
      id="overview"
      aria-label="Key metrics"
      className="grid scroll-mt-4 gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      {cards.map((card) => (
        <article
          key={card.label}
          className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
        >
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-medium text-gray-500">{card.label}</p>
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
              <Icon name={card.icon} className="h-5 w-5" />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight text-gray-900">{card.value}</p>
          <p className="mt-1 text-xs text-gray-500">{card.hint}</p>
        </article>
      ))}
    </section>
  )
}

export default KpiCards
