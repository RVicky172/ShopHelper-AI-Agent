import json
import os
from pathlib import Path

import pytest

RESULTS: list[dict] = []


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_EVALS") != "1":
        skip = pytest.mark.skip(reason="evals call real AWS Bedrock - set RUN_EVALS=1")
        for item in items:
            item.add_marker(skip)


@pytest.fixture
def record():
    return RESULTS.append


def pytest_sessionfinish(session, exitstatus):
    if not RESULTS:
        return
    passed = sum(r["passed"] for r in RESULTS)
    judged = [r["judge"]["score"] for r in RESULTS if r.get("judge")]
    summary = {
        "cases": len(RESULTS),
        "passed": passed,
        "attacks_blocked_or_refused": sum(r["passed"] for r in RESULTS if r["attack"]),
        "attacks": sum(r["attack"] for r in RESULTS),
        "mean_faithfulness": round(sum(judged) / len(judged), 2) if judged else None,
        "total_input_tokens": sum(r["input_tokens"] for r in RESULTS),
        "total_output_tokens": sum(r["output_tokens"] for r in RESULTS),
        "results": RESULTS,
    }
    Path(__file__).with_name("report.json").write_text(json.dumps(summary, indent=2))
    print(f"\nEVAL SUMMARY: {passed}/{len(RESULTS)} passed, "
          f"faithfulness={summary['mean_faithfulness']}, report: evals/report.json")
