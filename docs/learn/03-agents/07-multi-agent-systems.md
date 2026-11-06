---
title: Multi-agent systems
checked: 2026-11-06
---

## What you'll learn

- What multi-agent means, and the main designs
- What it gains you, with real numbers
- What it costs
- When not to use it

## The simple explanation

A **multi-agent system** uses several agents, each with its own instructions, tools and context, working on one job.

Think of a research team. A lead reads the brief, splits it up, and sends people off to look into different parts. They work at once, and each comes back with a short summary, not everything they read. The lead puts it together.

That shows the two real benefits:

- **Parallel work.** Several searches at once.
- **Separate context.** Each agent has its own window, so it isn't distracted by the others' detail, and only a summary comes back.

The main designs:

| Design | How it works |
| --- | --- |
| **Lead and sub-agents** | A lead delegates, and combines the results |
| **Handoffs** | One agent passes the whole conversation to a specialist |
| **Role-based crews** | Agents with roles, such as researcher and writer, work through tasks |
| **Graphs** | Fixed paths between agents, in your code |

## An example

Anthropic [published how its research system works](https://www.anthropic.com/engineering/multi-agent-research-system). A lead agent plans, then starts sub-agents that search in parallel, each in its own context window.

Their reported results:

| Measure | Result |
| --- | --- |
| Quality on their internal research eval | 90.2% better than a single agent |
| Research time on complex questions | Cut by up to 90% |
| Tokens used by an agent, against a chat | About 4 times |
| Tokens used by a multi-agent system, against a chat | About 15 times |

These are Anthropic's figures, for its own system and test. But the shape is the point: it works very well on the right task, at a high price. They also found that token use alone explained most of the difference in performance. Much of the gain comes from spending more.

It also suits only some work. They note it fits poorly where agents need to share context or depend on each other, and that most coding tasks fall into that group. Agents also coordinate poorly in real time.

Here's a test. Are the parts **independent**? Reading 10 sources is independent. Writing one coherent document isn't, because every part depends on the others.

## Not in ShopHelper

ShopHelper is a single agent, on purpose. Questions here are short and take a tool call or two, so splitting them up adds cost and nothing else.

You could imagine a "refund agent" and an "orders agent", but it wouldn't help:

- It would add a routing step before every answer.
- The two tools fit easily in one prompt.
- Each handoff is a chance to lose detail.

If this grew to dozens of tools across very different areas, a split could start to pay off. Even then, try [routing](06-workflow-patterns.md) first.

**The failure modes** are worth knowing, because interviews ask:

| Problem | Why it happens | What helps |
| --- | --- | --- |
| Costs explode | Each agent has its own calls | Budgets, and limits on sub-agents |
| Errors compound | One agent's mistake feeds the next | Checks between steps |
| Agents repeat work | Unclear tasks | Give each a clear, separate brief |
| Hard to debug | Many paths | Trace every step |
| One failure stops everything | Tight dependencies | Timeouts, and carrying on with partial results |

## In the market

Checked on 2026-11-06.

| Tool | Approach |
| --- | --- |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | Graphs with explicit paths |
| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) | Handoffs, or agents as tools |
| [CrewAI](https://docs.crewai.com/en/introduction) | Role-based crews, plus step-based flows |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | Sub-agents for focused tasks |
| [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview) | Graph-based workflows between agents |

The [next lesson](08-frameworks.md) compares these.

You can see this pattern in Claude Code: a helper agent does a noisy search, and only the summary returns. The [official docs](https://code.claude.com/docs/en/best-practices) describe sub-agents as useful for parallel work, noisy output and independent review.

## Interview questions

### When would you use a multi-agent system?

**Strong answer:** When a task splits into independent parts that benefit from running in parallel, or when each part would swamp a single context, like wide research. It's expensive: Anthropic reported about 15 times the tokens of a chat. So I'd only use it where the value justifies that. If the parts depend on each other, like most coding, or need real-time coordination, I'd keep one agent. My support agent is a single agent because questions need one or two tool calls.

**Follow-up:** How would you measure whether it was worth it?

### Design a system that researches a company and writes a report.

**Strong answer:** The research splits up well, so I'd use a lead agent that plans, and sub-agents that each cover an area, like news, financials and competitors, in parallel with their own context. They'd return short summaries with sources. Writing needs one voice, so one agent writes the report from those. I'd add a citation check, a token budget per sub-agent, and traces of every step. For evals I'd grade the final report against a rubric, since the paths will vary.

**Follow-up:** One sub-agent fails. What happens?

### What goes wrong in multi-agent systems?

**Strong answer:** Cost grows quickly, errors compound as one agent's mistake feeds another, agents duplicate work if their briefs overlap, and it's hard to debug. I'd give each a clear, narrow brief, set budgets, check outputs between steps, and trace everything. I'd also test the system end to end, because each agent can look fine while the whole thing fails.

**Follow-up:** How do you debug it?

## Check yourself

### What's a good test for whether a job suits multiple agents?

- [x] Are the parts independent? — right: dependent parts need shared context, which agents handle poorly.
- [ ] Is the task important? — importance doesn't make it splittable.
- [ ] Do you have a big budget? — money alone doesn't make it a good fit.

### What did Anthropic report about multi-agent token use?

- [ ] About the same as a chat — agents use far more.
- [ ] About 4 times a chat — that's a single agent.
- [x] About 15 times a chat — right: so the task has to be worth it.

### Why is ShopHelper a single agent?

- [x] Questions need a tool call or two, so splitting adds only cost — right: use the simplest thing that works.
- [ ] LangGraph can't do multi-agent — it can.
- [ ] Multi-agent systems don't work — they do, on the right tasks.
