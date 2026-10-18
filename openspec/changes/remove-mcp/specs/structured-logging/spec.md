# Spec Delta

## ADDED Requirements

### Requirement: Request correlation
`ai-service` SHALL use the incoming `X-Request-ID` when it matches `[A-Za-z0-9._-]{1,64}`, otherwise generate a new one, and SHALL put the id into every log line it writes for that request.

#### Scenario: Client supplies an id
- **WHEN** the bot sends `POST /chat` with `X-Request-ID: abc123`
- **THEN** every `ai-service` line for that request has `"x-request-id":"abc123"`

#### Scenario: No id supplied
- **WHEN** the bot sends `POST /chat` without `X-Request-ID`
- **THEN** `ai-service` generates an id and the same id appears in all its lines for that request

#### Scenario: Malformed id
- **WHEN** the bot sends an `X-Request-ID` containing spaces, newlines or more than 64 characters
- **THEN** it is ignored and a new id is generated

## MODIFIED Requirements

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
- **THEN** debug records are written for that request

#### Scenario: Other header value
- **WHEN** a request carries `X-Debugging: false`
- **THEN** the header has no effect and the environment rule applies

### Requirement: Content logging by level
At info level the system SHALL log request metadata only (step name, duration, status) and MUST NOT log user message text, search queries or search results. At debug level it SHALL additionally log them, each truncated to about 500 characters.

#### Scenario: Info level
- **WHEN** the FAQ search runs for a message containing an email address at info level
- **THEN** the log has the step name, duration and status and does not contain the message text or the FAQ hits

#### Scenario: Debug level
- **WHEN** the same search happens at debug level
- **THEN** the log includes the query and the hits, truncated to about 500 characters

## REMOVED Requirements

### Requirement: Request correlation across services
**Reason**: There is no second service to forward the id to; correlation now concerns `ai-service` lines only.
**Migration**: See "Request correlation".
