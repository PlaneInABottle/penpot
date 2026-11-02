# Canlı çalıştırma kuyruğu — durum tahtaları + Components

**Kapsam kararı:** mobil 390 ekranlar yol haritasından çıkarıldı; hangi sayfaların
yapılacağına kullanıcı karar verecek, o zaman yeniden eklenir.

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

## 4 · Durum tahtaları (desktop 1440)

```sh
python3 design/ihkd/build/build.py screen-state-01  # Kurumsal / 01-bos
python3 design/ihkd/build/build.py screen-state-07  # Kongre / 07-program-loading
python3 design/ihkd/build/build.py screen-state-09  # Kongre / 09-kayit-hata
```

## 5 · Kapı (her sayfa ayrı; export+crop yalnız `--boards` ile)

```sh
python3 scripts/gate.py --pages Kurumsal --boards 01-bos
python3 scripts/gate.py --pages Kongre --boards 07-program-loading,09-kayit-hata
python3 scripts/gate.py --pages Components
```

- `ux_gate` spec'i (`design/ihkd/ux-spec.json`) her koşuda bütünüyle denetlenir:
  01'in `01-bos`, 07'nin `07-program-loading` hedefleri bu adımdan sonra
  bulunmalı. `09-kayit-hata` spec'te yok (09 girdisi yok); eklemek ayrı bir iş.
- Kırmızı çıkarsa: `design_lint.py --page <sayfa> --json /tmp/l.json --dump-nodes /tmp/n.json`,
  `design_qa.py --page <sayfa> --lint-json /tmp/l.json`.

## 6 · Tile okuma (1:1) — PASS'ın tek kanıtı

```sh
python3 scripts/crop_board.py --board 01-bos --page Kurumsal --out design/ihkd/shots/01-bos/
python3 scripts/crop_board.py --board 07-program-loading --page Kongre --out design/ihkd/shots/07-program-loading/
python3 scripts/crop_board.py --board 09-kayit-hata --page Kongre --out design/ihkd/shots/09-kayit-hata/
```

Her tile/region `manifest.json` içinde `reviewed: true` + not ile işaretlenir,
sonra:

```sh
python3 scripts/crop_board.py --attest design/ihkd/shots/<board>/manifest.json
```

En az dört yer: en küçük metin, en yoğun bölge, birincil eylem, ikon/ok satırı.

## 8 · Bilinen riskler / açık işler (canlı turda bakılacak)

1. **Bileşen async commit'i** (adım 2): ilk turda eksik kalan bileşen ikinci
   turda tamamlanır; üç turda da eksik varsa `mainInstance`/ad çakışması vardır,
   `storage.H.audit("Components")` ile orphan listesine bakılır.
2. **Variant değeri yazılamaz:** plugin API'de variant property değeri ayarlayıcısı
   yok; aileler `aile/durum` düz adlarla yazıldı (Penpot'un yerel variant paneline
   bağlanmaz). Devir için yeterli, panel entegrasyonu ayrı iş.
