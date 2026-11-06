import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { api } from '../../shared/api/client'
import type { User } from '../../shared/api/types'

export function OrdersView({ user }: { user: User }) {
  const queryClient = useQueryClient()
  const orders = useQuery({ queryKey: ['orders'], queryFn: api.orders })
  const [params] = useSearchParams()
  const placed = params.get('placed')
  const staff = user.role !== 'customer'
  const deliver = useMutation({
    mutationFn: api.deliver,
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  })
  const reset = useMutation({
    mutationFn: api.resetOrders,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['refunds'] })
    },
  })

  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="mx-auto w-full max-w-page px-4 py-8">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <title>{`${staff ? 'All orders' : 'Your orders'} · ShopHelper`}</title>
            <h1 className="text-title font-semibold">{staff ? 'All orders' : 'Your orders'}</h1>
            <p className="mt-1 text-muted">
              {staff ? 'Mark an order delivered to make it refundable.' : 'Questions about an order? Ask in the chat.'}
            </p>
          </div>
          {user.role === 'admin' && (
            <button type="button"
              onClick={() => reset.mutate()}
              disabled={reset.isPending}
              className="rounded border border-rule bg-paper px-3 py-1.5 text-sm disabled:opacity-50"
            >
              Reset demo orders
            </button>
          )}
        </div>
        {placed && (
          <p role="status" className="mt-3 border-l-4 border-cobalt bg-shelf px-3 py-2">
            Thanks, your order {placed} is placed. You can ask the chat about it at any time.
          </p>
        )}
        {orders.isError && <p className="mt-3 text-sm text-danger">{orders.error.message}</p>}
        {deliver.isError && (
          <p role="alert" className="mt-3 text-sm text-danger">
            {deliver.error.message}
          </p>
        )}
        {/* biome-ignore lint/a11y/noNoninteractiveTabindex: a scrollable table must be reachable by keyboard (021 T090) */}
        {/* biome-ignore lint/a11y/useSemanticElements: a scrollable table must be reachable by keyboard (021 T090) */}
        <div role="region" aria-label="Orders" tabIndex={0} className="mt-4 overflow-x-auto rounded border border-rule bg-paper">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted">
              <tr className="border-b border-rule">
                <th className="px-3 py-2 font-medium">Order</th>
                {staff && <th className="px-3 py-2 font-medium">Customer</th>}
                <th className="px-3 py-2 font-medium">Item</th>
                <th className="px-3 py-2 text-right font-medium">Total</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Delivered</th>
                {staff && <th className="px-3 py-2 font-medium">Action</th>}
              </tr>
            </thead>
            <tbody>
              {orders.data?.map((order) => (
                <tr key={order.order_id} className="border-b border-rule last:border-0">
                  <td className="px-3 py-2 font-mono">{order.order_id}</td>
                  {staff && <td className="px-3 py-2">{order.customer}</td>}
                  <td className="px-3 py-2">{order.item}</td>
                  <td className="px-3 py-2 text-right tabular-nums">${order.total.toFixed(2)}</td>
                  <td className="px-3 py-2">{order.status}</td>
                  <td className="px-3 py-2 text-muted">{order.delivered_at ?? '-'}</td>
                  {staff && (
                    <td className="px-3 py-2">
                      {(order.status === 'processing' || order.status === 'shipped') && (
                        <button type="button"
                          onClick={() => deliver.mutate(order.order_id)}
                          disabled={deliver.isPending}
                          aria-label={`Mark delivered, order ${order.order_id}`}
                          className="min-h-8 rounded border border-field px-2 whitespace-nowrap hover:border-cobalt disabled:opacity-50"
                        >
                          Mark delivered
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
