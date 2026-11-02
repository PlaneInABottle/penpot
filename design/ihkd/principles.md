# İHKD — stance, voice, composition

The rules a token cannot express. Written before the screens.

## 1. Stance

**One patient, two specialties.** Every page should make the same point in a different
form: the internist and the cardiologist are looking at the same person. A congress session
with two chairs, a guideline co-signed by both groups, a member card that lists one working
group but never one discipline.

**A clinical product, not a brochure.** The member desk is the centre of gravity. Public
pages earn the right to that desk; they never imitate it. Anything that would look at home
on a hospital's "about us" page is rewritten or removed.

**Quiet interface, loud data.** Chrome is grey and white; the numbers, dates and evidence
grades are the only things allowed to be bold. If the interface is competing with the data,
the interface is wrong.

## 2. Voice

- Speak to a colleague. `siz`, never `sizler`.
- Verbs, not nominalisations: `Kılavuzu indirin`, not `Kılavuz indirilebilir`.
- Every deadline carries a date and a timezone: `Son gönderim 15 Şubat 2027, 23:59 (TSİ)`.
- Numbers: `6.847`, `3,2 MB`, `22–25 Nisan 2027`, `09:30`.
- Banned: `dünyanın önde gelen`, `en iyi`, `benzersiz`, `çözüm ortağı`, `yol arkadaşı`,
  `sağlığınız için`, `acele edin`, exclamation marks.
- Clinical abbreviations stay: `STE`, `EF`, `KKY`, `BKA`, `TAVİ`, `GİS`.

## 3. Composition rules

1. **One container: the card.** Content that can be acted on or read as a unit sits in a
   white card with a 1px border and 8px radius. Text that is merely a paragraph is not
   carded. Two card styles only: `card` (24px padding) and `feature` (32px padding).
2. **Two rhythms.** Public: 112px between sections, 24px between cards. Desk: 24px gaps,
   44px rows, no section rhythm — a desk is scanned, not strolled.
3. **One full-bleed moment per page.** A photograph may run edge to edge once; the rest are
   contained image cards. Two full-bleed images on one page is a magazine, not a product.
4. **The accent is an action.** Arterial red appears on: primary button, active nav
   item, link, selected chip, progress fill, focus ring, the live ECG trace, and the
   congress band. Kickers and category labels are graphite, never red. If a
   screen has five red elements, three are wrong.
5. **Signal is desaturated on purpose.** `signal.600` is a muted brick so that it reads as
   "attention" without becoming a second brand colour. It appears only for a passed
   deadline, an invalid field, or a cancelled session.
6. **Type does the hierarchy, not colour.** Size and weight separate levels; colour only
   separates primary text from meta (`ink.900` vs `ink.500`). No coloured headings.
7. **Photography is graded and captioned.** Cool, slightly desaturated, captioned in 13px
   sentence case. No photo behind text, no gradient scrim, no stock smile at the camera.

## 4. What would make this fail

