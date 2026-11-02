# İHKD — handoff index

Clinical-society platform for the invented **İHKD (İç Hastalıkları ve Kardiyoloji Derneği)**,
Ankara, founded 1998. Public site + congress + academy + journal, with a member desk behind a
login. Story one-liner: **Hastanın hekimi.** — kılavuz, kongre ve akademi tek adreste.

- Pages: `Kurumsal` (5 boards + empty state) · `Kongre` (5 + loading + error state) ·
  `Akademi` (4) · `İçerik` (3) · `Üyelik` (3) · `Components` (library sheet, 30 components).
- Token set: **`ihkd`** (`design/ihkd/tokens.json`; `tokens_sync --check` clean).
- Library: `design/ihkd/build/lib.js`; screens `screen-01…20.js` + `screen-state-01/07/09.js`
  + `screen-components.js`, one at a time through `build.py` (it restores photos from
  provenance, re-applies `flows.js` and verifies `photos N/N` / `links N/N`).
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
all five pages). Roles: `label · meta · data · body · bodyMed · nav · lead · h3 · h2 · stat ·
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

## Boards (live, re-verified 2026-11-03)

| # | page | board | size | live id |
|---|---|---|---|---|
| 01 | Kurumsal | 01-ana-sayfa | 1440×4076 | 20e5225e-73fe-80f2-8008-ddabe9d31da3 |
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
| — | Components | component sheet | 1440×2460 | d464fdd4-6900-809f-8008-e2dc73baa1d4 |

## Export evidence (`design/ihkd/shots/`, bytes on disk 2026-11-03)

| board | PNG bytes | board | PNG bytes |
|---|---|---|---|
| 01-ana-sayfa | 1221293 | 11-akademi | 211899 |
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
| `img-desk` | 13-kilavuzlar | https://www.pexels.com/photo/35044388/ by Marta Branco |
| `img-issue` | 14-dergi | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| `img-round` | 15-haberler | https://www.pexels.com/photo/6129043/ by RDNE Stock project |
| `img-team` | 16-makale | https://www.pexels.com/photo/20370745/ by Michael Obiero |
| `img-auth` | 19-giris | https://www.pexels.com/photo/8460227/ by Los Muertos Crew |

The pinned URL in `tools/media.py` is the single source, so a rebuild reimports the accepted
frame. The parked candidates' slots are also in provenance (`…@cand-2-kapak`,
`…@cand-4-topluluk`, page `_scratch`).

## Flows (live: 5 flows, 7 links, 0 errors)

| flow | page | interaction |
|---|---|---|
| `keşif` | Kurumsal (01-ana-sayfa) | `groups all` → 04-calisma-gruplari; `board all` (02) → 03-yonetim |
| `kayıt` | Kurumsal + Kongre (09-kayit) | `k cta` → 10-konaklama |
| `kurs` | Akademi (11-akademi) | `f cta` → 12-kurs-detay |
| `oku` | İçerik (15-haberler) | `f cta` → 16-makale |
| `üye` | Üyelik (19-giris) | `f submit` → 20-panel; `p cta` (20) → 18-uyelik |

Cross-page journeys stay unwired by design (the API stores a hollow destination proxy). The
01 primary and its ghost are cross-page, so the page's same-page route is the groups link.

## Gaps / limitations (honest list)

1. **Cross-page journeys unwired** (above). Wire them in the Penpot UI if needed.
2. **No mobile twin.** Mobile was dropped from the roadmap; `ux_gate` passes without the key.
   Adding it back is a decision, not a build detail.
3. **Components are not instanced** by the screens. The library is the handoff object; moving
   to instances is a breaking change and a later job.
4. **Ghost numerals** (`head num`, `ink.400`, 2.07:1) are decorative order marks; real copy
   never uses `ink.400` (principles §6).
5. **`fs.12`** remains in the token set as an unbound orphan (`tokens_sync` is additive). No
   shape binds it; QA coverage is 100% without it.
6. **Crop tool is provisional.** `crop_board`'s region heuristic picks the topmost
   CTA/label (often the nav) and its off-origin frame mis-framed three state-board crops;
   those manifest notes say so, and the coordinator re-cuts after the tool fix. Tiles are
   real; the region frames are not all trustworthy.
7. **Contrast on photographs** cannot be proven from token pairs. The 01 hero was measured
   against the pixels behind each ink box (worst 5.17:1) and 19/20's red-panel labels on
   their render (6.04 / 4.88 / 4.64:1); any new photo needs the same measurement.
8. **Exporter collision risk:** `export_png` accepts only a PNG of the exact size, so two
   boards of identical dimensions could still swap renders on the disk-rescue path.
9. **`_scratch` remains.** Three hero candidates (kept at the user's request, one is the live
   hero's source) and two parked concepts live there. Nothing is deleted without the user.
10. **State coverage is desktop-only and partial**: empty (01), loading (07), registration
    error (09). Success/disabled/offline states are not drawn.
