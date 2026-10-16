# Spec Delta

## ADDED Requirements

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
