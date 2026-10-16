"""Agent tools. Failures are returned as text so the LLM can explain them honestly."""
import logging

from langchain_core.tools import BaseTool, StructuredTool, tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from qdrant_client import QdrantClient

from app import faq
from app.settings import Settings

log = logging.getLogger(__name__)

NO_FAQ = "No relevant FAQ entries found."
FAQ_UNAVAILABLE = "The FAQ search is temporarily unavailable."
MCP_UNAVAILABLE = "The user data service is temporarily unavailable, so this information could not be retrieved."


def make_search_faq(settings: Settings, client: QdrantClient | None = None) -> BaseTool:
    qdrant = client or QdrantClient(url=settings.qdrant_url)

    @tool
    def search_faq(query: str) -> str:
        """Search the FAQ / knowledge base for answers to general product or support questions."""
        try:
            hits = faq.search(qdrant, settings.faq_collection, query, settings.faq_top_k)
        except Exception:
            log.exception("search_faq failed")
            return FAQ_UNAVAILABLE
        if not hits:
            return NO_FAQ
        return "\n\n".join(f"Q: {h['question']}\nA: {h['answer']}" for h in hits)

    return search_faq


def _guard_mcp_tool(t: BaseTool) -> BaseTool:
    """Wrap an MCP tool so transport errors become a tool result instead of an exception."""

    async def run(**kwargs):
        try:
            return await t.ainvoke(kwargs)
        except Exception:
            log.exception("MCP tool %s failed", t.name)
            return MCP_UNAVAILABLE

    return StructuredTool.from_function(
        coroutine=run, name=t.name, description=t.description, args_schema=t.args_schema
    )


class McpTools:
    """Loads MCP tools lazily so ai-service can start (and answer) while mcp-server is down."""

    def __init__(self, url: str):
        self._client = MultiServerMCPClient({"users": {"url": url, "transport": "streamable_http"}})

    async def load(self) -> list[BaseTool]:
        try:
            return [_guard_mcp_tool(t) for t in await self._client.get_tools()]
        except Exception:
            log.exception("could not load MCP tools")
            return []
