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
   and trace — never a decorative divider, and never a second red band. (M7: the home
   page no longer has a red congress band; its cover spends the red on the ECG trace
   and one primary. A red field is a choice, not a default.)

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
| `wordmark` | JetBrains Mono | 600 | 22 / 1.0 | 0.6 | masthead mark (cover masthead at 80, `fs.80` bound) |

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
| 01 | `Kurumsal` | `01-ana-sayfa` | Kongreye kayıt ol | 4064 |
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
- Nav: İHKD + `Dernek · Çalışma grupları · Kongre · Akademi · Yayın · Haberler` + `Üye girişi` + ghost `Üye ol` (tek doygun primary hero'dadır).
- Hero (seçim SAYI, M7): the page opens as the society's own issue. A 1200×740 `white` cover sheet at 120,140: masthead `İHKD` (the mono wordmark at 80, `fs.80` bound; the nav keeps wordmark 22), `KARDİYOVASKÜLER KLİNİK` label + `Cilt 12 · Sayı 1 · Mart 2027` data, coverline `Hastanın hekimi.` (h2 44); congress coverline `12. ULUSAL KONGRE` (label) + `22–25 Nisan 2027 · Antalya` (h3 30) + `147 gün · erken kayıt 31 Ocak 2027'de kapanıyor · 96 oturum` (meta). The cover figure is a self-drawn three-lead strip (I/II/III, 640×220, 8px minor / 40px major grid, `25 mm/s · 10 mm/mV`), labelled `KAPAK · EKG KAYDI`. `BU SAYIDA` TOC six rows — Kongre s.01 / Kılavuzlar s.12 / Akademi s.30 / Yayın s.38 / Topluluk s.44 / Haberler s.50 — each with a 13px note; one primary `Kongreye kayıt ol` + ghost `Derneği tanı`; imprint `6.847 üye · 41 il · 12 çalışma grubu · 10 kılavuz` (13px). No photo, no proof strip, no congress band: the cover carries the date, the countdown and the action.
- `Gündem` starts at 992 (cover bottom 880 + the 112 rhythm); the seam is the cover's own edge, not a strip. The page resumes on `paper`.
- `Gündem` — 3 rows (tarih, kategori, başlık, okuma süresi) + `Tüm haberler →` + yayım notu.
- `Çalışma grupları` — 6 rows, iki kolon (576 + 48 + 576 = 1200) + `12 çalışma grubunun tümü →`; sıra numarası `data` 13px, ok kolonun sağ kenarında ve başlığın ilk satırına hizalı.
- `Akademi` — 3 course rows; meta 1200'de biter, `Başla →` 1320 grid kenarında; STE notu.
- `Yayın` — kitap fotoğrafı (280×300) + dergi kolonu (3 TOC satırı, `Sayıyı oku`) + ayın kılavuzu kolonu (ECG şeridi 360×44, `Kılavuzu indir`); iki link aynı satırda, fotoğrafın alt kenarı o çizgiye oturur.
- `Üyelik` — `white` bant: `Yazan, toplayan, öğreten.`, lede, 3 madde, `Başvuruyu başlat →` linki, aidat satırı. İkinci doygun buton yok.
- Footer white. Board yüksekliği 4064.
- Declared bleeds: `top bar`, `masthead rule`, `uyelik band`, `footer` / `footer bar`. The cover is contained 120..1320; no hero bleed. Diğer her şey `X..X+CW` içinde (grid denetimi: 0 ihlal; cover kenar boşlukları 120/120).
- Açıklanan lint medium'ları (düzeltildi değil, gerekçeli): `type steps too close [1.23, 1.38, 1.36, 1.47, 1.82]` — 13→16 microcopy pair, the 80/44 masthead step and the 30/22 coverline step; principles §8. `dead space in uyelik band (74)` — the band's padding is symmetric 72/72, the measurement starts at the last ink. 13px microcopy (cover imprint, countdown, caption): the project's micro size. `inline mixed-size pair toc title/page` — the page number is nudged to the name's ink (+2) and read at 1:1; the flag is a review pointer, not a collision.

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

**Subject rule (2026-11-02, user-reported):** the frame must show the product's own
field — a heart/cardiology reading (auscultation, echo or cath lab, 12-lead trace, heart
model), not a generic clinical scene that only *could* happen in a hospital. A plausible
consultation still reads as stock filling; the hero's role is "the physician at the
patient's chest", not "healthcare".

| image | subject | used on |
|---|---|---|
| `img-hero` | stethoscope bell on a bare chest, hand in frame, no face, cool teal room — the heart is being heard | 01 |
| `img-journal` | open book, small body-text texture, no masthead | 01 |
| `img-angio` | catheterisation / angio suite: ECG-trace monitor, angio screen, masked team | 05 |
| `img-cath` | catheterisation laboratory | 06 |
| `img-hall` | conference hall from the back | 06 |
| `img-corridor` | hospital corridor, morning light | 10 |
| `img-venue` | convention centre exterior | 10 |
| `img-seminar` | small seminar room, physicians | 11 |
| `img-desk` | stethoscope and printed ECG on a desk | 13 |
| `img-round` | internal medicine ward round | 15 |
| `img-team` | congress programme workshop | 16 |
| `img-auth` | cardiology monitor, hospital equipment | 19 |
| `img-issue` | open book, small body-text texture (same source as `img-journal`) | 14 |
| `img-lab` | 12-lead ECG paper with limb/precordial electrodes, closeup | 12 |

Provenance (Pexels URL + photographer) is recorded in `media/provenance.json`; the pinned
URL in `tools/media.py` is the single source, so a rebuild reimports the accepted frame.

**Surface rule (2026-11-02).** Two neutral layers per screen: `paper` is the ground,
`white` is a card or content surface. `surface.alt` is an inset/secondary panel only
(05 künye, 12 progress, 10 plan). Same logical kind = same surface: 07's schedule cards are
`white`, a right-docked info panel is `surface.alt`. Counted on 2026-11-02: 05 künye
(alt), 12 progress (alt), 07 calendar cards (white) are consistent; 13 `pocket` cards and
20 `ecg card` still use `surface.alt` for cards — open, listed in the report.

## 7. Definition of done

1. `design_lint.py --page <page>` → 0 high.
2. `design_qa.py --page <page>` → `findings: none`, `renderMismatches: 0`, fills bound.
3. `check_contrast.py` → every pair used passes.
4. `export_board.py` → look at the render at 1:1 in four places.
5. Prototype: flows exist, per-board interaction count non-zero.
6. Independent reviewer has seen the render and crops.

## M6 · 01 hero — critique, three candidates, decision (2026-11-02, 1:1)

### Critique of the delivered hero (before this milestone)

Read from `shots/before/01-ana-sayfa.png` (1440×3952) plus 1:1 crops
`c1-hero-left`, `c2-hero-photo`, `c3-proof`, `c4-band`, `c5-head`, `c7-groups`,
`c8-pub` in the same folder.

1. **The hero's left column had 255px of nothing under its CTA.** kicker 156,
   title 188, lede 368, CTA 470–522, photo ends 716, strip starts 780. The title was
   an accidental 2-line wrap in a 560px box; nothing was centred against the photo, so
   the hero read as two half-pages.
2. **The proof strip broke the system.** 6.847 / 41 / 12 / 10 sat on `ink.900` at
   `dataLg` 16px with 13px labels — a near-black surface principles §6 forbids, and the
   opposite of "loud data".
3. **The band's CTA group had no row.** "Programı gör" sat at y+218, "Kayıt ol" at
   y+268 and 24px to its right: no shared centre, no fixed gap; 75px of dead band below.
4. **Three actions competed.** hero `Üye ol` (red fill), nav `Üye ol` (outline), band
   `Kayıt ol` (bone). The page's single primary was membership while its only
   time-limited action is congress registration.
5. **Ghost numerals fought their titles.** 01–04 at `h2` 44px, 148px left of the kicker,
   the same size as the 44px titles they labelled.
6. **Rows touched and drifted.** group title→meta was a 6px box gap (13px ink); the TOC
   rules sat 55px under one title and 17px above the next; the publication column left
   111px under the guideline title and the book photo's bottom aligned with nothing.

### Candidates (scratch boards, real photo, identical copy)

Renders: `shots/hero-candidates/cand-a-split.png`, `cand-b-kongre.png`,
`cand-c-veri.png` (1440×900, read at 1:1).

| axis | A "Tek hasta, iki uzman" | B "Kongre lead" | C "Klinik veri" |
|---|---|---|---|
| mechanism | message column centred against a 560×560 cardiology frame; proof strip docked to the photo's bottom edge | date/venue at 80px display, countdown, registration as the only action; no photo | typographic hero + 360px ECG strip + 44px figures; no photo |
| refuses | putting the congress in the hero (the primary is registration, the headline stays the society's) | naming the society in the first sentence | carrying feeling with photography |
| visual role | PROVES — the stethoscope on the chest shows "the patient's physician", no face, cool room | — | — (the ECG is the signature graphic) |
| hierarchy | 5 | 5 | 3 |
| story | 5 | 2 | 3 |
| first-5-seconds | 5 | 4 | 3 |
| fit | 5 | 4 | 4 |
| consistency | 5 | 3 | 4 |
| accessibility | 5 | 4 | 4 |
| **total** | **30** | 22 | 21 |

**A** wins: hook + proof + action in one viewport, the society speaks before the
congress, and the photo's role is stated. **B** rejected: no society identity; the
countdown's number and meta were hand-aligned at different sizes (visible 6px baseline
drift) and the lower 200px were empty. **C** rejected: an ECG alone does not say what
the product is; the job is unclear in the first five seconds and the lede arrived after
the figures.

### Decision (written, built)

1. **Hero = A.** Left column 560px, its block centred inside the 560×560 photo frame
   (x760); the title is a deliberate 2-line lockup (`Hastanın` / `hekimi.`); the CTA
   group is one row.
2. **The proof strip is neutral.** The black band is gone: a full-width `white` strip
   under a 1px `line.soft` rule, 44px `stat` figures in `ink.900`, 13px labels in
   `ink.600` (AA 6.43), dividers on the 3-column cell boundaries, own rhythm
   (28/48/10/20/28 = 134). Reason: principles §6 — a near-black surface is outside the
   system, and "quiet interface, loud data" was the point of the strip all along.
3. **One primary: congress registration.** hero `Kongreye kayıt ol` (red.600) + ghost
   `Derneği tanı`; nav keeps the outline `Üye ol` (a ghost, not a fill); the band's
   button is bone (`onred`); the page closes on a `Başvuruyu başlat →` link. Saturated
   fills on the board: 1.
4. **The band's CTA group is one row.** `ctaRow()` draws the button and its ghost link
   at one vertical centre with a fixed 32px gap; the band's height derives from its
   content (316).
5. **Ghost numerals were reduced, not removed.** 01–04 are now `figure` 30px mono in
   `ink.400`, on the kicker's line (baseline-aligned) with the section title starting on
   the page's left edge. Reason: at 44px sans they competed with 44px titles; deleting
   them would delete the product's spine (principles §5). New helper `headIndex()` is
   the home page's section grammar; inner pages keep `head()` (the shared helper was not
   touched).
6. **Row joints fixed from the block's own edge.** group title→meta 12px (≈20px ink),
   row height from content (112); TOC rows through `rows()` so each rule lands on a
   block's bottom edge; the two publication links share one line (y+282) and the book
   photo's bottom edge sits on it.
7. **Story spread.** hook (the cover) → proof (the ECG figure + the imprint) → path
   (`Bu sayıda`) → action (the cover's one primary).

## M7 · 01 hero — concept-first reset (2026-11-02, 1:1)

**M6 note (later the same day).** The photo-led hero was withdrawn. A patient/exam
image is not the society's visual language even when it is well cropped; the hero's
visual must be an artifact a physician recognizes (ECG strip, guideline figure,
anatomy plate, algorithm, cover) or the community gathered. The rule is written in
`principles.md` §10. This milestone also fixes the process: the previous round
produced three layouts of one hero, not three ideas. A candidate is now an object
(`ux-design-process` §3, "Concept before composition").

### Why the delivered hero was rejected (read at 1:1 from `shots/01-ana-sayfa.png`)

1. **The proof strip is a glued shelf.** `img-hero`'s bottom edge is the strip's top
   rule: a 560px photo ends on a full-bleed `white` surface with no gap and no shared
   line (`img-hero touches hero proof surface`, 0px). At 1:1 the photo looks cut by a
   shelf, not ended.
2. **Four planes in the first screen.** paper (156–716) → white strip (716–850) →
   107px paper → red band (962–1278). The strip is a section between the hero and the
   page, not the hero's evidence; that is the "dikiş" the user read.
3. **The strip outranks the message.** Four 44px figures on a 134px white band are
   the second-loudest element in the viewport; proof becomes a destination instead of
   evidence under the promise.
4. **The left block is four pieces, not a column.** Kicker ink→title 22px, title→lede
   49px, lede→CTA 37px; the CTA ends at 644 while the photo ends at 716 (72px), and
   the title's second line leaves 128px of its 560 box empty.
5. **The photo carries no place or scale.** A stethoscope bell on skin is the heart
   being heard, but the frame says nothing about Ankara, 6.847 colleagues, a congress
   or a guideline; at 560px it is a skin-coloured texture, and the system's
   paper/white/red never enters the image.
6. **The hero and the congress are two worlds.** The primary is registration, but the
   date/venue arrive 318px later in a separate red field after 112px of empty paper.
7. **No authored object.** Text-left / image-right is the same scaffold as 04, 06 and
   10; the hero has no full-bleed moment and no object of its own (principles §3.3).
8. **The visual language is wrong, not just the crop.** A patient/exam image cannot
   carry a scientific society's opening; see principles §10.

### Visual language (new, principles §10)

No patient, exam, chest, hand or stethoscope. The visual is a domain artifact: a
12-lead strip, a guideline figure (forest plot / evidence table), an anatomy plate, a
clinical algorithm, a journal cover or a congress programme. Draw it ourselves as
vector; a photo only as a place (hall, venue) or a publication object, never a stock
smile. Figures are measured: grid, lead labels, units, evidence grades, page counts.

### Concept candidates (objects, not layouts)

Renders: `shots/hero-candidates-3/` (`cand-sayi`, `cand-afis`, `cand-algoritma`,
`cand-levha`), each 1440 wide, read at 1:1 and shrunk to 200px side by side with the
shipped hero. No candidate shares a photo, a proof block, a band or a left
headline+lede+CTA arrangement.

| object | "this page is a …" | mechanism | refuses | visual role | H | S | 5s | F | C | A | D | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **SAYI** | the society's own issue | 1200×740 cover: masthead, issue, coverlines, a self-drawn 3-lead plate, `Bu sayıda` contents, imprint | making the congress the hero; a photo | PROVES the work through the instrument + publication | 4 | 5 | 4 | 4 | 5 | 5 | 5 | **32** |
| AFİŞ | a congress poster | full-bleed red, 520px `12`, a white trace across, date + one bone CTA | naming the society first | SETS the date; the trace is the science | 5 | 3 | 5 | 4 | 4 | 4 | 5 | **30** |
| ALGORİTMA | a clinical decision chart | start `Dispne · EF %35` → `EF ≤ %40?` → group / guideline / course → `Kılavuzu aç` | the hero as a picture | SHOWS the society as the path after the decision | 4 | 3 | 3 | 4 | 4 | 4 | 5 | **27** |
| LEVHA | an anatomy plate | schematic 4-chamber heart, 12 numbered leaders = 12 groups, legend `Levha I` | the web-hero grammar | SHOWS the field | 3 | 4 | 4 | 3 | 4 | 4 | 5 | **27** |

H hierarchy · S story · 5s first-5-seconds · F fit · C consistency · A accessibility ·
D distinguishability. Scores are the maker's; the independent review is a separate gate.

**Thumbnail test (200px, side by side with A).** All four are unmistakable: a white
cover with a masthead, a red poster with a `12`, a light flowchart, a plate with a
heart. None repeats A's photo+strip or another candidate's object. No elimination.

### Decision

**SAYI.** The site becomes the society's own publication: the issue (`Cilt 12 ·
Sayı 1 · Mart 2027`), the cover figure (the instrument), the contents (the site's six
paths with page numbers) and the imprint (the four figures). It keeps the M6 story
order — the society speaks before the congress — while the congress is a coverline
and the one primary, not a band. It is the most distinguishable cover at 200px, and
it needs no photo: the plate is vector, so a rebuild has nothing to re-import.

Rejected:

- **AFİŞ** is the most immediate at a glance, but it makes the congress the hero and
  the society a 13px line — the inversion M6 rejected. Its 520px numeral sits outside
  the fs scale (a declaration every future edit would carry). Keep it as a campaign
  layout for 06, not the home hero.
- **ALGORİTMA** is the most insider idea, but its terminal action is `Kılavuzu aç`,
  which changes the page's task; the `Hayır` branch ending at `Kongre 2027` is not a
  clinical path, and the chart leaves the lower half of the viewport empty.
- **LEVHA** is the strongest metaphor for "12 groups on one heart", but the drawn
  heart reads as a schematic valentine, not a Nether/Gray plate; the numbers scatter
  and the legend carries the page. It needs an illustration pass before it can claim
  `Levha I`.

### As-built

The cover sheet is 120..1320 × 740 (120/120 margins); the page resumes at 992 after
the 112 rhythm; board height 4064. There is no `kongre band` and no `hero proof`
strip: the date, venue, countdown, registration and the four figures live in the
cover. The masthead is the mono wordmark at 80, so the cover carries the same mark
as the navigation; the candidate's plate label `12 DERİVASYON`/V1 was corrected in
the build to a limb-lead record (I/II/III, `KAPAK · EKG KAYDI`). The page's only red is the primary + the ECG trace (data). Lint 0 high;
`design_qa` and `copy_lint` clean; `ux_gate` passes the 01 items and reports only the
mobile/state boards owned by a later milestone. Tiles + regions attested.

### Image inventory (other screens — changes deferred)

| screen | image | what it shows | fits the new rule? | recommended replacement |
|---|---|---|---|---|
| 01 | `img-hero` (39192342) | stethoscope bell on a bare chest, hand | **no** — patient/exam | removed; the cover plate is vector |
| 05 | `img-angio` (39459346) | cath lab team at a monitor, masked | **no** — procedure/clinical scene | a self-drawn coronary map or an equipment detail with no people |
| 06 | `img-cath` (28583897) | two clinicians at a cath monitor | **no** — clinical scene | a congress hall/poster session, or a cath-lab equipment plate |
| 12 | `img-lab` (28585011) | 12-lead ECG paper + electrodes | **yes** — scientific object, no patient | keep; may be redrawn as the 12-lead plate |
| 13 | `img-desk` (35044388) | stethoscope + ECG electrodes on a card | **borderline** — stethoscope as an object | an ECG-only detail or a guideline figure |
| 15 | `img-round` (6129043) | ward round, doctors at a patient | **no** — patient/exam | a poster session or a newsroom/committee scene |
| 16 | `img-team` (20370745) | doctor reviewing an image with a patient | **no** — patient | a journal spread or a speakers' panel |
| 19 | `img-auth` (8460227) | masked patient with a monitor | **no** — patient | a monitor/ECG detail with no patient, or the member card |

Changes are a separate round; this milestone only records the inventory.

### Hero visual contract (mobile twin)

**Visual type:** our own vector three-lead ECG strip (I/II/III, grid 8px minor / 40px
major, `25 mm/s · 10 mm/mV`); **aspect:** 640×220 (2.91:1); **source:** the build
(`screen-01.js` local `coverGrid`/`coverTrace`), no photo, no Pexels. Mobile twin:
390×150, the same drawing under the coverline, one primary.

### Open items

- `tools/media.py` still pins `img-hero` (39192342) in its table; `build.py --restore`
  uses provenance, so the rebuild is correct, but a future `media.py --all` would try
  to place a photo that no longer has a slot. The media owner should drop that entry.
- The `Bu sayıda` rows are content, not wired interactions; the masthead is the
  navigation. A later prototype pass may link the contents paths.
- The mobile twin and the empty/loading state boards are the later milestone's work.
