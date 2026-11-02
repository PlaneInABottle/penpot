# Penpot design workspace

Self-hosted Penpot plus the design work built in it. Global instructions apply.

## Skills (project-local)

| Skill | Load when | Owns |
|---|---|---|
| `.agents/skills/penpot-design-system` | token set, component, screen, prototype, handoff in Penpot | order of work, design rules, verification, handoff |
| `.agents/skills/ux-design-process` | story, density, states, review of a screen | task, story arc, hero contract, review rubric |
| `.agents/skills/penpot-mcp-operations` | snippet, helpers, export, failed/stale bridge call | bridge contract, helpers API, failure table |

Craft and art direction are **not** owned here: `visual-interface-design` for
direction, its checklist and the critique gate. `scripts/helpers.js` is a
symlink into the design-system skill's `assets/`; adding an asset never
repoints it. Moving these to `~/.agents/skills` later means deleting the
local copies and changing the symlink only.

## Runtime

Compose project `penpot`, containers `penpot-penpot-*`, file `docker-compose.yaml`.

```sh
cd /Users/Y_ALTAY1/Documents/personal/penpot
docker compose up -d            # start; also how config and image changes apply
docker compose ps               # status
docker compose logs -f --no-color penpot-backend
docker compose down             # stop, keep data in the named volumes
```

- Nothing starts automatically (`restart: "no"`); after a reboot or Docker
  restart the stack is down until `up -d` runs.
- Never run `docker compose down -v`: it deletes the postgres and assets
  volumes that hold every design and account.

## Version and upgrades

Prebuilt `penpotapp/*` images, pinned by `PENPOT_VERSION` in `.env` (2.18 is a
floating minor: `pull` takes patch releases, a new minor is a deliberate bump).

```sh
docker compose pull && docker compose up -d
docker exec penpot-penpot-postgres-1 pg_dump -U penpot penpot > ~/penpot-$(date +%F).sql
```

- **Dump the database before any bump.** Migrations are forward-only.
- After an upgrade: `tokens_sync --check`, `design_lint`, `design_qa`, one
  `export_board`, one `penpot_exec`. A changed plugin/MCP API shows up in the
  failure table first.
- Watch https://github.com/penpot/penpot/releases for new minors.

## Access

- App: http://localhost:9001 — Mailpit: http://localhost:8025
- MCP config is project-local in `opencode.jsonc`; the server URL is read from
  `~/.config/opencode/.penpot-mcp-url`. Never copy, print or commit that token.
- Stock photography: `PEXELS_API_KEY` is exported in the shell profile; record
  the photo URL as provenance. Never commit the key.

## Design decisions

- **Ask once, batched (max four):** who it is for, the single job of the
  surface, whether content is real or invented, any non-negotiable constraint.
- **A stated brief is fixed:** derive the rest yourself, record what you chose.
- **Never ask the user to specify design.** Propose two or three named
  directions (mechanism + "refuses" clause each), build only the chosen one.
- **No screens before a direction.** Sketch on a scratch page, one-sentence pick.
- **A decision not in a file does not exist.** Record in
  `design/<project>/brief.md` (+ stance in `principles.md`).

## Project lifecycle

Each phase writes a file before the next starts; no artifact, no phase.

| # | Phase | Writes | Exit condition |
|---|---|---|---|
| 1 | **Intake** | `brief.md` — audience, single job, content truth, constraints | answers exist or are marked unknown |
| 2 | **Direction** | `brief.md` § direction · `principles.md` | 2–3 named directions, one chosen, rejects recorded |
| 3 | **Story** | `ux-spec.json` — task, hook→proof→path→action, hero contract, states, mobile, claims | `ux_gate.py` exit 0, or findings owned with a reason |
| 4 | **Foundations** | `tokens.json` · Penpot set · `Components` page | `tokens_sync --check` clean; every component instanced once |
| 5 | **Screens** | `build/screen-NN.js` per screen | Definition of done holds |
| 6 | **Prototype** | flows and links on the screens | one flow, per-board interaction counts verified post-rebuild |
| 7 | **Handoff** | `README.md` · `shots/` · photo provenance | token/component inventory, board list, export evidence, gaps stated |

```sh
mkdir -p design/<project>/build design/<project>/shots
python3 scripts/tokens_sync.py --file design/<project>/tokens.json --set <set>
```

- One project folder per design; page, board and set names come from that
  project's `brief.md`.
- Build scripts run as `python3 scripts/penpot_exec.py --file
  design/<project>/build/screen-01.js`, idempotent: check-then-create, rebuild
  from scratch. Content-derived slots use `fit-slot.js` (`storage.FIT`):
  a fixed slot that cannot hold its content **throws** — the screen fails
  instead of painting over the next row.

