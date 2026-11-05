---
name: penpot-design-system
description: Design in Penpot — turn a brief into a token set, component library, screens and a clickable prototype inside a real Penpot file, then hand a token and component inventory to implementation. Use when a task needs a design file, token set, component library, screen mockup in Penpot, clickable prototype built there, or an export and handoff of tokens or components from a Penpot file. Not for polishing an existing code UI (use refactoring-ui), page design outside Penpot (use visual-interface-design), or scripting and debugging the Penpot MCP bridge (use penpot-mcp-operations).
license: MIT
metadata:
  author: configs
  version: "3.1.0"
---

# Penpot design system

Produce the artifact inside a real Penpot file and prove it exists: tokens first, components
second, screens third, prototype links fourth, verification last. This skill owns the
process and the design decisions. Art direction comes from `visual-interface-design`; its
§ Two Internal Checks, One Delivery governs the maker's idea-fit and rendered-execution
checks. Layout mechanics from `references/craft.md`; tool mechanics and the failure table from
`penpot-mcp-operations`; the definition of done from `design-verification`.

## Preconditions

- The target file is open in a browser tab with the MCP `plugin connected`. A write that fails
  with `No Penpot instance connected for user token.` is a downed bridge, not a design
  problem: switch to `penpot-mcp-operations` or stop and ask.
- Page names, token-set names, board numbering and target widths come from the project brief.
  `never invent a second scheme`.
- Signature and API questions are answered by `penpot_api_info` / `high_level_overview` on the
  MCP server; do not copy their answers into notes.

## Step 0 — inventory

Read before creating: `penpot.currentFile.pages`, token sets (`library.local.tokens.sets`),
components (`library.local.components`), flows, and a coverage audit of the target page.

- `reuse` an existing set, component, board or flow instead of adding a parallel one; state
  the target page, target width (1440 desktop, 390 mobile) and token-set name before the
  first write.
- A brief that names a different `palette` than the file already uses is a decision to
  surface, not to execute twice.

## Lifecycle

Seven phases, in order, for a new project. A later step must not invent a value an earlier
step owns: screens never hard-code a hex, components never carry per-screen
spacing. Each phase writes a file before the next starts; no artifact, no phase. Existing work
resumes at the affected phase and reuses valid artifacts, without unnecessary intake or files.
Rerun checks and review where changed inputs invalidate their evidence.

| # | Phase | Writes | `Exit` condition |
|---|---|---|---|
| 1 | Intake | `brief.md` — audience, single job, content truth, constraints | answers exist or are marked unknown |
| 2 | Direction | `brief.md` § direction · `principles.md` | 2–3 named directions, one chosen, rejects recorded; a taste-bearing hero instead gets 4–5 finished first viewports and the user chooses (`ux-design-process` § 3) |
| 3 | Story | `ux-spec.json` — task, hook→proof→path→action, hero contract, states, mobile, claims | `ux_gate.py` exit 0, or findings owned with a reason |
| 4 | Foundations | `tokens.json` · Penpot set · `Components` page | `tokens_sync --check` no drift; extras explained or `--strict`; every component instanced once |
| 5 | Screens | `build/screen-NN.js` per screen | applicable screen checks from `design-verification`: lint, QA, contrast, 1:1 attest, grid edges; not a PASS — full definition of done at handoff |
| 6 | Prototype | flows and links on the screens | links completed; one flow, per-board interaction count verified post-rebuild |
| 7 | Handoff | `README.md` · `shots/` · media provenance | the full eight-item definition of done on the final state; token/component inventory, board list, export evidence, gaps stated |

One project folder per design. Page, board and set names come from that project's `brief.md`;
boards are numbered for their screen, at `1440` desktop and 390 mobile, with
`component/state` names, components on the `Components` page and task-owned throwaway work on
`_scratch`, cleaned up at handoff. User-kept candidate boards follow `design-variety`'s parking
rule and are never deleted because handoff arrived. Build scripts are `idempotent` —
check-then-create, rebuild from scratch — and run one at a time through `build.py`.

## Start a new project

```sh
cp -R design/_template design/<name>
python3 scripts/tokens_sync.py --file design/<name>/tokens.json --set <set>
```

The template ships `brief.md`, `principles.md`, `tokens.json`, a `ux-spec.json` whose
placeholders fail `ux_gate` until answered, `craft-rules.json` declaring the template's
surface palette, empty `copy-terms.json`, plus the `build/README.md` and `media/README.md` notes. Write the new `design/<name>/build/lib.js`
from the four axes below; copying the previous project's `lib.js` is the failure this template
exists to prevent. The generic importer does not write `media/provenance.json`; persist each
accepted source there — that table is what a rebuild restores. The template ships no runner:
provide `build/build.py` with the lossless-rebuild contract before claiming a screen.

