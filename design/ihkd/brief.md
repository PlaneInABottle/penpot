# İHKD — İç Hastalıkları ve Kardiyoloji Derneği · platform brief (20 screens)

Design exercise for a member-based medical society. **Every organisation, person, date,
price and DOI below is invented for this build.** Nothing is copied from an existing
society; only the *category convention* of a clinical society platform is borrowed
(congress, programme, abstracts, guidelines, journal, member area).

## 1. Product

- Organisation: **İHKD — İç Hastalıkları ve Kardiyoloji Derneği**, Ankara, founded **1998**.
- Product: public institutional site + congress + academy + journal, with a **member
  desk** behind a login.
- Members **6.847** · **41** provincial representatives · **12** working groups ·
  **10** guidelines · quarterly journal **Kardiyovasküler Klinik** (vol. 12).
- Congress: **12. Ulusal İç Hastalıkları ve Kardiyoloji Kongresi**, **22–25 Nisan 2027**,
  Antalya Kongre Merkezi, Belek.
- Audience: internal medicine physicians (cardiology included), residents, fellows, cardiology technicians,
  clinical pharmacologists, medical students, industry medical affairs.
- One primary action per screen: understand the society → pick a working group → read the
  programme → submit an abstract → register → book a room → start a course → open a
  guideline → read the journal → apply → sign in → use the desk.

### The idea: **Hastanın hekimi.** (The patient's physician.)

> 1998'de Ankara'da on dört hekim bir karar verdi: iç hastalıkları hekimliğinin kılavuzu,
> kongresi ve kaydı tek çatı altında olacak. Dernek bunun için var: yazan, toplayan,
> öğreten ve kaydeden bir meslek topluluğu.

That sentence is the whole platform: one guideline library, one congress programme, one
member record — the working tools of internal medicine, in one place.

### Voice

Short sentences. Numbers instead of adjectives. Speak to a colleague, not to a patient.
No `dünyanın önde gelen`, no `çözüm ortağı`, no exclamation marks. Clinical abbreviations
stay as clinicians write them (`STE`, `EF`, `KKY`, `BKA`, `TAVİ`). Turkish, with dates as
`22–25 Nisan 2027` and times as `09:30`.

## 2. Direction — "aydınlık klinik" (daylight clinic)

A clinical product with the lights on: a cool paper canvas, white panels that read
as printed sheets, one arterial red, mono wayfinding labels, graphite order numerals,
and photography that behaves like a window into the ward. Numbers and dates carry
the hierarchy; chrome stays grey.

Six moves that define it:

1. **Daylight canvas, not paper, not black.** Everything lives on `paper` `#F2F4F5`;
   content sits in `white` panels with a 1px `line.soft` border and 8px corners. The
   canvas is the lit examination room; the panel is the printed sheet on the desk.
2. **One arterial red, spent on action and congress.** Red `#C4122F` marks the primary
   button, active nav item, links, selected chips, progress fill, the live ECG trace
   and the congress band. Kickers and category labels are `ink.500`, never red. There
   is no second accent, no green "success", no blue "info".
3. **Type does the hierarchy, not colour.** Inter Tight at 600/700 for headlines,
   400/500 for body and UI; JetBrains Mono for the time gutter, IDs, prices and stat
   figures. Helper text (`meta`) is 13px minimum and AA on paper. Size and weight
   separate levels; colour only separates primary text from meta (`ink.900` vs
   `ink.500/600`). No coloured headings.
4. **Ghost numerals, not ink numerals.** Section order is carried by oversized
   graphite numerals (`ink.400`, 44px) beside the section title — felt, not read.
   A numeral in full ink would compete with the title. One page never numbers the
   same order twice: no parallel `NN / 06`-style counters next to the ghosts.
5. **Room to breathe, then density.** Public pages run ~112px between sections, 24px
   between cards; the congress programme table runs 92px rows on a 30-minute grid;
   the member desk drops to 24px gaps and 44px rows. Density follows the reading task.
6. **The ECG is an instrument.** A 1.5px polyline in red appears on the member card,
   in one guideline block and beside the home congress note. It is data — calibration
   and trace — never a decorative divider, and never a second red band: the home page
   keeps exactly one red field, the congress band.

### Specificity budget

