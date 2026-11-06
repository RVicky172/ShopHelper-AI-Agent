import { type ReactNode, useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router'

// A button that shows a list of links. Links stay links, so they work with a keyboard, open in
// a new tab, and need no arrow-key handling.
export function Menu({
  label,
  align = 'left',
  children,
}: {
  label: ReactNode
  align?: 'left' | 'right'
  children: ReactNode
}) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const { pathname, search } = useLocation()

  useEffect(() => setOpen(false), [pathname, search])

  useEffect(() => {
    if (!open) return
    const onPointer = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      setOpen(false)
      button.current?.focus()
    }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: only watches focus leaving the menu
    <div
      ref={root}
      className="relative"
      onBlur={(event) => {
        // Tabbing past the last link closes the menu, so it can't sit over the page unnoticed.
        if (event.relatedTarget && !root.current?.contains(event.relatedTarget)) setOpen(false)
      }}
    >
      <button
        type="button"
        ref={button}
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex min-h-11 items-center gap-1 hover:text-cobalt"
      >
        {label}
        <svg aria-hidden="true" viewBox="0 0 12 12" className={`size-3 ${open ? 'rotate-180' : ''}`}>
          <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </button>
      {open && (
        <div
          className={`absolute top-full z-30 min-w-56 border border-rule bg-paper py-1 ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
        >
          {children}
        </div>
      )}
    </div>
  )
}

export function MenuLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="flex min-h-11 items-center px-4 hover:bg-shelf">
      {children}
    </Link>
  )
}

export function MenuButton({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} className="flex min-h-11 w-full items-center px-4 text-left hover:bg-shelf">
      {children}
    </button>
  )
}
