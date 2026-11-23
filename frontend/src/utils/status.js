// Shared state names, colors and event styles.
// Colors are written out as full class names so Tailwind can detect them.

export const STATE_ORDER = [
  'ORDERING',
  'PENDING_CONFIRMATION',
  'CONFIRMED',
  'CANCELLED',
  'EXPIRED',
]

// States where the session is still "live" and has a running timer.
export const ACTIVE_STATES = ['ORDERING', 'PENDING_CONFIRMATION']

export const STATUS_CONFIG = {
  ORDERING: {
    label: 'Ordering',
    short: 'Ordering',
    badge: 'bg-blue-50 text-blue-700 ring-blue-600/20',
    dot: 'bg-blue-500',
  },
  PENDING_CONFIRMATION: {
    label: 'Pending confirmation',
    short: 'Pending',
    badge: 'bg-amber-50 text-amber-700 ring-amber-600/20',
    dot: 'bg-amber-500',
  },
  CONFIRMED: {
    label: 'Confirmed',
    short: 'Confirmed',
    badge: 'bg-green-50 text-green-700 ring-green-600/20',
    dot: 'bg-green-500',
  },
  CANCELLED: {
    label: 'Cancelled',
    short: 'Cancelled',
    badge: 'bg-red-50 text-red-700 ring-red-600/20',
    dot: 'bg-red-500',
  },
  EXPIRED: {
    label: 'Expired',
    short: 'Expired',
    badge: 'bg-gray-100 text-gray-600 ring-gray-500/20',
    dot: 'bg-gray-400',
  },
}

const FALLBACK_STATUS = {
  label: 'Unknown',
  short: 'Unknown',
  badge: 'bg-gray-100 text-gray-600 ring-gray-500/20',
  dot: 'bg-gray-400',
}

export function getStatus(state) {
  return STATUS_CONFIG[state] ?? FALLBACK_STATUS
}

export const EVENT_STYLES = {
  SESSION_CREATED: { icon: 'phone', dot: 'bg-purple-500' },
  ITEM_ADDED: { icon: 'plus', dot: 'bg-blue-500' },
  ITEM_REMOVED: { icon: 'x', dot: 'bg-gray-400' },
  DTMF: { icon: 'activity', dot: 'bg-purple-500' },
  ITEM_UPDATED: { icon: 'pencil', dot: 'bg-purple-500' },
  EDIT_MODE: { icon: 'pencil', dot: 'bg-purple-600' },
  CONFIRMATION_REQUESTED: { icon: 'clock', dot: 'bg-amber-500' },
  ORDER_CONFIRMED: { icon: 'check', dot: 'bg-green-500' },
  ORDER_CANCELLED: { icon: 'x', dot: 'bg-red-500' },
  SESSION_EXPIRED: { icon: 'clock', dot: 'bg-gray-400' },
}

const FALLBACK_EVENT_STYLE = { icon: 'activity', dot: 'bg-gray-400' }

export function getEventStyle(type) {
  return EVENT_STYLES[type] ?? FALLBACK_EVENT_STYLE
}

// Backend DTMF actions (dtmf_history[].action) in plain words.
const DTMF_ACTION_LABELS = {
  request_confirmation: 'Requested confirmation',
  confirm: 'Order confirmed',
  edit: 'Entered edit mode',
  cancel: 'Cancelled order',
  buffer: 'Added to edit buffer',
  edit_applied: 'Edit applied',
  edit_invalid: 'Invalid edit sequence',
  ignored: 'Key ignored',
}

export function getDtmfActionLabel(action) {
  return DTMF_ACTION_LABELS[action] ?? action
}

export const CONNECTION_CONFIG = {
  mock: {
    label: 'Demo Mode · Mock data',
    badge: 'bg-purple-50 text-purple-700 ring-purple-600/20',
    dot: 'bg-purple-500',
  },
  connecting: {
    label: 'Connecting…',
    badge: 'bg-amber-50 text-amber-700 ring-amber-600/20',
    dot: 'bg-amber-500',
  },
  connected: {
    label: 'Live · Connected',
    badge: 'bg-green-50 text-green-700 ring-green-600/20',
    dot: 'bg-green-500',
  },
  disconnected: {
    label: 'Disconnected',
    badge: 'bg-red-50 text-red-700 ring-red-600/20',
    dot: 'bg-red-500',
  },
}

export function getConnectionStatus(status) {
  return CONNECTION_CONFIG[status] ?? CONNECTION_CONFIG.disconnected
}
