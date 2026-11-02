---
name: ux-design-process
description: Run the story-first UX process for a screen — one task per screen, hook→proof→path→action, hero contract, content-before-grid density, spacing scale, state matrix, and scored independent review. Use when planning or reviewing a screen's experience before or after building it in Penpot. Not for visual direction (use visual-interface-design), Penpot mechanics (use penpot-design-system, penpot-mcp-operations), or proof of done (use design-verification).
license: MIT
metadata:
  author: configs
  version: "1.1.0"
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
in `ux-spec.json`; `ux_gate.py` verifies each beat exists, each named shape is above the fold,
and accent fills stay under the declared ratio.

## 3. Hero contract

**Taste is the user's; the rest is the maker's.** On a taste-bearing surface (hero, cover,
brand opening) present 4–5 finished first viewports and let the user choose. Everywhere else
explore 2–3 directions, decide, record. Choosing among built candidates is expected;
specifying design is not.

In Penpot: build the candidates on the scratch page, same copy, each with a name, a "refuses"
sentence and an art-direction note for its visual (role: show / prove / set mood; subject,
framing, light, face or no face). Export and tile them, score 0–5 per axis, then hand the
taste-bearing set to the user and decide the rest yourself. Record the choice and the rejects.

- A candidate is a different domain-native **object**, named by "this page is a ___" — a
  journal cover, a clinical algorithm, an anatomy plate, a map, a poster. Layout or
  composition variations of one object are one candidate, never three.
- Candidates share no part: no common image, proof block, band, or "headline+lede+CTA on the
  left" arrangement. List five references from outside the category before drawing.
- A candidate is a filled first viewport: nav, a real visual, proof and one primary, no dead
  band. Shrink the set to 200px side by side and eliminate any that is not unmistakably
  different from the others and from the shipped surface.
- A hand-drawn organic figure that does not read at 1:1 is replaced by a photograph or a
  prepared asset; no candidate is presented before its render has been read at 1:1.
- In a dispatch, ask for "different objects", never "different compositions" — the second
  wording produces restyled layouts and burns a round.

Kept constraints: one message, one primary action, proof inside the first viewport; the
visual carries a role, and a visual with no role ("stock filling") is cut, not kept.

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
section (what separates, what groups). `rhythm.py` reads the lint geometry: gaps cluster at
the rhythm and anything past 2× carries a written reason. Margin symmetry is checked at 1:1
on the hero, never at page scale. This skill sets the numbers; the mechanics and the joints
are in `craft.md`.

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

Two rounds max, then the owner decides. Attest every tile in the manifest
(`crop_board.py --attest`) — an unreviewed tile is an unreviewed screen.

## 8. Record the decision

Audience, task, story beats, hero choice and rejected alternatives, rhythm numbers, state
coverage and review scores go in the project `brief.md` (as-built conformance). A decision not
in a file does not exist.
