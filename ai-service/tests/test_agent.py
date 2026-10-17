from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from app import tools
from app.agent import REFUSAL, Assistant
from app.settings import Settings
from tests.conftest import ScriptedModel


class NoMcp:
    def __init__(self, tools=()):
        self._tools = list(tools)

    async def load(self):
        return self._tools


def _settings():
    return Settings(_env_file=None, anthropic_api_key="x")


def _tool_call(name, args):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": "c1"}])


def _mcp_tool(result='{"id":1,"name":"Helena"}', calls=None):
    @tool
    def find_user_profile(email: str) -> str:
        """Find user by email."""
        if calls is not None:
            calls.append(email)
        return result

    return tools._guard_mcp_tool(find_user_profile)


async def test_greeting_gets_refusal_and_calls_no_tools():
    called = []
    model = ScriptedModel(script=[AIMessage(content="Hello!")])
    a = Assistant(_settings(), model=model, mcp=NoMcp([_mcp_tool(calls=called)]))
    assert await a.reply([{"role": "user", "content": "hi"}]) == REFUSAL
    assert model.calls == 1 and called == []


async def test_off_topic_answer_is_replaced_by_refusal():
    model = ScriptedModel(script=[AIMessage(content="Jesienne liście, spadają...")])
    a = Assistant(_settings(), model=model, mcp=NoMcp())
    assert await a.reply([{"role": "user", "content": "napisz piosenkę o jesieni"}]) == REFUSAL


async def test_step_limit_ends_in_refusal():
    called = []

    class Looping(ScriptedModel):
        def _generate(self, messages, *a, **k):  # a fresh tool call id every time, so it never ends
            self.script = [AIMessage(content="", tool_calls=[{"name": "find_user_profile", "args": {"email": "a@b.c"}, "id": f"c{self.calls}"}])]
            return super()._generate(messages, *a, **k)

    model = Looping(script=[])
    s = Settings(_env_file=None, anthropic_api_key="x", agent_max_steps=2)
    a = Assistant(s, model=model, mcp=NoMcp([_mcp_tool(calls=called)]))
    assert await a.reply([{"role": "user", "content": "kto to a@b.c?"}]) == REFUSAL
    assert len(called) == 2  # exactly agent_max_steps tool rounds, then stopped


async def test_user_not_found_is_refused():
    from langchain_core.tools import ToolException

    @tool
    def find_user_profile(email: str) -> str:
        """Find user by email."""
        raise ToolException("User not found.")

    model = ScriptedModel(
        script=[_tool_call("find_user_profile", {"email": "x@y.z"}), AIMessage(content="Nie znaleziono.")]
    )
    a = Assistant(_settings(), model=model, mcp=NoMcp([tools._guard_mcp_tool(find_user_profile)]))
    assert await a.reply([{"role": "user", "content": "kto to x@y.z?"}]) == REFUSAL


async def test_user_question_routes_to_mcp_tool():
    called = []
    model = ScriptedModel(
        script=[_tool_call("find_user_profile", {"email": "olena1@example.com"}), AIMessage(content="To Helena.")]
    )
    a = Assistant(_settings(), model=model, mcp=NoMcp([_mcp_tool(calls=called)]))
    reply = await a.reply([{"role": "user", "content": "kto to olena1@example.com?"}])
    assert reply == "To Helena."
    assert called == ["olena1@example.com"]


async def test_history_is_passed_to_model():
    seen = {}

    class Spy(ScriptedModel):
        def _generate(self, messages, *a, **k):
            seen["n"] = len(messages)
            return super()._generate(messages, *a, **k)

    a = Assistant(_settings(), model=Spy(script=[AIMessage(content="ok")]), mcp=NoMcp())
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
    assert Assistant(s, mcp=NoMcp())._model.effort == "low"
    assert Assistant(_settings(), mcp=NoMcp())._model.effort is None


def test_max_tokens_is_passed_to_claude_model():
    s = Settings(_env_file=None, anthropic_api_key="x", claude_max_tokens=256)
    assert Assistant(s, mcp=NoMcp())._model.max_tokens == 256
    assert Assistant(_settings(), mcp=NoMcp())._model.max_tokens == 1024


async def test_faq_answer_passes_the_check(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [{"question": "Q?", "answer": "A.", "score": 0.9}])
    from unittest.mock import MagicMock

    faq_tool = tools.make_search_faq(_settings(), client=MagicMock())
    model = ScriptedModel(script=[_tool_call("search_faq", {"query": "q"}), AIMessage(content="A.")])
    a = Assistant(_settings(), model=model, extra_tools=[], mcp=NoMcp())
    a._static_tools = [faq_tool]
    assert await a.reply([{"role": "user", "content": "q"}]) == "A."
