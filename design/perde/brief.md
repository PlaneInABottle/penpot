# Perde — brief

İstanbul'da bu akşam ne var? A culture map for theatre, concerts, exhibitions and stage.
Exploration build: sample event data, the map is a placeholder image.

## 1. Product

- Product: **Perde** — `İstanbul kültür haritası`. An isometric city map where tonight's
  events are pins, plus a list that shares the same selection.
- Audience: someone in Istanbul deciding what to do tonight — resident or visitor, reading
  Turkish. They already know the city; they are choosing, not sightseeing.
- Job: *"It's 18:00, I'm in Beyoğlu and free tonight — show me what's on near me, and let me
  pick one."*
- Primary action: open a pin → read the event → `Bilet al`.
- Copy: Turkish, sentence case except labels, times `20.30`, prices `₺240`.
- One primary action per screen.

## 2. Direction — "Maket"

A city read as a physical model on a warm table: cream paper, ink-brown type, one terracotta
stamp, cards that behave like printed labels. The chrome is stationery; the map is the object.
Three other directions (night marquee, riso zine, daylight console) were built, compared and
dropped; only this one continues.

**Refuses:** dark glass chrome, neon pins, dashboard panels, more than one accent.

| axis | this project |
|---|---|
| surface | cream paper `#FCF8EF` on table `#E7DBC4`, ink `#2A2419` |
| density | map owns the canvas; chrome floats in corners; list rows 88px |
| navigation | no masthead — wordmark stamp, search pill, left category rail, map |
| only here | the **paired selection**: one pin and one list row are the same selection |

Type: `Fraunces` 600 for names and numbers, `Work Sans` 400/500/600 for UI and times.

## 3. Boards (all on `Page 1`, no overlaps)

| board | size | job |
|---|---|---|
| `A1-harita` | 1440×900 | the map: 6 pins, category rail, time scope |
| `A2-detay` | 1440×900 | pin + museum-label popover |
| `A3-liste` | 520×820 | the list, alone |
| `A4-pinler` | 900×440 | pin and chip states |
| `A5-figur` | 1200×880 | figurine pins (pixel), sheet + real size + on the map |
| `A6-piksel` | 1200×900 | pixel component sheet: buttons, chips, tabs, search, dialog, row, badges, toast |

`A1` keeps its original lollipop pins; `A5` is the alternative token set, not yet applied.

Claims: category counts `5 + 3 + 2 + 2 = 12` match every list header and footer.
All strings are sample data; the map is `isometricistanbul.com` as a placeholder.

## 4. Figurine pins

The request was pins that read as objects rather than map markers — Monopoly-token energy.
Ten figurines: penguin, martı, kedi, vapur, simit, lale, fincan, maske, plak, nazar.
Each stands on a small plinth in its category colour, so category survives while the figure
carries personality.

Pipeline (`tools/pixelize.py`): the vector figurines live in `build/figures.json`, are
rasterised with `rsvg-convert` at 512×576, reduced to a 16×N grid with an area filter, and
snapped to their own flat palette. A one-cell cutline is added automatically — cream for dark
figures, ink for pale ones, because a cream bird on a cream canvas disappears.

A pixel **map** was tested and rejected: downscaling the photo to a 6px grid produces a
mosaic, not pixel art. Pixel art stays on the token and icon layer only.

## 5. Rhythm and type

- Spacing 4/8/12/16/24/40. Radius 8/12/16/20/28.
- Section inset 40, card gap 16, list row 88.
- Type scale 10 / 12 / 13.5 / 17 / 24 / 26 / 30.

## 6. UI audit

Contrast (`scripts/check_contrast.py`, AA text 4.5):

| pair | ratio | result |
|---|---|---|
| ink.900 / paper | 14.52 | pass |
| ink.500 / paper | 5.50 | pass |
| ink.500 / paper.alt | 4.92 | pass |
| accent.ink / paper | 5.98 | pass |
| cat.tiyatro / paper | 6.92 | pass |
| cat.sergi / paper | 4.64 | pass |
| cat.sahne / paper | 6.19 | pass |
| cat.konser / paper | 3.54 | pass as graphic (7px dot, 3:1), never used as text |
| paper / ink.900 | 14.52 | pass |

Fixed across the exploration:

1. Popover title wrapped into the venue line → 24px, one line, stamp moved off the corner.
2. A floating date chip collided with the list panel → date moved into the panel header.
3. Pins rendered as hollow rings → solid head, 4px cream ring, ground shadow.
4. Boards sat on top of each other → separate coordinates, stale copies deleted, overlap check
   returns `[]`.
5. Every component was crammed on one board → split into map / detail / list / parts.
6. The map had no "when" control → `Bu akşam / Yarın / Bu hafta`.
7. Hover chip floated away from its pin → attached with a tail.
8. 13 boards from the dropped directions removed.

## 7. Gaps

- Figurine pins exist on `A5` only; `A1` still uses the lollipop pins.
- No selected/cluster state for a figurine yet.
- `A6` is a component vocabulary, not a screen; it is not wired into `A1`.
- No close affordance on the detail card.
- No mobile 390 twin, no keyboard/focus states, no empty/loading states.
- `₺` falls back to a wrong glyph in `Fraunces`; prices use `Work Sans`.
- The map is a placeholder image, not a drawn isometric tile set.
