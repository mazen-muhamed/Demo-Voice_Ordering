import { useEffect, useState } from 'react'

// Current time, updated every second. Drives countdowns and "x ago" labels.
export function useNow() {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])

  return now
}
