# Seeding the FAQ (RAG)

The Qdrant collection `faq` (1024 dims, cosine) starts empty. Chat works without it; `search_faq` simply returns no results.

Entries file format (JSON list; `key` must be unique and stable — it determines the point ID):

```json
[{"key": "password-reset", "question": "Як скинути пароль?", "answer": "..."}]
```

Run the seed script inside the `ai-service` container (idempotent: safe to re-run, no duplicates):

```bash
# only ensure the empty collection exists
docker compose run --rm ai-service python -m scripts.seed_faq

# load entries (the sample file demonstrates the mechanism)
docker compose run --rm ai-service python -m scripts.seed_faq data/faq.sample.json
```

To load your own file, place it in `ai-service/data/` and rebuild the image.
Texts are embedded locally with `intfloat/multilingual-e5-large` (`passage:` prefix for indexing, `query:` for search).
