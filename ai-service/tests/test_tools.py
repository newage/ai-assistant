from unittest.mock import MagicMock

import pytest

from app import tools
from app.settings import Settings


def _settings():
    return Settings(_env_file=None, anthropic_api_key="x")


def _hit(score):
    return {"text": "A.", "score": score}


def test_strong_hit_counts_and_weak_one_is_dropped(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [_hit(0.9), _hit(0.5)])
    assert tools.search_faq(_settings(), MagicMock(), "q") == [_hit(0.9)]


def test_weak_hits_are_not_data(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [_hit(0.79), _hit(0.5)])
    assert tools.search_faq(_settings(), MagicMock(), "q") == []


def test_empty_search_gives_no_hits(monkeypatch):
    monkeypatch.setattr(tools.faq, "search", lambda *a, **k: [])
    assert tools.search_faq(_settings(), MagicMock(), "hi") == []


def test_search_failure_raises_faq_search_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(tools.faq, "search", boom)
    with pytest.raises(tools.FaqSearchError):
        tools.search_faq(_settings(), MagicMock(), "hi")
