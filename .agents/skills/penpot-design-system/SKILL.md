---
name: penpot-design-system
description: Design in Penpot — turn a brief into a token set, component library, screens and a clickable prototype inside a real Penpot file, then hand a token and component inventory to implementation. Use when a task needs a design file, token set, component library, screen mockup in Penpot, clickable prototype built there, or an export and handoff of tokens or components from a Penpot file. Not for polishing an existing code UI (use refactoring-ui), page design outside Penpot (use visual-interface-design), or scripting and debugging the Penpot MCP bridge (use penpot-mcp-operations).
license: MIT
metadata:
  author: configs
  version: "2.0.0"
---

# Penpot design system

Produce the design artifact inside a real Penpot file and prove it exists: tokens first,
components second, screens third, prototype links fourth, verification last. This skill
owns the process, the design decisions and the evidence. Art direction and layout
judgement come from `visual-interface-design`; this skill realises them in Penpot. Tool
mechanics, the helper library and every known MCP failure live in `penpot-mcp-operations`.

## Preconditions

- The target file is open in a browser tab with the MCP plugin connected. A write that
  fails with `No Penpot instance connected for user token.` is a downed bridge, not a
  design problem: switch to `penpot-mcp-operations` or stop and ask.
- Page names, token set names, board numbering and target widths come from the project
  `AGENTS.md`. Never invent a second scheme.
- `high_level_overview` and `penpot_api_info` on the MCP server answer signature questions;
  do not duplicate them in notes.

## Step 0 — inventory

Read before creating: `penpot.currentFile.pages`, token sets (`library.local.tokens.sets`),
components (`library.local.components`), flows, and a coverage audit of the target page.
Reuse a set, component or board instead of adding a parallel one, and state the target
page, target width (1440 desktop, 390 mobile) and the token-set name before the first
write. A brief that names a different palette than the file already uses is a decision to
surface, not to execute twice.

## Order of work

One path, in order. A later step that invents a value an earlier step owns is a defect:
screens never hard-code a hex, components never carry per-screen spacing. The six phases and
the file each one writes are declared in the workspace `AGENTS.md`; this skill owns the work
inside phases 3–5.

### 1. Foundations

One token set for colour, spacing, radius and font sizes, reconciled by name
(`syncTokens`). The set the screens use must be active. Names are role paths, unique
across types within a set (`color.surface`, `space.md`, `radius.md`), never two tokens
called `md`. Values that a token cannot express — line height, letter tracking, stroke
widths, shadows — stay a documented convention, not an undeclared literal.

### 2. Components

Build only what repeats verbatim: navigation, buttons, badges, alerts, footer, inputs.
Content cards whose copy changes per row are templates in the build script, not components
— a component whose every instance overrides every text is a template with extra steps.
States and sizes of one component belong to one variant family (`transformInVariant`).

### 3. Screens

Boards at the target width, one page per product area, numbered and named for the screen.
Sections get a container and a fixed rhythm instead of ad-hoc coordinates; absolute
placement is for overlays and freeform art. Every screen carries the same navigation and
footer instance, so a change to them reaches all screens.

### 4. Prototype

One flow per journey from a real starting board, `navigate-to` links on the elements a
user would actually click, overlays for menus and modals. Always pass `easing`. A flow can
drop while its interactions remain — audit `page.flows` and repair with `createFlow`.

### 5. Verify, then hand off

Run the protocol below on every screen claimed as finished — a written board is inferred,
not done — then hand off.

## One system per project, not one palette

A new project inside an existing workspace is the highest-risk case for sameness: the
previous `lib.js`, section blocks and page rhythm are right there to copy. Reusing the
primitive library reuses the grammar, and a new accent colour on old primitives produces
the old page.

Before the first screen, write down four structural axes and make them differ:

1. **Surface** — light / dark / tinted, and what the text colour is.
2. **Density** — the section rhythm and the data-row height in px.
3. **Navigation model** — masthead, rail, status bar, or none.
4. **One element that exists only in this product** — a numeral spine, a viewer chrome,
   a schedule gutter. If it can be removed without loss, it is decoration.

