---
name: ux-design-process
description: Run the story-first UX process for a screen — one task per screen, hook→proof→path→action, hero contract, content-before-grid density, spacing scale, state matrix, and scored independent review. Use when planning or reviewing a screen's experience before or after building it in Penpot. Not for visual direction (use visual-interface-design), Penpot mechanics (use penpot-design-system, penpot-mcp-operations), or pipeline/build/test operation.
license: MIT
metadata:
  author: configs
  version: "1.0.0"
---

# UX design process

Decide what the screen is for and in what order it speaks, before choosing
how it looks. Art direction lives in `visual-interface-design`, realisation
in Penpot in `penpot-design-system`, bridge mechanics in
`penpot-mcp-operations` — this skill owns neither; it owns the story, the
density, the states and the review. Anything those skills already rule is
referenced, not repeated.

## 1. One task, one screen

Name the visitor's job as a single sentence (JTBD): who, in what situation,
gets what done here. A screen with two jobs is two screens. Record it as
`task` in `ux-spec.json`; the gate fails an empty one.

## 2. Story arc per screen: hook → proof → path → action

Order the first viewport as four beats, in this order:

1. **Hook** — the promise, one message, above everything else.
2. **Proof** — evidence inside the first viewport: a number, a result, a logo
   row. A claim without evidence here is decoration.
3. **Path** — the two to four onward routes, named as the visitor would.
4. **Action** — exactly one dominant call to action per board; the gate
   counts shapes named `*cta*`/`*primary*` and fails on two or more.

Record the four beats plus `firstViewport` (the shape names that must sit
inside the first 900px) in `ux-spec.json`; `ux_gate.py` verifies each beat
exists, each named shape is above the fold, and accent fills stay under the
declared ratio.

## 3. Hero contract

- One message, one primary action, proof inside the first viewport.
- The visual carries a **role**: it shows, proves, or sets mood — state which
  one in the brief. A visual with no role ("stock filling") is cut, not kept.
- Write an art-direction brief for the visual: subject, framing, light, face
  or no face, why this image and not another.
- Compose **three alternative heroes** on the scratch page first, pick one in
  a sentence, record the rejected two with a reason. No screen starts from a
  single uncompared hero.

## 4. Content-first density

Write the copy before the grid. The number a screen claims is the number it
shows: `claims` in `ux-spec.json` pairs a name pattern with the expected
count, and the gate fails a mismatch (19 shown vs 96 claimed). A claim the
file cannot show is rewritten to what the file shows ("19 today · 96 across
four days", never a bare "96" over 19 cards). When content
grows, either show all of it or change the claim — never keep the number and
crop the list. Fixed grids (calendars, tables) derive their row heights from
the tallest measured content via `fit-slot.js`, or fail the build; the lint
`fit` family (overflow, boundary entry, rule crossing, bar-vs-content)
proves the last build.

## 5. Rhythm, then eyes

One spacing scale per project, one declared section rhythm in px, one
"breather" rule per section (what separates, what groups). Verify with
`rhythm.py` on the lint geometry — gaps cluster at the rhythm, anything past
2× carries a written reason..Margin symmetry is checked at 1:1 on the hero,
never at page scale. See `penpot-design-system` ("Grid is code",
"Rhythm is declared, then audited") for the mechanics; this skill sets the
numbers, the scripts prove them.

## 6. State matrix and mobile

Design the reachable states where they live, not later in code: default,
hover, focus, active, disabled, loading, empty, error, success — each as a
board or a named shape the `states` list points at. The gate fails a listed
state with no board. Every desktop screen ships a 390px twin or a reasoned
`n/a: …`; an unreasoned `n/a` fails the gate.

## 7. Independent review (rubric, scored)

The maker's pass is not review. A separate reviewer — different model or
session — receives **only the tile PNGs** from `crop_board.py` plus the
mechanical outputs (lint, rhythm, ux-gate); it never reads the written spec,
so the story must survive on pixels alone. It scores 0–5 per axis and returns
`region · score · observed vs expectation` findings:

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

Audience, task, story beats, hero choice and rejected alternatives, rhythm
numbers, state coverage and review scores go in the project `brief.md`
(as-built conformance). A decision not in a file did not happen.