Three things that could only exist for this society:

1. **The congress programme is organised by clinical question, not by specialty.**
   There is a single track list and a single time gutter. Sessions run in council
   format (`konsey`) carry two chairs and a red session bar; every other session carries
   a graphite bar. Format is wayfinding, not identity.
2. **The member card is a clinical ID.** Name, member no, working group, dues status and a
   QR block — the object a physician keeps in a wallet, and the largest element of the desk.
3. **Guidelines are documents with a decision surface.** Each row states year, scope,
   evidence grade, page count and file size, so a clinician can decide whether to download
   from those five fields alone.

Rejected directions:

- **"Kurumsal mavi"** — navy hero, a smiling physician in a corridor, three icon columns.
  Rejected: every hospital site; no direction.
- **"Kâğıt dosya"** — cream paper, serif headlines, mono labels, numbered sections. Rejected:
  it is the register of a printed congress programme, and this product is a working clinical
  tool that someone opens on a ward laptop at 07:40.
- **Superseded — "klinik panel" v1–v2 (cobalt).** Cobalt `#1B4DC4` accent on `canvas`
  `#EEF2F6`, "no numbered sections, no monospace headlines", Inter Tight-only copy. This
  §2 used to describe that version. Superseded by the daylight direction above: the build
  moved to arterial red, paper, mono wayfinding and graphite numerals, and this brief was
  rewritten to match `tokens.json` and `lib.js` instead of the other way round.

## 3. Foundations — token set `ihkd`

File `design/ihkd/tokens.json`, Penpot set **`ihkd`**. This table is generated from the
live set; `tokens_sync --check` is clean.

| token | value | use |
|---|---|---|
| `ink.900` | #0E1318 | headings, primary text |
| `ink.800` | #1B232A | strong text |
| `ink.700` | #333D45 | text |
| `ink.600` | #55606A | secondary text |
| `ink.500` | #5E6A71 | meta, caption (darkened from #6E7982 for AA) |
| `ink.400` | #A3ADB5 | placeholder, ghost numerals, disabled |
| `paper` | #F2F4F5 | page background, every board |
| `white` | #FFFFFF | cards, inputs, footer / sidebar panels |
| `surface.alt` | #E8EBED | image mat, inset block, pocket cards, zebra rows |
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

Typography — Inter Tight for interface, JetBrains Mono for instruments:

| role | family | weight | size / line | tracking | use |
|---|---|---|---|---|---|
| `display` | Inter Tight | 700 | 80 / 0.98 | -2.6 | home and page hero |
| `h2` | Inter Tight | 600 | 44 / 1.06 | -1.3 | section title, congress date, ghost numeral |
| `h3` | Inter Tight | 600 | 30 / 1.2 | -0.6 | card title, article h2 |
| `lead` | Inter Tight | 400 | 22 / 1.5 | 0 | lede, article body |
| `body` | Inter Tight | 400 | 16 / 1.6 | 0 | default body, UI |
| `bodyMed` | Inter Tight | 600 | 16 / 1.5 | 0 | emphasised row title |
| `nav` | Inter Tight | 500 | 16 / 1.4 | 0 | nav, button, link |
| `label` | JetBrains Mono | 500 | 13 / 1.2 | 1.1, upper | kickers, table heads, wayfinding |
| `meta` | Inter Tight | 400 | 13 / 1.5 | 0 | helper text, captions, notes (13px minimum) |
| `data` | JetBrains Mono | 400 | 13 / 1.5 | 0.2 | time gutter, IDs, prices, legal microcopy |
| `dataLg` | JetBrains Mono | 500 | 16 / 1.4 | 0.2 | day numbers, large tabular |
| `stat` | JetBrains Mono | 500 | 44 / 1.1 | -0.6 | stat figures, countdown |
| `figure` | JetBrains Mono | 500 | 30 / 1.1 | -0.6 | small data figures (article data list) |
| `wordmark` | JetBrains Mono | 600 | 22 / 1.0 | 0.6 | masthead mark |