Then write a new `lib.js` from those axes. Do not import the previous project's atoms.
Thumbnail test before building 20 screens: at 200px wide, the home page must not be
mistakable for the previous project. If it is, change an axis, not the accent.

## Design rules

1. **One set per brand area, active, reused.** A second palette is a theme, not a second
   screen.
2. **No undeclared value.** A colour, size or gap that a token owns is applied through the
   token; a gap in the scale is reported, not filled with a literal.
3. **One accent per view.** The accent marks action and time; a second accent means the
   hierarchy is wrong.
4. **Rhythm before detail.** One spacing scale (4/8 based), one radius scale, one type
   scale; hierarchy comes from weight and colour before size.
5. **Same token names on every rebuild.** A regenerated screen must reconcile, not
   duplicate.
6. **Reuse before creating.** Existing set, component, board or flow wins over a new one.
7. **The file stays clean.** Scratch work on a scratch page, removed before handoff; the
   library is file-scoped, so deleting a page leaves its sets behind.
8. **Content is real.** Real strings, real dates, real prices; no lorem ipsum and no
   placeholder that a reviewer would mistake for copy.
   When the direction changes, grep the old vocabulary project-wide BEFORE freezing the
   new scope — frozen leftovers contradict the new story. Sync every changed string back
   into brief §5 (as-built conformance), or the brief stops being the source of truth and
   the next milestone re-introduces the old words.
9. **States are part of the screen.** Hover, disabled, empty and error states are designed
   where they are reachable, not invented later in code.
10. **Prove with a render.** A token binding is intent; the exported image is evidence.

## Origins are never zero (boards, slots, shapes)

Shape coords are page-absolute even inside a board, so any placer that takes
board-local numbers must add `board.x/board.y` before assigning. A photo that renders
exactly one board-height too high is this bug, not a bad crop. Prefer reading live
slot geometry (already absolute) over passing numbers in.

## Grid is code, not documentation

Incident (İHKD 01, Oct 2026): the hero photo was written as x=800 w=640 on a 1440 board,
so it ended at 1440 — the board edge — instead of the 1320 content edge. Lint was clean
(overflow only fires past the *board*), QA was clean, the page-scale render looked almost
right. A 120px asymmetry survived every gate because the grid lived only in prose.

- Derive, don't decorate. Every content x/w comes from the grid constants (X, CW):
  a right-aligned block is `x = X + CW - w`, a half is `(CW - gap) / 2`. A literal that
  was hand-added to "reach the edge" is a defect until proven otherwise.
- Declared bleeds. Each screen lists the shapes allowed to touch the board edge
  (x=0, w=board width) — bands, bleeds, footers. Anything else must satisfy
  X <= x and x + w <= X + CW. An undeclared edge-touch is a finding, not a style.
- Audit from geometry, not eyes. `design_lint.py --page <p> --json` already collects
  x/y/w/h per node; assert the grid edges from that file with a ten-line check. Eyeballing
  a page-scale render is how the 120px survived — it is not a verification method.
- 1:1 the margins. The four verification crops gain a fifth: left/right margin symmetry
  at the hero and at one dense section. Asymmetry hides at page scale and nowhere else.

## Slots derive from content

A slot's height comes from its measured content, never from a fixed grid
constant. A time grid that maps minutes to px while copy height varies paints
text over the next row — the lint `fit` family reports that after the fact;
build it right the first time instead.

- `assets/fit-slot.js` (loaded like `helpers.js`, exposes `storage.FIT`):
  `fitSlotLive(container, children, opts)` grows the container to its ink
  union plus padding; `fitRows(totalH, rows)` splits a fixed grid across
  minima plus weights; `rideDown(shapes, fromY, dy)` moves followers.
- A fixed slot that cannot hold its content is a **build error**
  (`fitSlotLive` with `fixed`, or `fitRows` minima over total) — it throws,
  the screen fails, the copy shortens or the slot grows. A warning scrolls
  by; an error stops the screen.
