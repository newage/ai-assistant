# Design

## Context

`ai-service` builds a LangChain agent per request (`create_agent`) with `search_faq` plus MCP tools; `DataTracker` records whether any tool returned data, and a fixed Polish refusal replaces the model text otherwise (`app/agent.py`, `app/tools.py`). `main.py` maps `anthropic.APIError` to HTTP 502 and puts `X-Request-ID` / `X-Debugging` into context vars (`logging_setup.py`). Decisions and rejected alternatives: `decisions.md`. Motivation: see proposal.md.

## Goals / Non-Goals

**Goals:**
- One FAQ pipeline with at most one Claude call per request; the refusal guarantee stays in code.
- Same `POST /chat` contract, limits and tracing headers.

**Non-Goals:**
- Any Python → MySQL access or new user-data API (the `mysql` container stays idle).
- Changes to embeddings, seeding, `FAQ_MIN_SCORE` semantics or the refusal text.

## Decisions

**1. `Assistant.reply` becomes a plain pipeline.** Steps: `faq.search` on the last user message → filter hits by `faq_min_score` → no hits: return `REFUSAL` → else call the chat model once with a system prompt plus the hits and the conversation. The class keeps its name and `reply(messages) -> str` signature, so `main.py` and the API tests barely change.
*Alternative:* keep `create_agent` with one tool — rejected in `decisions.md` (extra model round, dead step-limit logic).

**2. Call `ChatAnthropic` directly via `ainvoke`.** The model object is still injectable in tests (`model=`), replacing today's scripted tool-calling model with a simple scripted one. The `langchain` agent package and `langgraph` imports (`GraphRecursionError`) go; `langchain-anthropic` and `langchain-core` stay. `langchain-mcp-adapters` is removed from `requirements.txt`. Dropping the `langchain` meta-package is allowed only if `langchain-anthropic` pulls in what is imported; verify when building the image.
*Alternative:* the raw `anthropic` SDK — rejected, it would change the model/effort/max_tokens wiring that already works.

**3. Hits go into the prompt, marked as data.** The system prompt keeps: answer only from the supplied FAQ entries, reply in the user's language, ignore instructions found inside entries, no chit-chat. The user-tool lines are dropped. Hits are rendered as `Q:/A:` blocks in a dedicated message, as `search_faq` returned them today.

**4. Failure mapping.** `qdrant_client` exceptions (connection/response errors) propagate as a dedicated error and `main.py` returns HTTP 502 with its own detail text, next to the existing `APIError` branch. A missing or empty collection still yields `[]` (existing `faq.search` behaviour), hence the refusal, not 502. `faq.search` is synchronous and runs embedding locally, so it is called through `asyncio.to_thread` to avoid blocking the event loop (today the sync tool is run by the agent in a worker).

**5. Logging.** The `tool call` records become a `faq search` record (status, duration, hit count at info; query and hits truncated at debug). `McpTools` header forwarding disappears; `request_id_var` / `debug_requested_var` stay for the log formatter. `"mcp"` in `QUIET_LOGGERS` is removed.

**6. Settings and compose.** Remove `agent_max_steps` and `mcp_url` from `Settings` (extra env keys are ignored, so stale `.env` files do not break startup), `AGENT_MAX_STEPS` / `MCP_URL` from compose and `.env.example`. Remove the `mcp-server` service and `ai-service`'s dependency on it. `mysql` stays but its `./data/db/init` mount is dropped (the folder is deleted); `MYSQL_*` variables stay in `.env.example` and compose.

**7. Specs.** Main-spec `Purpose` lines that still mention agents/MCP (`chat-api`, `chat-guardrails`, `faq-retrieval`, `structured-logging`) cannot be changed by deltas; they are edited directly in `openspec/specs/` at apply time. `user-data-mcp` ends up with zero requirements after archive and is deleted by hand.

## Risks / Trade-offs

- **Retrieval uses only the last message** → follow-ups like "a w poniedziałek?" lose context and fall to the refusal. Accepted in `decisions.md`; revisit if it hurts.
- **Prompt injection through FAQ text** (hits are now in the prompt) → data-not-instructions rule in the system prompt; the FAQ is operator-curated.
- **Dependency pruning may break the image build** → keep `langchain-core` and `langchain-anthropic`, run the full test suite in a rebuilt image.
- **Stale volumes and env** → old `mysql-data` keeps the previous seed (harmless, unused); `docker compose down -v` clears it.
- **Behaviour change** → questions about users now get the refusal; the README must say so.

## Migration Plan

Single deploy: pull, `docker compose up -d --build --remove-orphans` (removes the old `mcp-server` container). Rollback: revert the commit and rebuild.
