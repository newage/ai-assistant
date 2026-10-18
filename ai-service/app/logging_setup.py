"""JSON logging on stdout with a per-request id and a per-request debug switch."""
import json
import logging
import os
import re
from contextvars import ContextVar
from datetime import datetime, timezone

SERVICE = "ai-service"
CONTENT_LIMIT = 500
# Libraries whose debug output is noise (or may carry request headers); they never log below INFO.
QUIET_LOGGERS = ("httpcore", "httpx", "anthropic", "urllib3", "asyncio")
REQUEST_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,64}")

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
debug_requested_var: ContextVar[bool] = ContextVar("debug_requested", default=False)

_STANDARD = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime", "request_id"}


def environment() -> str:
    return os.environ.get("ENVIRONMENT") or "local"


def debug_enabled() -> bool:
    """Debug is on when the request asked for it, or outside production."""
    return debug_requested_var.get() or environment() != "prod"


def valid_request_id(value: str | None) -> str | None:
    return value if value and REQUEST_ID_RE.fullmatch(value) else None


def truncate(value, limit: int = CONTENT_LIMIT) -> str:
    text = value if isinstance(value, str) else str(value)
    return text if len(text) <= limit else text[:limit] + "…"


class ContextFilter(logging.Filter):
    """Adds the request id to the record and drops debug records unless debug is enabled (and never from quiet libraries)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        if record.levelno > logging.DEBUG:
            return True
        return debug_enabled() and not record.name.startswith(QUIET_LOGGERS)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extra = {k: v for k, v in record.__dict__.items() if k not in _STANDARD}
        if record.exc_info:
            extra["exception"] = self.formatException(record.exc_info)
        line = {
            "priority": record.levelname,
            "service": SERVICE,
            "short_message": record.getMessage(),
            "x-request-id": getattr(record, "request_id", request_id_var.get()),
            "extra": extra or [],
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "log_id": os.environ.get("LOG_ID") or "dev",
            "environment": environment(),
        }
        return json.dumps(line, ensure_ascii=False, default=str)
