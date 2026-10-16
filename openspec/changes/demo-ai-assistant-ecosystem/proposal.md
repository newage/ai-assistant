# Proposal

## Why

The repository is an empty scaffold; the AI assistant ecosystem (chat bot, Python orchestrator, vector DB, PHP MySQL service) exists only as notes. Service boundaries and contracts must be fixed before `docker-compose.yml` and implementation can start, otherwise they get decided by accident during coding. The result is needed for a demonstration on a demo website.

## What Changes

- Add `ai-service` (Python + FastAPI + LangChain): a stateless agent exposing `POST /chat`; the LLM (Claude API) decides via tool calling whether to call `search_faq` (Qdrant RAG) and/or MCP tools.
- Add `mcp-server` (PHP 8 + Swoole): a real MCP server over HTTP with two read-only tools, `find_user_profile` (by ID or email) and `get_user_activity` (by ID), backed by MySQL.
- Add `vector-db` (Qdrant) with an idempotent seed script that creates the collection (1024 dims, cosine) and upserts FAQ entries with stable IDs. The collection starts empty.
- Add local embeddings (`intfloat/multilingual-e5-large` via fastembed) inside `ai-service`, using the `query:` / `passage:` prefixes.
- Add `mysql` with a minimal schema (`users`, `user_activity`) and a seed of fake data (tens of users).
- Add `docker-compose.yml` assembling `ai-service`, `vector-db`, `mcp-server`, `mysql`, with secrets in `.env`. Only `ai-service` is exposed externally.
- The chat bot is an external client and is out of the repo.

Out of scope: the chat bot itself, streaming responses, server-side session storage, authentication/access control (data is fake, demo only), real FAQ content, write access to MySQL.

## Capabilities

### New Capabilities
- `chat-api`: the `POST /chat` contract with the external bot (messages in, `{reply}` out, stateless) and the tool-calling agent behavior, including error handling.
- `faq-retrieval`: embedding model, Qdrant collection configuration, idempotent seeding and the `search_faq` tool, including behavior while the collection is empty.
- `user-data-mcp`: the MCP server's `find_user_profile` and `get_user_activity` tools, read-only MySQL access, and the demo schema and seed data.
- `demo-deployment`: the docker-compose composition, network exposure rules, and `.env` configuration.

### Modified Capabilities
<!-- None: no specs exist yet. -->

## Impact

- New code and directories: `ai-service/`, `mcp-server/`, `docker-compose.yml`, `.env.example`, MySQL init/seed SQL, Qdrant seed script.
- Dependencies: FastAPI, LangChain, Anthropic SDK, MCP client, fastembed, qdrant-client; PHP 8 with Swoole and an MCP server library or hand-rolled HTTP MCP; MySQL; Qdrant.
- External service: Claude API (single secret, `ANTHROPIC_API_KEY`).
- `ai-service` image grows by ~2.2 GB (embedding model); first start is longer unless the model is baked in or the cache is a volume.
- Known risk, accepted for the demo: any user's data can be retrieved by ID or email without authorization.
