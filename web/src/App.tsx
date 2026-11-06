import { lazy } from 'react'
import { Route, Routes } from 'react-router'
import { AuthPage } from './features/auth/AuthPage'
import { RequireAuth } from './features/auth/RequireAuth'
import { useAuth } from './features/auth/useAuth'
import { CartPage } from './features/cart/CartPage'
import { CheckoutPage } from './features/cart/CheckoutPage'
import { CartProvider } from './features/cart/useCart'
import { ChatProvider } from './features/chat/ChatProvider'
import { Layout } from './shared/layout/Layout'
import { NotFound } from './shared/layout/NotFound'
import { CategoryPage } from './features/shop/CategoryPage'
import { Landing } from './features/shop/Landing'
import { ProductPage } from './features/shop/ProductPage'
import { OrdersView } from './features/shop/OrdersView'
import { QueueView } from './features/staff/QueueView'
import { UsersView } from './features/staff/UsersView'

const ReturnsPolicy = lazy(() => import('./features/shop/ReturnsPolicy').then((m) => ({ default: m.ReturnsPolicy })))
const HowItWorks = lazy(() => import('./features/how-it-works/HowItWorks').then((m) => ({ default: m.HowItWorks })))

export function App() {
  const auth = useAuth()
  const { user } = auth

  if (auth.loading) return <div className="h-dvh bg-paper" />
  if (auth.failed) {
    return (
      <p role="alert" className="min-h-dvh bg-paper p-6 text-sm text-ink">
        Can't reach the API. Check `docker compose ps`.
      </p>
    )
  }

  // The key rebuilds everything when the user changes, so no state can carry over between people.
  return (
    <ChatProvider key={user?.id ?? 'guest'} user={user}>
      <CartProvider user={user}>
      <Routes>
        <Route element={<Layout auth={auth} />}>
          <Route index element={<Landing />} />
          <Route path="shop/:category" element={<CategoryPage />} />
          <Route path="products/:slug" element={<ProductPage />} />
          <Route path="policies/returns" element={<ReturnsPolicy />} />
          <Route path="cart" element={<CartPage user={user} />} />
          <Route
            path="checkout"
            element={<RequireAuth user={user}>{user && <CheckoutPage user={user} />}</RequireAuth>}
          />
          <Route path="signin" element={<AuthPage auth={auth} mode="login" />} />
          <Route path="signup" element={<AuthPage auth={auth} mode="signup" />} />
          <Route
            path="account/orders"
            element={<RequireAuth user={user}>{user && <OrdersView user={user} />}</RequireAuth>}
          />
          <Route
            path="staff/refunds"
            element={
              <RequireAuth user={user} roles={['support', 'admin']}>
                {user && <QueueView user={user} />}
              </RequireAuth>
            }
          />
          <Route
            path="staff/orders"
            element={
              <RequireAuth user={user} roles={['support', 'admin']}>
                {user && <OrdersView user={user} />}
              </RequireAuth>
            }
          />
          <Route
            path="admin/users"
            element={
              <RequireAuth user={user} roles={['admin']}>
                {user && <UsersView me={user} />}
              </RequireAuth>
            }
          />
          <Route
            path="how-it-works/*"
            element={<RequireAuth user={user}>{user && <HowItWorks user={user} />}</RequireAuth>}
          />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
      </CartProvider>
    </ChatProvider>
  )
}
