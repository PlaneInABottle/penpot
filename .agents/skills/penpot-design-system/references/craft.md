# Layout craft

Mechanics a build applies. Design judgement lives in `visual-interface-design`, the process
in `../SKILL.md`, the proof in `design-verification`. Every rule here exists because a gate
passed while the pixels were wrong.

## Contents

- Origins are never zero · Grid is code · Slots derive from content · Repeated blocks
- Media · Surfaces · Rhythm and joints · Optical joints · At a second width

## Origins are never zero

Shape coords are `page-absolute` even inside a board, so any placer that takes board-local
numbers must add `board.x`/`board.y` before assigning. A photo that renders exactly one
board-height too high is this bug, not a bad crop. Prefer reading live slot geometry
(already absolute) over passing numbers in.

## Grid is code, not documentation

Prose is not a constraint; the numbers in the build are. A grid that lives only in a brief
survives every gate while a 120px asymmetry ships.

- **Derive, don't decorate.** Every content `x`/`w` comes from the grid constants (`X`,
  `CW`): a right-aligned block is `x = X + CW - w`, a half is `(CW - gap) / 2`. A literal
  hand-added to "reach the edge" is a defect until proven otherwise — overflow lint fires
  past the *board*, so an edge-aligned block reads clean.
- **Declared bleeds.** Each screen lists the shapes allowed to touch the board edge (bands,
  bleeds, footers). Everything else satisfies `X <= x` and `x + w <= X + CW`; an undeclared
  edge-touch is a finding, not a style.
- **1:1 the margins.** Margin symmetry at the hero and at one dense section is checked in a
  crop, never at page scale. Asymmetry hides at page scale and nowhere else.

## Slots derive from content

A slot's height comes from its measured content, never from a fixed grid constant. A row's
height comes from its tallest card, never from an average — and a card whose **fill ratio**
(ink span over card height) drops under 0.6 is a box around air: shrink the card, not the
content. A time grid that maps minutes to px while copy height varies paints text over the
next row.

- `assets/fit-slot.js` (loaded like `helpers.js`, exposes `storage.FIT`): `fitSlotLive(container,
  children, opts)` grows the container to its ink union plus padding; `fitRows(totalH, rows)`
  splits a fixed grid across minima plus weights; `rideDown(shapes, fromY, dy)` moves followers.
- A fixed slot that cannot hold its content is a **build error** (`fitSlotLive` with `fixed`,
  or `fitRows` minima over total) — it `throws`, the screen fails, the copy shortens or the
  slot grows. A warning scrolls by; an error stops the screen.
- After any copy swap, `re-run` the slot fit on the touched board before exporting: lint
  proves the last build, `storage.FIT` prevents the next defect.
- **One arithmetic chain per screen.** Every y below the masthead derives from a cursor
  (`y = rows(...); y = head(y + gap...)`), never from a literal. A literal y past the head is
  a defect, not a shortcut.
- **Seed every box, trust no commit.** A shape created without dimensions (bare auto-width
  text, unmeasured slot) is invisible until Penpot's async layout reaches it — on a
  board-scale build that can be never. Estimate the box at creation (`estLines`), let `fit()`
  tighten it after commit, gate the 1×1 leftover in lint. Never retry a timed-out build
  blindly: the first task may still be running server-side.

## Repeated blocks have one helper

- **`rows(items)`** builds every list, table, schedule and curriculum: each item declares its
  content-derived block height and a `draw(yRow, hRow)` that centres its content; the
  separator always lands on the block's bottom edge. A manual `y + 64` next to a manual rule y
  is how a separator drifts into a text's middle — the helper makes that shape of code
  unwritable, and a fixed-pitch grid throws when content exceeds the pitch.
- **`bullets()`**, one helper, dots on the cap centre: a hand-placed dot at `row + 6` sits
  2–4px high on every list because the ink is centred in its line box — dot centre is
  `lineBox / 2` and the dot opts out of the 4px snap (`raw`). The separator belongs to the
  block's bottom edge, which is what makes the air above and below match.
- **`fitCards(...)`**, cards are their content: content-sized card, symmetric pad, row pitch =
  tallest + 8, and a post-fit pass re-settles each box on measured ink. A conservative
  estimate leaves 20–50px of white under one meta; leftover air belongs outside the card,
  where it is the schedule's rhythm. Equalising a row never stretches a card.
- **The `column band`, not the box, is the fit container.** A row divided only by a hairline
  has no box, so a title can leave its column with every container check green. Derive the
  title box from the band (band − inset − arrow gutter) and the row height from the measured
  line count; lint's `column band` rule measures ink against the rule's own length.

## Media

- **Rebuilds wipe photos; reimport every slot on the board, not just the touched one.**
  A build clears all children including placed images, so re-importing only slot A deletes
  slot B — and token coverage counts the placeholder's bound fill, so gates stay green.
- **The media table is the single source for photo choice.** Persist the winning query or
  pinned URL in the table the moment a photo is accepted, then reimport from the table; a
  one-off inline import regresses on the next rebuild. The generic `import_media.py` only
  prints provenance — it writes no table and takes no `--only`/`--force`; that is a project
  tool's job.
- **A photo replaces its slot, never covers it.** Name every image slot, import by that name,
  delete the placeholder rect in the placing call; after the import the board holds exactly
  one shape under that name. An empty mat next to a photo is a finding, not a style.
