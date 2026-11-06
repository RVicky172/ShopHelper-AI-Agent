import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../shared/api/client'
import type { User } from '../../shared/api/types'

async function currentUser(): Promise<User | null> {
  try {
    return await api.me()
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}

export function useAuth() {
  const queryClient = useQueryClient()
  const me = useQuery({ queryKey: ['me'], queryFn: currentUser, refetchInterval: 30_000 })

  // Starting from an empty cache means nothing fetched for one user can show for the next.
  const startSession = (user: User) => {
    queryClient.clear()
    queryClient.setQueryData(['me'], user)
  }

  const login = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => api.login(email, password),
    onSuccess: startSession,
  })

  const signup = useMutation({
    mutationFn: ({ email, password, name }: { email: string; password: string; name: string }) =>
      api.signup(email, password, name),
    onSuccess: startSession,
  })

  const logout = useMutation({
    mutationFn: api.logout,
    onSettled: () => {
      queryClient.clear()
      queryClient.setQueryData(['me'], null)
    },
  })

  return { user: me.data ?? null, loading: me.isPending, failed: me.isError, login, signup, logout }
}
