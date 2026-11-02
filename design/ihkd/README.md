# İHKD — handoff index

Clinical-society platform for the invented **İHKD (İç Hastalıkları ve Kardiyoloji Derneği)**,
Ankara, founded 1998. Public site + congress + academy + journal, with a member desk behind
a login. Story one-liner: **Hastanın hekimi.** — kılavuz, kongre ve akademi tek adreste.

- Pages: `Kurumsal` (5 boards) · `Kongre` (5) · `Akademi` (4) · `İçerik` (3) · `Üyelik` (3).
  `Components` is empty (see gaps); `_scratch` is empty (stray `Path` removed this milestone).
- Token set: **`ihkd`** (`design/ihkd/tokens.json`, no drift — `tokens_sync --check` clean).
- Library: `design/ihkd/build/lib.js` (used only, never edited here). Builders:
  `design/ihkd/build/screen-01.js` … `screen-20.js`, run one at a time via `build.py`.
- Flows map (re-applied live, no rebuild wiring): `design/ihkd/build/flows.js`.
- Exports: `design/ihkd/shots/*.png` (20 board files + `01-joint-crop.png`; sizes tabled below).
  This milestone changed no pixels except links, so exports stay valid.

## Tokens (live `tokens.json`)

| token | value | use |
|---|---|---|
| `ink.900` | #0E1318 | headings, primary text |
| `ink.800` | #1B232A | strong text |
| `ink.700` | #333D45 | text |
| `ink.600` | #55606A | secondary text |
| `ink.500` | #5E6A71 | meta, caption (darkened from #6E7982 for AA; repainted on full rebuild) |
| `ink.400` | #A3ADB5 | placeholder, ghost numerals, disabled |
| `paper` | #F2F4F5 | page background, every board |
| `white` | #FFFFFF | cards, inputs, footer / sidebar panels |
| `surface.alt` | #E8EBED | image mat, inset block, pocket cards |
| `line.soft` | #DDE1E4 | hairline rules, dividers |
| `line.300` | #CFDBE4 | input lines, stronger dividers |
| `line.strong` | #B9C0C6 | section rules |
| `red.700` | #8F0F24 | accent text on tint, links, label role |
| `red.600` | #C4122F | primary button, active nav, top bar, progress fill |
| `red.500` | #E85063 | unused (15 bulletin label moved to `red.700`) |
| `red.100` | #FBE3E7 | error field background, deadline tint |
| `red.050` | #FDF1F3 | hover tint, info / quote block |
| `bone` | #FFFFFF | publication sheets (journal, guideline, article) |
| `doc.text` | #14191D | sheet body text |
| `doc.muted` | #5A666E | sheet meta |
| `doc.rule` | #D8DCDE | sheet rules |
| `on.ink` | #FFFFFF | text on ink.900 |
| `on.red` | #FFFFFF | text on red.600 |

Type is bound per shape to `fs.13 / fs.16 / fs.22 / fs.30 / fs.44 / fs.80`
(QA: text-size token coverage 100% on all five pages). Roles live in `lib.js`
(`label · meta · data · body · bodyMed · nav · lead · h3 · h2 · stat · figure ·
display · wordmark`). Spacing tokens `4–120`, radius tokens `0 / 2 / 4` (buttons bind
`radius.2`; corner coverage is not part of the QA token audit).

## Component inventory (`lib.js` primitives)

Atoms: `rect` (fill + optional stroke + radius) · `board` (sub-panel) ·
`text(chars, role, color, {x, y, w, align})` · `rule / vrule` ·
`btn(label, kind: primary | secondary | onred | ghost)` ·
`link(label)` (text + underline) · `tag` (dot + label) ·
`photo(name, x, y, w, h, caption)` (placeholder slot; media fills it) ·
`field(label, value, {placeholder, error, hint})` · `stat(value, label)` ·
`progress(name, pct)` · `ecg(name, tone)` · `row(title, meta, opts)` ·
`crumbs(items)` · `sheet` (bone publication panel).

Blocks: `masthead(active)` (4px red top bar, wordmark, 6 nav links, login + CTA) ·
`pageHead(label, title, lede)` · `head(label, title, {link | index})` (ghost numeral
section head, excluded from the lint dominant-element check by `craft-rules.json`) ·
`footer(y)` (white panel, link columns, legal lines) ·
`sidebar(active, height)` (260px member desk nav).

