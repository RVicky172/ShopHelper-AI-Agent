---
title: Other clouds and hosting your own model
checked: 2026-11-06
---

## What you'll learn

- How AWS's AI services map to other clouds
- How to reduce lock-in
- When hosting your own model makes sense
- How to work out the break-even

## The simple explanation

So far, this project has used AWS and a laptop. There are other choices, and interviewers often ask how your design would move.

Most clouds offer the same building blocks under different names. Think of supermarkets: the layout differs, and you can still find milk.

Then there's a bigger question: **rent a model, or run your own?**

| | API from a provider | Your own model |
| --- | --- | --- |
| **Picture** | A taxi | Owning a car |
| **Pay** | Per token | Per GPU hour, used or not |
| **Quality** | Best available | Good open models, usually behind the best |
| **Data** | Sent to the provider | Stays with you |
| **Work** | Almost none | Serving, scaling, patching, monitoring |

Owning a car only saves money if you drive a lot. A GPU only saves money if it's busy.

## An example

Let's work out the break-even. A cloud GPU is often quoted at around $3 an hour, though [prices vary a lot](https://www.gmicloud.ai/en/blog/h100-cost-per-token-vs-api-break-even), and the quotes we found ran from about $1.50 to $7. They mostly came from vendors, so treat this as a sketch.

```text
One GPU, always on: $3 × 24 × 30 = $2,160 a month
```

From [the cost lesson](08-cost.md), a turn costs $0.0045 on Sonnet 5.5, and $0.000225 on Haiku 5.5.

| Compared with | Break-even turns a month | A day |
| --- | --- | --- |
| Sonnet 5.5 | 480,000 | 16,000 |
| Haiku 5.5 | 9,600,000 | 320,000 |

And one GPU has to handle that. Our local test topped out at 44 turns a minute, which is about 1.9 million a month with the GPU running flat out, day and night. Real traffic has peaks and quiet hours, so you'd need spare capacity. That was a consumer card, so a data centre GPU would do better, but the picture holds.

Then add the work. One engineer's time costs more than that GPU. So for most teams, **cost alone doesn't justify self-hosting unless traffic is very high.** Better reasons are privacy rules, control over the model, or needing a fine-tuned small model.

## How ShopHelper does it

This project already runs its own model, in a small way. LM Studio serves Qwen on a local GPU, and it speaks the OpenAI API:

```yaml
LLM_PROVIDER: openai_compatible
```

That's the lock-in lesson in one line. Because the model sits behind a small interface, moving between Claude on Bedrock and a local Qwen is a setting. The agent code doesn't change. The model provider is the piece that's easiest to swap here.

What was learned running a 30B model on a 16 GB card:

- The 18.6 GB model doesn't fit in VRAM, so part runs on the CPU, and it's slower.
- It needed more prompt rules and more code checks than expected.
- It's free per call, which makes evals cheap to run. That's a real advantage in development.
- The first answer waits for the model to load.

**How portable is the rest?**

| Part | Portable? | Would need changing |
| --- | --- | --- |
| Agent, tools, FastAPI | Yes | Nothing |
| Docker image | Yes | Nothing |
| Postgres version | Yes | Runs anywhere |
| Claude on Bedrock | Mostly | A provider setting |
| Knowledge Base, S3 Vectors | No | Back to pgvector, which already works |
| Bedrock Guardrails | No | Another filter |
| DynamoDB | No | Back to Postgres |
| Terraform | No | Rewrite for the new provider |

So the app is portable, and the wiring isn't. The one-contract pattern from [running locally](01-running-locally.md) is the reason. And the local stack proves it: it's already a second home.

## In the market

Checked on 2026-11-06. Names in this area change often, and the mapping below comes partly from third-party comparisons.

| Need | AWS | Azure | Google Cloud |
| --- | --- | --- | --- |
| Hosted models | Bedrock | [Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/) | Vertex AI |
| Agent runtime | AgentCore | Foundry Agent Service | [Agent Engine](https://docs.cloud.google.com/agent-builder/agent-engine/overview) |
| Containers | ECS Fargate | Container Apps | Cloud Run |
| Functions | Lambda | Functions | Cloud Run functions |
| Serverless GPU | None on Fargate | [Container Apps GPUs](https://learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview) | [Cloud Run GPUs](https://cloud.google.com/run/docs/configuring/services/gpu) |

Claude is available on all three, as well as directly from Anthropic.

**Choosing a cloud.** It's usually decided by where the company already is: its data, its contracts, and what its team knows. Model availability and region come next.

**Serving your own model:**

| Tool | Good for |
| --- | --- |
| [vLLM](https://docs.vllm.ai/en/latest/) | High-throughput serving, with an OpenAI-compatible API |
| [Ollama](https://ollama.com/) | Simple local use |
| LM Studio | A desktop app, used here |
| Bedrock, Together, Fireworks and others | Hosted open models, with no GPUs to run |

The last row is a middle path: open models, paid per token, with someone else running them.

**Data residency.** Some rules say data must stay in a country. This project's `global.` model profile can route to any region, which would be wrong for such a rule. Check what your model option does.

## Try it

1. Work out the break-even for a $1.50 and a $7 GPU.
2. Take the portability table, and pick the part you'd move first, if asked to go to Google Cloud.
3. Read `src/shophelper/core/config.py`. How many settings does it take to change the model?
4. If you have LM Studio, load a smaller model, set `LOCAL_CHAT_MODEL` in `.env`, and restart. Compare speed and answers.

## Interview questions

### Should we host our own model?

**Strong answer:** Usually not for cost. A GPU at about $3 an hour is roughly $2,160 a month, so against a cheap hosted model the break-even is millions of turns, and that's before engineering time. I'd self-host for privacy rules, control, or a small fine-tuned model doing one job well. There's a middle path too: hosted open models. I run Qwen locally, and it's great for free evals, though it needed extra prompt rules and code checks.

**Follow-up:** What would you need to run it in production?

### How would you avoid cloud lock-in?

**Strong answer:** I'd put interfaces around the things that differ, and keep the core portable: containers, Postgres, and a model interface. In my project the agent doesn't know if it's on AWS or local, because a setting picks the backend. I accept some lock-in where it saves real work, like managed guardrails, as long as there's a known way out. Trying to avoid it entirely costs more than it saves.

**Follow-up:** Which part of yours would be hardest to move?

### How would you move this project to Google Cloud?

**Strong answer:** The app moves easily: Cloud Run takes the same image, and it handles streaming. I'd use the Postgres path, with Cloud SQL and pgvector, which replaces DynamoDB and the Knowledge Base, and already works locally. The model goes to Vertex AI through a provider setting. I'd need another guardrail, Terraform rewritten, and OIDC set up for Google. Then I'd run the evals again, since those pieces differ.

**Follow-up:** What would you test first?

## Check yourself

### When does self-hosting usually pay off on cost?

- [ ] At any size — fixed costs say otherwise.
- [x] At high, steady use — right: a GPU only saves money when it's busy.
- [ ] When traffic is low — then it sits idle.

### Why can this project swap models with a setting?

- [x] The model sits behind a small interface — right: the agent code doesn't change.
- [ ] All models are the same — they differ a lot.
- [ ] Docker handles it — it's about the code design.

### Which part of ShopHelper is least portable?

- [ ] The FastAPI app — it runs anywhere.
- [ ] The Docker image — that's portable.
- [x] The AWS-specific services and Terraform — right: the wiring is what's tied to AWS.
