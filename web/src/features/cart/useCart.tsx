import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../shared/api/client'
import type { CartProduct, CartView, MergeChange, User } from '../../shared/api/types'
import { buildView, type GuestItem, MAX_QUANTITY, parseGuestCart, setQuantity as setGuestQuantity } from './cartLogic'

const GUEST_KEY = 'shophelper.guest-cart'
const CART = ['cart']
const EMPTY: CartView = { items: [], count: 0, total: 0 }

function readGuest(): GuestItem[] {
  try {
    return parseGuestCart(localStorage.getItem(GUEST_KEY))
  } catch {
    return [] // storage blocked: the cart still works until the page closes
  }
}

function writeGuest(items: GuestItem[]) {
  try {
    if (items.length) localStorage.setItem(GUEST_KEY, JSON.stringify(items))
    else localStorage.removeItem(GUEST_KEY)
  } catch {
    // storage blocked
  }
}

interface Cart {
  view: CartView
  loading: boolean
  added: number // goes up on each add, so the navbar can tick
  changes: MergeChange[]
  failed: boolean
  add: (product: CartProduct, quantity: number) => number
  setQuantity: (product: CartProduct, quantity: number) => void
  dismiss: () => void
}

const CartContext = createContext<Cart | null>(null)

// A signed-in cart lives only on the server and in the query cache, which is cleared at logout, so
// nothing of it stays in the browser. Sits under the provider keyed by user, so it restarts for each person.
export function CartProvider({ user, children }: { user: User | null; children: ReactNode }) {
  const queryClient = useQueryClient()
  const [guest, setGuest] = useState<GuestItem[]>(() => (user ? [] : readGuest()))
  const [changes, setChanges] = useState<MergeChange[]>([])
  const [failed, setFailed] = useState(false)
  const [added, setAdded] = useState(0)

  const server = useQuery({ queryKey: CART, queryFn: api.cart, enabled: Boolean(user) })

  const ids = guest.map((item) => item.product_id).sort((a, b) => a - b)
  const products = useQuery({
    queryKey: ['products', 'ids', ids],
    queryFn: () => api.productsByIds(ids),
    enabled: !user && ids.length > 0,
    placeholderData: keepPreviousData,
  })

  // Join a guest's items to the account. Taking them out of storage first means a repeat run finds
  // nothing, so React's double effects in development and a second tab can't add them twice.
  useEffect(() => {
    if (!user) return
    const items = readGuest()
    if (!items.length) return
    writeGuest([])
    api
      .mergeCart(items)
      .then(async (result) => {
        await queryClient.cancelQueries({ queryKey: CART }) // an older read mustn't overwrite this
        queryClient.setQueryData(CART, result.cart)
        setChanges(result.changes)
      })
      .catch(() => {
        writeGuest(items) // nothing is lost: the next sign-in or reload tries again
        setFailed(true)
      })
  }, [user, queryClient])

  // A guest with two tabs open sees one cart.
  useEffect(() => {
    if (user) return
    const onStorage = (event: StorageEvent) => {
      if (event.key === GUEST_KEY) setGuest(parseGuestCart(event.newValue))
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [user])

  // `scope` runs these one at a time, in order, so quick clicks can't arrive out of order.
  const save = useMutation({
    mutationKey: CART,
    scope: { id: 'cart' },
    mutationFn: ({ id, quantity }: { id: number; quantity: number }) => api.setCartItem(id, quantity),
    onSuccess: (cart) => {
      if (queryClient.isMutating({ mutationKey: CART }) === 1) queryClient.setQueryData(CART, cart)
    },
    onError: () => {
      setFailed(true)
      void queryClient.invalidateQueries({ queryKey: CART })
    },
  })
  const saveItem = save.mutate

  const guestRef = useRef(guest)
  guestRef.current = guest

  const change = useCallback(
    (product: CartProduct, quantity: (current: number) => number): number => {
      setFailed(false)
      if (!user) {
        const current = guestRef.current.find((item) => item.product_id === product.id)?.quantity ?? 0
        const next = quantity(current)
        const items = setGuestQuantity(guestRef.current, product.id, next)
        guestRef.current = items
        writeGuest(items)
        setGuest(items)
        return next - current
      }
      const view = queryClient.getQueryData<CartView>(CART) ?? EMPTY
      const current = view.items.find((line) => line.product.id === product.id)?.quantity ?? 0
      const next = quantity(current)
      const others = view.items.filter((line) => line.product.id !== product.id)
      queryClient.setQueryData(CART, buildView(next > 0 ? [...others, { product, quantity: next }] : others))
      saveItem({ id: product.id, quantity: next })
      return next - current
    },
    [queryClient, saveItem, user],
  )

  const value = useMemo<Cart>(() => {
    const byId = new Map(products.data?.items.map((product) => [product.id, product]))
    const guestLines = guest.flatMap((item) => {
      const product = byId.get(item.product_id)
      return product ? [{ product, quantity: item.quantity }] : []
    })
    const guestCount = guest.reduce((sum, item) => sum + item.quantity, 0)
    return {
      view: user ? (server.data ?? EMPTY) : { ...buildView(guestLines), count: guestCount },
      loading: user ? server.isPending : ids.length > 0 && products.isPending,
      added,
      changes,
      failed,
      add: (product, quantity) => {
        const count = change(product, (current) => Math.min(current + quantity, MAX_QUANTITY))
        if (count > 0) setAdded((n) => n + 1)
        return count
      },
      setQuantity: (product, quantity) => void change(product, () => quantity),
      dismiss: () => {
        setChanges([])
        setFailed(false)
      },
    }
  }, [added, change, changes, failed, guest, ids.length, products.data, products.isPending, server.data, server.isPending, user])

  return <CartContext value={value}>{children}</CartContext>
}

export function useCart(): Cart {
  const cart = useContext(CartContext)
  if (!cart) throw new Error('useCart needs a CartProvider above it')
  return cart
}
