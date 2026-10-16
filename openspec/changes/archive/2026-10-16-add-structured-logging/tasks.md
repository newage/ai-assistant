# Tasks

## 1. Configuration and deployment

- [x] 1.1 Add `LOG_ID` and `ENVIRONMENT` to `.env.example`, to the `ai-service` and `mcp-server` environment in `docker-compose.yml`, and to `Settings` (`ai-service/app/settings.py`); verify with `python -m pytest tests/test_settings.py` including a new test for the defaults and overrides
- [x] 1.2 Add `logging: json-file, max-size 1m, max-file 2` to both services in `docker-compose.yml`; verify with `docker compose config` that both services show these options

## 2. ai-service logging

- [x] 2.1 Add `app/logging_setup.py` with the JSON formatter, the context filter (`request_id`, `debug`) and the uvicorn `log_config`; verify with a unit test that a record serializes to valid JSON with all required fields and `priority` in upper case
- [x] 2.2 Add the request middleware in `app/main.py` (id validation and generation, debug rule, `X-Request-ID` response header incl. 422 and 502); verify with API tests for echoed, generated, malformed id and header-on-error cases
- [x] 2.3 Add metadata logging at info and content logging at debug (500-char truncation) for the chat request and tool calls in `agent.py` and `tools.py`; verify with tests that info lines omit the email and result and debug lines include them
- [x] 2.4 Start uvicorn with the log config (`Dockerfile` CMD) and verify the access line for `POST /chat` is JSON with the request id

## 3. Propagation to MCP

- [x] 3.1 Make `McpTools.load()` accept the request id and debug flag and pass them as `X-Request-ID` and `X-Debugging` headers; verify with a test that an MCP call carries both headers

## 4. mcp-server logging

- [x] 4.1 Add `monolog/monolog` to `mcp-server/composer.json`, create the JSON formatter and a per-request logger factory in `src/`; verify with a PHPUnit test that a record has all required fields
- [x] 4.2 Wire the logger in `server.php` and `McpHandler`/`Tools` (id from `X-Request-ID` or `-`, level by the debug rule, metadata at info, arguments and results at debug); verify with PHPUnit tests for id propagation, `-` fallback, and the info/debug content rule
- [x] 4.3 Pass `LOG_ID` and `ENVIRONMENT` into the PHP logger fields; verify in the same tests

## 5. Docs and integration

- [x] 5.1 Document the log format, `X-Request-ID`, `X-Debugging` and the env variables in `CLAUDE.md` and `README`/`docs`; verify the documented example matches real output
- [x] 5.2 Run the full stack with `docker compose up -d --build`, send `POST /chat` with `X-Request-ID: abc123`, and verify with `docker compose logs` that lines from both services carry `abc123`, and that `ENVIRONMENT=prod` without the header produces no debug lines