- After any copy swap, re-run the slot fit on the touched board before
  exporting: `lint` proves the last build, `FIT` prevents the next defect.
- **Rows come from one helper, never from hand-written y.** A repeating
  row (list, table, schedule, curriculum) is built with a single
  `rows(items)` call: each item declares its content-derived block height
  and a `draw(yRow, hRow)` that centers its content; the separator always
  lands on the block's bottom edge. A manual `y + 64` next to a manual
  rule y is how a separator drifts into a text's middle — the helper makes
  that shape of code unwritable. Fixed-pitch grids throw when content
  exceeds the pitch instead of overlapping.
- **One arithmetic chain per screen.** Every y below the masthead derives
  from a cursor (`y = rows(...); y = head(y + gap...)`), never from a
  literal. Cards, lists, schedules and side panels share the same chain,
  so a taller row above pushes everything below instead of burying it.
  A literal y past the head is a defect, not a shortcut.

## Media and rhythm (generic)

- **Rebuilds wipe photos; reimport every slot on the board, not just the touched
  one.** `build` clears all children including placed images, so a milestone that
  rebuilds for slot A and re-imports only slot A silently deletes slot B (İHKD 01:
  hero rebuild restored img-echo, img-journal stayed an empty mat through green
  lint+QA — token coverage counts the placeholder's bound fill, so gates can't see
  it). After ANY rebuild, re-import ALL slots of that board and prove each with
  `media-audit --live` (photo placed, not merely slot present) plus a 1:1 look.
- **The media table is the single source for photo choice.** A one-off inline import
  (different query, pinned URL tried by hand) regresses on the next rebuild
  reimport, which re-runs the table query (İHKD 01 hero silently reverted to the
  masked photo one milestone later). Persist the winning query or pinned URL in
  the table the moment a photo is accepted, then reimport from the table.
- **A photo replaces its slot, never covers it.** Name every image slot, import by that
  name, and delete the placeholder rect in the placing call. Before/after the import the
  board holds exactly one shape under that name. A render showing an empty mat next to
  (or under) a photo is a finding, not a style.
- **Scope every reimport with `--only`.** A bare `--board` retargets ALL table slots
  to that board and misfires photos across pages (İHKD: one unscoped call sprayed
  slots; correct form is always `--only a,b --board B --page P --force`).
- **Slots are measured, not assumed.** Read the slot's committed `width`/`height` in the
  call before the import and crop to that aspect; re-cropping to a guessed size is how a
  face ends up behind a caption. Cropping to the slot is allowed to change — cropping to
  a stale number is not.
- **Copy edits re-budget geometry.** A headline that gains width or loses a line
  invalidates every neighbor clearance the old copy had — re-measure ink against
  adjacent shapes instead of trusting the old box (İHKD 01: one-line hero slid 14px
  under its photo). The text-over-shape lint check exists for exactly this; a new flag
  after a copy edit means the layout moved, not that the rule is noisy.
  Line-count changes cascade: body text in auto-height boxes absorbs the new copy,
  but followers at fixed y do NOT move — a shortened paragraph leaves a dead void
  (İHKD 19: 2-line claim became 1 line, body stayed, 170px gap), a lengthened one
  overlaps (the text-overlap lint catches that direction). After any copy swap,
  re-run the rhythm audit on the touched boards and read the section, not just the
  edited line.
- **CTAs dock to their text column.** A button floating in the opposite column's
  airspace reads lost no matter how even the clearance (İHKD 06: "Kayıt ol" alone
  at x1104 while its lede lived at x120). Dock the action under its own text,
  then ride everything below down — never park a CTA where no text leads to it.
- **Seams are not shelves.** A leftover band between two sections gets ONE gesture,
  not a stack: label + trace + CTA crammed into 96px read as three competing
  lines (İHKD 01 V3). Promote the seam to a band (one red mass: white ECG + two
  white lines + link) or delete elements until one voice remains.
