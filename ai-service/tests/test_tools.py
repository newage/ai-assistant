from unittest.mock import MagicMock

from langchain_core.tools import StructuredTool, ToolException

from app import tools
from app.settings import Settings


def _settings():
    return Settings(_env_file=None, anthropic_api_key="x")


def _hit(score):
    return {"question": "Q?", "answer": "A.", "score": score}


def _tracked(fn):
    tracker = tools.DataTracker()
    token = tools.data_tracker_var.set(tracker)
    try:
        return fn(), tracker
    finally:
        tools.data_tracker_var.reset(token)


def test_search_faq_strong_hit_marks_data(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [_hit(0.9), _hit(0.5)])
    t = tools.make_search_faq(_settings(), client=MagicMock())
    result, tracker = _tracked(lambda: t.invoke({"query": "q"}))
    assert tracker.found and "Q: Q?" in result and result.count("Q: ") == 1  # the weak hit is dropped


def test_search_faq_weak_hits_are_not_data(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [_hit(0.79), _hit(0.5)])
    t = tools.make_search_faq(_settings(), client=MagicMock())
    result, tracker = _tracked(lambda: t.invoke({"query": "q"}))
    assert not tracker.found and result == tools.NO_FAQ


def test_search_faq_empty_returns_notice(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    t = tools.make_search_faq(_settings(), client=MagicMock())
    assert t.invoke({"query": "hi"}) == tools.NO_FAQ


def test_search_faq_empty_is_not_data(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    t = tools.make_search_faq(_settings(), client=MagicMock())
    _, tracker = _tracked(lambda: t.invoke({"query": "q"}))
    assert not tracker.found


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


async def _guarded_call(coroutine):
    inner = StructuredTool.from_function(coroutine=coroutine, name="get_user_activity", description="d")
    tracker = tools.DataTracker()
    token = tools.data_tracker_var.set(tracker)
    try:
        return await tools._guard_mcp_tool(inner).ainvoke({"user_id": 9}), tracker
    finally:
        tools.data_tracker_var.reset(token)


async def test_mcp_not_found_is_passed_through_but_not_data():
    async def not_found(user_id: int) -> str:
        raise ToolException("User not found.")

    result, tracker = await _guarded_call(not_found)
    assert result == "User not found." and not tracker.found


async def test_mcp_result_is_data():
    async def found(user_id: int) -> str:
        return '{"id": 9}'

    result, tracker = await _guarded_call(found)
    assert result == '{"id": 9}' and tracker.found


async def test_mcp_unavailable_is_not_data():
    async def boom(user_id: int) -> str:
        raise ConnectionError("down")

    result, tracker = await _guarded_call(boom)
    assert result == tools.MCP_UNAVAILABLE and not tracker.found