- A hero with a photo behind a headline and a dark gradient.
- Three icon cards reading `Kalite · Güven · Yenilik`.
- A member area that is the public nav with a name in the corner.
- A congress programme without a time gutter and hall columns.
- Guidelines as image cards with no year, evidence grade or page count.
- Shadows, glows, or a second accent.
- A serif headline (that is the other project's register, not this one).

## 5. Retrospective — why the first two attempts looked like the other project

Written after the third direction, because the first two failed the same way.

**What happened.** v1 (cream, green, Source Serif, § strips) and v2 (white, cobalt, cards)
were both rejected as "the same as the brain congress". They were. Only the hue changed:

| axis | brain congress | v1 | v2 | verdict |
|---|---|---|---|---|
| surface | warm paper | warm paper | cool white | light page in all three |
| density | 96px sections, hairlines | 96px, hairlines | 112px, card borders | same rhythm |
| type | Plex Sans + Mono | Serif + Mono | Serif + Mono | same three-role split |
| section grammar | numbered strip | numbered strip | accent bar + title | a label above a rule |
| composition | hero, stats, cards, banner, list | same | same | a landing page |

**Why.** Three causes, in order of damage:

1. **The primitive library was inherited.** v2's `lib.js` was a rewrite of the brain
   project's `screen-kit`: the same `rect / board / text / rule` atoms and the same
   `strip / plate / footer` blocks. Reusing the atoms reuses the grammar — a new palette on
   old primitives always produces the old page.
2. **Colour was treated as the system.** Hue is the last axis, not the first. Changing
   vermilion to green to cobalt to crimson never touched surface, density, type roles or
   composition, so the thumbnail stayed identical.
3. **The brief described print.** "Data strip, plate captions, folio, hairlines" is poster
   vocabulary. The build was faithful to a brief that had already chosen the answer.

**Rules that follow.**

1. Before any colour, fix four structural axes: **surface** (light / dark / tinted),
   **density** (the rhythm in px), **navigation model**, and **one element that exists only
   in this product**. A direction that does not name all four is not a direction.
2. **Never reuse the previous project's primitive library.** Write a new `lib.js` from the
   four axes; only then pick type and colour.
3. **Thumbnail test.** Shrink the home page to 200px wide next to the previous project. If
   they could be siblings, the direction failed — go back to the axes, not to the palette.
4. **Write "this is not" from the rejected artefact**, naming its concrete features
   (cream page, hairline rows, serif headline, numbered sections), not from generic clichés
   ("no navy hero").
5. Record the rejected screenshots, not just the words. A rejection that is not visible gets
   rebuilt.

**The third direction, stated on the axes.** Surface: near-black `#0B0E11`, one warm-white
text colour, one arterial red — a viewer, not a page. Density: 96px section rhythm but 44px
data rows; the desk runs at 24px. Navigation: a 4px red bar and a one-line masthead that
never grows. Signature element: an **80px graphite section numeral** that carries the page
order, plus full-bleed photography with no frame. No serif anywhere in the interface; the
serif is reserved for document text only.

## 6. Colour, argued from the work

The palette is not a mood board. It follows what these two specialties actually look at —
with the lights on. An earlier direction made the viewer near-black; it read as gloom, not
as clinical focus, and it was rejected. The reading room has daylight: the canvas is a
cool clinical grey, text is near-black ink, and the only saturated colour is arterial red.

- **Daylight canvas, not paper, not black.** `paper` `#F2F4F5` is the lit examination
  room: neutral, cool, shadowless. Panels are pure `white`, so a card reads as the
  printed sheet on the desk. `#000`-adjacent surfaces appear nowhere except 1px
  instrument details; a board that renders near-black has broken the system.
- **Bone is the printed sheet.** `bone` `#FFFFFF` is the guideline you print, the journal
  you fold, the letter from the board. On the grey canvas a white sheet needs no border
  to read as an object; inside it, text is `doc.text`, never `ink.*`.
- **Arterial red, nothing else.** `#C4122F` is the colour of the thing the society is named
  after. It marks action (buttons), time (deadlines, congress) and the live trace. There is
  no second accent, no green for "success", no blue for "info": those are states, written in
  words and rules, not in colour.
- **Ghost numerals, not ink numerals.** Section numerals are `ink.400`: oversized order
  marks that stay recessive. A numeral in full ink would compete with the title; the
  spine is felt, not read.

Where each colour is allowed:

| surface | fill | text | used by |
|---|---|---|---|
| viewer | `paper` | `ink.900` | every public page, the desk |
| panel | `white` | `ink.900` | forms, side panels, footer |
| sheet | `bone` `#FFFFFF` | `doc.text` | guideline, journal TOC, article body |
| band | `red.600` | `on.red` | one per page at most (congress, login) |
| signal | `red.100` | `red.700` | deadline callout, invalid field |

A screen with two red bands, or a bone sheet used as a card, has broken the system.

## 7. Incident — the photo stuck to the edge (Oct 2026)

The home hero photo was placed at x=800, w=640: right edge 1440, the board edge, 120px
past the 1320 grid. Every gate passed — lint checks overflow past the board, not past the
grid; the render at page scale looked nearly right. Cause, in order: (1) coordinates were
hand-written in board space instead of derived from X/CW; (2) no declared-bleed list, so
an edge-touching shape was ambiguous rather than wrong; (3) verification was by eye at
page scale, which hides exactly this class. Durable fix, now in the skill and in the
workspace definition of done: derive x/w from the grid constants, declare bleeds per
screen, assert edges from the lint JSON geometry, and check margin symmetry at 1:1.

## 8. Standing explanations (lint mediums/lows that are by design)

- Uppercase ratio (~20% on most pages): labels, kickers, table headers and section
  markers are uppercase-tracked 11–12px by the type system. This is wayfinding, not
  shouting; the lint 15% default assumes prose-heavy pages. Not fixed, by decision.
- 13px microcopy everywhere: kickers, helper text, captions, time gutter, IDs,
  prices and legal share one micro size, so the scale stays at six sizes. The 13→16
  step (1.23) is the craft checklist's body/meta-pair exception class (the checklist
  names 16/14; ours is the same pair, one step tighter). Long 13px table-meta lines
  still trip the `min_body_size` low — they are short tabular lines by design, and the
  low stays visible rather than exempted.
