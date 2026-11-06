import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../../shared/api/client'
import type { QueuedRefund, User } from '../../shared/api/types'

function RefundRow({ refund, reviewer }: { refund: QueuedRefund; reviewer: User }) {
  const queryClient = useQueryClient()
  const [note, setNote] = useState('')
  const decide = useMutation({
    mutationFn: (approved: boolean) => api.decide(refund.session_id, approved, note),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['refunds'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })

  const needsAdmin = refund.needs_supervisor && reviewer.role !== 'admin'
  const processing = refund.status === 'claimed'

  return (
    <li className="rounded border border-rule bg-paper p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-medium">
          Order <span className="font-mono">{refund.order_id}</span>, {refund.item}
        </p>
        <p className="tabular-nums">${refund.amount.toFixed(2)}</p>
      </div>
      <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-sm">
        <dt className="text-muted">Customer</dt>
        <dd>{refund.customer}</dd>
        <dt className="text-muted">Reason</dt>
        <dd>{refund.reason || 'None given'}</dd>
      </dl>
      {refund.needs_supervisor && <p className="mt-2 text-sm font-medium">Over $200: an admin must decide this one.</p>}
      {processing ? (
        <p className="mt-3 text-sm text-muted">Decided. The agent is finishing this conversation.</p>
      ) : (
        !needsAdmin && (
          <div className="mt-3 space-y-2">
            <label className="block text-xs text-muted">
              Note (optional)
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={500}
                className="mt-0.5 w-full rounded border border-field bg-paper px-2 py-1.5 text-sm text-ink"
              />
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={decide.isPending}
                onClick={() => decide.mutate(true)}
                className="rounded bg-cobalt px-3 py-1.5 text-sm font-medium text-on-cobalt disabled:opacity-50"
              >
                {decide.isPending ? 'Working...' : 'Approve refund'}
              </button>
              <button
                type="button"
                disabled={decide.isPending}
                onClick={() => decide.mutate(false)}
                className="rounded border border-rule px-3 py-1.5 text-sm font-medium disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          </div>
        )
      )}
      {decide.isError && (
        <p role="alert" className="mt-2 text-sm text-danger">
          {decide.error.message}
        </p>
      )}
    </li>
  )
}

export function QueueView({ user }: { user: User }) {
  const refunds = useQuery({ queryKey: ['refunds'], queryFn: api.refunds, refetchInterval: 5000 })

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-page px-4 py-8">
        <title>Refund queue · ShopHelper</title>
        <h1 className="text-title font-semibold">Refund queue</h1>
        <p className="mt-1 max-w-3xl text-muted">
          The agent paused each of these and is waiting for a person. Your decision resumes it, acting as the customer.
          You're recorded as the reviewer.
        </p>
        {refunds.isError && <p className="mt-3 text-sm text-danger">{refunds.error.message}</p>}
        {refunds.data?.length === 0 && (
          <p className="mt-6 rounded border border-rule bg-paper p-4 text-sm text-muted">
            Nothing is waiting. Sign in as a customer and ask for a refund to fill this queue.
          </p>
        )}
        <ul className="mt-4 space-y-3">
          {refunds.data?.map((refund) => (
            <RefundRow key={refund.id} refund={refund} reviewer={user} />
          ))}
        </ul>
      </div>
    </div>
  )
}
