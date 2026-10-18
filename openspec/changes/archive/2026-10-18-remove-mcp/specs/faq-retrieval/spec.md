# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: FAQ search tool`
- TO: `### Requirement: FAQ search step`

## MODIFIED Requirements

### Requirement: Multilingual local embeddings
The system SHALL embed text locally with `intfloat/multilingual-e5-large`, using the `query:` prefix for search texts and the `passage:` prefix for indexed texts, without calling any external embedding service.

#### Scenario: Indexing a passage
- **WHEN** an FAQ entry is indexed
- **THEN** its text is embedded with the `passage:` prefix into a 1024-dimension vector

#### Scenario: Searching
- **WHEN** a chat request searches the FAQ
- **THEN** the search text is embedded with the `query:` prefix

### Requirement: FAQ search step
The system SHALL search the FAQ on every chat request, using the last user message as the query, and SHALL return the most relevant FAQ entries with their similarity scores.

#### Scenario: Relevant entry exists
- **WHEN** the last user message matches an indexed entry
- **THEN** the search returns that entry among the top results

### Requirement: Empty collection tolerance
The system MUST keep answering requests when the FAQ collection is empty or has not been seeded.

#### Scenario: Search on empty collection
- **WHEN** the FAQ search runs and the collection is empty
- **THEN** the search returns no results and the chat request completes normally with the fixed refusal

#### Scenario: Collection missing
- **WHEN** the FAQ search runs and the collection does not exist
- **THEN** the search returns no results and the chat request does not fail
