# Design

## Context

Nothing uses `mysql` today: no schema, no seed, no client code in `ai-service` (see `CLAUDE.md`). It only costs a container, two passwords and a healthcheck. `ai-service` is a single container, so an embedded database fits.

## Goals / Non-Goals

**Goals:**
- Remove the MySQL container and all its config; leave a stack of `ai-service` + `vector-db`.

**Non-Goals:**
- Creating the SQLite file, schema, volume, env setting or any Python code. The future user-data API owns them.

## Decisions

- **Do not prepare SQLite now (no volume, no `SQLITE_PATH`).** An unused setting is dead config and the file location depends on the future API (it may need a named volume mounted into `ai-service`, added with it). Alternative: add a `sqlite-data` volume and path now — rejected as speculative.
- **Delete `MYSQL_*` from `.env.example` without a compat shim.** Compose and `ai-service` ignore unknown variables, so old `.env` files keep working. Alternative: keep them commented — rejected, they would mislead.
- **Leave history untouched.** `.agents/decisions/*`, archived changes and the FAQ/frontend skill lists (MySQL as Vadym's real skill) are not about this stack.

## Risks / Trade-offs

- [SQLite allows one writer and lives in one container] → fine for 1-2 tables of a demo; revisit if the user-data API becomes multi-instance.
- [Stale `mysql-data` volume on existing machines] → `make down` (drops data) or `docker volume rm ai-assistant_mysql-data`.

## Migration Plan

Run `make rebuild`. Rollback: restore the removed compose service and env lines from git.