## Foundations and components

1. **Foundations.** One token set for colour, spacing, radius and font sizes, `reconciled by name`
   (`syncTokens`); the set the screens use must be active. Names are `role path`s,
   unique across types within a set (`color.surface`, `space.md`, `radius.md`) — never two
   tokens called `md`. Values a token cannot express — line height, letter tracking, stroke
   width, shadows — stay a `documented convention`, not an undeclared literal. Declare the
   surface palette in `craft-rules.json` (`surface_white`, `surface_alt`) from the tokens;
   without it `surface.role` warns and skips rather than assume a project's hex.
2. **Components.** Build only what repeats verbatim: navigation, buttons, badges, alerts,
   footer, inputs. Content cards whose copy changes per row are a `template` in the build
   script, not a component — a component whose every instance overrides every text is a
   template with extra steps. States and sizes of one component are one `variant family`.
3. **Screens.** Boards at the target width, one page per product area, sections with a
   container and a fixed rhythm; absolute placement is for `overlays` and freeform art. Every
   screen carries the same `nav` and footer instance, so a change reaches all screens.
4. **Prototype.** One flow per journey from a real starting board, links on what a user would
   click, overlays for menus and modals, always `easing`. Audit `page.flows` after a rebuild.
5. **Verify, then hand off.** A written board is inferred, not done: run the `gates` in
   `design-verification` on every screen you claim, then hand off with its four artifacts.

## One system per project, not one palette

A new project inside an existing workspace is the highest-risk case for sameness: the
previous `lib.js`, section blocks and page rhythm are right there to copy. Reusing the
primitive library reuses the grammar, and a new accent on old primitives produces the old
page. Before the first screen, write down `four structural axes` and make them differ:

1. **Surface** — light / dark / tinted, and what the text colour is.
2. **Density** — the section rhythm and the data-row height in px.
3. **Navigation model** — masthead, rail, status bar, or none.
4. **One element that exists only in this product** — a numeral spine, a viewer chrome, a
   schedule gutter. If it can be removed without loss, it is decoration.

Then write a new `lib.js` from those axes: `no previous atoms`. Before building 20 screens,
run the `thumbnail test` at 200px wide — the home page must not be mistakable for the
previous project. If it is, change an axis, not the accent.

## Design rules

1. **`one set per brand area`**, active, reused. A second palette is a theme, not a second screen.
2. **`no undeclared value`.** A colour, size or gap that a token owns is applied through the
   token; a gap in the scale is reported, not filled with a literal.
3. **`one accent per view`.** The accent marks action and time; a second accent means the
   hierarchy is wrong. Likewise one saturated primary button per board — every other action
   is a ghost or a link, and dominance is visual: the gate counts saturated fills.
4. **`rhythm before detail`.** One spacing scale (4/8 based), one radius scale, one type
   scale; hierarchy comes from weight and colour before size.
5. **`same token names` on every rebuild.** A regenerated screen reconciles, never duplicates.
6. **`reuse before creating`.** An existing set, component, board or flow wins over a new one.
7. **The file stays clean.** Scratch work lives on a scratch page; handoff cleanup removes
   only task-owned temporary work and never a kept candidate (`design-variety` § Park, do not
   delete). The library is `file-scoped`, so deleting a page leaves its sets behind.
8. **`content is truthful`.** Use real production strings, dates and prices when they are
   known; otherwise label concept, demo or sample data explicitly — never lorem ipsum or fake
   proof. Do not invent claimed shipping capability or customer statistics. When the
   direction changes, grep the old vocabulary project-wide before freezing the new scope and
   sync every changed string back into the brief, or the next milestone re-introduces the old
   words.
9. **`states are part of the screen`.** Hover, disabled, empty and error states are designed
   where they are reachable, not invented later in code.
10. **`prove with a render`.** A token binding is intent; the exported image is evidence.
11. **`openings end on the fold`.** A full-bleed opening block ends on the fold: anchor its
    foot (signature, trace, imprint) to the block's bottom edge, never to a fixed offset.

## Layout mechanics

`references/craft.md` holds the geometry: origins, grid as code, slots and helpers, media,
rhythm and optical joints. Read it before writing a placer or a row helper — every rule there
exists because a gate passed while the pixels were wrong.
