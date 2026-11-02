# Penpot design workspace

Self-hosted Penpot plus the design work built in it. Global instructions apply. This file
covers the **workspace** — runtime, access, commands, ownership. Design rules do not live
here; they live in the skills below and are stated once.

## Skills (project-local)

| Skill | Load when | Owns |
|---|---|---|
| `penpot-design-system` | token set, component, screen, prototype, handoff | process, lifecycle, design rules, layout mechanics |
| `design-verification` | claiming a screen finished, a failed gate, a rebuild | definition of done, gate order, evidence |
| `ux-design-process` | story, density, states, review of a screen | task, story arc, hero contract, review rubric |
| `penpot-mcp-operations` | snippet, helpers, export, failed/stale bridge call | bridge contract, helpers API, failure table |

Craft and art direction come from `visual-interface-design`; option variety comes from
`design-variety`; never from here.
`scripts/helpers.js` is a symlink into the design-system skill's `assets/`; adding an asset
never repoints it.

## Start here

| I need to… | start with |
|---|---|
| begin a new design project | `penpot-design-system` § Start a new project |
| decide what a screen is for | `ux-design-process` § 1–2 |
| produce genuinely different options (hero, brand opening) | global `design-variety` § Protocol, then `ux-design-process` § 3 |
| build or tighten a screen | `penpot-design-system` + its `references/craft.md` |
| prove a screen is finished | `design-verification` § Definition of done |
| fix a failed or stale Penpot call | `penpot-mcp-operations/references/mcp-failures.md` |
| a render shows the wrong paint or a gate passed on a bad screen | `penpot-mcp-operations` § Paint is not bind, then `design-verification` § Evidence |
| add or change a lint rule | `design-verification` § Change discipline, then `scripts/test_lint_rules.py` |

## Runtime

Compose project `penpot`, containers `penpot-penpot-*`, file `docker-compose.yaml`.
Nothing starts automatically (`restart: "no"`): after a reboot or a Docker restart the stack
is down until `up -d` runs.

```sh
docker compose up -d                                   # start; also how config/image changes apply
docker compose ps                                      # status
docker compose logs -f --no-color penpot-backend
docker compose down                                    # stop, keep data in the named volumes
```

- **Never `docker compose down -v`**: it deletes the postgres and assets volumes that hold
  every design and account.
- Prebuilt `penpotapp/*` images, pinned by `PENPOT_VERSION` in `.env` (2.18 is a floating
  minor; `pull` takes patches, a new minor is a deliberate bump). **Dump the database before
  any bump** — migrations are forward-only:

  ```sh
  docker exec penpot-penpot-postgres-1 pg_dump -U penpot penpot > ~/penpot-$(date +%F).sql
  ```

- After an upgrade run one smoke: `tokens_sync --check`, `design_lint`, `design_qa`, one
  `export_board`, one `penpot_exec`. A changed plugin API shows up in the failure table first.

## Access

- App: http://localhost:9001 — Mailpit: http://localhost:8025
- The MCP endpoint URL carries a user token; it is read from its file at call time. Never
  copy, print, log or commit it, and never echo a command that contains it.
- `PEXELS_API_KEY` is exported in the shell profile; record the photo URL as provenance,
  never the key.

## Commands

All live scripts need the plugin connected. Exit codes everywhere: `0` clean, `1` finding,
`2` environment or transport.

