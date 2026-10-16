# Tasks

## 1. MySQL schema and seed data

- [x] 1.1 Create `db/init/01-schema.sql` with `users` and `user_activity` tables and verify it applies cleanly in a throwaway MySQL container
- [x] 1.2 Create `db/init/02-seed.sql` with tens of fake users and their activity, and verify row counts via `SELECT COUNT(*)`
- [x] 1.3 Create `db/init/03-readonly-user.sh` with a `SELECT`-only account and verify an `INSERT` as that user is denied

## 2. mcp-server (PHP 8 + Swoole)

- [x] 2.1 Spike: choose a PHP MCP library vs. a minimal JSON-RPC handler on Swoole; record the choice in `design.md` and verify `initialize` and `tools/list` respond over HTTP
- [x] 2.2 Scaffold `mcp-server/` (composer.json, Dockerfile, Swoole HTTP server, env-based DB config) and verify the container builds and starts
- [x] 2.3 Implement `find_user_profile` (by ID or email, not-found and no-identifier results) and verify with PHPUnit tests against seeded MySQL
- [x] 2.4 Implement `get_user_activity` (by user ID, unknown-user result) and verify with PHPUnit tests
- [x] 2.5 Verify `tools/list` returns exactly the two tools and document the server in `mcp-server/README.md`, checking the documented curl call works

## 3. ai-service foundation

- [x] 3.1 Scaffold `ai-service/` (pyproject/requirements, Dockerfile, FastAPI app, settings from env, health endpoint) and verify `GET /health` returns 200 in the container
- [x] 3.2 Make the service fail fast with a clear error when the Claude API key is missing, and verify with a unit test

## 4. FAQ retrieval

- [x] 4.1 Implement the embedding module (`intfloat/multilingual-e5-large`, `query:`/`passage:` prefixes) and verify a unit test sees 1024-dim vectors with correct prefixes
- [x] 4.2 Bake the model into the Docker image (or configure a cache volume) and verify a restart makes no network download
- [x] 4.3 Implement the idempotent seed script (create collection 1024/cosine if missing, upsert with stable IDs) and verify running it twice yields no duplicates
- [x] 4.4 Implement the `search_faq` tool, returning empty results for an empty or missing collection, and verify with integration tests against Qdrant including the empty case
- [x] 4.5 Add a small sample FAQ file used only by tests and document how to add real FAQ entries in `docs/faq-seeding.md`, verifying the documented command runs as written

## 5. Agent and chat API

- [x] 5.1 Implement the MCP client wiring so MCP tools are loaded from `mcp-server` over HTTP, and verify tool discovery lists both tools
- [x] 5.2 Implement tool wrappers that convert MCP/Qdrant failures into tool-result text, and verify with unit tests for unavailable-server and not-found cases
- [x] 5.3 Implement the LangChain agent with Claude, the system prompt, `search_faq` and the MCP tools, and verify with a mocked-LLM test that tool calls are routed correctly
- [x] 5.4 Implement `POST /chat` (request validation, stateless history, `{reply}` response, 5xx on Claude API failure) and verify with API tests for 200, 422 and 5xx
- [x] 5.5 Verify with a mocked LLM that a greeting triggers no tool calls

## 6. Compose assembly

- [x] 6.1 Write `docker-compose.yml` with `ai-service`, `vector-db`, `mcp-server`, `mysql`, a shared network, healthchecks and `depends_on` conditions, and verify `docker compose config` passes
- [x] 6.2 Publish only the `ai-service` port, and verify with `docker compose ps` that no other service exposes host ports
- [x] 6.3 Add `.env.example` (Claude key, DB passwords, ports) and `.gitignore` entry for `.env`, and verify `.env` is ignored by git
- [x] 6.4 Update `CLAUDE.md` with real build, run and single-test commands and architecture, and verify the commands run as written

## 7. End-to-end verification

- [x] 7.1 From empty volumes run `docker compose up` and verify all services become healthy without manual restarts
- [x] 7.2 Verify via `curl POST /chat` that a profile question by email and an activity question by ID return correct data from the seed
- [x] 7.3 Verify a "user not found" question and a stopped `mcp-server` both yield an HTTP 200 with an honest explanation
- [x] 7.4 Verify chat works with the empty FAQ collection, then seed the sample FAQ and verify an FAQ question is answered from it
- [x] 7.5 Write the root `README.md` (quick start, architecture, demo caveat about no access control) and verify a fresh clone follows it successfully
