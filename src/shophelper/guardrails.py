"""Step 5: Bedrock Guardrail checks around the agent loop (ApplyGuardrail API).

Running the guardrail ourselves (instead of attaching it to each model call) means it
runs once per turn on the user's text and once on the final answer - not on every
intermediate tool call - and it works the same for every agent framework.
"""

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
