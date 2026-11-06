---
title: Tokens
checked: 2026-11-06
---

## What you'll learn

- What a token is, and why models don't read words
- Why tokens matter for cost, speed and limits
- Why numbers and some languages cost more
- How to see real token counts in this project

## The simple explanation

A model can't read text. It works on numbers. So before anything else, a **tokenizer** cuts your text into small pieces called **tokens**, and gives each piece a number.

A token isn't quite a word. Common words are usually one token. Rarer words split into pieces the tokenizer knows. Think of building with Lego: you keep plenty of common bricks ready, and build anything unusual from smaller ones.

Why not just use words, or letters?

| Method | Problem |
| --- | --- |
| Whole words | There are too many, and a new word couldn't be read at all |
| Single letters | Text becomes very long, and a letter carries little meaning |
| **Pieces of words** | A compromise: common words stay whole, and rare ones are built from parts |

The usual way of learning those pieces is **byte pair encoding**. Start with single characters, find the pair that appears most often, merge it into a new piece, and repeat until you have enough. Hugging Face has a [clear walkthrough](https://huggingface.co/docs/transformers/main/en/tokenizer_summary).

Tokens matter because they're how everything is measured. You pay per token, speed is tokens per second, and a model's limit is counted in tokens.

## An example

These were measured on this project's local model, Qwen3. Other models split text differently, so counts vary.

| Text | Characters | Tokens |
| --- | --- | --- |
| `refund` | 6 | 1 |
| `refunds` | 7 | 2 |
| `ShopHelper` | 10 | 2 |
| `unbelievably` | 12 | 3 |
| `How long do refunds take?` | 25 | 6 |
| `The quick brown fox jumps over the lazy dog.` | 44 | 10 |
| `1002` | 4 | 4 |
| `1234567890` | 10 | 10 |

Three things stand out:

- `refund` is one token, but adding an *s* makes it two. Small changes aren't always small to a model.
- This tokenizer gives every digit its own token. That's one reason models can be clumsy with numbers: they never see 1002 as a single thing.
- English averages about 4 characters a token here, but that's only a rule of thumb.

Now the same question in two languages:

| Text | Characters | Tokens |
| --- | --- | --- |
| `Where is my order?` | 18 | 5 |
| `मेरा ऑर्डर कहाँ है?` | 19 | 18 |

Nearly the same length, but the Hindi costs over three times as many tokens. Tokenizers learn from their training text, and most of that is English. So the same conversation can cost more, run slower and fill the limit sooner in another language. That's worth knowing if you build for customers in India.

## How ShopHelper does it

The agent caps how much the model may write in one reply:

```python file=src/shophelper/core/config.py
max_tokens: int = 1024
```

Every reply reports the tokens it used, and the service adds them up for each turn:

```python file=src/shophelper/agent/service.py
tokens_in += usage.get("input_tokens", 0)
tokens_out += usage.get("output_tokens", 0)
```

**Input tokens** are everything you send: the instructions, the conversation so far, and tool results. **Output tokens** are what the model writes. Input is usually much larger. One real turn on the trace page used 1,757 tokens in and 98 out, and most of that input was the system prompt and the policy passages.

A message also costs more than its own words. Sending just the letter "a" counted as 9 tokens here, because a chat message is wrapped in markers saying who's speaking.

## Try it

1. Sign in, open **How it works**, and click the **Tool call** example.
2. Find the token counts in the trace.
3. Compare the input of "Model call 1" and "Model call 2". The second is larger, because it includes the tool result.
4. Ask "Hello!". It uses far fewer tokens, because nothing was looked up.

## Interview questions

### What's a token, and why does it matter?

**Strong answer:** A token is the unit a model reads and writes: usually a common word or a piece of a rarer one. It matters because pricing, speed and context limits are all in tokens. So when I estimate cost, I count tokens, not words. I also separate input from output, because input is often far larger: a real turn in my project used about 1,750 in and 100 out.

**Follow-up:** How would you cut token usage in a chat product?

### Why are language models often bad at counting letters or doing arithmetic?

**Strong answer:** Partly tokenization. The model sees tokens, not letters, so a word's spelling isn't directly visible to it. Numbers are split in ways that depend on the tokenizer: mine gives each digit its own token. It's also predicting likely text rather than calculating. So for anything exact, I don't ask the model: I give it a tool, or do it in code.

**Follow-up:** Give an example where you kept something exact out of the model's hands.

### Your product launches in a new language, and costs jump. What's happening?

**Strong answer:** Tokenizers are trained mostly on English, so other languages often take more tokens for the same meaning. I measured this: a short question took 5 tokens in English and 18 in Hindi. So cost, speed and context use all get worse. I'd measure real token counts per language, test models with better tokenizers for that language, and set budgets per language.

**Follow-up:** What else might get worse besides cost?

## Check yourself

### What does a tokenizer do?

- [x] Cuts text into pieces and turns them into numbers — right: models work on numbers, not text.
- [ ] Counts how many words you typed — a token isn't the same as a word.
- [ ] Translates text into English — it doesn't change the language.

### Why might the same message cost more in Hindi than English?

- [ ] Providers charge more for other languages — the price per token doesn't change.
- [x] It can take more tokens — right: tokenizers mostly learn from English text.
- [ ] Hindi replies are always longer — the extra cost shows up in the input too.

### What's usually the larger part of a chat turn?

- [x] Input tokens — right: instructions, history and tool results all go in every time.
- [ ] Output tokens — the reply is usually much shorter than what's sent.
- [ ] They're always equal — a real turn here used about 1,750 in and 100 out.
