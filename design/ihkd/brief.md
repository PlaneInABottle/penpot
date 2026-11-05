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
| 01 | `Kurumsal` | `01-ana-sayfa` | Kongreye kayıt ol | 4084 |
| 02 | `Kurumsal` | `02-dernek` | Tüzüğü oku | 2452 |
| 03 | `Kurumsal` | `03-yonetim` | Kurul üyesine ulaş | 2296 |
| 04 | `Kurumsal` | `04-calisma-gruplari` | Grup seç | 2088 |
| 05 | `Kurumsal` | `05-grup-detay` | Gruba katıl | 2512 |
| 06 | `Kongre` | `06-kongre` | Kayıt ol | 3840 |
| 07 | `Kongre` | `07-program` | Programa ekle | 2856 |
| 08 | `Kongre` | `08-bildiri` | Bildiri gönder | 2632 |
| 09 | `Kongre` | `09-kayit` | Kaydı tamamla | 1968 |
| 10 | `Kongre` | `10-konaklama` | Otel seç | 2400 |
| 11 | `Akademi` | `11-akademi` | Kursa başla | 2488 |
| 12 | `Akademi` | `12-kurs-detay` | Kursa yazıl | 1736 |
| 13 | `Akademi` | `13-kilavuzlar` | Kılavuzu indir | 2400 |
| 14 | `Akademi` | `14-dergi` | Sayıyı oku | 2000 |
| 15 | `İçerik` | `15-haberler` | Haberi oku | 2080 |
| 16 | `İçerik` | `16-makale` | — (okuma) | 2416 |
| 17 | `İçerik` | `17-takvim` | Etkinliğe kaydol | 2096 |
| 18 | `Üyelik` | `18-uyelik` | Başvuruyu gönder | 2292 |
| 19 | `Üyelik` | `19-giris` | Giriş yap | 1024 |
| 20 | `Üyelik` | `20-panel` | Kursa devam et | 1680 |

Heights are the live board sizes, re-verified 2026-11-03; 01 was re-measured 2026-11-05
after M11 (4084). `README.md` tables the same 4084.

States and the library are first-class boards now:

| board | page | action | size |
|---|---|---|---|
| `01-bos` | `Kurumsal` | empty gündem (one link, no saturated button) | 1440×592 |
| `07-program-loading` | `Kongre` | skeleton grid, day tabs ready | 1440×1300 |
| `09-kayit-hata` | `Kongre` | error summary + two invalid fields | 1440×1104 |
| `component sheet` | `Components` | 30 library components (9 families) | 1440×2460 |

`_scratch` holds the hero candidates: three kept at the user's request (cand-1 the live
hero's source, cand-3/cand-5 presented-not-chosen) and the two parked concepts (§ Parked
concepts). Nothing there is deleted without the user's word.

## 5. Per-screen spec

Copy below is final Turkish; build it verbatim.

