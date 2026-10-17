# Design

## Context

See `proposal.md` for motivation and `.agents/decisions/restrictions.md` for the full decision log. `Assistant.reply()` builds a LangChain agent per request with `search_faq` and the MCP tools. `faq.search` returns scores, but `search_faq` drops them and the tools return text, so the agent run itself says nothing about whether data was found. Limits live in `Settings`, where invalid values fail startup (as `CLAUDE_EFFORT` does).

## Goals / Non-Goals

**Goals:** bounded spend per request; refusal guaranteed in code for anything not backed by FAQ/MCP data; no contract change beyond new 422 cases.

**Non-Goals:** rate limiting, authentication, a pre-agent classifier, language detection, changing Qdrant, `mcp-server` or logging.

## Decisions

**1. Grounding check in code, not in the prompt.** After the agent run, if no tool recorded data, `reply()` returns the fixed refusal and discards the model text. The prompt is also tightened (answer only from tool results, no small talk), but only as a first line of defence. Rejected: prompt-only (injectable) and a classifier call before the agent (+1 Claude call per request, false rejections).

**2. Tools record "data found" explicitly.** A per-request holder (set in `reply()`, via a `contextvar` like `request_id_var`) is marked by `search_faq` when at least one hit has `score >= FAQ_MIN_SCORE`, and by the MCP guard wrapper when a call succeeds with a real result. `search_faq` also drops hits below the threshold from what it returns to the model and answers `NO_FAQ` when none are left. Rejected: parsing `ToolMessage` text in the agent result, which depends on message wording such as "User not found".

**3. MCP "not found" is not data.** The MCP server marks it with `isError: true`; the implementation must confirm how `langchain-mcp-adapters` surfaces this (exception caught by the guard, or error text) and make sure neither path marks data.

**4. Step limit through the graph recursion limit.** Today nothing is set and LangGraph's default recursion limit is 10007, i.e. effectively unbounded. `AGENT_MAX_STEPS` (default 4) counts model → tool rounds; a normal request needs 1–3 (FAQ: 1; user lookup: 1–2; mixed: up to 3), so 4 leaves headroom while cutting a stuck loop quickly. It is passed as `recursion_limit = 2 * steps + 1` in the invoke config. `GraphRecursionError` is caught in `reply()` and turned into the refusal (HTTP 200), not a 5xx. `max_tokens` is passed to `ChatAnthropic` (`CLAUDE_MAX_TOKENS`).

**5. FAQ threshold measured, not guessed.** `FAQ_MIN_SCORE` defaults to 0.82. Measured on the live collection (cosine, e5-large) with 20 queries: Polish in-topic questions score 0.83–0.88, in-topic questions in English/Ukrainian 0.80, off-topic and greetings 0.72–0.81. Scores are compressed, so the score alone cannot separate the groups: 0.82 removes obvious junk but also rejects in-topic questions in other languages (lower it to 0.80 to accept them, at the cost of letting a few off-topic queries through, which the prompt must then catch).

**6. Request limits in Pydantic.** `max_length` on `Message.content` (`MAX_MESSAGE_CHARS`, 500) and the existing `max_messages` default lowered to 4; violations are 422 before Claude is called.

**7. Refusal text.** One fixed Polish constant, friendly, saying the assistant helps with service questions and user data. No language detection.

## Risks / Trade-offs

- [Tokens for a discarded reply are still spent] → bounded by `max_tokens` and the step limit.
- [`FAQ_MIN_SCORE` too high rejects valid questions (in-topic questions in a non-Polish language score about 0.80), too low lets junk through] → start at 0.82, re-measure on real `debug` logs, adjust in env.
- [The external bot breaks on 422 for long dialogs] → known and accepted (explicit limit chosen over silent truncation).
- [A reply that mixes tool data with off-topic content passes the check] → the prompt restricts this; the check guarantees only that some data backed the request.

## Migration Plan

Deploy `ai-service` with new env defaults; no data migration. Rollback by redeploying the previous image. The bot owner is told about the 4-message / 500-character limits.

## Open Questions

- Whether to lower `FAQ_MIN_SCORE` to 0.80 if real users write in languages other than Polish; an env value that does not change the specs or tasks.
