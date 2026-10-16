import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.embeddings import VECTOR_SIZE, embed_passages, embed_query

log = logging.getLogger(__name__)

_NAMESPACE = uuid.UUID("6f1c2d3e-8a4b-4c5d-9e0f-1a2b3c4d5e6f")


def point_id(key: str) -> str:
    """Stable point ID derived from the entry key, so re-seeding never duplicates."""
    return str(uuid.uuid5(_NAMESPACE, key))


def ensure_collection(client: QdrantClient, name: str) -> bool:
    """Create the collection (1024 dims, cosine) if missing. Returns True if created."""
    if client.collection_exists(name):
        return False
    client.create_collection(name, vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE))
    return True


def upsert_entries(client: QdrantClient, name: str, entries: list[dict]) -> int:
    """Upsert FAQ entries `{key, question, answer}`; idempotent thanks to stable IDs."""
    ensure_collection(client, name)
    if not entries:
        return 0
    texts = [f"{e['question']}\n{e['answer']}" for e in entries]
    vectors = embed_passages(texts)
    client.upsert(
        name,
        points=[
            PointStruct(
                id=point_id(e["key"]),
                vector=vec,
                payload={"key": e["key"], "question": e["question"], "answer": e["answer"]},
            )
            for e, vec in zip(entries, vectors, strict=True)
        ],
    )
    return len(entries)


def search(client: QdrantClient, name: str, query: str, top_k: int = 4) -> list[dict]:
    """Return the most relevant FAQ entries; empty if the collection is missing or empty."""
    if not client.collection_exists(name):
        return []
    hits = client.query_points(name, query=embed_query(query), limit=top_k, with_payload=True).points
    return [
        {"question": h.payload["question"], "answer": h.payload["answer"], "score": round(h.score, 4)}
        for h in hits
    ]
