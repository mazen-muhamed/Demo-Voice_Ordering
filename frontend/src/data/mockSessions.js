// Mock data for the Phase 2 Live Monitor.
//
// `sessions` follow the backend session shape (id, caller_number, state, items,
// total, editing, dtmf_buffer, dtmf_history, created_at, updated_at, expires_at,
// expires_in_seconds, confirmation_expires_at, confirmation_expires_in_seconds).
//
// `eventsBySessionId` is UI-only mock data for the timeline and is kept
// separate from the backend-shaped sessions.
//
// All timestamps are generated relative to `baseTime`, so every refresh gives
// fresh, believable values. In Phase 3, replace buildMockData() with calls to
// the real API / WebSocket service and keep the same return shape.

import { MOCK_MENU } from './mockMenu'

const SESSION_TTL_SECONDS = 600

const MENU_BY_ID = Object.fromEntries(
  MOCK_MENU.flatMap((category) => category.items).map((item) => [item.item_id, item]),
)

const round2 = (value) => Math.round(value * 100) / 100

function makeItem(itemId, quantity) {
  const menuItem = MENU_BY_ID[itemId]
  return {
    item_id: menuItem.item_id,
    name: menuItem.name,
    unit_price: menuItem.unit_price,
    quantity,
    line_total: round2(menuItem.unit_price * quantity),
  }
}

export const IDS = {
  editing: '3f9a1c52-8d47-4e6b-9a20-7c1e5b8d4f03',
  ordering: '9c47f1d0-3a8e-4b92-8d65-f1a0e7c35b14',
  pendingSmall: 'b71e04d8-52c9-4a3f-8e16-0d9f7a2c6b55',
  pendingLarge: '0b6f83e5-d794-41ca-8a07-c52e9f1b3d48',
  confirmed: '5d2c8e97-14ab-4f60-b3d8-e49a1f0c7286',
  empty: 'e08b6a33-9f71-4d25-a5c4-2b7d90e1f8a9',
  cancelled: '27ae5b64-c0d1-48f9-97e3-6a8b1d4f20c7',
  expired: 'a4d90c18-6e2b-4735-b1f8-83c5e07a9d62',
}

