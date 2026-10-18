# faq-retrieval Specification

## Purpose

Defines how FAQ knowledge is stored in the vector database, seeded, and searched on every chat request, including the state where no FAQ data exists yet.

## Requirements

### Requirement: Multilingual local embeddings
The system SHALL embed text locally with `intfloat/multilingual-e5-large`, using the `query:` prefix for search texts and the `passage:` prefix for indexed texts, without calling any external embedding service.

#### Scenario: Indexing a passage
- **WHEN** an FAQ entry is indexed
- **THEN** its text is embedded with the `passage:` prefix into a 1024-dimension vector

#### Scenario: Searching
- **WHEN** a chat request searches the FAQ
- **THEN** the search text is embedded with the `query:` prefix

### Requirement: FAQ collection configuration
The system SHALL store FAQ vectors in a Qdrant collection with dimension 1024 and cosine distance.

#### Scenario: Collection created by seeding
- **WHEN** the seed script runs against an empty Qdrant
- **THEN** the collection exists with dimension 1024 and cosine metric

### Requirement: Idempotent seeding
The seed script SHALL be safely re-runnable: it SHALL create the collection only if missing and upsert entries with stable IDs, so repeated runs create no duplicates.

#### Scenario: Running the seed twice
- **WHEN** the seed script runs twice with the same FAQ entries
- **THEN** the collection contains each entry exactly once

#### Scenario: Adding entries later
- **WHEN** new FAQ entries are added and the seed script is run again
- **THEN** the new entries become searchable without any change to the architecture

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
