// WebSocket client for /ws/live.
// The server sends a "snapshot" first, then one message per backend event.
// It only calls receive_text() to keep the socket open, so we send a small
// "ping" text now and then. If the socket closes we retry automatically.

const RETRY_DELAYS_MS = [1000, 2000, 5000, 10000]
const PING_INTERVAL_MS = 25000

export function startMonitorSocket({ onStatus, onMessage }) {
  let socket = null
  let retryTimer = null
  let pingTimer = null
  let attempt = 0
  let stopped = false

  function connect() {
    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
    socket = new WebSocket(`${scheme}://${window.location.host}/ws/live`)

    socket.onopen = () => {
      attempt = 0
      onStatus('connected')
      pingTimer = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send('ping')
      }, PING_INTERVAL_MS)
    }

    socket.onmessage = (event) => {
      let message
      try {
        message = JSON.parse(event.data)
      } catch {
        return
      }
      if (message && typeof message === 'object') onMessage(message)
    }

    socket.onclose = () => {
      clearInterval(pingTimer)
      if (stopped) return
      onStatus('disconnected')
      const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)]
      attempt += 1
      // The status stays "disconnected" while retrying, so the UI does not flicker.
      retryTimer = setTimeout(connect, delay)
    }
  }

  connect()

  return function stop() {
    stopped = true
    clearTimeout(retryTimer)
    clearInterval(pingTimer)
    if (socket) socket.close()
  }
}
