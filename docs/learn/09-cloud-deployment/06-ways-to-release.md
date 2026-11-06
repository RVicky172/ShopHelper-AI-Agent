---
title: Ways to release
checked: 2026-11-06
---

## What you'll learn

- Rolling, blue/green, canary and shadow releases
- How to separate deploying from releasing
- How to release a prompt or a model safely
- How this project rolls back

## The simple explanation

Deploying is putting new code on servers. Releasing is letting people use it. Good teams keep those apart.

Think of a restaurant changing its menu. It can swap everything at once and hope. It can try the new dish on one table first. Or it can cook the new dish alongside the old one, tasting it in the kitchen before anyone orders it.

| Strategy | How | Risk | Cost |
| --- | --- | --- | --- |
| **All at once** | Replace everything | Everyone hit at once | Lowest |
| **Rolling** | Replace a few at a time | Old and new run together | Low |
| **Blue/green** | Build a full copy, then switch | Instant switch back | Double, for a while |
| **Canary** | Send a small share to the new version | Only that share is affected | Needs good metrics |
| **Shadow** | New version gets real traffic, and its answers are thrown away | No user risk | Double the model bill |
| **Feature flag** | Code ships switched off | Turn on per user | Flags to manage |

[Blue/green](https://martinfowler.com/bliki/BlueGreenDeployment.html) and [canary](https://martinfowler.com/bliki/CanaryRelease.html) are the two most often asked about.

## An example

Say you want to move the agent from one model to a cheaper one. A code test can't tell you if that's safe. Here's a careful release:

1. **Offline.** Run the golden set on the new model. Compare it with the old one.
2. **Shadow.** Send a copy of real questions to the new model, and record its answers without showing them. Compare answers, cost and speed.
3. **Canary.** Send 5% of real conversations to it. Watch failed tools, escalations, thumbs-down and cost.
4. **Ramp.** 25%, 50%, 100%, with a pause at each step.
5. **Keep the old one ready.** Going back is one setting.

Each step tests something the last couldn't. And each costs more, so a small prompt fix doesn't need all five.

An agent adds a wrinkle: **stick to one version per conversation.** Switching models halfway through can confuse a conversation, and a saved checkpoint from one version may not suit another. So route by conversation, not by request.

## How ShopHelper does it

**ECS uses a rolling deployment**, with an automatic safety net:

```hcl file=infra/ecs.tf
deployment_circuit_breaker {
enable   = true
rollback = true
```

If new tasks keep failing their health checks, [ECS stops, and goes back](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html) to the last good version. That needs a health check that means something. This project's `/health` only proves the process is up, and it wouldn't notice that the model is failing.

**Lambda swaps everything at once.** `update-function-code` points at the new image. It's simple and quick, and everyone moves together. Lambda offers aliases for gradual shifts, and they aren't used here.

**Rolling back by hand.** Images are immutable, and tagged by commit, so going back means releasing an older tag:

```bash
TAG=<older-commit> scripts/release.sh
```

That command changes a live service, so only run it on a real deployment.

**Things a rollback can't undo:**

- **Database changes.** If a release changes the schema, the old code may not work with it. Make changes in small steps that both versions can handle.
- **Saved agent state.** A paused refund is a checkpoint made by the old version. If the graph's shape changes, it may not resume. This project has no versioning for that.
- **Sent messages and refunds.** They've happened.

**Prompts** live in code here, so they go through the same pipeline, and a rollback is a code rollback. That's simple, and it's slow: changing a prompt means a deployment.

**Feature flags.** Settings work as a simple kind of flag. For example, `enable_ecs` and `AWS_DEPLOY_ENABLED` turn things on and off. There's no per-user flag system.

**So what's here?** Rolling with auto-rollback on ECS, all-at-once on Lambda, and rollback by tag. There's no canary or blue/green, and it's never been needed, because there's never been a real customer. For a real product, canary comes first, because model changes are hard to judge offline.

## In the market

Checked on 2026-11-06.

| Tool | Gives you |
| --- | --- |
| [AWS CodeDeploy](https://docs.aws.amazon.com/codedeploy/latest/userguide/welcome.html) | Blue/green and canary for ECS and Lambda |
| Lambda aliases | Weighted traffic between versions |
| Load balancer weights | Split traffic between target groups |
| LaunchDarkly, Unleash | Feature flags |

**Prompts as config.** Tools such as LangSmith and Langfuse can store prompts outside the code, so you can change one without a deployment, and go back quickly. The cost is that prompts then skip code review and CI, unless you add that back. Whichever you choose, version them, and link each result to the version that made it.

**Provider changes.** A hosted model can be retired or updated by its provider. Pin versions where you can, and watch for retirement notices. That's a release you didn't choose.

## Try it

1. In `infra/ecs.tf`, find the circuit breaker and the health check.
2. In `src/shophelper/api/app.py`, read `/health`. What could be broken while it still says `ok`?
3. Design a release for changing `MAX_CHUNK_CHARS`. Which steps do you need, and what would you measure?
4. Say what you'd do if a bad prompt shipped at 5 pm, in each of the two designs: prompts in code, and prompts in a tool.

## Interview questions

### How would you roll out a new model to production?

**Strong answer:** Offline evals first, comparing with the current model. Then shadow traffic if I can afford it, then a canary at a few percent, routing by conversation so nobody switches midway. I'd watch task success, tool errors, escalations, cost and latency, and ramp up in steps. The old model stays one setting away. My project isn't there: it has rolling deploys and rollback by tag, and no canary, since it has no real users.

**Follow-up:** What metric would stop the rollout?

### What's the difference between blue/green and canary?

**Strong answer:** Blue/green builds a full second copy, tests it, and switches all traffic at once, so switching back is instant, at the cost of double capacity for a while. Canary sends a small share of real traffic to the new version, and grows it, so problems reach few users, but you need good metrics to notice. For AI changes I'd prefer canary, because behaviour problems show up in real use.

**Follow-up:** When would you choose blue/green?

### What can't a rollback fix?

**Strong answer:** Anything already written or sent. Schema changes can break old code, so I change schemas in compatible steps. Paused agent state from a new version might not resume on the old one, and refunds or messages have already happened. So I make risky changes reversible, and keep side effects behind checks.

**Follow-up:** How would you version agent state?

## Check yourself

### What's a shadow release?

- [ ] A release at night — not quite.
- [x] Real traffic reaches the new version, and its answers aren't shown — right: no user risk.
- [ ] A secret feature — that's closer to a flag.

### Why route a canary by conversation?

- [ ] It's cheaper — cost isn't the reason.
- [ ] Load balancers require it — they don't.
- [x] Switching versions mid-conversation can confuse it — right: keep each one on one version.

### What does this project's ECS rollback depend on?

- [x] Health checks failing — right: so a shallow check limits it.
- [ ] A person watching — it's automatic.
- [ ] The evals — they run before deployment.