### 01 · Ana sayfa
- Nav: İHKD + `Dernek · Çalışma grupları · Kongre · Akademi · Yayın · Haberler` + `Üye girişi` + ghost `Üye ol` (tek doygun primary hero'dadır).
- Hero (seçim AFİŞ, M8; kullanıcı seçti): the page opens as a congress poster over a full hall, and the poster **is** the first viewport: `hero scene` board 1440×816 at y 84 (84..900), fill `ink.900`, with a full-bleed `img-hero` rect (Pexels 20733081, cool grade) filling the same box. The masthead draws no bottom rule (`S.masthead(..., { rule: false })`), so there is no paper band above the poster, and the poster's bottom edge is the fold: no paper band below it either. White type on it: `12. ULUSAL İÇ HASTALIKLARI VE KARDİYOLOJİ KONGRESİ` (label), `22–25 Nisan 2027` (display 80), `Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı` (body), `147` (stat 44) + `gün kaldı · erken kayıt 31 Ocak 2027'de kapanıyor` (meta), one primary `Kongreye kayıt ol` + ghost `Programı gör`; the edition numeral `12` is a vector path (469×384 at 904, Inter Tight 700 outlines) and a white 1440×30 ECG trace crosses the audience edge to edge (0..1440). The society signs the poster: `Hastanın hekimi.` (h3 30) above the trace and `İHKD · İç Hastalıkları ve Kardiyoloji Derneği · 1998'den beri Ankara` (label) as the imprint below it. The foot is anchored to the poster's bottom edge (society at H−248, trace at H−128, imprint at H−44), so the copy rides a taller poster. No scrim, no gradient.
- Afiş altındaki 4 hücreli proof şeridi kaldırıldı (M10): `12` §01'in kendi başlığında, `10` §03'te, `6.847` ve `41` Dernek sayfasında zaten yazılı. Kanıt afişin kendi rakamlarında (96 oturum, 214 konuşmacı, 147 gün) ve Dernek sayfasında kalır; bölüm başlığı afişin altından standart 112 ritmiyle başlar.
- `Çalışma grupları` — 6 rows, iki kolon (576 + 48 + 576 = 1200) + `12 çalışma grubunun tümü →`; sıra numarası `data` 13px, ok kolonun sağ kenarında ve başlığın ilk satırına hizalı.
- `Akademi` — 3 course rows; meta 1200'de biter, `Başla →` 1320 grid kenarında; STE notu.
- `Yayın` — kitap fotoğrafı (280×300) + dergi kolonu (3 TOC satırı, `Sayıyı oku`) + ayın kılavuzu kolonu (ECG şeridi 360×44, `Kılavuzu indir`); iki link aynı satırda, fotoğrafın alt kenarı o çizgiye oturur.
- `Gündem` — **Yayın'dan sonra** (`Bu hafta`): 3 rows (tarih, kategori, başlık, okuma süresi) + `Tüm haberler →` + yayım notu. Kongre satırı tektir; hero'nun duyurusunu dev bir bantla tekrarlamaz.
- `Üyelik` — `white` bant: `Yazan, toplayan, öğreten.`, lede, 3 madde, `Başvuruyu başlat →` linki, aidat satırı. İkinci doygun buton yok.
- Footer white. Board yüksekliği 4084.
- Declared bleeds: `top bar`, `hero scene` / `img-hero` (1440 wide, the poster edge — the masthead draws no rule on this screen, M11), `hero ecg` (1440 wide trace), `uyelik band`, `footer` / `footer bar`, `hero twelve` (its right edge ends on 1296, inside the poster). Diğer her şey `X..X+CW` içinde (grid denetimi: 0 ihlal).
- Açıklanan lint medium/low'ları (düzeltildi değil, gerekçeli): `type steps too close [1.23, 1.38, 1.36, 1.47, 1.82]` — 13→16 microcopy pair and the display steps; principles §6. `type.small_body` ×6 at 13px (`hero label`, `hero countdown note`, `hero society line`, `member fee`, `akademi note`, footer microcopy) — these are the project's `label`/`meta` micro role, not body copy (13px minimum, brief §3). `dead space in uyelik band` — the band's padding is symmetric 72/72. The ghost section numerals are `ink.400` (2.07:1 on paper): a decorative-structural numeral, principles §3.7 "felt, not read", on every board of the set.
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

Fourteen placements of eleven photographs across eight boards, one cool grade (light
desaturation, contrast lift, neutral shadows) so they read as one set. Captions are 13px `meta`, sentence case, no
uppercase.

**Subject rule (2026-11-02, amended by M7).** A photo may show the society's *place* (hall,
venue, poster session) or a *publication object* (book, journal, ECG paper). It may not show
a patient, an examination, a chest, a hand or a stethoscope: that image is not this
society's visual language (principles §3.8). A generic "healthcare" scene that only *could*
happen in a hospital is stock filling, not evidence.

