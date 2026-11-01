# AWS services and configuration

Everything lives in `ap-south-1` (Mumbai), is created by Terraform in [`infra/`](../infra), and
is tagged `Project=ShopHelper`. Prices are approximate list prices - check the AWS pricing pages.

## What you have to do by hand (once)

| What | Where | Why |
| --- | --- | --- |
| Admin AWS credentials for the CLI | `aws configure` | Terraform and the scripts use them |
| **Anthropic use-case form** | Bedrock console → Model catalog → any Claude model | Required once per account before any Claude call ("Model use case details have not been submitted") |
| Confirm the SNS email | Inbox: "AWS Notification - Subscription Confirmation" | Alarm emails are only delivered after you click it |
| LangSmith key (optional) | smith.langchain.com → Settings → API keys → paste into `.env` → `scripts/set_langsmith_key.sh` | Tracing |

No AWS access keys are ever stored in GitHub: CI uses OIDC.

## Bedrock

| Resource | Terraform | Notes |
| --- | --- | --- |
| Agent model | - (serverless) | `global.anthropic.claude-haiku-4-5-20251001-v1:0` - a *global cross-region inference profile*: Bedrock routes to any region with capacity. IAM therefore allows the profile ARN **and** the region-less foundation-model ARN. ~$1 / $5 per M input/output tokens. |
| Judge model | - | `global.anthropic.claude-sonnet-4-6`, evals only. |
| Embeddings | - | `amazon.titan-embed-text-v2:0`, 1024 dims, used by the KB at ingestion and query time. |
| Knowledge Base | `knowledge_base.tf` | Vector KB, fixed-size chunking (300 tokens, 20 % overlap), S3 data source `policies/`. A `terraform_data` resource starts an ingestion job whenever a policy file's hash changes. |
| Guardrail | `guardrail.tf` | `PROMPT_ATTACK` (HIGH, input only), HATE/INSULTS/SEXUAL/VIOLENCE/MISCONDUCT (MEDIUM), **BLOCK** card number, CVV, password, SSN, AWS keys, Aadhaar (regex); **ANONYMIZE** email and phone. A numbered version is published and pinned by the app (`GUARDRAIL_VERSION`). |

## Storage

| Resource | Notes |
| --- | --- |
| S3 bucket `shophelper-kb-docs-<account>` | Policy markdown, public access blocked, `force_destroy` for teardown |
| S3 Vectors bucket + index `policies` | float32, 1024 dims, cosine. `AMAZON_BEDROCK_TEXT` and `AMAZON_BEDROCK_METADATA` are declared non-filterable - Bedrock stores the chunk text there and it exceeds the filterable-metadata size limit otherwise |
| DynamoDB `shophelper-orders` | 7 seeded fake orders (from `src/shophelper/data/orders.json`, dates relative to apply time) |
| DynamoDB `shophelper-history` | `session_id` + `ts`, TTL `expires_at` |
| DynamoDB `shophelper-checkpoints` | `PK` + `SK`, TTL `ttl` - schema required by `langgraph-checkpoint-aws` |

All tables are on-demand: $0 when idle.

## Compute

| Resource | Notes |
| --- | --- |
| ECR `shophelper` | Immutable tags (git SHA), scan on push, keep last 10, `force_delete` |
| Lambda `shophelper` | Container image, 2048 MB, 30 s timeout. The **AWS Lambda Web Adapter** extension in the image turns Lambda invokes into HTTP calls to uvicorn, so the FastAPI app is unchanged. `TOOLS_TRANSPORT=local` and `AWS_LWA_ASYNC_INIT=true` keep cold starts ~4 s |
| API Gateway HTTP API | `$default` route → Lambda proxy (payload v2), throttled to 5 rps / burst 10 |
| VPC | 2 public subnets, IGW, **no NAT gateway**. Task SG only accepts the ALB SG on 8080 |
| ECS Fargate | 0.5 vCPU / 1 GB, 1 task, public IP (for ECR/Bedrock without NAT), circuit-breaker rollback, `TOOLS_TRANSPORT=mcp` |
| ALB | HTTP :80 → target group :8080, health check `/health`, idle timeout 120 s for streaming |

`enable_ecs = false` in `terraform.tfvars` removes the VPC/ALB/ECS part (~$1.5/day) and keeps Lambda.

## IAM

| Role | Permissions |
| --- | --- |
| `shophelper-lambda`, `shophelper-ecs-task` | Shared policy `shophelper-app`: invoke the two Claude models, `ApplyGuardrail` on the guardrail, `Retrieve` on the KB, item-level DynamoDB actions on the 3 tables, read the LangSmith SSM parameter |
| `shophelper-ecs-execution` | AWS managed `AmazonECSTaskExecutionRolePolicy` (pull image, write logs) |
| `shophelper-kb-role` | Assumed by Bedrock: embed with Titan, read the docs bucket, write/query the vector index |
| `shophelper-github-deploy` | Trusts GitHub OIDC for `repo:RVicky172/ShopHelper-AI-Agent:ref:refs/heads/main` only. ECR push, Lambda `UpdateFunctionCode`, ECS register/update, `PassRole` for the two task roles, plus `shophelper-app` for evals |

## Observability

| Resource | Notes |
| --- | --- |
| Log groups `/aws/lambda/shophelper`, `/ecs/shophelper` | 7-day retention |
| 14 metric filters | `Requests`, `InputTokens`, `OutputTokens`, `LatencyMs`, `GuardrailBlocks`, `RefundsPending`, `Errors` in namespace `ShopHelper`, dimension `Runtime` = lambda / ecs - parsed from the app's JSON turn log |
| Dashboard `shophelper` | Tokens, requests, latency p50/p90, errors & blocks, estimated LLM cost, Lambda duration, cold starts (Logs Insights on `REPORT` lines) |
| Alarms → SNS email | App errors (per runtime), Lambda function errors, ALB target 5xx |
| SSM `/shophelper/langsmith-api-key` | SecureString created by `scripts/set_langsmith_key.sh` - deliberately *not* in Terraform so the key never lands in state |
| Budget `shophelper-learning-budget` | $10/month, email at 50 % actual and 100 % forecast |
