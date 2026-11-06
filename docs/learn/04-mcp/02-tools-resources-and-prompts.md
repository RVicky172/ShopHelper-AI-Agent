---
title: Tools, resources and prompts
checked: 2026-11-06
---

## What you'll learn

- The three things an MCP server can offer
- Who controls each one
- How to choose between a tool and a resource
- What this project offers, and what it doesn't

## The simple explanation

Most people only think of tools, but an MCP server can offer three kinds of thing. What separates them is **who decides to use it**:

| Offers | What it is | Who decides | Example |
| --- | --- | --- | --- |
| **Tools** | Actions the model can ask for | The model | Look up an order |
| **Resources** | Data, each with a URI | The application | A file, a database schema |
| **Prompts** | Ready-made templates | The user | A "summarise this ticket" command |

Think of a library. A **tool** is asking the librarian to do something: "find me books on chess". A **resource** is a book you pick from the shelf and put on the table. A **prompt** is a printed request form you can fill in.

The MCP spec describes [resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources.md) as application-driven: the host decides how to use them, such as showing a file picker. They share context, rather than doing something.

## An example

Imagine a server for a shop's documents. All three could be useful:

```text
Tool:      search_policy(query)         the model decides to search
Resource:  policy://returns             a person attaches the policy to a chat
Prompt:    /draft-refund-email          a person chooses this from a menu
```

When should something be a tool, and when a resource?

| Question | Tool | Resource |
| --- | --- | --- |
| Should the model choose when? | Yes | No: the app or user does |
| Takes arguments that vary? | Usually | Fixed URI, or a template |
| Does something, or searches? | Yes | No: it's data to read |

A search has to be a tool, because the query varies and the model needs to decide. A fixed document that a person might attach suits a resource.

## How ShopHelper does it

This project uses only tools. Here's what the server really reports, measured against the running server:

```text
tools/list      get_order_status, search_policy
resources/list  []
prompts/list    []
```

The server still announces all three capabilities when a client connects, because FastMCP does that by default. They're simply empty.

That fits the job. An agent answering customers needs the model to decide what to look up, so tools are right. There's no person picking files.

Tools here also return structured data as well as text, as this real reply shows:

```json
{"content": [{"type": "text", "text": "{\n  \"error\": \"No order found with id 1001\"\n}"}],
 "structuredContent": {"error": "No order found with id 1001"},
 "isError": false}
```

Notice `isError: false`. The call worked, and the tool's *answer* was an error. A failure the model can react to isn't a protocol failure.

**Not in ShopHelper:** resources and prompts. A natural first resource would be the policies, as `policy://returns`, for a person using a desktop MCP client.

## In the market

Checked on 2026-11-06.

Not every client supports everything. Many clients focus on tools, so tools are the safe choice if you want the widest reach. Check the client you're targeting.

The spec also keeps growing through optional extensions, such as [Tasks and MCP Apps](https://blog.modelcontextprotocol.io/posts/2026-07-28/), and some older features are now deprecated: Roots, Sampling and Logging keep working for at least 12 months, but new code shouldn't adopt them.

## Try it

1. Sign in, open **How it works**, then **Tools**.
2. Find which tools say `via mcp`, and which says `via graph node (never MCP)`.
3. Ask yourself: why must `request_refund` not be on the server? [Designing tools](../03-agents/03-tools.md) has the answer.

## Interview questions

### What can an MCP server expose?

**Strong answer:** Tools, resources and prompts, and what separates them is who's in control. The model decides when to call a tool, the application decides how to use a resource, and the user chooses a prompt. In my project I only use tools, because the agent has to decide what to look up. If people used it from a desktop client, I'd add the policies as resources.

**Follow-up:** Why not make everything a tool?

### Should a database schema be a tool or a resource?

**Strong answer:** Probably a resource: it's fixed context that the app can supply when it's relevant, and nothing happens when it's read. A query against that database would be a tool, because the arguments vary and the model decides when to run it. Though if the client I'm targeting doesn't support resources, I'd expose it as a tool.

**Follow-up:** What are the risks of a tool that runs SQL?

## Check yourself

### Who decides when a tool is used?

- [x] The model — right: resources are the application's choice, and prompts the user's.
- [ ] The user, every time — the model asks for tools by itself.
- [ ] The MCP server — it only responds.

### What does ShopHelper's server offer?

- [ ] Tools, resources and prompts — resources and prompts are empty.
- [x] Only tools — right: the agent has to decide what to look up.
- [ ] Only resources — it offers two tools.

### A tool returns `{"error": ...}` with `isError: false`. What does that mean?

- [ ] The server crashed — the call worked.
- [x] The call worked, and the tool's answer was an error — right: the model can react to it.
- [ ] The protocol failed — it behaved normally.
