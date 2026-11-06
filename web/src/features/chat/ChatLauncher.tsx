import { useMatch } from 'react-router'
import { CartLink } from '../../shared/layout/Navbar'
import { useSharedChat } from './ChatProvider'
import { ChatNudge } from './ChatNudge'

// AC-25: this must never cover an Add to cart, at any scroll position. A floating button can't promise
// that, so it has its own space. Under 1280 px it's a bar below the scrolling page, not over it.
// From 1280 px it sits in the gutter left by the page's maximum width.
export function ChatLauncher() {
  const { panelOpen, openPanel, launcher } = useSharedChat()
  const inCheckout = useMatch('/checkout') !== null
  if (inCheckout) return null

  return (
    <nav
      aria-label="Chat and cart"
      className="flex h-14 shrink-0 items-center gap-3 border-t border-rule bg-paper px-4 xl:fixed xl:right-5 xl:bottom-5 xl:z-30 xl:h-auto xl:w-[76px] xl:flex-col-reverse xl:items-stretch xl:border-0 xl:bg-transparent xl:px-0"
    >
      <button
        ref={launcher}
        onClick={openPanel}
        aria-expanded={panelOpen}
        className="flex min-h-11 items-center justify-center gap-1.5 rounded bg-cobalt px-3 font-medium text-on-cobalt hover:underline xl:px-0"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5">
          <path
            d="M4 5h16v11H9l-5 4V5z"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
        Chat
      </button>
      <ChatNudge />
      <div className="ml-auto xl:hidden">
        <CartLink />
      </div>
    </nav>
  )
}
