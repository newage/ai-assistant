# mcp-server

Read-only MCP server (PHP 8.3 + Swoole) exposing demo user data from MySQL over HTTP.

- Endpoint: `POST /mcp` (JSON-RPC 2.0, streamable-HTTP style, JSON responses only), `GET /health`
- Tools: `find_user_profile` (`user_id` or `email`), `get_user_activity` (`user_id`)
- DB access uses a `SELECT`-only account (see `db/init/03-readonly-user.sh`)
- Config (env): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `MCP_PORT` (default 9501), `LOG_ID`, `ENVIRONMENT`
- Logs: JSON lines on stdout (Monolog), `X-Request-ID` and `X-Debugging` request headers are honored; see the Logging section in the root `CLAUDE.md`

## Try it

```bash
curl -s -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' http://localhost:9501/mcp
curl -s -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_user_profile","arguments":{"email":"olena1@example.com"}}}' \
  http://localhost:9501/mcp
```

Tool failures (user not found, validation) come back as `isError: true` tool results, not protocol errors.

## Tests

PHPUnit runs against the seeded MySQL (`DB_*` env must point to it):

```bash
composer install && vendor/bin/phpunit
```
