"""LLM-as-judge for faithfulness: is every claim in the answer supported by the retrieved passages?

A different, stronger model (Sonnet) judges the agent model (Haiku) to reduce self-preference bias.
"""

import json
import re
from functools import lru_cache

import boto3

from shophelper.core.config import get_settings

JUDGE_PROMPT = """You are grading a customer-support answer for FAITHFULNESS.

<question>{question}</question>
<retrieved_passages>
{passages}
</retrieved_passages>
<answer>{answer}</answer>

An answer is faithful if every factual claim about store policy in it is supported by the
retrieved passages. Saying that the information is not available, when the passages don't
contain it, is faithful. Friendly filler and offers to help further are fine.

Reply with ONLY a JSON object:
{{"score": <1-5, 5 = fully supported>, "faithful": <true|false>, "reason": "<one sentence>"}}"""


@lru_cache
def _client():
    return boto3.client("bedrock-runtime", region_name=get_settings().aws_region)


def _ask_bedrock(prompt: str) -> str:
    resp = _client().converse(
        modelId=get_settings().judge_model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )
    return resp["output"]["message"]["content"][0]["text"]


def _ask_local(prompt: str) -> str:
    """Local runs: the agent's own model is the judge, so the bias noted above applies."""
    from shophelper.rag.pipeline import _client as local_client

    resp = local_client().chat.completions.create(
        model=get_settings().local_chat_model, temperature=0, max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def judge_faithfulness(question: str, passages: list[str], answer: str) -> dict:
    prompt = JUDGE_PROMPT.format(
        question=question, passages="\n---\n".join(passages) or "(none)", answer=answer
    )
    text = _ask_local(prompt) if get_settings().llm_provider == "openai_compatible" else _ask_bedrock(prompt)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else {"score": 0, "faithful": False, "reason": text}
