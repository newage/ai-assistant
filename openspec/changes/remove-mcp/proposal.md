# Proposal

## Why

The user-data backend (PHP/Swoole MCP server plus MySQL with fake data) is no longer needed: Python will reach MySQL later through a different API. Meanwhile `ai-service` runs a LangChain agent only to choose between the FAQ and MCP; with one source left there is nothing to choose, and the agent loop costs an extra Claude round per request. Source of decisions: `decisions.md` in this change.

## What Changes

- **BREAKING** Remove `mcp-server/` (PHP + Swoole, tools `find_user_profile` and `get_user_activity`) and `data/db/init/` (schema, seed, read-only user). Questions about users are no longer answered; they get the fixed refusal.
- Replace the agent in `ai-service` with a direct pipeline: embed the last user message → Qdrant top-k → if no hit scores ≥ `FAQ_MIN_SCORE`, return the fixed Polish refusal (HTTP 200, no Claude call) → otherwise one Claude call with the hits in the prompt.
- Qdrant unavailable → HTTP 502 (same as a Claude API failure).
- Remove the MCP client, the "did any tool return data" tracking, `AGENT_MAX_STEPS` and `MCP_URL`; drop `langchain-mcp-adapters` and the agent framework dependency if no longer used.
- Keep `X-Request-ID` / `X-Debugging` in `ai-service` logs; stop forwarding them (nothing to forward to).
- `docker-compose.yml`: remove the `mcp-server` service and `ai-service`'s dependency on it. The `mysql` container, its volume and `MYSQL_*` variables stay for later, but it no longer mounts `data/db/init`.
- Update `README.md`, `CLAUDE.md`, `.env.example`, `data/http/chat.http` and the affected tests.
- `.agents/decisions/*` stay untouched as history.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `chat-api`: replace LLM-driven tool selection and tool-error reporting with the direct FAQ pipeline; Qdrant failure becomes HTTP 502.
- `chat-guardrails`: grounding is defined by FAQ hits above the threshold; remove MCP data rules and the agent step limit; startup validation drops the step limit.
- `faq-retrieval`: FAQ search is a direct pipeline step, not an agent tool.
- `structured-logging`: no cross-service forwarding to `mcp-server`; the request id and debug flag stay in `ai-service` logs.
- `demo-deployment`: stack is `ai-service`, `vector-db`, `mysql`; startup ordering and shared log settings no longer mention `mcp-server`.
- `user-data-mcp`: all requirements removed (the capability goes away).

## Impact

- Code: `ai-service/app/agent.py`, `tools.py`, `settings.py`, `main.py`, `requirements.txt`; deleted `mcp-server/`, `data/db/init/`.
- Tests: `ai-service/tests/test_agent.py`, `test_tools.py`, `test_logging.py`, `test_chat_api.py`, `test_settings.py`; all PHPUnit tests go with `mcp-server/`.
- Config and docs: `docker-compose.yml`, `.env.example`, `README.md`, `CLAUDE.md`, `data/http/chat.http`.
- External contract of `POST /chat` (request/response shape, 422 limits, `X-Request-ID`) is unchanged; only the answers about users and the Qdrant-failure status change.
