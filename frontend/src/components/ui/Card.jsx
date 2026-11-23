function Card({ id, title, subtitle, action, className = '', children }) {
  return (
    <section
      id={id}
      className={`scroll-mt-4 rounded-2xl border border-gray-200 bg-white shadow-sm ${className}`}
    >
      {title && (
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-gray-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  )
}

export default Card
