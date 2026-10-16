import logging
from typing import Literal

from anthropic import APIError
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.agent import Assistant
from app.settings import get_settings

log = logging.getLogger("ai-service")
settings = get_settings()  # fail fast on missing configuration (e.g. ANTHROPIC_API_KEY)

app = FastAPI(title="ai-service")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=settings.max_messages)


class ChatResponse(BaseModel):
    reply: str


def get_assistant(request: Request) -> Assistant:
    if not hasattr(request.app.state, "assistant"):
        request.app.state.assistant = Assistant(settings)
    return request.app.state.assistant


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    if body.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="The last message must have role 'user'.")
    try:
        reply = await get_assistant(request).reply([m.model_dump() for m in body.messages])
    except APIError as exc:
        log.exception("Claude API failure")
        raise HTTPException(status_code=502, detail="The language model is unavailable.") from exc
    return ChatResponse(reply=reply)
