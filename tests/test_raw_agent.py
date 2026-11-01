import pytest

from shophelper.raw_agent import MaxStepsExceeded, run_agent


class StubBedrock:
    """Replays canned Converse responses so the loop can be tested offline."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _resp(stop, content):
    return {
        "stopReason": stop,
        "output": {"message": {"role": "assistant", "content": content}},
        "usage": {"inputTokens": 10, "outputTokens": 5},
    }


TOOL_CALL = _resp(
    "tool_use",
    [{"toolUse": {"toolUseId": "t1", "name": "get_order_status", "input": {"order_id": "1002"}}}],
)


def test_loop_runs_tool_then_answers():
    stub = StubBedrock([TOOL_CALL, _resp("end_turn", [{"text": "It ships in 2 days."}])])
    result = run_agent("Where is 1002?", client=stub)

    assert result.answer == "It ships in 2 days."
    assert result.tools_used == ["get_order_status"]
    assert result.input_tokens == 20
    # messages: user, assistant(toolUse), user(toolResult), assistant(answer)
    tool_result = result.messages[2]["content"][0]["toolResult"]
    assert tool_result["content"][0]["json"]["status"] == "shipped"


def test_max_steps_guard():
    stub = StubBedrock([TOOL_CALL] * 10)
    with pytest.raises(MaxStepsExceeded):
        run_agent("loop forever", client=stub)


def test_local_policy_search_finds_returns_policy():
    from shophelper.tools import search_policy

    top = search_policy("restocking fee for opened electronics returns")["passages"][0]
    assert top["source"] == "returns.md"
