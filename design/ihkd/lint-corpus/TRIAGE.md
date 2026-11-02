# Lint corpus triage — 2026-11-02

Every finding the old `design_lint.py` produced on the five İHKD pages was read
against a 1:1 crop of the board before any rule changed. The labels are:

- **GERÇEK** — a defect to fix on the screen (this round lists it, it does not edit design).
- **FP** — the rule fired on a clean screen; the rule, not the design, was wrong.
- **KABUL** — a declared design decision; recorded in `craft-rules.json` (`acknowledge`)
  or by the project's written deviation.

Frozen corpus: `design/ihkd/lint-corpus/<page>.nodes.json` (5 pages, 2 852 shapes),
captured read-only with `--dump-nodes` while the hero agent was building on
Kurumsal (only a snapshot; no build, no write). `--from-nodes` replays each dump
offline and reproduced the live run byte-for-byte on all five pages, so the
before/after numbers below rest on one snapshot each.

## Counts

| stage | high | medium | acknowledged | low | rows |
|---|---|---|---|---|---|
| before, default rules | 0 | 56 | 0 | 81 | 137 |
| before, project `craft-rules.json` (the gate's view) | 0 | 36 | 0 | 81 | 117 |
| after, default rules | 0 | 9 | 0 | 35 | 44 |
| after, project rules | 0 | 1 | 3 | 35 | 39 |

Labels over the 137 default-rule findings: **GERÇEK 5 · FP 31 · KABUL 101**.

## Table

`rule` · `board/shape` · `label` · `why` (the crop that decided it in parentheses)

| rule | board / shape | n | label | why |
|---|---|---|---|---|
| type.steps | all 5 pages | 20 | KABUL | 13→16 = 1.23 is the project's declared body/meta step; `craft-rules.json` sets `min_step_ratio` 1.2 and the gate passes that file. Under the project rules: 0 findings. |
| type.small_body | footer address (all 18 boards) | 18 | KABUL | legal/address meta at 13px, grey, in the footer — the declared meta role (1:1 İHKD footers). |
| type.small_body | footer legal 2 (all 18 boards) | 18 | KABUL | "Tasarım çalışması — kurum ve kişiler kurgudur." is fine print by definition (1:1). |
| type.small_body | 07-program sess meta 0–18 | 19 | KABUL | time/chair meta under the session title; the project's grid is 13px meta (1:1 row crop). |
| type.small_body | 08-bildiri faq a 0–2 | 3 | **GERÇEK** | the FAQ *answer* is content, not meta: 13px grey under a 16px question reads as fine print (1:1 crop of the SSS block) → set answers to the 16px body. |
| type.small_body | 23 single meta/caption/note texts (a meta, au bio, t sub, ics, f check label, p note, v note, tr note 0, img-cath caption, prev where 0, band text 12:00, member fee, akademi note, cover imprint, cover countdown, sec note, g chair, f by, s cert, k instructor, k meta, method, foot) | 23 | KABUL | captions, bylines, methodology notes and legal lines: each read as meta at 1:1 (checked 12-kurs-detay, 16-makale, 13-kilavuzlar, 03-yonetim). |
| inline.baseline | 9 mixed-size row classes: 12-kurs-detay `m n`/`m title`, 14-dergi `toc p`/`toc k`, 07-program `day num`/`day month`, 08-bildiri `dl label`/`dl value`, 09-kayit `fee name`/`fee badge`, 01-ana-sayfa `toc page`/`toc title`, 01-ana-sayfa `head num`/`head label`, 04-calisma-gruplari `g idx`/`g name`, 16-makale `a share label`/`a share li` | 28 rows (23 pairs + 5 summaries) | FP | every class was cropped 1:1: the 13px index/label sits on the 16/30px title's baseline or is deliberately centred against a two-line block; none drifted (m_row, toc_row, 07_daytabs, fee_row, g_row, head_row, faq). The rule could not tell a prompt from a defect — retired (`RULES["inline.baseline"]`). |
| dead_space | 14-dergi toc sheet 46px | 1 | FP | entry inset 47px vs trailing 46px: symmetric sheet padding (tocsheet.png). |
| dead_space | 16-makale article sheet 52px | 1 | FP | entry inset 55px vs trailing 52px: symmetric article-sheet padding (articlesheet.png). |
| dead_space | 01-ana-sayfa uyelik band 74px | 1 | FP | band top pad 80px vs trailing 74px: section band padding, not a leak (uyelik_band.png). |
| dead_space | 20-panel sidebar 39px | 1 | KABUL | the sign-out row is docked at the foot: 39px pad under it against a 24px head pad (sidebar.png) → `acknowledge` entry. |
| gap.intra_card | 07-program sess card 8, sess card 2 (40px) | 2 | **GERÇEK** | the card is 128px tall while its one-line title + 2-line meta need 104px: it was sized for a wrapped title, so its meta drifts 38px below the title and its bottom sits 24px under its row-mates (card 3 h=104). Fix: re-height both cards. |
| gap.intra_card | 18-uyelik form 40px | 1 | KABUL | the KVKK consent line is its own block; the break separates consent from the document rows (form_gap.png) → `acknowledge`. |
| gap.intra_card | 19-giris auth left 72px | 1 | KABUL | the brand panel pins the photo caption to its top and the legal footer to its bottom; the 72px is the panel's spare height (auth_gap.png) → `acknowledge`. |

## To fix on the design (closed 2026-11-03 — see § Resolved)

1. `08-bildiri` — SSS answers at 16px instead of 13px (3 nodes; the `faq a *` texts).
2. `07-program` — `sess card 8` and `sess card 2`: re-height to the content (104px, like
   `sess card 3`) so the title/meta gap returns to 14px and the row bottoms align.

Both stayed in the lint output: (1) as `type.small_body` LOW (present in `--json` and
`--verbose`, hidden by default), (2) as the one unexplained MEDIUM.

## Rule changes this triage justified

| change | evidence |
|---|---|
| `inline.baseline` retired | 23/23 pairs clean at 1:1; no museum fixture ever failed without it |
| `dead_space` learns symmetric padding (`dead_pad_tol` 8px) | 3/4 live hits were a void equal to the container's own entry inset |
| `type.small_body` → LOW, grouped | 78/81 are declared meta; the 3 real ones stay in the JSON |
| grouping by cause (`family`) | 19 session metas → 1 row, 18 footers → 1 row; counts kept |
| `acknowledge` (craft-rules.json) replaces ad-hoc exemptions | 3 accepted decisions, each with a reason and a 1:1 check |

## Limits of this triage

- Kurumsal was being edited by another agent during the capture. The dump is a
  snapshot; both before and after runs read that same snapshot, so the delta is
  valid, but the page's live state has moved on.
- The corpus proves what the rules do on *this* design, not that a rule is
  wrong in general: 16 rules produced no live finding and are covered only by
  their museum fixtures.
- `type.small_body` cannot distinguish a 13px *meta* from a 13px *content*
  paragraph by geometry alone; the three FAQ answers are the price of that, and
  they are the reason the rule is report-only (LOW), not silent.

## Resolved (2026-11-03) — the corpus above is frozen

1. **08-bildiri FAQ answers** — the four `faq a *` nodes (the triage counted three; the fourth
   is 39 chars and stayed under the `type.small_body` threshold) are 16px `body` with a 72px
   row pitch (was 13px `meta` / 60px); the board grew 2568 → 2632 and the footer docks to the
   last rule. Lint no longer reports `faq a 0-2`; the SSS block was read at 1:1
   (`shots/08-bildiri.png`, crop of 1920-2220).
2. **07-program `sess card 2` / `sess card 8`** — `lib.fitCards` now re-settles a card's meta
   on the title's measured ink before sizing the card (the line count was an estimate, and a
   character model cannot tell where a title wraps). Both cards: 128px / 40px joint → 104px /
   16px, the same as their row-mates, accent bar padding kept. The page's `gap.intra_card`
   medium is gone; the rows were read at 1:1.
3. **New, proven on the render (not in the frozen corpus): 19/20 shape-opacity text.**
   `al sub` and `al foot` (13px, opacity .72) composited to 3.66:1 on `red.600`; `al caption`
   (.80) 4.25:1; `mc label` (.72) 3.66:1 — all below AA. They are opaque `on.red` now
   (6.04:1, pixel-verified). The intentional .88/.85 secondary lines stay: measured 4.88 and
   4.64:1. The lint collector does not yet see shape opacity, so this finding came from a
   tool review; both boards were rebuilt and re-read at 1:1.

The triage table above is left as captured; these three notes are the closure record.
