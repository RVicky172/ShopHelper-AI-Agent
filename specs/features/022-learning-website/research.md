# 022 — Research Notes

Researched on 2026-11-06. This shaped the course in `spec.md`, and it's a starting point for lessons, not their content: each lesson re-checks its
own facts (AC-12).

**How far to trust this.** Most market writing is by vendors or course sellers. Primary sources are marked **[primary]**. Anything else is
direction, not fact.

## The role

- "AI engineer" means building with models, not training them. Roadmaps from course sellers still lead with ML theory, which interview guides
  don't support.
- In 3,449 postings on one job board, May 2026: Python 71%, LLMs 66%, RAG 40%, AWS 37%, Azure 33%, monitoring 31%, Google Cloud 25%, CI/CD 24%,
  observability 19%, vector databases 18%, Docker 18%, Kubernetes 16%. The publisher sells interview prep, and this is one board. It argues RAG
  and LangChain are now baseline, and that operations skills are what stand out.
  [Analysis](https://dev.to/gnana_6392e836fd500a957dc/ai-engineer-skills-companies-want-in-2026-3449-posting-analysis-5f9l)
- **What it means for the course:** evals, monitoring and production stages get as much space as RAG and agents.

## Interviews

- A usual loop: recruiter, technical screen, 1 or 2 deep rounds on RAG and system design, behavioural. Prep sites say over 60% is about
  generative AI. [Upenn careers](https://careerservices.upenn.edu/blog/2026/06/25/45-ai-engineer-interview-questions-answers-2026-guide/),
  [Exponent](https://www.tryexponent.com/blog/ai-engineer-interview-questions),
  [PracHub](https://prachub.com/resources/ai-engineer-interview-questions-2026-rag-agents-evals-and-production-systems)
- "Design a RAG chatbot" is reported as the warm-up. Harder rounds cover evaluation, failure handling, cost, and debugging a wrong answer when
  the right document exists.
- _2026-11-07: reading these sources again, none gives a share of generative AI questions or names "design a RAG chatbot" as a warm-up, and Exponent is now
  Aced. Stage 12 doesn't repeat either claim, and says so._
- **What it means for the course:** debugging scenarios and system design walkthroughs, not only definitions.

## AI-assisted interviews

- Policies differ, so "companies ask you to use Claude Code" is true of some, not all.
- Anthropic's own rule: no AI in take-homes or live interviews **unless it says so**. Prep is encouraged. **[primary]**
  [Candidate guidance](https://www.anthropic.com/candidate-ai-guidance)
- Codility offers Claude Code inside its interview environment as a preview, and interviewers can review prompts. **[primary]**
  [Codility](https://support.codility.com/hc/en-us/articles/49075175492497-Claude-Code).
  CodeSignal's Agentic Interviewing assesses how candidates prompt, review and validate. **[primary]**
  [CodeSignal](https://support.codesignal.com/hc/en-us/articles/38841637349015-How-can-I-use-Agentic-Interviewing-in-my-recruiting-process)
- Reported rubrics reward breaking the problem down, directing the tool, and checking its output, rather than speed.
  [Guide](https://pawankjha.substack.com/p/ai-assisted-coding-interviews-a-complete)
- _2026-11-07: the Substack guide is paywalled, so its rubric claim couldn't be checked. Canva's own posts replace it: [its rule](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/),
  and [what its interviewers assess](https://www.canva.dev/blog/engineering/ai-interview-success/). Codility's and CodeSignal's help pages returned 403._
- **What it means for the course:** practise verifying and explaining, and always ask the recruiter what's allowed (AC-18).

## Claude Code **[primary]**

- Explore, plan, code, commit. Give Claude a way to check its own work, such as tests. _2026-11-07: the page no longer uses this framing. It now
  says: tell Claude what it can't see, give it a check to run, and enforce the rules that can't have exceptions. Stage 11 follows the new wording._
- Keep `CLAUDE.md` short, around 200 lines, with facts it can't work out. Use hooks for rules with no exceptions, and skills for repeatable
  procedures. Subagents suit parallel work and independent review.
  [Best practices](https://code.claude.com/docs/en/best-practices), [Features](https://code.claude.com/docs/en/features-overview)

## Spec-driven development

- Main options: GitHub Spec Kit, Kiro, and custom Claude Code workflows like this project's. Anthropic ships no single SDD product. The trade-off
  is depth against portability. [Comparison](https://glukhov.org/ai-devtools/ai-coding-assistants/spec-kit-vs-kiro-vs-claude-code/)

## Agents **[primary]**

- Workflows follow fixed code paths. Agents direct their own steps. Start with the simplest thing that works. Patterns: prompt chaining, routing,
  parallelization, orchestrator-workers, evaluator-optimizer.
  [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Multi-agent: Anthropic's research system beat a single agent by 90.2% on its own eval, but used about 15 times the tokens of a chat, and agents about
  4 times. It's a poor fit for tasks with many dependencies, which covers most coding.
  [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- Frameworks: LangGraph for durable stateful flows, CrewAI for role-based teams, provider SDKs such as the OpenAI Agents SDK and Claude Agent SDK for
  lighter work. AutoGen is reported to be in maintenance mode. Vendor rankings conflict.
  [Comparison](https://www.morphllm.com/ai-agent-framework)

## MCP **[primary]**

- The current revision is **2026-07-28**. Requests are stateless: the initialize handshake and `Mcp-Session-Id` are gone, Streamable HTTP needs
  `Mcp-Method` and `Mcp-Name` headers, the old HTTP+SSE transport is deprecated, and Dynamic Client Registration gives way to client metadata
  documents. [Release](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- **To check:** `docs/learn/03-mcp.md` and the SDK version here may describe an older revision. Some spec pages still show 2025-11-25.

## RAG

- Core metrics: context recall and precision, faithfulness, answer relevance.
- One study found contextual retrieval with rank fusion and reranking most accurate but costly, and late chunking cheaper but variable. Reranking
  was essential, and fixed and semantic chunking differed little without context. [Paper](https://arxiv.org/html/2504.19754v1)
- This project found the same kind of problem itself: a chunk arrived without the definition it depended on (D-019).
- Vector databases: pgvector if you already run Postgres, Qdrant for control, Pinecone for low operations, Weaviate for hybrid search. The benchmarks
  and prices conflict and come from blogs. [Comparison](https://alexcloudstar.com/blog/vector-database-comparison-2026/). Not covered well: S3 Vectors.

## Evals

- Grade outcomes, not fixed steps, because valid agent paths vary. Read the transcripts. Start with about 20 realistic cases. **[primary]**
  [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
  [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Golden sets: build them from real traces, include unanswerable inputs, keep them small and versioned, and label by hand before calibrating a
  judge. About 20 to 50 examples can show where a judge disagrees. Binary labels are easier to diagnose, and a check a regex can do needs no model.
  [Arize](https://arize.com/docs/ax/cookbooks/evaluate/align-llm-evals-with-human-judgment),
  [OneUptime](https://oneuptime.com/blog/post/2026-08-31-build-golden-evaluation-dataset-production-failures/markdown)
- Judges have position and verbosity bias, per Zheng and colleagues' MT-Bench paper.
- Tools: DeepEval suits pytest and CI, Ragas gives RAG metrics, Braintrust is hosted, Langfuse can be self-hosted. Rankings here are mostly vendors'.
  One source calls Ragas dormant: unverified. OpenAI's hosted Evals is reported to close on 2026-11-30.
  [Comparison](https://ecorpit.com/rag-evaluation-tools-ragas-deepeval-braintrust-giskard-2026/)

## Security

- Secondary sources describe a 2026 LLM Top 10. OWASP's own page still showed the 2025 edition on 2026-11-06, so the course quotes that:
  these details are from secondary sources. [Akamai](https://www.akamai.com/blog/ai/owasp-top-10-llm-applications-2026-realistic-security-model)
- A separate OWASP Top 10 for Agentic Applications, December 2025, starts with ASI01 Agent Goal Hijack, then Tool Misuse and Identity and Privilege Abuse.
  **[primary]** [OWASP](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/),
  [Cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
- Prompt injection has no equivalent of a parameterised query, so defences are layered: least-privilege tools, human approval for irreversible actions,
  and checks on input and output. This project's "model asks, code acts" is a real example.

## Deployment and operations

- On AWS: Lambda with API Gateway, ECS Fargate, and AgentCore Runtime. One blog suggests Lambda for short calls and AgentCore for long multi-step agents.
  AgentCore's limits are reported inconsistently, so check AWS's docs. [AWS re:Post](https://repost.aws/articles/AR9fNVsR75Q_KYE19tA9E2HQ/re-invent-2025-build-deploy-and-operate-agentic-architectures-on-aws-serverless)
- Tracing: OpenTelemetry's GenAI conventions are the emerging standard. Sources disagree on whether they're stable, so check the spec. Langfuse and
  Phoenix both accept these traces. [Greptime](https://www.greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)

## How LLMs work

- Prefill reads the whole prompt and is compute-bound. Decode writes one token at a time and is limited by memory bandwidth. The KV cache avoids redoing
  earlier work, and prefix caching reuses shared prompts. Sources were thin on tokenization and attention, so those lessons need primary references.
  [Overview](https://henrygwb.github.io/posts/inference.htm)

## Site options

- Starlight is the common default, Docusaurus suits versioned React docs, VitePress suits Vue, and Fumadocs suits React stacks. None ships a course stepper.
  Several sources sell hosted docs. [Comparison](https://www.pkgpulse.com/guides/docusaurus-vs-vitepress-vs-nextra-vs-starlight-2026)

## Gaps to close while writing

Tokenization and attention, S3 Vectors, AgentCore's current limits, OWASP's exact wording, pass@k against pass^k, and the status of OpenTelemetry's
GenAI conventions.
