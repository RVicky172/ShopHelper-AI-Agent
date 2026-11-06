---
title: Eval tools in the market
checked: 2026-11-06
---

## What you'll learn

- What eval tools add over a plain test runner
- The main kinds of tool
- What ShopHelper uses, and what it's missing
- How to choose one

## The simple explanation

You can run evals with a test framework and a file of cases. That's what this project does. So what do eval tools add?

Think of keeping accounts. A notebook works when you're small. As you grow, you want history, charts, and something your accountant can open. A spreadsheet or accounting system doesn't make the sums any truer. It makes them easier to track and share.

Tools tend to do some of these jobs:

| Job | Means |
| --- | --- |
| **Run** | Send cases through your system |
| **Score** | Ready-made metrics and judges |
| **Compare** | This run against the last, side by side |
| **Trace** | See each step of a real conversation |
| **Collect** | Turn real traffic into new cases |
| **Share** | Let non-engineers review and label |

They fall into three rough groups: **libraries** you run in your tests, **platforms** that store results and traces, and **red-team tools** that attack your app.

## An example

Say a team wants to change a prompt. Here's the same task, two ways.

**With a test runner, as in this project:**

1. Change the prompt.
2. Run `scripts/evals_local.sh`.
3. Read `evals/report.json`, and compare with the last one by hand.

**With a platform:**

1. Change the prompt.
2. Run the eval.
3. Open a page showing both runs, side by side, with each changed case highlighted.
4. Share the link, so a product manager can read the differences.

The score is no more accurate either way. The second is easier when several people need to see it, or when you run it often. With one builder and 37 cases, that's not worth a new dependency yet.

## How ShopHelper does it

Everything is plain pytest:

| Part | How |
| --- | --- |
| Cases | `evals/golden_cases.yaml` |
| Runner | `evals/test_golden.py` |
| Judge | `evals/judge.py`, about 60 lines |
| Rates | `evals/measure_policy.py` |
| Report | `evals/report.json` |

The report is written when the run ends:

```python file=evals/conftest.py
print(f"\nEVAL SUMMARY: {passed}/{len(RESULTS)} passed, "
```

Why build it? This project exists to teach, so seeing the whole thing matters. It's also small, and pytest gives selection by name for free. There's nothing to pay for, and no data leaves the machine.

What's missing:

- No history: each run overwrites the last report.
- No side-by-side comparison.
- No way for a non-engineer to label anything.
- No link from production traffic to new cases.

**LangSmith** is the exception. Tracing is built into LangGraph's world, and this project has settings for it, off by default for local work:

```bash file=scripts/evals_local.sh
export LANGSMITH_TRACING=false
```

## In the market

Checked on 2026-11-06. Most comparisons online come from the vendors themselves, so treat rankings with care. Descriptions here are what each project says of itself.

| Tool | Group | Known for |
| --- | --- | --- |
| [DeepEval](https://deepeval.com/docs/getting-started) | Library | Pytest-style tests for LLM apps |
| [Ragas](https://docs.ragas.io/en/latest/concepts/metrics/) | Library | RAG metrics |
| [Inspect](https://inspect.aisi.org.uk/) | Library | Evals from the UK AI Security Institute |
| [Promptfoo](https://www.promptfoo.dev/docs/intro/) | Library and red team | Config-file evals, and attack testing |
| [LangSmith](https://docs.langchain.com/langsmith/evaluation) | Platform | Tracing and evals, close to LangChain |
| [Langfuse](https://langfuse.com/docs) | Platform | Open source, and you can host it yourself |
| [Braintrust](https://www.braintrust.dev/docs) | Platform | Hosted evals and comparison |

**This market moves.** [OpenAI agreed to buy Promptfoo](https://siliconangle.com/?p=733680) in March 2026, and reports say it stays open source. So check that a tool is alive and independent before relying on it. One source called Ragas dormant, and we couldn't confirm that, so look at its recent releases yourself.

**How to choose:**

1. **Start with your test runner**, until people need to see results together.
2. **Need RAG metrics quickly?** Try Ragas or DeepEval, and check their judges against your labels.
3. **Need tracing and history?** Pick a platform. Host it yourself if your data can't leave.
4. **Have sensitive data?** Check what's sent to any hosted service, because traces contain customer messages.

**Avoid lock-in by keeping your cases in your own files.** Cases and labels are what's valuable, and they're the slow part to build. A plain file moves to any tool, as YAML did here.

A metric from a library is a judge someone else wrote. It needs [the same checking as your own](06-llm-judges.md).

## Try it

1. Open `evals/conftest.py`, and read what goes into the report.
2. Add one more number to the summary, such as the slowest case's `latency_ms`. It's a few lines, which shows how far plain pytest can go.
3. Read the Langfuse or DeepEval quick start, and list what you'd have to change in this project to use it.

## Interview questions

### Which eval tool would you use?

**Strong answer:** It depends on the team. For one person or a small set, plain pytest with cases in a file goes a long way, which is what I built, so I could see every part. When several people need to compare runs, or we need history and traces, I'd add a platform: Langfuse if we need to host it ourselves, or LangSmith if we're already in LangChain. I'd keep the cases in our own files either way, so we can change tools.

**Follow-up:** What would make you switch from your own runner?

### What are the risks of a hosted eval or tracing tool?

**Strong answer:** Traces contain customer messages and maybe personal data, so that data leaves your system. I'd check where it's stored, how long it's kept, and what gets masked first, or host it myself. The other risks are lock-in and the vendor changing, and this market moves quickly. And built-in metrics are judges someone else wrote, so they need checking against my own labels.

**Follow-up:** How would you mask data before sending it?

## Check yourself

### What do eval platforms mainly add?

- [ ] More accurate scores — the scores aren't truer.
- [x] History, comparison and sharing — right: easier to track, for more people.
- [ ] A better model — they don't change your model.

### What's the valuable, portable part of your evals?

- [x] Your cases and labels — right: they're the slow part to build.
- [ ] The vendor's dashboard — that doesn't move with you.
- [ ] The chart colours — not quite.

### What should you check before sending traces to a hosted tool?

- [ ] That it has a dark mode — not a priority.
- [ ] Nothing: traces are harmless — they contain customer messages.
- [x] What data leaves, and where it's kept — right: traces can hold private details.