- **Dividers on cell boundaries, numbers inset uniformly.** In a stat row, float the
  dividers to exact cell boundaries and give every number the same left inset;
  dividers parked at "column minus a guess" drift with digit width and read
  accidental (İHKD 01: 120/203/197/243px tails). Raggedness belongs inside the
  cell's dead side, never between a digit and its divider.
- **One right edge per row group.** A right-aligned column must terminate at the
  grid edge or at the next column's start. Two different right edges in one list
  (İHKD 01 course rows: meta ended at 1180, CTA at 1320) read as misaligned even
  though every box is internally "aligned" — the lint cannot see this, only a
  full-width 1:1 crop can. When in doubt, left-align the data column at a fixed x
  and keep a single right-aligned action column on the grid edge.
- **Board children use page-absolute coords — pad them like it.** S.board children
  position from the page origin, not the board edge, so `x:120` inside a board at
  `x:120` is zero padding against a stroked edge (İHKD 04 propose: label, title
  and CTA all inked at the stroke). Keep ≥16px between a text's ink left edge and
  a stroked/surface panel edge; pills (single-label chips) and full-bleed boards
  at x=0 are exempt by design. The lint `panel padding` medium guards this —
  a flag after a board move means the layout shifted, not that the rule is noisy.
- **One baseline zone, one voice.** Two different-size/color texts sharing a y-band
  read as one broken line even with a few px of clearance (İHKD 01 hero: photo
  caption vs red congress label). Give the band to one of them: delete, stack with
  ≥1 rhythm step, or divide explicitly. The lint `text collides` medium guards true
  ink overlap; the near-miss is a 1:1 judgment call.
- **1:1 the joint, not the element.** A crop centered on a headline proves the headline;
  the defect lives where two things meet. Frame verification crops on boundaries:
  text/photo edges, row/meta joints, panel/footer seams.
- **Rows align from one shared top, never three hand-tuned offsets.** A meta+title
  row (date, category, headline) tempts three different y values that "look aligned";
  they never are, because each size carries its own ink offset (İHKD 01 gündem: three
  offsets, all wrong). Start every box in the row at the SAME y, then nudge the small
  text as a group from a 2x crop until ink tops agree within 2px (max two rounds, keep
  the best). The `inline mixed-size pair` lint flags exactly this pattern — clear the
  flag instead of explaining it.
- **One line, one box — or computed baselines.** A value+unit line faked with two
  top-aligned boxes at different sizes always drifts, because box tops are not
  baselines and nobody measures the joint. Either use a single text node, stack the
  parts vertically (value over unit label — no baseline math, looks deliberate), or
  compute both baselines from committed `textBounds` in a later call and nudge. The
  lint rule `inline mixed-size pair` flags every top-aligned mixed-size adjacency for
  a 1:1 baseline read; a flag is a review pointer, not a failure.
- **Footers dock to content, panels are sums not slabs.** A footer sits at
  last-content-bottom + section rhythm; a board ends at footer + footer height. A
  hardcoded footer y survives every layout change above it and leaves a dead canvas
  void (İHKD 04: 556px of nothing). After any block move, recompute both numbers and
  confirm with the rhythm audit — a trailing void is a finding, never air.
- **Stale renders lie.** Never open a PNG older than the last build that touched its
  board — check mtime first. Reviewing yesterday's export as today's state invents
  defects and hides real ones.
- **Panels are sums, not slabs.** A panel's height is paddings plus its stacked
  content; after any content move, recompute it. A panel with a dead middle third is
  a recompose signal, not whitespace.
- **Rhythm is declared, then audited.** The brief states the section rhythm in px (and
  the data-row height). After the build, list every board's top-level y-gaps from the
  lint `--json` geometry: gaps cluster at the rhythm, and any gap beyond 2× the rhythm
  needs a reason written in the brief, not a shrug. Margin symmetry (left vs right at
  the hero) is checked at 1:1, never at page scale.
