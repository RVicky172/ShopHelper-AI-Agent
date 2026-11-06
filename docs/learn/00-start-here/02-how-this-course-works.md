---
title: How this course works
checked: 2026-11-06
---

## What you'll learn

- The order of the course, and why it's in that order
- What each part of a lesson is for
- How to get the most from it in the time you have

## The simple explanation

This course is one path. Each stage builds on the one before, so go in order the first time. Later, use it as a reference.

| Stages | What they cover |
| --- | --- |
| 1 to 2 | How models work, and how to talk to them |
| 3 to 5 | Agents, MCP and RAG: the core of the job |
| 6 | Building a real app around them |
| 7 to 8 | Testing and security |
| 9 to 10 | Deploying and running it |
| 11 to 12 | Building with AI tools, and interviews |

The stepper at the top shows where you are, and it remembers your place in this browser. **Continue** on the course page takes you back to your last lesson.

## An example

Every lesson has the same shape, so you always know what's coming:

| Part | Why it's there |
| --- | --- |
| What you'll learn | So you know if this lesson is what you need |
| The simple explanation | The idea in plain words, usually with a comparison |
| An example | One concrete case, before any code |
| How ShopHelper does it | The real code, or a clear "Not in ShopHelper" |
| In the market | Other options, and when to choose them |
| Try it | Something to do in the running app |
| Interview questions | How you'd be asked, with a strong answer |
| Check yourself | A quick test, with feedback on every answer |

Try this with interview questions: read the question, answer it out loud, *then* open the strong answer. Saying it is what makes it stick.

## How ShopHelper does it

Lessons are plain Markdown files in `docs/learn/`, so you can read them on GitHub too. This site reads the same files, so there's only one copy.

The code examples are real. A test fails if a line shown in a lesson no longer exists in that file, so what you read can't quietly drift from the project.

Some lessons cover things this project doesn't have. They say so plainly, under **Not in ShopHelper**. Numbers measured in this project say so, and anything from a vendor is labelled.

## In the market

Checked on 2026-11-06.

This field moves fast. Anything about products or prices shows the date it was checked and links its source, and much market writing comes from vendors selling those products. Good habits:

- Prefer primary sources, such as [Anthropic's guide to building agents](https://www.anthropic.com/engineering/building-effective-agents), over rankings.
- Ask who wrote a comparison, and what they sell.
- Test on your own data before believing a benchmark.

## Try it

1. Open **Learn** in the navbar and find your progress.
2. Press **Mark as done** at the end of this lesson, then look at the stepper and the lesson list.
3. Search the course for "chunking", and open the result.

## Interview questions

### How do you keep up with such a fast-moving field?

**Strong answer:** I focus on ideas that last, like the agent loop, retrieval and evals, and treat tools as changeable. For news I go to primary sources: official docs, specs and engineering blogs. I'm careful with comparison articles, because most are written by vendors. And I test a claim on my own project before trusting it.

**Follow-up:** What's something you learned recently that changed how you work?

### How do you learn a new technology quickly?

**Strong answer:** I build the smallest real thing with it. On this project I wrote the agent loop by hand before using a framework, so I knew what the framework was doing for me. Then I break it on purpose, because seeing a test fail teaches more than seeing it pass.

**Follow-up:** Tell me about something that was harder than you expected.

## Check yourself

### What's the best way to use the interview questions?

- [ ] Read the strong answer several times — reading feels productive, but it isn't practice.
- [x] Answer out loud before opening it — right: saying it is what you'll have to do in the room.
- [ ] Learn the answers word for word — interviewers follow up, so you need the idea.

### What does "Not in ShopHelper" mean on a lesson?

- [x] The topic matters, but this project hasn't built it — right: you still learn it, knowing you can't run it here.
- [ ] You can skip that lesson — no: those topics still come up in the job.
- [ ] It's out of date — dates are shown separately.
