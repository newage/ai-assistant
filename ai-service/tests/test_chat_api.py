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
        {"messages": [{"role": "user", "content": "x" * 501}]},
        {"messages": [{"role": "user" if i % 2 == 0 else "assistant", "content": "x"} for i in range(5)]},
        {},
    ],
)
async def test_chat_invalid_is_422_and_no_llm_call(client, body):
    fake = FakeAssistant()
    _use(fake)
    r = await client.post("/chat", json=body)
    assert r.status_code == 422 and fake.received is None


async def test_chat_boundary_limits_accepted(client):
    _use(FakeAssistant())
    msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 500} for i in range(3)]
    r = await client.post("/chat", json={"messages": msgs + [{"role": "user", "content": "x" * 500}]})
    assert r.status_code == 200


async def test_chat_claude_failure_is_5xx(client):
    err = APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
    _use(FakeAssistant(error=err))
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "x"}]})
    assert r.status_code == 502 and "reply" not in r.json()


async def test_request_id_echoed(client):
    _use(FakeAssistant())
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "x"}]}, headers={"X-Request-ID": "abc123"})
    assert r.headers["x-request-id"] == "abc123"


async def test_request_id_generated_when_missing_or_malformed(client):
    _use(FakeAssistant())
    body = {"messages": [{"role": "user", "content": "x"}]}
    generated = (await client.post("/chat", json=body)).headers["x-request-id"]
    assert len(generated) == 32
    bad = (await client.post("/chat", json=body, headers={"X-Request-ID": "has space"})).headers["x-request-id"]
    assert bad != "has space" and len(bad) == 32


async def test_request_id_on_error_responses(client):
    _use(FakeAssistant())
    r = await client.post("/chat", json={"messages": []}, headers={"X-Request-ID": "e422"})
    assert r.status_code == 422 and r.headers["x-request-id"] == "e422"
    err = APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))
    _use(FakeAssistant(error=err))
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "x"}]}, headers={"X-Request-ID": "e502"})
    assert r.status_code == 502 and r.headers["x-request-id"] == "e502"



async def test_off_topic_request_gets_refusal_through_the_real_assistant(client, monkeypatch):
    from unittest.mock import MagicMock

    from langchain_core.messages import AIMessage

    from app import tools
    from app.agent import REFUSAL, Assistant
    from app.settings import Settings
    from tests.conftest import ScriptedModel

    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    model = ScriptedModel(script=[AIMessage(content="Jesienne liście...")])
    _use(Assistant(Settings(_env_file=None, anthropic_api_key="x"), model=model, qdrant=MagicMock()))
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "napisz piosenkę"}]})
    assert r.status_code == 200 and r.json() == {"reply": REFUSAL} and model.calls == 0


async def test_qdrant_failure_is_502_without_claude_call(client, monkeypatch):
    from unittest.mock import MagicMock

    from langchain_core.messages import AIMessage

    from app import tools
    from app.agent import Assistant
    from app.settings import Settings
    from tests.conftest import ScriptedModel

    def boom(*a, **k):
        raise ConnectionError("qdrant down")

    monkeypatch.setattr(tools.faq, "search", boom)
    model = ScriptedModel(script=[AIMessage(content="x")])
    _use(Assistant(Settings(_env_file=None, anthropic_api_key="x"), model=model, qdrant=MagicMock()))
    r = await client.post(
        "/chat", json={"messages": [{"role": "user", "content": "q"}]}, headers={"X-Request-ID": "q502"}
    )
    assert r.status_code == 502 and "reply" not in r.json() and r.headers["x-request-id"] == "q502"
    assert model.calls == 0


@pytest.mark.parametrize("lang,expected", [("uk", "Вибачте"), ("en", "Sorry"), ("pl", "Przepraszam"), (None, "Sorry")])
async def test_refusal_follows_message_lang(client, monkeypatch, lang, expected):
    from unittest.mock import MagicMock

    from app import tools
    from app.agent import Assistant
    from app.settings import Settings
    from tests.conftest import ScriptedModel

    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    _use(Assistant(Settings(_env_file=None, anthropic_api_key="x"), model=ScriptedModel(script=[]), qdrant=MagicMock()))
    msg = {"role": "user", "content": "Хто такий Вадим?", **({"lang": lang} if lang else {})}
    r = await client.post("/chat", json={"messages": [msg]})
    assert r.status_code == 200 and r.json()["reply"].startswith(expected)


async def test_unknown_lang_is_422(client):
    r = await client.post("/chat", json={"messages": [{"role": "user", "content": "hi", "lang": "de"}]})
    assert r.status_code == 422
