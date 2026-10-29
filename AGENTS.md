# Penpot design workspace

Self-hosted Penpot plus the design work built in it. Global instructions apply. This file
holds only what is true for the workspace as a whole; each design project carries its own
folder under `design/`.

## Skills (project-local)

Penpot is not a global concern, so its skills live here rather than in `~/.agents/skills`:

| Skill | Load when | Owns |
|---|---|---|
| `.agents/skills/penpot-design-system` | designing a token set, component, screen, prototype or handoff in Penpot | order of work, design rules, verification, handoff |
| `.agents/skills/penpot-mcp-operations` | writing or debugging a Penpot MCP call, exporting a board, injecting helpers, a failed or stale call | bridge contract, helpers API, failure table |

Craft and art direction are **not** owned here: load `visual-interface-design` for the
direction, its craft checklist and the independent critique gate. `scripts/helpers.js` is a
symlink into the design-system skill; keep it pointed at the local copy. Moving these to
`~/.agents/skills` later means deleting the local copies and changing the symlink only.

## Runtime

Compose project `penpot`, containers `penpot-penpot-*`, file `docker-compose.yaml`.

```sh
cd /Users/Y_ALTAY1/Documents/personal/penpot
docker compose up -d            # start; also how config and image changes apply
docker compose ps               # status
docker compose logs -f --no-color penpot-backend
docker compose down             # stop, keep data in the named volumes
```

- Nothing starts automatically. Every service declares `restart: "no"`, so after a reboot or
  a Docker restart the stack is down until `up -d` runs.
- Never run `docker compose down -v`: it deletes the postgres and assets volumes that hold
  every design and account.

## Version and upgrades

All Penpot services are official prebuilt images from Docker Hub (`penpotapp/*`), pinned by
`PENPOT_VERSION` in `.env` — nothing is built from a git checkout, and nothing updates on its
own. `2.18` is a floating minor tag, so a `pull` picks up patch releases inside that line;
moving to a new minor is a deliberate bump.

```sh
docker compose pull && docker compose up -d      # apply the pinned version
docker exec penpot-penpot-postgres-1 pg_dump -U penpot penpot > ~/penpot-$(date +%F).sql
```

- **Dump the database before any bump.** The backend runs migrations on start and they are
  forward-only, so reverting the image without a dump loses the schema.
- After an upgrade, re-run the gates: `tokens_sync --check`, `design_lint`, `design_qa`, one
  `export_board`, and one `penpot_exec` snippet. The failure table records behaviour observed
  on 2.18.5; a changed plugin or MCP API shows up there first.
- Watch https://github.com/penpot/penpot/releases for new minors rather than guessing tags.

## Access

- App: http://localhost:9001 — Mailpit: http://localhost:8025
- MCP config is project-local in `opencode.jsonc`; the server URL is read from
  `~/.config/opencode/.penpot-mcp-url`. Never copy, print or commit that token.
- Stock photography: `PEXELS_API_KEY` is exported in the shell profile; use it for mock
  imagery and record the photo URL as provenance. Never commit the key.

## Design decisions

Applies to every design in this workspace; the reasoning lives in
`visual-interface-design` → "Decision Authority".

- **Ask once, at the start, batched (max four):** who it is for, the single job of the surface,
  whether the content is real or invented, any non-negotiable constraint. Do not ask twice.
- **If the brief already names it, do not ask.** A stated audience, style, palette or
  constraint is fixed: derive layout, type, tone and structure yourself and say what you chose.
- **Never ask the user to specify design** — no "how should the story go", no "which layout".
  Propose two or three named directions instead, each with a mechanism and a "refuses" clause.
- **No screens before a direction is chosen.** Sketch directions as boards on a scratch page,
  get the choice in one sentence, then build.
- **Record the decision** in `design/<project>/brief.md` (and the stance in `principles.md`),
  so later sessions inherit it instead of re-deciding. Accepted decisions are not reopened
  without a stated reason.

## Design projects

```
design/
  tokens.json            # the generic demo set (`core`)
  <project>/
    brief.md             # direction, content, per-page spec — the project's single source
    tokens.json          # the project token file, synced to a Penpot set of the same name
    build/               # Penpot build scripts, idempotent, run through penpot_exec.py
    shots/               # exported board renders, the visual evidence
```

- One project folder per design; never mix two projects in one token file or build folder.
- Page, board and token-set names are declared in that project's `brief.md`, not here.
- A project folder is throwaway-able: everything needed to rebuild it lives inside it.

## Scripts

`scripts/` talks to the same MCP endpoint, so it needs the plugin connected.

```sh
python3 scripts/penpot_exec.py --file <snippet.js>        # run JS in the plugin context
python3 scripts/export_board.py --board <board> --page <page> --out design/<project>/shots
python3 scripts/import_media.py --search "<query>" --name <shape> --page <page> --board <board> \
    --x <px> --y <px> --w <px> --h <px>                  # Pexels photo -> image fill
python3 scripts/tokens_sync.py --file design/<project>/tokens.json --set <set> [--check]
python3 scripts/design_qa.py --page <page> [--strict]     # coverage, render truth, hygiene
python3 scripts/design_lint.py --page <page>              # craft thresholds (type scale, accents, grid)
python3 scripts/check_contrast.py --file design/<project>/tokens.json --pair fg:bg
```

- Exit codes: `0` clean, `1` drift or findings, `2` environment or transport, so a failing
  gate is distinguishable from a broken connection. `--export` writes a timestamped `.bak`
  and refuses `--check`; `--page` never switches the page.
- `export_shape` returns data and writes no file, so `export_board.py` is the only way to an
  image — and the image is the only proof of paint. A fill can be token-bound and still
  render white; `design_qa.py` reports that as `renderMismatches` and fails on it.
- `import_media.py` needs `PEXELS_API_KEY`, downloads and shrinks the photo itself (the
  plugin sandbox cannot fetch cross-origin), and attaches it to a board **only while that
  page is active** — the script opens the page and verifies it first.
- `design_lint.py` reads `DESIGN_LINT_DEFAULTS` from the script and can be overridden per
  project with `--rules`; its thresholds are deliberately generic, the project brief decides
  the values that are brand choices.
- The MCP tool text wraps the plugin return value in a second `result` field; unwrap before
  decoding.
- Tests: `python3 -m unittest scripts/test_penpot_scripts.py`, 33 cases, no network.

## Design file conventions

Generic, shared by every project:

- One page per product area, named for the area; components on `Components`; throwaway work
  on `_scratch`, removed before handoff.
- Boards are numbered and named for their screen (`01-home`, `02-signup`) and sized to the
  target: 1440 wide for web desktop, 390 wide for mobile.
- Components are named `component/state` (`button/primary`, `button/primary-hover`), with
  states and sizes in one variant family.
- The library is file-scoped: deleting a page leaves its token sets behind.
