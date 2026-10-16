from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from app.agent import Assistant
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


async def test_greeting_calls_no_tools():
    called = []

    @tool
    def find_user_profile(email: str) -> str:
        """Find user."""
        called.append(email)
        return "x"

    model = ScriptedModel(script=[AIMessage(content="Hello!")])
    a = Assistant(_settings(), model=model, mcp=NoMcp([find_user_profile]))
    assert await a.reply([{"role": "user", "content": "hi"}]) == "Hello!"
    assert model.calls == 1 and called == []


async def test_user_question_routes_to_mcp_tool():
    called = []

    @tool
    def find_user_profile(email: str) -> str:
        """Find user by email."""
        called.append(email)
        return '{"id":1,"name":"Олена"}'

    model = ScriptedModel(
        script=[_tool_call("find_user_profile", {"email": "olena1@example.com"}), AIMessage(content="Це Олена.")]
    )
    a = Assistant(_settings(), model=model, mcp=NoMcp([find_user_profile]))
    reply = await a.reply([{"role": "user", "content": "хто olena1@example.com?"}])
    assert reply == "Це Олена."
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
