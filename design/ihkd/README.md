# İHKD — handoff index

Clinical-society platform for the invented **İHKD (İç Hastalıkları ve Kardiyoloji Derneği)**,
Ankara, founded 1998. Public site + congress + academy + journal, with a member desk behind a
login. Story one-liner: **Hastanın hekimi.** — kılavuz, kongre ve akademi tek adreste.

- Pages: `Kurumsal` (5 boards + empty state) · `Kongre` (5 + loading + error state) ·
  `Akademi` (4) · `İçerik` (3) · `Üyelik` (3) · `Mobil` (2: home + open menu) ·
  `Components` (library sheet, 30 components).
- Token set: **`ihkd`** (`design/ihkd/tokens.json`; `tokens_sync --check` clean).
- Library: `design/ihkd/build/lib.js`; screens `screen-01…20.js` + the mobile `screen-01-m.js`
  / `screen-state-01-m.js` + `screen-state-01/07/09.js` + `screen-components.js`, one at a time
  through `build.py` (it restores photos from provenance, re-applies `flows.js` and verifies
  `photos N/N` / `links N/N`).
- Exports: `design/ihkd/shots/*.png`; `shots/<board>/` holds the 1:1 tiles and the manifest
  whose notes are the review record.
- Selected hero: the **congress poster** (candidate 1), contract in `brief.md` § M8. Two
  further candidates are parked with build scripts (brief § Parked concepts); their boards
  and renders are kept at the user's request.

## Tokens (live `tokens.json`)

| token | value | use |
|---|---|---|
| `ink.900` | #0E1318 | headings, primary text |
| `ink.800` | #1B232A | strong text |
| `ink.700` | #333D45 | text |
| `ink.600` | #55606A | secondary text |
| `ink.500` | #5E6A71 | meta, caption (AA on paper) |
| `ink.400` | #A3ADB5 | placeholder, ghost numerals, disabled |
| `paper` | #F2F4F5 | page ground, every board |
| `white` | #FFFFFF | cards, inputs, footer / sidebar panels |
| `surface.alt` | #E8EBED | image mat, inset/secondary panel, skeleton, disabled |
| `line.soft` | #DDE1E4 | hairline rules, dividers |
| `line.300` | #CFDBE4 | input lines, stronger dividers |
| `line.strong` | #B9C0C6 | section rules |
| `red.700` | #8F0F24 | accent text on tint, links, label role |
| `red.600` | #C4122F | primary button, active nav, top bar, progress fill |
| `red.500` | #E85063 | unused |
| `red.100` | #FBE3E7 | error field background, deadline tint |
| `red.050` | #FDF1F3 | hover tint, info / quote block |
| `bone` | #FFFFFF | publication sheets (journal, guideline, article) |
| `doc.text` | #14191D | sheet body text |
| `doc.muted` | #5A666E | sheet meta |
| `doc.rule` | #D8DCDE | sheet rules |
| `on.ink` | #FFFFFF | text on ink.900 |
| `on.red` | #FFFFFF | text on red.600 |

Type is bound per shape to `fs.13 / 16 / 22 / 30 / 44 / 80` (QA text-size coverage 100% on
all six pages). Roles: `label · meta · data · body · bodyMed · nav · lead · h3 · h2 · stat ·
figure · display · wordmark`. Spacing `4–120`, radius `0 / 2 / 4`.

## Component inventory

**Primitives (`lib.js`)**: `rect · board · text · rule / vrule · btn(primary | secondary |
onred | ghost) · link · tag · photo · field · stat · progress · ecg · row · crumbs · sheet ·
masthead · pageHead · head · headIndex · footer · sidebar · statsStrip · ctaRow · chips ·
rows · bullets · fit · fitBars · fitCards`.

**Library components (30, `Components` page)**: `button-primary` / `-secondary` / `-ghost`
× `default · hover · focus · active · disabled` (15), `field` × `default · hover · focus ·
error · disabled` (5), `row` × `default · hover · focus` (3), `chip` × `default · hover ·
active · disabled` (4), `tag`, `card`, `stat` (3). Names are `aile-durum`, not `aile/durum`:
Penpot rewrites a `/` in a shape or component name as a path separator. The screens do not
instance them yet — moving to instances is a breaking change and a later job.

## Boards (live; 01 and Mobil re-verified 2026-11-05, others 2026-11-03)

