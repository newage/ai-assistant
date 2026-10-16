# demo-deployment Specification

## Purpose

Defines how the whole demo ecosystem is started with docker-compose, which services are reachable from outside, and how secrets are supplied.

## Requirements

### Requirement: One-command ecosystem
The system SHALL provide a `docker-compose.yml` that runs `ai-service`, `vector-db`, `mcp-server` and `mysql` together.

#### Scenario: Starting the stack
- **WHEN** an operator runs `docker compose up` with a valid `.env`
- **THEN** all four services start and `ai-service` can answer `POST /chat`

### Requirement: Restricted network exposure
Only `ai-service` SHALL be reachable from outside the compose network; `vector-db`, `mcp-server` and `mysql` MUST NOT publish ports to the host.

#### Scenario: Port check
- **WHEN** the stack is running
- **THEN** only the `ai-service` port is published on the host

### Requirement: Secrets via environment file
The system SHALL read the Claude API key and database passwords from `.env`, SHALL provide a `.env.example` listing them, and MUST NOT commit real secrets.

#### Scenario: Missing API key
- **WHEN** `ai-service` starts without the Claude API key
- **THEN** it fails fast with a clear configuration error

### Requirement: Startup ordering
The system SHALL start dependent services only after their dependencies are healthy (`mcp-server` after `mysql`, `ai-service` after `vector-db` and `mcp-server`).

#### Scenario: Cold start
- **WHEN** the stack starts from empty volumes
- **THEN** the services reach a healthy state without manual restarts

### Requirement: Embedding model availability
The system SHALL make the embedding model available to `ai-service` without a download at request time, by baking it into the image or persisting its cache in a volume.

#### Scenario: Restart after first start
- **WHEN** `ai-service` is restarted
- **THEN** it does not re-download the embedding model
