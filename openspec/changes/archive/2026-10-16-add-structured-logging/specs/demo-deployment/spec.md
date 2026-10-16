# Spec Delta

## ADDED Requirements

### Requirement: Logging configuration from env
The system SHALL read `LOG_ID` and `ENVIRONMENT` from `.env`, pass them to both `ai-service` and `mcp-server`, and list both in `.env.example`.

#### Scenario: Shipped defaults
- **WHEN** the stack starts with the values from `.env.example`
- **THEN** both services start and write JSON lines carrying those `log_id` and `environment` values

### Requirement: Container log rotation
The system SHALL configure Docker log rotation for `ai-service` and `mcp-server` at 1 MB per file with one old copy kept, and MUST NOT require a shared log volume.

#### Scenario: Log size bounded
- **WHEN** a service writes more than 1 MB of logs
- **THEN** Docker keeps at most the current file and one rotated copy of about 1 MB each
