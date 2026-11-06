---
title: Incidents and rollback
checked: 2026-11-06
---

## What you'll learn

- What to do, in order, when something breaks
- What's different about an AI incident
- Your options for stopping the harm quickly
- How to learn from it without blame

## The simple explanation

An incident is when something's wrong for users, and it needs attention now.

Think of a kitchen fire. First you turn off the gas. You don't start by working out why the pan caught fire. Then you make the place safe, then you find the cause, and then you change something so it doesn't happen again.

The order matters:

| Step | Goal | Not yet |
| --- | --- | --- |
| 1. **Detect** | Know it's happening | |
| 2. **Assess** | How bad, and who's affected? | Finding the cause |
| 3. **Mitigate** | Stop the harm | The perfect fix |
| 4. **Communicate** | Tell who needs to know | Guesses |
| 5. **Fix** | Find and repair the real cause | Blame |
| 6. **Learn** | Stop it happening again | |

The most common mistake is jumping to step 5. **Stop the bleeding first.** A rollback that works in two minutes beats a clever fix that takes two hours.

## An example

Let's walk through one. It's a drill, since this project has no customers, but it uses a measured fact: a planted policy made the agent send customers to an outside link, [5 times out of 5](../08-security/02-prompt-injection.md).

**9:02.** A customer reports a strange link in a shipping answer.

**Detect.** Nothing alerted, because every metric is fine. It's a 200 with normal latency. This is the quiet failure from [the first lesson](01-monitoring-and-tracing.md).

**Assess.** Is it one case, or many? Search for the link in `chat_history`. The trace shows `search_policy` returned a chunk from a file nobody recognises.

**Mitigate.** Remove the document, and re-ingest:

```bash
docker compose up setup
```

Or, if you can't find the source quickly, turn off that tool or the whole chat. A "chat is unavailable" message is better than a phishing link.

**Communicate.** Tell support what's happening, and tell affected customers not to use the link. Find who received it from history.

**Fix.** Find how the file got there, and add an output rule for links.

**Learn.** Add a golden case, an alert for unknown links, and a review step for policy changes.

Notice how many steps needed something built in advance. **You can't build the off switch during the fire.**

## How ShopHelper does it

**Rollback by tag.** Images are immutable, so going back to a known-good version is one command, on a real deployment:

```bash
TAG=<older-commit> scripts/release.sh
```

**Automatic rollback.** ECS undoes a deployment that fails health checks:

```hcl file=infra/ecs.tf
rollback = true
```

**A safe failure.** When policy search fails, the agent doesn't guess. Code replaces the answer:

```python file=src/shophelper/agent/graph.py
return {"messages": [AIMessage(NO_POLICY_ANSWER)]}  # no passages, so nothing to answer from
```

That's a small example of **failing safely**: being unhelpful is better than being wrong.

**Demo reset.** Admins can reset demo orders, which is handy here and has no place in production.

**A runbook** lists known problems and fixes, in [runbook.md](../../reference/runbook.md):

| Symptom | Cause or fix |
| --- | --- |
| First Lambda request slow | Cold start, about 4 s |
| 503 from API Gateway after 30 s | Very long agent turns. Use the load balancer |
| ECS deploy rolls back | Check the logs for the startup error |

**What's missing:**

- No kill switch for the agent or a single tool. You'd have to redeploy, or stop the service.
- No handover to a human when the agent is struggling.
- No on-call or paging. Alarms go to one email address.
- No status page.
- The health check doesn't test the model or database.

## In the market

Checked on 2026-11-06.

**Ways to stop the harm, fastest first:**

| Option | Speed | Use when |
| --- | --- | --- |
| Feature flag: turn off a tool or the chat | Seconds | You have one, and the harm is ongoing |
| Roll back the prompt | Seconds, if prompts are config | A prompt change caused it |
| Fall back to another model | Minutes | The provider is down or misbehaving |
| Roll back the code | Minutes | A release caused it |
| Remove a document, and re-ingest | Minutes | Bad knowledge |
| Hand over to humans | Depends | All else fails |

**AI incidents have their own shapes:**

| Incident | First move |
| --- | --- |
| Provider outage | Fall back, or show an honest message |
| Wrong answers after a release | Roll back, and compare traces |
| Prompt injection in the wild | Turn off the tool, and check what was reached |
| A leak of private data | Stop it, keep the evidence, and bring in legal and security |
| A runaway bill | Limit or disable, then find the loop |
| Harmful output shared publicly | Stop it, and have someone own communication |

**What a rollback can't undo:** sent messages, promises made, and wrong refunds. Air Canada was held to [a refund policy its chatbot invented](https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html), in a 2024 tribunal case. What an agent says can matter long after you've fixed the bug.

**Postmortems.** Write one after any real incident. Google's guidance on [blameless postmortems](https://sre.google/workbook/postmortem-culture/) says to focus on how the system failed, not who failed:

- What happened, with a timeline.
- The impact, in numbers.
- Root causes, more than the trigger.
- What went well, what went badly, and where you got lucky.
- Actions, each with an owner and a measurable end.

Blame makes people hide things. Good systems assume people will make mistakes, and make those mistakes safe.

## Try it

1. Read `docs/reference/runbook.md`. Add one row for something that went wrong while you were learning.
2. Stop LM Studio's server with `lms server stop`, and ask the agent something. What does the customer see? What do the logs show? Then run `lms server start`.
3. Write a one-page postmortem for the drill above.
4. Design a kill switch for this project. Where would the check go, and who could press it?

## Interview questions

### Your agent starts giving wrong answers in production. What do you do?

**Strong answer:** First stop the harm, then find the cause. I'd assess scope from traces, then roll back whatever changed last, or turn off the affected tool if I can't tell. I'd tell support, and find who was affected. Then find the cause by checking what changed: code, prompt, model, documents or traffic. After that, a blameless postmortem, and I'd add the failing case to my evals. A wrong answer is a 200, so I'd also ask why nothing alerted.

**Follow-up:** How do you know what changed?

### The model provider goes down. What happens?

**Strong answer:** It depends what I built beforehand. Ideally a timeout, a retry, then a fallback model or region, then an honest message, and a route to a human. Agents should fail safely, not guess. My project replaces the answer when policy search fails, and it has one model path. So a full outage would show an error. I'd add a fallback and a status message, and test them by turning the model off.

**Follow-up:** How would a fallback model change your evals?

### What makes a good postmortem?

**Strong answer:** It's blameless, and it's about how the system allowed the failure. It has a timeline, the impact in numbers, root causes beyond the trigger, what went well, and where we got lucky. Each action has an owner and a measurable end. It's written soon, and shared widely. For AI, I'd include the exact prompt, model and document versions, and turn the failure into an eval case.

**Follow-up:** How do you make sure actions get done?

## Check yourself

### What comes first in an incident?

- [ ] Finding the root cause — that comes later.
- [ ] Blaming the last deployer — never.
- [x] Stopping the harm — right: mitigate, then fix.

### Why did nothing alert in the drill?

- [x] A bad answer is a normal 200 — right: quiet failures need other signals.
- [ ] The alarm was asleep — alarms don't sleep.
- [ ] Logs were turned off — they were on.

### What's the point of a blameless postmortem?

- [ ] To avoid writing anything down — the opposite.
- [ ] To protect managers — that's not it.
- [x] To fix the system, with people being honest — right: blame makes people hide things.
