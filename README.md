# ShopHelper AI Agent

A customer-support AI agent for a fictional electronics store, built on **AWS Bedrock** as a
learning project. It answers order questions, explains store policy from documents (RAG),
and submits refunds that **pause for human approval**. It runs behind guardrails, is deployed
**twice** (serverless and containers) entirely with **Terraform**, is gated by an **eval suite**
in CI, and is observable in CloudWatch and LangSmith.

> Learning project. Everything is in one AWS account/region (`ap-south-1`) and is removed with
> one `terraform destroy` - see [Teardown](#teardown).

## Architecture

```mermaid
flowchart LR
    client["Client (curl / UI)"]
    client -- HTTPS --> apigw["API Gateway<br/>HTTP API"]
    client -- HTTP --> alb["Application<br/>Load Balancer"]
    apigw --> lambda["Lambda<br/>(container + Web Adapter)"]
    alb --> ecs["ECS Fargate task"]

    subgraph app["ShopHelper app - same Docker image in both runtimes"]
        gin["Guardrail check<br/>(input)"] --> graph["LangGraph agent<br/>agent / tools / refund_approval"] --> gout["Guardrail check<br/>(output)"]
    end
    lambda --> app
    ecs --> app

    graph -- Converse --> claude["Bedrock<br/>Claude Haiku 4.5"]
    graph -- "MCP (stdio)" --> mcp["FastMCP server<br/>get_order_status · search_policy"]
    mcp --> orders[("DynamoDB<br/>orders")]
    mcp -- Retrieve --> kb["Bedrock<br/>Knowledge Base"]
    kb --> vectors[("S3 Vectors<br/>index")]
    docs[("S3<br/>policy docs")] -. "ingest (Titan v2 embeddings)" .-> kb
    graph --> ckpt[("DynamoDB<br/>checkpoints")]
    app --> hist[("DynamoDB<br/>history + TTL")]
    gin & gout --> guard["Bedrock<br/>Guardrail"]
    app -- JSON logs --> cw["CloudWatch<br/>metrics · dashboard · alarms"] --> sns["SNS → email"]
    app -. traces .-> ls["LangSmith"]

    gh["GitHub Actions"] -- OIDC --> role["IAM deploy role"] --> ecr["ECR"]
    ecr --> lambda & ecs
```

**One turn:** input guardrail (block prompt attacks / card numbers, mask email & phone) →
LangGraph agent loop on Claude (max-steps guard) → tools over MCP (orders in DynamoDB, policies
via Knowledge Base) → output guardrail → answer + history. A `request_refund` call goes to the
`refund_approval` node: a deterministic policy check, then `interrupt()` pauses the graph; state is
checkpointed in DynamoDB until a human calls `/approve`. Details: [docs/architecture.md](docs/architecture.md).

## AWS services used

| Service | What it does here | Idle cost |
| --- | --- | --- |
| **Bedrock - Claude Haiku 4.5** (`global.` inference profile) | Agent model | $0 (per token) |
| **Bedrock - Claude Sonnet 4.6** | LLM judge in evals | $0 (per token) |
| **Bedrock Knowledge Base** + Titan Text Embeddings v2 | RAG over policy docs | $0 |
| **S3 Vectors** | Vector index for the Knowledge Base | ~$0 |
| **S3** | Policy documents (KB data source) | ~$0 |
| **Bedrock Guardrails** | Prompt-attack + PII filter, input & output | $0 (per text unit) |
| **DynamoDB** (on-demand) | Orders, chat history (TTL), LangGraph checkpoints (TTL) | $0 |
| **Lambda** + **API Gateway HTTP API** | Deployment 1 (serverless) | $0 |
| **ECS Fargate** + **ALB** + VPC | Deployment 2 (containers) | **~$1.5/day** ⚠️ |
| **ECR** | Container images | ~$0.03/month |
| **CloudWatch** Logs, metric filters, dashboard, alarms + **SNS** | Observability | ~$0.10/day |
| **SSM Parameter Store** | LangSmith API key (SecureString) | $0 |
| **IAM** OIDC provider + roles | Keyless GitHub Actions deploys | $0 |
| **AWS Budgets** | $10/month alert | $0 |

Per-service notes and configuration: [docs/aws-services.md](docs/aws-services.md).

## Repository layout

```text
src/shophelper/   raw_agent.py (step 1) · api.py · graph.py · service.py · tools.py
                  mcp_server.py / mcp_client.py · guardrails.py · memory.py · orders.py
                  observability.py · config.py · data/orders.json
knowledge/policies/   9 markdown policy documents (the RAG corpus)
infra/            Terraform for everything (one file per concern)
evals/            20 golden cases (5 attacks) + LLM faithfulness judge
tests/            offline unit tests (scripted fake LLM, no AWS)
scripts/          deploy.sh · release.sh · compare_deployments.sh · teardown.sh ...
.github/workflows/ci.yml   lint/tests → evals → deploy (OIDC)
```

## Quick start

Prerequisites: AWS CLI (admin credentials), Terraform ≥ 1.9, Docker, [uv](https://docs.astral.sh/uv/), Git Bash on Windows.

1. **One-time Bedrock setup:** in the Bedrock console open any Anthropic model in the *Model
   catalog* and submit the Anthropic **use-case form** (required once per account; ~15 min to activate).
2. **Run locally with no AWS resources at all** (in-memory orders/history, keyword policy search):

   ```bash
   uv sync
   uv run pytest                                  # 19 offline tests
   uv run python -m shophelper.raw_agent "Where is order 1002?"   # step 1: raw loop
   uv run uvicorn shophelper.api:app --reload     # http://localhost:8000/docs
   ```
3. **Deploy everything:**

   ```bash
   cp infra/terraform.tfvars.example infra/terraform.tfvars   # set alert_email
   scripts/deploy.sh                 # Terraform + image + Lambda/ECS rollout, writes .env
   scripts/set_langsmith_key.sh      # optional: LANGSMITH_API_KEY from .env -> SSM
   scripts/set_github_vars.sh        # CI variables (evals + deploy on push to main)
   RUN_EVALS=1 uv run pytest evals -v
   ```
4. **Try it** (use either `api_gateway_url` or `alb_url` from `terraform -chdir=infra output`):

   ```bash
   URL=https://<id>.execute-api.ap-south-1.amazonaws.com
   curl -s $URL/chat -H 'content-type: application/json' \
     -d '{"session_id":"demo-0001","message":"Refund order 1006, it arrived scratched"}'
   # -> "status": "pending_approval" ... a human approves:
   curl -s $URL/approve -H 'content-type: application/json' \
     -d '{"session_id":"demo-0001","approved":true,"reviewer":"alice"}'
   ```

   More: [docs/runbook.md](docs/runbook.md).

## Decisions and trade-offs

| Decision | Why | Trade-off |
| --- | --- | --- |
| **Terraform for all infra** (not SAM/CDK) | One tool, one state, one `destroy` | More verbose than SAM for Lambda |
| **LangGraph** for the agent | Explicit graph, `interrupt()` for human-in-the-loop, pluggable checkpointers | More concepts than a raw loop (kept in `raw_agent.py` for comparison) |
| **DynamoDB checkpointer** (not Postgres) | Serverless, $0 idle, TTL cleanup | Needs a specific PK/SK schema; 400 KB item limit (S3 offload available) |
| **S3 Vectors** (not OpenSearch Serverless) | Pay-per-use; OpenSearch Serverless costs ≥ ~$12/day idle | Fewer query features, higher query latency than OpenSearch |
| **Guardrail via ApplyGuardrail** around the loop | Runs once per turn on user text and final answer, framework-agnostic | Doesn't inspect intermediate tool outputs; streaming tokens reach the user before the output check |
| **Refund = policy check + human approval** | LLM can *request*, never *execute* money movement; ineligible requests never reach a human | Adds latency for the customer (async approval) |
| **Tools behind MCP** | Same tools reusable by any MCP client (Claude Desktop, other agents) | stdio subprocess adds ~3 s cold start → **Lambda uses in-process tools, ECS uses MCP** |
| **One image, two runtimes** (Lambda Web Adapter) | Identical code path; fair comparison | Container Lambdas cold-start slower than zip |
| **Haiku 4.5 agent, Sonnet 4.6 judge** | Cheap/fast agent; a different, stronger judge reduces self-grading bias | Claude 5.x isn't enabled on this account yet; switch with `AGENT_MODEL_ID` |
| **CI deploys code, not infra** | Small OIDC role (ECR push, Lambda/ECS update); infra changes stay a reviewed `terraform apply` | Infra drift must be applied manually |
| **Local Terraform state** | Simplest for a single-person learning project | For a team: S3 backend with `use_lockfile` |
| **No auth on the API** | Learning scope | Anyone with the URL can chat; API Gateway throttling (5 rps) limits abuse. Add Cognito/JWT for real use |

### Lambda vs ECS (measured, see [docs/deployment-comparison.md](docs/deployment-comparison.md))

| | Lambda + API Gateway | ECS Fargate + ALB |
| --- | --- | --- |
| Cold start | ~4 s first request (was 20.7 s before moving MCP out of Lambda + async init) | none (always warm) |
| Warm `/health` | ~0.24 s | ~0.24 s |
| Streaming (`/chat/stream`) | buffered by API Gateway → arrives all at once | true SSE token streaming |
| Idle cost | $0 | ~$1.5/day (Fargate + ALB + public IPv4) |
| Max request time | 30 s (HTTP API limit) | ALB idle timeout (set to 120 s) |

## Teardown

```bash
scripts/teardown.sh     # terraform destroy + SSM key + CI variables off
```

Removes every resource including the budget, the GitHub OIDC role, the ECR images and the vector
index. Check *Billing → Bills* the next day; anything left will be tagged `Project=ShopHelper`.

## The 12 steps (one commit each)

1 raw Converse loop · 2 FastAPI + validation + max-steps · 3 DynamoDB memory with TTL ·
4 RAG (S3 → KB → S3 Vectors) · 5 Guardrail before/after · 6 LangGraph + human-approval refund +
DynamoDB checkpointer · 7 tools via FastMCP · 8 evals (20 cases, 5 attacks, LLM judge) ·
9 deploy twice (Lambda/API GW, ECS/ALB) · 10 CloudWatch + LangSmith · 11 GitHub Actions + OIDC ·
12 this README. `git log --oneline` shows them in order.