Size tokens `fs.13 / 16 / 22 / 30 / 44 / 80`, bound per shape by role size.
Weights by variant id (`600`, `700`, `500`, `regular`), never `fontWeight` alone.
Spacing `4 8 12 16 20 24 32 40 48 64 80 96 112 120`. Radius `0 / 2 / 4` (buttons bind
`radius.2`; photo corners are 8px by placer convention).
Grid: 1440 board, content 1200 at x=120, 12 columns of 78 with 24 gutters. Every
content x/w derives from `X`/`CW`; bleeds (bands, footers) are declared per screen.
Card: 24px padding (32 for feature cards), 1px border, no shadow.

## 4. Sitemap — 20 boards on 6 pages

| # | Page | Board | Primary action | Height |
|---|---|---|---|---|
| 01 | `Kurumsal` | `01-ana-sayfa` | Kongreye kayıt ol | 3896 |
| 02 | `Kurumsal` | `02-dernek` | Tüzüğü oku | 2452 |
| 03 | `Kurumsal` | `03-yonetim` | Kurul üyesine ulaş | 2296 |
| 04 | `Kurumsal` | `04-calisma-gruplari` | Grup seç | 2088 |
| 05 | `Kurumsal` | `05-grup-detay` | Gruba katıl | 2684 |
| 06 | `Kongre` | `06-kongre` | Kayıt ol | 3840 |
| 07 | `Kongre` | `07-program` | Programa ekle | 2716 |
| 08 | `Kongre` | `08-bildiri` | Bildiri gönder | 2568 |
| 09 | `Kongre` | `09-kayit` | Kaydı tamamla | 2000 |
| 10 | `Kongre` | `10-konaklama` | Otel seç | 2400 |
| 11 | `Akademi` | `11-akademi` | Kursa başla | 2488 |
| 12 | `Akademi` | `12-kurs-detay` | Kursa yazıl | 1740 |
| 13 | `Akademi` | `13-kilavuzlar` | Kılavuzu indir | 2400 |
| 14 | `Akademi` | `14-dergi` | Sayıyı oku | 2000 |
| 15 | `İçerik` | `15-haberler` | Haberi oku | 2080 |
| 16 | `İçerik` | `16-makale` | — (okuma) | 2540 |
| 17 | `İçerik` | `17-takvim` | Etkinliğe kaydol | 2096 |
| 18 | `Üyelik` | `18-uyelik` | Başvuruyu gönder | 2292 |
| 19 | `Üyelik` | `19-giris` | Giriş yap | 1024 |
| 20 | `Üyelik` | `20-panel` | Kursa devam et | 1680 |

`Components` holds the library sheet; `_scratch` is removed before handoff.

## 5. Per-screen spec

Copy below is final Turkish; build it verbatim.

### 01 · Ana sayfa
- Nav: İHKD + `Dernek · Çalışma grupları · Kongre · Akademi · Yayın · Haberler` + `Üye girişi` + `Üye ol`.
- Hero (paper, grid-derived 2 columns): kicker `1998'DEN BERİ · ANKARA` (ink.500), display `Hastanın hekimi.`, lede "1998'den beri iç hastalıkları hekimlerinin camiası: kılavuz, kongre, akademi tek adreste.", buttons `Kongreye kayıt ol` + `Derneği tanı`; right: image 560×384 inside the grid (no bleed, no caption) — wall-mounted 12-lead ECG monitor, nurse from behind, no face at camera.
- Congress note: white card with red ECG trace + `12. ULUSAL KONGRE` + date/venue + `Kayıt ol →`. The page's single red field is the congress band below.
- Stat row: 4 mono figures at 44px (`stat`) — 6.847 üye · 41 il · 12 çalışma grubu · 10 kılavuz — labels 13px `ink.600`.
- `Gündem` — 3 rows (date, category, title) + `Tüm haberler`.
- Congress band: red `#C4122F`, `12. ULUSAL KONGRE`, `22–25 Nisan 2027`, `Antalya`, `147` countdown, `Kayıt ol`.
- `Çalışma grupları` — 6 rows + `12 çalışma grubunun tümü →`. No `NN / 06` counters: ghost numerals already carry the order.
- `Akademi` — 3 course rows. Right-aligned meta column ends at the grid edge; single action column.
- `Yayın` — journal card (open-pages texture, no masthead) + TOC + guideline card side by side.
- Footer white.