export function buildMockData(baseTime = Date.now()) {
  // `ago(30)` = 30 seconds before baseTime. Negative values are in the future.
  const ago = (seconds) => new Date(baseTime - seconds * 1000).toISOString()

  const press = (digit, secondsAgo, state, action) => ({
    digit,
    at: ago(secondsAgo),
    state,
    action,
  })

  const evt = (type, secondsAgo, message) => ({ type, at: ago(secondsAgo), message })

  const withIds = (sessionId, list) =>
    list.map((event, index) => ({ id: `${sessionId}-evt-${index}`, ...event }))

  function makeSession({
    id,
    caller_number,
    state,
    items = [],
    editing = false,
    dtmf_buffer = '',
    dtmf_history = [],
    createdAgo,
    updatedAgo,
    confirmationIn = null,
  }) {
    const hasSessionTimer =
      state === 'ORDERING' || state === 'PENDING_CONFIRMATION' || state === 'EXPIRED'
    const expiresIn = hasSessionTimer ? SESSION_TTL_SECONDS - updatedAgo : null

    return {
      id,
      caller_number,
      state,
      items,
      total: round2(items.reduce((sum, item) => sum + item.line_total, 0)),
      editing,
      dtmf_buffer,
      dtmf_history,
      created_at: ago(createdAgo),
      updated_at: ago(updatedAgo),
      expires_at: hasSessionTimer ? ago(-expiresIn) : null,
      expires_in_seconds: hasSessionTimer ? Math.max(0, expiresIn) : null,
      confirmation_expires_at: confirmationIn == null ? null : ago(-confirmationIn),
      confirmation_expires_in_seconds: confirmationIn,
    }
  }

  const sessions = [
    // ORDERING, currently in edit mode with a partly typed DTMF sequence
    makeSession({
      id: IDS.editing,
      caller_number: '+1 (555) 016-9182',
      state: 'ORDERING',
      items: [makeItem('pizza-margherita', 1), makeItem('side-wings', 3)],
      editing: true,
      dtmf_buffer: '2*',
      dtmf_history: [
        press('2', 62, 'ORDERING', 'Entered edit mode'),
        press('2*3#', 31, 'ORDERING', 'Edit sequence applied: line 2 quantity set to 3'),
      ],
      createdAgo: 300,
      updatedAgo: 14,
    }),

    // ORDERING, multiple items, no DTMF yet
    makeSession({
      id: IDS.ordering,
      caller_number: '+1 (555) 014-2291',
      state: 'ORDERING',
      items: [
        makeItem('pizza-margherita', 1),
        makeItem('side-garlic-bread', 1),
        makeItem('drink-cola', 2),
      ],
      createdAgo: 420,
      updatedAgo: 38,
    }),

    // ORDERING, empty cart
    makeSession({
      id: IDS.empty,
      caller_number: '+1 (555) 013-5507',
      state: 'ORDERING',
      createdAgo: 35,
      updatedAgo: 35,
    }),

    // PENDING_CONFIRMATION, waiting for the caller
    makeSession({
      id: IDS.pendingLarge,
      caller_number: '+1 (555) 015-8814',
      state: 'PENDING_CONFIRMATION',
      items: [
        makeItem('pizza-margherita', 2),
        makeItem('pizza-pepperoni', 1),
        makeItem('pizza-veggie', 1),
        makeItem('side-garlic-bread', 2),
        makeItem('drink-cola', 4),
        makeItem('dessert-tiramisu', 2),
      ],
      dtmf_history: [press('1', 25, 'ORDERING', 'Requested confirmation')],
      createdAgo: 780,
      updatedAgo: 25,
      confirmationIn: 95,
    }),

    // PENDING_CONFIRMATION, confirmation window almost over
    makeSession({
      id: IDS.pendingSmall,
      caller_number: '+1 (555) 018-7340',
      state: 'PENDING_CONFIRMATION',
      items: [
        makeItem('pizza-pepperoni', 2),
        makeItem('side-caesar-salad', 1),
        makeItem('side-wings', 1),
        makeItem('drink-lemonade', 2),
      ],
      dtmf_history: [press('1', 68, 'ORDERING', 'Requested confirmation')],
      createdAgo: 540,
      updatedAgo: 68,
      confirmationIn: 52,
    }),

    // CONFIRMED
    makeSession({
      id: IDS.confirmed,
      caller_number: '+1 (555) 019-6628',
      state: 'CONFIRMED',
      items: [makeItem('pizza-veggie', 1), makeItem('drink-sparkling-water', 1)],
      dtmf_history: [
        press('1', 640, 'ORDERING', 'Requested confirmation'),
        press('1', 610, 'PENDING_CONFIRMATION', 'Order confirmed'),
      ],
      createdAgo: 900,
      updatedAgo: 610,
    }),

    // CANCELLED
    makeSession({
      id: IDS.cancelled,
      caller_number: '+1 (555) 012-4473',
      state: 'CANCELLED',
      items: [makeItem('pizza-pepperoni', 1), makeItem('drink-cola', 1)],
      dtmf_history: [press('0', 1260, 'ORDERING', 'Cancelled order')],
      createdAgo: 1500,
      updatedAgo: 1260,
    }),

    // EXPIRED
    makeSession({
      id: IDS.expired,
      caller_number: '+1 (555) 017-3056',
      state: 'EXPIRED',
      items: [makeItem('side-garlic-bread', 1)],
      createdAgo: 1400,
      updatedAgo: 660,
    }),
  ]

  const eventsBySessionId = {
    [IDS.editing]: withIds(IDS.editing, [
      evt('SESSION_CREATED', 300, 'Session created from incoming call'),
      evt('ITEM_ADDED', 270, 'Item added: Margherita Pizza × 1'),
      evt('ITEM_ADDED', 200, 'Item added: Chicken Wings × 1'),
      evt('EDIT_MODE', 62, 'Caller entered edit mode'),
      evt('ITEM_UPDATED', 31, 'Quantity updated: Chicken Wings 1 → 3'),
    ]),
    [IDS.ordering]: withIds(IDS.ordering, [
      evt('SESSION_CREATED', 420, 'Session created from incoming call'),
      evt('ITEM_ADDED', 395, 'Item added: Margherita Pizza × 1'),
      evt('ITEM_ADDED', 250, 'Item added: Garlic Bread × 1'),
      evt('ITEM_ADDED', 38, 'Item added: Cola × 2'),
    ]),
    [IDS.empty]: withIds(IDS.empty, [
      evt('SESSION_CREATED', 35, 'Session created from incoming call'),
    ]),
    [IDS.pendingLarge]: withIds(IDS.pendingLarge, [
      evt('SESSION_CREATED', 780, 'Session created from incoming call'),
      evt('ITEM_ADDED', 740, 'Item added: Margherita Pizza × 1'),
      evt('ITEM_UPDATED', 700, 'Quantity updated: Margherita Pizza 1 → 2'),
      evt('ITEM_ADDED', 620, 'Item added: Pepperoni Pizza × 1'),
      evt('ITEM_ADDED', 540, 'Item added: Veggie Supreme Pizza × 1'),
      evt('ITEM_ADDED', 400, 'Item added: Garlic Bread × 2'),
      evt('ITEM_ADDED', 300, 'Item added: Cola × 4'),
      evt('ITEM_ADDED', 180, 'Item added: Tiramisu × 2'),
      evt('CONFIRMATION_REQUESTED', 25, 'Confirmation requested, waiting for caller'),
    ]),
    [IDS.pendingSmall]: withIds(IDS.pendingSmall, [
      evt('SESSION_CREATED', 540, 'Session created from incoming call'),
      evt('ITEM_ADDED', 500, 'Item added: Pepperoni Pizza × 1'),
      evt('ITEM_UPDATED', 430, 'Quantity updated: Pepperoni Pizza 1 → 2'),
      evt('ITEM_ADDED', 360, 'Item added: Caesar Salad × 1'),
      evt('ITEM_ADDED', 300, 'Item added: Chicken Wings × 1'),
      evt('ITEM_ADDED', 210, 'Item added: Lemonade × 2'),
      evt('CONFIRMATION_REQUESTED', 68, 'Confirmation requested, waiting for caller'),
    ]),
    [IDS.confirmed]: withIds(IDS.confirmed, [
      evt('SESSION_CREATED', 900, 'Session created from incoming call'),
      evt('ITEM_ADDED', 860, 'Item added: Veggie Supreme Pizza × 1'),
      evt('ITEM_ADDED', 720, 'Item added: Sparkling Water × 1'),
      evt('CONFIRMATION_REQUESTED', 640, 'Confirmation requested'),
      evt('ORDER_CONFIRMED', 610, 'Order confirmed by caller'),
    ]),
    [IDS.cancelled]: withIds(IDS.cancelled, [
      evt('SESSION_CREATED', 1500, 'Session created from incoming call'),
      evt('ITEM_ADDED', 1450, 'Item added: Pepperoni Pizza × 1'),
      evt('ITEM_ADDED', 1380, 'Item added: Cola × 1'),
      evt('ORDER_CANCELLED', 1260, 'Order cancelled by caller'),
    ]),
    [IDS.expired]: withIds(IDS.expired, [
      evt('SESSION_CREATED', 1400, 'Session created from incoming call'),
      evt('ITEM_ADDED', 660, 'Item added: Garlic Bread × 1'),
      evt('SESSION_EXPIRED', 660 - SESSION_TTL_SECONDS, 'Session expired after inactivity'),
    ]),
  }

  return { sessions, eventsBySessionId }
}
