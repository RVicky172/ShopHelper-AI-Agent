---
title: Telling the ShopHelper story
checked: 2026-11-07
---

## What you'll learn

- How to describe this project in 30 seconds, 2 minutes and 10 minutes
- Which of its stories fit common behavioural questions
- Exactly what you can claim, and what you can't
- How to answer the hard follow-ups

## The simple explanation

A project only helps you if you can tell it well. Most people list technologies: "I used LangGraph, pgvector, FastAPI and Terraform." That says nothing about what you can do.

Think about how you'd describe a holiday. Nobody wants the full itinerary. They want where you went, the best moment, and what went wrong. A project story works the same way: what it is, one thing you're proud of, and one thing that went wrong and what you did about it.

Prepare it at three lengths, like a zoom lens. Start short, and let the interviewer pull you in. They'll show you what they care about by what they ask next.

The rule above all others: **only say what's true, and be exact.** Interviewers go deep on purpose. One overstated claim, once exposed, makes them doubt the rest. An honest limit does the opposite.

## An example

**30 seconds, for "tell me about yourself":**

> I built a customer support agent for a small test shop, to learn how these systems really work. It looks up orders, answers from policy documents, and handles refunds with a human approving each one. I spent most of my effort on testing, with 37 evals including 12 attacks, and those found real problems.

**2 minutes, for "tell me about a project":** use four beats.

| Beat | Say |
| --- | --- |
| What it is | A support agent with tools, RAG, MCP and human approval, in a real web shop with accounts |
| The hard part | An agent can act, so a wrong answer can cost money. The model asks, and code decides |
| One real problem | It promised refunds it hadn't requested. A prompt rule only reduced that, so I added a check in code |
| What it proves, and doesn't | It runs end to end, with measured results. It's a learning project, on a local model, with no real customers |

**10 minutes, for a deep dive:** follow one message through the system, as in [how data flows](../02-talking-to-models/05-how-data-flows.md). Stop at the three decisions you know best, and say what you'd do differently.

## How ShopHelper does it

Everything you need is in the repo, so your stories can be exact.

**Stories for common behavioural questions.** Each one is real, with its record:

| They ask about | Tell | The record |
| --- | --- | --- |
| A failure | The false refund promises, and the failing eval that exposed them | Progress log, 2026-11-04 |
| A test that misled you | 20 of 20 repeated, and 0 of 20 mixed with other questions | `memory/learnings.md` |
| A change of plan | Claude on Bedrock was blocked by a form, so the project went local first, and AWS stayed the default | D-003 |
| A cost trade-off | S3 Vectors, not OpenSearch Serverless, which idles at about $12 a day | D-002 |
| Shipping with a known issue | The warranty refund bug, 0 of 8 on one wording: recorded, and left for the backlog | D-023 |
| Accepting less than perfect | Why the bug fix waited, and what the fix would be | D-023 |
| Keeping quality up | Sabotage checks: break the code, and see the test fail | Task notes in `specs/features/` |

Use a simple shape: the situation, what you did, what happened, and what you learned. Keep it near two minutes.

**What you can and can't say.** This table is the most important part of the lesson.

| Topic | True, so say it | Not true, so never say it |
| --- | --- | --- |
| **AWS** | "All 12 steps were deployed and checked on AWS, then destroyed to stop charges" | "It runs on AWS" or "It's in production" |
| **Claude** | "Bedrock refused every Claude call, because a use-case form wasn't active. So evals and latency are unmeasured there" | "I tested it on Claude" |
| **Evals** | "37 of 37 locally, on Qwen" | "It passes every eval", with no mention of the model |
| **Latency** | "Median 2.95 s, p95 9.69 s, over 66 local turns" | "It's fast" or any number for AWS |
| **Users** | "A fictional shop, with demo accounts" | "It served customers" |
| **Scale** | "Local throughput stopped at about 44 turns a minute" | "It scales to thousands" |
| **Who wrote it** | "I directed Claude Code, and it wrote most of the code" | "I wrote it all myself" |
| **Tracing** | "LangSmith is wired in, but it's never run with a real model" | "I use LangSmith in production" |

