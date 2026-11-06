import { useEffect, useState } from 'react'
import { useMatch } from 'react-router'
import { useSharedChat } from './ChatProvider'

const QUIET_MS = 45_000
const SCROLLED = 0.6
const SEEN_KEY = 'shophelper.nudge-seen'
const DESKTOP = '(min-width: 1280px)'

function seen(): boolean {
  try {
    return sessionStorage.getItem(SEEN_KEY) !== null
  } catch {
    return true // storage blocked: staying quiet is the safe choice
  }
}

function markSeen() {
  try {
    sessionStorage.setItem(SEEN_KEY, '1')
  } catch {
    // storage blocked
  }
}

// One quiet line, at most once per browser session, and only on a product page. It never moves and
// never opens the chat by itself. It sits in the bottom bar or the gutter, so it can't cover anything.
export function ChatNudge() {
  const { panelOpen, openPanel } = useSharedChat()
  const onProduct = useMatch('/products/:slug') !== null
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!onProduct || panelOpen || visible || seen()) return
    const show = () => {
      markSeen()
      setVisible(true)
    }

    let timer = setTimeout(show, QUIET_MS)
    const restart = () => {
      clearTimeout(timer)
      timer = setTimeout(show, QUIET_MS)
    }

    const page = document.getElementById('page')
    const onScroll = () => {
      if (!page || window.matchMedia(DESKTOP).matches) return
      const room = page.scrollHeight - page.clientHeight
      if (room > 0 && page.scrollTop / room >= SCROLLED) show()
    }

    document.addEventListener('click', restart)
    document.addEventListener('keydown', restart)
    page?.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      clearTimeout(timer)
      document.removeEventListener('click', restart)
      document.removeEventListener('keydown', restart)
      page?.removeEventListener('scroll', onScroll)
    }
  }, [onProduct, panelOpen, visible])

  if (!visible || !onProduct || panelOpen) return null

  return (
    <div role="status" className="flex min-w-0 flex-1 items-start gap-1 text-sm xl:flex-none xl:flex-col">
      <button type="button" onClick={openPanel} className="min-h-6 text-left underline hover:text-cobalt">
        Questions? Ask support.
      </button>
      <button
        type="button"
        onClick={() => setVisible(false)}
        aria-label="Dismiss"
        className="size-6 shrink-0 text-muted hover:text-ink"
      >
        ×
      </button>
    </div>
  )
}