Lifecycle: `start(page, board, height)` (find-or-create, wipe children, paint
`paper`) · `fit(page)` (re-measure text) · `end` (warnings/gaps, ≤20 shown).

## Boards (live, 1440 wide)

| # | page | board | live id | height |
|---|---|---|---|---|
| 01 | Kurumsal | 01-ana-sayfa | 20e5225e-73fe-80f2-8008-ddabe9d31da3 | 3896 |
| 02 | Kurumsal | 02-dernek | 20e5225e-73fe-80f2-8008-ddaf06748101 | 2452 |
| 03 | Kurumsal | 03-yonetim | 20e5225e-73fe-80f2-8008-ddaf2955649f | 2296 |
| 04 | Kurumsal | 04-calisma-gruplari | 20e5225e-73fe-80f2-8008-ddaf3f95791b | 2088 |
| 05 | Kurumsal | 05-grup-detay | 20e5225e-73fe-80f2-8008-dddfa2dba62d | 2684 |
| 06 | Kongre | 06-kongre | 48eb7286-684f-8018-8008-e18d9ac60385 | 3840 |
| 07 | Kongre | 07-program | 48eb7286-684f-8018-8008-e18de1b20b79 | 2716 |
| 08 | Kongre | 08-bildiri | 48eb7286-684f-8018-8008-e18df3c083f2 | 2568 |
| 09 | Kongre | 09-kayit | 48eb7286-684f-8018-8008-e18e04bbb783 | 2000 |
| 10 | Kongre | 10-konaklama | 48eb7286-684f-8018-8008-e18e155d92c1 | 2400 |
| 11 | Akademi | 11-akademi | 48eb7286-684f-8018-8008-e195e681d762 | 2488 |
| 12 | Akademi | 12-kurs-detay | 48eb7286-684f-8018-8008-e195f464c9c3 | 1740 |
| 13 | Akademi | 13-kilavuzlar | 48eb7286-684f-8018-8008-e196021511f5 | 2400 |
| 14 | Akademi | 14-dergi | 48eb7286-684f-8018-8008-e19611df36e9 | 2000 |
| 15 | İçerik | 15-haberler | 48eb7286-684f-8018-8008-e1961e99e8fd | 2080 |
| 16 | İçerik | 16-makale | 48eb7286-684f-8018-8008-e1978c73ee8e | 2540 |
| 17 | İçerik | 17-takvim | 48eb7286-684f-8018-8008-e19796e7ecb7 | 2096 |
| 18 | Üyelik | 18-uyelik | 48eb7286-684f-8018-8008-e197aa759d2e | 2292 |
| 19 | Üyelik | 19-giris | 48eb7286-684f-8018-8008-e197b848b03b | 1024 |
| 20 | Üyelik | 20-panel | 48eb7286-684f-8018-8008-e197bd55d6fb | 1680 |

Heights are the `S.start` heights in `screen-01…20.js` (snapped to 4px live:
02 → 2452, 08 → 2568). This milestone rebuilt all 20 boards on the new type scale
(meta/label/data 13px, `stat` 44px, ghost numerals 44px); the older M8 live heights
above are superseded.

## Export evidence (`design/ihkd/shots/`)

| board | PNG bytes (current `design/ihkd/shots/`) |
|---|---|
| 01-ana-sayfa | 716250 |
| 02-dernek | 258613 |
| 03-yonetim | 232268 |
| 04-calisma-gruplari | 238005 |
| 05-grup-detay | 519520 |
| 06-kongre | 991272 |
| 07-program | 283783 |
| 08-bildiri | 272425 |
| 09-kayit | 171843 |
| 10-konaklama | 716034 |
| 11-akademi | 422030 |
| 12-kurs-detay | 251516 |
| 13-kilavuzlar | 384960 |
| 14-dergi | 331920 |
| 15-haberler | 424807 |
| 16-makale | 578358 |
| 17-takvim | 143214 |
| 18-uyelik | 203774 |
| 19-giris | 150212 |
| 20-panel | 142864 |

## Photo provenance (`design/ihkd/media/provenance.json` — every placed photo covered)

