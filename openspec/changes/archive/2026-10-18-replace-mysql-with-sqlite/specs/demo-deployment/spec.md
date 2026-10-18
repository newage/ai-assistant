# Spec Delta

## MODIFIED Requirements

### Requirement: One-command ecosystem
The system SHALL provide a `docker-compose.yml` that runs `ai-service` and `vector-db` together, and MUST NOT run a separate database server container.

#### Scenario: Starting the stack
- **WHEN** an operator runs `docker compose up` with a valid `.env`
- **THEN** both services start and `ai-service` can answer `POST /chat`

#### Scenario: No database container
- **WHEN** the stack is running
- **THEN** `docker compose ps` lists no `mysql` or other SQL server service

### Requirement: Restricted network exposure
Only `ai-service` SHALL be reachable from outside the compose network; `vector-db` MUST NOT publish ports to the host.

#### Scenario: Port check
- **WHEN** the stack is running
- **THEN** only the `ai-service` port is published on the host

### Requirement: Secrets via environment file
The system SHALL read the Claude API key from `.env`, SHALL provide a `.env.example` listing it, and MUST NOT commit real secrets. No database credentials SHALL be required.

#### Scenario: Missing API key
- **WHEN** `ai-service` starts without the Claude API key
- **THEN** it fails fast with a clear configuration error

#### Scenario: No database passwords
- **WHEN** an operator copies `.env.example` to `.env` and sets only the Claude API key
- **THEN** the stack starts without asking for any database password