### 02 · Dernek
Hero (white card, no photo) with `1998'den beri`, display `1998'den beri tek çatı.`, lead.
Story: 3 paragraphs + a pull quote card (accent.050). Timeline 1998 · 2004 · 2011 · 2017 · 2023 · 2027 as a vertical list with year in `data`.
`Sayılarla` 5 figures. `Misyon / Vizyon` two cards. `Belgeler` 4 rows. `Yönetim` 3 preview cards.

### 03 · Yönetim
Hero compact. `Yönetim kurulu` 7 cards (monogram, name, role, institution). `Denetim` 3 rows. `Bilim kurulu` table 12 rows (`Ad · Kurum · Alan · Grup`). `Komisyonlar` 5 chips. Note `Genel kurul: 24 Nisan 2027, Antalya`.

### 04 · Çalışma grupları
Hero + filter chips (`Tümü 12 · Görüntüleme · Girişimsel · Ritim · Metabolik · Diğer`). 12 cards in 3 columns: name, chair, members, one-line mandate, `Grubu gör →`. Bottom card: `Yeni grup önerisi` with 3 criteria.

### 05 · Grup detay
Breadcrumb. Title + chair/secretary + `Gruba katıl`. Mandate lead. `2027 çalışma planı` 4 numbered rows. `Etkinlikler` 3 rows, `Yayınlar` 3 rows, `Üyelik koşulları` 3 checks. Right sidebar card: kuruluş 2009 · üye 412 · toplantı 6/yıl · başkan.

### 06 · Kongre
Full-bleed image hero 1440×520 with a white card overlapping (date block, venue, CTA). `Neden` 3 cards. `Track'ler` 5 rows with session counts and a discipline tag. `Konuşmacılar` 4 cards. `Program önizleme` day tabs + 3 rows. `Sponsorlar` 6 wordmarks. `Ücretler` 3 rows teaser.

### 07 · Program
22 Nisan günü: 30 dakikalık 18 dilim (09:00–18:00) × 4 salon, 19 oturum. Header + day tabs (21–25 Nisan, 22 seçili). Filters: hall chips + `Konsey oturumu` legend + tek `Seçili oturumları programa ekle` (satır başı tekrar yok). Table: time gutter + 4 hall columns; every session carries `HH:MM–HH:MM` first in its meta, chairs after. Konsey sessions have two chairs + red bar, others graphite bar. Meta line: `Son güncelleme 12 Mart 2027 · 22 Nisan 19 oturum · toplam 96 oturum` (96 is the 4-day total). Note `Son güncelleme 12 Mart 2027`.

### 08 · Bildiri
Header + deadline callout (signal) `Son gönderim 15 Şubat 2027, 23:59 (TSİ)`. `Süreç` 4 steps with dates. `Konular` 8 chips. Form card: başlık, track select, yazarlar 3 rows, özet textarea with `248/300 kelime`, dosya yükleme, KVKK checkbox, `Taslak kaydet` + `Gönder`. `Kurallar` 6 bullets, `SSS` 4 rows.

### 09 · Kayıt
Header + `Erken kayıt 31 Ocak 2027`. Fee table 5 rows × 3 columns (Erken / Standart / Geç); member row tinted. `Ücrete dahil` 6 checks / `Dahil değil` 3. `Grup kaydı` card. `İptal koşulları` 3 rules.

### 10 · Konaklama
Hero + venue image. 4 hotel cards (name, distance, room type, nightly price, `Otel seç`). `Ulaşım` 3 rows. `Kongre merkezi` 4 facts + floor plan block (A–D halls). Note about booking with registration.

### 11 · Akademi
Header + search + topic chips. Featured course card (large, image, 8 modül · 6 STE · 4s 20dk, progress `%40`). 6 course cards + `Tüm kurslar →`. `Nasıl çalışır` 3 steps. STE explainer card.

### 12 · Kurs detay
Breadcrumb, title, meta row, instructor. Left: outcomes 5 items; curriculum 8 module rows (3 tamamlandı, 1 devam, 4 kilitli). Right card: image, `%40` progress, `Devam et`, includes, certificate note. `Kimler için`, `Ön koşul`, `Akreditasyon`.

