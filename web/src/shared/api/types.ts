// The API's shapes, mirrored by hand from src/shophelper/schemas.py and service.py.

export type TurnStatus = 'answered' | 'pending_approval' | 'blocked'
export type GuardrailAction = 'passed' | 'masked' | 'blocked' | 'skipped'

export interface PendingRefund {
  order_id: string
  item: string
  order_total: number
  amount: number
  reason: string
  needs_supervisor: boolean
}

export interface ChatResponse {
  session_id: string
  status: TurnStatus
  answer: string
  tools_used: string[]
  citations: string[]
  pending_refund: PendingRefund | null
  input_tokens: number
  output_tokens: number
  latency_ms: number
  guardrail_action: GuardrailAction
  guardrail_reasons: string[]
}

export interface GuardrailData {
  stage: 'input' | 'output'
  action: GuardrailAction
  reasons: string[]
}

export interface ModelStepData {
  step: number
  tool_calls: string[]
  input_tokens: number
  output_tokens: number
  ms: number
}

export interface ToolStartData {
  id: string
  name: string
  args: Record<string, unknown>
}

export interface ToolEndData {
  id: string
  name: string
  status: 'success' | 'error'
  result: unknown
  ms: number
}

// A discriminated union: checking `event` tells TypeScript what `data` is.
export type StreamEvent =
  | { event: 'guardrail'; data: GuardrailData }
  | { event: 'model_step'; data: ModelStepData }
  | { event: 'tool_start'; data: ToolStartData }
  | { event: 'tool_end'; data: ToolEndData }
  | { event: 'token'; data: string }
  | { event: 'interrupt'; data: PendingRefund }
  | { event: 'final'; data: ChatResponse }
  | { event: 'error'; data: string }

export interface Passage {
  source: string
  chunk_index?: number
  score: number
  text: string
}

export interface RagSearchResult {
  query: string
  embedding_dimensions: number
  embedding_preview: number[]
  embed_ms: number
  passages: Passage[]
}

export interface Chunk {
  source: string
  chunk_index: number
  text: string
}

export interface Order {
  order_id: string
  customer: string
  item: string
  total: number
  status: string
  ordered_at: string
  delivered_at?: string
  estimated_delivery?: string
  refund_amount?: number
  refund_reason?: string
  items?: OrderLine[]
}

export interface OrderLine {
  product_id: number
  name: string
  price: number
  quantity: number
}

export interface ToolInfo {
  name: string
  description: string
  args: Record<string, { type?: string; title?: string; description?: string }>
  via: string
}

export interface ServiceCheck {
  ok: boolean
  detail: string
}

export interface SystemInfo {
  chat_model: string
  embedding_model: string
  llm_base_url: string
  tools_transport: string
  mcp_url: string | null
  guardrails: string
  max_steps: number
  tools: ToolInfo[]
  services: { llm: ServiceCheck; database: ServiceCheck }
}

export interface HistoryRow {
  role: 'user' | 'assistant'
  text: string
}

export type Role = 'customer' | 'support' | 'admin'

export interface User {
  id: number
  email: string
  role: Role
  display_name: string
}

export interface DemoAccount {
  email: string
  role: Role
  display_name: string
  password: string
}

export interface ConversationSummary {
  id: string
  title: string
  updated_at: string
}

export interface ConversationDetail {
  id: string
  messages: HistoryRow[]
  pending_refund: PendingRefund | null
}

export interface QueuedRefund {
  id: number
  session_id: string
  order_id: string
  customer: string
  item: string
  amount: number
  reason: string
  needs_supervisor: boolean
  status: 'pending' | 'claimed'
}

export type ProductSort = 'rating' | 'price_asc' | 'price_desc' | 'newest'

export interface Category {
  slug: string
  name: string
  count: number
  cover: { slug: string; name: string }
}

export interface Product {
  id: number
  slug: string
  category: string
  name: string
  price: number
  description: string
  specs: Record<string, string>
  rating: number
  rating_count: number
  added_at: string
}

export interface ProductPage {
  items: Product[]
  total: number
}

export interface ProductDetail extends Product {
  related: Product[]
}

export type CartProduct = Pick<Product, 'id' | 'slug' | 'name' | 'price' | 'category'>

export interface CartLine {
  product: CartProduct
  quantity: number
  line_total: number
}

export interface CartView {
  items: CartLine[]
  count: number
  total: number
}

export interface MergeChange {
  kind: 'combined' | 'capped' | 'unavailable'
  product_id: number
  name: string | null
  quantity?: number
}

export interface MergeResult {
  cart: CartView
  changes: MergeChange[]
}