| # | page | board | size | live id |
|---|---|---|---|---|
| 01 | Kurumsal | 01-ana-sayfa | 1440×4084 | 20e5225e-73fe-80f2-8008-ddabe9d31da3 |
| 02 | Kurumsal | 02-dernek | 1440×2452 | 20e5225e-73fe-80f2-8008-ddaf06748101 |
| 03 | Kurumsal | 03-yonetim | 1440×2296 | 20e5225e-73fe-80f2-8008-ddaf2955649f |
| 04 | Kurumsal | 04-calisma-gruplari | 1440×2088 | 20e5225e-73fe-80f2-8008-ddaf3f95791b |
| 05 | Kurumsal | 05-grup-detay | 1440×2512 | 20e5225e-73fe-80f2-8008-dddfa2dba62d |
| — | Kurumsal | 01-bos (empty) | 1440×592 | d464fdd4-6900-809f-8008-e2dd5fe2e91b |
| 06 | Kongre | 06-kongre | 1440×3840 | 48eb7286-684f-8018-8008-e18d9ac60385 |
| 07 | Kongre | 07-program | 1440×2856 | 48eb7286-684f-8018-8008-e18de1b20b79 |
| 08 | Kongre | 08-bildiri | 1440×2632 | 48eb7286-684f-8018-8008-e18df3c083f2 |
| 09 | Kongre | 09-kayit | 1440×1968 | 48eb7286-684f-8018-8008-e18e04bbb783 |
| 10 | Kongre | 10-konaklama | 1440×2400 | 48eb7286-684f-8018-8008-e18e155d92c1 |
| — | Kongre | 07-program-loading | 1440×1300 | d464fdd4-6900-809f-8008-e2dd75292db9 |
| — | Kongre | 09-kayit-hata | 1440×1104 | d464fdd4-6900-809f-8008-e2dd931a9cf4 |
| 11 | Akademi | 11-akademi | 1440×2488 | 48eb7286-684f-8018-8008-e195e681d762 |
| 12 | Akademi | 12-kurs-detay | 1440×1736 | 48eb7286-684f-8018-8008-e195f464c9c3 |
| 13 | Akademi | 13-kilavuzlar | 1440×2400 | 48eb7286-684f-8018-8008-e196021511f5 |
| 14 | Akademi | 14-dergi | 1440×2000 | 48eb7286-684f-8018-8008-e19611df36e9 |
| 15 | İçerik | 15-haberler | 1440×2080 | 48eb7286-684f-8018-8008-e1961e99e8fd |
| 16 | İçerik | 16-makale | 1440×2416 | 48eb7286-684f-8018-8008-e1978c73ee8e |
| 17 | İçerik | 17-takvim | 1440×2096 | 48eb7286-684f-8018-8008-e19796e7ecb7 |
| 18 | Üyelik | 18-uyelik | 1440×2292 | 48eb7286-684f-8018-8008-e197aa759d2e |
| 19 | Üyelik | 19-giris | 1440×1024 | 48eb7286-684f-8018-8008-e197b848b03b |
| 20 | Üyelik | 20-panel | 1440×1680 | 48eb7286-684f-8018-8008-e197bd55d6fb |
| 01 | Mobil | 01-ana-sayfa-m | 390×5436 | — |
| — | Mobil | 01-ana-sayfa-m-menu (menu state) | 390×844 | — |
| — | Components | component sheet | 1440×2460 | d464fdd4-6900-809f-8008-e2dc73baa1d4 |

