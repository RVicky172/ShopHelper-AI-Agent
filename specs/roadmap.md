# ShopHelper — Roadmap

> Phased plan. Each phase is a set of feature specs. Update statuses as work moves.
> Status legend: ⬜ Not started · 📝 Spec drafted · ✅ Spec approved · 🚧 In progress · ✔️ Done

**Last updated:** 2026-11-06

---

## Phase 0 — Foundation

_Goal:_ the agent runs end to end locally, its AWS code is intact, and the spec workflow is in place.

| #   | Feature                                                                                                       | Spec | Status |
| --- | ------------------------------------------------------------------------------------------------------------- | ---- | ------ |
| 000 | Baseline: the agent, local stack, React UI, AWS infrastructure and docs that already exist | [spec](features/000-baseline/spec.md) | ✔️     |

**Exit criteria:** every gate in the Definition of Done passes after `docker compose down -v` and a rebuild. Met on 2026-11-04.

## Phase 1 — Move to AWS

_Goal:_ the project runs on AWS with Claude, proven by the same evals, and then torn down. Details:
[docs/next-steps.md](../docs/next-steps.md). Blocked until the Anthropic use-case form is accepted.

| #   | Feature                                                               | Spec | Status |
| --- | --------------------------------------------------------------------- | ---- | ------ |
| 010 | Claude on Bedrock: redeploy and pass the 20 evals with the new prompt | —    | ⬜     |
| 011 | Measure Lambda and ECS: chat latency, first token, cold start         | —    | ⬜     |
| 012 | Turn on CI deploys and confirm the pipeline goes green                | —    | ⬜     |

**Exit criteria:** evals pass on Bedrock with Sonnet as judge, the comparison docs hold real numbers, and
`scripts/teardown.sh` leaves nothing tagged `Project=ShopHelper`.

## Phase 2 — Users and understanding

_Goal:_ each user's data is private, access has levels, and the app explains more of what it does.

| #   | Feature                                                                 | Spec | Status |
| --- | ----------------------------------------------------------------------- | ---- | ------ |
| 020 | User accounts, access levels and per-user data isolation                | [spec](features/020-user-accounts/spec.md) | ✔️     |
| 021 | Storefront: products, categories, cart, chat button                     | [spec](features/021-storefront/spec.md) | ✔️     |
| 022 | Learning views: see more of what the system does (scope to be agreed)   | —    | ⬜     |

**Exit criteria:** cross-user evals pass, and a customer can't reach another user's data by any route.

## Backlog (unscheduled ideas)

- Care questions: a code check so the agent always searches the policy. Only 12 of 24 did (D-016). Add the failing wordings as evals.
- Hybrid search: combine keyword and vector search in RAG.
- Product search in the shop.
- A read-only MCP tool so the agent can answer questions about the catalogue.
- Postgres row-level security, as a second layer of isolation behind the owner filters.
- Accounts on AWS with Cognito, needed before the API is hosted publicly.
- A way for staff to clear a refund stuck in `claimed` after a failed resume.
- Defence against indirect prompt injection in tool results.
- A committed browser test for the UI (Playwright), and a CI job for `web/`.
- Host the React UI on AWS, which also needs auth on the API.
- Generate TypeScript API types from FastAPI's OpenAPI schema.
