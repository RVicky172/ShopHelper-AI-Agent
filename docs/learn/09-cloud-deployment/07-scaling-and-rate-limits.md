---
title: Scaling and rate limits
checked: 2026-11-06
---

## What you'll learn

- Where an AI app really hits its limits
- What happened when we loaded the local stack
- How to handle a model provider's limits
- Why you need your own rate limits

## The simple explanation

Scaling a normal web app usually means adding servers. An AI app is different, because the slow part isn't yours. It's the model.

Think of a coffee shop with one espresso machine. Hiring more cashiers doesn't help. The queue is at the machine. So find the real bottleneck first, because scaling anything else wastes money.

For an agent, the usual bottlenecks are:

| Bottleneck | Limit | Fix |
| --- | --- | --- |
| **Model quota** | Requests and tokens per minute | Ask for more, spread load, use a smaller model |
| **Model speed** | Tokens per second | Shorter prompts and answers, streaming |
| **Open connections** | Every stream holds one open | Async servers, more tasks |
| **Database** | Connections | A pool |
| **Your wallet** | Your budget | Rate limits, alarms |

**Rate limits** work in both directions. Providers limit you. And you should limit your users, because each message costs real money.

## An example

We loaded the local stack with several turns at once, using real questions:

| Turns at once | Time for all | Median turn | Turns per minute |
| --- | --- | --- | --- |
| 1 | 3.0 s | 3.0 s | 20 |
| 2 | 3.9 s | 3.7 s | 31 |
| 4 | 5.5 s | 4.0 s | 43 |
| 8 | 11.0 s | 9.0 s | 44 |

Read the last column. Throughput rises, then stops at about 44 turns a minute. Past that point, more parallel turns don't add throughput, they only wait longer: the median went from 4 to 9 seconds.

That's a bottleneck, seen in numbers. Here it's one GPU running LM Studio. The API and database weren't the limit, so more containers wouldn't help at all.

It's one small test on one machine, with no streaming. But the method carries over: **raise the load until throughput stops rising, then find what's full.**

## How ShopHelper does it

**The API Gateway limit** is the one real rate limit here. It's for the whole API, not per user:

```hcl file=infra/lambda.tf
throttling_burst_limit = 10
throttling_rate_limit  = 5
```

That's 5 requests a second, with bursts of 10, a cheap cap for a public endpoint.

**ECS is fixed at one task.** There's no autoscaling:

```hcl file=infra/ecs.tf
desired_count   = 1
```

**Per-turn limits** stop any one turn running away: 6 model steps at most, and 2,000 characters per message.

```python file=src/shophelper/core/config.py
max_steps: int = 6
```

**What isn't built:** per-user rate limits, a queue, autoscaling, or retry logic of our own for model throttling. The local login lockout protects passwords, and it doesn't limit chat. So one signed-in person could send messages as fast as they like, which matters most if a paid model is behind it.

**The maths for planning.** Say each turn uses 1,750 input tokens, and you expect a peak of 100 turns a minute. That's 175,000 input tokens a minute. Compare that with your model quota before launch, not after. Then multiply by the number of model calls per turn, because an agent may make several.

## In the market

Checked on 2026-11-06.

**Handling provider limits.** When a provider returns a 429, slow down:

- **Retry with exponential backoff and jitter**, so clients don't all retry together. Most SDKs do this for you.
- **Respect `retry-after`** when it's given.
- **Queue** work that can wait.
- **Fall back** to another model or region when you can.
- **Check [Bedrock's quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html)** for your model and region, and ask for increases early, since they aren't instant. This project uses a global profile, so Bedrock can route to any region with capacity.

**Your own limits.** Use several layers:

| Limit | Stops |
| --- | --- |
| Per IP | Anonymous floods |
| Per user | One heavy user |
| Tokens per user per day | Cost abuse |
| Total spend | A runaway bill |

[OWASP calls this](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) Denial of Wallet. Redis is a common place to count, and API gateways have this built in.

**Queues for slow work.** If a task can wait, don't hold a request open. SQS is the AWS service. A worker pulls jobs at the rate your quota allows, so a burst becomes a backlog and not a pile of errors.

**Making each turn lighter.** Often the best way to scale is doing less:

- Answer common questions from a cache.
- Use a smaller model for easy work.
- Trim the prompt and history.
- Use prompt caching for what repeats.
- Don't call the model when code can answer.

**Autoscaling** on ECS can follow CPU or request count. But an agent waiting on a model uses little CPU, so CPU is a poor signal. Use open connections or requests per task.

## Try it

1. Work out the tokens per minute for 500 turns a minute, at 2 model calls a turn.
2. Find the limit you'd hit first in the table above, for this project on AWS.
3. In the shop, open two browser windows, and send a question in both at once. Compare the times in the traces.
4. Read `infra/lambda.tf`, and work out how many chat turns a minute 5 requests a second allows.

## Interview questions

### How would you scale an agent to 10,000 users?

**Strong answer:** First I'd find the bottleneck, which is usually model quota and speed, not my servers. I'd work out peak tokens per minute, compare it with quotas, and ask for increases early. Then async containers with autoscaling on connections, a database pool, and per-user limits. I'd cut the load per turn: caching, smaller models where they're good enough, and trimmed prompts. I'd load test by raising traffic until throughput flattens. On my local stack that was 44 turns a minute, and the limit was the GPU.

**Follow-up:** What would you autoscale on?

### A provider starts returning 429s at peak. What do you do?

**Strong answer:** Immediately: retry with backoff and jitter, respect `retry-after`, and shed or queue what can wait. If it's user-facing, say so honestly instead of hanging. Then fix the cause: ask for more quota, spread across regions or models, and cut tokens per turn. I'd alert on throttling before users notice.

**Follow-up:** How do you stop retries making it worse?

### Why rate limit your own users?

**Strong answer:** Because each message costs money and uses shared quota, so one person or a bot can hurt everyone, or run up a bill. I'd limit per IP, per user, and by tokens per day, with an overall spending alarm. My project only has a whole-API limit on API Gateway, and a step limit per turn. Per-user limits are a known gap.

**Follow-up:** How would you do that across many servers?

## Check yourself

### Throughput stops rising as load increases. What does it mean?

- [x] Something is full, so find it — right: more load only adds waiting.
- [ ] The test is broken — it's expected.
- [ ] Add more of everything — only the bottleneck matters.

### Why is CPU a poor autoscaling signal for an agent?

- [ ] It's expensive to measure — it isn't.
- [x] Turns mostly wait, so CPU stays low — right: use connections or requests.
- [ ] Fargate has no CPU — it does.

### What is Denial of Wallet?

- [ ] A payment bug — not quite.
- [ ] A refund attack — that's something else.
- [x] Running up your bill through heavy use — right: so set limits.
