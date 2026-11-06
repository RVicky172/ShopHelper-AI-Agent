---
title: Designing tools
checked: 2026-11-06
---

## What you'll learn

- How to decide what should be a tool
- The habits that make tools reliable
- Why read and write tools must be treated differently
- What to do when a tool goes wrong

## The simple explanation

You've seen [how tool calling works](../02-talking-to-models/04-tool-calling.md). Now the design question: what tools should an agent have?

Think of tools as the buttons on a remote control. Too few, and you can't do what you want. Too many, and you press the wrong one. Each button needs a clear label.

The biggest idea here is about risk. Reading something and changing something aren't the same:

| | Read tool | Write tool |
| --- | --- | --- |
| Example | Look up an order | Refund an order |
| If the model gets it wrong | A bad answer | Lost money or data |
| Can be undone? | Nothing to undo | Often not |
| How careful to be | Normal | Extremely |

So give a model read access freely, and put anything that changes the world behind something it can't talk its way past.

## An example

A tool's description is the whole interface, so write it for a new colleague. Compare:

```text
Bad:  get_data(id): Gets data.
Good: get_order_status(order_id): Look up an order by its numeric order ID
      (e.g. '1001'): status, item, total and dates.
```

The first leaves the model guessing what "data" means, and which id. The second says what it's for, shows the format, and says what comes back.

Anthropic's guide to [writing tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) adds habits like these:

- **Build a few tools for important jobs**, rather than wrapping every API. A `search_logs` beats a `read_logs` that returns everything.
- **Use clear names**, such as `user_id` rather than `user`.
- **Return what's useful**, such as a name rather than an internal id.
- **Keep results small**, with filtering and sensible limits.
- **Make errors helpful**, so the model can correct itself.

## How ShopHelper does it

| Tool | Does | Risk | Where it runs |
| --- | --- | --- | --- |
| `get_order_status` | Reads one order | Read-only | MCP server |
| `search_policy` | Searches the policy documents | Read-only | MCP server |
| `request_refund` | Asks for a refund | **Moves money** | A graph node |

The read tool shows three habits:

```python file=src/shophelper/agent/tools.py
def get_order_status(order_id: str) -> dict[str, Any]:
clean_id = order_id.strip().lstrip("#")
...
order = get_order_repo().get_for_owner(clean_id, user_id)
...
return order or {"error": f"No order found with id {order_id}"}
```

- **Clean the input.** `lstrip("#")` handles the model passing `#1002`. Models are inconsistent.
- **Return errors as data.** `{"error": ...}` goes back to the model, which can tell the customer. An exception would crash the turn.
- **Keep identity out.** `user_id` isn't an argument. The model chooses only `order_id`, and who's asking comes from elsewhere. [Accounts and isolation](../06-building-the-app/07-accounts-and-isolation.md) explains why.

### Why `request_refund` is different

Look at how it's defined:

```python file=src/shophelper/agent/graph.py
def request_refund(order_id: str, amount: float, reason: str) -> str:
"""Request a refund for a delivered order. A human support agent must approve it."""
raise RuntimeError("Handled by the refund_approval node, never executed directly")
```

The body never runs. It exists only so the model can *see* the tool. When the model asks for it, the graph sends the request to a node that enforces the rules in code. It isn't on the MCP server at all, because any client can reach that.

So the model has no path to money. Even a fully jailbroken model can only *ask*, and the code checks and a person still stand in the way.

### When things go wrong

| Situation | Handling |
| --- | --- |
| Order doesn't exist | The tool returns `{"error": ...}`, and the model says so |
| Tool throws an exception | `run_tool` returns the error to the model |
| Model invents a tool name | `run_tool` replies "Unknown tool" |
| Model loops forever | `recursion_limit` stops it, and the customer gets a polite message |

## In the market

Checked on 2026-11-06.

Tools can be defined in your code, as here, or shared through a protocol. [MCP](../04-mcp/01-mcp.md) is the common standard for that, and it's the next stage.

As tool lists grow, models choose less well, and the descriptions use up the context. So some platforms load tools on demand. Anthropic offers a [tool search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) for working with thousands of tools.

## Try it

1. Open **How it works**, then **Tools**, and read the descriptions as if you were the model.
2. Ask "Where is order 9999?". In the trace, the tool *succeeds* and returns an error object. The model reads it and tells you.
3. Sign in as Arjun, and ask for a refund on order 1004. The code refuses, because it's outside the 30-day window. No person was bothered, and the model explains why.
4. Edit a tool's docstring in [server.py](../../../src/shophelper/mcp/server.py) to something vague, like "Gets data". Save, run `docker compose restart mcp api`, and see how the model behaves. Then change it back.

## Interview questions

### How do you decide what tools to give an agent?

**Strong answer:** I start from the jobs it must do, not the APIs I have. A few well-described tools beat many narrow ones, because the model chooses better. I separate reading from writing: reads can be generous, writes need checks. And I keep arguments minimal: the model picks an order id, but never who the user is.

**Follow-up:** Your API has 200 endpoints. What do you do?

### How would you let an agent take a risky action safely?

**Strong answer:** The model should only be able to request it. In my project `request_refund` is visible to the model, but its body never runs. The request goes to a graph node that checks the rules in code, and then a human approves. It isn't on the MCP server, since any client can reach that. So a jailbroken model can only ask, and it still can't move money.

**Follow-up:** What if the approval step becomes a bottleneck?

### A tool fails halfway through a turn. What should happen?

**Strong answer:** The agent shouldn't crash. I return the error to the model as data, so it can try again or explain. Errors should say what went wrong and how to fix it. I'd add limits so it can't retry forever, and for a write I'd make sure a retry can't do the action twice.

**Follow-up:** How do you make a write safe to retry?

## Check yourself

### Why does `request_refund` have a body that never runs?

- [x] It exists so the model can see the tool, while code does the real work — right: the model can only ask.
- [ ] It isn't finished yet — it's deliberate.
- [ ] To save tokens — the point is safety.

### What should a tool do when an order doesn't exist?

- [ ] Crash, so someone notices — that would end the customer's turn.
- [x] Return an error as data — right: the model can then explain.
- [ ] Return an empty string — the model wouldn't know why.

### Why is `user_id` not an argument to `get_order_status`?

- [ ] It would use too many tokens — it's about safety.
- [x] The model could then ask for anyone's data — right: identity must come from the session.
- [ ] The database doesn't need it — it filters by it.
