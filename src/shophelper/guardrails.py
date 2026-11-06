"""Step 5: Bedrock Guardrail checks around the agent loop (ApplyGuardrail API).

Running the guardrail ourselves (instead of attaching it to each model call) means it
runs once per turn on the user's text and once on the final answer - not on every
intermediate tool call - and it works the same for every agent framework.
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal

import boto3

from shophelper.config import get_settings


@dataclass
class GuardResult:
    blocked: bool
    text: str  # original, masked (PII anonymized) or the guardrail's blocked message
    reasons: list[str] = field(default_factory=list)


@lru_cache
def _client():
    return boto3.client("bedrock-runtime", region_name=get_settings().aws_region)


def check(text: str, source: Literal["INPUT", "OUTPUT"], client: Any = None) -> GuardResult:
    settings = get_settings()
    if not settings.guardrail_id:
        if settings.local_guardrails:
            return _local_check(text, source)
        return GuardResult(blocked=False, text=text)
    resp = (client or _client()).apply_guardrail(
        guardrailIdentifier=settings.guardrail_id,
        guardrailVersion=settings.guardrail_version,
        source=source,
        content=[{"text": {"text": text}}],
    )
    if resp["action"] != "GUARDRAIL_INTERVENED":
        return GuardResult(blocked=False, text=text)

    reasons, blocked = _findings(resp.get("assessments", []))
    out = "".join(o["text"] for o in resp.get("outputs", [])) or text
    return GuardResult(blocked=blocked, text=out, reasons=reasons)


# Local stand-in for infra/guardrail.tf, so the block/mask path can be seen without AWS.
# Same messages and same actions, but plain regexes: it catches the obvious cases only.
BLOCKED_INPUT = (
    "Sorry, I can't help with that request. Please don't share card numbers, passwords or other "
    "sensitive details, and keep questions to orders and store policy."
)
BLOCKED_OUTPUT = "Sorry, I can't share that. Please contact a human support agent."

_PROMPT_ATTACK = re.compile(
    r"ignore (all |any |the |your )*(previous |prior |above |earlier )?(instructions|rules|prompts?)"
    r"|(reveal|show|print|repeat|tell me)\b.{0,30}\b(system prompt|instructions)"
    r"|you are now\b|developer mode|jailbreak|pretend (you|to be)",
    re.IGNORECASE,
)
_BLOCK_PATTERNS = {
    "CREDIT_DEBIT_CARD_NUMBER": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "AADHAAR": re.compile(r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b"),
    "PASSWORD": re.compile(r"\b(password|passcode|cvv|otp)\s*(is|:|=)\s*\S+", re.IGNORECASE),
}
_MASK_PATTERNS = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "PHONE": re.compile(r"(?<![\w-])\+?\d[\d -]{8,13}\d\b"),
}


def _local_check(text: str, source: Literal["INPUT", "OUTPUT"]) -> GuardResult:
    blocked_message = BLOCKED_INPUT if source == "INPUT" else BLOCKED_OUTPUT
    reasons = [f"{name}:BLOCKED" for name, rx in _BLOCK_PATTERNS.items() if rx.search(text)]
    if source == "INPUT" and _PROMPT_ATTACK.search(text):
        reasons.append("PROMPT_ATTACK:BLOCKED")
    if reasons:
        return GuardResult(blocked=True, text=blocked_message, reasons=reasons)

    for name, rx in _MASK_PATTERNS.items():
        text, hits = rx.subn(f"{{{name}}}", text)
        if hits:
            reasons.append(f"{name}:ANONYMIZED")
    return GuardResult(blocked=False, text=text, reasons=reasons)


def _findings(assessments: list[dict[str, Any]]) -> tuple[list[str], bool]:
    """Flatten assessment entries into readable reasons; blocked if any entry BLOCKED."""
    reasons, blocked = [], False
    for a in assessments:
        groups = [
            a.get("contentPolicy", {}).get("filters", []),
            a.get("topicPolicy", {}).get("topics", []),
            a.get("sensitiveInformationPolicy", {}).get("piiEntities", []),
            a.get("sensitiveInformationPolicy", {}).get("regexes", []),
            a.get("wordPolicy", {}).get("customWords", []),
        ]
        for entries in groups:
            for e in entries:
                label = e.get("type") or e.get("name") or e.get("match", "?")
                reasons.append(f"{label}:{e.get('action')}")
                blocked = blocked or e.get("action") == "BLOCKED"
    return reasons, blocked
