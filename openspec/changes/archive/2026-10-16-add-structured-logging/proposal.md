# Proposal

## Why

`ai-service` and `mcp-server` emit unstructured, error-only output, and a request that crosses both services has no shared identifier, so an incident cannot be traced per request. There is also no controlled way to switch detailed (debug) logging on and off. Decisions are recorded in `.agents/decisions/logging.md`.

## What Changes

- Both services write JSON log lines to stdout; Docker's logging driver stores and rotates them (1 MB, 1 old copy). No log files, shared volume or file handlers.
- Line format: `priority`, `service`, `short_message`, `x-request-id`, `extra`, `timestamp`, plus `log_id` and `environment` from env (`LOG_ID`, `ENVIRONMENT`).
- Levels: critical, error, warning, info, debug. Debug is on when `X-Debugging: true` is sent, or when no such header is sent and `ENVIRONMENT` is not `prod`.
- `ai-service` accepts or generates `X-Request-ID`, returns it in the response, and forwards it (and `X-Debugging`) to `mcp-server`, which adds it to its own logs for that request.
- info logs metadata only; debug additionally logs user messages, tool arguments and results, truncated.
- All Python output (including uvicorn) is JSON; Swoole's own system messages stay plain text.
- Uses `monolog` for PHP and stdlib `logging` for Python.

## Capabilities

### New Capabilities
- `structured-logging`: JSON log format, levels and debug switching, request-id propagation across services, what content is logged at each level.

### Modified Capabilities
- `chat-api`: `POST /chat` accepts `X-Request-ID` and `X-Debugging` request headers and returns `X-Request-ID`.
- `demo-deployment`: logging is configured from env (`LOG_ID`, `ENVIRONMENT`) and container logs are rotated by Docker.

## Impact

- `ai-service`: logging setup, request middleware, MCP client headers per request, uvicorn log config, `settings.py`.
- `mcp-server`: `monolog` dependency (`composer.json`), per-request logger in `server.php`/`McpHandler`.
- `docker-compose.yml` (env for both services, `logging` options), `.env.example`, docs.
- No change to the `POST /chat` body or to the MCP tool contracts.
