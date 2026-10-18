# demo-deployment Specification

## Purpose

Defines how the whole demo ecosystem is started with docker-compose, which services are reachable from outside, and how secrets are supplied.

## Requirements

### Requirement: One-command ecosystem
The system SHALL provide a `docker-compose.yml` that runs `ai-service`, `vector-db` and `mysql` together.

#### Scenario: Starting the stack
- **WHEN** an operator runs `docker compose up` with a valid `.env`
- **THEN** all three services start and `ai-service` can answer `POST /chat`

### Requirement: Restricted network exposure
Only `ai-service` SHALL be reachable from outside the compose network; `vector-db` and `mysql` MUST NOT publish ports to the host.

#### Scenario: Port check
- **WHEN** the stack is running
- **THEN** only the `ai-service` port is published on the host

### Requirement: Secrets via environment file
The system SHALL read the Claude API key and database passwords from `.env`, SHALL provide a `.env.example` listing them, and MUST NOT commit real secrets.

#### Scenario: Missing API key
- **WHEN** `ai-service` starts without the Claude API key
- **THEN** it fails fast with a clear configuration error

### Requirement: Startup ordering
The system SHALL start `ai-service` only after `vector-db` is healthy.

#### Scenario: Cold start
- **WHEN** the stack starts from empty volumes
- **THEN** the services reach a healthy state without manual restarts

### Requirement: Embedding model availability
The system SHALL make the embedding model available to `ai-service` without a download at request time, by baking it into the image or persisting its cache in a volume.

#### Scenario: Restart after first start
- **WHEN** `ai-service` is restarted
- **THEN** it does not re-download the embedding model

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

### Requirement: Logging configuration from env
The system SHALL read `LOG_ID` and `ENVIRONMENT` from `.env`, pass them to `ai-service`, and list both in `.env.example`.

#### Scenario: Shipped defaults
- **WHEN** the stack starts with the values from `.env.example`
- **THEN** `ai-service` starts and writes JSON lines carrying those `log_id` and `environment` values

### Requirement: Container log rotation
The system SHALL configure Docker log rotation for `ai-service` at 1 MB per file with one old copy kept, and MUST NOT require a shared log volume.

#### Scenario: Log size bounded
- **WHEN** a service writes more than 1 MB of logs
- **THEN** Docker keeps at most the current file and one rotated copy of about 1 MB each
