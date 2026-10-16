# AI Assistant Demo Ecosystem

Demo of an AI assistant: an external chat bot talks to `ai-service`, whose Claude-powered agent can search an FAQ (Qdrant RAG) and look up demo users via an MCP server backed by MySQL.

```
chat bot ──HTTP──▶ ai-service ──▶ vector-db (Qdrant)
                       └─MCP/HTTP─▶ mcp-server (PHP + Swoole) ──▶ mysql
```

## Quick start

```bash
cp .env.example .env     # set ANTHROPIC_API_KEY and the DB passwords
docker compose up -d --build --wait
curl -s localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Show profile olena1@example.com"}]}'
```

`POST /chat` takes the full conversation (`messages: [{role: user|assistant, content}]`, last one from the user) and returns `{"reply": "..."}`. The service is stateless, so the bot resends the history each time. A Claude API failure gives HTTP 502.

The first image build downloads the ~2.2 GB embedding model; later builds and starts do not.

## FAQ data

The FAQ collection starts empty (chat still works). See [docs/faq-seeding.md](docs/faq-seeding.md).

## Demo caveat

There is **no access control**: the agent can show data of any user by ID or email. This is acceptable only because the data is fake; production needs authorization. Only `ai-service` publishes a host port.

## Development

See `CLAUDE.md` for test commands and architecture notes; specs live in `openspec/`. Design decisions and their rationale: [.agents/decisions/demo-ai-assistant-ecosystem.md](.agents/decisions/demo-ai-assistant-ecosystem.md).
