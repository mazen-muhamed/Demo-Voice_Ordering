// Helpers for the "Agent Responses" card.
//
// PROPOSED backend event. The backend does NOT send it yet, so in real mode
// nothing arrives and the card shows an empty state:
//   {
//     type: 'ai_response',
//     session_id: '<application session uuid>',
//     response_id: 1,                      // grows by 1 per session
//     text: 'تمام، ضفتلك 2 كشري كبير',
//     intent: 'order',                     // not used by the UI
//     at: '2026-11-23T10:15:32.481Z',
//     session: { ... }                     // not used by the UI
//   }
//
// A stored response looks like: { id, text, at }.

const MAX_RESPONSES_PER_SESSION = 100

// Turns a raw event into { sessionId, response }, or null if it is not usable.
export function toAgentResponse(message) {
  const sessionId = message.session_id ?? message.session?.id
  if (typeof sessionId !== 'string' || typeof message.text !== 'string') return null

  const text = message.text.trim()
  if (!text) return null

  return {
    sessionId,
    response: { id: message.response_id ?? null, text, at: message.at ?? null },
  }
}

// Oldest first: by response_id when both have one, otherwise by timestamp.
function byTime(a, b) {
  if (typeof a.id === 'number' && typeof b.id === 'number') return a.id - b.id
  const timeA = Date.parse(a.at)
  const timeB = Date.parse(b.at)
  if (!Number.isNaN(timeA) && !Number.isNaN(timeB)) return timeA - timeB
  return 0 // sort() is stable, so the arrival order is kept
}

// Returns a new list with the response added. A response_id we already have is ignored.
export function addAgentResponse(list, response, receivedAt) {
  if (response.id != null && list.some((item) => item.id === response.id)) return list

  const stored = { ...response, id: response.id ?? `local-${receivedAt}-${list.length}` }
  return [...list, stored].sort(byTime).slice(-MAX_RESPONSES_PER_SESSION)
}
