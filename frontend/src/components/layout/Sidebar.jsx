import { useEffect, useState } from 'react'
import Icon from '../ui/Icon'

// Every item scrolls to a section of this page (the URL hash changes).
const NAV_ITEMS = [
  { id: 'live-monitor', label: 'Live Monitor', icon: 'activity', href: '#sessions' },
  { id: 'overview', label: 'Overview', icon: 'grid', href: '#overview' },
  { id: 'menu', label: 'Menu', icon: 'book', href: '#menu-reference' },
  { id: 'agent-responses', label: 'Agent Responses', icon: 'mic', href: '#agent-responses' },
]

// The active item follows the current URL hash. No hash means the main page.
function getActiveId() {
  const match = NAV_ITEMS.find((item) => item.href === window.location.hash)
  return match ? match.id : NAV_ITEMS[0].id
}

const ITEM_BASE =
  'flex h-10 w-full items-center gap-3 rounded-xl px-3 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500'

function Brand() {
  return (
    <div className="flex items-center gap-3 px-1">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-600 text-white shadow-sm">
        <Icon name="mic" className="h-5 w-5" />
      </span>
      <div className="leading-tight">
        <p className="text-sm font-bold text-gray-900">Voice Ordering</p>
        <p className="text-xs text-gray-500">Live Monitor</p>
      </div>
    </div>
  )
}

function NavList({ activeId, onNavigate }) {
  return (
    <ul className="space-y-1.5">
      {NAV_ITEMS.map((item) => {
        const active = item.id === activeId
        return (
          <li key={item.id}>
            <a
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? 'page' : undefined}
              className={`${ITEM_BASE} ${
                active
                  ? 'bg-white text-purple-700 shadow-sm ring-1 ring-gray-200'
                  : 'text-gray-600 hover:bg-white/60 hover:text-gray-900'
              }`}
            >
              <Icon
                name={item.icon}
                className={`h-5 w-5 shrink-0 ${active ? 'text-purple-600' : 'text-gray-500'}`}
              />
              <span>{item.label}</span>
            </a>
          </li>
        )
      })}
    </ul>
  )
}

function Sidebar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeId, setActiveId] = useState(getActiveId)

  useEffect(() => {
    const syncActive = () => setActiveId(getActiveId())
    window.addEventListener('hashchange', syncActive)
    return () => window.removeEventListener('hashchange', syncActive)
  }, [])

  return (
    <>
      {/* Mobile / tablet top bar */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-100 px-4 py-3 lg:hidden">
        <Brand />
        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-controls="mobile-nav"
          aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
          className="rounded-lg p-2 text-gray-700 hover:bg-white"
        >
          <Icon name={menuOpen ? 'x' : 'menu'} />
        </button>
      </div>
      {menuOpen && (
        <nav id="mobile-nav" aria-label="Main" className="border-b border-gray-200 bg-gray-100 p-3 lg:hidden">
          <NavList activeId={activeId} onNavigate={() => setMenuOpen(false)} />
        </nav>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-gray-200 bg-gray-100 lg:block">
        <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col gap-6 p-4">
          <Brand />
          <nav aria-label="Main" className="border-t border-gray-200 pt-4">
            <NavList activeId={activeId} />
          </nav>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
