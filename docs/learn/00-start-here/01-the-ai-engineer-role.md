---
title: The AI engineer role
checked: 2026-11-06
---

## What you'll learn

- What an AI engineer actually does
- How the role differs from data science and ML engineering
- Which skills job postings ask for
- What seems to set candidates apart

## The simple explanation

An AI engineer builds products on top of AI models. Mostly they don't train those models. They use models that already exist, and do the hard work of making them useful, safe and reliable.

Think of an architect and a brick factory. The factory makes bricks. The architect doesn't, but has to know what bricks can bear, and how to build something that stands up. AI engineers are the architects. Companies like Anthropic make the models.

It's mostly software engineering, with one big difference: your main component doesn't always give the same answer. So much of the job is handling that, by measuring quality, adding safety checks, and designing for failure.

| Role | Main question | Main work |
| --- | --- | --- |
| Data scientist | What does this data tell us? | Analysis, statistics, experiments |
| ML engineer | How do we train and serve this model? | Training pipelines, model serving |
| **AI engineer** | **How do we build a reliable product with models?** | **Agents, RAG, evals, integration, production** |

The lines blur, and titles vary by company.

## An example

A company wants a support assistant that answers from its own policies and can start refunds. An AI engineer would:

1. Choose a model, based on quality, speed and cost
2. Connect it to the policies, using RAG
3. Give it tools, such as looking up an order
4. Make sure refunds need a human's approval
5. Build a test set, to measure whether answers are right
6. Add defences against attacks like prompt injection
7. Deploy it, watch how it behaves, and fix what goes wrong

Notice how little of that list is about the model itself. That list is also this project.

## How ShopHelper does it

ShopHelper is that assistant, built to learn from:

| The job | In this project |
| --- | --- |
| Agents and tools | A LangGraph agent with tools for orders and policies |
| RAG | Policy search with Postgres and pgvector |
| Human approval | Refunds wait for a staff member |
| Evals | 37 test conversations, including attacks |
| Security | Guardrails, and per-user data isolation |
| Deployment | Docker locally, Terraform for AWS |

Every stage of this course uses it as the example. By the end, you can explain each part because you've read and run it.

## In the market

Checked on 2026-11-06.

One [analysis of 3,449 AI engineer postings](https://dev.to/gnana_6392e836fd500a957dc/ai-engineer-skills-companies-want-in-2026-3449-posting-analysis-5f9l), from May 2026, gives a rough picture:

| Skill | Share of postings |
| --- | --- |
| Python | 71% |
| LLMs | 66% |
| RAG | 40% |
| AWS | 37% |
| Azure | 33% |
| Monitoring | 31% |
| Google Cloud | 25% |
| CI/CD | 24% |
| Observability | 19% |
| Vector databases | 18% |
| Docker | 18% |

**Read this with care.** It covers one job board, whose owner sells interview preparation. Treat it as a direction, and read real postings from companies you want to join.

Its argument is worth noting, though: RAG and frameworks are now expected, and what stands out is keeping a system running in production. That's why this course gives evals, security and monitoring as much space as agents.

[One interview guide](https://prachub.com/resources/ai-engineer-interview-questions-2026-rag-agents-evals-and-production-systems) points the same way. Beyond RAG, it lists evaluation, failure handling, debugging by pipeline stage, cost per task, security and operational ownership. It sells preparation too, so again, take it as a direction.

## Interview questions

### What does an AI engineer do that a regular software engineer doesn't?

**Strong answer:** Most of it is software engineering. The difference is building on a component that isn't deterministic: the same input can give a different output. So I need evals instead of only unit tests, guardrails against bad input and output, and designs that assume the model will sometimes be wrong. In my project, anything that must always hold, like a refund needing human approval, is enforced in code, not left to the model.

**Follow-up:** Give an example of a bug only an AI system could have.

### Tell me about a project you've built.

**Strong answer:** I built ShopHelper, a customer-support agent for a small shop, to learn how these systems really work. It's a LangGraph agent with RAG over policy documents, tools behind MCP, human approval for refunds, and per-user data isolation, tested by 37 eval conversations including attacks. It runs locally with Docker, and has Terraform for AWS. One thing I learned: a prompt rule can pass tests and still fail. Measuring across wordings showed only half of one kind of question searched the policy, so I moved that decision into code.

**Follow-up:** What would you do differently?

## Check yourself

### What does an AI engineer mostly do?

- [ ] Train new models from scratch — that's research and ML engineering work, and most products don't need it.
- [x] Build reliable products on existing models — right: agents, RAG, evals and production work.
- [ ] Analyse company data — that's closer to data science.

### Why does this course spend so long on evals and monitoring?

- [ ] They're the easiest topics — they aren't: measuring a system that varies is hard.
- [x] Keeping a system working well is what stands out — right: building a demo is the expected part.
- [ ] Every posting requires them — monitoring appears in about 31% of postings in that analysis, so no.
