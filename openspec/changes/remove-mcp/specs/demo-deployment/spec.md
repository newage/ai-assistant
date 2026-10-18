# Spec Delta

## MODIFIED Requirements

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

### Requirement: Startup ordering
The system SHALL start `ai-service` only after `vector-db` is healthy.

#### Scenario: Cold start
- **WHEN** the stack starts from empty volumes
- **THEN** the services reach a healthy state without manual restarts

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
