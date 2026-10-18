# AI Assistant Demo Ecosystem

Demo of an AI assistant: an external chat bot talks to `ai-service`, which answers questions from an FAQ (Qdrant RAG) with a single Claude call.

```
chat bot ──HTTP──▶ ai-service ──▶ vector-db (Qdrant)
```

## Technologies by stage

Following one chat request through the system:

| Stage | Component | Technologies |
|---|---|---|
| 1. Request in | chat bot → `ai-service` | External client, plain HTTP/JSON (`POST /chat`), optional `X-Request-ID` / `X-Debugging` headers |
| 2. Orchestration | `ai-service` | Python, FastAPI; a fixed pipeline: FAQ search, then one Claude call (no agent) |
| 3. FAQ search (RAG) | `ai-service` → `vector-db` | Local embeddings (`intfloat/multilingual-e5-large` via fastembed, baked into the image), Qdrant vector database |
| 4. Reasoning | Claude API | Anthropic Claude (`CLAUDE_MODEL`, default Haiku 5.5, with `CLAUDE_EFFORT`) |
| 5. Response out | `ai-service` → chat bot | `{"reply": "..."}`; a Claude API or Qdrant failure gives HTTP 502; with no relevant FAQ entry the reply is a fixed refusal and Claude is not called |

Cross-cutting:

- **Packaging and runtime:** Docker and Docker Compose (the whole stack, one command).
- **Logging and tracing:** one JSON object per line on stdout, Docker `json-file` rotation, `X-Request-ID` and `X-Debugging` request headers.
- **Tests:** pytest (`ai-service`).
- **Specs and decisions:** OpenSpec (`openspec/`) and the decision log in `.agents/decisions/`.

## Quick start

```bash
cp .env.example .env     # set ANTHROPIC_API_KEY
make up                  # docker/docker-compose.yml, reads .env
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Czym dokładnie się zajmujecie?"}]}'
```

`POST /chat` takes the full conversation (`messages: [{role: user|assistant, content, lang?}]`, last one from the user) and returns `{"reply": "..."}`. The service is stateless, so the bot resends the history each time. A Claude API or Qdrant failure gives HTTP 502. Questions the FAQ cannot answer (including questions about users) get a fixed refusal in the language given by the last message's optional `lang` (`uk`, `en` or `pl`; default `en`).

Model settings in `.env`: `CLAUDE_MODEL` (default `claude-haiku-5-5`) and `CLAUDE_EFFORT` (default `low`; allowed `low|medium|high|xhigh|max`, empty = the model's API default). An invalid value stops `ai-service` at startup; a level the chosen model does not support gives HTTP 502. If you switch to another model (e.g. Sonnet), set `CLAUDE_EFFORT` explicitly.

The first image build downloads the ~2.2 GB embedding model; later builds and starts do not.

## FAQ data

The Qdrant collection `faq` (1024 dims, cosine) starts empty. Chat works without it; every question then gets the refusal.

Entries file format (JSON list; `key` must be unique and stable — it determines the point ID):

```json
[{"key": "password-reset", "question": "...?", "answer": "..."}]
```

Run the seed script inside the `ai-service` container (idempotent: safe to re-run, no duplicates):

```bash
# only ensure the empty collection exists
docker compose run --rm ai-service python -m scripts.seed_faq

# load entries (the sample file demonstrates the mechanism)
docker compose run --rm ai-service python -m scripts.seed_faq data/faq.sample.json
```

To tune `FAQ_MIN_SCORE` after changing the FAQ, print the best-hit score of fixed in-topic and off-topic questions (en/uk/pl):

```bash
docker compose run --rm ai-service python -m scripts.measure_faq_score
```

To load your own file, place it in `ai-service/data/` and rebuild the image. Texts are embedded locally with `intfloat/multilingual-e5-large` (`passage:` prefix for indexing, `query:` for search).

## Resetting data

Qdrant keeps its collection between restarts. To replace the FAQ data (old data is dropped), remove the volumes and seed again:

```bash
make rebuild   # down -v (drops qdrant-data), up --build, seed the sample FAQ
```

`--build` is needed because `data/faq.sample.json` is baked into the image.

## Demo caveat

There is **no access control or rate limiting**; the FAQ is the only data source. Only `ai-service` publishes a host port. The future user-data API will use an embedded SQLite file, not a separate database container.

## Development

See `CLAUDE.md` for test commands and architecture notes; specs live in `openspec/`. Design decisions and their rationale: [.agents/decisions/demo-ai-assistant-ecosystem.md](.agents/decisions/demo-ai-assistant-ecosystem.md).
