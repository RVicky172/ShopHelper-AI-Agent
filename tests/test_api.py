from fastapi.testclient import TestClient

from shophelper import api
from shophelper.raw_agent import AgentResult, MaxStepsExceeded

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_validates_input():
    assert client.post("/chat", json={"session_id": "short", "message": "hi"}).status_code == 422
    assert client.post("/chat", json={"session_id": "abcd1234", "message": ""}).status_code == 422


def test_chat_returns_answer(monkeypatch):
    monkeypatch.setattr(
        api, "run_agent", lambda q: AgentResult(answer="Hi!", messages=[], tools_used=["x"])
    )
    body = client.post("/chat", json={"session_id": "abcd1234", "message": "hi"}).json()
    assert body["answer"] == "Hi!" and body["tools_used"] == ["x"]


def test_chat_max_steps(monkeypatch):
    def boom(q):
        raise MaxStepsExceeded("too many")

    monkeypatch.setattr(api, "run_agent", boom)
    assert client.post("/chat", json={"session_id": "abcd1234", "message": "hi"}).status_code == 422