## Scripts

All live scripts need the plugin connected. Exit codes everywhere:
`0` clean, `1` finding, `2` environment/transport.

```sh
python3 scripts/design_lint.py --page <page> [--rules <craft-rules.json>] [--json out.json] [--dump-nodes nodes.json]
python3 scripts/design_qa.py --page <page> [--strict] [--lint-json lint.json]   # --lint-json makes high lint findings fatal here
python3 scripts/ux_gate.py --spec design/<project>/ux-spec.json
python3 scripts/crop_board.py --board <b> --page <p> --out shots/<b>/ [--regions nodes.json]
python3 scripts/crop_board.py --attest shots/<b>/manifest.json
python3 scripts/export_board.py --board <board> --page <page> --out design/<project>/shots
python3 scripts/check_contrast.py --file design/<project>/tokens.json --pair fg:bg
python3 scripts/rhythm.py nodes.json [--rhythm 80]
```

- `design_lint.py` owns the **fit family**: text ink must stay inside its
  container, must not enter a sibling slot or cross a hairline rule (both
  HIGH), accent bars must match their text span (MEDIUM). Thresholds live in
  its `DEFAULTS` (uppercase ceiling 0.25 with the label-UI rationale there);
  `--rules` is a written deviation, not a silent one.
- `export_board.py` is the only path to an image, one board per call — the
  bulk renderer (`design/<project>/tools/render.py --all`) is unreliable past
  the MCP task limit, so export board-by-board and retry `render.py` per
  board instead. A tall-board export that times out usually still rendered:
  rescue the newest `penpot.*.png.*` from the exporter container.
- `export_shape` returns data, writes no file; a bound fill can still render
  white — `design_qa.py` reports that as `renderMismatches` and fails on it.
- `import_media.py` needs `PEXELS_API_KEY`, shrinks the photo itself
  (cross-fetch fails inside the sandbox; ~100KB base64 request cap), and
  attaches only while the target page is active — open it first.
- `crop_board.py` tiles the render (default 1440x900, 10% overlap) plus
  smallest-text/densest/CTA regions; reviewers mark `reviewed` + note in
  `manifest.json`, `--attest` enforces it. PIL first, ImageMagick `magick`
  fallback.
- The MCP text wraps the plugin return in a second `result` field; unwrap
  before decoding.
- Tests, one form only: `python3 -m unittest scripts/test_penpot_scripts.py`
  (66 cases, no network). `python -m py_compile` for `scripts/*.py`,
  `node --check` for helpers/build JS — never cross-check (py_compile on a
  `.js` comment once sent a clean rebuild back for inspection).

Shell and git frictions, learned the hard way:

- In zsh, separate output sections with `---`, never `echo ===` (it misparses).
- `design/*/` is gitignored: stage designs only with an explicit
  `git add -f <paths>` list, and verify with `git ls-files design/` —
  `git status`/`git diff` look empty otherwise.

## Design file conventions

- One page per product area; components on `Components`; throwaway work on
  `_scratch`, removed before handoff.
- Boards numbered for their screen (`01-home`, `02-signup`); 1440 desktop,
  390 mobile. Components `component/state` (`button/primary`); states and
  sizes in one variant family. The library is file-scoped.

## Definition of done

A screen is finished only when all eight hold on the final state:

1. `design_lint.py --page <page>` → **0 high** (fit family included; a
   medium is fixed or explained).
2. `design_qa.py --page <page> --lint-json <lint.json>` → clean,
   `renderMismatches: 0`, fills bound.
3. `check_contrast.py` → every pair used on the screen passes; pairs listed.
4. Tile-verified 1:1 review: `crop_board.py` tiles + regions for the board,
   every tile/region `reviewed: true` with a note,
   `crop_board.py --attest <manifest>` exit 0. Four places minimum: smallest
   text, densest region, primary action, every icon/arrow row — plus margin
   symmetry on the hero at 1:1.
5. Prototype: `page.flows.length` is what you claim, per-board interaction
   count non-zero after the last rebuild (rebuilds wipe interactions).
6. Independent reviewer: a different model/session scores the tiles 0–5 on
   hierarchy, story, first-5-seconds, fit, consistency, accessibility (rubric
   in `ux-design-process` §7); it reads tiles, never the spec. Two rounds max.
7. Grid edges hold: every content shape inside the declared grid, only
   declared bleeds touch the board edge — from lint `--json` geometry, plus
   margin symmetry at 1:1 on the hero.
8. `ux_gate.py --spec design/<project>/ux-spec.json` → exit 0 (task, single
   CTA, beats above the fold, states, mobile twin, claims match).

Anything not covered is reported as a gap, never as done.
