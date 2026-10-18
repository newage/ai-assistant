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
    assert qdrant.count(collection, exact=True).count == sum(1 + len(e.get("questions", [])) for e in SAMPLE)


def test_search_finds_relevant_entry(qdrant, collection):
    faq.upsert_entries(qdrant, collection, SAMPLE)
    hits = faq.search(qdrant, collection, "is he available to start and work remotely?", top_k=2)
    assert "Availability" in hits[0]["text"]


def test_search_on_empty_collection(qdrant, collection):
    faq.ensure_collection(qdrant, collection)
    assert faq.search(qdrant, collection, "anything") == []


def test_search_on_missing_collection(qdrant, collection):
    assert faq.search(qdrant, collection, "anything") == []


def test_question_points_are_collapsed_per_entry(qdrant, collection):
    faq.upsert_entries(qdrant, collection, SAMPLE)
    hits = faq.search(qdrant, collection, "How can I contact Vadym?", top_k=4)
    assert len(hits) == len({h["text"] for h in hits}) == 4
    assert "Contact" in hits[0]["text"]


def test_reseed_drops_removed_questions(qdrant, collection):
    entry = {"id": "a", "type": "t", "project": None, "lang": "en", "text": "Alpha.", "questions": ["q1?", "q2?"]}
    faq.upsert_entries(qdrant, collection, [entry])
    faq.upsert_entries(qdrant, collection, [{**entry, "questions": ["q1?"]}])
    assert qdrant.count(collection, exact=True).count == 2
