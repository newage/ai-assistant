# Decision Log: Model restrictions in ai-service

## Problem
`POST /chat` behaves like a general-purpose chatbot: for "write a song" or "do my programming homework" the model answers, and it is paid for from the Claude key. Nothing limits the length of the reply, the length of the input message, or the agent loop. If nothing is done, cost and behaviour depend on whatever a random user types.

## Given
- `max_tokens` is not set, there is no limit on reply length — verified: `ai-service/app/agent.py`, `settings.py`.
- `max_messages=50`, the length of `content` is unbounded — verified: `settings.py`, `main.py`.
- The agent runs a model → tool → model loop (`create_agent`), at least two Claude calls per message — `agent.py`.
- The system prompt allows small talk and has no topical boundaries — `agent.py`.
- Data sources: `search_faq` (Qdrant, always returns top-k) and MCP tools (`find_user_profile`, `get_user_activity`) — `agent.py`, `faq.py`, `CLAUDE.md`.
- There is no authentication or rate limiting, deliberately (the data is fake) — `CLAUDE.md`.
- `claude_effort` / `claude_model` already live in `Settings` from env, an invalid value fails startup — `settings.py`.

## Inputs from the developer
- `max_tokens` is sent to the API, default 1024, moved to env. It limits a single call; total spend per request is bounded by the agent step limit.
- Allowed sources: FAQ and MCP. A request outside them gets a refusal.
- The agent step limit is configured in env.
- Incoming message: up to 500 characters.
- The `{messages}` contract is kept, but at most 4 messages (instead of 50).
- The refusal text is in Polish.

## Solution Concept
**Chosen:** B — system prompt plus a check of the result in code: if no tool returned data, the model's reply is replaced with a fixed refusal.
**Whose:** generated in the funnel
**Why:** the refusal guarantee lives in code rather than in the model's obedience, and there are no extra Claude calls.
**Rejected:**
- A. Prompt rules only — bypassed by prompt injection, nobody checks the model's reply.
- C. Classifier before the agent — +1 Claude call on every request, false rejections on vague requests, and the agent stays unprotected once a request passes.

## Vector
```
Client ─POST /chat─▶ validation (Pydantic)
                      ├ messages ≤ 4, content ≤ 500 chars ─ no ─▶ 422
                      ▼
                  Assistant.reply()
                      │ system prompt: "only tool data"
                      ▼
                  agent (Claude, max_tokens per call,
                      │   recursion_limit = step limit)
                      │        ├─▶ search_faq ─▶ Qdrant
                      │        └─▶ MCP ─▶ MySQL
                      ▼
                  check: did a tool return data?
                      ├ yes ─▶ model text ─▶ {reply}
                      └ no  ─▶ fixed refusal ─▶ {reply}
```
- All limits are `Settings` fields from env.
- Length validation runs before the Claude call, so no tokens are spent on an oversized input.
- The check runs after the agent finishes: tokens for the discarded reply are already spent, but `max_tokens` and the step limit bound them.
- The refusal is returned as `200 {reply}`, the contract does not change. Exceeding the step limit also yields the refusal, not a 5xx.
- Qdrant, MCP, the DB schema and logging are not changed.

## Details
### Small talk and greetings
**Decision:** no special behaviour. Anything without tool data, including "Hi!" and "Thanks", gets the same refusal; the refusal is written in a friendly tone and hints at what the bot can do. The small-talk line is removed from the system prompt.
**Why:** an exception would need a whitelist of words for several languages, and a refusal with a hint covers the same case.
**Alternative:** a greeting whitelist with a fixed reply without Claude — extra code for uk/pl/en.

### What counts as "tool data"
**Decision:** FAQ counts if at least one hit has a score not below the threshold (value in env). MCP counts if the tool returned real data; "not found" and errors are not data. With no data, the refusal is returned.
**Why:** Qdrant always returns top-k, so without a threshold the check would filter nothing.
**Alternative:** any non-empty result — a song request would also pass through weak FAQ matches.

### Exceeding the message limit
**Decision:** more than 4 messages → 422 from validation; no truncation.
**Why:** the limit is explicit, and the bot gets an error and fixes itself. A truncated slice could start with an assistant reply that has no question.
**Alternative:** take the last 4 — context is silently lost.

### Refusal language
**Decision:** the fixed refusal text is in Polish.
**Why:** developer's decision.
**Alternative:** English or the language of the user's message — rejected by the developer; a single fixed text also keeps the check free of language detection.

## Open Questions
- The concrete FAQ similarity threshold — to be tuned on real questions during implementation (starting value from `faq.sample.json`).

## Assumptions
- Variable names: `CLAUDE_MAX_TOKENS` (1024), `AGENT_MAX_STEPS`, `MAX_MESSAGE_CHARS` (500), `MAX_MESSAGES` (4, already exists), `FAQ_MIN_SCORE`. Non-blocking.
- The default for `AGENT_MAX_STEPS` is small (around 5–8 "model → tool" steps), tuned during implementation. Non-blocking.
- All new limits are validated in `Settings` following `CLAUDE_EFFORT`: an invalid value fails the service at startup.
- The exact wording of the Polish refusal is written during implementation (friendly tone, hints at what the bot can do). Non-blocking.
