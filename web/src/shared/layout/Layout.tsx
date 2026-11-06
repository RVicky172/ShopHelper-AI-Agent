import { lazy, type RefObject, Suspense, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Outlet, useLocation, useMatch, useNavigationType } from 'react-router'
import type { useAuth } from '../../features/auth/useAuth'
import { changeMessage } from '../../features/cart/cartLogic'
import { useCart } from '../../features/cart/useCart'
import { ChatLauncher } from '../../features/chat/ChatLauncher'
import { useSharedChat } from '../../features/chat/ChatProvider'
import { Navbar } from './Navbar'

// Loaded on first use, so the landing page doesn't carry the Markdown renderer.
const ChatPanel = lazy(() => import('../../features/chat/ChatPanel').then((m) => ({ default: m.ChatPanel })))

function Footer() {
  return (
    <footer className="border-t border-rule bg-shelf">
      <p className="mx-auto w-full max-w-page px-4 py-6 text-sm text-muted">
        ShopHelper is a learning project. Orders are pretend, and nothing is charged or shipped.
      </p>
    </footer>
  )
}

// Shown on whichever page the shopper lands on after signing in, so a merge is never silent.
function CartNotice() {
  const { changes, failed, dismiss } = useCart()
  if (!changes.length && !failed) return null
  return (
    <div role="status" className="border-b border-rule bg-shelf">
      <div className="mx-auto flex w-full max-w-page items-start justify-between gap-4 px-4 py-3">
        <div>
          {failed && <p>We couldn't update your cart. Please try again.</p>}
          {changes.map((change) => (
            <p key={`${change.kind}-${change.product_id}`}>{changeMessage(change)}</p>
          ))}
        </div>
        <button onClick={dismiss} className="min-h-6 text-sm underline">
          Dismiss
        </button>
      </div>
    </div>
  )
}

const DESKTOP = '(min-width: 1280px)'

function useDesktop() {
  const [desktop, setDesktop] = useState(() => window.matchMedia(DESKTOP).matches)
  useEffect(() => {
    const query = window.matchMedia(DESKTOP)
    const onChange = () => setDesktop(query.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])
  return desktop
}

// The page scrolls in its own region, which ends above the bottom bar, so nothing can slide under the
// bar. The browser only restores scroll positions for the window, so Back is handled here.
function useScrollMemory(page: RefObject<HTMLDivElement | null>, main: RefObject<HTMLElement | null>, chatOpen: boolean) {
  const { key } = useLocation()
  const navigation = useNavigationType()
  const positions = useRef(new Map<string, number>())
  const first = useRef(true)
  const keepFocus = useRef(chatOpen)
  keepFocus.current = chatOpen

  // A new page makes no sound and leaves focus nowhere, so move it to the content. A screen reader then
  // reads the new page, and Tab carries on from there. Not on first load, and not out of an open chat.
  useEffect(() => {
    if (!first.current && navigation !== 'POP' && !keepFocus.current) main.current?.focus({ preventScroll: true })
    first.current = false
  }, [key, navigation, main])

  useLayoutEffect(() => {
    const element = page.current
    if (!element) return
    element.scrollTop = navigation === 'POP' ? (positions.current.get(key) ?? 0) : 0
    const onScroll = () => positions.current.set(key, element.scrollTop)
    element.addEventListener('scroll', onScroll, { passive: true })
    return () => element.removeEventListener('scroll', onScroll)
  }, [key, navigation, page])
}

export function Layout({ auth }: { auth: ReturnType<typeof useAuth> }) {
  const fullHeight = useMatch('/how-it-works/trace') !== null // its panels scroll, not the page
  const { panelOpen } = useSharedChat()
  const desktop = useDesktop()
  const page = useRef<HTMLDivElement>(null)
  const main = useRef<HTMLElement>(null)
  useScrollMemory(page, main, panelOpen)

  return (
    <div className="flex h-dvh flex-col bg-paper text-ink">
      {/* On a phone the chat fills the screen, so the page behind it leaves the tab order. */}
      <div
        id="page"
        ref={page}
        inert={panelOpen && !desktop}
        className={`flex min-h-0 flex-1 scroll-pt-32 scroll-pb-6 flex-col overflow-x-hidden ${
          fullHeight ? 'overflow-y-hidden' : 'overflow-y-auto'
        }`}
      >
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:z-40 focus:bg-paper focus:px-4 focus:py-2"
        >
          Skip to content
        </a>
        <Navbar auth={auth} />
        <CartNotice />
        <main
          id="main"
          ref={main}
          tabIndex={-1}
          className={`flex flex-col outline-none ${fullHeight ? 'min-h-0 flex-1' : 'flex-[1_0_auto]'}`}
        >
          <Suspense fallback={null}>
            <Outlet />
          </Suspense>
        </main>
        {!fullHeight && <Footer />}
      </div>
      <ChatLauncher />
      {panelOpen && (
        <Suspense fallback={null}>
          <ChatPanel user={auth.user} />
        </Suspense>
      )}
    </div>
  )
}
