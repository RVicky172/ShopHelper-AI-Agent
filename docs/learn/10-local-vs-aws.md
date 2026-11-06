# 10. Local vs AWS

## The goal

Local development should run the same code as production, without copying it or littering it with
`if local:`. This project gets there with one pattern, used throughout.

## The pattern: one contract, many backends

Each external dependency has an interface, and one implementation per backend. For orders, in
[orders.py](../../src/shophelper/shop/orders.py):

```python
class OrderRepo(Protocol):                  # the contract
    def get(self, order_id: str) -> dict | None: ...
    def mark_refunded(self, order_id, amount, reason) -> None: ...

class InMemoryOrderRepo: ...                # tests
class DynamoOrderRepo: ...                  # AWS
class PostgresOrderRepo: ...                # local
```

One function chooses, based on settings:

```python
def get_order_repo() -> OrderRepo:
    if settings.database_url:
        return PostgresOrderRepo()
    if settings.orders_table:
        return DynamoOrderRepo(...)
    return InMemoryOrderRepo()
```

The rest of the code only knows `OrderRepo`, so `graph.py` works unchanged in every environment.
This is **dependency inversion**, and it's what makes offline tests possible at all.

## What each setting switches

All of them are in [config.py](../../src/shophelper/core/config.py).

| Setting | Default (AWS) | In Docker | Switches |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | `bedrock` | `openai_compatible` | Claude → LM Studio |
| `DATABASE_URL` | unset | Postgres URL | DynamoDB and Knowledge Base → Postgres, and turns accounts on |
| `INTERNAL_TOKEN_SECRET` | unset | A local-only value | Signs identity for the MCP server |
| `SEED_DEMO_USERS` | `false` | `true` | Creates the demo accounts |
| `TOOLS_TRANSPORT` | `local` | `mcp` | In-process tools → MCP |
| `MCP_URL` | unset | `http://mcp:8765/mcp` | stdio → HTTP |
| `LOCAL_GUARDRAILS` | `false` | `true` | No rules → regex rules |

The local values are set in [docker-compose.yml](../../docker-compose.yml). AWS sets its own in
Terraform, and those didn't change.

Why LM Studio works so easily: it speaks the OpenAI API, which has become a common standard. Any
OpenAI-compatible server (vLLM, Ollama, a hosted provider) works by changing `LLM_BASE_URL`.

## Keeping AWS safe

The local stack was added without changing the deployed behaviour:

| Protection | How |
| --- | --- |
| AWS stays the default | Every new setting defaults to the old behaviour. A test pins this |
| `infra/` untouched | No Terraform file changed |
| Same image | Compose builds the Dockerfile that ships to Lambda and ECS |
| Local packages stay unloaded | `psycopg` is imported inside functions, so AWS never loads it |
| Local routes are hidden | `/orders`, `/auth/*` and friends return 404 unless accounts are on, so a public API can't leak order data |
| Accounts are off on AWS | With no database, the login gate passes everything through, as before |
| Demo accounts stay local | Their password is public, so seeding refuses to run unless `SEED_DEMO_USERS` is set |

Things that *did* change for AWS, and should be retested on your next deployment:

- **The system prompt** gained rules while tuning for Qwen. They're general, but Claude hasn't been
  evaluated with them.
- **`/chat/stream`** now sends step events before the first token. Clients that read only `token`
  and `final` are unaffected. `scripts/compare_deployments.sh` was updated to time the first token.
- **The image** is larger, because it contains the extra Python packages.

## What local can't show you

Passing locally doesn't prove AWS works. These only exist there:

| Only on AWS | Why it matters |
| --- | --- |
| IAM permissions | The most common cause of "works locally, fails deployed" |
| Lambda cold starts and the 30 s limit | Local has neither |
| API Gateway buffering SSE | Streaming behaves differently |
| DynamoDB's 400 KB item limit | Large checkpoints could fail |
| Real Bedrock Guardrail behaviour | Much stronger than regex |
| Accounts | Local only. **The AWS API has no login**, so don't host it publicly until it does |
| Claude's behaviour | Different model, different failures |

## The shop is local only

Accounts exist only on the local stack, and the shop depends on them, so it doesn't exist on AWS at all. Every shop route uses
`accounts_only`, which returns 404 with accounts off. That keeps the rule from the start of this chapter: a new feature changes
nothing on AWS unless a setting says so.

Two things *are* shared, and it's worth being honest about them. The system prompt and the policy documents reach AWS on the next
deploy, because the agent there uses the same code and the Knowledge Base uses the same files. They've only been tested on
Qwen so far.

## When you're ready for AWS

See [next-steps.md](../next-steps.md). In short: submit the Anthropic use-case form, deploy, run the
evals on real Bedrock, and tear down.

## Try it

1. Read [docker-compose.yml](../../docker-compose.yml) and find each setting from the table above.
2. Read `test_defaults_are_the_aws_path` in
   [test_local_stack.py](../../tests/test_local_stack.py). Think about what it would catch.
3. Point at a different model by setting `LOCAL_CHAT_MODEL` in `.env`, then run
   `docker compose up -d`. Run the evals and compare.
4. Pick another dependency, such as chat history in
   [memory.py](../../src/shophelper/agent/memory.py), and find its three implementations.
5. Run `uv run pytest tests/test_shop.py -k accounts_off`. Each test turns accounts off and checks that a shop route
   returns 404. That's the AWS behaviour, proved without AWS.

Next: [Accounts and isolation](11-accounts-and-isolation.md)
