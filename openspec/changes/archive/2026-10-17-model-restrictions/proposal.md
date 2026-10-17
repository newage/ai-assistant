# Proposal

Source of decisions: `.agents/decisions/restrictions.md`.

## Why

`POST /chat` behaves like a general-purpose chatbot: it writes songs and solves programming tasks, and it is paid for from the Claude key. Nothing limits reply length, input size or the agent loop, so cost and behaviour depend on whatever a random user types.

## What Changes

- Cap the output of every Claude call with `max_tokens` (default 1024, from env).
- Cap the agent loop with a step limit (from env).
- Limit the request: at most 4 messages (was 50) and at most 500 characters per message; violations get HTTP 422 before any Claude call.
- Answer only from tool data: if no tool returned data, the model's reply is replaced with a fixed refusal in Polish (HTTP 200, same `{reply}` contract). This includes greetings and small talk, and a run that exceeds the step limit.
- FAQ hits count as data only at or above a similarity threshold (from env); MCP results count only when real data came back ("not found" and errors are not data).
- Remove small talk from the system prompt.
- **BREAKING** for the external bot: requests with more than 4 messages or a message longer than 500 characters are now rejected with 422.

## Capabilities

### New Capabilities
- `chat-guardrails`: limits on tokens and agent steps, and the rule that replies are grounded in FAQ/MCP tool data, otherwise a fixed refusal.

### Modified Capabilities
- `chat-api`: request validation limits (4 messages, 500 characters per message) and greetings no longer answered without tools.

## Impact

- `ai-service/app/settings.py`, `agent.py`, `tools.py`, `main.py`, `.env.example`, `docker-compose.yml` (env passthrough), tests in `ai-service/tests/`.
- External chat bot: must send at most 4 messages of at most 500 characters.
- No change to Qdrant, `mcp-server`, MySQL schema or logging.
