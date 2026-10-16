# Design

## Context

Greenfield repo: no code, compose file or dependency manifests exist (verified in `CLAUDE.md` and `git status`). Service roles come from `docs/prepare/setup.md` and the decision log `.agents/decisions/demo-ai-assistant-ecosystem.md`. See proposal.md for motivation.

```
chat bot ──HTTP──▶ ai-service (FastAPI + LangChain agent)
(external)          ├─▶ search_faq ─────▶ Qdrant (vector-db)
                    └─▶ MCP client ─HTTP─▶ mcp-server (PHP 8 + Swoole) ─▶ MySQL
```

## Goals / Non-Goals

**Goals:**
- Fixed service boundaries and contracts so each service can be built independently.
- A self-contained demo: one `docker compose up`, one external secret (Claude API key).
- Adding FAQ data later requires no architectural change.

**Non-Goals:**
- Production hardening: authentication, authorization, rate limiting, TLS.
- Streaming, session storage, write operations on MySQL.

## Decisions

1. **Agent with two tools (tool calling), LLM decides.** `search_faq` and the MCP tools are registered on a LangChain agent. *Alternatives:* RAG always + MCP when needed (wasteful Qdrant search on "hi"); a router before answering (extra LLM step, poor on complex requests).
2. **Claude API as the LLM.** Reliable tool calling, single secret. *Alternatives:* OpenAI (second ecosystem), Ollama (weaker tool calls, hardware needs).
3. **Single non-streaming response, `POST /chat` with `{messages:[{role,content}]}` → `{reply}`.** Simplest contract for an external bot. *Alternative:* SSE.
4. **Stateless `ai-service`.** The bot resends history. No session store, no state lost on restart. *Alternative:* `session_id` + server-side history.
5. **Local embeddings: `intfloat/multilingual-e5-large` via fastembed**, 1024 dims, cosine, `query:`/`passage:` prefixes. No second API key; multilingual (FAQ likely Ukrainian). *Alternatives:* external embedding API, `paraphrase-multilingual-mpnet-base-v2` (768, lower quality). Model is baked into the image at build time (preferred) or cached in a named volume.
6. **MCP over HTTP.** `ai-service` is the MCP client, `mcp-server` the MCP server, since they run in separate containers. The `ai-service` MCP tools are loaded via a LangChain MCP adapter. The PHP side implements the MCP HTTP transport (library if a suitable one exists for Swoole, otherwise a minimal JSON-RPC handler for `initialize`, `tools/list`, `tools/call`) — **Spike outcome:** a minimal hand-written JSON-RPC handler on `Swoole\Http\Server` (`initialize`, `ping`, `tools/list`, `tools/call`, notifications → 202). The server needs only two read-only tools and JSON responses (no SSE, sessions or auth), the handler is ~100 lines, and it avoids bridging a PSR-7-based SDK into Swoole's request/response objects. Endpoint: `POST /mcp`, plus `GET /health`.
7. **Tool errors as tool results.** MCP/Qdrant failures are caught in the tool wrappers and returned as text so the LLM explains them; only Claude API failure becomes HTTP 5xx.
8. **Read-only MySQL.** `mcp-server` connects with a dedicated user granted `SELECT` only. Schema/seed live in an init SQL mounted into the `mysql` container (`/docker-entrypoint-initdb.d`).
9. **Idempotent Qdrant seed script.** Creates the collection if missing and upserts with stable IDs (e.g. UUIDv5 from entry key). Runs as a one-shot command in the `ai-service` image; collection starts empty. `search_faq` treats a missing/empty collection as zero results.
10. **Network.** One compose network; only `ai-service` publishes a port. Compose `depends_on` with healthchecks orders startup. Secrets via `.env` (+ `.env.example`).

Proposed layout: `ai-service/`, `mcp-server/`, `db/init/`, `docker-compose.yml`, `.env.example`.

## Risks / Trade-offs

- [No access control: any user's data retrievable by ID/email] → Acceptable for fake demo data; documented in README, production needs authorization.
- [~2.2 GB embedding model enlarges image and slows first build/start] → Bake into image so runtime has no download; keep the 10 GB limit in mind.
- [Swoole MCP support may be immature] → Early spike; fallback to a minimal hand-written JSON-RPC MCP endpoint.
- [Prompt injection via tool data could steer the agent] → Data is fake and tools are read-only, so impact is limited; the system prompt treats tool output as data.
- [Stateless history grows with each request] → Bot responsibility; `ai-service` may cap the number of accepted messages.
