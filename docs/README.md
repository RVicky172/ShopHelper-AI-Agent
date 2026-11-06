# ShopHelper docs

ShopHelper is a customer-support AI agent, built to learn how agents work. These docs teach the
ideas using this project's real code. You can run every example on your own machine.

## Start here

1. **[Local setup](local-setup.md):** get everything running with one command.
2. **[Architecture](architecture.md):** the whole system, starting from the simplest picture.
3. **The learning path below:** read it in order. Each chapter builds on the one before it.

## Learning path

| # | Chapter | The question it answers |
| --- | --- | --- |
| 1 | [Agents and the loop](learn/01-agents-and-the-loop.md) | What makes an agent different from a chatbot? |
| 2 | [Tools](learn/02-tools.md) | How does a model that only writes text do anything? |
| 3 | [MCP](learn/03-mcp.md) | Why put tools behind a protocol? |
| 4 | [RAG](learn/04-rag.md) | How does the model answer from documents it was never trained on? |
| 5 | [Memory and human approval](learn/05-memory-and-human-approval.md) | How does an agent remember, and pause for a person? |
| 6 | [Streaming](learn/06-streaming.md) | How do steps and words reach the browser as they happen? |
| 7 | [The React frontend](learn/07-frontend.md) | How does the UI turn a stream into a screen, and a dashboard into a shop? |
| 8 | [Guardrails](learn/08-guardrails.md) | How do we stop bad input and bad output? |
| 9 | [Evals](learn/09-evals.md) | How do you test something that isn't deterministic? |
| 10 | [Local vs AWS](learn/10-local-vs-aws.md) | How does the same code run in both places? |
| 11 | [Accounts and isolation](learn/11-accounts-and-isolation.md) | How do you keep one user's data from another, when a model is involved? |

Every chapter ends with **Try it**, a short exercise using the running app.

## Reference

| Doc | Use it for |
| --- | --- |
| [Runbook](runbook.md) | AWS commands: deploy, operate, tear down |
| [AWS services](aws-services.md) | What each AWS service does here and what it costs |
| [Deployment comparison](deployment-comparison.md) | Lambda vs ECS measurements |
| [Next steps](next-steps.md) | What's left, including moving to AWS |

## How the project is run

| Doc | Use it for |
| --- | --- |
| [Constitution](../specs/constitution.md) | The project's rules, and what "done" means |
| [Memory](../memory/MEMORY.md) | Current state of the project |
| [Learnings](../memory/learnings.md) | Gotchas and non-obvious fixes |
| [Decisions](../memory/decisions.md) | Why each choice was made |
