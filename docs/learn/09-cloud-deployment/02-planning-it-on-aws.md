---
title: Planning it on AWS
checked: 2026-11-06
---

## What you'll learn

- How the project maps onto AWS services
- What it costs, with real prices
- The steps to deploy it, and to remove it
- What's stale and has to be fixed first

## The simple explanation

Moving to the cloud is like opening a real shop after running a market stall. The goods are the same. But now there's rent, and it's charged whether customers come or not.

So plan before you build. Four questions:

1. **What maps to what?** Each local part needs a cloud home.
2. **What does it cost when idle?** That's your rent.
3. **What does it cost per customer?** That's your stock.
4. **How do I turn it off?** A forgotten test environment is the classic surprise bill.

**Reading this lesson costs nothing. The commands marked as paid create real resources.** Don't run them until you mean to, and don't skip the teardown.

## An example

Here's the rent, worked out from [AWS's public price list](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/ap-south-1/index.json) for Mumbai, in US dollars.

| Always-on part | Price | Per hour | Per day |
| --- | --- | --- | --- |
| Fargate, 0.5 vCPU | $0.04256 per vCPU-hour | $0.0213 | $0.51 |
| Fargate, 1 GB | $0.004655 per GB-hour | $0.0047 | $0.11 |
| Load balancer | $0.0239 per hour | $0.0239 | $0.57 |
| 3 public IPv4 addresses | $0.005 each per hour | $0.0150 | $0.36 |
| **Total** | | **$0.065** | **About $1.56** |

That's about $47 a month, before traffic charges. It matches the roughly $1.50 a day seen when this project ran on AWS.

The Lambda half costs almost nothing when idle:

| Pay-per-use part | Price |
| --- | --- |
| Lambda | $0.20 per million requests, plus $0.0000166667 per GB-second |
| Lambda free tier | 1 million requests and 400,000 GB-seconds a month |
| API Gateway HTTP API | $1.05 per million requests |
| DynamoDB | On demand, so nothing when idle |

Model calls are extra, and [the cost lesson](08-cost.md) puts them together. Bedrock has [its own price list](https://aws.amazon.com/bedrock/pricing/), so check that before you start.

## How ShopHelper does it

Everything lives in `ap-south-1`, is created by Terraform, and is tagged `Project=ShopHelper`.

| Job | Local | AWS |
| --- | --- | --- |
| Run the API | Docker | Lambda, and ECS Fargate |
| Model | LM Studio, Qwen | Bedrock, Claude |
| Embeddings | nomic | Titan v2 |
| Vectors | pgvector | S3 Vectors, behind a Knowledge Base |
| Orders, history, checkpoints | Postgres | DynamoDB |
| Guardrails | Regex | Bedrock Guardrails |
| Accounts and shop | Yes | **Not built** |

The same image runs both ways. Two compute options exist so they can be compared, and you can turn one off:

```hcl file=infra/variables.tf
variable "enable_ecs" {
```

**Fix these before deploying.** This project last ran on AWS on 2026-11-01, and then everything was removed:

- **No real Claude call ever ran.** The account's use-case form wasn't active, so the evals and real latency are unmeasured there.
- **The model ids are old.** `infra/variables.tf` still names Haiku 4.5 and Sonnet 4.6.
- **The AWS API has no login.** Don't host it publicly until it has one.
- **The system prompt has only been tested on Qwen.**

**The deployment steps.** Run them in Git Bash, from the repo root. You need admin AWS credentials and Terraform.

| Step | Command or action | Paid? |
| --- | --- | --- |
| 1. Copy `infra/terraform.tfvars.example`, and add your email | By hand | No |
| 2. Submit the Anthropic use-case form | Bedrock console, Model catalog | No |
| 3. Deploy | `scripts/deploy.sh`, about 10 minutes | **Yes: rent starts** |
| 4. Confirm the two emails | Alarm and budget notices | No |
| 5. Run the evals | `RUN_EVALS=1 uv run pytest evals -v` | **Yes: model calls** |
| 6. Compare the two | `scripts/compare_deployments.sh` | **Yes: model calls** |
| 7. Remove it all | `scripts/teardown.sh` | Stops the rent |

To skip the rent while testing, set `enable_ecs = false` in `infra/terraform.tfvars` before step 3. That removes the network, load balancer and Fargate, and keeps Lambda.

The teardown ends by listing everything still tagged for this project. An empty list means nothing's left. Check it. The last teardown removed 89 resources, and six ECS task definitions had to be cleared by hand, because `release.sh` had made them outside Terraform. The script now handles those.

**Only the owner of this project should decide to deploy.** Nothing in this course runs these commands for you. Moving to AWS is a later phase on the roadmap.

## In the market

Checked on 2026-11-06.

- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/) and the price list above are the sources to use. Prices vary by region, so work them out for yours.
- Public IPv4 addresses have had an hourly charge since 2024, and people often forget them. Here, they're nearly a quarter of the rent.
- A NAT gateway would have cost more than everything else here. That's why this design uses public subnets with no NAT, and limits the task's security group to the load balancer. A real product would weigh that differently.

A rough plan like this is good enough to choose a direction. Before committing real money, run a short test, and read the actual bill.

## Try it

1. Work out the table above for a different region, using the price list. Change `ap-south-1` in the link.
2. Read `scripts/deploy.sh` and `scripts/teardown.sh`, without running them. What does each do, in order?
3. Find the budget in `infra/budget.tf`. What's the limit, and when does it email?
4. Why does `deploy.sh` create the image repository first?

## Interview questions

### How would you plan moving a local AI app to AWS?

**Strong answer:** I'd map each part to a service, then work out the idle cost and the cost per request before building. For mine, Fargate, the load balancer and public addresses come to about $1.56 a day in Mumbai, and Lambda costs nothing when idle. I'd put a budget alarm in first, tag everything, and write the teardown with the deployment. Then I'd run evals there, since the model and guardrails differ.

**Follow-up:** What would you do differently for a real product?

### What usually surprises people on an AWS bill?

**Strong answer:** Things that charge by the hour while idle: load balancers, NAT gateways, public IPv4 addresses, and vector stores that keep servers running. I avoided OpenSearch Serverless and NAT for that reason. Logs and data transfer can grow too. So I set budgets, tag resources, check the first real bill, and remove test environments when I'm done.

**Follow-up:** How do you find what's costing the money?

## Check yourself

### Which is rent, charged even with no customers?

- [x] The load balancer — right: it's billed by the hour.
- [ ] Lambda — it charges per use.
- [ ] DynamoDB on demand — it charges per use.

### What should you write alongside the deployment?

- [ ] A press release — not yet.
- [x] The teardown — right: a forgotten environment keeps charging.
- [ ] A second region — that's more cost.

### Why isn't this project ready to host publicly on AWS?

- [ ] Docker doesn't run there — it does.
- [ ] Bedrock has no models — it has them.
- [x] The AWS API has no login — right: accounts are local only.
