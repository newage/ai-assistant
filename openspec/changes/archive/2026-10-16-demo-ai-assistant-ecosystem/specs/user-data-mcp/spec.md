# Spec Delta

## Purpose

Defines the MCP server that gives the agent read-only access to demo user data stored in MySQL, and the demo data it serves.

## ADDED Requirements

### Requirement: MCP server over HTTP
The system SHALL provide an MCP server reachable over HTTP transport that advertises exactly two tools: `find_user_profile` and `get_user_activity`.

#### Scenario: Tool discovery
- **WHEN** an MCP client lists the tools
- **THEN** the response contains `find_user_profile` and `get_user_activity` and no others

### Requirement: Find user profile
The `find_user_profile` tool SHALL return the profile (`id`, `email`, `name`, `created_at`) of the user identified by either an ID or an email.

#### Scenario: Lookup by ID
- **WHEN** the tool is called with an existing user ID
- **THEN** it returns that user's profile

#### Scenario: Lookup by email
- **WHEN** the tool is called with an existing user email
- **THEN** it returns that user's profile

#### Scenario: User not found
- **WHEN** the tool is called with an ID or email that matches no user
- **THEN** it returns a "user not found" tool result rather than a server failure

#### Scenario: No identifier
- **WHEN** the tool is called with neither an ID nor an email
- **THEN** it returns a validation error as a tool result

### Requirement: Get user activity
The `get_user_activity` tool SHALL return the activity records (`id`, `action`, `created_at`) of the user with the given ID.

#### Scenario: User with activity
- **WHEN** the tool is called with the ID of a user who has activity
- **THEN** it returns that user's activity records

#### Scenario: Unknown user
- **WHEN** the tool is called with an ID that matches no user
- **THEN** it returns a "user not found" tool result

### Requirement: Read-only data access
The MCP server MUST NOT modify MySQL data, and its database account SHALL have read-only privileges.

#### Scenario: Write attempt is impossible
- **WHEN** any MCP tool is invoked with any input
- **THEN** no row in MySQL is created, changed or deleted

### Requirement: Demo data
The system SHALL provide a MySQL schema with `users(id, email, name, created_at)` and `user_activity(id, user_id, action, created_at)` and SHALL seed it with fake data for tens of users.

#### Scenario: Fresh environment
- **WHEN** MySQL starts with an empty data volume
- **THEN** the schema is created and the fake users and their activity are present
