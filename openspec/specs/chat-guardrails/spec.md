# chat-guardrails Specification

## Purpose

Keeps the assistant inside its intended scope and budget: it answers only from FAQ data, and bounds the tokens spent on one request.

## Requirements

### Requirement: Output token limit
The system SHALL send a configurable `max_tokens` value (default 1024) with every Claude API call.

#### Scenario: Default limit
- **WHEN** the service starts without the token limit configured
- **THEN** every Claude call is sent with `max_tokens` of 1024

#### Scenario: Configured limit
- **WHEN** the token limit is set in the environment
- **THEN** every Claude call uses that value

### Requirement: Limits are validated at startup
The system SHALL read the token limit, the message length limit, the message count limit and the FAQ similarity threshold from the environment and SHALL refuse to start when one of them is invalid.

#### Scenario: Invalid limit
- **WHEN** the token limit is set to a non-positive number
- **THEN** the service fails at startup

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