### 13 · Kılavuzlar
Header + search + year chips (`Tümü 10 · 2027 3 · 2026 2 · 2025 2 · 2024 3`). Featured guideline spotlight (also listed as the 2027 Hipertansiyon row) with ECG strip + calibration. 10 rows: title, scope, `2027 · Kanıt A · 48 sayfa · 3,2 MB`, `İndir` + `Özet`. `Cep kartları` 3 small cards. Method note.

### 14 · Dergi
Header `Kardiyovasküler Klinik · Cilt 12 · Sayı 1 · Mart 2027`. Cover image card + `Sayıyı oku`. İçindekiler 6 rows (page, type, title, authors). `Editörden` card with signature. `Arşiv` 4 rows. `Yazara notlar` 3 rules.

### 15 · Haberler
Header + category chips. Featured card with image. 6 list rows (date, category, title, reading time). `Bülten` card with input + button. Pagination.
Lede: "Kongre, akademi ve dernekten haftanın duyuruları."

### 16 · Makale
Breadcrumb, category kicker, display title (3 lines), meta (author, date, 6 dk), share row. Full-bleed image 1440×420. Body: 5 paragraphs, pull quote card, data list 3 items, `Bu yazıda` TOC card on the left. Related 3 rows. Author card.

### 17 · Takvim
Header + `Ay / Liste` toggle. Month grid April 2027 (7×5), event pills. `Yaklaşan` 6 rows with `Kaydol`. Filter chips. ICS note.

### 18 · Üyelik
Header `Üyelik`, display, lead, `3 adım`. Benefits 6 items in 2 columns. Fee tiers 4 cards. Application form card: step indicator 1/3, fields (ad soyad, e-posta, telefon, kurum, unvan, il, diploma no, çalışma grubu), document checklist 3, KVKK, `Devam et`. SSS 4 rows.

### 19 · Giriş
Split 720/720: left cobalt panel with mark, quote `Hekimin evi.`, image; right form card: `Üye girişi`, e-posta/üye no, şifre, `Beni hatırla` + `Şifremi unuttum`, `Giriş yap`, divider, `e-Devlet ile giriş`, `Üye değil misiniz? Başvuru`. Invalid password state visible (`Şifre en az 8 karakter olmalı`). Note `İki adımlı doğrulama zorunludur.`

### 20 · Panel
Ink sidebar 260: member name, `İHKD-24817`, nav, `Çıkış`. Header `İyi günler, Dr. Selin Aydın` + date + `Kongreye kayıt ol`. Member card (cobalt, 520×300, QR block, dues `31.12.2027`). Aidat card. Kurslarım 2 rows with progress. Yaklaşan 3 rows. Duyurular 2. ECG card with calibration.

## 6. Photography (Pexels, graded)

Thirteen placements of twelve photographs, one cool grade (light desaturation, contrast lift, neutral shadows) so they
read as one set. Captions are 13px `meta`, sentence case, no uppercase.

| image | subject | used on |
|---|---|---|
| `img-echo` | wall-mounted 12-lead ECG monitor, nurse from behind (no face at camera) | 01 |
| `img-journal` | open book, small body-text texture, no masthead | 01 |
| `img-cath` | catheterisation laboratory | 05, 06 |
| `img-hall` | conference hall from the back | 06 |
| `img-corridor` | hospital corridor, morning light | 10 |
| `img-venue` | convention centre exterior | 10 |
| `img-seminar` | small seminar room, physicians | 11 |
| `img-desk` | stethoscope and printed ECG on a desk | 13 |
| `img-round` | internal medicine ward round | 15 |
| `img-team` | congress programme workshop | 16 |
| `img-auth` | cardiology monitor, hospital equipment | 19 |
| `img-issue` | open book, small body-text texture (same source as `img-journal`) | 14 |
| `img-lab` | blood-pressure measurement, clinical supervision | 12 |

Provenance (Pexels URL + photographer) is recorded in `README.md`.

## 7. Definition of done

1. `design_lint.py --page <page>` → 0 high.
2. `design_qa.py --page <page>` → `findings: none`, `renderMismatches: 0`, fills bound.
3. `check_contrast.py` → every pair used passes.
4. `export_board.py` → look at the render at 1:1 in four places.
5. Prototype: flows exist, per-board interaction count non-zero.
6. Independent reviewer has seen the render and crops.
