# Proposal

## Why

The idle `mysql` container is kept for a future user-data API, but that API will need only 1-2 tables. A separate MySQL server (image, root and read-only passwords, healthcheck, volume) is too heavy for that; an embedded SQLite file is enough and removes a service from the stack.

## What Changes

- Remove the `mysql` service, its healthcheck and the `mysql-data` volume from `docker/docker-compose.yml`.
- Remove `MYSQL_*` variables from `.env.example`; the only secret left is `ANTHROPIC_API_KEY`.
- The future user-data store is an SQLite file inside the `ai-service` environment, not a separate container. No schema, seed or code is added now.
- Update `README.md` and `CLAUDE.md`: the architecture no longer lists an idle `mysql` service.
- **BREAKING**: operators must drop the old `mysql-data` volume (`make down` / `make rebuild` already do) and may delete `MYSQL_*` from their `.env` (unused values are ignored).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `demo-deployment`: the stack runs `ai-service` and `vector-db` only; secrets are just the Claude API key; no database container.

## Impact

- `docker/docker-compose.yml`, `.env.example`, `README.md`, `CLAUDE.md`, `openspec/specs/demo-deployment/spec.md` (via archive).
- No change in `ai-service` code, API or dependencies (Python's stdlib `sqlite3` is enough later).
- Out of scope: the user-data API itself, its tables, and the FAQ/frontend texts that mention MySQL as Vadym's skill (`faq.sample.json`, `frontend/index.html`); `.agents/decisions/*` and archived changes stay as history.
