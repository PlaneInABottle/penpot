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
9. **States are part of the screen.** Hover, disabled, empty and error states are designed
   where they are reachable, not invented later in code.
10. **Prove with a render.** A token binding is intent; the exported image is evidence.

## Verification protocol

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
- **Coverage**: run the audit — unexplained hard-coded fills, unnamed shapes, orphan
  components and render mismatches are findings, not noise.
- **Craft**: measure the render against the thresholds and tells in
  `visual-interface-design`'s `references/craft-checklist.md` (type-size count and ratio,
  line-height and tracking bands, measure, accent count, placeholder-as-material, section
  rhythm). Passing them proves compliance, not design.
- **After a rebuild**, re-check the prototype: rebuilding deletes the shapes that carried
  interactions, so links vanish and a second `createFlow` leaves a duplicate with no pages.
  Re-wire, then verify `page.flows.length` and the per-board interaction count before
  claiming the file is done.
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
