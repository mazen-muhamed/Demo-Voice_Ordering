import { useCallback, useRef, useState } from 'react'

// Runs one REST action at a time. While it is running every control is
// disabled (`pending`), which also prevents double submissions.
export function useSessionActions(onSession) {
  const [pending, setPending] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const busy = useRef(false)

  const run = useCallback(
    async (sessionId, successMessage, request) => {
      if (busy.current) return
      busy.current = true
      setPending(true)
      setFeedback(null)

      try {
        const session = await request()
        onSession(session)
        setFeedback({ sessionId, type: 'success', message: successMessage })
      } catch (error) {
        setFeedback({ sessionId, type: 'error', message: error.message })
      } finally {
        busy.current = false
        setPending(false)
      }
    },
    [onSession],
  )

  return { pending, feedback, run }
}
