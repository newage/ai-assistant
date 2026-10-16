# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

A demo AI-assistant ecosystem assembled by `docker-compose.yml`. The chat bot is an external client (not in this repo); all its traffic goes only through `ai-service`.

```
chat bot ──HTTP──▶ ai-service (FastAPI + LangChain agent, Claude API)
                    ├─▶ search_faq ─────▶ vector-db (Qdrant)
                    └─▶ MCP client ─HTTP─▶ mcp-server (PHP 8 + Swoole) ─▶ mysql (read-only)
```

- `ai-service/` — Python orchestrator. `POST /chat` takes `{messages:[{role,content}]}` and returns `{reply}` (stateless, no streaming). A LangChain agent lets the LLM decide whether to call `search_faq` and/or the MCP tools. Tool failures are returned to the LLM as text; only a Claude API failure becomes HTTP 502. Embeddings are local (`intfloat/multilingual-e5-large` via fastembed, baked into the image; `query:`/`passage:` prefixes are mandatory).
- `mcp-server/` — PHP/Swoole MCP server (hand-written JSON-RPC at `POST /mcp`) with tools `find_user_profile` and `get_user_activity`. Uses a `SELECT`-only MySQL account.
- `db/init/` — MySQL schema, fake seed data and the read-only user (run by the MySQL image on first start).
- `docs/faq-seeding.md` — how to load FAQ entries into Qdrant (collection starts empty).
- `openspec/` — specs and changes; `.agents/decisions/` holds the decision log.

There is no access control: any user's data can be fetched by ID or email. This is acceptable only because the data is fake.

## Commands

```bash
cp .env.example .env              # then set ANTHROPIC_API_KEY and passwords
docker compose up -d --build      # whole stack; ai-service on http://localhost:${AI_SERVICE_PORT:-8000}
docker compose down -v            # stop and drop data

# ai-service tests (needs Qdrant reachable via QDRANT_URL for the FAQ tests; others run without it)
docker run --rm -v $PWD/ai-service:/srv -w /srv -e QDRANT_URL=http://<qdrant-host>:6333 <ai-service-image> \
  sh -c 'pip install -q -r requirements-dev.txt && python -m pytest -q'
#   single test: python -m pytest tests/test_chat_api.py::test_chat_ok

# mcp-server tests (needs the seeded MySQL; DB_HOST/DB_NAME/DB_USER/DB_PASSWORD env)
docker run --rm -v $PWD/mcp-server:/app -w /app -e DB_HOST=... -e DB_NAME=demo -e DB_USER=readonly -e DB_PASSWORD=... \
  phpswoole/swoole:php8.3-alpine sh -c 'composer install -q && vendor/bin/phpunit'
#   single test: vendor/bin/phpunit --filter testLookupByEmail
```
