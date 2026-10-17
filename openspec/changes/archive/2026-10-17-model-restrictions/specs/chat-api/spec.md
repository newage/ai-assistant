# Spec Delta

## MODIFIED Requirements

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

### Requirement: LLM-driven tool selection
The system SHALL let the LLM decide, per request, whether to call the FAQ search tool, the MCP user-data tools, both, or neither. A request for which no tool returns data is answered with the fixed refusal.

#### Scenario: Greeting needs no tools
- **WHEN** the user message is a greeting such as "hi"
- **THEN** the system answers with the fixed refusal, without relying on any tool data

#### Scenario: User data question
- **WHEN** the user asks about the profile of a user identified by ID or email
- **THEN** the agent calls an MCP tool and bases the reply on its result
