// Turns backend messages into dashboard state.
//
// WebSocket /ws/live (voice_ordering/app/modules/orders/router.py):
//   { type: 'snapshot', sessions: [...] }   (live sessions only, sent once on connect)
//   { type: 'session_created' | 'item_added' | 'item_updated' | 'item_removed' |
//           'state_changed' | 'session_expired' | 'dtmf', session: {...}, ...extra }
// Every event carries the full updated session. The backend keeps no event
// history, so the timeline is built from events this page has received.

import { ACTIVE_STATES, getDtmfActionLabel } from './status'
import { addAgentResponse, toAgentResponse } from './agentResponses'

const MAX_EVENTS_PER_SESSION = 100

export const initialLiveState = {
  sessions: {},
  events: {},
  // Agent responses by session id. Stays empty until the backend sends 'ai_response'.
  agentResponses: {},
  nextEventId: 1,
  lastMessageAt: null,
}

function isSession(value) {
  return Boolean(value) && typeof value.id === 'string' && typeof value.state === 'string'
}

// `received_at` lets countdowns use the server's *_in_seconds values
// without depending on the browser clock matching the server clock.
function normalizeSession(raw, receivedAt) {
  return {
    ...raw,
    caller_number: raw.caller_number ?? 'Unknown caller',
    items: raw.items ?? [],
    dtmf_history: raw.dtmf_history ?? [],
    received_at: receivedAt,
  }
}

function createdEvent(session) {
  return { id: `${session.id}-created`, type: 'SESSION_CREATED', at: session.created_at, message: 'Session created' }
}

function findItem(session, itemId) {
  return session?.items.find((item) => item.item_id === itemId)
}

function describeStateChange(session) {
  switch (session.state) {
    case 'PENDING_CONFIRMATION':
      return { type: 'CONFIRMATION_REQUESTED', message: 'Confirmation requested, waiting for caller' }
    case 'CONFIRMED':
      return { type: 'ORDER_CONFIRMED', message: 'Order confirmed' }
    case 'CANCELLED':
      return { type: 'ORDER_CANCELLED', message: 'Order cancelled' }
    case 'ORDERING':
      return {
        type: 'EDIT_MODE',
        message: session.editing ? 'Edit mode started' : 'Order reopened for editing',
      }
    default:
      return null
  }
}

function describeEvent(message, session, previous) {
  switch (message.type) {
    case 'item_added': {
      const item = findItem(session, message.item_id)
      return {
        type: 'ITEM_ADDED',
        message: item ? `Item added: ${item.name} (now × ${item.quantity})` : 'Item added',
      }
    }
    case 'item_updated': {
      const item = findItem(session, message.item_id)
      const before = findItem(previous, message.item_id)
      if (!item) return { type: 'ITEM_UPDATED', message: 'Quantity updated' }
      return {
        type: 'ITEM_UPDATED',
        message:
          before && before.quantity !== item.quantity
            ? `Quantity updated: ${item.name} ${before.quantity} → ${item.quantity}`
            : `Quantity updated: ${item.name} × ${item.quantity}`,
      }
    }
    case 'item_removed': {
      const before = findItem(previous, message.item_id)
      return { type: 'ITEM_REMOVED', message: before ? `Item removed: ${before.name}` : 'Item removed' }
    }
    case 'state_changed':
      return describeStateChange(session)
    case 'session_expired':
      return { type: 'SESSION_EXPIRED', message: 'Session expired' }
    case 'dtmf': {
      const action = message.action ? ` (${getDtmfActionLabel(message.action)})` : ''
      return { type: 'DTMF', message: `Key ${message.digit} pressed${action}` }
    }
    default:
      return null
  }
}

