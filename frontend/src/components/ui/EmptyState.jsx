import Icon from './Icon'

function EmptyState({ icon = 'inbox', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50/60 px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-purple-50 text-purple-500">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <h3 className="mt-3 text-sm font-semibold text-gray-900">{title}</h3>
      {description && <p className="mt-1 max-w-xs text-sm text-gray-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export default EmptyState
