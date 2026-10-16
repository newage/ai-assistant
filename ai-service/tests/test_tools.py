from unittest.mock import MagicMock

from langchain_core.tools import StructuredTool

from app import tools
from app.settings import Settings


def _settings():
    return Settings(_env_file=None, anthropic_api_key="x")


def test_search_faq_empty_returns_notice(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    t = tools.make_search_faq(_settings(), client=MagicMock())
    assert t.invoke({"query": "hi"}) == tools.NO_FAQ


def test_search_faq_failure_becomes_text(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(tools.faq, "search", boom)
    t = tools.make_search_faq(_settings(), client=MagicMock())
    assert t.invoke({"query": "hi"}) == tools.FAQ_UNAVAILABLE


async def test_mcp_tool_failure_becomes_text():
    async def boom(user_id: int) -> str:
        raise ConnectionError("mcp-server unavailable")

    inner = StructuredTool.from_function(coroutine=boom, name="get_user_activity", description="d")
    guarded = tools._guard_mcp_tool(inner)
    assert await guarded.ainvoke({"user_id": 1}) == tools.MCP_UNAVAILABLE


async def test_mcp_loading_failure_gives_no_tools():
    mcp = tools.McpTools("http://127.0.0.1:1/mcp")  # nothing listens here
    assert await mcp.load() == []


async def test_mcp_not_found_is_passed_through():
    async def not_found(user_id: int) -> str:
        return "User not found."

    inner = StructuredTool.from_function(coroutine=not_found, name="get_user_activity", description="d")
    assert await tools._guard_mcp_tool(inner).ainvoke({"user_id": 9}) == "User not found."
