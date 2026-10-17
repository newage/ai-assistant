import json
from pathlib import Path

from app import faq

SAMPLE = json.loads((Path(__file__).parent.parent / "data" / "faq.sample.json").read_text(encoding="utf-8"))


def test_collection_config(qdrant, collection):
    assert faq.ensure_collection(qdrant, collection) is True
    assert faq.ensure_collection(qdrant, collection) is False
    params = qdrant.get_collection(collection).config.params.vectors
    assert params.size == 1024
    assert params.distance.name == "COSINE"


def test_seed_twice_has_no_duplicates(qdrant, collection):
    faq.upsert_entries(qdrant, collection, SAMPLE)
    faq.upsert_entries(qdrant, collection, SAMPLE)
    assert qdrant.count(collection, exact=True).count == len(SAMPLE)


def test_search_finds_relevant_entry(qdrant, collection):
    faq.upsert_entries(qdrant, collection, SAMPLE)
    hits = faq.search(qdrant, collection, "jaka jest cena usługi?", top_k=2)
    assert hits[0]["question"] == "Ile to kosztuje?"


def test_search_on_empty_collection(qdrant, collection):
    faq.ensure_collection(qdrant, collection)
    assert faq.search(qdrant, collection, "anything") == []


def test_search_on_missing_collection(qdrant, collection):
    assert faq.search(qdrant, collection, "anything") == []