// Keypad edits ("2*3#") change the order but the backend only sends a `dtmf`
// event for them, so compare the cart before and after to show what changed.
function diffItems(previous, session) {
  if (!previous) return []
  const entries = []

  session.items.forEach((item) => {
    const before = findItem(previous, item.item_id)
    if (before && before.quantity !== item.quantity) {
      entries.push({
        type: 'ITEM_UPDATED',
        message: `Quantity updated: ${item.name} ${before.quantity} → ${item.quantity}`,
      })
    }
  })
  previous.items.forEach((before) => {
    if (!findItem(session, before.item_id)) {
      entries.push({ type: 'ITEM_REMOVED', message: `Item removed: ${before.name}` })
    }
  })

  return entries
}

function applySnapshot(state, rawSessions, receivedAt) {
  const sessions = {}
  rawSessions.filter(isSession).forEach((raw) => {
    sessions[raw.id] = normalizeSession(raw, receivedAt)
  })

  // The snapshot only lists live sessions. Keep sessions that ended while
  // this page was open, so the operator can still see how they finished.
  Object.values(state.sessions).forEach((old) => {
    if (!sessions[old.id] && !ACTIVE_STATES.includes(old.state)) sessions[old.id] = old
  })

  const events = {}
  Object.keys(sessions).forEach((id) => {
    events[id] = state.events[id] ?? [createdEvent(sessions[id])]
  })

  return { ...state, sessions, events, lastMessageAt: receivedAt }
}

function applyEvent(state, message, receivedAt) {
  if (!isSession(message.session)) return state

  const session = normalizeSession(message.session, receivedAt)
  const previous = state.sessions[session.id]
  const known = state.events[session.id] ?? [createdEvent(session)]
  const mainEntry = describeEvent(message, session, previous)

  let entries = mainEntry ? [mainEntry] : []
  if (message.type === 'dtmf') entries = [...diffItems(previous, session), ...entries]

  let nextEventId = state.nextEventId
  const added = entries.map((entry) => ({
    ...entry,
    id: `evt-${nextEventId++}`,
    at: session.updated_at,
  }))

  return {
    ...state,
    sessions: { ...state.sessions, [session.id]: session },
    events: {
      ...state.events,
      [session.id]: [...known, ...added].slice(-MAX_EVENTS_PER_SESSION),
    },
    nextEventId,
    lastMessageAt: receivedAt,
  }
}

// Used after a REST action: every endpoint returns the full session.
// The WebSocket still supplies the timeline events, so only the session is
// updated here, and only if it is not older than what we already have.
function applySessionUpdate(state, rawSession, receivedAt) {
  if (!isSession(rawSession)) return state

  const existing = state.sessions[rawSession.id]
  if (existing && Date.parse(rawSession.updated_at) < Date.parse(existing.updated_at)) {
    return state
  }

  const session = normalizeSession(rawSession, receivedAt)
  return {
    ...state,
    sessions: { ...state.sessions, [session.id]: session },
    events: state.events[session.id]
      ? state.events
      : { ...state.events, [session.id]: [createdEvent(session)] },
  }
}

// Proposed 'ai_response' event (see utils/agentResponses.js). Not sent by the
// backend yet. It only adds to the agent response list of its own session.
function applyAgentResponse(state, message, receivedAt) {
  const parsed = toAgentResponse(message)
  if (!parsed) return state

  const list = state.agentResponses[parsed.sessionId] ?? []
  const next = addAgentResponse(list, parsed.response, receivedAt)
  if (next === list) return state

  return {
    ...state,
    agentResponses: { ...state.agentResponses, [parsed.sessionId]: next },
  }
}

export function liveReducer(state, action) {
  switch (action.type) {
    case 'snapshot':
      return Array.isArray(action.sessions)
        ? applySnapshot(state, action.sessions, action.receivedAt)
        : state
    case 'event':
      if (action.message.type === 'ai_response') {
        return applyAgentResponse(state, action.message, action.receivedAt)
      }
      return applyEvent(state, action.message, action.receivedAt)
    case 'session':
      return applySessionUpdate(state, action.session, action.receivedAt)
    default:
      return state
  }
}
