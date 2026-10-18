# Spec Delta

## ADDED Requirements

### Requirement: Replies grounded in FAQ data
The system SHALL call the LLM only when at least one FAQ hit counts as data and SHALL return the model's reply built from those hits; otherwise it SHALL reply with a fixed refusal text in Polish without calling the LLM.

#### Scenario: Off-topic request
- **WHEN** the user asks "napisz piosenkę o jesieni" and no FAQ hit counts as data
- **THEN** the system responds with HTTP 200 and the fixed Polish refusal as `reply`, without calling the LLM

#### Scenario: FAQ question answered
- **WHEN** the user asks a question for which the FAQ has a sufficiently similar entry
- **THEN** the reply is the model's answer based on that entry

#### Scenario: Greeting
- **WHEN** the user sends "Cześć!" and no FAQ hit counts as data
- **THEN** the system responds with the fixed refusal, which is friendly and says what the assistant can help with

### Requirement: What counts as FAQ data
The system SHALL count an FAQ hit as data only when its similarity score is not below a configurable threshold.

#### Scenario: Weak FAQ matches
- **WHEN** every FAQ hit scores below the threshold
- **THEN** the system responds with the fixed refusal

#### Scenario: Empty FAQ
- **WHEN** the FAQ collection is empty or missing
- **THEN** the system responds with the fixed refusal

## MODIFIED Requirements


### Requirement: Limits are validated at startup
The system SHALL read the token limit, the message length limit, the message count limit and the FAQ similarity threshold from the environment and SHALL refuse to start when one of them is invalid.

#### Scenario: Invalid limit
- **WHEN** the token limit is set to a non-positive number
- **THEN** the service fails at startup

## REMOVED Requirements

### Requirement: Replies grounded in tool data
**Reason**: Grounding is no longer based on tool results; it is now defined by FAQ hits.
**Migration**: See "Replies grounded in FAQ data".

### Requirement: What counts as tool data
**Reason**: MCP results no longer exist; only FAQ hits can count as data.
**Migration**: See "What counts as FAQ data".

### Requirement: Agent step limit
**Reason**: There is no agent loop; a request makes at most one LLM call, so a step limit has nothing to bound.
**Migration**: None. `AGENT_MAX_STEPS` is no longer read; the per-call token limit still bounds spend.
