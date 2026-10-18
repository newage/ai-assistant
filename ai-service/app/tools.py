"""FAQ search step of the chat pipeline."""
import logging
import time

from qdrant_client import QdrantClient

from app import faq
from app.logging_setup import truncate
from app.settings import Settings

log = logging.getLogger(__name__)


class FaqSearchError(Exception):
    """The FAQ search could not be performed (vector database unavailable)."""


def _log_step(step: str, status: str, started: float, args, result, hits: int | None = None) -> None:
    """Info: metadata only. Debug: arguments and result, truncated."""
    log.info("step", extra={"step": step, "status": status, "hits": hits, "duration_ms": round((time.perf_counter() - started) * 1000, 1)})
    log.debug("step content", extra={"step": step, "arguments": truncate(args), "result": truncate(result)})


def search_faq(settings: Settings, client: QdrantClient, query: str) -> list[dict]:
    """Return the FAQ hits that count as data (score not below `faq_min_score`); raise `FaqSearchError` on failure."""
    started = time.perf_counter()
    try:
        hits = faq.search(client, settings.faq_collection, query, settings.faq_top_k)
    except Exception as exc:
        log.exception("faq search failed")
        _log_step("faq_search", "error", started, {"query": query}, str(exc))
        raise FaqSearchError("The FAQ search is unavailable.") from exc
    hits = [h for h in hits if h["score"] >= settings.faq_min_score]
    _log_step("faq_search", "ok", started, {"query": query}, hits, hits=len(hits))
    return hits
