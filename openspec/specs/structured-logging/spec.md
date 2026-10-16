# structured-logging Specification

## Purpose

Defines how `ai-service` and `mcp-server` emit structured JSON logs, how a single request is traced across both services, and how detailed (debug) logging is controlled.

## Requirements

### Requirement: JSON log lines on stdout
Each service SHALL write every application log record as one JSON object per line to stdout, with the fields `priority`, `service`, `short_message`, `x-request-id`, `extra`, `timestamp` (ISO 8601 with timezone), `log_id` and `environment`.

#### Scenario: Application record
- **WHEN** `ai-service` logs a record while handling a request
- **THEN** stdout receives one line of valid JSON with all of those fields and `service` equal to `ai-service`

#### Scenario: Identity fields from env
- **WHEN** a service starts with `LOG_ID=vadym` and `ENVIRONMENT=local`
- **THEN** every line it writes has `"log_id":"vadym"` and `"environment":"local"`

### Requirement: Log levels
The system SHALL support the levels critical, error, warning, info and debug, reported in `priority` in upper case.

#### Scenario: Level reported
- **WHEN** a service logs an error
- **THEN** the line has `"priority":"ERROR"`

### Requirement: Debug level switching
The system SHALL log at debug level for a request when it carries `X-Debugging: true`; without that header it SHALL log at debug level only if `ENVIRONMENT` is not `prod`, and otherwise at info level.

#### Scenario: Development without header
- **WHEN** `ENVIRONMENT=local` and a request has no `X-Debugging` header
- **THEN** debug records for that request are written

#### Scenario: Production without header
- **WHEN** `ENVIRONMENT=prod` and a request has no `X-Debugging` header
- **THEN** no debug records are written for that request

#### Scenario: Production with header
- **WHEN** `ENVIRONMENT=prod` and a request carries `X-Debugging: true`
- **THEN** debug records are written for that request in both services

#### Scenario: Other header value
- **WHEN** a request carries `X-Debugging: false`
- **THEN** the header has no effect and the environment rule applies

### Requirement: Request correlation across services
`ai-service` SHALL use the incoming `X-Request-ID` when it matches `[A-Za-z0-9._-]{1,64}`, otherwise generate a new one. It SHALL forward the id and the `X-Debugging` value to `mcp-server` on every MCP call of that request, and `mcp-server` SHALL put the id into every log line it writes for that request.

#### Scenario: Client supplies an id
- **WHEN** the bot sends `POST /chat` with `X-Request-ID: abc123`
- **THEN** lines from `ai-service` and `mcp-server` for that request have `"x-request-id":"abc123"`

#### Scenario: No id supplied
- **WHEN** the bot sends `POST /chat` without `X-Request-ID`
- **THEN** `ai-service` generates an id and the same id appears in lines from both services

#### Scenario: Malformed id
- **WHEN** the bot sends an `X-Request-ID` containing spaces, newlines or more than 64 characters
- **THEN** it is ignored and a new id is generated

#### Scenario: MCP call without id
- **WHEN** `mcp-server` receives a request without `X-Request-ID`
- **THEN** its lines for that request have `"x-request-id":"-"`

### Requirement: Content logging by level
At info level the system SHALL log request metadata only (tool name, duration, status) and MUST NOT log user message text, tool arguments or tool results. At debug level it SHALL additionally log them, each truncated to about 500 characters.

#### Scenario: Info level
- **WHEN** the agent calls `find_user_profile` with an email at info level
- **THEN** the log has the tool name, duration and status and does not contain the email or the profile

#### Scenario: Debug level
- **WHEN** the same call happens at debug level
- **THEN** the log includes the arguments and result, truncated to about 500 characters

### Requirement: Python framework logs in JSON
All Python output, including uvicorn access and error logs, SHALL be JSON in the same format. The system messages of Swoole MAY remain plain text.

#### Scenario: Access log
- **WHEN** `POST /chat` completes
- **THEN** the uvicorn access record is a JSON line with the request's `x-request-id`
