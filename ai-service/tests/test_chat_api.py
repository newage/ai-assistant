import httpx
import pytest
from anthropic import APIConnectionError
from httpx import ASGITransport, AsyncClient

from app.main import app, get_assistant


class FakeAssistant:
    def __init__(self, reply="pong", error=None):
        self._reply, self._error, self.received = reply, error, None

    async def reply(self, messages):
        self.received = messages
        if self._error:
            raise self._error
        return self._reply


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")


@pytest.fixture(autouse=True)
def _reset():
    yield
    app.dependency_overrides.clear()
    if hasattr(app.state, "assistant"):
        del app.state.assistant


def _use(fake):
    app.state.assistant = fake


async def test_chat_ok(client):
    fake = FakeAssistant("pong")
    _use(fake)
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "ping"}]})
    assert r.status_code == 200 and r.json() == {"reply": "pong"}
    assert fake.received == [{"role": "user", "content": "ping"}]


@pytest.mark.parametrize(
    "body",
    [
        {"messages": []},
        {"messages": [{"role": "bot", "content": "x"}]},
        {"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]},
        {},
    ],
)
async def test_chat_invalid_is_422_and_no_llm_call(client, body):
    fake = FakeAssistant()
    _use(fake)
    r = await client.post("/chat", json=body)
    assert r.status_code == 422 and fake.received is None


async def test_chat_claude_failure_is_5xx(client):
    err = APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
    _use(FakeAssistant(error=err))
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "x"}]})
    assert r.status_code == 502 and "reply" not in r.json()
