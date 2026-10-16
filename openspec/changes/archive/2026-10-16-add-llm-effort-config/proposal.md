# Proposal

## Why

`ai-service` calls Claude with the API's default effort, so the model spends more thinking tokens than a support chat needs. Claude Haiku 5.5 at `low` effort is the documented fit for chat ("the cheapest and fastest level, for chat, short tool tasks"), but the effort level cannot be set today and the default model is still `claude-sonnet-5-5`.

## What Changes

- Add a `CLAUDE_EFFORT` environment setting (`low | medium | high | xhigh | max`; empty = not sent, so the API default of the chosen model applies) next to `CLAUDE_MODEL`.
- `ai-service` passes it to the Claude API as `output_config.effort` when set.
- Change the default model in `.env.example`, `docker-compose.yml` and `Settings` from `claude-sonnet-5-5` to `claude-haiku-5-5`, with `CLAUDE_EFFORT=low` as the shipped default (**assumption**: the request says to set `low` for Haiku 5.5 because it is enough for chat, which is read as making Haiku 5.5 + `low` the default; switching back to Sonnet is one `.env` edit).
- An invalid effort value makes `ai-service` fail fast at startup, like a missing API key.
- Document the setting in README/CLAUDE.md where `CLAUDE_MODEL` is described.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `demo-deployment`: adds a requirement that the Claude model and its effort level are configurable through `.env`, with Haiku 5.5 at `low` as the default, and that invalid values fail fast.

## Impact

- Code: `ai-service/app/settings.py`, `ai-service/app/agent.py` (`ChatAnthropic(effort=...)`), tests in `ai-service/tests/`.
- Config: `.env.example`, `docker-compose.yml` (new `CLAUDE_EFFORT` variable, new model default).
- Docs: `README.md`, `CLAUDE.md`.
- No new dependencies: the installed `langchain-anthropic` (1.7.6) already supports `effort`.
- Behavior: default replies come from Haiku 5.5 at low effort. Per the Haiku 5.5 docs, `low` is more likely to skip a search or stop early in long agent prompts; the agent prompt here is short, but FAQ/MCP tool use should be spot-checked.
- Out of scope: per-message/mid-conversation effort (beta), the `thinking` parameter, `max_tokens` tuning.
