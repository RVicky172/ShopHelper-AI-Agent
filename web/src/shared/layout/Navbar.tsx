import { useQuery } from '@tanstack/react-query'
import { Link, NavLink, useLocation, useNavigate } from 'react-router'
import { signInPath } from '../../features/auth/next'
import type { useAuth } from '../../features/auth/useAuth'
import { useCart } from '../../features/cart/useCart'
import { api } from '../api/client'
import type { User } from '../api/types'
import { Menu, MenuButton, MenuLink } from './Menu'

function ShopMenu() {
  const categories = useQuery({ queryKey: ['categories'], queryFn: api.categories, staleTime: Infinity })
  return (
    <Menu label="Shop">
      <MenuLink to="/shop/all">All products</MenuLink>
      {categories.data?.map((category) => (
        <MenuLink key={category.slug} to={`/shop/${category.slug}`}>
          {category.name}
        </MenuLink>
      ))}
    </Menu>
  )
}

function AccountMenu({ user, onLogout }: { user: User; onLogout: () => void }) {
  const staff = user.role !== 'customer'
  return (
    <Menu label={user.display_name} align="right">
      {!staff && <MenuLink to="/account/orders">Your orders</MenuLink>}
      {staff && <MenuLink to="/staff/refunds">Refund queue</MenuLink>}
      {staff && <MenuLink to="/staff/orders">All orders</MenuLink>}
      {user.role === 'admin' && <MenuLink to="/admin/users">Users</MenuLink>}
      <MenuButton onClick={onLogout}>Log out</MenuButton>
    </Menu>
  )
}

export function CartLink() {
  const { view, added } = useCart()
  return (
    <Link
      to="/cart"
      aria-label={`Cart, ${view.count} ${view.count === 1 ? 'item' : 'items'}`}
      className="flex min-h-11 items-center gap-1.5 hover:text-cobalt"
    >
      <svg aria-hidden="true" viewBox="0 0 24 24" className="size-6">
        <path
          d="M4 8h16l-1.2 12H5.2L4 8zm4 0V6a4 4 0 0 1 8 0v2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinejoin="round"
        />
      </svg>
      {view.count > 0 && (
        // The key restarts the tick each time something is added.
        <span
          key={added}
          className={`min-w-6 rounded-full bg-marigold px-1.5 text-center text-sm font-semibold text-on-marigold ${
            added > 0 ? 'cart-tick' : ''
          }`}
        >
          {view.count}
        </span>
      )}
    </Link>
  )
}

export function Navbar({ auth }: { auth: ReturnType<typeof useAuth> }) {
  const location = useLocation()
  const navigate = useNavigate()
  const logout = () => {
    navigate('/')
    auth.logout.mutate()
  }

  return (
    <header className="sticky top-0 z-20 border-b border-rule bg-paper">
      <div className="mx-auto flex w-full max-w-page flex-wrap items-center gap-x-6 px-4">
        <Link to="/" className="flex min-h-14 items-center text-xl font-semibold tracking-tight">
          ShopHelper
        </Link>
        <nav aria-label="Main" className="order-last flex w-full items-center gap-x-6 sm:order-none sm:w-auto">
          <ShopMenu />
          <NavLink
            to="/how-it-works"
            className={({ isActive }) =>
              `flex min-h-11 items-center hover:text-cobalt ${isActive ? 'font-medium text-cobalt' : ''}`
            }
          >
            How it works
          </NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-x-5">
          {auth.user ? (
            <AccountMenu user={auth.user} onLogout={logout} />
          ) : (
            <Link to={signInPath(location)} className="flex min-h-11 items-center hover:text-cobalt">
              Sign in
            </Link>
          )}
          <CartLink />
        </div>
      </div>
    </header>
  )
}
