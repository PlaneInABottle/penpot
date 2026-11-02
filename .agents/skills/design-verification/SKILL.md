---
name: design-verification
description: The one definition of done for a Penpot screen or file — which gate proves what, in what order, and what counts as evidence versus inference. Use when claiming a screen, board, prototype or handoff is finished, when a gate fails or a defect survived the gates, when a rebuild or copy change must be proven lossless, or before handing tokens and components to implementation. Not for design decisions (use penpot-design-system), story and review rubric (use ux-design-process), or bridge failures (use penpot-mcp-operations).
license: MIT
metadata:
  author: configs
  version: "1.1.0"
---

# Design verification

This skill owns the **definition of done**. It is the only place a screen is declared
finished: every gate command, when it runs, and what passing means. Commands are listed in
the workspace `AGENTS.md`; numeric thresholds live in the scripts
(`design_lint.DEFAULTS`/`RULES`, `ux_gate`, `build.py`) so a threshold can never drift away
from the code that applies it.

## Gates

Run in this order; a later gate does not excuse an earlier failure.

| gate | run when | passing means |
|---|---|---|
| `tokens_sync.py --check [--strict]` | after a token edit, before any build | no drift; tokens only in Penpot are printed, `--strict` also fails them |
| `design_lint.py --page <p> [--json] [--dump-nodes]` | before the first visual review of a new or rebuilt page | **0 high**; a medium is fixed or explained; exit 2 = page unmeasured, findings invalid |
| `design_qa.py --page <p> --lint-json lint.json` | with lint | verdict clean and `renderMismatches: 0`; advisory fills/unnamed/no-flow are printed and are not a clean pass |
| `check_contrast.py --file … --pair fg:bg` | before a board is claimed | every pair used on the screen passes, pairs listed |
| `contrast_audit.py --page <p>` | before claiming a board | automatic PASS/FAIL on resolved solid pairs; image, gradient, alpha, translucent and no-background texts are MANUAL — eye-check them, never count as pass |
| `rhythm.py <dump-nodes file>` | after any layout or copy move | advisory only (exit 0): gaps cluster at the declared rhythm, `>2×` and `TOP-VOID` get a written reason |
| `export_board.py --board <b> --page <p>` | together with the 1:1 review | one image per board, from the board's own id |
| `crop_board.py --board … --out …` then `--attest` | the 1:1 review itself | every tile and region the board has is `reviewed: true` with a note; `--attest` also fails a missing PNG |
| `ux_gate.py --spec design/<p>/ux-spec.json` | after the story is written, again on the final state | structural contract only: non-empty task/beats, named CTA exists, one saturated primary, firstViewport names above the fold, state/mobile names, claim counts |
| `gate.py --pages <p1,p2> [--boards …]` | a convenience run: lint → QA → copy → ux per page (+export/crop for `--boards`) | prints QA advisories and a `PASS (not clean)` line; `coverage incomplete` means an unconfigured lint rule, not clean coverage; prints `FAIL (invalid)`, never PASS, on an unmeasured page. It is **not** the definition of done: contrast, rhythm, 1:1 attest, flows and the independent review are separate gates below |

## Definition of done

A screen is finished only when all eight hold on the **final** state:

1. `design_lint.py` → 0 high (fit family included; a medium fixed or explained).
2. `design_qa.py --lint-json` → verdict clean and `renderMismatches: 0`; advisory fills keep
   it from being a clean fill count.
3. `check_contrast.py` → every listed pair passes; `contrast_audit.py` → no automatic failure
   and every MANUAL item eye-checked.
4. 1:1 attest: tiles plus the regions the board has — smallest text, densest region, primary
   action, icon/arrow row when present (`--primary-action` with `--regions`, or a
   board-relative `--region`, when the heuristic misses) — and margin symmetry on the hero
   at 1:1; `crop_board.py --attest` exit 0.
5. Prototype: `page.flows.length` is what you claim and the per-board interaction count is
   non-zero **after the last rebuild**.
6. Independent review: a different model or session scores the tiles 0–5 per axis
   (rubric: `ux-design-process` §7) reading tiles, never the spec; two rounds max.
7. Grid edges hold: every content shape inside the declared grid and only declared bleeds on
   the board edge. This is a manual `--dump-nodes` + 1:1 render check, not a script.
8. `ux_gate.py` → exit 0 for the structural contract above; whether hook→proof→path→action
   actually reads visually is item 6, never inferred from the gate.

