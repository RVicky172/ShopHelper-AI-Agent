import type {
  CartView,
  Category,
  Chunk,
  ConversationDetail,
  ConversationSummary,
  DemoAccount,
  MergeResult,
  Order,
  ProductDetail,
  ProductPage,
  ProductSort,
  QueuedRefund,
  RagSearchResult,
  Role,
  SystemInfo,
  User,
} from './types'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

// Vite proxies /api/* to the FastAPI server, so the browser sees one origin and needs no CORS.
// The session cookie is HttpOnly: this code never sees it, the browser just sends it.
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed: ${response.status}`
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function send<T>(method: string, path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

export const api = {
  me: () => request<User>('/auth/me'),
  login: (email: string, password: string) => send<User>('POST', '/auth/login', { email, password }),
  signup: (email: string, password: string, display_name: string) =>
    send<User>('POST', '/auth/signup', { email, password, display_name }),
  logout: () => send<void>('POST', '/auth/logout'),
  demoAccounts: () => request<DemoAccount[]>('/auth/demo-accounts'),

  categories: () => request<Category[]>('/categories'),
  products: (category: string | null, sort: ProductSort, offset: number, limit = 12) => {
    const query = new URLSearchParams({ sort, offset: String(offset), limit: String(limit) })
    if (category) query.set('category', category)
    return request<ProductPage>(`/products?${query}`)
  },
  product: (slug: string) => request<ProductDetail>(`/products/${encodeURIComponent(slug)}`),
  productsByIds: (ids: number[]) => {
    const query = new URLSearchParams(ids.map((id) => ['ids', String(id)]))
    return request<ProductPage>(`/products?${query}`)
  },

  cart: () => request<CartView>('/cart'),
  setCartItem: (id: number, quantity: number) => send<CartView>('PUT', `/cart/${id}`, { quantity }),
  mergeCart: (items: { product_id: number; quantity: number }[]) => send<MergeResult>('POST', '/cart/merge', { items }),
  checkout: () => send<Order>('POST', '/checkout'),
  deliver: (orderId: string) => send<Order>('POST', `/orders/${orderId}/deliver`),

  conversations: () => request<ConversationSummary[]>('/conversations'),
  conversation: (id: string) => request<ConversationDetail>(`/conversations/${id}`),
  createConversation: () => send<{ id: string }>('POST', '/conversations'),

  refunds: () => request<QueuedRefund[]>('/refunds/pending'),
  decide: (session_id: string, approved: boolean, note: string) =>
    send<unknown>('POST', '/approve', { session_id, approved, note }),

  users: () => request<User[]>('/admin/users'),
  setRole: (id: number, role: Role) => send<User>('PATCH', `/admin/users/${id}`, { role }),

  system: () => request<SystemInfo>('/system'),
  orders: () => request<Order[]>('/orders'),
  resetOrders: () => send<unknown>('POST', '/demo/reset'),
  chunks: () => request<Chunk[]>('/rag/chunks'),
  ragSearch: (q: string, k: number) => request<RagSearchResult>(`/rag/search?q=${encodeURIComponent(q)}&k=${k}`),
}
