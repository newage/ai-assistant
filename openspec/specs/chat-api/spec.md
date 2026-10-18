# chat-api Specification

## Purpose

Defines the contract between the external chat bot and the assistant orchestrator, and how a chat request is answered from the FAQ.

## Requirements

### Requirement: Single chat endpoint
The system SHALL expose `POST /chat` accepting a list of `{role, content}` messages and SHALL return a single JSON response `{reply}` containing the full answer, without streaming. A request SHALL contain at most 4 messages, and each message SHALL be at most 500 characters.

#### Scenario: Successful chat request
- **WHEN** the bot sends `POST /chat` with a non-empty list of at most 4 messages ending with a user message
- **THEN** the system responds with HTTP 200 and a JSON body `{reply: <string>}`

#### Scenario: Invalid request body
- **WHEN** the bot sends an empty message list or a message with an unknown role
- **THEN** the system responds with HTTP 422 and does not call the LLM

#### Scenario: Too many messages
- **WHEN** the bot sends more than 4 messages
- **THEN** the system responds with HTTP 422 and does not call the LLM

#### Scenario: Message too long
- **WHEN** the bot sends a message longer than 500 characters
- **THEN** the system responds with HTTP 422 and does not call the LLM

### Requirement: Stateless conversation
The system SHALL NOT store conversation state between requests and SHALL derive the conversation context only from the messages sent in the current request.

#### Scenario: History supplied by the bot
- **WHEN** the bot sends earlier turns together with a new user message
- **THEN** the reply takes those earlier turns into account

#### Scenario: Restart does not lose sessions
- **WHEN** the service restarts between two requests
- **THEN** the next request behaves identically as long as the bot resends the history

### Requirement: LLM-driven tool selection
The system SHALL let the LLM decide, per request, whether to call the FAQ search tool, the MCP user-data tools, both, or neither. A request for which no tool returns data is answered with the fixed refusal.

#### Scenario: Greeting needs no tools
- **WHEN** the user message is a greeting such as "hi"
- **THEN** the system answers with the fixed refusal, without relying on any tool data

#### Scenario: User data question
- **WHEN** the user asks about the profile of a user identified by ID or email
- **THEN** the agent calls an MCP tool and bases the reply on its result

### Requirement: Tool errors are reported to the agent
The system SHALL return tool failures (user not found, MCP server unavailable) to the agent as tool results so that the reply honestly explains the situation.

#### Scenario: User not found
- **WHEN** an MCP tool reports that no such user exists
- **THEN** the system responds with HTTP 200 and a reply stating the user was not found

#### Scenario: MCP server unavailable
- **WHEN** the MCP server cannot be reached during a request
- **THEN** the system responds with HTTP 200 and a reply that explains the data could not be retrieved

### Requirement: LLM provider failure
The system SHALL respond with an HTTP 5xx status when the Claude API is unavailable.

#### Scenario: Claude API down
- **WHEN** the Claude API request fails
- **THEN** the system responds with HTTP 5xx and no `reply` is produced

### Requirement: Request tracing headers
`POST /chat` SHALL accept the optional request headers `X-Request-ID` and `X-Debugging` and SHALL return the request id used in the `X-Request-ID` response header, without changing the request or response body.

#### Scenario: Id echoed
- **WHEN** the bot sends `POST /chat` with `X-Request-ID: abc123`
- **THEN** the response has the header `X-Request-ID: abc123` and the usual `{reply}` body

#### Scenario: Id generated
- **WHEN** the bot sends `POST /chat` without `X-Request-ID`
- **THEN** the response contains a generated `X-Request-ID` header

#### Scenario: Error responses
- **WHEN** a request fails with HTTP 422 or 502
- **THEN** the response still carries the `X-Request-ID` header
