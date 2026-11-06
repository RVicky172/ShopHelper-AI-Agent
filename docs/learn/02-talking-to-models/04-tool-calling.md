---
title: Tool calling
checked: 2026-11-06
---

## What you'll learn

- What really happens when a model "uses a tool"
- What a tool definition contains
- The exact messages that go back and forth
- Why the description matters so much

## The simple explanation

A model only produces text. It can't call a function. So how can it look up an order?

It asks. You tell the model which tools exist. If it needs one, it replies with a structured request instead of an answer. Your code runs the function, and sends the result back in a new call.

Think of a manager with an assistant. The manager can't reach the filing cabinet, but can write "please fetch order 1002" on a slip. The assistant fetches it and hands it back, and the manager writes the reply. The manager never touches the cabinet.

A tool definition has three parts:

| Part | Purpose |
| --- | --- |
| **Name** | What the model asks for |
| **Description** | How the model decides when to use it |
| **Parameters** | The information it must supply, as a schema |

The model never sees your code, only this description. So the description is a prompt. A vague one means wrong tool choices.

## An example

This is a real exchange with this project's local model, trimmed for space.

**You send** the question, plus the tool:

```json
{
  "messages": [
    {"role": "system", "content": "You are a support agent. Use tools for order questions."},
    {"role": "user", "content": "Where is order 1002?"}
  ],
  "tools": [{"type": "function", "function": {
    "name": "get_order_status",
    "description": "Look up an order by its id.",
    "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}
  }}]
}
```

**The model replies** with no text, and a request:

```json
{
  "finish_reason": "tool_calls",
  "message": {
    "content": "",
    "tool_calls": [{
      "id": "CiOfLFN2nR3kWEG7brJjefYRtOZEOTRf",
      "function": {"name": "get_order_status", "arguments": "{\"order_id\":\"1002\"}"}
    }]
  }
}
```

Nothing has happened yet. It's only a request. `finish_reason` tells your code what to do next.

**You run the function**, then send everything back, adding the result with a matching id:

```json
{"role": "tool", "tool_call_id": "CiOfLFN2nR3kWEG7brJjefYRtOZEOTRf", "content": "{\"status\": \"shipped\", \"item\": \"Mechanical Keyboard\"}"}
```

**The model answers:** "Your order #1002, which includes a Mechanical Keyboard, has been shipped."

But look what else it wrote: "You can track its progress using the provided tracking information." There was no tracking information. Even a good reply can include a small invention, which is why tool results and answers both need checking.

Tools also cost tokens. That first call used 172 input tokens, mostly the tool's description. And asked "Hello there", the model simply replied, because no tool was needed. Using a tool is its choice.

## How ShopHelper does it

The description comes straight from the function's docstring:

```python file=src/shophelper/mcp/server.py
def get_order_status(order_id: str, ctx: Context) -> dict[str, Any]:
"""Look up an order by its numeric order ID (e.g. '1001'): status, item, total and dates."""
```

When a tool fails, the error goes back to the model as data, so it can explain, rather than crashing the turn:

```python file=src/shophelper/agent/graph.py
return ToolMessage(f"Tool error: {exc}", tool_call_id=call["id"], status="error")
```

And notice `ctx` above. It's kept out of what the model sees, so the model can't pass a different customer's identity. The arguments come from the model, so treat them as untrusted input, just like a form on a website. `get_order_status` doesn't trust the id to decide whose order it is.

[Tools](../03-agents/03-tools.md) looks at this project's tools in more depth.

## In the market

Checked on 2026-11-06. From Anthropic's [tool use docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview).

Every major provider works this way, with small differences in the format. With Claude, the reply has `stop_reason: "tool_use"` and a `tool_use` block.

| Kind of tool | Where it runs |
| --- | --- |
| Client tools | Your code. All of ShopHelper's tools are these |
| Server tools | The provider's systems, such as web search |

Useful options:

- **`tool_choice`** can force a tool rather than leaving it to the model.
- **Strict mode** guarantees the arguments match the schema.
- **Parallel calls** let a model ask for several tools at once.

By default the model decides. Anthropic's docs note you can steer that from the system prompt, and that `tool_choice` is how you require a call. This project found the limits of steering by prompt, and [wrote the call in code instead](../03-agents/02-the-agent-loop.md).

## Try it

1. Sign in, open **How it works**, then **Tools**.
2. Read the description of each tool. That's all the model knows about it.
3. Open **Step trace**, and click the **Tool call** example.
4. In the trace, find the tool's arguments and its result.

## Interview questions

### How does tool calling actually work?

**Strong answer:** The model never runs anything. I send tool definitions with the request. If it needs one, it replies with a structured call: a name and arguments. My code validates and runs that, then sends the result back in a new request, linked by an id, and the model continues. So it's a loop of normal API calls. The model decides, and my code acts.

**Follow-up:** What do you do if the arguments are invalid?

### Your agent keeps picking the wrong tool. What do you do?

**Strong answer:** I'd start with the descriptions, because that's all the model sees. I'd check that they're specific, say when to use each tool, and don't overlap. Too many similar tools also confuses it, so I might merge some. Then I'd measure with test cases that check which tool was chosen. If one case must always use a tool, I'd force it with `tool_choice` or in code.

**Follow-up:** How many tools is too many?

### What are the security risks of tool calling?

**Strong answer:** The arguments come from the model, and the model can be influenced by a customer or by retrieved text. So I treat them as untrusted. I use least privilege, so tools only do what's needed. Identity comes from the session, never from an argument. Anything that changes data needs a separate check, and in my project refunds need human approval and aren't on the MCP server at all.

**Follow-up:** What if a tool's result contains instructions?

## Check yourself

### Who runs a tool?

- [ ] The model — it only asks.
- [x] Your code — right: then it sends the result back.
- [ ] Always the provider — only for server tools, and ShopHelper has none.

### What does the model see of a tool?

- [ ] Its source code — it never sees your code.
- [x] Its name, description and parameters — right: so the description is really a prompt.
- [ ] Your database — only what a tool returns.

### Why treat a tool's arguments as untrusted?

- [x] The model can be influenced by what it reads — right: treat them like input from a web form.
- [ ] Models always make mistakes with JSON — they rarely do on simple cases.
- [ ] They're encrypted — they aren't.
