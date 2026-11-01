# Lambda + API Gateway vs ECS Fargate + ALB

Same Docker image, same code, same AWS resources behind it. Measured from India against
`ap-south-1` with `curl` (`scripts/compare_deployments.sh`).

## Measured

| Measurement | Lambda + API Gateway | ECS Fargate + ALB |
| --- | --- | --- |
| First request after deploy, v1 (MCP subprocess at startup) | **20.7 s** - init hit Lambda's 10 s init limit (`Init Duration: 9999.57 ms`) and was re-run inside the invoke | n/a (task warm before it takes traffic) |
| First request after deploy, v2 (in-process tools + `AWS_LWA_ASYNC_INIT`) | **4.2 s** | n/a |
| Warm `/health` | 0.24 s | 0.24 s |
| Guardrail-blocked `/chat` (no model call) | ~0.5 s | ~0.5 s |
| Memory used | ~260 MB of 2048 MB | - |

**Lesson from v1:** the app import took ~6.8 s on a cold Lambda (vs 1.4 s on a warm laptop
container - Lambda lazily loads image layers on first read), and spawning the MCP stdio server
re-imported most of it (+3 s). Pushing past 10 s meant Lambda killed the init and started again.
Fixes: Lambda calls tools in-process (ECS keeps MCP, it pays the cost once per task), and
`AWS_LWA_ASYNC_INIT` finishes a long init during the first invoke instead of restarting it.

Full `/chat` latency (model + tools) and streaming time-to-first-token still have to be
recorded: the account's Anthropic use-case form was not yet active when this was written.
Run `scripts/compare_deployments.sh` and paste the numbers here.

## Qualitative comparison

| | Lambda + API Gateway | ECS Fargate + ALB |
| --- | --- | --- |
| Cold starts | Yes, per new execution environment (~4 s) | No; scale-out takes ~1-2 min per task |
| Streaming | API Gateway HTTP API buffers the response - SSE arrives all at once. (Lambda function URLs with `RESPONSE_STREAM` can stream) | Native: tokens arrive as generated |
| Max request duration | 30 s (HTTP API integration limit) | Bounded by ALB idle timeout (120 s here) |
| Concurrency model | One request per execution environment | Many concurrent requests per task (async FastAPI) |
| MCP stdio subprocess | Expensive (per environment cold start) | Cheap (once per task) |
| Idle cost | $0 | ~$1.5/day (0.5 vCPU/1 GB Fargate, ALB hours, 3 public IPv4 addresses) |
| Cost at load | Per request + GB-s; cheaper at low/spiky traffic | Flat per task-hour; cheaper at steady high traffic |
| Ops | Nothing to patch or size beyond memory | Task size, desired count, autoscaling, VPC |

**When to pick which:** spiky or low traffic, short turns, no streaming requirement → Lambda.
Streaming UX, long multi-tool turns, steady traffic, or long-lived connections (MCP, websockets) → ECS.
