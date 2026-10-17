# Spec Delta

## Purpose

Keeps the assistant inside its intended scope and budget: it answers only from FAQ and user-data tool results, and bounds the tokens and agent steps spent on one request.

## ADDED Requirements

### Requirement: Replies grounded in tool data
The system SHALL return the model's reply only when at least one tool returned data during the request; otherwise it SHALL reply with a fixed refusal text in Polish.

#### Scenario: Off-topic request
- **WHEN** the user asks "napisz piosenkę o jesieni" and no tool returns data
- **THEN** the system responds with HTTP 200 and the fixed Polish refusal as `reply`

#### Scenario: FAQ question answered
- **WHEN** the user asks a question for which the FAQ has a sufficiently similar entry
- **THEN** the reply is the model's answer based on that entry

#### Scenario: User data question answered
- **WHEN** the user asks about an existing user and the MCP tool returns the user's data
- **THEN** the reply is the model's answer based on that data

#### Scenario: Greeting
- **WHEN** the user sends "Cześć!" and no tool returns data
- **THEN** the system responds with the fixed refusal, which is friendly and says what the assistant can help with

### Requirement: What counts as tool data
The system SHALL count FAQ search results as data only for entries whose similarity score is not below a configurable threshold, and SHALL count MCP results as data only when the tool returned real data.

#### Scenario: Weak FAQ matches
- **WHEN** every FAQ hit scores below the threshold and no MCP tool returned data
- **THEN** the system responds with the fixed refusal

#### Scenario: User not found
- **WHEN** an MCP tool reports that the user does not exist
- **THEN** the system responds with the fixed refusal

#### Scenario: MCP server unavailable
- **WHEN** the MCP server cannot be reached and no other tool returned data
- **THEN** the system responds with the fixed refusal

### Requirement: Output token limit
The system SHALL send a configurable `max_tokens` value (default 1024) with every Claude API call.

#### Scenario: Default limit
- **WHEN** the service starts without the token limit configured
- **THEN** every Claude call is sent with `max_tokens` of 1024

#### Scenario: Configured limit
- **WHEN** the token limit is set in the environment
- **THEN** every Claude call uses that value

### Requirement: Agent step limit
The system SHALL stop the agent after a configurable number of tool-calling steps and SHALL answer with the fixed refusal instead of an error.

#### Scenario: Step limit exceeded
- **WHEN** the agent would need more steps than the limit allows
- **THEN** the system responds with HTTP 200 and the fixed refusal

### Requirement: Limits are validated at startup
The system SHALL read the token limit, the step limit, the message length limit, the message count limit and the FAQ similarity threshold from the environment and SHALL refuse to start when one of them is invalid.

#### Scenario: Invalid limit
- **WHEN** the token limit is set to a non-positive number
- **THEN** the service fails at startup