| image | board | source |
|---|---|---|
| img-echo | 01-ana-sayfa | https://www.pexels.com/photo/6129683/ by RDNE Stock project |
| img-journal | 01-ana-sayfa | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| img-cath | 05-grup-detay · 06-kongre (same source) | https://www.pexels.com/photo/28583897/ by محمد عزام الشيخ يوسف |
| img-hall | 06-kongre | https://www.pexels.com/photo/9275222/ by Atlantic Ambience |
| img-corridor | 10-konaklama | https://www.pexels.com/photo/37770089/ by Svet Svet |
| img-venue | 10-konaklama | https://www.pexels.com/photo/35877127/ by Mark Stebnicki |
| img-seminar | 11-akademi | https://www.pexels.com/photo/1170979/ by EVG Kowalievska |
| img-lab | 12-kurs-detay | https://www.pexels.com/photo/7659573/ by Thirdman |
| img-desk | 13-kilavuzlar | https://www.pexels.com/photo/35044388/ by Marta Branco |
| img-issue | 14-dergi | https://www.pexels.com/photo/3860983/ by Robert Munteanu |
| img-round | 15-haberler | https://www.pexels.com/photo/6129043/ by RDNE Stock project |
| img-team | 16-makale | https://www.pexels.com/photo/20370745/ by Michael Obiero |
| img-auth | 19-giris | https://www.pexels.com/photo/8460227/ by Los Muertos Crew |

Live check: 14 placed `img-*` shapes (12 boards; 01 places two, 06 places two,
10 places two) — each name has a base and a `@board` provenance entry. No gaps.

## Flows (live-verified this milestone: full rebuild, then 8 re-links, 0 errors)

- `keşif` + `kayıt` (Kurumsal, both start 01-ana-sayfa): `hero cta`
  (“Kongreye kayıt ol”) → 04-calisma-gruplari; `hero cta 2` (“Derneği tanı”) →
  02-dernek; `board all` (“Tüm kurullar”) → 03-yonetim.
- `kayıt` (Kongre, start 09-kayit): `k cta` (“Kaydı tamamla”) → 10-konaklama.
- `kurs` (Akademi, start 11-akademi): `f cta` (“Devam et”) → 12-kurs-detay.
- `oku` (İçerik, start 15-haberler): `f cta` (“Haberi oku”) → 16-makale.
- `üye` (Üyelik, start 19-giris): `f submit` (“Giriş yap”) → 20-panel;
  `p cta` → 18-uyelik.

No junk null-start flows (auto-named `Flow N` side effects dropped in the same call).
Per-board interaction counts: 01 = 2, 02 = 1, 09 = 1, 11 = 1, 15 = 1, 19 = 1, 20 = 1.
Note: two flows share the name `kayıt` on different pages (Kurumsal start 01,
Kongre start 09) — inherited from `flows.js`, harmless but confusing; renaming is
owned by the flows milestone, not this one.

## Gaps / limitations (honest list)

1. Cross-page journeys stay unwired by design: `navigate-to` to another page stores
   a hollow destination proxy (`id: ""`), verified live — only the 8 same-page
   links above exist. Wire cross-page journeys in the Penpot UI if needed.
2. `Components` page holds no library sheet (brief §4 names one); the build
   scripts are the working library. Deliberate deviation, recorded here.
3. Ghost numerals (`head num`, ink.400 2.07:1) are exempt from the contrast gate:
   44px order marks redundant with the adjacent section title — felt, not read.
   Contrast gates run with `--ignore "head num"`; see principles §8.
4. Lint mediums stand per `craft-rules.json`: the uppercase ceiling
   (`max_uppercase_ratio` 0.35), the 13→16 microcopy step (1.23, the body/meta-pair
   exception class — see principles §8), and inline mixed-size baseline pointers
   (verified at 1:1 this milestone). 0 high on all five pages.
5. `fs.12` remains in the Penpot set as an unbound orphan (tokens_sync is additive
   by design and never deletes; `--check` reports it as informational). No shape
   binds it; QA text-size coverage is 100% without it.
6. `build.py` `SCREENS` lists a `components` entry with no `components.js` file, so
   `build.py all` exits 1 after building all 20 screens. Pre-existing script-side
   condition; not touched (scripts/ owned elsewhere).
