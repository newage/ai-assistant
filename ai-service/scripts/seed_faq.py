"""Idempotent FAQ seeding: python -m scripts.seed_faq [path/to/faq.json]

Creates the Qdrant collection if missing and upserts entries with stable IDs.
Entries file: JSON list of {"id", "type", "project", "lang", "text", "questions"?}. Without a path the
script only ensures the (empty) collection exists.
"""
import json
import sys
from pathlib import Path

from qdrant_client import QdrantClient

from app.faq import ensure_collection, upsert_entries
from app.settings import get_settings


def main(argv: list[str]) -> None:
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)
    if len(argv) < 2:
        created = ensure_collection(client, settings.faq_collection)
        print(f"collection '{settings.faq_collection}': {'created' if created else 'already exists'}")
        return
    entries = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    ensure_collection(client, settings.faq_collection)
    n = upsert_entries(client, settings.faq_collection, entries)
    print(f"upserted {n} entries into '{settings.faq_collection}'")


if __name__ == "__main__":
    main(sys.argv)
