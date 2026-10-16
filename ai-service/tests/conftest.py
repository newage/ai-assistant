import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from qdrant_client import QdrantClient


class ScriptedModel(BaseChatModel):
    """Chat model returning scripted AIMessages in order; records how often it was called."""

    script: list[AIMessage]
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


@pytest.fixture
def qdrant():
    """Qdrant for integration tests (QDRANT_URL); collection names are unique per test."""
    url = os.environ.get("QDRANT_URL")
    if not url:
        pytest.skip("QDRANT_URL not set")
    return QdrantClient(url=url)


@pytest.fixture
def collection(qdrant, request):
    name = f"test_{request.node.name}".lower()[:60]
    if qdrant.collection_exists(name):
        qdrant.delete_collection(name)
    yield name
    if qdrant.collection_exists(name):
        qdrant.delete_collection(name)
