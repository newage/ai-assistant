# Tasks

## 1. Settings and agent wiring

- [x] 1.1 Add `claude_effort: Literal["low","medium","high","xhigh","max"] | None = None` to `Settings` (`ai-service/app/settings.py`), normalise empty string to `None`, and switch the `claude_model` default to `claude-haiku-5-5`. Verify with new tests in `ai-service/tests/test_settings.py`: valid value accepted, empty -> `None`, `CLAUDE_EFFORT=turbo` raises `ValidationError` naming `claude_effort`.
- [x] 1.2 Pass `effort=settings.claude_effort` to `ChatAnthropic` in `Assistant.__init__` (`ai-service/app/agent.py`). Verify with a test in `ai-service/tests/test_agent.py` that builds `Assistant` without an injected model and asserts the resulting `ChatAnthropic` has `effort == "low"` (and `None` when unset); run `python -m pytest -q` in the ai-service container and confirm it passes.

## 2. Deployment config and docs

- [x] 2.1 Update `.env.example` (`CLAUDE_MODEL=claude-haiku-5-5`, add `CLAUDE_EFFORT=low` with a one-line comment listing allowed values and "empty = API default") and `docker-compose.yml` (`CLAUDE_MODEL` default `claude-haiku-5-5`, new `CLAUDE_EFFORT: ${CLAUDE_EFFORT-low}`). Verify with `docker compose config` showing both variables on `ai-service`.
- [x] 2.2 Document `CLAUDE_MODEL`/`CLAUDE_EFFORT` in `README.md` and `CLAUDE.md` (defaults, allowed levels, that an unsupported level for the chosen model gives HTTP 502, and that Sonnet users should set `CLAUDE_EFFORT` explicitly). Verify the docs match `.env.example`.

## 3. Integration check

- [x] 3.1 Start the stack with `docker compose up -d --build`, send `POST /chat` with a greeting and with an FAQ/user-lookup question, and confirm replies come back (HTTP 200) on Haiku 5.5 at `low`; then start with `CLAUDE_EFFORT=turbo` and confirm `ai-service` exits with the configuration error.
