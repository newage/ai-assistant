# Spec Delta

## REMOVED Requirements

### Requirement: MCP server over HTTP
**Reason**: The MCP server is deleted; user data will later be reached from Python through a different API.
**Migration**: None. `ai-service` no longer has an MCP client.

### Requirement: Find user profile
**Reason**: Tool `find_user_profile` goes away together with the MCP server.
**Migration**: None; a future user-data API gets its own capability.

### Requirement: Get user activity
**Reason**: Tool `get_user_activity` goes away together with the MCP server.
**Migration**: None; a future user-data API gets its own capability.

### Requirement: Read-only data access
**Reason**: There is no component left that reads MySQL; the `mysql` container stays but nothing queries it.
**Migration**: None.

### Requirement: Demo data
**Reason**: The schema and fake seed in `data/db/init/` are deleted; they are not needed.
**Migration**: None; the future API defines its own data.
