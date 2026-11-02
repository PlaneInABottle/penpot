# Canlı çalıştırma kuyruğu — mobil 390 + durum tahtaları + Components

**Durum: hiçbiri canlı çalıştırılmadı.** Bu dosyadaki dosyalar yazıldı ve yalnız
statik doğrulamadan geçti (`node --check`, `py_compile`, `build.py --dry-run`,
unittest). Aşağıdaki sıra, **hero ajanı canlı sayfayı bıraktıktan sonra** tek
yazarla koşulur: paylaşılan plugin sekmesinde aynı anda iki yazar `currentPage`'i
çalar ve iki build birbirinin tahtasını ezer.

Süre ölçümü yok; sıra ve komut var.

## 0 · Ön koşullar (kontrol, yazma yok)

```sh
cd /Users/Y_ALTAY1/Documents/personal/penpot
docker compose up -d
docker compose ps                      # penpot-backend/frontend healthy
pgrep -fl "penpot_exec.py|build.py"    # BOŞ olmalı: başka yazar yok
```

Hero ajanının bitişi: `design/ihkd/build/screen-01.js` ve `lib.js` üzerinde
çalışan oturum kapandı, brief.md § hero kararı yazıldı.

## 1 · `Mobil` sayfası (yoksa) — iki çağrı

`penpot.createPage()` `currentPage`'i senkron değiştirmez; adı **ayrı** çağrıda
yazılır (tek çağrıda yazmak önceki sayfayı yeniden adlandırır). Kimlik
`storage`da tutulur:

```sh
# 1a: oluştur (varsa hiçbir şey yapmaz)
python3 scripts/penpot_exec.py --code 'const f = penpot.currentFile; if (!f.pages.some((p) => p.name === "Mobil")) { const pg = penpot.createPage(); storage.MOBIL_PAGE = pg.id; return JSON.stringify({ created: pg.id }); } return JSON.stringify({ created: null, pages: f.pages.map((p) => p.name) });'

# 1b: adı yaz (yeni sayfanın varsayılan adı ne olursa olsun id ile bulur)
python3 scripts/penpot_exec.py --code 'const f = penpot.currentFile; const pg = f.pages.find((p) => p.id === storage.MOBIL_PAGE); if (pg && pg.name !== "Mobil") { pg.name = "Mobil"; } return JSON.stringify({ pages: f.pages.map((p) => p.name) });'
```

`Components` sayfası zaten var (README gap 2). Yoksa aynı iki çağrı `"Components"`
ile koşulur.

## 2 · Bileşen kitaplığı (en riskli adım — iki kez)

```sh
python3 design/ihkd/build/build.py screen-components
python3 design/ihkd/build/build.py screen-components   # async commit: eksik bileşenleri tamamlar
```

- `30 bileşen` beklenir (3 buton × 5 durum, field × 5, row × 3, chip × 4, tag,
  card, stat). Konsol `! component not created: …` satırı yazarsa üçüncü kez koş.
- Doğrulama (ayrı çağrı, yazma yok):

```sh
python3 scripts/penpot_exec.py --code 'return JSON.stringify({ components: penpot.library.local.components.map((c) => c.name).sort(), page: penpot.currentPage.name });'
```

Beklenen adlar: `button/primary`, `button/primary-hover`, … `field/error`,
`chip/active`, `tag`, `card`, `stat`. Adlar `aile/durum`; etkileşim durumu
`-durum` ile eklenir (adın içine ikinci `/` koymak Penpot path'ini bozar).

## 3 · Mobil 390 ekranları (tek tek, aynı yazar)

```sh
python3 design/ihkd/build/build.py screen-m01     # 01-ana-sayfa-m
python3 design/ihkd/build/build.py screen-m07     # 07-program-m
python3 design/ihkd/build/build.py screen-m09     # 09-kayit-m
python3 design/ihkd/build/build.py screen-m19     # 19-giris-m
```

`build.py` her ekrandan sonra `lib.js + lib-m.js` enjekte eder, fit'i bekler,
provenance fotoğrafı olmayan tahtada `photos 0/0` yazar — mobil tahtalarda
bitmap fotoğraf yok (bilimsel figür kendi vektörümüz), bu yüzden foto onarımı
beklenmez. `links 0/0` normaldir: mobil akışlar `flows.js`'e eklenmedi (kapsam
dışı, aşağıdaki açık iş).

## 4 · Durum tahtaları (desktop 1440)

```sh
python3 design/ihkd/build/build.py screen-state-01  # Kurumsal / 01-bos
python3 design/ihkd/build/build.py screen-state-07  # Kongre / 07-program-loading
python3 design/ihkd/build/build.py screen-state-09  # Kongre / 09-kayit-hata
```

## 5 · Kapı (her sayfa ayrı; export+crop yalnız `--boards` ile)

```sh
python3 scripts/gate.py --pages Mobil --boards 01-ana-sayfa-m,07-program-m,09-kayit-m,19-giris-m
python3 scripts/gate.py --pages Kurumsal --boards 01-bos
python3 scripts/gate.py --pages Kongre --boards 07-program-loading,09-kayit-hata
python3 scripts/gate.py --pages Components
```

