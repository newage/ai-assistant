import logging
import time
import uuid
from typing import Literal

from anthropic import APIError
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.agent import Assistant
from app.logging_setup import debug_requested_var, request_id_var, truncate, valid_request_id
from app.settings import get_settings
from app.tools import FaqSearchError

log = logging.getLogger("ai-service")
access_log = logging.getLogger("ai-service.access")
settings = get_settings()  # fail fast on missing configuration (e.g. ANTHROPIC_API_KEY)

app = FastAPI(title="ai-service")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=settings.max_message_chars)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=settings.max_messages)


class ChatResponse(BaseModel):
    reply: str


def get_assistant(request: Request) -> Assistant:
    if not hasattr(request.app.state, "assistant"):
        request.app.state.assistant = Assistant(settings)
    return request.app.state.assistant


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Resolve the request id and debug flag, expose the id in the response, log the access line."""
    request_id = valid_request_id(request.headers.get("x-request-id")) or uuid.uuid4().hex
    id_token = request_id_var.set(request_id)
    debug_token = debug_requested_var.set(request.headers.get("x-debugging") == "true")
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("Unhandled error")
        raise
    else:
        response.headers["X-Request-ID"] = request_id
        if request.url.path != "/health":  # the container healthcheck would flood the log
            access_log.info(
                "%s %s %s", request.method, request.url.path, response.status_code,
                extra={"status": response.status_code, "duration_ms": round((time.perf_counter() - started) * 1000, 1)},
            )
        return response
    finally:
        request_id_var.reset(id_token)
        debug_requested_var.reset(debug_token)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="The last message must have role 'user'.")
    messages = [m.model_dump() for m in body.messages]
    started = time.perf_counter()
    log.info("chat request", extra={"messages_count": len(messages)})
    log.debug("chat request content", extra={"messages": [truncate(m["content"]) for m in messages]})
    try:
        reply = await get_assistant(request).reply(messages)
    except FaqSearchError as exc:
        raise HTTPException(status_code=502, detail="The FAQ search is unavailable.") from exc
    except APIError as exc:
        log.exception("Claude API failure")
        raise HTTPException(status_code=502, detail="The language model is unavailable.") from exc
    log.info("chat reply", extra={"duration_ms": round((time.perf_counter() - started) * 1000, 1)})
    log.debug("chat reply content", extra={"reply": truncate(reply)})
    return ChatResponse(reply=reply)