- **The head joint gets its own audit.** A shared head helper (pageHead) hardcodes the
  label/title/lede/rule spacing — one stale number there voids every page at once
  (İHKD: label at y=236 under a rule at y=84 left 152px of dead air on nine pages;
  the fix tightened the helper to label 156 / rule 352 and rode every follower up
  80px). After any head change, read the masthead-rule→first-content gap on every
  affected board: anything much past one rhythm step is a finding. The rhythm
  `TOP-VOID` line guards exactly this joint.

## Verification protocol

- **Lint before eyes.** A new or rebuilt component/screen is not opened
  for visual review until `design_lint.py` reports 0 high on its page —
  the eye forgives, the gate does not.
- **A missed visual defect becomes a rule first.** When eyes catch what
  lint missed (a text sitting on a sibling control, a rule through a
  middle line), write the failing test, then the rule, then the fix — in
  that order. The DAHİL/'Devam et' overlap and the mid-row separator both
  entered the gate this way.
- **A "looked at 1:1" claim without an attested manifest is not evidence.**
  Tile the render with `crop_board.py`, review every tile and region, mark
  `reviewed` with a finding note, and let `--attest` pass — that is the
  1:1 review, not a sentence in a report.

- **Structure**: read back name, size, position, children and token bindings for every
  claimed shape in a later call than the write.
- **Paint**: export each finished screen by its own board id and look at the image. A
  bound fill can still render white or black; coverage counts do not catch it. Then look
  again at **1:1** in four places: the smallest text, the densest region, the primary
  action, and every row that carries an icon, arrow or marker. A page-scale view hides 1px
  rules and 16px glyphs, which is where the defects live.
- **Geometry is not a render.** Clean coordinates coexist with overlapping bands and
  clipped glyphs; after any layout, measurement or icon change, take the crop again instead
  of trusting the read-back.
- **Baselines, not boxes.** Any line composed of two text nodes at different sizes gets
  a 2× crop checking baseline continuity. Eye-measured offsets always drift; the lint
  geometry cannot see optical alignment, only you can.
- **Coverage**: run the audit — unexplained hard-coded fills, unnamed shapes, orphan
  components and render mismatches are findings, not noise.
- **Craft**: measure the render against the thresholds and tells in
  `visual-interface-design`'s `references/craft-checklist.md` (type-size count and ratio,
  line-height and tracking bands, measure, accent count, placeholder-as-material, section
  rhythm). Passing them proves compliance, not design.
- **After a rebuild**, re-check the prototype: rebuilding deletes the shapes that carried
  interactions, so links vanish and a second `createFlow` leaves a duplicate with no pages.
  Re-wire, then verify `page.flows.length` and the per-board interaction count before
  claiming the file is done. This step is DoD item 5 — it is never scoped out of a
  rebuild milestone; a 10-board tighten once shipped with four boards' links wiped
  because re-link was left for "later", and only a post-hoc flows re-apply caught it.
- **Sweep by fingerprint, not by helper name.** A helper change reaches only its callers;
  hand-rolled copies of the same numbers do not move (pageHead tightened, but 18-uyelik
  painted its own head with the old 236/500 and kept the 152px void; flows.js wired
  every board except 15-haberler while its own header comment claimed it did). When a
  repeated pattern changes, enumerate occurrences by the pattern's literals — the magic
  numbers, the `wire(...)` entries, the board list — and diff that enumeration against
  the helper's caller list. Anything on one list but not the other is the finding.
- **Independent critique**: the maker's own check is not evidence. A separate reviewer opens
  the render and 2× crops (densest region, smallest text, primary action) and returns
  `region · severity · observed vs brief` findings; it does not rewrite. One round, then the
  owner decides.
- **Flows**: list `page.flows` and confirm each starts from the board you claim.
- **Report** the exact page, board and token-set names, and separate what was verified
  from what was inferred.

## Handoff to implementation

Give the implementer four artifacts, not a screenshot:

1. Token table — name, value, role.
2. Component inventory — name, variants, slots, where used.
3. Board list — page, board name, board id, target width, responsive notes.
4. Export evidence — board id, format, byte size per screen, and whether the client saved
   a file.

Code follows the tokens and the component structure, never exported CSS or pixel
coordinates.
