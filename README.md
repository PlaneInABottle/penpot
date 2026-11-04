# Penpot (self-hosted, released images)

Official Penpot 2.18 compose stack (frontend, backend, admin-console, mcp, exporter,
postgres 15, valkey, mailpit). No source build; images come from `penpotapp/*:2.18`.

This file covers the local stack only. The active MCP target may be a hosted instance
(see `AGENTS.md` § Runtime); the compose facts here do not describe it.

- App: <http://localhost:9001> (registration open, email verification disabled)
- Mailpit (captured mail): <http://localhost:8025>
- Config: `docker-compose.yaml` (upstream file; only the secret key is templated and
  `restart: always` changed to `restart: "no"`) + `.env`

Runtime commands, start/stop, logs, health and the full safety boundary live in
[AGENTS.md](AGENTS.md) § Runtime. This file keeps only what is specific to the released
image stack:

- Every service declares `restart: "no"`, so nothing starts automatically — not after a
  reboot, and not when Docker Desktop starts at login. `docker compose up -d` starts it and
  also applies compose/image changes.
- While containers exist but are stopped, `docker compose start` is enough. After
  `docker compose down` the containers are gone; `up -d` recreates them (named volumes are
  reattached, no data loss). `up -d --force-recreate` applies the restart policy they were
  created with.
- `.env` holds `PENPOT_VERSION` and the randomly generated `PENPOT_SECRET_KEY` (chmod 600,
  do not commit or share). Changing the secret key logs out existing sessions.
- The data lives in the `penpot_penpot_postgres_v15` and `penpot_penpot_assets` volumes.
  **Never run `docker compose down -v`** — it deletes both.
- Images are pinned by `PENPOT_VERSION`; 2.18 floats patches. Dump postgres before any
  version bump (migrations are forward-only); the command is in [AGENTS.md](AGENTS.md).
