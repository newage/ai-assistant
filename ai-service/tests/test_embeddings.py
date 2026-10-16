from app import embeddings


def test_real_model_returns_1024_dims():
    assert len(embeddings.embed_query("як скинути пароль")) == 1024
    assert all(len(v) == 1024 for v in embeddings.embed_passages(["a", "b"]))


def test_prefixes_are_applied(monkeypatch):
    seen = []
    monkeypatch.setattr(embeddings, "_embed", lambda texts: seen.extend(texts) or [[0.0]] * len(texts))
    embeddings.embed_query("hello")
    embeddings.embed_passages(["doc1", "doc2"])
    assert seen == ["query: hello", "passage: doc1", "passage: doc2"]
