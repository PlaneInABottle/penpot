# <project> — brief

Copy of `design/_template`. Every section is a decision with a date; nothing here is
restated in a skill. Fill §1 before any screen, §2 before any layout.

## 1. Product

- Organisation, product, category convention borrowed (and what is invented).
- Audience, in one line, as the visitor would describe themselves.
- One primary action per screen.
- The idea in one sentence, in the product's own words.

## 2. Direction

- Chosen direction, named, with its mechanism and a "refuses" clause.
- The two rejected directions, one line each, with the reason.
- Four structural axes: surface / density / navigation model / the element that exists only
  here.
- References named with the structural idea taken from each.

## 3. Story (as-built)

Per screen: `task`, `hook → proof → path → action`, `primaryCta`, `states`, `mobile`,
`firstViewport`, `claims`. The live copy of this section is `ux-spec.json`; prose here only
records why a beat is what it is.

## 4. Rhythm and type

- Section rhythm in px, data-row height, spacing scale, type scale.
- Margin and bleed decisions, one line each.
- Declared surface palette: white and alt hexes, mirrored in `craft-rules.json`
  (`surface_white`, `surface_alt`). `surface.role` warns and skips until they are declared.
- Any deviation from a lint default, with the reason (`craft-rules.json` is the machine copy).

## 5. Copy

- Vocabulary, numbers and dates as the project writes them; banned phrases.
- Every string changed after the direction was frozen is synced back here, or the brief
  stops being the source of truth.

## 6. Media

| slot | board | role (shows / proves / sets mood) | source (pinned URL) | crop |
|---|---|---|---|---|

The table is the only source for photo choice: a rebuild re-imports from it.

## 7. Review

- Hero choice and the rejected candidates.
- Independent review scores per board (rubric: `ux-design-process` §7).

## 8. Gaps

Anything not covered by the gates, stated as a gap and never as done.
