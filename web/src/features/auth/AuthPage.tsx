import { useQuery } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Link, Navigate, useLocation, useSearchParams } from 'react-router'
import { api } from '../../shared/api/client'
import type { DemoAccount, Role } from '../../shared/api/types'
import { safeNext, signInPath } from './next'
import type { useAuth } from './useAuth'

const LEVELS: Partial<Record<Role, string>> = {
  support: 'Sees all orders, reviews refunds up to $200',
  admin: 'Reviews any refund, manages users',
}

function DemoAccounts({ accounts, onPick }: { accounts: DemoAccount[]; onPick: (a: DemoAccount) => void }) {
  const staff = accounts.filter((a) => a.role !== 'customer')
  const customers = accounts.filter((a) => a.role === 'customer')
  return (
    <section className="mt-6 surface-solid p-4">
      <h2 className="text-sm font-semibold">Demo accounts</h2>
      <p className="mt-0.5 text-xs text-muted">
        Sign in as each level to see the same app from each side. All use the password{' '}
        <code className="font-mono">{accounts[0].password}</code>.
      </p>
      <ul className="mt-3 space-y-1.5">
        {staff.map((account) => (
          <li key={account.email}>
            <button
              type="button"
              onClick={() => onPick(account)}
              className="w-full rounded-xl border border-rule px-3 py-1.5 text-left text-sm hover:border-cobalt"
            >
              <span className="font-medium">{account.display_name}</span>
              <span className="block text-xs text-muted">{LEVELS[account.role]}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-muted">Customers each see only their own orders and chats.</p>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {customers.map((account) => (
          <button
            type="button"
            key={account.email}
            onClick={() => onPick(account)}
            className="rounded-xl border border-rule px-2.5 py-1 text-sm hover:border-cobalt"
          >
            {account.display_name}
          </button>
        ))}
      </div>
    </section>
  )
}

export function AuthPage({ auth, mode }: { auth: ReturnType<typeof useAuth>; mode: 'login' | 'signup' }) {
  const location = useLocation()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const demo = useQuery({ queryKey: ['demo-accounts'], queryFn: api.demoAccounts })

  const active = mode === 'login' ? auth.login : auth.signup
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (mode === 'login') auth.login.mutate({ email, password })
    else auth.signup.mutate({ email, password, name })
  }

  // Signing in rebuilds the app with the new user and lands here, which sends them back.
  if (auth.user) return <Navigate to={safeNext(params.get('next'))} replace />

  const tabs = {
    login: { to: signInPath(location), label: 'Sign in' },
    signup: { to: signInPath(location).replace('/signin', '/signup'), label: 'Create account' },
  }

  return (
    <div className="px-4 py-10">
      <title>{`${tabs[mode].label} · ShopHelper`}</title>
      <div className="mx-auto max-w-md">
        <h1 className="text-title font-semibold">{tabs[mode].label}</h1>

        <div className="mt-6 surface-solid p-4">
          <nav aria-label="Sign in or create an account" className="flex gap-1">
            {(['login', 'signup'] as const).map((option) => (
              <Link
                key={option}
                to={tabs[option].to}
                aria-current={mode === option ? 'page' : undefined}
                onClick={() => {
                  auth.login.reset()
                  auth.signup.reset()
                }}
                className={`rounded px-2.5 py-1 text-sm ${
                  mode === option ? 'bg-shelf font-medium' : 'text-muted hover:text-ink'
                }`}
              >
                {tabs[option].label}
              </Link>
            ))}
          </nav>

          <form className="mt-4 space-y-3" onSubmit={submit}>
            {mode === 'signup' && (
              <label className="block text-sm">
                Name
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={64}
                  autoComplete="name"
                  className="mt-1 w-full rounded-xl border border-field bg-paper px-3 py-2"
                />
              </label>
            )}
            <label className="block text-sm">
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="mt-1 w-full rounded-xl border border-field bg-paper px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                className="mt-1 w-full rounded-xl border border-field bg-paper px-3 py-2"
              />
              {mode === 'signup' && <span className="mt-1 block text-xs text-muted">At least 8 characters.</span>}
            </label>
            {active.isError && (
              <p role="alert" className="text-sm text-danger">
                {active.error.message}
              </p>
            )}
            <button
              type="submit"
              disabled={active.isPending}
              className="min-h-11 w-full rounded-xl bg-cobalt px-4 py-2 text-sm font-medium text-on-cobalt disabled:opacity-50"
            >
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>

        {demo.data && demo.data.length > 0 && (
          <DemoAccounts
            accounts={demo.data}
            onPick={(a) => auth.login.mutate({ email: a.email, password: a.password })}
          />
        )}
      </div>
    </div>
  )
}
