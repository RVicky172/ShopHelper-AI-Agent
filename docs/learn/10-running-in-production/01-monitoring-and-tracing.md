---
title: Monitoring and tracing
checked: 2026-11-06
---

## What you'll learn

- The difference between logs, metrics and traces
- Why agents need more than a normal dashboard
- What this project records on each turn
- What to do about private data in traces

## The simple explanation

Once real people use your agent, you can't sit beside each one. You need a way to see what happened.

Think of running a hospital ward. Monitors show every patient's heart rate at a glance. Notes record what happened. And a patient's chart tells one person's full story. You need all three.

| Tool | Answers | Picture |
| --- | --- | --- |
| **Metrics** | How are we doing overall? | The heart-rate monitor |
| **Logs** | What happened at this moment? | The nurse's notes |
| **Traces** | What happened on this one request, step by step? | The patient's chart |

Normal apps fail loudly: a 500 error, a crash. **Agents fail quietly.** A fluent wrong answer is a 200 OK, with no error anywhere. So a green dashboard can hide a bad day, and that's the big difference.

An agent's trace has to answer questions a normal one doesn't: what did the model see, which tools did it pick, why did it stop, and what did it cost?

## An example

Here's a real log line from this project, one per turn:

```json
{"event": "chat_completed", "runtime": "local", "endpoint": "chat_stream",
 "session_id": "c-ab54cb7c-...", "status": "answered", "tools": ["get_order_status"],
 "input_tokens": 1423, "output_tokens": 80, "latency_ms": 2961}
```

A customer says "the bot was wrong earlier". With that one id, you can follow the thread:

1. Find the turn in the logs, using `session_id`.
2. See which tools ran.
3. Read the conversation in `chat_history`.
4. On the trace, read what the model actually received.

Without an id that joins these together, you'd be guessing. **Give every turn an id, and put it everywhere.**

Notice what's not in that line: the customer's message. That's deliberate. Logs spread widely and are kept for a long time, so they shouldn't hold what people typed.

## How ShopHelper does it

**Logs.** One JSON line per turn, printed to standard output:

```python file=src/shophelper/core/observability.py
print(json.dumps(record, default=str), file=sys.stdout, flush=True)
```

Structured logs matter because a machine can read them. That's enough to get metrics for free.

**Metrics.** On AWS, CloudWatch turns those lines into numbers, with no agent or SDK:

```hcl file=infra/observability.tf
InputTokens     = { pattern = "{ $.event = \"chat_completed\" }", value = "$.input_tokens" }
```

There are 7 metrics: requests, input and output tokens, latency, guardrail blocks, refunds pending, and errors. Each is split by runtime, Lambda or ECS, and a dashboard shows them with estimated model cost.

**Alarms.** They send an email through SNS:

| Alarm | Fires on |
| --- | --- |
| App errors | 1 or more in 5 minutes |
| Lambda function errors | 1 or more in 5 minutes |
| Load balancer 5xx | 3 or more in 5 minutes |

All of these catch loud failures. **There's no alarm for slow answers, high cost, or a rise in wrong answers.** That's the honest gap.

**Traces.** Two kinds exist here:

- **On How it works**, the live trace shows each step, built from the stream's events. It's great for learning, and it's only there while you watch.
- **LangSmith** records runs when a key is set, because LangGraph sends them automatically. It's off locally. It never ran with a real model on AWS.

**What's stored for later:** the checkpoints in Postgres and `chat_history` keep each conversation, so you can reconstruct a turn afterwards.

**Log retention** is 7 days on AWS, which keeps costs down. A real product would keep more, for as long as its privacy policy allows.

## In the market

Checked on 2026-11-06.

| Tool | Kind | Notes |
| --- | --- | --- |
| [LangSmith](https://docs.langchain.com/langsmith/evaluation) | Hosted | Close to LangChain and LangGraph. Used here, when switched on |
| [Langfuse](https://langfuse.com/docs) | Open source | You can host it yourself |
| [Phoenix](https://arize.com/docs/phoenix) | Open source | Built on OpenTelemetry |
| CloudWatch | AWS | Logs, metrics, alarms. Used here |
| Datadog, Grafana | General | Often already in place |

**A shared standard is forming.** [OpenTelemetry](https://opentelemetry.io/) is the common way to send traces, and its [GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai) define names for model and agent data. They now have their own repository, with sections for agent spans, MCP and specific providers. Sources disagree on how stable they are, so check before you depend on them. Using the standard lets you change tools later.

**Private data in traces.** A trace holds prompts and answers, so it's a copy of your customers' words, maybe on someone else's servers. So:

- Mask before sending. Here, masking happens first, so history and traces see `{EMAIL}`.
- Decide what's kept, and for how long.
- Limit who can read traces. They're as sensitive as the data in them.
- Sample if you can't keep everything.

## Try it

1. Run this, and read the most recent turns:

```bash
docker compose logs api --no-log-prefix | grep chat_completed | tail -n 5
```

2. Pick a `session_id`, and find that conversation in pgAdmin:

```sql
SELECT role, text, created_at FROM chat_history
WHERE session_id = 'PASTE-THE-ID'
ORDER BY created_at;
```

3. On **How it works**, ask a question, and name one fact the trace shows that the log line doesn't.
4. Find the 7 metrics in `infra/observability.tf`. Which would you add first?

## Interview questions

### How do you monitor an AI agent in production?

**Strong answer:** Three layers. Metrics for overall health: traffic, latency, errors, tokens and cost. Logs with one structured line per turn, joined by a session id. And traces showing what the model saw and which tools it called. But agents fail quietly, since a wrong answer is still a 200, so I also score a sample of real answers, and track outcomes like escalations. My project has the first parts, with alarms on errors. It doesn't yet alert on quality or cost.

**Follow-up:** How would you score real answers?

### Why isn't normal APM enough for an agent?

**Strong answer:** It sees requests, not reasoning. A turn can return 200 in three seconds, with the wrong tool, a made-up fact, or a promise it didn't keep. I need the prompt, passages, tool calls and token use per step. And cost varies per request, unlike most web apps. So I'd keep APM, and add an LLM tracing layer, ideally on OpenTelemetry so I'm not tied to one vendor.

**Follow-up:** What would you put on one dashboard?

### What are the privacy risks of tracing?

**Strong answer:** A trace is a copy of customers' words. So I mask before anything is stored or sent, keep it for a limited time, restrict who can read it, and check where a hosted tool keeps it. My logs have ids and counts, not message text, and masked text is what reaches history. I'd also think about deletion: if a customer asks, their traces have to go too.

**Follow-up:** How would you delete one customer's data?

## Check yourself

### Why can an agent fail with a green dashboard?

- [x] A wrong answer still returns 200 — right: agents fail quietly.
- [ ] Dashboards are slow to update — that's not the point.
- [ ] Agents never fail — sadly they do.

### What links a complaint to what happened?

- [ ] The customer's name in the logs — that puts private data in logs.
- [x] A session id, used everywhere — right: it joins logs, history and traces.
- [ ] The time of day — too vague.

### Which of these is a trace for?

- [ ] Overall traffic — that's a metric.
- [ ] Billing — that's not its job.
- [x] One request, step by step — right: the patient's chart.
