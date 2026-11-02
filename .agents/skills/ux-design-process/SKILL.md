---
name: ux-design-process
description: Run the story-first UX process for a screen — one task per screen, hook→proof→path→action, hero contract, content-before-grid density, spacing scale, state matrix, and scored independent review. Use when planning or reviewing a screen's experience before or after building it in Penpot. Not for visual direction (use visual-interface-design), Penpot mechanics (use penpot-design-system, penpot-mcp-operations), or proof of done (use design-verification).
license: MIT
metadata:
  author: configs
  version: "1.2.0"
---

# UX design process

Decide what the screen is for and in what order it speaks, before choosing how it looks.
Art direction lives in `visual-interface-design`, realisation in `penpot-design-system`,
proof of done in `design-verification`, bridge mechanics in `penpot-mcp-operations`. This
skill owns the story, the density, the states and the review; anything those skills already
rule is referenced, not repeated.

## 1. One task, one screen

Name the visitor's job as a single sentence (JTBD): who, in what situation, gets what done
here. A screen with two jobs is two screens. Record it as `task` in `ux-spec.json`; the gate
fails an empty one.

## 2. Story arc per screen: hook → proof → path → action

1. **Hook** — the promise, one message, above everything else.
2. **Proof** — evidence inside the first viewport: a number, a result, a logo row. A claim
   without evidence here is decoration.
3. **Path** — the two to four onward routes, named as the visitor would.
4. **Action** — exactly one dominant call to action per board; the gate counts shapes named
   `*cta*`/`*primary*` and fails on two or more.

Record the four beats plus `firstViewport` (shape names that must sit inside the first 900px)
in `ux-spec.json`; `ux_gate.py` verifies each beat string is non-empty, each named shape is
above the fold, CTA/state/mobile names resolve, and accent fills stay under the ratio. It
cannot judge whether a beat actually reads: §7 review owns that.

## 3. Hero contract

On a taste-bearing surface (hero, cover, brand opening) the user chooses; the maker builds the
choice. Run the global `design-variety` protocol for the candidate rules — objects not layouts,
no shared parts, finished first viewports, the 1:1 defect pass, the similarity test, unranked
presentation and parking — and use this section only for how that set is built and recorded in
Penpot.

1. Build each candidate on the scratch page from the same copy, one board per candidate. Name
   it, write its "refuses" sentence, and add an art-direction note for its visual (role:
   show / prove / set mood; subject, framing, light, face or no face).
2. Export and tile the boards and review every one at 1:1 against the §7 rubric before it is
   shown; the user-facing set stays unranked.
3. Write a candidate section in the project `README.md`: name, "this page is a ___", carrier
   source, one strength, one risk, no ranking.
4. Hand the finished set to the user. Until they choose, keep the live page on its current
   hero and continue everything that does not depend on it; never pick for them.
5. Record the chosen candidate and the rejects in `brief.md`. Park each candidate the user
   marks with its build script, render and revival condition; do not delete candidate boards
   or renders unless the user asks — cleanup happens before handoff.

Keep the constraints: one message, one primary action, proof inside the first viewport, and a
visual that carries a role ("stock filling" is cut). On a non-taste surface, explore two or
three directions, decide and record; the authority and scoring table are in
`visual-interface-design`.

## 4. Content-first density

Write the copy before the grid, and make the number a screen claims the number it shows:
`claims` in `ux-spec.json` pairs a name pattern with an expected count and the gate fails a
mismatch. A claim the file cannot show is rewritten to what the file shows ("19 today · 96
across four days", never a bare "96" over 19 cards). When content grows, either show all of
it or change the claim — never keep the number and crop the list.

Fixed grids (calendars, tables) derive row heights from measured content via `storage.FIT` or
fail the build; mechanics in `penpot-design-system/references/craft.md`. Time-proportional
calendars are allowed only above ~50% density; a sparse program is an agenda — one row per
start time, height from content, no empty rows, duration as a label. Every card keeps a
content-fill ratio ≥ 0.6.

## 5. Rhythm, then eyes

One spacing scale per project, one declared section rhythm in px, one "breather" rule per
section (what separates, what groups). This skill sets the numbers; the advisory audit
(`rhythm.py`, exit stays 0), the joints and margin symmetry are in `craft.md`.

## 6. State matrix and mobile

Design the reachable states where they live, not later in code: default, hover, focus,
active, disabled, loading, empty, error, success — each as a board or a named shape the
`states` list points at. The gate fails a listed state with no board. Every desktop screen
ships a 390px twin or a reasoned `n/a: …`; an unreasoned `n/a` fails the gate.

## 7. Independent review (rubric, scored)

The maker's pass is not review. A separate reviewer — different model or session — receives
**only the tile PNGs** from `crop_board.py` plus the mechanical outputs (lint, rhythm,
ux-gate); it never reads the written spec, so the story must survive on pixels alone. It
scores 0–5 per axis and returns `region · score · observed vs expectation` findings:

| axis | 5 means |
|---|---|
| hierarchy | the task reads before anything else at first glance |
| story | hook→proof→path→action survives without the spec |
| first-5-seconds | a new visitor states the job and the action within 5s |
| fit | every glyph sits inside its slot at 1:1, no crossings |
| consistency | tokens, rhythm and voice match the rest of the file |
| accessibility | contrast pairs pass, touch targets and focus order hold |

Two rounds max, then the owner decides. Attest every tile and region in the manifest
(`crop_board.py --attest`) — an unreviewed tile or missing PNG is an unreviewed screen.

## 8. Record the decision

Audience, task, story beats, hero choice and rejected alternatives, rhythm numbers, state
coverage and review scores go in the project `brief.md` (as-built conformance). A decision not
in a file does not exist.
