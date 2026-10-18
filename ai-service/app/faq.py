import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchAny, PointStruct, VectorParams

from app.embeddings import VECTOR_SIZE, embed_passages, embed_queries, embed_query

log = logging.getLogger(__name__)

_POINTS_FETCH_FACTOR = 6  # roughly 1 text + up to 5 questions per entry
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
    """Upsert FAQ entries `{id, type, project, lang, text, questions?}`; idempotent thanks to stable IDs.

    Each entry becomes several points sharing one payload: one for its `text` (embedded as a passage)
    and one per question (embedded as a query, so a user question matches a question, not a paragraph).
    """
    ensure_collection(client, name)
    if not entries:
        return 0
    client.delete(name, points_selector=Filter(must=[FieldCondition(key="id", match=MatchAny(any=[e["id"] for e in entries]))]))
    payloads, passages, questions = [], [], []
    for e in entries:
        payload = {k: e.get(k) for k in ("id", "type", "project", "lang", "text")}
        payloads.append((point_id(e["id"]), payload))
        passages.append(e["text"])
        for i, q in enumerate(e.get("questions") or []):
            questions.append((point_id(f"{e['id']}#q{i}"), payload, q))
    vectors = embed_passages(passages)
    points = [PointStruct(id=pid, vector=vec, payload=p) for (pid, p), vec in zip(payloads, vectors, strict=True)]
    if questions:
        qvectors = embed_queries([q for _, _, q in questions])
        points += [PointStruct(id=pid, vector=vec, payload=p) for (pid, p, _), vec in zip(questions, qvectors, strict=True)]
    client.upsert(name, points=points)
    return len(entries)


def search(client: QdrantClient, name: str, query: str, top_k: int = 4) -> list[dict]:
    """Return the most relevant FAQ entries (best point per entry); empty if the collection is missing or empty."""
    if not client.collection_exists(name):
        return []
    # an entry has several points (text + questions), so over-fetch before collapsing them per entry
    points = client.query_points(name, query=embed_query(query), limit=top_k * _POINTS_FETCH_FACTOR, with_payload=True).points
    best: dict[str, dict] = {}
    for h in points:
        key = h.payload["id"]
        if key not in best:  # points come sorted by score, so the first one per entry is its best
            best[key] = {"text": h.payload["text"], "score": round(h.score, 4)}
    return list(best.values())[:top_k]
