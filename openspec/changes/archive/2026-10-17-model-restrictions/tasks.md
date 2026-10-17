# Tasks

## 1. Settings and request limits

- [x] 1.1 Add `CLAUDE_MAX_TOKENS` (1024), `AGENT_MAX_STEPS` (4), `MAX_MESSAGE_CHARS` (500), `FAQ_MIN_SCORE` (0.82) and set `MAX_MESSAGES` default to 4 in `Settings` with positive-value validation; document them in `.env.example` and pass them through `docker-compose.yml`; verify with `test_settings.py` cases for defaults, overrides and invalid values failing.
- [x] 1.2 Enforce `MAX_MESSAGE_CHARS` and the 4-message limit in the request model in `main.py`; verify with `test_chat_api.py` cases for 5 messages, a 501-character message and a valid request, all returning 422 without calling the assistant where invalid.

## 2. Tool data tracking

- [x] 2.1 Add the per-request data holder and mark it from `search_faq` only for hits with `score >= FAQ_MIN_SCORE`, returning `NO_FAQ` when none qualify; verify with `test_tools.py` for strong, weak and empty hits. Also re-measure the threshold against real queries (the `debug` logs show the model's `search_faq` queries) and note in `.env.example` that in-topic questions in other languages score about 0.80.
- [x] 2.2 Mark the holder from the MCP guard wrapper only on real results; confirm how the adapter reports `isError` and verify with `test_tools.py` that a found user marks data while "User not found" and an unavailable server do not.

## 3. Agent behaviour

- [x] 3.1 Pass `max_tokens` to `ChatAnthropic`, apply `recursion_limit = 2 * AGENT_MAX_STEPS + 1`, and catch `GraphRecursionError`; verify with `test_agent.py` that the limit is sent and an endless tool loop ends in the refusal.
- [x] 3.2 Add the Polish refusal constant, return it when no tool recorded data, and rewrite the system prompt (answer only from tool results, no small talk); verify with `test_agent.py` for off-topic, greeting, FAQ and MCP-data requests.
- [x] 3.3 Update `test_chat_api.py` end to end: an off-topic request returns 200 with the refusal and a data-backed request returns the model reply; verify the full ai-service suite passes.

## 4. Documentation

- [x] 4.1 Update `CLAUDE.md` (limits, refusal behaviour, new env variables) and the `data/http/chat.http` sample; verify the documented variables match `.env.example`.
