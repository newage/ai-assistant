# Design

## Context

Both services currently log nothing structured (see `proposal.md`). `ai-service` is one uvicorn process with stdlib `logging`; `mcp-server` is Swoole with two workers and no logger. `McpTools.load()` already runs on every `reply()`, and `MultiServerMCPClient` connections accept a `headers` map. Settings come from `.env` (pydantic in Python, `getenv` in PHP). Full decision log: `.agents/decisions/logging.md`.

## Goals / Non-Goals

**Goals:**
- One JSON line format in both services, one request id across both.
- Debug switchable per environment and per request.

**Non-Goals:**
- Log files, shared volumes, date-based rotation, a log collector.
- JSON-wrapping Swoole's own system messages.
- Redacting user data; content appears only at debug level.

## Decisions

**Stdout + Docker rotation instead of files.** Both services print JSON; `docker-compose.yml` sets `logging: {driver: json-file, options: {max-size: "1m", max-file: "2"}}`. Alternatives: files in a shared volume (Monolog's `RotatingFileHandler` rotates by date only, and several writers on one file need a custom handler); a sidecar collector (extra container).

**Python: contextvars + a JSON formatter.** A FastAPI middleware resolves the request id (validated `[A-Za-z0-9._-]{1,64}`, else `uuid4().hex`) and the debug flag, stores them in `ContextVar`s, and sets the `X-Request-ID` response header, including on error responses. A logging filter injects the id into each record; a small JSON formatter produces the line (`priority` from `levelname`). Uvicorn is started with a `log_config` that routes its loggers through the same formatter. The root level is `DEBUG` and a filter drops debug records unless the request's flag allows them, so the per-request switch works with one logger tree.

**Debug flag rule.** `debug = (X-Debugging == "true") or (ENVIRONMENT != "prod")`, computed once per request in the middleware. Outside a request (startup) the environment rule applies.

**Headers to MCP.** `McpTools.load()` receives the current request id and debug flag and builds the `MultiServerMCPClient` connection with `headers={"X-Request-ID": ..., "X-Debugging": ...}`. `McpTools` is no longer a long-lived client; it builds one per `reply()`.

**PHP: Monolog, one logger per request.** Add `monolog/monolog`. A `StreamHandler('php://stdout')` with a custom JSON formatter emits the same fields. For each HTTP request `server.php` reads `X-Request-ID` (same validation, `-` when absent) and `X-Debugging`, creates the logger with that id and level (`Debug` or `Info` by the same rule), and passes it to `McpHandler`/`Tools`. Per-request instances avoid sharing mutable state between Swoole coroutines.

**Content logging.** `ai-service` logs the user message, tool arguments and tool results only through `log.debug`, truncated to 500 characters by a helper; info records carry the tool name, duration and status. `mcp-server` follows the same rule for tool arguments and results.

**Env.** `LOG_ID` and `ENVIRONMENT` are added to `Settings` (defaults `local` and `local`) and passed in `docker-compose.yml` to both services; `mcp-server` reads them with `getenv`.

## Risks / Trade-offs

- [Swoole system messages are plain text and mixed into the stream] → accepted; documented, they are rare.
- [Docker rotation keeps only about 2 MB, which debug logs fill quickly] → accepted for a demo; operators can raise `max-size`.
- [Debug in production exposes user data in logs when the header is sent] → debug is explicit; the data in this demo is fake.
- [Uvicorn log config and the context filter could drop or duplicate records] → covered by tests on the emitted lines.
- [Client-supplied ids could inject text into logs] → ids are validated against a strict pattern, otherwise replaced.

## Migration Plan

Deploy by rebuilding the images (`docker compose up -d --build`) after adding `LOG_ID` and `ENVIRONMENT` to `.env`. Rollback: redeploy the previous images; no data is migrated.
