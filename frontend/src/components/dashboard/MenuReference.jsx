import Card from '../ui/Card'
import EmptyState from '../ui/EmptyState'
import { formatCurrency } from '../../utils/formatters'

function MenuContent({ menu }) {
  if (menu.status === 'loading') {
    return <EmptyState icon="book" title="Loading menu…" />
  }
  if (menu.status === 'error') {
    return (
      <EmptyState
        icon="book"
        title="Could not load the menu"
        description={`${menu.error}. Use Refresh to try again.`}
      />
    )
  }
  if (menu.categories.every((category) => category.items.length === 0)) {
    return <EmptyState icon="book" title="The menu is empty" />
  }

  const singleGroup = menu.categories.length === 1

  return (
    <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
      {menu.categories.map((category) => (
        <section
          key={category.id}
          aria-labelledby={`menu-${category.id}`}
          className={singleGroup ? 'sm:col-span-2 xl:col-span-4' : ''}
        >
          <h3
            id={`menu-${category.id}`}
            className="text-xs font-semibold tracking-wide text-purple-700 uppercase"
          >
            {category.name}
          </h3>
          <ul
            className={`mt-2 divide-y divide-gray-100 ${
              singleGroup ? 'sm:columns-2 sm:gap-8 xl:columns-3' : ''
            }`}
          >
            {category.items.map((item) => (
              <li
                key={item.item_id}
                className="flex break-inside-avoid items-center justify-between gap-3 py-2"
              >
                <span className="min-w-0">
                  <span dir="auto" className="block text-sm text-gray-800">
                    {item.name}
                  </span>
                  {item.aliases?.length > 0 && (
                    <span dir="auto" className="block truncate text-xs text-gray-500">
                      Also: {item.aliases.join('، ')}
                    </span>
                  )}
                </span>
                <span className="shrink-0 text-sm font-semibold text-gray-900">
                  {formatCurrency(item.unit_price)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}

function MenuReference({ menu }) {
  return (
    <Card
      id="menu-reference"
      title="Menu Reference"
      subtitle={
        menu.source === 'mock'
          ? 'Sample menu used by the mock sessions (demo data)'
          : 'Loaded from the backend · prices in EGP · aliases are alternative names the voice agent understands'
      }
    >
      <MenuContent menu={menu} />
    </Card>
  )
}

export default MenuReference
