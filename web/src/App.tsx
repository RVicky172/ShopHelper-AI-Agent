import { lazy } from 'react'
import { Route, Routes } from 'react-router'
import { AuthPage } from './auth/AuthPage'
import { RequireAuth } from './auth/RequireAuth'
import { useAuth } from './auth/useAuth'
import { CartPage } from './cart/CartPage'
import { CheckoutPage } from './cart/CheckoutPage'
import { CartProvider } from './cart/useCart'
import { ChatProvider } from './chat/ChatProvider'
import { Layout } from './layout/Layout'
import { NotFound } from './layout/NotFound'
import { CategoryPage } from './shop/CategoryPage'
import { Landing } from './shop/Landing'
import { ProductPage } from './shop/ProductPage'
import { OrdersView } from './views/OrdersView'
import { QueueView } from './views/QueueView'
import { UsersView } from './views/UsersView'

const ReturnsPolicy = lazy(() => import('./shop/ReturnsPolicy').then((m) => ({ default: m.ReturnsPolicy })))
const HowItWorks = lazy(() => import('./views/HowItWorks').then((m) => ({ default: m.HowItWorks })))

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
