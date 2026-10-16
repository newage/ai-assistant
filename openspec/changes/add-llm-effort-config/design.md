# Design

## Context

`Settings.claude_model` (env `CLAUDE_MODEL`) is passed to `ChatAnthropic` in `Assistant.__init__` (`ai-service/app/agent.py`); compose forwards `CLAUDE_MODEL` with a Sonnet default, duplicated in `Settings` and `.env.example`. The installed `langchain-anthropic` 1.7.6 exposes `ChatAnthropic(effort=...)` (alias of `reasoning_effort`), which it sends as `output_config.effort`; when it is `None` nothing is sent. See proposal.md for motivation.

Per the Claude effort docs, Haiku 5.5 supports all five levels, defaults to `medium`, and recommends `low` for chat and short tool tasks.

## Goals / Non-Goals

**Goals:**
- One env variable controls effort for whichever model is configured.
- Misconfiguration is caught at startup, not as a 400 from the API on the first chat.

**Non-Goals:**
- Per-model effort tables or auto-selecting effort from the model name.
- Per-request effort, the `thinking` parameter, `max_tokens` changes.

## Decisions

- **Single `CLAUDE_EFFORT` variable, typed as `Literal["low","medium","high","xhigh","max"] | None` in `Settings`.** Pydantic validates it, so a bad value fails at startup like a missing API key. Empty string is normalised to `None` (a `field_validator(mode="before")`), because compose passes `CLAUDE_EFFORT=` as an empty string when it is blank. Alternative: free-form string passed through to the API — rejected, errors would surface only at request time as HTTP 502.
- **Pass it via `ChatAnthropic(effort=settings.claude_effort)`**, not `model_kwargs`/`output_config`. It is the first-class parameter, and `None` means "not sent", which gives the empty-value behavior for free. Alternative: building `output_config={"effort": ...}` by hand — rejected, same wire result with more code.
- **Defaults live in compose and `.env.example` (`claude-haiku-5-5` / `low`); `Settings` defaults to the same model with `claude_effort=None`.** Compose uses `${CLAUDE_EFFORT-low}` (no colon, so an explicitly empty value stays empty), so the shipped stack gets `low` while a bare `Settings()` (tests, local runs) sends no effort. Alternative: default `low` in `Settings` too — rejected, `low` is a model-specific recommendation and would silently apply to a user's chosen Sonnet/Opus. The model default in `Settings` is switched to Haiku for consistency with compose.
- **No model/effort compatibility check.** All current models that support effort accept the five levels except where the docs say otherwise (e.g. `xhigh` is not on every model); the API returns a clear error and ai-service maps it to 502. Hard-coding a matrix would go stale.

## Risks / Trade-offs

- [Default model changes from Sonnet 5.5 to Haiku 5.5, so answer quality/behavior changes] → intentional per the request; revert is `CLAUDE_MODEL=claude-sonnet-5-5` (and `CLAUDE_EFFORT` as desired) in `.env`; spot-check FAQ and MCP tool calls after the switch.
- [At `low`, Haiku 5.5 may skip a search or stop early in long agent prompts (docs)] → system prompt is short; mitigated by raising `CLAUDE_EFFORT` to `medium` without code changes.
- [An effort unsupported by the chosen model gives a 400 from the API, surfaced as HTTP 502] → documented in README; not validated locally (see last decision).
- [Existing deployments keep `CLAUDE_MODEL` in their `.env`, so only `CLAUDE_EFFORT` newly applies to them] → acceptable; effort is sent only if they set it, since an old `.env` has no `CLAUDE_EFFORT` and compose then defaults it to `low` (unset, unlike empty) — noted in README so Sonnet users know to set it explicitly.
