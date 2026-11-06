---
title: Agent frameworks
checked: 2026-11-06
---

## What you'll learn

- What a framework gives you, and what it costs
- The main options, and how they differ
- Why this project chose LangGraph
- How to choose, and how to avoid being locked in

## The simple explanation

An agent framework is a library that handles the repeated work around the loop: state, tools, memory, pausing and tracing.

Think of building a house. You could cut your own timber, or buy ready-made window frames. Frames save time, but you live with their sizes.

You've seen the loop by hand in [The agent loop](02-the-agent-loop.md), so you know what's underneath. Every framework is that loop, plus features.

| You get | You pay |
| --- | --- |
| Less code for common needs | Another thing to learn |
| Tested handling of state and pausing | Layers that can hide what's happening |
| Tracing and integrations | Their updates and breaking changes |

Anthropic's [advice](https://www.anthropic.com/engineering/building-effective-agents) is to start with plain API calls, because many patterns take only a few lines. Frameworks can add layers that hide the prompts underneath, so if you use one, make sure you understand the code.

Frameworks fall into rough groups:

| Group | Idea | Examples |
| --- | --- | --- |
| **Graphs** | You draw the steps and paths | LangGraph, Microsoft Agent Framework |
| **Roles** | You describe a team | CrewAI |
| **Provider SDKs** | A light agent loop from a model company | OpenAI Agents SDK, Claude Agent SDK |

## An example

Say you need an agent that pauses for a person, for hours, and survives restarts.

With the raw loop, you'd write the saving, the resuming and the state handling yourself, and get the edge cases wrong a few times.

With LangGraph it's a few lines, and that's why this project uses it:

```python file=src/shophelper/agent/graph.py
decision = interrupt({
```

Now say you need one question answered with one tool. A framework adds nothing, so the raw loop or a client SDK is fine.

The need decides, not the fashion.

## How ShopHelper does it

This project uses LangGraph, and it also keeps a framework-free version on purpose:

```python file=src/shophelper/agent/raw_agent.py
def run_agent(
```

The hand-written loop is there to learn from. The real agent needs what the framework gives:

| Need | Why LangGraph fits |
| --- | --- |
| Pausing for human approval | `interrupt()` |
| Surviving restarts | Checkpointers for Postgres and DynamoDB |
| Different paths | Nodes and edges |
| Showing each step | Streaming |

The cost was real too. LangGraph's re-run on resume [catches people out](05-human-approval.md), and identity needed special handling inside tools.

To avoid being locked in, the framework stays in `src/shophelper/agent/`. Tools, orders and rules are plain Python, and tools are served over MCP, so they don't depend on LangGraph.

## In the market

Checked on 2026-11-06, from each project's own docs. Comparison blogs often disagreed, so check the source.

| Framework | What it is | Good for |
| --- | --- | --- |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | A low-level runtime for long-running, stateful agents. It doesn't require LangChain | Durable flows, human approval, explicit control |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | A light Python package, with handoffs, guardrails, sessions and tracing. Supports other providers through adapters | Getting started quickly with few concepts |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | Claude Code's agent loop and tools, as a library for Python and TypeScript | Agents that work with files and commands |
| [CrewAI](https://docs.crewai.com/en/introduction) | Crews of agents, plus step-based flows | Role-based teams |
| [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview) | The direct successor to AutoGen and Semantic Kernel, for .NET, Python and Go | Microsoft stacks |

Two things to watch:

- **Old advice dates fast.** Microsoft now directs AutoGen users to Agent Framework, so older tutorials may point at a path that's been replaced. OpenAI's Swarm was experimental, and the Agents SDK is its successor.
- **Hosted options exist too.** [Claude Managed Agents](https://code.claude.com/docs/en/agent-sdk/overview) hosts the agent for you, and AWS has Bedrock AgentCore. [Stage 9](../09-cloud-deployment/01-running-locally.md) covers deployment.

**How to choose:**

1. Do you need one at all? If the loop is simple, skip it.
2. What do you need most: pausing, multi-agent, or speed of building?
3. What does your team know, and what's your stack?
4. Which models must it support?
5. Build one small real feature in your top choice before committing.

**Stay portable.** Keep business rules and tools outside the framework, keep your evals independent of it, and swapping becomes a contained job.

## Try it

1. Read [raw_agent.py](../../../src/shophelper/agent/raw_agent.py), then the graph in [graph.py](../../../src/shophelper/agent/graph.py).
2. Find the same four steps in each: ask, check, run, repeat.
3. List what `graph.py` does that the raw loop doesn't. That list is what the framework is for.

## Interview questions

### Why did you choose LangGraph?

**Strong answer:** My agent needs to pause for human approval and survive restarts, which is what LangGraph's `interrupt()` and checkpointers give me. I wrote the loop by hand first, so I know what it's doing. The trade-offs are more concepts, and surprises like nodes re-running on resume. For a simple tool loop I wouldn't use it. I keep my tools and rules outside it, so it could be replaced.

**Follow-up:** What would make you switch?

### Should a team use a framework or build their own?

**Strong answer:** It depends on what they need. For a simple loop I'd write it directly, since it's short and clear. For durable state, approvals or complex paths, a framework saves real work and edge cases. Either way, the team should understand the loop underneath. And I'd keep rules and tools separate, so the choice isn't permanent.

**Follow-up:** What's the risk of building your own?

### How do you avoid being locked in to a framework or model?

**Strong answer:** Keep business logic in plain code, and let the framework only do orchestration. Put the model behind a setting. Serve tools through something neutral like MCP. And own your evals, because they're what let you change something and know whether it still works. My evals run against the service, not the framework's internals.

**Follow-up:** What would be hardest to move in your project?

## Check yourself

### What do all these frameworks have at their core?

- [x] The agent loop — right: ask, check, run, repeat, plus features.
- [ ] A special model — they work with existing models.
- [ ] A database — some use one, but that isn't the core.

### Why does ShopHelper keep `raw_agent.py`?

- [ ] It's the production agent — production uses LangGraph.
- [x] To show what the framework does for you — right: it's the loop with nothing hidden.
- [ ] It's left over — it's kept on purpose.

### What's the best way to stay portable?

- [ ] Put all your logic in the framework — that ties you to it.
- [x] Keep rules and tools outside it, and own your evals — right: then swapping is a contained job.
- [ ] Never use a framework — sometimes one's the right choice.
