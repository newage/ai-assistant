# Tasks

## 1. Stack configuration

- [x] 1.1 Remove the `mysql` service and the `mysql-data` volume from `docker/docker-compose.yml`; verify `docker compose -f docker/docker-compose.yml config` succeeds and lists only `ai-service` and `vector-db`
- [x] 1.2 Remove the `MYSQL_*` lines from `.env.example`; verify `grep -ri mysql .env.example docker/` returns nothing
- [x] 1.3 Run `make rebuild` with a `.env` holding only the Claude API key; verify the stack becomes healthy, `docker compose ps` has no mysql service and `POST /chat` answers

## 2. Documentation

- [x] 2.1 Update `README.md` (diagram, `.env` step, `make rebuild` note, demo caveat) and `CLAUDE.md` (diagram and the `mysql` bullet: future user-data store is an SQLite file, not a container); verify `grep -n -i mysql README.md CLAUDE.md` returns nothing

## Workflow follow-up

- Archive the change after review so `openspec/specs/demo-deployment/spec.md` is updated.
