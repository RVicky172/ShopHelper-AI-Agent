import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../shared/api/client'
import type { Role, User } from '../../shared/api/types'

const ROLES: Role[] = ['customer', 'support', 'admin']

export function UsersView({ me }: { me: User }) {
  const queryClient = useQueryClient()
  const users = useQuery({ queryKey: ['users'], queryFn: api.users })
  const change = useMutation({
    mutationFn: ({ id, role }: { id: number; role: Role }) => api.setRole(id, role),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-page px-gutter py-8">
        <title>Users · ShopHelper</title>
        <h1 className="text-title font-semibold">Users</h1>
        <p className="mt-1 max-w-3xl text-muted">
          A change applies on that person's next request, because the level is read fresh every time.
        </p>
        {change.isError && (
          <p role="alert" className="mt-3 text-sm text-danger">
            {change.error.message}
          </p>
        )}
        {/* biome-ignore lint/a11y/useSemanticElements: a scrollable table must be reachable by keyboard (021 T090) */}
        <div
          role="region"
          aria-label="Users"
          // biome-ignore lint/a11y/noNoninteractiveTabindex: a scrollable table must be reachable by keyboard (021 T090)
          tabIndex={0}
          className="mt-4 overflow-x-auto surface-solid"
        >
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted">
              <tr className="border-b border-rule">
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Email</th>
                <th className="px-3 py-2 font-medium">Level</th>
              </tr>
            </thead>
            <tbody>
              {users.data?.map((user) => (
                <tr key={user.id} className="border-b border-rule last:border-0">
                  <td className="px-3 py-2">
                    {user.display_name}
                    {user.id === me.id && <span className="text-muted"> (you)</span>}
                  </td>
                  <td className="px-3 py-2 text-muted">{user.email}</td>
                  <td className="px-3 py-2">
                    <select
                      aria-label={`Level for ${user.display_name}`}
                      value={user.role}
                      disabled={change.isPending}
                      onChange={(e) => change.mutate({ id: user.id, role: e.target.value as Role })}
                      className="rounded-xl border border-field bg-paper px-2 py-1"
                    >
                      {ROLES.map((role) => (
                        <option key={role}>{role}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