Anything not covered is reported as a gap, never as done.

## What counts as evidence

- **Lint before eyes.** Do not open a new or rebuilt screen for visual review before lint
  reports 0 high: the eye forgives, the gate does not.
- **A PASS claim is checked by eye.** An "open item" that reads as a visual defect is not
  PASS; fix it before returning. A blocked fix is a gap, not an explanation.
- **A written shape is not paint.** Export the board and look: a binding proves intent, a
  bound fill can still render white or black, and coverage counts miss it. Then look again
  at 1:1 in every region the board has — smallest text, densest region, primary action,
  icon/arrow row when present — because page scale hides 1px rules and 16px glyphs.
- **Structure**: re-read name, size, position, children and token bindings in a later call
  than the write; the commit is asynchronous.
- **Geometry is not a render.** Clean coordinates coexist with clipped glyphs and
  overlapping bands; after any layout, measurement or icon change take the crop again.
- **Baselines, not boxes.** A line built from two text sizes gets a 2× crop on baseline
  continuity; optical alignment is invisible to a geometry dump.
- **Stale renders lie.** Never open a PNG older than the last build that touched its board;
  check mtime first, or you review yesterday's state as today's. Review carry requires the
  same board, source hash and region geometry; a changed input needs a new inspection.
- **Coverage**: unexplained hard-coded fills, unnamed shapes, orphan components and render
  mismatches are findings, not noise.
- **Craft** is checked against `visual-interface-design`'s `references/craft-checklist.md`.
  Passing its thresholds proves compliance, not design.
- **Flows**: list `page.flows` and confirm each starts from the board you claim.
- **Independent critique is not optional.** The maker's own review is not evidence; see
  `ux-design-process` §7 for the scored rubric and the `region · severity · observed` format.
- **Report** the exact page, board and token-set names, separating what was verified from
  what was inferred.

## Change discipline

- **Test the evidence pipeline, not only its arithmetic.** After a false PASS, drive the
  production collector → resolver → verdict with a real failure fixture; include inherited
  opacity, hidden layers and unsupported paint when relevant (`ContrastAuditTest`).
- **Exercise geometry away from the origin.** Crop changes need off-origin boards, the
  actual observed shape names, wrong-board reuse and mismatched render dimensions; assert
  pixels and preserved evidence, not just coordinates (`CropBoardTest`).
- **Revision labels are part of review evidence.** Name the checkout and SHA of each
  observation; a worktree's project snapshot does not describe a newer primary checkout.
- **A lint rule is earned.** Fix the screen first, then encode the defect. It starts from a defect the eye caught and lint missed: a
  failing fixture in `test_lint_rules.py` first, then the rule, then its wrong-positive
  count on the frozen corpus (`--from-nodes`, `--rules-report`) written into `RULES`.
  HIGH means 0 wrong positives there; a rule that only produces wrong positives is retired,
  and an accepted finding gets an `acknowledge` entry with a reason, never silence.
- **Edit scripts with `patch_file.py`, not by hand**: one exact `--old` block → `--new`,
  a `.bak` kept, `py_compile`/`node --check`/`json.load` before the edit is accepted.
- **Copy rides along, never retyped.** After any copy-touching change read the diff's `string lines`
  one by one — kicker against title, numbers against claims, names against the brief.
  No gate and no dictionary catches a real word in the wrong place.
- **A rebuild is lossless or it is not done.** A rebuild deletes the shapes that carried
  photos and interactions: re-place every provenance photo, re-wire the links, then verify
  live `photos N/N`, `links N/N`, `page.flows.length` and the per-board interaction count.
  Automate the repair in the build runner so no manual step remains.
- **Sweep by fingerprint, not by helper name.** When a repeated pattern changes, enumerate
  its literals (magic numbers, `wire(...)` entries, board lists) and diff that list against
  the helper's caller list; anything on one but not the other is the finding.
- **One writer per page.** Ownership, the plugin lock and `--read` intent are stated once in
  `AGENTS.md` § Ownership and safety; this skill does not restate them.

## Handoff to implementation

Give four artifacts, not a screenshot:

1. **Token table** — name, value, role.
2. **Component inventory** — name, variants, slots, where used.
3. **Board list** — page, board name, id, target width, responsive notes.
4. **Export evidence** — board id, format, byte size per screen, whether the client saved a file.

Code follows the tokens and the component structure, never exported CSS or pixel coordinates.
