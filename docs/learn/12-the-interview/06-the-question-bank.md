---
title: The question bank
checked: 2026-11-07
---

## What you'll learn

- How to practise questions so the answers stick
- How to use the bank to find your weak spots
- Questions nearly every interview asks, which no technical lesson covers

## The simple explanation

This page gathers every interview question in the course into one place, so you can search them and practise in any order.

Think of learning a language. Reading a phrasebook feels productive, but you only learn when you have to say the words with nobody to help. The same goes here. Reading a strong answer feels like knowing it. It isn't, until you've said it yourself.

So don't read this page from the top. Use it as a gym: pick a few, work hard on them, and come back another day.

## An example

Here's a practice session of about 20 minutes. It's our suggestion, not research.

1. **Choose.** Pick a stage you're weak on, or search for a word from a job advert.
2. **Answer aloud.** Take one question and give yourself two minutes, before opening anything.
3. **Compare.** Open the strong answer. Note what you left out, not how the words differ. Your own words are better.
4. **Face the follow-up.** Answer it aloud too. It's where interviewers really find out what you know.
5. **Go back.** If you got stuck, the answer links to its lesson. Read that part, then try again tomorrow.

Do five questions, not fifty. Coming back on a later day does more than one long session. Keep a short list of the questions you missed, and start with those next time.

Don't memorise the strong answers. They're written about this project, and they'd sound rehearsed from anyone else. Learn the points, then say them your way, using what you've really done. If an answer describes something you didn't do, change it.

**Choosing what to practise from a job advert:**

| If the advert says | Filter to |
| --- | --- |
| Agents, tools, orchestration | Agents, MCP |
| RAG, search, knowledge base | RAG |
| Evaluation, quality | Evals and testing |
| LLM security, guardrails | Security |
| AWS, deployment, CI/CD | Cloud deployment |
| Production, monitoring | Running in production |

## All the questions

On the website, every question in the course appears below, with a filter for each stage and a search box. On GitHub, find them under **Interview questions** in each lesson.

## How ShopHelper does it

The bank holds no copies. Each question lives in its own lesson, and the bank is built from those lessons. This function reads one:

```typescript file=web/src/features/learn/bankQuestions.ts
export function questionsIn(raw: string, where: Source): BankQuestion[] {
```

So a fixed answer changes everywhere at once, and adding a lesson adds its questions with no other work. A test checks the course holds at least 60 questions, drawn from every stage.

The questions load only when you open this page, in their own file, so the shop and other lessons don't pay for them. Answers turn into formatted text only when you open them, because doing that for every answer at once would be wasted work.

It's a small example of a good habit: one home for each fact, as with the returns policy and the agent's copy of it.

## Try it

1. Choose **RAG** in the Stage box above. How many questions are there?
2. Set the stage back to **All stages**, and search for "refund". Open one, and answer it aloud before reading the strong answer.
3. Open the lesson it came from, using the link under the answer.
4. Paste a real job advert into a note, and pick its three main skills. Search for each here, and practise one question for each.
5. Count the questions per stage: `grep -c '^\*\*Strong answer:\*\*' docs/learn/*/*.md | sed -E 's#docs/learn/([^/]+)/.*:#\1 #' | awk '{s[$1]+=$2} END {for (k in s) print k, s[k]}' | sort`.

## Interview questions

These are the questions nearly every interview asks. No technical lesson covers them.

### Why do you want to be an AI engineer?

**Strong answer:** I like building things that work for real people, and models changed what's possible. What pulled me in was how different the engineering is: your main component sometimes gets things wrong, so testing and safety become the real work. I built a whole support agent to find out if I liked that part, and I did. Evals and failure cases were the most interesting bits.

**Follow-up:** What part of the job do you expect to dislike?

### What questions do you have for us?

**Strong answer:** Always have some, because this is an interview in both directions. How do you test AI features before they ship? What happened the last time a model change affected users? Who decides when something is good enough to release? How much of the work is new features, and how much keeps existing ones healthy? These show how you think, and the answers tell you how seriously they take quality.

**Follow-up:** What answer would make you hesitate to join?

### Where do you think AI engineering is going?

**Strong answer:** I'd be careful predicting, because the tools change every few months. Some things seem likely to last: models will keep being imperfect, so evals, safety and good design stay valuable. Agents are taking more real actions, so the question of who's accountable matters more. The details change fast, so I focus on the fundamentals, and I check the date on what I read.

**Follow-up:** What's something popular right now that you're sceptical of?

## Check yourself

### What's the best way to use the bank?

- [ ] Read it from top to bottom — reading feels like knowing, but it isn't.
- [x] Answer a few aloud, then compare — right: saying it is what makes it stick.
- [ ] Memorise the strong answers — they'd sound rehearsed, and they're about this project.

### You compare your answer with the strong one. What should you note?

- [ ] Every word that differs — your own words are better.
- [x] The points you left out — right: learn the points, and say them your way.
- [ ] Nothing, if it felt right — feeling right isn't the test.

### A strong answer describes something you didn't do. What now?

- [ ] Say it anyway — the first follow-up will expose it.
- [ ] Skip the question — you'd still be asked it.
- [x] Change it to what you really did — right: only say what's true.
