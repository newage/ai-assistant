"""Agent tools. Failures are returned as text so the LLM can explain them honestly."""
import logging
import time
from contextvars import ContextVar

from langchain_core.tools import BaseTool, StructuredTool, ToolException, tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from qdrant_client import QdrantClient

from app import faq
from app.logging_setup import debug_requested_var, request_id_var, truncate
from app.settings import Settings

log = logging.getLogger(__name__)

NO_FAQ = "No relevant FAQ entries found."
FAQ_UNAVAILABLE = "The FAQ search is temporarily unavailable."
MCP_UNAVAILABLE = "The user data service is temporarily unavailable, so this information could not be retrieved."


class DataTracker:
    """Per-request record of whether any tool returned real data (see `Assistant.reply`)."""

    def __init__(self) -> None:
        self.found = False


data_tracker_var: ContextVar[DataTracker | None] = ContextVar("data_tracker", default=None)


def mark_data() -> None:
    tracker = data_tracker_var.get()
    if tracker is not None:
        tracker.found = True


def _log_tool_call(name: str, status: str, started: float, args, result) -> None:
    """Info: metadata only. Debug: arguments and result, truncated."""
    log.info("tool call", extra={"tool": name, "status": status, "duration_ms": round((time.perf_counter() - started) * 1000, 1)})
    log.debug("tool call content", extra={"tool": name, "arguments": truncate(args), "result": truncate(result)})


def make_search_faq(settings: Settings, client: QdrantClient | None = None) -> BaseTool:
    qdrant = client or QdrantClient(url=settings.qdrant_url)

    @tool
    def search_faq(query: str) -> str:
        """Search the FAQ / knowledge base for answers to general product or support questions."""
        started = time.perf_counter()
        try:
            hits = faq.search(qdrant, settings.faq_collection, query, settings.faq_top_k)
        except Exception:
            log.exception("search_faq failed")
            _log_tool_call("search_faq", "error", started, {"query": query}, FAQ_UNAVAILABLE)
            return FAQ_UNAVAILABLE
        hits = [h for h in hits if h["score"] >= settings.faq_min_score]
        if hits:
            mark_data()
        result = NO_FAQ if not hits else "\n\n".join(f"Q: {h['question']}\nA: {h['answer']}" for h in hits)
        _log_tool_call("search_faq", "ok", started, {"query": query}, result)
        return result

    return search_faq


def _guard_mcp_tool(t: BaseTool) -> BaseTool:
    """Wrap an MCP tool so transport errors become a tool result instead of an exception."""

    async def run(**kwargs):
        started = time.perf_counter()
        try:
            result = await t.ainvoke(kwargs)
        except ToolException as exc:  # the tool ran but reported an error, e.g. "User not found." - not data
            _log_tool_call(t.name, "error", started, kwargs, str(exc))
            return str(exc)
        except Exception:
            log.exception("MCP tool %s failed", t.name)
            _log_tool_call(t.name, "error", started, kwargs, MCP_UNAVAILABLE)
            return MCP_UNAVAILABLE
        mark_data()
        _log_tool_call(t.name, "ok", started, kwargs, result)
        return result

    return StructuredTool.from_function(
        coroutine=run, name=t.name, description=t.description, args_schema=t.args_schema
    )


class McpTools:
    """Loads MCP tools lazily so ai-service can start (and answer) while mcp-server is down."""

    def __init__(self, url: str):
        self._url = url

    async def load(self, request_id: str | None = None, debug: bool | None = None) -> list[BaseTool]:
        """Build a client for this request so its id and debug flag travel to mcp-server as headers."""
        headers = {
            "X-Request-ID": request_id or request_id_var.get(),
            "X-Debugging": "true" if (debug_requested_var.get() if debug is None else debug) else "false",
        }
        client = MultiServerMCPClient(
            {"users": {"url": self._url, "transport": "streamable_http", "headers": headers}},
            handle_tool_errors=False,  # isError results raise, so the guard can tell "not found" from data
        )
        try:
            return [_guard_mcp_tool(t) for t in await client.get_tools()]
        except Exception:
            log.exception("could not load MCP tools")
            return []
