# Penpot (self-hosted, released images)

Official Penpot 2.18 compose stack (frontend, backend, admin-console, mcp, exporter,
postgres 15, valkey, mailpit). No source build; images come from `penpotapp/*:2.18`.

- App: <http://localhost:9001> (registration open, email verification disabled)
- Mailpit (captured mail): <http://localhost:8025>
- Config: `docker-compose.yaml` (upstream file; only the secret key is templated and
  `restart: always` is changed to `restart: "no"`) + `.env`

## Lifecycle (on demand, never automatic)

Every service declares `restart: "no"`, so **nothing starts automatically**: not
after a reboot, and not when Docker Desktop starts at login. Start it yourself.

```sh
cd /Users/Y_ALTAY1/Documents/personal/penpot

# start (also the "update" command: reapplies compose/image changes)
docker compose up -d

# status
docker compose ps

# logs
docker compose logs -f --no-color
docker compose logs -f --no-color penpot-backend

# stop (removes containers, keeps data in the named volumes)
docker compose down
```

- `restart: "no"` is deliberate. Do not switch to `unless-stopped`: it still
  auto-starts with the daemon unless the container was explicitly stopped.
- While containers exist but are stopped, `docker compose start` is enough. After
  `docker compose down` the containers are gone; `docker compose up -d` recreates
  them (named volumes are reattached, no data loss).
- Recreating containers with `docker compose up -d --force-recreate` applies the
  restart policy they were created with.

Never run `docker compose down -v`: that deletes the `penpot_penpot_postgres_v15`
and `penpot_penpot_assets` volumes holding all designs and accounts.

`.env` holds `PENPOT_VERSION` and the randomly generated `PENPOT_SECRET_KEY`
(chmod 600, do not commit or share). Changing the secret key logs out existing sessions.