| image | subject | used on |
|---|---|---|
| `img-hero` | auditorium seen from the audience, speaker at the left, cool grade — the congress hall as a place (Pexels 20733081) | 01 |
| `img-journal` | open book, small body-text texture, no masthead | 01 |
| `img-angio` | catheterisation / angio suite: ECG-trace monitor, angio screen, masked team | 05 |
| `img-cath` | catheterisation laboratory | 06 |
| `img-hall` | conference hall from the back | 06 |
| `img-corridor` | hospital corridor, morning light | 10 |
| `img-venue` | convention centre exterior | 10 |
| `img-seminar` | small seminar room, physicians | 11 |
| `img-desk` | ECG print close-up: three traces on ECG paper, no patient (Pexels 415779, same source as `img-auth`) | 13 |
| `img-round` | internal medicine ward round | 15 |
| `img-team` | open journal spread, no masthead (same source as `img-journal`/`img-issue`) | 16 |
| `img-auth` | cardiology monitor, hospital equipment | 19 |
| `img-issue` | open book, small body-text texture (same source as `img-journal`) | 14 |
| `img-lab` | 12-lead ECG paper with limb/precordial electrodes, closeup | 12 |

Subject audit (2026-11-03, contact sheet of every image that could violate the rule): the
masked-patient frame on 19, the stethoscope-on-ECG still on 13 and the physician-with-patient
frame on 16 were replaced with already-sourced instrument/publication assets (`img-auth` and
`img-desk` → Pexels 415779, `img-team` → Pexels 3860983); their captions were corrected to
match the frame. The other two inspected frames are compliant: `img-round` is a physician
writing at a chart with no patient, and `img-angio` is cath-lab equipment (monitors, injector)
with a masked team only at the frame's edge — no patient. `img-hero` (auditorium), `img-journal`
and `img-lab` already followed the amended rule.

Provenance (Pexels URL + photographer) is recorded in `media/provenance.json`; the pinned
URL in `tools/media.py` is the single source, so a rebuild reimports the accepted frame.

**Surface rule.** Two neutral layers per screen: `paper` is the ground, `white` is a card
or content surface; `surface.alt` is an inset/secondary panel only (05 künye, 12 progress,
10 plan, 07 skeleton blocks, disabled states). Same logical kind = same surface: 07's
schedule cards are `white`, a right-docked info panel is `surface.alt`. 13 `pocket` cards
and 20 `ecg card` were moved to `white` + hairline in the 2026-11-02 triage. The two hex
values are also declared in `craft-rules.json` (`surface_white`, `surface_alt`) for the
tool-side surface audit.

## 7. Definition of done

1. `design_lint.py --page <page>` → 0 high.
2. `design_qa.py --page <page>` → `findings: none`, `renderMismatches: 0`, fills bound.
3. `check_contrast.py` → every pair used passes.
4. `export_board.py` → look at the render at 1:1 in four places.
5. Prototype: flows exist, per-board interaction count non-zero.
6. Independent reviewer has seen the render and crops.

## Hero history (M6–M7, superseded by M8)

The home hero was rebuilt three times before the poster was chosen. What survives from
those rounds is the rule, not the narrative:

1. **A candidate is an object, not a layout.** A hero is named "this page is a ___" (a
   poster, a journal cover, a plate, a chart, a map) and drawn as that object; three
   compositions of one idea are one candidate (`ux-design-process` §3).
2. **No patient, exam or stethoscope.** The hero's visual is an artifact a physician
   recognises (12-lead strip, guideline figure, anatomy plate, algorithm, cover) or the
   community gathered. A patient/exam image is not this society's visual language, however
   well cropped (principles §3.8). `img-echo` and the stethoscope hero are gone with their
   slots; the surviving images were re-inventoried in §6.
