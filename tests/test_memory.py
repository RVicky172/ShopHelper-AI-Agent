from shophelper.agent.memory import InMemoryHistory, to_converse_messages


def test_history_round_trip_and_limit():
    h = InMemoryHistory()
    for i in range(6):
        h.append("s1", "user" if i % 2 == 0 else "assistant", f"m{i}")
    turns = h.load("s1", limit=3)
    assert [t["text"] for t in turns] == ["m3", "m4", "m5"]


def test_converse_messages_start_with_user():
    msgs = to_converse_messages([{"role": "assistant", "text": "a"}, {"role": "user", "text": "u"}])
    assert msgs == [{"role": "user", "content": [{"text": "u"}]}]