Canvas spacing: after a rebuild settles a board's height, the runner reconciles that board's
column (`lib.reflowColumn`, the project's 240px gap). Only the following boards that would sit
closer than 240px move; ids, sizes, contents and relative child geometry are untouched, and a
large deliberate gap is never compacted. 2026-11-03 on Kongre: `07-program` +40,
`08-bildiri` +396, overlap 0, every other board where it was; a second run is a no-op.

## Export evidence (`design/ihkd/shots/`, bytes on disk 2026-11-03; 01 re-exported 2026-11-05)

| board | PNG bytes | board | PNG bytes |
|---|---|---|---|
| 01-ana-sayfa | 1341471 | 11-akademi | 211899 |
| 01-bos | 58582 | 12-kurs-detay | 255395 |
| 02-dernek | 258613 | 13-kilavuzlar | 384861 |
| 03-yonetim | 232334 | 14-dergi | 331920 |
| 04-calisma-gruplari | 238373 | 15-haberler | 424540 |
| 05-grup-detay | 583029 | 16-makale | 577157 |
| 06-kongre | 991271 | 17-takvim | 143214 |
| 07-program | 293825 | 18-uyelik | 203774 |
| 07-program-loading | 48773 | 19-giris | 150241 |
| 08-bildiri | 277412 | 20-panel | 142754 |
| 09-kayit | 171892 | component sheet | 140540 |
| 09-kayit-hata | 83178 | | |

Fresh this round: 01 (reused), 01-bos, 02, 04, 06, 07, 07-program-loading, 08, 09,
09-kayit-hata, 14, 15, 16, 19, 20, component sheet. The older full-PNG set (03, 05, 10, 11,
12, 13, 17, 18) was not rebuilt and its renders stay as the last accepted snapshot.

## Photo provenance (`media/provenance.json` — one `name@board` entry per placement)

| image | board | source |
|---|---|---|
| `img-hero` | 01-ana-sayfa | https://www.pexels.com/photo/20733081/ by BBSO |
| `img-journal` | 01-ana-sayfa | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| `img-angio` | 05-grup-detay | https://www.pexels.com/photo/39459346/ by Stéf -b. |
| `img-cath` | 06-kongre | https://www.pexels.com/photo/28583897/ by محمد عزام الشيخ يوسف |
| `img-hall` | 06-kongre | https://www.pexels.com/photo/9275222/ by Atlantic Ambience |
| `img-corridor` | 10-konaklama | https://www.pexels.com/photo/37770089/ by Svet Svet |
| `img-venue` | 10-konaklama | https://www.pexels.com/photo/35877127/ by Mark Stebnicki |
| `img-seminar` | 11-akademi | https://www.pexels.com/photo/1170979/ by EVG Kowalievska |
| `img-lab` | 12-kurs-detay | https://www.pexels.com/photo/28585011/ by Marta Branco |
| `img-desk` | 13-kilavuzlar | https://www.pexels.com/photo/415779/ by Pixabay |
| `img-issue` | 14-dergi | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| `img-round` | 15-haberler | https://www.pexels.com/photo/6129043/ by RDNE Stock project |
| `img-team` | 16-makale | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| `img-auth` | 19-giris | https://www.pexels.com/photo/415779/ by Pixabay |

The pinned URL in `tools/media.py` is the single source, so a rebuild reimports the accepted
frame. The parked candidates' slots are also in provenance (`…@cand-2-kapak`,
`…@cand-4-topluluk`, page `_scratch`).

## Flows (live: 6 flows, 9 links, 0 errors)

| flow | page | interaction |
|---|---|---|
| `keşif` | Kurumsal (01-ana-sayfa) | `groups all` → 04-calisma-gruplari; `board all` (02) → 03-yonetim |
| `kayıt` | Kurumsal + Kongre (09-kayit) | `k cta` → 10-konaklama |
| `kurs` | Akademi (11-akademi) | `f cta` → 12-kurs-detay |
| `oku` | İçerik (15-haberler) | `f cta` → 16-makale |
| `üye` | Üyelik (19-giris) | `f submit` → 20-panel; `p cta` (20) → 18-uyelik |
| `menü` | Mobil (01-ana-sayfa-m) | `masthead menu` → 01-ana-sayfa-m-menu; `menu close` (menu) → 01-ana-sayfa-m |

Cross-page journeys stay unwired by design (the API stores a hollow destination proxy). The
01 primary and its ghost are cross-page, so the page's same-page route is the groups link.

## Gaps / limitations (honest list)

1. **Cross-page journeys unwired** (above). Wire them in the Penpot UI if needed.
2. **Mobile is one screen, not a system.** `Mobil` carries the phone twin of the home
   (`01-ana-sayfa-m` 390×5436) and its open menu (`01-ana-sayfa-m-menu` 390×844), wired as flow
   `menü`. The other 19 screens, their three state boards and the component sheet stay
   desktop-only: the twin proves the home's refold, not a mobile breakpoint set or a mobile
   library.
3. **Components are not instanced** by the screens. The library is the handoff object; moving
   to instances is a breaking change and a later job.
4. **Ghost numerals** (`head num`, `ink.400`, 2.07:1) are decorative order marks; real copy
   never uses `ink.400` (principles §6).
5. **`fs.12`** remains in the token set as an unbound orphan (`tokens_sync` is additive). No
   shape binds it; QA coverage is 100% without it.
6. **Crop regions need an explicit primary on nav-carrying boards.** The repaired
   `crop_board` resolves regions from a node dump and accepts `--primary-action`; without it
   the heuristic can still pick a nav label on boards whose CTA lives in the chrome. Every
   board's choice is in `tools/crop-plan.json`, and `--attest` now fails a missing PNG.
7. **Contrast on photographs** cannot be proven from token pairs (the audit prints MANUAL, not
   pass). The 01 hero was measured against the pixels behind each ink box (worst 5.17:1) and
   19/20's red-panel labels on their render (6.04 / 4.88 / 4.64:1); 13/16/19's replaced photos
   carry their captions on paper below the frame, so no text sits on an image there.
8. **Exporter collision risk:** `export_png` accepts only a PNG of the exact size, so two
   boards of identical dimensions could still swap renders on the disk-rescue path.
