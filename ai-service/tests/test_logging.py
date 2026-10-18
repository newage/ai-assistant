import io
import json
import logging
import logging.config
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app import logging_setup, tools
from app.logging_setup import ContextFilter, JsonFormatter
from app.main import app
from app.settings import Settings

REQUIRED = {"priority", "service", "short_message", "x-request-id", "extra", "timestamp", "log_id", "environment"}


@pytest.fixture
def json_logs(monkeypatch):
    """Captures root-logger output through the production formatter and filter."""
    monkeypatch.setenv("ENVIRONMENT", "local")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(ContextFilter())
    root = logging.getLogger()
    old_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    root.removeHandler(handler)
    root.setLevel(old_level)


def test_record_is_json_with_required_fields(monkeypatch):
    monkeypatch.setenv("LOG_ID", "vadym")
    monkeypatch.setenv("ENVIRONMENT", "local")
    record = logging.LogRecord("x", logging.WARNING, __file__, 1, "hello %s", ("world",), None)
    line = json.loads(JsonFormatter().format(record))
    assert REQUIRED <= line.keys()
    assert line["priority"] == "WARNING" and line["service"] == "ai-service"
    assert line["short_message"] == "hello world" and line["extra"] == []
    assert line["log_id"] == "vadym" and line["environment"] == "local"
    assert line["timestamp"].endswith("+00:00")


def test_extra_fields_and_exception_go_to_extra():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "failed", None, sys.exc_info())
    record.step = "faq_search"
    extra = json.loads(JsonFormatter().format(record))["extra"]
    assert extra["step"] == "faq_search" and "ValueError: boom" in extra["exception"]


def test_uvicorn_log_config_loads_and_emits_json(capsys, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    cfg = json.loads((Path(__file__).parent.parent / "log_config.json").read_text())
    root = logging.getLogger()
    saved = root.handlers[:], root.level
    try:
        logging.config.dictConfig(cfg)
        logging.getLogger("uvicorn.error").info("Application startup complete.")
        line = json.loads(capsys.readouterr().out.strip())
        assert line["short_message"] == "Application startup complete." and REQUIRED <= line.keys()
    finally:
        root.handlers[:], root.level = saved


@pytest.mark.parametrize(
    "environment, requested, expected",
    [("local", False, True), ("prod", False, False), ("prod", True, True), ("local", True, True)],
)
def test_debug_rule(monkeypatch, environment, requested, expected):
    monkeypatch.setenv("ENVIRONMENT", environment)
    token = logging_setup.debug_requested_var.set(requested)
    try:
        assert logging_setup.debug_enabled() is expected
    finally:
        logging_setup.debug_requested_var.reset(token)


def test_valid_request_id():
    assert logging_setup.valid_request_id("abc-123_x.y") == "abc-123_x.y"
    for bad in (None, "", "has space", "new\nline", "x" * 65):
        assert logging_setup.valid_request_id(bad) is None


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")


class _Fake:
    async def reply(self, messages):
        return "pong"


async def test_request_id_in_logs_and_debug_header_in_prod(client, json_logs, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "prod")
    app.state.assistant = _Fake()
    try:
        body = {"messages": [{"role": "user", "content": "ping"}]}
        r = await client.post("/chat", json=body, headers={"X-Request-ID": "abc123"})
        assert r.headers["x-request-id"] == "abc123"
        lines = [l for l in json_logs() if l["short_message"].startswith(("chat", "POST /chat"))]  # app records only
        assert len(lines) >= 3 and {l["x-request-id"] for l in lines} == {"abc123"}
        assert not [l for l in lines if l["priority"] == "DEBUG"]  # prod without header: no debug
        access = [l for l in lines if l["short_message"] == "POST /chat 200"]
        assert len(access) == 1 and access[0]["priority"] == "INFO"

        before = len(json_logs())
        await client.post("/chat", json=body, headers={"X-Debugging": "true"})
        assert [l for l in json_logs()[before:] if l["priority"] == "DEBUG" and l["short_message"].startswith("chat")]

        before = len(json_logs())
        await client.post("/chat", json=body, headers={"X-Debugging": "false"})
        assert not [l for l in json_logs()[before:] if l["priority"] == "DEBUG" and l["short_message"].startswith("chat")]
    finally:
        del app.state.assistant


def test_content_logged_only_at_debug(json_logs, monkeypatch):
    secret = "olena1@example.com"
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [{"question": "Q?", "answer": "A.", "score": 0.9}])

    # info only (prod, no header): metadata, no content
    monkeypatch.setenv("ENVIRONMENT", "prod")
    tools.search_faq(Settings(_env_file=None, anthropic_api_key="x"), MagicMock(), secret)
    out = json.dumps(json_logs())
    assert "faq_search" in out and "duration_ms" in out and secret not in out and "A." not in out

    # debug: query and hits are present
    monkeypatch.setenv("ENVIRONMENT", "local")
    tools.search_faq(Settings(_env_file=None, anthropic_api_key="x"), MagicMock(), secret)
    debug = [l for l in json_logs() if l["priority"] == "DEBUG"]
    assert debug and secret in json.dumps(debug) and "A." in json.dumps(debug)


def test_debug_content_is_truncated(json_logs):
    tools._log_step("s", "ok", 0.0, {"q": "a"}, "x" * 2000)
    debug = [l for l in json_logs() if l["priority"] == "DEBUG"][0]
    assert len(debug["extra"]["result"]) <= 501


def test_quiet_libraries_never_log_debug(json_logs):
    logging.getLogger("httpcore.http11").debug("send_request_headers.started")
    logging.getLogger("httpcore.http11").info("kept")
    logging.getLogger("app.x").debug("mine")
    messages = [l["short_message"] for l in json_logs()]
    assert "send_request_headers.started" not in messages and "kept" in messages and "mine" in messages
