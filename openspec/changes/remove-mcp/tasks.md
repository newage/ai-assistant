# Tasks

## 1. Remove the MCP server and demo data

- [x] 1.1 Delete `mcp-server/` and `data/db/init/`; verify `git status` shows only those paths deleted and `grep -ri "mcp-server\|data/db/init" --exclude-dir=.git --exclude-dir=openspec --exclude-dir=.agents .` leaves only files handled by later groups
- [x] 1.2 Update `docker-compose.yml`: remove the `mcp-server` service, its `depends_on` entry and the `MCP_URL` / `AGENT_MAX_STEPS` variables of `ai-service`, drop the `./data/db/init` mount from `mysql`; verify `docker compose config` succeeds and lists `ai-service`, `vector-db`, `mysql`
- [x] 1.3 Remove `AGENT_MAX_STEPS` from `.env.example` (keep `MYSQL_*`); verify `docker compose config` still passes with a copy of `.env.example`

## 2. FAQ pipeline in ai-service

- [x] 2.1 Rewrite `ai-service/app/agent.py` as the direct pipeline (search via `asyncio.to_thread`, filter by `faq_min_score`, `REFUSAL` without a model call when nothing counts, otherwise one `ainvoke` with the grounded system prompt); verify with new unit tests in `tests/test_agent.py`: FAQ hit → one model call and its text returned, greeting/off-topic/weak hits/empty collection → `REFUSAL` and zero model calls, user-data question → `REFUSAL`
- [x] 2.2 Reduce `app/tools.py` to FAQ search helpers and the `faq search` log record (info: status, duration, hit count; debug: query and hits truncated); delete `McpTools`, `_guard_mcp_tool`, `DataTracker`; verify with updated `tests/test_tools.py` and `tests/test_logging.py` (info level has no query text, debug level has it)
- [x] 2.3 Map Qdrant connection/response failures to HTTP 502 in `app/main.py` without calling Claude; verify with a `tests/test_chat_api.py` case that stubs a failing search and asserts 502, no model call and the `X-Request-ID` header present
- [x] 2.4 Remove `agent_max_steps` and `mcp_url` from `app/settings.py` and the `"mcp"` entry from `QUIET_LOGGERS`; verify `tests/test_settings.py` (invalid token limit and effort still fail startup, a leftover `AGENT_MAX_STEPS` env var is ignored)
- [x] 2.5 Drop `langchain-mcp-adapters` (and `langchain`/`langgraph` imports if unused) from `requirements.txt`; verify `grep -rn "mcp\|langgraph\|create_agent" ai-service/app ai-service/tests` is empty and the image builds
- [x] 2.6 Run the full ai-service suite as in `CLAUDE.md` (with Qdrant reachable); verify all tests pass, including `test_faq.py` and `test_embeddings.py`

## 3. Specs and docs

- [x] 3.1 Update `README.md` (diagram, stage table, quick start example question, "Resetting data", demo caveat now saying user questions are refused) and `CLAUDE.md` (architecture block, `ai-service` and `mcp-server` bullets, logging forwarding sentence, mcp-server test command); verify no mention of MCP/PHP/Swoole remains in them
- [x] 3.2 Replace the user-data request in `data/http/chat.http` with an FAQ question; verify against the running stack that it returns an FAQ-based answer
- [x] 3.3 Run `openspec validate remove-mcp --strict`; verify it passes
- [x] 3.4 Edit the `Purpose` lines of `chat-api`, `chat-guardrails`, `faq-retrieval` and `structured-logging` in `openspec/specs/` so they no longer mention agents, tools or `mcp-server`; verify with `sed -n 3,5p openspec/specs/<spec>/spec.md` for each (the remaining MCP/agent mentions are requirement bodies that the deltas replace at archive)

## 4. Integration check

- [x] 4.1 `docker compose down -v && docker compose up -d --build --wait --remove-orphans`, seed the FAQ, then verify with `curl`: an FAQ question returns a grounded reply, "Cześć!" and "Show profile olena1@example.com" return the Polish refusal, and stopping `vector-db` gives HTTP 502
- [x] 4.2 Verify with `docker compose logs ai-service` that one request is traceable by `X-Request-ID` and that no `mcp-server` container or port exists (`docker compose ps`)

## Workflow follow-up

- Archive the change after review; then delete the empty `openspec/specs/user-data-mcp/` directory if archive leaves it behind.
