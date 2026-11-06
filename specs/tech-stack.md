# ShopHelper — Tech Stack

> Approved technologies. Adding or replacing anything here requires updating this file and logging the
> decision in `memory/decisions.md` (Constitution III).

**Last updated:** 2026-11-06

---

## Runtime

Local and AWS use the same code. Settings choose the backend.

| Concern | Choice | Why |
| ------- | ------ | --- |
| Backend | Python 3.13, FastAPI, Pydantic | Async, typed, generates API docs |
| Agent | LangGraph | `interrupt()` for human approval, pluggable checkpointers |
| Tools | MCP, with FastMCP and langchain-mcp-adapters | Tools any client can reuse |
| Chat model (local) | LM Studio: `qwen/qwen3-30b-a3b-2507`, through langchain-openai | Free, on the user's GPU, OpenAI-compatible |
| Embeddings (local) | LM Studio: `text-embedding-nomic-embed-text-v1.5`, 768 dimensions | Already installed, small and fast |
| Data (local) | Postgres 17 + pgvector, with psycopg | One inspectable store for everything |
| Models (AWS) | Bedrock: Claude Haiku 4.5 agent, Sonnet 4.6 judge, Titan v2 embeddings | Managed, pay per token |
| Data (AWS) | DynamoDB, Bedrock Knowledge Base on S3 Vectors | $0 idle |
| Guardrails | Bedrock Guardrails on AWS, regex rules locally | Regex shows the flow; it isn't real protection |
| Frontend | React 19, TypeScript (strict), Vite | Standard, fast hot reload, built-in proxy |
| Streaming | SSE, with `fetch` and eventsource-parser | Traffic is one-way, and `EventSource` can't POST |
| Accounts | argon2-cffi (password hashing), PyJWT (internal tokens) | Hashing must not be hand-written; PyJWT already came with `mcp` |
| Routing and type | React Router, Schibsted Grotesk (self-hosted through Fontsource) | Real URLs; no runtime call to a font service |
| UI data and styling | TanStack Query, Tailwind CSS 4, react-markdown | Caching, co-located styles, safe Markdown |

## Tooling (dev only)

Dev-only tools. The commands are in `testing-strategy.md`.

| Concern | Choice |
| ------- | ------ |
| Python packages | uv, with `uv.lock`. Run `uv export --no-dev --no-emit-project -o requirements.txt` after any change, because the Dockerfile installs that file |
| Frontend packages | npm, Node 22 in Docker |
| Backend tests and lint | pytest, pytest-asyncio, ruff |
| Frontend tests | Vitest |
| Frontend lint and format | Biome. ESLint's TypeScript parser doesn't support TypeScript 7 (D-024) |
| Python type checks | Pyright |
| Commit hooks | pre-commit |
| Local runtime | Docker Compose, pgAdmin |
| Infrastructure | Terraform |
| CI | GitHub Actions with OIDC |

## Explicitly Not Used (and why)

See `memory/decisions.md` for the full reasoning.

| Rejected | Reason |
| -------- | ------ |
| Ollama | LM Studio already held the user's model and an embedding model |
| WebSockets | The stream only flows one way |
| Vercel AI SDK | Expects its own stream format, and hides what this project exists to teach |
| Dedicated vector database | pgvector is enough, and can be browsed with SQL |
| OpenSearch Serverless | About $12 a day idle |
| SAM or CDK | One tool for all infrastructure: Terraform |
