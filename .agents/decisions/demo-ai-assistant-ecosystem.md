# Decision Log: AI Assistant Demo Ecosystem

## Problem
The repository is empty, and the ecosystem of a chat bot, a Python orchestrator, a vector database and a PHP service for MySQL access exists only as notes in `docs/prepare/setup.md`. Until it is fixed how these parts connect and what each one is responsible for, `docker-compose.yml` cannot be assembled and implementation cannot start: the boundaries between services would be decided by accident during coding. The result is needed for a demonstration on a demo website.

## Given
- The repo is an empty scaffold with no code, compose file or dependencies — verified: `CLAUDE.md`, `git status`.
- `docker-compose.yml` assembles the whole ecosystem — verified: `docs/prepare/setup.md`.
- `ai-service` — Python + FastAPI + LangChain, the orchestrator — `docs/prepare/setup.md`.
- `vector-db` — Qdrant for RAG — `docs/prepare/setup.md`.
- `mcp-server` — PHP 8 + Swoole, talks to MySQL — `docs/prepare/setup.md`.
- The chat bot is an external client and is not part of the repo — user's words.
- MySQL runs in compose with fake data (demo) — user's words.
- The MCP is real, with two tools: `find_user_profile` (by ID or email) and `get_user_activity` (by ID) — user's words.
- There is no RAG data yet; FAQ data will be added later — user's words.
- OpenSpec is initialized, no changes exist; this log is kept outside `openspec/` — `openspec/config.yaml`.

## Solution Concept
**Chosen:** an agent with two tools — RAG search (Qdrant) and MCP tools; the LLM decides what to call (tool calling).
**Whose:** generated in the funnel (the developer's idea "the LLM decides when to go to MCP" was considered as variant A)
**Why:** the standard LangChain path, shows MCP best in the demo, and nothing breaks while RAG is empty.
**Rejected:**
- A: RAG always, MCP when needed — an extra Qdrant search on every request, including "hi".
- C: router before answering — an extra LLM step and classes that cover complex requests poorly.

## Vector
```
chat bot ──HTTP──▶ ai-service (FastAPI)
(external)          │  LangChain agent (LLM + tool calling)
                    ├─▶ search_faq ─────▶ Qdrant (vector-db)
                    └─▶ MCP client ─HTTP─▶ mcp-server (PHP 8 + Swoole)
                                            ├ find_user_profile ─▶ MySQL
                                            └ get_user_activity ─▶ MySQL
```
- All chat bot traffic goes only through `ai-service`; Qdrant and `mcp-server` are not exposed externally.
- `ai-service` is the MCP client, `mcp-server` is the MCP server; HTTP transport, since they are in different containers.
- `mcp-server` only reads from MySQL.
- Compose: `ai-service`, `vector-db`, `mcp-server`, `mysql`.

## Details
### Response format to the chat bot
**Decision:** a single response (no streaming).
**Why:** a simpler contract with the external bot.
**Alternative:** SSE streaming — looks livelier in the demo, but a more complex contract; rejected by the developer's choice.

### Agent LLM
**Decision:** Claude API.
**Why:** reliable tool calling, a single secret in `.env`.
**Alternative:** OpenAI API (a foreign ecosystem); Ollama (weaker tool calls, hardware required).

### Embeddings
**Decision:** local multilingual model `intfloat/multilingual-e5-large` via fastembed in `ai-service`. Qdrant collection: dimension 1024, cosine metric. The prefixes `query:` (search) and `passage:` (indexing) are mandatory.
**Why:** no second API key needed, the demo is self-contained, the FAQ is likely in Ukrainian; the model (~2.2 GB) fits the 10 GB limit and gives the best quality among those considered.
**Alternative:** external API (OpenAI/Voyage) — good search quality, but a second secret and a dependency on an external service; `paraphrase-multilingual-mpnet-base-v2` (768) — a lighter image, lower quality.
**Consequence:** the `ai-service` image is ~2 GB larger and the first start is longer; bake the model into the image or mount the cache as a volume. Verified by the developer against the fastembed supported models list: `intfloat/multilingual-e5-large`, 1024, text-only, multilingual, MIT license, 2.24 GB.

### Conversation history
**Decision:** the bot sends the history in every request; `ai-service` is stateless.
**Why:** the bot is external, and compose needs no session store.
**Alternative:** `session_id` + history kept in `ai-service` — a lighter contract for the bot, but a store is needed and sessions are lost on restart.

## Open Questions
- There are no open questions.

## Assumptions
- Contract with the bot: a single endpoint `POST /chat` accepts a list of `{role, content}` messages and returns `{reply}` — non-blocking.
- An MCP tool error (user not found, `mcp-server` unavailable) is returned to the agent as a tool result, and the LLM honestly explains the situation; HTTP 5xx to the bot only if the Claude API itself is unavailable — non-blocking.
- The MySQL schema is minimal: `users(id, email, name, created_at)` and `user_activity(id, user_id, action, created_at)`; fake data is a small seed (tens of users) — non-blocking.
- There is no access control: the agent can show data of any user by ID or email. Acceptable because the data is fake and the service is a demo; production requires authorization.
- Secrets (Claude API key, DB passwords) are passed via `.env` in compose.
- Qdrant is populated by an idempotent seed script (create the collection + upsert with stable IDs); the collection starts empty, and FAQ entries are added later with no architecture changes — non-blocking.
