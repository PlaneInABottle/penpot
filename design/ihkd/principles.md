# İHKD — stance, voice, composition

What a token cannot express. Mechanics live in the skills (`penpot-design-system`,
`references/craft.md`, `design-verification`); this file states the project's stance and the
decisions that are its own.

## 1. Stance

**One patient, two specialties.** Every page makes the same point differently: the internist
and the cardiologist look at the same person. A session with two chairs, a guideline
co-signed by both groups, a member card that names one working group and never one
discipline.

**A clinical product, not a brochure.** The member desk is the centre of gravity; public
pages earn the right to it and never imitate it. Anything that would sit on a hospital's
"about us" page is rewritten or removed.

**Quiet interface, loud data.** Chrome is grey and white; numbers, dates and evidence grades
are the only loud things. If the interface competes with the data, the interface is wrong.

## 2. Voice

- Speak to a colleague. `siz`, never `sizler`.
- Verbs, not nominalisations: `Kılavuzu indirin`, not `Kılavuz indirilebilir`.
- Every deadline carries a date and a timezone: `Son gönderim 15 Şubat 2027, 23:59 (TSİ)`.
- Numbers: `6.847`, `3,2 MB`, `22–25 Nisan 2027`, `09:30`.
- Banned: `dünyanın önde gelen`, `en iyi`, `benzersiz`, `çözüm ortağı`, `yol arkadaşı`,
  `sağlığınız için`, `acele edin`, exclamation marks.
- Clinical abbreviations stay: `STE`, `EF`, `KKY`, `BKA`, `TAVİ`, `GİS`.

## 3. Composition

1. **One container: the card.** What can be acted on or read as a unit sits in a white card
   with a 1px hairline; a paragraph is not carded. Two paddings only: 24px (`card`) and 32px
   (`feature`).
2. **Two rhythms.** Public: 112px between sections, 24px between cards. Desk: 24px gaps,
   44px rows, no section rhythm — a desk is scanned, not strolled.
3. **One full-bleed moment per page.** A photograph may run edge to edge once (the 01 poster
   is that moment); everything else is contained.
4. **The accent is an action.** Arterial red appears on: primary button, active nav item,
   link, selected chip, progress fill, focus ring, the live ECG trace. Kickers and category
   labels are graphite, never red. A screen with five red elements has three wrong ones.
5. **Signal is not a second brand colour.** `red.100` surface + `red.700` text for a passed
   deadline, an invalid field, a cancelled session. No green "success", no blue "info".
6. **Type does the hierarchy, not colour.** Six sizes (13 / 16 / 22 / 30 / 44 / 80); size and
   weight separate levels, colour only separates primary text (`ink.900`) from meta
   (`ink.500/600`). No coloured headings.
7. **Ghost numerals.** Section order is carried by a 44px `ink.400` numeral in the kicker's
   line — felt, not read; the title owns the left edge.
8. **Photography is a place or a publication object**, graded cool and captioned in 13px
   sentence case. No patient, no examination, no stock smile (brief §6).

## 4. Visual language — the congress poster (01, M8)

The home page opens as a **poster over the hall**, chosen by the user:

- **Full bleed, real place.** A 1440×668 photograph of the auditorium; the type sits on the
  `hero scene` board whose `ink.900` fill is the surface behind the text. **No gradient
  scrim, no overlay rectangle.**
- **The date is the message, the society is the signature.** `22–25 Nisan 2027` at 80px;
  `Hastanın hekimi.` at 30px above the white ECG trace and the association's name as a 13px
  imprint below it, on the poster's darkest band.
- **One numeral, vector.** The edition `12` is a path (Inter Tight 700 outlines), not a text
  node: at poster size a text node would be a seventh type size. It is a layer of the poster,
  not copy.
- **One trace.** A white 1440×30 ECG line across the audience — the instrument, not a
  divider.
- **One primary.** `Kongreye kayıt ol` (saturated) + ghost `Programı gör`. The page's other
  actions are links.
- **Proof on paper.** The society's four figures are a 44px stat strip on `paper` under the
  poster's edge, not small text on the photo.

## 5. Colour

| surface | fill | text | used by |
|---|---|---|---|
| ground | `paper` `#F2F4F5` | `ink.900` | every page, the desk |
| panel | `white` `#FFFFFF` | `ink.900` | cards, forms, footer |
| sheet | `bone` `#FFFFFF` | `doc.text` | guideline, journal TOC, article |
| narrow band | `red.600` `#C4122F` | `on.red` | at most one per page |
| signal | `red.100` `#FBE3E7` | `red.700` | deadline, invalid field |
| poster | photo + `ink.900` | `on.ink` | 01 hero only |

`#000`-adjacent surfaces appear nowhere except 1px instrument details. A second accent, a
bone sheet used as a card, or two red bands on one page all break the system.

## 6. Accepted deviations (lint mediums/lows that are by design)

- **13px microcopy.** Kickers, helper text, captions, time gutter, IDs, prices and legal share
  one micro size, so the scale stays at six. The 13→16 step (1.23) is the one recorded
  deviation (`craft-rules.json`, `min_step_ratio` 1.2); long 13px tabular lines still trip
  `type.small_body` LOW and stay visible.
- **Ghost numerals** (`head num`, `ink.400`) are 2.07:1 on paper: decorative order marks
  redundant with the title beside them. Real copy never uses `ink.400`.
- **Uppercase wayfinding** sits at ~31% of texts on the fee screen; the lint ceiling is the
  DEFAULT 0.35 and passes without a project rule.
- **Row heights are declared per surface**: programme 92px, fee/guideline/news rows 64–68px,
  bilim-kurulu index 44px. Density follows the reading task.
- **Other mediums stay visible** (dead space, intra-card gaps, inline mixed-size pairs):
  measured per screen, fixed when they are defects, never thresholded away.

## 7. Verification stance

A written shape is not paint: prove with a render. Contrast on a photograph is measured
against the **pixels behind the ink**, never against token pairs alone; type over a photo
counts only once its darkest and brightest backing pixels both pass. A tile is read at 1:1
before a screen is called finished, and a tool's own heuristic (a CTA picker, an off-origin
crop frame) is never the evidence — the note in the manifest says which crop was inspected
and what it shows.
