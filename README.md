# AI Assistant Demo Ecosystem

Demo of an AI assistant: an external chat bot talks to `ai-service`, whose Claude-powered agent can search an FAQ (Qdrant RAG) and look up demo users via an MCP server backed by MySQL.

```
chat bot ──HTTP──▶ ai-service ──▶ vector-db (Qdrant)
                       └─MCP/HTTP─▶ mcp-server (PHP + Swoole) ──▶ mysql
```

## Technologies by stage

Following one chat request through the system:

| Stage | Component | Technologies |
|---|---|---|
| 1. Request in | chat bot → `ai-service` | External client, plain HTTP/JSON (`POST /chat`), optional `X-Request-ID` / `X-Debugging` headers |
| 2. Orchestration | `ai-service` | Python, FastAPI, LangChain agent; the LLM decides which tools to call |
| 3. Reasoning | Claude API | Anthropic Claude (`CLAUDE_MODEL`, default Haiku 5.5, with `CLAUDE_EFFORT`) |
| 4a. FAQ search (RAG) | `search_faq` → `vector-db` | Local embeddings (`intfloat/multilingual-e5-large` via fastembed, baked into the image), Qdrant vector database |
| 4b. User data | MCP client → `mcp-server` → `mysql` | MCP over HTTP (JSON-RPC at `POST /mcp`), PHP 8 + Swoole, MySQL with a `SELECT`-only account, fake seed data from `db/init/` |
| 5. Response out | `ai-service` → chat bot | `{"reply": "..."}`; Claude API failure gives HTTP 502, tool failures are passed to the LLM as text |

Cross-cutting:

- **Packaging and runtime:** Docker and Docker Compose (the whole stack, one command).
- **Logging and tracing:** one JSON object per line on stdout, Docker `json-file` rotation, `X-Request-ID` forwarded from `ai-service` to `mcp-server`.
- **Tests:** pytest (`ai-service`), PHPUnit (`mcp-server`).
- **Specs and decisions:** OpenSpec (`openspec/`) and the decision log in `.agents/decisions/`.

## Quick start

```bash
cp .env.example .env     # set ANTHROPIC_API_KEY and the DB passwords
docker compose up -d --build --wait
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Show profile olena1@example.com"}]}'
```

`POST /chat` takes the full conversation (`messages: [{role: user|assistant, content}]`, last one from the user) and returns `{"reply": "..."}`. The service is stateless, so the bot resends the history each time. A Claude API failure gives HTTP 502.

Model settings in `.env`: `CLAUDE_MODEL` (default `claude-haiku-5-5`) and `CLAUDE_EFFORT` (default `low`; allowed `low|medium|high|xhigh|max`, empty = the model's API default). An invalid value stops `ai-service` at startup; a level the chosen model does not support gives HTTP 502. If you switch to another model (e.g. Sonnet), set `CLAUDE_EFFORT` explicitly.

The first image build downloads the ~2.2 GB embedding model; later builds and starts do not.

## FAQ data

The FAQ collection starts empty (chat still works). See [docs/faq-seeding.md](docs/faq-seeding.md).

## Resetting data

MySQL runs `db/init/*.sql` only on the first start with an empty volume, and Qdrant keeps its collection between restarts. To replace all data with new seeds (old data is dropped), remove both volumes and seed again:

```bash
docker compose down -v                      # drops mysql-data and qdrant-data
docker compose up -d --build --wait         # MySQL re-runs db/init/*.sql
docker compose run --rm ai-service python -m scripts.seed_faq data/faq.sample.json
```

`--build` is needed because `data/faq.sample.json` is baked into the image.

## Demo caveat

There is **no access control**: the agent can show data of any user by ID or email. This is acceptable only because the data is fake; production needs authorization. Only `ai-service` publishes a host port.

## Development

See `CLAUDE.md` for test commands and architecture notes; specs live in `openspec/`. Design decisions and their rationale: [.agents/decisions/demo-ai-assistant-ecosystem.md](.agents/decisions/demo-ai-assistant-ecosystem.md).
