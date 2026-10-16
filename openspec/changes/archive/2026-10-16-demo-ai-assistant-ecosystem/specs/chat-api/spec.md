# Spec Delta

## Purpose

Defines the contract between the external chat bot and the assistant orchestrator, and how the agent decides to use its tools to answer a user.

## ADDED Requirements

### Requirement: Single chat endpoint
The system SHALL expose `POST /chat` accepting a list of `{role, content}` messages and SHALL return a single JSON response `{reply}` containing the full answer, without streaming.

#### Scenario: Successful chat request
- **WHEN** the bot sends `POST /chat` with a non-empty list of messages ending with a user message
- **THEN** the system responds with HTTP 200 and a JSON body `{reply: <string>}`

#### Scenario: Invalid request body
- **WHEN** the bot sends an empty message list or a message with an unknown role
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
The system SHALL let the LLM decide, per request, whether to call the FAQ search tool, the MCP user-data tools, both, or neither.

#### Scenario: Greeting needs no tools
- **WHEN** the user message is a greeting such as "hi"
- **THEN** the system answers without querying the vector database or the MCP server

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