- **Scope every reimport to its slots.** A project media tool that owns the table can use
  `--only a,b --board B --page P --force`; a bare `--board` retargets every slot and sprays
  photos across pages.
- **Slots are measured, and crops are verified.** Read the slot's committed width/height in
  the call before the import and `crop` to that aspect — re-cropping to a guess is how a face
  ends up behind a caption. After placing, open the 1:1 tile and confirm the subject survives
  (face, hands, equipment — whatever the art direction names); a decapitated subject is a
  reshoot. Provenance lives in the media table, not in canvas captions.
- **A photo's subject must name the product's field.** A "plausible clinical scene" reads as
  stock filling; the accepted frame carries the domain's own object (the specific instrument,
  trace or model). The pinned URL in the media table lets a rebuild reimport it, and the
  caption never has to hide the mismatch.

## Surfaces

- **Two neutral layers per screen.** `paper` is the ground, `white` the card surface, and
  `surface.alt` only an inset or side panel. A card in `surface.alt` while its sibling
  screens use `white` is an inconsistency to fix, not a variation to explain.
- **Declare the palette.** Put the white/alt hexes in `craft-rules.json`
  (`surface_white`, `surface_alt`) so `surface.role` reads this project's tokens; without
  the declaration the rule warns and skips, and a green lint means nothing for this check.

## Rhythm and joints

- **Rhythm is declared, then audited.** The brief states the section rhythm in px (and the
  data-row height); after the build, list every board's top-level y-gaps from
  `design_lint.py --dump-nodes` geometry (`--json` is findings, not geometry). Gaps cluster
  at the rhythm; `rhythm.py` prints a beyond-2× gap as advisory, and it needs a written reason.
- **The head joint gets its own audit.** A shared head helper hardcodes the
  label/title/lede/rule spacing — one stale number voids every page at once. After any head
  change, read the masthead-rule→first-content gap on every affected board; anything much past
  one rhythm step needs a reason, and the rhythm `TOP-VOID` advisory line flags exactly this
  joint (`--rule-name` when the head rule is named otherwise).
- **Footers dock to content, panels are sums not slabs.** A footer sits at
  last-content-bottom + section rhythm and the board ends at footer + footer height; a
  hardcoded footer y survives every change above it and leaves dead canvas. A panel's height
  is paddings plus its stacked content, and a dead middle third is a recompose signal, not
  whitespace.
- **CTAs dock to their text column.** A button floating in the opposite column's airspace
  reads lost however even the clearance. Dock the action under its own text, then ride
  everything below down.
- **Seams are not shelves.** A leftover band between two sections gets ONE gesture, not a
  stack: label + trace + CTA crammed into 96px read as three competing lines. Promote the
  `seam` to a band with one voice, or delete elements until one remains.
- **Dividers on cell boundaries, numbers inset uniformly.** Float `divider`s to exact cell
  boundaries and give every number the same left inset; a divider parked at "column minus a
  guess" drifts with digit width. Raggedness belongs inside the cell's dead side.
- **One right edge per row group.** A right-aligned column terminates at the grid edge or at
  the next column's start. Two different right edges in one list read as misaligned even
  though every box is internally aligned — no lint sees this, only a full-width 1:1 crop.
- **Board children use page-absolute coords — pad them like it.** `x:120` inside a board at
  `x:120` is zero padding against a stroked edge. Keep `≥16px` between a text's ink left edge
  and a stroked/surface panel edge; pills and full-bleed boards at x=0 are exempt by design.
- **Copy edits re-budget geometry.** A headline that gains width or loses a line invalidates
  every neighbour clearance the old copy had: re-measure ink against adjacent shapes and
  re-run the rhythm audit on the touched boards, reading the section and not just the edited
  line. A shortened paragraph leaves a dead void, a lengthened one overlaps.

## Optical joints

- **1:1 the joint, not the element.** A crop centred on a headline proves the headline; the
  defect lives where two things meet — text/photo edges, row/meta joints, panel/footer seams.
- **One baseline zone, one voice.** Two different-size or -colour texts sharing a y-band read
  as one broken line even with a few px of clearance. Give the band to one of them: delete,
  stack with ≥1 rhythm step, or divide explicitly.
- **Rows align from one shared top.** A meta+title row tempts three hand-tuned offsets that
  "look aligned" and never are, because each size carries its own ink offset. Start every box
  at the same y, then nudge the small text as a group from a 2× crop until ink tops agree
  within 2px (two rounds max, keep the best). The 1:1 row crop is the only check.
- **One line, one box — or computed baselines.** A value+unit line faked with two top-aligned
  boxes at different sizes always drifts, because box tops are not baselines. Use a single
  text node, stack value over unit label, or compute both baselines from committed
  `textBounds` in a later call.

## At a second width

- **Refold, never reword.** Copy is final; the width change is a measured fit pass, not a rewrite.
- **Check each last line.** No single short word left alone, and a separator leads the next line.
- **An action keeps its affordance at every width** — the underline, fill or border stays.
- **A list's last row rule is its boundary;** the block ends there, nothing below reuses it.
- **Right-align to the measure edge,** not to a pixel picked at one width.
- **Full-bleed media has radius 0;** a radius on an edge-touching band reads as a card.
