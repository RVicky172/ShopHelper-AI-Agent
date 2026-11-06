import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import type { Role, User } from '../../shared/api/types'
import { signInPath } from './next'

// Convenience only: the server enforces the real rules on every request.
export function RequireAuth({
  user,
  roles,
  children,
}: {
  user: User | null
  roles?: Role[]
  children: ReactNode
}) {
  const location = useLocation()
  if (!user) return <Navigate to={signInPath(location)} replace />
  if (roles && !roles.includes(user.role)) {
    return (
      <div className="mx-auto w-full max-w-page px-4 py-16">
        <title>No access · ShopHelper</title>
        <h1 className="text-title font-semibold">You don't have access to this page</h1>
        <p className="mt-2 text-muted">It's for staff only. If that's a mistake, ask an admin.</p>
      </div>
    )
  }
  return children
}
