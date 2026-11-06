---
title: Managing prompts and models after launch
checked: 2026-11-06
---

## What you'll learn

- Why prompts need versions, like code
- Where prompts can live
- What happens when a model is retired
- How to keep an AI product healthy over time

## The simple explanation

Launching isn't the end. A normal app stays the same until you change it. An AI product can change under you: models get retired, documents go out of date, and customers ask new things.

Think of a car. You don't buy it and forget it. There are services, new tyres, and recalls you didn't choose. An AI product needs the same kind of care, on a schedule.

There are four things to manage:

| Thing | Changes because | Treat it like |
| --- | --- | --- |
| **Prompts** | You improve them | Code |
| **Models** | Providers update and retire them | A dependency |
| **Knowledge** | The business changes | Content with an owner |
| **Eval sets** | Real failures appear | A growing test suite |

The rule for all four: **know exactly what was running when an answer was given.** If you can't say which prompt, model and documents produced an answer, you can't debug it.

## An example

Model retirement is real, and it's already reached this project.

[Anthropic's deprecations page](https://platform.claude.com/docs/en/about-claude/model-deprecations) says requests to a retired model fail. It promises at least 60 days' notice for public models. The dates listed when we checked:

| Model | Status | Retirement |
| --- | --- | --- |
| Claude Haiku 4.5 | Active | Not sooner than 2026-10-15 |
| Claude Sonnet 4.6 | Active | Not sooner than 2027-02-17 |
| Claude Sonnet 4.5 | Deprecated | 2026-11-30 |

The first two are this project's AWS defaults:

```hcl file=infra/variables.tf
default = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
```

Haiku 4.5's "not sooner than" date has already passed. It's still listed as active, but it could get a notice at any time. Bedrock sets its own schedule, too, so these dates may differ there. **A date in a config file is a slow-burning problem.**

It's not only models. Parameters change as well. The same page lists `temperature` as removed in API version `2026-10-21`, and this project's judge sends it:

```python file=evals/judge.py
inferenceConfig={"maxTokens": 300, "temperature": 0},
```

That's through Bedrock's Converse API, so it may behave differently, and we haven't tested it. But it's exactly the sort of thing to check when moving models. A migration is more than a new id.

## How ShopHelper does it

**Prompts live in code.** The system prompt is a constant in `graph.py`:

```python file=src/shophelper/agent/graph.py
SYSTEM_PROMPT = """You are ShopHelper, a concise, friendly customer-support assistant for a \
```

So it has version history through git, review through pull requests, and tests through the evals. Project rules say prompt changes need the full evals, with `EVAL_RUNS=3` when it matters. That's a good default for a small team.

The cost is that changing a word means a deployment, and a non-engineer can't do it.

**Models are settings.** Changing one is an environment change, and evals are the gate:

```python file=src/shophelper/core/config.py
local_chat_model: str = "qwen/qwen3-30b-a3b-2507"
```

**Knowledge has a pipeline.** Policies are Markdown in git, so they get review too. `docker compose up setup` re-embeds only what changed, using a hash of each file. On AWS, an ingestion job does this.

There's even a test that catches drift between two copies. The shop's returns page must match the agent's policy, or the build fails. Otherwise a customer could read one thing and be told another.

**Eval sets grow.** Every bug becomes a case. It started at 20, and it's now 37.

**What's missing:**

- No prompt or model version in the logs, so you couldn't tell which one gave an old answer. Git history and dates are the only link.
- No scheduled eval run, so a provider's change wouldn't be noticed.
- No owner or review date on policy documents.
- No record of when a model retires, beyond this lesson.

The first is the cheapest fix: add two fields to the log line.

## In the market

Checked on 2026-11-06.

**Where prompts can live:**

| Option | Good | Bad |
| --- | --- | --- |
| In code | Review, tests, one history | Needs a deployment |
| In a config file | Same, and easier to find | Still a deployment |
| In a [prompt tool](https://langfuse.com/docs/prompt-management/features/prompt-version-control) | Change and roll back in seconds, and non-engineers can edit | Can skip review and evals, unless you add them |

Langfuse, for example, uses **labels**: your code asks for the `production` label, and rolling back means moving that label to an older version. Protected labels limit who can do it. That's powerful, and the risk is the same: a fast change is one that bypasses your tests.

**Migrating to a new model**, in order:

1. Read the migration notes: parameters, behaviour, tokenizer.
2. Run your evals on the new model, and compare.
3. Re-tune prompts. Rules written for one model can hurt another.
4. Check your judge, if it's the same model family.
5. Check cost and latency.
6. Release gradually, as in [ways to release](../09-cloud-deployment/06-ways-to-release.md).
7. Keep the old one available until you're sure.

Anthropic's own advice is to test with new models well before the retirement date, and its console can export usage by model, to find what's still using an old one.

**A simple routine:**

| How often | Do |
| --- | --- |
| Weekly | Read a sample of real conversations |
| Weekly | Review failures, and add eval cases |
| Monthly | Check model deprecation notices |
| Monthly | Review cost per resolved conversation |
| Quarterly | Review documents with their owners |
| Quarterly | Try the newest models against your evals |

Reading real conversations sounds small. It's often the most valuable hour of the week.

## Try it

1. Run `git log --oneline -- src/shophelper/agent/graph.py`. That's your prompt's version history.
2. Open the [deprecations page](https://platform.claude.com/docs/en/about-claude/model-deprecations), and find today's status of this project's two AWS models.
3. Add `prompt_version` and `model` to `_log_turn` in `src/shophelper/api/app.py`, as an experiment. What would you use for the version? Undo it afterwards.
4. Write a one-page migration plan from Haiku 4.5 to a current model for this project.

## Interview questions

### How do you manage prompts in production?

**Strong answer:** Like code: versioned, reviewed, and tested with evals before release. Mine live in code, so they get git history and CI, and a rollback is a code rollback. That's slower to change. A prompt tool lets me change and roll back in seconds, and lets non-engineers edit, but I'd keep evals as the gate so a quick edit can't skip them. Either way, every answer should record which version made it. Mine doesn't yet, and that's a cheap fix.

**Follow-up:** Who should be allowed to change a prompt?

### Your model is being retired in 60 days. What's your plan?

**Strong answer:** I'd find everything using it, then read the migration notes, because parameters and behaviour change, and not just the name. I'd run evals on the replacement, re-tune prompts, and check cost, latency and my judge. Then release gradually, with the old one ready. It's already relevant for me: my AWS default is Haiku 4.5, and its "not sooner than" date has passed, so I'd plan that move before deploying.

**Follow-up:** What if the new model scores lower on one case?

### How do you keep an AI product good after launch?

**Strong answer:** I treat prompts, models, knowledge and evals as things that need upkeep. I read real conversations every week, turn failures into eval cases, check deprecation notices, and review documents with their owners. I'd run evals on a schedule to catch changes I didn't make. And I log which versions produced each answer, so any problem can be traced.

**Follow-up:** Who owns that work?

## Check yourself

### What should you be able to say about any past answer?

- [ ] How the customer felt — you may not know.
- [x] Which prompt, model and documents produced it — right: otherwise you can't debug it.
- [ ] Who wrote the code — that's not the point.

### Why is a model migration more than a new id?

- [x] Parameters, behaviour and costs can all change — right: so test it.
- [ ] It isn't: only the name changes — models differ.
- [ ] Providers require a new account — they don't.

### What's the risk of a prompt tool?

- [ ] It's too slow — it's fast.
- [ ] It can't roll back — that's its strength.
- [x] Changes can skip your evals — right: keep the gate.