- `ux_gate` spec'i (`design/ihkd/ux-spec.json`) her koşuda bütünüyle denetlenir:
  01'in `01-bos` + `01-ana-sayfa-m`, 07'nin `07-program-loading` + `07-program-m`
  hedefleri bu adımdan sonra bulunmalı. `09-kayit-hata` ve `19-giris-m` spec'te
  yok (09/19 girdisi yok); eklemek ayrı bir iş.
- Kırmızı çıkarsa: `design_lint.py --page <sayfa> --json /tmp/l.json --dump-nodes /tmp/n.json`,
  `design_qa.py --page <sayfa> --lint-json /tmp/l.json`.

## 6 · Tile okuma (1:1) — PASS'ın tek kanıtı

```sh
python3 scripts/crop_board.py --board 01-ana-sayfa-m --page Mobil --out design/ihkd/shots/01-ana-sayfa-m/
python3 scripts/crop_board.py --board 07-program-m --page Mobil --out design/ihkd/shots/07-program-m/
python3 scripts/crop_board.py --board 09-kayit-m --page Mobil --out design/ihkd/shots/09-kayit-m/
python3 scripts/crop_board.py --board 19-giris-m --page Mobil --out design/ihkd/shots/19-giris-m/
python3 scripts/crop_board.py --board 01-bos --page Kurumsal --out design/ihkd/shots/01-bos/
python3 scripts/crop_board.py --board 07-program-loading --page Kongre --out design/ihkd/shots/07-program-loading/
python3 scripts/crop_board.py --board 09-kayit-hata --page Kongre --out design/ihkd/shots/09-kayit-hata/
```

Her tile/region `manifest.json` içinde `reviewed: true` + not ile işaretlenir,
sonra:

```sh
python3 scripts/crop_board.py --attest design/ihkd/shots/<board>/manifest.json
```

Mobilde en az dört yer: en küçük metin (13px meta), en yoğun bölge (oturum
kartları), birincil eylem (hero/reg cta), ikon/ok satırı (masthead hamburger,
`→` okları) + hero kenar boşluğu simetrisi (16/16).

## 7 · Hero görsel sözleşmesi netleşince: `heroM` güncelle

brief.md'ye `Hero görsel sözleşmesi` satırı yazıldığında:

1. `design/ihkd/build/screen-m01.js` içinde `HERO_VISUAL` sabitini sözleşmeye
   göre ayarla (`"figure"` | `"photo"`) — tek dönüş noktası bu sabit ve
   `heroM()` gövdesi.
2. `photo` seçilirse: `media/provenance.json`'a mobil satırı **hero ajanı**
   ekler (`img-hero@01-ana-sayfa-m`), `build.py` foto onarımını o tahtada
   çalıştırır; bu dosya o satıra dokunmaz.
3. Yeniden: `python3 design/ihkd/build/build.py screen-m01` →
   `gate.py --pages Mobil --boards 01-ana-sayfa-m` → tile'ları yeniden oku.

## 8 · Bilinen riskler / açık işler (canlı turda bakılacak)

1. **lib-m genişlik snap'i.** `S.board` genişliği 4px'e snap'ler; 390 - 2·16 =
   358 dörde bölünmez. `lib-m.exact()` tam genişlikli bloklarda snap'i geri alır
   (16/16 kenar). 1:1'de sağ kenar 374 mü, ölç.
2. **Ölçek oranı.** `design_lint` `min_display_ratio 3.0` ister. Mobil ekranlar
   bu yüzden 80px `display` ile açılır (hero cümlesi, tarih, son gün, `Hekimin
   evi.`); en sık kullanılan gövde 13–16px. Yeni bir tahtada 44px'ten büyük
   hiçbir şey yoksa lint HIGH verir.
3. **Bileşen async commit'i** (adım 2): ilk turda eksik kalan bileşen ikinci
   turda tamamlanır; üç turda da eksik varsa `mainInstance`/ad çakışması vardır,
   `storage.H.audit("Components")` ile orphan listesine bakılır.
4. **Gün şeridi kaydırma.** 5 × 66 + 4 × 7 = 358: şerit 390'a tam oturur, gerçek
   kaydırma yok. Gerçek gün listesi 5'ten uzun olursa şerit yatay kaydırılır
   (tasarım tahtasında taşan pill lint `overflow` verir — bilinçli karar).
5. **Oturum verisi kopyası.** `screen-m07.js` `SESS` dizisi `screen-07.js`ten
   birebir kopyadır; build.py yalnız `lib.js + lib-m.js + ekran` enjekte eder.
   Ortak veri dosyası istersen build.py'ye üçüncü enjeksiyon eklenmeli (ayrı iş).
6. **Mobil akışlar.** `flows.js`'e mobil `navigate-to` eklenmedi; `links 0/0`
   beklenen sonuç. Prototip işi ayrı milestone.
7. **`ux-spec.json`.** 09/19 girdisi yok; `09-kayit-hata` / `19-giris-m` kapıda
   denetlenmiyor. 01/07 girdileri bu milestone'da **değiştirilmedi** (hedefleri
   zaten `01-bos`, `07-program-loading`, `01-ana-sayfa-m`, `07-program-m`).
8. **README gap 2** ("`Components` boş") bu işten sonra geçersiz; handoff
   README'si ayrı güncellenir (bu dosyalar README'ye dokunmaz).