- Row heights are declared per surface, not tightened to one law: programme table
  92px, fee/guideline/news rows 64–68px, bilim-kurulu index 44px. Scan tables breathe;
  the dense index runs tight. Density follows the reading task.
- Ghost numerals (`head num`, ink.400, 2.07:1) are exempt from the contrast gate:
  44px order marks redundant with the section title beside them — felt, not read.
  Real copy never uses ink.400; run contrast gates with `--ignore "head num"`.
- Gate invocation for this project always adds `--rules design/ihkd/craft-rules.json`:
  the ghost numerals are excluded from the dominant-element check (they are chrome,
  never the dominant element) and the uppercase ceiling is 0.35. Both are recorded
  deviations in `craft-rules.json`, not silent weakenings.

## 9. Decisions — home tightening + programme rebuild (Nov 2026)

Made from verified renders (01-ana-sayfa, 07-program), not from the old brief text.

1. **One red band per page, enforced.** The home hero's red ECG strip (a second red
   field beside the congress band) became a white card: red ECG trace (the trace is
   data, allowed red), graphite kicker, ink date, red action link. The congress band
   is the page's only red field. Kickers and category labels moved from red to
   `ink.500` helpers-wide; red is spent only on action (buttons, links, selection)
   plus congress and the live trace.
2. **Ghost numerals stepped down, not removed.** They are the product's spine (§5),
   so they stay — but 80px fought the section titles. Now 44px (`h2` size, still
   `ink.400`, still exempt): recessive order marks beside 44px ink titles and 44px
   mono stat figures. The parallel `NN / 06` counters on 01 were deleted instead:
   they double-numbered the same order with the wrong denominator.
3. **Data got louder, chrome got quieter.** Stat figures 30→44px via a new `stat`
   role (the article's small `figure` 30px is untouched); stat labels 13px `ink.600`;
   helper text `meta` 12→13px with a new `fs.13` token, synced. Tabular microcopy
   (`data` 12px: time gutter, IDs, prices, legal) stays small by role.
4. **Hero photograph, chosen from nine candidates.** Placed: RDNE Stock project
   6129683 — wall-mounted 12-lead ECG monitor (V1–V6 visible), nurse from behind, no
   face at the camera: the internist and the cardiologist looking at the same trace.
   Rejected: fetal ultrasound 7089623 (wrong specialty), powered-off echo unit 7108402
   (dead screens), monitor close-up 9408868 (good backup, no human), waiting-room
   6129035 (faces, smiles), red stethoscope 5149754 (product cliché). Journal texture
   replaced too: Brett Jordan 6770532 cropped to a `MEDICINE` masthead, so both 01
   and 14 now use Robert Munteanu 3860983 (open pages, small body text, no headline).
   Rejected: newspaper stacks, blank notebooks, archive shelving, German-spine shelf,
   staged "Medical Research" flatlay, hand-writing-notebook. Full candidate table in
   the milestone return; provenance in `media/provenance.json`.
5. **Programme rebuilt for density.** 07 showed 9 sessions in 36 cells with no end
   times and nine repeated `Programa ekle +` links. Now 22 April runs 18 thirty-minute
   slots (09:00–18:00) × 4 halls with 19 sessions, every meta opening with
   `HH:MM–HH:MM`; per-row links replaced by one `Seçili oturumları programa ekle`
   above the table. Konsey sessions (six) carry two chairs and the red bar; the rest
   keep the graphite bar. The meta line scopes the count: `22 Nisan 19 oturum ·
   toplam 96 oturum` (96 is the four-day total).
6. **Masthead estimator 8.9→8.2** so inter-link gaps match the underline estimator
   used elsewhere; verified at 1:1 on the new export.
