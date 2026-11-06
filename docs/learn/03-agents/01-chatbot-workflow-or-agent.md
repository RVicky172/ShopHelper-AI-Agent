---
title: Chatbot, workflow or agent?
checked: 2026-11-06
---

## What you'll learn

- The three kinds of AI system, and how they differ
- Why "agent" isn't always the right answer
- How to choose the simplest thing that works
- Where ShopHelper sits, and why

## The simple explanation

People call almost anything an "agent" now. A clearer way to think about it comes from Anthropic's [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents):

| Kind | Who decides the steps? | Example |
| --- | --- | --- |
| **Single model call** | Nobody: one question, one answer | Summarise this email |
| **Workflow** | Your code. The model fills in steps you fixed | Classify a ticket, then route it |
| **Agent** | The model, as it goes | Investigate a problem, choosing what to check next |

Think of three ways to get dinner made:

- A single call is asking for one recipe.
- A workflow is a recipe card: fixed steps, always in that order.
- An agent is a chef: told the goal, deciding what to do as they taste.

A chef handles surprises, but costs more, and takes longer, and may do something you didn't expect. A recipe card is predictable, but useless when something isn't on it.

So the advice is simple: **use the simplest thing that works.** Anthropic's guidance is to start with a single call, and add complexity only when it clearly improves results. Microsoft's docs put it more bluntly: if you can write a function to handle the task, do that.

## An example

Take "Help customers with their refunds". Three ways to build it:

**A single call** can explain the refund policy, if you paste it in. It can't look anything up.

**A workflow** could be: classify the message, look up the order, check the rule, reply. It's reliable, but it breaks when a customer says "my order 1001 arrived, but I also want to know if the kettle in 1004 has a warranty".

**An agent** handles that. It looks up what it needs, in whatever order the question demands. The cost is more model calls, and steps that vary between runs, which makes testing harder.

| | Single call | Workflow | Agent |
| --- | --- | --- | --- |
| Cost | Lowest | Low | Highest |
| Predictable | Yes | Yes | Less so |
| Handles the unexpected | No | Only as designed | Yes |
| Testing | Easy | Easy | Hard |

## How ShopHelper does it

ShopHelper is an agent with workflow parts inside it. That mix is common, and it's where the real design lives.

**The agent part.** The model chooses tools, because customers ask things in endless ways:

```python file=src/shophelper/agent/graph.py
g.add_conditional_edges("agent", route, ["tools", "refund_approval", END])
```

**The workflow parts.** Anything with a right answer is fixed in code, and the model has no say:

| Step | Who decides |
| --- | --- |
| Which tool to use for "where's my order?" | The model |
| Whether a refund is allowed | Code |
| Whether a Care question searches the policy | Code |
| Whether a refund goes ahead | A person |
| Whose orders can be seen | Code |

So the question isn't really "agent or workflow?". It's "which decisions should the model make?". Give it the parts that need judgement, and keep the rest in code.

## In the market

Checked on 2026-11-06.

Primary sources agree on this more than the marketing does:

- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) separates workflows from agents, and says agents trade cost and the risk of compounding errors for flexibility.
- Microsoft: its [Agent Framework docs](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview) say to use an agent for open-ended tasks, and a workflow for well-defined steps.
- LangChain: [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) lets you mix fixed code and model steps in one graph.

Be wary of products calling a fixed script an agent, or suggesting you need agents for everything.

## Try it

1. Sign in, open **How it works**, and ask "Where is order 1001?". The model chose a tool.
2. Ask "What is ShopHelper Care?". Code chose the search, shown by 0 tokens on the first step.
3. Ask for a refund on order 1001. The model asks, code checks, and it waits for a person. Spot all three.

## Interview questions

### When would you build an agent, and when a workflow?

**Strong answer:** I start with the simplest option. If the steps are known and fixed, a workflow is cheaper, faster and easier to test. I'd use an agent when the steps depend on what's found along the way, so they can't be written in advance. Most real systems mix them. In mine the model chooses tools, but refund eligibility, identity and approval are all fixed in code. The real question is which decisions need a model.

**Follow-up:** How would you test the agent parts?

### Someone wants an agent for a task with five fixed steps. What do you say?

**Strong answer:** I'd ask what the agent would add. If the steps are fixed, a workflow gives the same result with lower cost, less delay and easier testing. A model can still do individual steps, like classifying or drafting. If they expect the task to grow into something open-ended, I'd design for that later, but I wouldn't pay for the flexibility now.

**Follow-up:** What would change your mind?

## Check yourself

### What's the main difference between a workflow and an agent?

- [ ] Workflows don't use a model — they often do, at fixed steps.
- [x] In an agent, the model decides the steps — right: in a workflow, your code does.
- [ ] Agents are always better — they cost more, and are harder to test.

### A task has known, fixed steps. What's the best fit?

- [x] A workflow, or plain code — right: use the simplest thing that works.
- [ ] A multi-agent system — that adds cost for no gain.
- [ ] An agent, in case it changes — you'd pay for flexibility you don't need.

### In ShopHelper, who decides whether a refund is allowed?

- [ ] The model — it can only ask.
- [x] Code, then a person — right: the rule is fixed, and a human approves.
- [ ] The customer — they can only request one.
