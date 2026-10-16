## ADDED Requirements

### Requirement: Configurable Claude model and effort
The system SHALL read the Claude model name and the effort level from `.env` (`CLAUDE_MODEL`, `CLAUDE_EFFORT`) and SHALL list both in `.env.example`. The shipped defaults MUST be `claude-haiku-5-5` with effort `low`.

#### Scenario: Default configuration
- **WHEN** `ai-service` starts with the values from `.env.example`
- **THEN** every Claude API request uses model `claude-haiku-5-5` with effort `low`

#### Scenario: Operator overrides the model and effort
- **WHEN** `.env` sets `CLAUDE_MODEL=claude-sonnet-5-5` and `CLAUDE_EFFORT=high`
- **THEN** every Claude API request uses that model with effort `high`

#### Scenario: Effort left empty
- **WHEN** `CLAUDE_EFFORT` is empty or unset
- **THEN** no effort is sent and the Claude API default for the chosen model applies

### Requirement: Effort value validation
The system SHALL accept only the effort levels `low`, `medium`, `high`, `xhigh` and `max` (or empty) and MUST fail fast at startup on any other value.

#### Scenario: Unknown effort level
- **WHEN** `ai-service` starts with `CLAUDE_EFFORT=turbo`
- **THEN** it exits with a clear configuration error naming the setting