3. **Hero images from the withdrawn rounds** (kept only as the record of why): stethoscope
   bell on skin (rejected: patient/exam), a 3-lead plate cover (M7's choice, superseded),
   red postcard with a white trace (rejected: a second red field). Their renders are in
   `shots/hero-candidates-2/` and `shots/hero-candidates-3/`; nothing is rebuilt from them.

## M8 · 01 hero — five objects, the user chose the poster (2026-11-03)

**Round.** `ux-design-process` §3: five finished 1440×900 first viewports on `_scratch`
(`cand-1-afis` … `cand-5-algoritma`), renders in `shots/hero-candidates-4/` with sources
and risks in that folder's `README.md`. They share no part: a hall poster, a journal
cover, an anatomy plate, a community map, a decision chart.

**Decision — the user's (2026-11-03).** The hero is **cand-1-afis, "Kongre afişi"**: a
congress poster pasted over a full auditorium. The user chose it (their words: "ilki iyi
duruyor") and it is applied to the live `01-ana-sayfa`. Reason: **the user chose it** — a
taste-bearing surface is decided by the user (`ux-design-process` §3), not by the maker's
score, and the M7 decision (SAYI) is superseded.

Presented, not chosen (boards stay on `_scratch`, renders stay, no parked script) — one
line each:

- **cand-3-levha (anatomy plate)** — a 1918 Gray's engraving; presented, not chosen.
- **cand-5-algoritma (clinical decision chart)** — the guideline path as the page; its
  terminal action is `Kılavuzu aç`, not registration; presented, not chosen.

**cand-2-kapak** and **cand-4-topluluk** are kept as *parked* concepts: see § Parked
concepts.

### Hero visual contract (as applied)

- **Photo:** Pexels **20733081** (BBSO) — a large auditorium seen from the audience, the
  speaker at the left, cool grade. Pinned in `tools/media.py` (`img-hero`) and recorded in
  `media/provenance.json`; the slot `img-hero` is a full-bleed 1440×816 rect inside the
  `hero scene` board, so `build.py --restore` re-places, re-crops and verifies it on every
  rebuild.
- **Surface:** `hero scene` is a board with an `ink.900` fill and the type sits on that
  board; the photo is the board's sibling rect. No gradient, no scrim rectangle.
- **First viewport (M11).** The poster occupies 84..900: straight under the 84px masthead,
  whose bottom rule is off on this screen (`rule: false`), and ending on the 900px fold.
  There is no paper band above or below it; the fold is the poster's bottom edge.
- **Type on the photo:** white (`on.ink`) — `12. ULUSAL İÇ HASTALIKLARI VE KARDİYOLOJİ
  KONGRESİ` (label 13), `22–25 Nisan 2027` (display 80), `Antalya Kongre Merkezi, Belek ·
  96 oturum · 214 konuşmacı` (body 16), `147` (stat 44) + `gün kaldı · erken kayıt 31
  Ocak 2027'de kapanıyor` (meta 13), `Hastanın hekimi.` (h3 30) + `İHKD · İç Hastalıkları
  ve Kardiyoloji Derneği · 1998'den beri Ankara` (label 13).
- **`12`:** a **vector path** (Inter Tight 700, 520px, tracking −16, baked into
  `screen-01.js`), 469×384, ink at 808,120 inside the poster. It is a path, not a text
  node: at 520px a text node would be the board's seventh type size (`design_lint`
  `type.sizes`, max 6), and the numeral is a poster layer, not copy.
- **White ECG trace:** the project's `S.ecg` instrument, 1440×30 at the poster's lower
  third, stroke `on.ink` — data, not a divider. It spans the full board width (`x 0..1440`;
  before M11 the 10th cycle's 0.18 length left the trace ending at 1321).
- **Actions:** one saturated primary `Kongreye kayıt ol` (`red.600`) + ghost `Programı
  gör` (white text, white underline). No other red field on the page.
- **Proof is the poster itself:** the 4-cell stat strip under the poster was removed (M10).
  `12` repeated §01's own title `On iki grup, on iki soru`, `10` is implied by §03, and
  `6.847` with `41` are already stated on the Dernek page. The poster's own figures — 96
  oturum, 214 konuşmacı, 147 gün — are the proof; §01 starts 112 below the poster's edge.
- **Society identity stays in the first viewport** as a secondary line: `Hastanın hekimi.`
  at 30px plus the association's name at 13px, bottom-left of the poster. The congress is
  the poster's message, the society is its signature; the date is not contested.

### As-built (2026-11-03, re-measured 2026-11-05 after M11, 1:1)

Poster 84..900 (`hero scene` 1440×816 at y 84, `img-hero` full bleed), Çalışma grupları head
1012, Akademi 1668, Yayın 2224, Gündem 2816, news title 0 at 2988, Üyelik band 3372..3708
(h 336), footer bar 3764; board **4084**. The `12` is 392×321 at 904 — its ink right edge 1296
keeps the candidate's 144px margin, and the numeral kept its size and its `HERO_Y`-relative
offset when the poster grew, so it now sits in the poster's upper half (M11) instead of
carrying the candidate's 48% share of a 668px height. ECG trace 772..802, brand line 652..689,
imprint 855..873 — all inside the poster, the imprint 27px clear of the fold.

White type was measured against the pixels actually behind each ink box (the graded photo
cache at the poster's M11 1440×816 crop), not against `ink.900`: p95-background contrast is
**19.68:1** countdown, **11.49:1** date, **9.63:1** label, **18.66:1** countdown note,
**18.43:1** ghost link, **8.76:1** primary label, **8.38:1** brand line (large text),
**5.56:1** imprint and **4.92:1** venue — the 16px `body` venue line is now the tightest
(3.6% of its box dips below 4.5:1); its old 18.7:1 belonged to the 668px crop, and the taller
crop puts it over brighter audience pixels. AA still holds at the p95 measure with no scrim;
the venue line is the one to watch if the crop moves again. Paper pairs: `ink.900` 16.92,
`ink.600` 5.83, `ink.500` 5.04, `red.700` 8.42, `on.red` 6.04.

Two fixes this milestone made, both rebuild-safe:

1. **`media.py` PLACE now inserts a photo at its slot's stack index.** Appending it last put
   the hero photo over its own white type (the first build rendered an empty poster). A photo
   replaces its slot where the slot sat; every board's slots keep their place.
2. **The numeral is a vector path, and its group is resized after import.** `createShapeFromSvg`
   sizes a group from the viewBox, not from the svg's width/height, so the first build ignored
   the scale; `posterNumeral` resizes the group. It is a path, not a text node, because at
   520px a text node would be the board's seventh type size (`type.sizes`, max 6).

Prototype: 01's same-page interaction is now `groups all` → `04-calisma-gruplari` (the hero
ghost `Programı gör` and the primary `Kongreye kayıt ol` both leave the Kurumsal page, and
cross-page navigation stays unwired by design). `flows.js` carries the change.

Verified: `build.py screen-01` → `RESULT ok nulls=0`, `photos 2/2` (`img-hero`,
`img-journal`), `links 1/1`, layout quiet after 3 fit passes; `design_lint` 0 high;
`design_qa` `findings: none`, fills 742/742, text sizes 577/577; `copy_lint` clean;
`ux_gate` reports only the two state boards owned by a later round (`01-bos`,
`07-program-loading`). Tiles + regions attested in `shots/01-ana-sayfa/manifest.json`
(5 tiles, 11 regions, the hero CTA among them); the crop tool's own heuristic still picks
the nav CTA as "primary-action", so the hero primary is covered by an explicit
`region-hero-cta.png` crop.

## Parked concepts

Two of the five M8 candidates are kept as parked objects. Their boards stay on `_scratch`
and each has a build script; neither is the live hero.

**What is proven, and what is not.** The two scripts are *reconstructions*: each was
generated from a read-only structure dump of its live board (names, geometry, type, fills)
and has been validated statically only — `node --check`, plus one run of its data walk
against a stub plugin API (41 and 39 children, the right photo slots). They have **not**
been executed against Penpot, so idempotency (reuse board → clear children → redraw) is a
property of the code, not a runtime observation. The PNGs in `shots/hero-candidates-4/` were
produced by the original candidate round, **not** by these scripts.

| concept | "this page is a …" | when to use it | build script | render |
|---|---|---|---|---|
| Dergi kapağı (`cand-2-kapak`) | a journal cover | the home page after the congress, or the opening of the publication (`Yayın`) area | `design/ihkd/build/parked/cand-2-kapak.js` | `shots/hero-candidates-4/cand-2-kapak.png` |
| Topluluk haritası (`cand-4-topluluk`) | the society's community map | the opening of `Dernek` / `Üyelik`, or when the story is "tek çatı" instead of the next congress | `design/ihkd/build/parked/cand-4-topluluk.js` | `shots/hero-candidates-4/cand-4-topluluk.png` |

Run either with `python3 scripts/penpot_exec.py --file
design/ihkd/build/parked/<file>.js`: it reuses the board on `_scratch`, clears its children
and rebuilds them. A first run may only switch the page (Penpot switches asynchronously) —
run it once more. Photos are not embedded: `python3 design/ihkd/tools/media.py --restore
--board cand-2-kapak --page _scratch` (or `--board cand-4-topluluk`) places the pinned
sources recorded in `media/provenance.json`.

Sources: kapak — Pexels **415779** (Pixabay), an ECG print close-up, no patient, no hand;
topluluk — Pexels **12319354** (poster session, Roxanne Minnish), **15325468** (audience,
Luis Quintero), **35138560** (convention hall, Tahir Xələfquliyev), and the Turkey outline
from **Natural Earth 110m admin-0** (public domain) with 41 dots and one Ankara marker (a
field inside the outline, not exact province positions).

`_scratch` aday board'ları ve `shots/hero-candidates-4/` render'ları kullanıcı isteğiyle
tutulur; kullanıcı aksini söyleyene kadar silinmez.

## M9 · Completion round — states, library, two design defects (2026-11-03)

- **Components (30).** `screen-components.js` builds the `component sheet` (9 families ×
  state variants). Naming is `aile-durum` (`button-primary-focus`), not `aile/durum`: Penpot
  treats `/` in a shape or component name as a path separator and rewrote `button/primary`
  to `button / primary`, so the first run created 15 of 30 components and the mismatch was
  silent. The script now drops its own normalised leftovers, names families with a dash, and
  clears non-board children so a second run doubles nothing.
- **States.** `01-bos`, `07-program-loading`, `09-kayit-hata` are built and referenced by
  the spec; `ux_gate` over the whole spec exits 0. `09-kayit` entered the spec with the error
  state, and its masthead CTA became a ghost so the form's `Kaydı tamamla` is the board's one
  saturated primary (the gate counts saturated CTAs; there were two).
- **07-program cards.** `lib.fitCards` now re-settles a card's meta on the title's measured
  ink before sizing the card — the estimate model cannot tell where a title wraps. `sess
  card 2` and `8`: 128px / 40px joint → 104px / 16px, matching the row's cards; the accent
  bar keeps its padding.
- **08-bildiri FAQ.** The four answers are 16px `body` (were 13px `meta`), row pitch 60 → 72,
  board 2568 → 2632; the footer docks to the last rule.
- **19/20 contrast.** Four 13px labels carried a shape opacity that failed AA on `red.600`
  (`al sub` and `al foot` .72 → 3.66:1, `al caption` .80 → 4.25:1, `mc label` .72). They are
  opaque `on.red` now (6.04:1, pixel-verified). The intentional .88/.85 secondary lines stay:
  measured 4.88 / 4.64:1 on the render.
- **Surface tokens.** `craft-rules.json` gains `surface_white` / `surface_alt` (values read
  from `tokens.json`) for the tool-side surface audit.
- **One saturated primary per board, enforced on the nav too.** 08-bildiri's masthead CTA is
  a ghost now, like 09's: the form's `Gönder` (and 09's `Kaydı tamamla`) is the board's action,
  so the nav must not compete with it.
- **Photo compliance finished.** `img-auth` (19), `img-desk` (13) and `img-team` (16) were
  replaced with already-sourced instrument/publication frames (Pexels 415779 and 3860983) and
  their captions corrected to the frame; a contact sheet of the remaining candidates shows
  `img-round` and `img-angio` compliant (no patient, no stethoscope). Brief §6 carries the
  audit.
- **Surface palette is a list, and the lint enforces it.** `surface_white`/`surface_alt` were
  scalars, so `surface.role` read them character by character and reported nothing for a whole
  milestone; they are one-element arrays now, `design_lint.py` exits 2 on a non-list or
  non-string entry at the rules-loading boundary, and a fixture test proves the shipped config
  activates the rule (1 medium) instead of silently skipping it.
- **Evidence plan.** `tools/crop-plan.json` + `tools/crop_plan.py` re-cut every board's 1:1
  evidence from an existing render plus a node dump, with the real primary action named per
  board; the coordinator re-runs one command after a tool change.
- **Verification limits.** Crop tiles are real and attested, but contrast on photographs is
  measured against the pixels behind each ink box (never token pairs alone), and the
  `contrast_audit.py` shipped this round mis-reads an unset shape opacity (`Number(null) → 0`),
  so the audit above ran from a patched copy — the repository tool needs that null guard.

## M10 · Hero proof strip removed (2026-11-05)

- **The strip is gone.** The 4-cell stat strip under the poster (`6.847` Üye · `41` İl
  temsilcisi · `12` Çalışma grubu · `10` Kılavuz) is removed; `screen-01.js` now goes straight
  to `let y = HERO_Y + HERO_H;`, so §01's head follows on the standard 112 rhythm and the
  112px dead band the bar left between poster and §01 is gone. Board 3960; §01 head 888,
  Akademi 1544, Yayın 2100, Gündem 2692, Üyelik band 3248..3584, footer bar 3640.
- **Duplication, not shortage.** `12` repeated §01's own title `On iki grup, on iki soru`, `10`
  is implied by §03, and `6.847` with `41` are stated on the Dernek page. The poster's own
  figures (`96 oturum · 214 konuşmacı · 147 gün`) remain the home page's proof.
- **Hosted `fontVariantId`.** `lib.js` `ROLE.data`'s `fontVariantId` changed `"400"` → `"regular"`:
  hosted Penpot 2.19 rejects `400` (`Value not valid: 400. Code: :fontVariantId`), so every
  400-weight text on the hosted file now reads back as `regular`.

## M11 · Poster fills the first viewport (2026-11-05)

- **The defect, measured on the 1440×3960 render.** The poster ran 108..776, so the first
  900px viewport carried a 24px paper band between the masthead rule and the photo (the rule
  sat on 84, the poster began on 108) and a 124px paper band below the photo (776..900). The
  white ECG trace also stopped at x 1321: its 10th cycle only draws 0.18 of a slot, so the
  path ended at 0.918 × 1440 while the shape is 1440 wide.
- **Poster = first viewport.** `HERO_Y 84`, `HERO_H 816` (84..900); the masthead takes
  `{ rule: false }` and `lib.js masthead` draws its bottom rule only when `o.rule !== false`
  (every other screen still draws it — `01` is the only caller that opts out). Poster foot is
  anchored to the bottom edge — `hero society` at `H-248`, `hero ecg` at `H-128`,
  `hero society line` at `H-44` — while label/date/venue/countdown/CTA/numeral keep their
  `HERO_Y`-relative offsets, so the copy block is unchanged and only the space between CTA
  and foot grew.
- **ECG spans the board.** `lib.js ecg` appends one closing segment at the flat level
  (`0.55*h`) from the last cycle's end to `x = w`. Wave shape, stroke width, count and every
  other ECG (guideline strip, states) are untouched.
- **Spec and geometry.** `ux-spec.json` 01: `story.proof` is the poster's own figures, the
  viewport claim is `hero countdown value`, and the four-cell `hero proof value` claim is
  gone. As-built 4084: §01 head 1012, Akademi 1668, Yayın 2224, Gündem 2816, news title 0
  2988, üyelik band 3372..3708, footer bar 3764.
- **Pixel proof (exported PNG, 1440×4084).** Row means: 64..83 = 243.7 (paper masthead
  interior), **84 = 26.6 first poster row**, 85..899 all dark (only y 788 is bright at 241.4 —
  that row *is* the white trace), **900 = 243.7 paper**. Pure-white pixels in y 772..802
  cover every column 0..1439 (previously 0..1321). `img-hero` is 1440×816, re-cropped by
  `media.py --restore` from the pinned source, not stretched; the imprint ink 855..873 sits
  27px above the fold with no clipping.
- **White type re-measured.** The taller crop also changes the pixels behind the type: the
  16px `hero venue` line is now the tightest at **4.92:1** (p95 of the graded crop, 3.6% of
  its box under 4.5:1) and the imprint 5.56:1; every other poster line is 8.4:1 or better.
  The as-built contrast paragraph carries the new numbers; the old 18.7:1 venue figure
  described the 668px crop.
- **Run.** `build.py screen-01` completed inside one session (no 120s abort):
  `RESULT ok nulls=0`, photos 2/2, links 1/1, layout quiet after 3 fit passes; canvas reflow
  moved `02-dernek` 4720→4764. `ux_gate --spec design/ihkd/ux-spec.json` → exit 0, 0 findings.
