# Spec Delta

## ADDED Requirements

### Requirement: Direct FAQ answering
The system SHALL answer every chat request from FAQ search results, without an agent or tool selection: it searches the FAQ with the last user message and, when at least one hit counts as data, asks the LLM once to answer from those hits in the language of the user's message.

#### Scenario: FAQ question
- **WHEN** the user asks a question for which the FAQ has a sufficiently similar entry
- **THEN** the system responds with HTTP 200 and a reply based on that entry, produced by a single LLM call

#### Scenario: Greeting
- **WHEN** the user message is a greeting such as "hi"
- **THEN** the system answers with the fixed refusal

#### Scenario: Question about a user
- **WHEN** the user asks about the profile of a user identified by ID or email
- **THEN** the system answers with the fixed refusal, because no user data source exists

### Requirement: Vector database failure
The system SHALL respond with HTTP 502 when the vector database is unavailable, the same status as for an LLM provider failure.

#### Scenario: Qdrant down
- **WHEN** the FAQ search fails because Qdrant cannot be reached
- **THEN** the system responds with HTTP 502, no `reply` is produced and the Claude API is not called

## REMOVED Requirements

### Requirement: LLM-driven tool selection
**Reason**: The FAQ is the only data source, so there is nothing for the LLM to choose between; FAQ search is always the first step.
**Migration**: See "Direct FAQ answering".

### Requirement: Tool errors are reported to the agent
**Reason**: There are no tools and no MCP server; user-not-found and MCP-unavailable situations no longer exist, and a Qdrant outage is an HTTP 502.
**Migration**: See "Vector database failure".
