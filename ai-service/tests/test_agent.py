from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from app import tools
from app.agent import REFUSAL, Assistant
from app.settings import Settings
from tests.conftest import ScriptedModel


def _settings():
    return Settings(_env_file=None, anthropic_api_key="x")


def _hit(score=0.9, text="A."):
    return {"text": text, "score": score}


def _assistant(monkeypatch, hits, model):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: hits)
    return Assistant(_settings(), model=model, qdrant=MagicMock())


async def test_faq_hit_gets_one_model_call_and_its_text(monkeypatch):
    model = ScriptedModel(script=[AIMessage(content="A.")])
    a = _assistant(monkeypatch, [_hit()], model)
    assert await a.reply([{"role": "user", "content": "q"}]) == "A."
    assert model.calls == 1


async def test_faq_entries_are_given_to_the_model(monkeypatch):
    seen = {}

    class Spy(ScriptedModel):
        def _generate(self, messages, *a, **k):
            seen["system"] = messages[0].content
            return super()._generate(messages, *a, **k)

    a = _assistant(monkeypatch, [_hit(text="Kliknij Reset.")], Spy(script=[AIMessage(content="ok")]))
    await a.reply([{"role": "user", "content": "q"}])
    assert "Kliknij Reset." in seen["system"]


async def test_search_uses_the_last_user_message(monkeypatch):
    queries = []
    monkeypatch.setattr(tools.faq, "search", lambda client, name, query, top_k: queries.append(query) or [])
    a = Assistant(_settings(), model=ScriptedModel(script=[AIMessage(content="x")]), qdrant=MagicMock())
    await a.reply([{"role": "user", "content": "first"}, {"role": "assistant", "content": "r"}, {"role": "user", "content": "second"}])
    assert queries == ["second"]


async def test_greeting_gets_refusal_without_model_call(monkeypatch):
    model = ScriptedModel(script=[AIMessage(content="Hello!")])
    a = _assistant(monkeypatch, [_hit(0.75)], model)  # a weak hit does not count
    assert await a.reply([{"role": "user", "content": "hi"}]) == REFUSAL
    assert model.calls == 0


async def test_off_topic_and_empty_collection_get_refusal_without_model_call(monkeypatch):
    model = ScriptedModel(script=[AIMessage(content="Jesienne liście...")])
    a = _assistant(monkeypatch, [], model)
    assert await a.reply([{"role": "user", "content": "napisz piosenkę o jesieni"}]) == REFUSAL
    assert model.calls == 0


async def test_history_is_passed_to_model(monkeypatch):
    seen = {}

    class Spy(ScriptedModel):
        def _generate(self, messages, *a, **k):
            seen["n"] = len(messages)
            return super()._generate(messages, *a, **k)

    a = _assistant(monkeypatch, [_hit()], Spy(script=[AIMessage(content="ok")]))
    await a.reply(
        [
            {"role": "user", "content": "my email is a@b.c"},
            {"role": "assistant", "content": "noted"},
            {"role": "user", "content": "what is it?"},
        ]
    )
    assert seen["n"] == 4  # system prompt + 3 history messages


def test_effort_is_passed_to_claude_model():
    s = Settings(_env_file=None, anthropic_api_key="x", claude_effort="low")
    assert Assistant(s)._model.effort == "low"
    assert Assistant(_settings())._model.effort is None


def test_max_tokens_is_passed_to_claude_model():
    s = Settings(_env_file=None, anthropic_api_key="x", claude_max_tokens=256)
    assert Assistant(s)._model.max_tokens == 256
    assert Assistant(_settings())._model.max_tokens == 1024