The AWS row matters most. It's the easiest thing to overstate. The infrastructure really did deploy and get checked, but [no real Claude call ever ran](../09-cloud-deployment/02-planning-it-on-aws.md). Said plainly, it's a good story: you hit a real blocker, and the project kept moving.

**On a CV.** Keep it factual, and let them ask for more:

- Built a customer support agent with LangGraph, RAG on pgvector, MCP tools and human-approved refunds, in a React and FastAPI shop with accounts.
- Wrote a 37-case eval suite, including 12 attacks, which exposed and led to fixing false refund promises.
- Wrote Terraform for two AWS deployments, Lambda and ECS Fargate, and deployed and removed both. Local-first development in Docker, directed with Claude Code and spec-driven development.

Check every line against your own memory before you send it. If you can't defend a line for five minutes, cut it.

**Going deeper.** The follow-ups below are the ones that hurt if you haven't prepared:

| They'll ask | Have ready |
| --- | --- |
| Why LangGraph? | Durable pauses for human approval. See [frameworks](../03-agents/08-frameworks.md) |
| Why MCP here? | Learning, mostly. Say what it adds, and what it costs. See [why MCP](../04-mcp/01-why-mcp.md) |
| Why pgvector? | 24 chunks, and one database to run. See [choosing a database](../06-building-the-app/05-choosing-a-database.md) |
| What would break first? | [Model throughput](../09-cloud-deployment/07-scaling-and-rate-limits.md), then human approval as a queue |
| What would you change? | Version logging, running tracing, and a hook for the checks |

"Learning, mostly" is a perfectly good answer to why you used MCP. Not every choice needs a grand reason, and admitting that sounds like a real engineer.

## Try it

1. Check the stack is running: `docker compose ps --format '{{.Service}} {{.Status}}'`. In a deep dive you may be asked to show it, so know how to start it.
2. Say the 30-second version aloud, and time it. Cut it until it fits.
3. Record the 2-minute version on your phone, and play it back. Did you say what it doesn't prove?
4. Open `memory/decisions.md`, and read D-002, D-003 and D-023. Tell each one as a story, in under two minutes.
5. Cover the right-hand column of the "What you can and can't say" table. For each row, say the true version aloud.
6. Ask someone to interrupt you with "why?" three times in a row. Where did you run out of answers?

## Interview questions

### Was this deployed?

**Strong answer:** Yes and no, so let me be exact. All 12 build steps were deployed to AWS and checked, on both Lambda and ECS Fargate, then destroyed to stop charges. But Bedrock refused every Claude call, because the account's use-case form wasn't active. So the infrastructure was proven, and the evals and real latency on AWS are still unmeasured. I moved to a local model in Docker and kept building there. Before deploying again, I'd also update the model ids and add a login to the API.

**Follow-up:** What would you expect to change on Claude?

### How do you know it works?

**Strong answer:** Three levels. A fast gate of lint, types and unit tests runs on every task. Targeted evals run when the agent changes. The full 37 cases, 12 of them attacks, run once per feature. For important tests I break the code on purpose, to prove they can fail. The limits are that these ran on a local Qwen model, with test data. And I have a known bug: a customer who mentions a warranty can be wrongly refused. It's recorded, with the fix I'd make.

**Follow-up:** Why did you ship with a known bug?

### What are you most proud of, and what would you change?

**Strong answer:** I'm proudest of the refund flow, because it takes safety seriously: the model only proposes, code checks eligibility, and a person approves, and that pause survives a restart. I'd change how I handled visibility. I'd log the prompt and model version from the start, because without them I can't explain an old answer.

**Follow-up:** How would you add that now?

## Check yourself

### What's the true statement about AWS?

- [ ] It runs on AWS today — everything was destroyed.
- [x] It was deployed and checked, but no real Claude call ran — right: say both halves.
- [ ] It was never deployed — it was, on Lambda and Fargate.

### Why give a project's limits without being asked?

- [x] Being exact makes the rest believable — right: an exposed overstatement does the opposite.
- [ ] Interviewers require it — they don't, but it helps you.
- [ ] To sound modest — it's about accuracy, not modesty.

### What should the 30-second version do?

- [ ] List every technology — a list shows no judgement.
- [ ] Explain the whole architecture — that's the deep dive.
- [x] Say what it is, and one thing worth asking about — right: then let them pull you in.
