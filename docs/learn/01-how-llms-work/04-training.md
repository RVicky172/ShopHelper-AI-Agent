---
title: How models are trained
checked: 2026-11-06
---

## What you'll learn

- The stages that turn raw text into a helpful assistant
- Why a model has a knowledge cutoff
- What fine-tuning is, and why you rarely need it
- Why a smaller, well-trained model can beat a bigger one

## The simple explanation

A model isn't programmed with facts or rules. It learns by adjusting billions of numbers, its **parameters**, until it gets good at predicting text.

It happens in stages. Think of training a doctor.

**Stage 1: pre-training. Reading the whole library.** The model reads an enormous amount of text and repeatedly guesses the next token. Each wrong guess nudges its parameters a little. To predict well, it has to pick up grammar, facts and reasoning patterns. This is by far the most expensive stage. The result knows a lot, but it isn't an assistant. Ask it a question, and it might just continue with more questions, because that's what text often does.

**Stage 2: instruction tuning. Learning to do the job.** People write examples of good answers, and the model trains on those. Now it learns the shape of being helpful: a question gets an answer.

**Stage 3: learning from feedback. Being reviewed.** People, or other models, compare answers and pick the better one. The model is trained towards what's preferred. This is called **reinforcement learning from human feedback**, or RLHF. It's where much of the helpfulness and caution comes from.

After training, the parameters are fixed. Using the model changes nothing. When you chat with it, it isn't learning.

## An example

A 2022 paper from OpenAI, [Training language models to follow instructions](https://arxiv.org/abs/2203.02155), shows how much the later stages matter. They took GPT-3 and applied stages 2 and 3:

1. People wrote demonstrations of good behaviour, and the model was fine-tuned on them.
2. People ranked the model's answers.
3. The model was tuned further using those rankings.

In human evaluations, answers from a 1.3 billion parameter model trained this way were preferred to those of the original 175 billion parameter GPT-3, despite having over 100 times fewer parameters.

The lesson: size isn't everything. How a model is taught matters too.

## Not in ShopHelper

ShopHelper doesn't train anything. Almost no AI engineering job does, because pre-training costs a fortune. You use a finished model, and you control what it sees at run time.

Three things follow from how training works.

**The knowledge cutoff.** A model only knows what was in its training text, up to a date. It doesn't know today's news, and it has never seen your orders. That's why ShopHelper gives the model tools and search, rather than expecting it to know.

**It doesn't learn from you.** If a customer corrects the agent, it won't remember tomorrow. Anything it must know has to be sent with each request.

**Fine-tuning is usually not the first answer.** **Fine-tuning** means running a little more training on your own examples. It's good at teaching a style or a format. It's bad at keeping facts current: every policy change would mean training again, and the model can still blur the facts. So ShopHelper keeps policies in documents and searches them. When a policy changed in this project, the fix took one edit and a re-embed.

| Goal | Try first |
| --- | --- |
| Answer from your own, changing facts | [RAG](../05-rag/01-why-rag.md) |
| Take actions, or read live data | Tools |
| Follow a format or tone | A better prompt, then fine-tuning |
| Cut the cost of a narrow, repeated task | Fine-tune a smaller model |

## Interview questions

### How does a base model become a chat assistant?

**Strong answer:** Pre-training gives it broad knowledge by predicting the next token over huge amounts of text. But it only continues text. Instruction tuning on examples of good answers teaches it to respond, and reinforcement learning from feedback teaches it which answers people prefer. The InstructGPT paper showed how much this matters: a 1.3 billion parameter tuned model was preferred over the 175 billion parameter base GPT-3.

**Follow-up:** What's a downside of training on human preferences?

### When would you fine-tune instead of using RAG?

**Strong answer:** RAG for facts, especially ones that change, because updating a document is instant and answers can cite a source. Fine-tuning for behaviour, like a consistent format or tone, or to get a smaller, cheaper model to do one narrow task well. I'd try prompting first, because it's the cheapest thing to change. In my project policies change, so they live in documents.

**Follow-up:** How would you know fine-tuning was worth it?

## Check yourself

### A customer corrects the agent in a chat. What does the model learn?

- [x] Nothing: its parameters don't change — right: it can only use that correction while it's in the conversation.
- [ ] It remembers for everyone — training happens long before you use it.
- [ ] It remembers for that customer — only if your code stores it and sends it back.

### Your returns policy changes every few weeks. What's the best approach?

- [ ] Fine-tune each time — you'd retrain constantly, and it may still blur the old facts.
- [x] Keep it in a document, and search it — right: one edit, and answers can show their source.
- [ ] Wait for a newer model — it would never know your policy.

### Which stage costs the most?

- [x] Pre-training — right: reading vast amounts of text takes huge compute.
- [ ] Instruction tuning — it uses far less data.
- [ ] Using the finished model — a single call is tiny by comparison.
