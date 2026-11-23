// REST calls to the FastAPI backend (voice_ordering/app/modules/orders/router.py).
// Paths are relative, so they go through the Vite dev proxy (/api -> backend).
// Every session endpoint returns the full updated session (SessionOut).

const API_BASE = '/api/v1'

async function readError(response) {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    // FastAPI validation errors send a list of { msg, loc, ... }.
    if (Array.isArray(body.detail)) {
      const messages = body.detail.map((entry) => entry.msg).filter(Boolean)
      if (messages.length) return messages.join('; ')
    }
  } catch {
    // The error body was not JSON, so the status code is used instead.
  }
  return `Request failed (${response.status})`
}

async function request(path, { method = 'GET', body } = {}) {
  const options = { method }
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${path}`, options)
  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

// GET /api/v1/menu returns a flat list: [{ id, name, price, aliases }].
// It has no categories, so everything goes into one "Menu" group.
export async function fetchMenu() {
  const items = await request('/menu')
  if (!Array.isArray(items)) throw new Error('Unexpected menu response')

  return [
    {
      id: 'menu',
      name: 'Menu',
      items: items.map((item) => ({
        item_id: item.id,
        name: item.name,
        unit_price: item.price,
        aliases: Array.isArray(item.aliases) ? item.aliases : [],
      })),
    },
  ]
}

const sessionPath = (sessionId) => `/sessions/${encodeURIComponent(sessionId)}`

// POST /sessions/{sid}/items  { item_id, quantity }   (ORDERING only)
export function addItem(sessionId, itemId, quantity) {
  return request(`${sessionPath(sessionId)}/items`, {
    method: 'POST',
    body: { item_id: itemId, quantity },
  })
}

// PATCH /sessions/{sid}/items/{item_id}  { quantity }   (0 removes the line)
export function setItemQuantity(sessionId, itemId, quantity) {
  return request(`${sessionPath(sessionId)}/items/${itemId}`, {
    method: 'PATCH',
    body: { quantity },
  })
}

// DELETE /sessions/{sid}/items/{item_id}
export function removeItem(sessionId, itemId) {
  return request(`${sessionPath(sessionId)}/items/${itemId}`, { method: 'DELETE' })
}

// POST /sessions/{sid}/request-confirmation   (ORDERING -> PENDING_CONFIRMATION)
export function requestConfirmation(sessionId) {
  return request(`${sessionPath(sessionId)}/request-confirmation`, { method: 'POST' })
}

// POST /sessions/{sid}/confirm   (PENDING_CONFIRMATION -> CONFIRMED)
export function confirmSession(sessionId) {
  return request(`${sessionPath(sessionId)}/confirm`, { method: 'POST' })
}

// POST /sessions/{sid}/edit   (PENDING_CONFIRMATION -> ORDERING)
export function editSession(sessionId) {
  return request(`${sessionPath(sessionId)}/edit`, { method: 'POST' })
}

// POST /sessions/{sid}/cancel   (ORDERING or PENDING_CONFIRMATION -> CANCELLED)
export function cancelSession(sessionId) {
  return request(`${sessionPath(sessionId)}/cancel`, { method: 'POST' })
}

// POST /sessions/{sid}/dtmf  { digit }   (one of 0-9 * #)
export function sendDtmf(sessionId, digit) {
  return request(`${sessionPath(sessionId)}/dtmf`, { method: 'POST', body: { digit } })
}
