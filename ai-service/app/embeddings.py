from functools import lru_cache

from fastembed import TextEmbedding

from app.embeddings_model import MODEL_NAME, VECTOR_SIZE

__all__ = ["VECTOR_SIZE", "embed_passages", "embed_queries", "embed_query"]


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def _embed(texts: list[str]) -> list[list[float]]:
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a search text. e5 models require the `query: ` prefix."""
    return _embed([f"query: {text}"])[0]


def embed_queries(texts: list[str]) -> list[list[float]]:
    """Embed question-like texts for indexing, symmetric to the user's query (`query: ` prefix on both sides)."""
    return _embed([f"query: {t}" for t in texts])


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed texts for indexing. e5 models require the `passage: ` prefix."""
    return _embed([f"passage: {t}" for t in texts])
