from fastapi.testclient import TestClient

from shophelper import api
from shophelper.schemas import ChatResponse
from shophelper.service import NoPendingApproval


class FakeService:
    async def chat(self, session_id, message, principal=None):
        return ChatResponse(session_id=session_id, answer=f"echo: {message}")

    async def approve(self, session_id, approved, reviewer, note="", owner_id=None):
        raise NoPendingApproval(session_id)


api.app.state.service = FakeService()
client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_validates_input():
    assert client.post("/chat", json={"session_id": "short", "message": "hi"}).status_code == 422
    assert client.post("/chat", json={"session_id": "abcd1234", "message": ""}).status_code == 422
    assert client.post("/chat", json={"session_id": "abcd1234", "message": "x" * 2001}).status_code == 422


def test_chat_returns_answer():
    body = client.post("/chat", json={"session_id": "abcd1234", "message": "hi"}).json()
    assert body["answer"] == "echo: hi" and body["status"] == "answered"


def test_approve_without_pending_is_409():
    r = client.post("/approve", json={"session_id": "abcd1234", "approved": True, "reviewer": "a"})
    assert r.status_code == 409