| command | when |
|---|---|
| `python3 scripts/tokens_sync.py --file design/<p>/tokens.json --set <set>` | create/update a token set (`--check` reports drift; extras are informational unless `--strict`; `--export` reverses) |
| `python3 scripts/design_lint.py --page <p> [--json out.json] [--dump-nodes nodes.json] [--rules design/<p>/craft-rules.json]` | before any visual review of a page; `--json` is findings, `--dump-nodes` is geometry |
| `python3 scripts/design_qa.py --page <p> --lint-json lint.json` | with lint; high lint findings become fatal, advisory findings are printed and exit 0 (read the verdict) |
| `python3 scripts/check_contrast.py --file design/<p>/tokens.json --pair fg:bg` | before claiming a board |
| `python3 scripts/contrast_audit.py --page <p>` | walk every text; image/translucent backgrounds are MANUAL, never an automatic pass |
| `python3 scripts/rhythm.py nodes.json` | after a layout or copy move; nodes from `--dump-nodes`, findings are advisory (exit 0) |
| `python3 scripts/ux_gate.py --spec design/<p>/ux-spec.json` | structural story contract; visual beats stay in independent review |
| `python3 scripts/export_board.py --board <b> --page <p> --out design/<p>/shots` | one board per call |
| `python3 scripts/crop_board.py --board <b> --page <p> --out shots/<b> [--regions n.json] [--region JSON] [--primary-action NAME]` | the 1:1 review; `--regions` is repeatable |
| `python3 scripts/crop_board.py --attest shots/<b>/manifest.json` | before any "reviewed 1:1" claim; also fails a missing PNG |
| `python3 scripts/gate.py --pages <p1,p2> [--boards 01,05]` | one run: lint → QA → copy per page (+ux, export/crop); prints QA advisories and never calls them clean |
| `python3 scripts/gate.py stage design/<p>/build/screen-NN.js` | the only `git add -f design/…` path |
| `python3 design/<p>/build/build.py screen-NN` | REQUIRED project runner: page/session affinity, fit poll, photos, flows, live `photos`/`links` counts, `RESULT ok|fail nulls=N` (not shipped by the template) |
| `python3 scripts/penpot_exec.py [--read] --file design/<p>/build/screen-NN.js` | run a snippet; writer by default, `--read` passes a build session and never injects helpers |
| `python3 scripts/patch_file.py <file> --old-file a.txt --new-file b.txt` | edit a build script |
| `python3 scripts/import_media.py --url <url> --search "<q>" --name <slot> --page <p> --board <b> --x 0 --y 0 --w <w> --h <h>` | generic import (one source, `--url` or `--search`); prints source/provenance, persists nothing |
| `python3 scripts/docs_check.py [--json]` | after editing this file, README, a skill or the template |
| `python3 -m unittest scripts.test_docs_check scripts.test_penpot_scripts scripts.test_speed_tools scripts.test_lint_rules` | offline; no network, no Penpot |

`--only`/`--force`/`--restore` belong to a project's `tools/media.py`, never the generic
importer. The generic importer does not write a media table: record the accepted source URL
and provenance in the project table before claiming a lossless rebuild. `crop_board.py
--region '{"slug":"…","name":"…","x":0,"y":0,"w":0,"h":0}'` declares one region (page-absolute,
repeatable); `--primary-action NAME` overrides the CTA heuristic.

Thresholds live in `design_lint.DEFAULTS`/`RULES`, `ux_gate` and `build.py`, never in prose:
`--rules` is a written deviation, and `--acknowledge` entries need a reason. `design_lint.py`
exits 2 when a page is unmeasured (over 5% of texts without `textBounds`), and `gate.py` then
prints `FAIL (invalid)`, never PASS. Grid edges and declared bleeds are a manual nodes+render
check, not a script.

## Ownership and safety

- **One plugin, one writer.** Every MCP call holds a `flock` in `~/.cache/penpot-mcp/`; a
  second writer waits and exits 2 (`plugin busy: held by pid=…`). One owner per live page and
  per `lib.js`; parallel agents split by board, never by session. The OS releases a `flock`
  when its process dies, so never delete a lock file by hand: wait, or find the holder.
  `penpot_exec.py --read` is caller intent: it skips the session wait and helper injection,
  but still takes the call lock — it is not a sandbox and does not prove a snippet is read-only.
- `design/*/` is gitignored: stage a design only with an explicit `git add -f <path>` list (or
  `gate.py stage`), and verify with `git ls-files design/` — `git status` looks empty otherwise.
- In zsh, separate output sections with `---`, never `echo ===` (it misparses).
- `python3 -m py_compile` for `scripts/*.py`, `node --check` for helpers/build JS; never
  cross-check.
