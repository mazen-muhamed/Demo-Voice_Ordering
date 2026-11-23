// MOCK PREVIEW DATA. Used only when the app is opened with ?mock=1.
// These sentences are made up to preview the "Agent Responses" card.
// They are NOT real voice agent output and never appear in real mode.
//
// Responses are grouped by session id, using the same ids as the mock sessions.
// Each response has the shape the future backend event will give us:
//   { id, text, at }   (id = response_id, at = ISO timestamp)

import { IDS } from './mockSessions'

export function buildMockAgentResponses(baseTime = Date.now()) {
  // `ago(30)` = 30 seconds before baseTime.
  const ago = (seconds) => new Date(baseTime - seconds * 1000).toISOString()
  const reply = (id, secondsAgo, text) => ({ id, text, at: ago(secondsAgo) })

  return {
    [IDS.ordering]: [
      reply(1, 424, 'Welcome! What would you like to order today?'),
      reply(2, 394, 'Sure, I added 1 Margherita Pizza. Anything else?'),
      reply(3, 249, 'Got it, 1 Garlic Bread added. Anything else?'),
      reply(4, 37, 'Done, 2 Colas added. Would you like anything else?'),
    ],
    [IDS.editing]: [
      reply(1, 304, 'Welcome! What would you like to order today?'),
      reply(2, 269, 'I added 1 Margherita Pizza. Anything else?'),
      reply(3, 199, 'Sure, 1 Chicken Wings added. Anything else?'),
      reply(4, 61, 'Edit mode is on. Which item would you like to change?'),
      reply(5, 30, 'Chicken Wings is now 3. Anything else?'),
    ],
    [IDS.pendingLarge]: [
      reply(1, 784, 'Welcome! What would you like to order today?'),
      reply(2, 739, 'I added 1 Margherita Pizza. Anything else?'),
      reply(3, 619, 'Sure, 1 Pepperoni Pizza added. Anything else?'),
      reply(4, 24, 'Your order is ready. Press 1 to confirm or 2 to edit.'),
    ],
    [IDS.empty]: [reply(1, 34, 'Welcome! What would you like to order today?')],
    [IDS.confirmed]: [
      reply(1, 898, 'Welcome! What would you like to order today?'),
      reply(2, 612, 'Thank you! Your order is confirmed.'),
    ],
  }
}