9. **`_scratch` remains.** Three hero candidates (kept at the user's request, one is the live
   hero's source) and two parked concepts live there. Nothing is deleted without the user.
10. **State coverage is partial**: empty (01), loading (07) and registration error (09) on
    desktop, the open menu on `Mobil`. Success/disabled/offline states are not drawn.
11. **`contrast_audit.py` read an unset shape opacity as 0** (`Number(null) === 0`), so on
    this file every text was "translucent (opacity 0)" and nothing was checked automatically.
    Fixed in the tool (`num()` falls back on null/undefined/"" before coercion; an unreadable
    value is MANUAL, an explicit 0 stays transparent), with `ContrastCollectorTest` running the
    shipped COLLECT source in node against null/0/.72/1/bad values (§ Verification item 2).
12. **The Penpot file is still named "New File 3"** (live check this round). Renaming is a
    live write on the shared file and is left to the owner of the handoff, not a build step.
13. **Component instances are not used by the screens** (see § Component inventory); the
    library is the handoff object.

## Verification — 2026-11-03 final acceptance (integrated tools, main `32ce45c`)

Run on this checkout with the cherry-picked evidence tools (`2420380`, `2279557`, `a0e3b01`).

| check | result |
|---|---|
| `python -m unittest …` (4 modules) | **272 tests OK** (266 + 6 palette-config tests added this round) |
| `docs_check.py` | 0 findings, 12 files |
| `design_lint … --rules craft-rules.json` on five pages + `Components` | **0 high, 0 unexplained medium** everywhere; Üyelik's 3 mediums are its `acknowledge` entries |
| `design_qa` on Kurumsal/Kongre/Components/Üyelik | fills 764/764 · 885/885 · 120/120 · 261/261, text sizes 100%, `findings: none` except Components' advisory "no prototype flow" (a library page has no journey — printed, not called clean) |
| `ux_gate --spec` | **0 findings**, 3 screens |
| `contrast_audit` (Kurumsal, Üyelik, Components — repository tool, exit 0/0/1) | Kurumsal 593 texts / 578 checked / **0 failing**, 7 ghost numerals ignored, 8 MANUAL over `img-hero`; Üyelik 0 fails, 4 MANUAL (the retained .85/.88 lines, measured 4.88 / 4.64 on the render); Components 6 automatic fails, all **disabled-state** labels (1.91–2.28) — inactive controls, no live-content failure |
| `crop_board` re-cut (11 boards) + `--attest` | exit 0 on every board; no blank CTA region; the hero CTA, 07's nav CTA, 08's `f send` and 09's `reg cta` are the crop subjects |
| negative attest (temp fixture, one PNG removed) | exit 1 with "1 referenced PNG(s) missing" — the real evidence files were copied, never deleted |
| `penpot_exec.py --read` | returns the live file and all seven pages live at the time (`Kurumsal…_scratch`; `Mobil` was added later) |

Two tool/data facts this round produced, recorded so the next reader does not rediscover them:

1. **`craft-rules.json` surface palette must be a list.** Written as scalars it iterated as
   characters, `surface.role` silently reported nothing, and every page looked green for the
   whole previous milestone. It is `["#FFFFFF"]` / `["#E8EBED"]` now; `design_lint.py` rejects a
   non-list or non-string entry with exit 2 at the rules-loading boundary, and
   `test_lint_rules.ProjectPaletteConfigTest` proves the shipped config activates the rule
   (fixture → 1 medium) and that no `design/*/craft-rules.json` carries a scalar again.
2. **`contrast_audit.py` treated an unset shape opacity as 0.** `num(null, 1)` →
   `Number(null)=0`, so every text was "translucent (opacity 0)" and nothing was checked
   automatically. Fixed in the tool: `num()` returns the fallback for null/undefined/"" before
   any coercion, keeps an explicit `0` (transparent) and `0.72`/`1` as given, and returns `NaN`
   for an unreadable value so the reader reports it MANUAL instead of inventing a solid ratio.
   `ContrastCollectorTest` executes the shipped COLLECT source in node (null opacity and
   fillOpacity and ancestor → 1; explicit 0 → transparent/MANUAL; 0.72 → 0.72; "abc" →
   MANUAL) and the resolver has NaN guards for both the text and the background layer. The
   numbers in the table above come from the repository tool, no copy.

Photo compliance: `img-auth`, `img-desk` and `img-team` were replaced with already-sourced
instrument/publication frames (415779, 3860983) and their captions corrected; a contact sheet of
the remaining candidates shows `img-round` (physician writing, no patient) and `img-angio`
(cath-lab equipment, masked team at the frame edge) as compliant. 13, 16 and 19 were rebuilt;
photos 1/1 each.
