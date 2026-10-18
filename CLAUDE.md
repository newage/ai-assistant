# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

A demo AI-assistant ecosystem assembled by `docker-compose.yml`. The chat bot is an external client (not in this repo); all its traffic goes only through `ai-service`.

```
chat bot ──HTTP──▶ ai-service (FastAPI, Claude API) ──▶ vector-db (Qdrant)
                                                     mysql (idle, kept for a future user-data API)
```

- `ai-service/` — Python orchestrator. `POST /chat` takes `{messages:[{role,content,lang?}]}` (`lang` ∈ `uk|en|pl`, optional, default `en`) and returns `{reply}` (stateless, no streaming). There is no agent: every request searches the FAQ in Qdrant with the last user message, and only if at least one hit has score ≥ `FAQ_MIN_SCORE` makes one Claude call that answers from those hits. Otherwise (off-topic, greetings, questions about users) the reply is a fixed refusal in the `lang` of the last message (uk/en/pl; HTTP 200) and Claude is not called. A Claude API failure or an unavailable Qdrant becomes HTTP 502. Limits (env): `CLAUDE_MAX_TOKENS` (1024 per Claude call), `MAX_MESSAGES` (4) and `MAX_MESSAGE_CHARS` (500) — violating the last two is HTTP 422. The model and its effort level come from `CLAUDE_MODEL` (default `claude-haiku-5-5`) and `CLAUDE_EFFORT` (default `low`; empty = API default; invalid value fails at startup). Embeddings are local (`intfloat/multilingual-e5-large` via fastembed, baked into the image; `query:`/`passage:` prefixes are mandatory). Each FAQ entry is indexed as several points: its `text` (`passage:`) plus one point per item of its optional `questions` list (`query:`); search collapses them to the best point per entry.
- `mysql` — the container stays in `docker-compose.yml` for a future user-data API; nothing uses it now and it has no schema or seed.
- `openspec/` — specs and changes; `.agents/decisions/` holds the decision log.

## Logging

`ai-service` writes one JSON object per line to stdout; Docker (`json-file`, 1 MB × 2 files) rotates them. Fields: `priority`, `service`, `short_message`, `x-request-id`, `extra`, `timestamp`, `log_id`, `environment` (`LOG_ID` and `ENVIRONMENT` from `.env`).

- `ai-service` takes `X-Request-ID` (`[A-Za-z0-9._-]{1,64}`) or generates one, returns it in the response and puts it into every log line of that request.
- Debug is on when the request has `X-Debugging: true`, or without it when `ENVIRONMENT` is not `prod`. info logs metadata only; debug adds user messages, the FAQ query and hits (truncated to ~500 chars).
- Read logs with `docker compose logs ai-service`; follow one request with `grep <request-id>`.

There is no access control or rate limiting; the FAQ is the only data source.

## Commands

```bash
cp .env.example .env              # then set ANTHROPIC_API_KEY and passwords
make up                           # whole stack (docker/docker-compose.yml); ai-service on http://localhost:${AI_SERVICE_PORT:-8000}
make down                         # stop and drop data
make rebuild                      # down -v, up --build, seed the sample FAQ

# ai-service tests (needs Qdrant reachable via QDRANT_URL for the FAQ tests; others run without it)
docker run --rm -v $PWD/ai-service:/srv -w /srv -e QDRANT_URL=http://<qdrant-host>:6333 <ai-service-image> \
  sh -c 'pip install -q -r requirements-dev.txt && python -m pytest -q'
#   single test: python -m pytest tests/test_chat_api.py::test_chat_ok
```
