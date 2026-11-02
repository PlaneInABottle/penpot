/**
 * 07 — Bilimsel program, mobil 390 (`07-program-m`, sayfa `Mobil`).
 *
 *   python3 design/ihkd/build/build.py screen-m07
 *
 * Masaüstü 07'nin verisi aynı (22 Nisan, 19 oturum, dört salon); tek kolonda
 * okunacak biçim: gün şeridi, salon filtresi, oturum kartları, öğle/kahve
 * bantları. Konsey oturumu kırmızı ray taşır (masaüstü kırmızı çubuğun
 * karşılığı), diğerleri grafit ray.
 *
 * Gün şeridi 390'da kaydırma gerektirmez: 5 × 66 + 4 × 7 = 358, yani şerit
 * içeriğe tam oturur (kaydırılabilir bir şeridin son pill'i board dışına
 * taşardı — lint `overflow` bu yüzden yasak).
 *
 * `SESS` verisi screen-07.js'ten birebir kopyadır (ortak veri dosyası yok:
 * build.py yalnız lib.js + lib-m.js + ekran dosyasını enjekte eder).
 */
const S = IK;
const M = IKM;
const pb = M.start("Mobil", "07-program-m", 3800);

M.masthead(pb);

/* ------------------------------------------------------------------ sayfa başı */
/* Tarih iki ölçekte: 80px gün aralığı, 30px ay — sayı hiyerarşiyi taşır. */
S.text(pb, "p label", "BİLİMSEL PROGRAM", "label", "ink.500", { x: M.G, y: 96 });
S.text(pb, "p title a", "22–25", "display", "ink.900", { x: M.G, y: 120, w: M.CW });
S.text(pb, "p title b", "Nisan 2027", "h3", "ink.900", { x: M.G, y: 218, w: M.CW });
S.text(pb, "p note", "Son güncelleme 12 Mart 2027 · 22 Nisan 19 oturum · dört gün toplam 96 oturum",
  "meta", "ink.500", { x: M.G, y: 274, w: M.CW });
S.rule(pb, "p rule", M.G, 330, M.CW, "line.strong", 2);

/* -------------------------------------------------------------- gün sekmeleri */
const DAYS = [["21", "Nis"], ["22", "Nis"], ["23", "Nis"], ["24", "Nis"], ["25", "Nis"]];
const DW = 66, DGAP = 7;
DAYS.forEach((d, i) => {
  const on = i === 1;
  const dx = M.G + i * (DW + DGAP);
  const b = S.board(pb, "day " + i, dx, 350, DW, 56, on ? "red.600" : "white");
  if (!on) S.stroke(b, "line.strong", 1);
  S.text(b, "day num " + i, d[0], "dataLg", on ? "on.red" : "ink.900", { x: dx + 10, y: 360 });
  S.text(b, "day month " + i, d[1], "meta", on ? "on.red" : "ink.500", { x: dx + 10, y: 382 });
});
S.text(pb, "day tags", "21 Nisan kurs günü · 22 açılış · 25 kapanış", "meta", "ink.500",
  { x: M.G, y: 418, w: M.CW });

/* ------------------------------------------------------------------ filtreler */
let fy = M.chips(pb, "hall", ["Tüm salonlar", "Salon A", "Salon B", "Salon C", "Salon D"],
  M.G, 456, { active: 0, stroke: "line.soft" });
const legLine = S.ROLE.meta.size * S.ROLE.meta.lh;
S.rect(pb, "track dot 0", M.G, fy + legLine / 2 - 4, 8, 8, "red.600", { raw: true });
S.text(pb, "track leg 0", "Konsey oturumu", "meta", "ink.600", { x: M.G + 14, y: fy });
fy += 36;
M.btn(pb, "prog add", "Seçili oturumları programa ekle", fy, { kind: "secondary" });
let y = fy + 52 + 24;

/* -------------------------------------------------------------------- oturumlar */
/* [slot, dilim, salon 0-3, başlık, konuşmacı / kapsam, konsey mi] — screen-07.js */
const SESS = [
  [0, 2, 0, "Açılış oturumu", "Başkanlar: Prof. Dr. Ayşe Tunç, Prof. Dr. Murat Şen · Konsey", true],
  [2, 2, 0, "Kalp yetersizliğinde yeni eşikler", "Başkanlar: Prof. Dr. Elif Karaca, Prof. Dr. Murat Şen · Konsey", true],
  [4, 2, 0, "Vaka konseyi: nefes darlığı", "Prof. Dr. Murat Şen, Doç. Dr. Deniz Arslan · Konsey", true],
  [8, 1, 0, "TAVİ'de hasta seçimi", "Doç. Dr. Barış Demir · Kardiyoloji", false],
  [10, 2, 0, "Kapak hastalıklarında TAVİ kararı", "Başkanlar: Prof. Dr. Elif Karaca, Prof. Dr. Murat Şen · Konsey", true],
  [13, 1, 0, "Antikoagülasyon pratiği", "Doç. Dr. Kerem Yalçın · İç hastalıkları", false],
  [1, 2, 1, "Görüntülemede standart rapor", "Doç. Dr. Elif Karaca · Kardiyoloji", false],
  [4, 2, 1, "Eko: vaka okuma atölyesi", "Uzm. Dr. Selin Aydın · Kardiyoloji", false],
  [8, 1, 1, "Biyobelirteçler: ne zaman?", "Prof. Dr. Sema Yıldız · İç hastalıkları", false],
  [10, 2, 1, "Aritmi ve ani ölüm", "Prof. Dr. Ayşe Tunç · Kardiyoloji", false],
  [14, 2, 1, "Uyku apnesi ve kalp", "Doç. Dr. Onur Kılıç · Kardiyoloji", false],
  [2, 2, 2, "Böbrek ve kalp: iki hedef", "Prof. Dr. Murat Şen · İç hastalıkları", false],
  [5, 1, 2, "Dirençli hipertansiyon", "Prof. Dr. Sema Yıldız · Kardiyoloji", false],
  [9, 2, 2, "Diyabet ve kalp: ortak protokol", "Doç. Dr. Kerem Yalçın · İç hastalıkları", false],
  [13, 1, 2, "Lipid hedefleri 2027", "Uzm. Dr. Deniz Arslan · Kardiyoloji", false],
  [0, 2, 3, "Asistan forumu: vaka sunumları", "Dr. Emre Kaya · Eğitim", false],
  [4, 2, 3, "Geriatride çoklu ilaç", "Başkanlar: Doç. Dr. Deniz Arslan, Prof. Dr. Murat Şen · Konsey", true],
  [11, 1, 3, "Kardiyo-onkoloji", "Başkanlar: Doç. Dr. Onur Kılıç, Prof. Dr. Sema Yıldız · Konsey", true],
  [15, 2, 3, "Genç sporcuda EKG taraması", "Doç. Dr. Elif Karaca · Kardiyoloji", false],
];
const HALL = "ABCD";
const tstr = (s) => {
  const m = 9 * 60 + s * 30;
  return ("0" + Math.floor(m / 60)).slice(-2) + ":" + ("0" + (m % 60)).slice(-2);
};
const metaOf = (s) => tstr(s[0]) + "–" + tstr(s[0] + s[1]) + " · " + (s[1] * 30) + " dk · SALON " + HALL[s[2]];

const CARD_PAD = 16;
const TW = M.CW - 2 * CARD_PAD;          /* 326: kart metin kolonu */
const up4 = (v) => Math.ceil(v / 4) * 4;
const titleLines = (s) => S.estLines(s[3], TW, 16, false);
const speakerLines = (s) => S.estLines(s[4], TW, 13, false);
const cardH = (s) => up4(CARD_PAD + 20 + 6 + titleLines(s) * 24 + 6 + speakerLines(s) * 20 + CARD_PAD);

const sessionItem = (i) => {
  const s = SESS[i];
  const h = cardH(s);
  return {
    h,
    draw(yRow) {
      const top = yRow, ch = h;
      const titleY = top + CARD_PAD + 26;
      const card = S.board(pb, "sess card " + i, M.G, top, M.CW, ch, "white");
      S.stroke(card, "line.soft", 1);
      S.rect(card, "sess rail " + i, M.G, top + CARD_PAD, 3, ch - 2 * CARD_PAD, s[5] ? "red.600" : "line.strong");
      S.text(card, "sess meta " + i, metaOf(s), "data", s[5] ? "red.700" : "ink.500",
        { x: M.G + CARD_PAD, y: top + CARD_PAD, w: TW });
      S.text(card, "sess title " + i, s[3], "bodyMed", "ink.900", { x: M.G + CARD_PAD, y: titleY, w: TW });
      S.text(card, "sess who " + i, s[4], "meta", "ink.600",
        { x: M.G + CARD_PAD, y: titleY + titleLines(s) * 24 + 6, w: TW });
    },
  };
};

const bandItem = (label) => ({
  h: 48,
  draw(yRow) {
    const b = S.board(pb, "band " + label.slice(0, 5), M.G, yRow, M.CW, 48, "white");
    S.text(b, "band text " + label.slice(0, 5), label, "meta", "ink.500", { x: M.G + 16, y: yRow + 14, w: M.CW - 32 });
  },
});

/* Kronoloji: başlangıç saatine göre; bantlar boş dilimlerin yerinde. */
const items = [];
let lunch = true, coffee = true;
SESS.map((s, i) => i).sort((a, b) => SESS[a][0] - SESS[b][0] || SESS[a][2] - SESS[b][2]).forEach((i) => {
  const s = SESS[i];
  if (lunch && s[0] >= 6) { items.push(bandItem("12:00–13:00 · Öğle arası · poster sunumları")); lunch = false; }
  if (coffee && s[0] >= 12) { items.push(bandItem("15:00–15:30 · Kahve arası")); coffee = false; }
  items.push(sessionItem(i));
});
if (lunch) items.push(bandItem("12:00–13:00 · Öğle arası · poster sunumları"));
if (coffee) items.push(bandItem("15:00–15:30 · Kahve arası"));

y = S.rows(pb, "sess", M.G, y, M.CW, items, { gap: 12, bare: true });

/* --------------------------------------------------------------- program notu */
y += 24;
S.text(pb, "pn label", "PROGRAM NOTLARI", "label", "ink.500", { x: M.G, y: y });
const notes = [
  "Konsey oturumlarını iki başkan yönetir; konuşmacı listesi oturumdan 15 gün önce kesinleşir.",
  "21 Nisan kurs günü ayrı kayıt gerektirir; kontenjan 180 kişidir.",
  "Salon C ve D çeviri kabini içerir; talep kayıt sırasında alınır.",
  "Bildiri sunumları 8 dakika + 4 dakika tartışma.",
];
y = S.bullets(pb, "note", M.G, y + 28, M.CW, notes, { ink: "ink.700" });

/* --------------------------------------------------------------------- footer */
y = M.footer(pb, y + M.SECTION);
pb.resize(M.W, S.snap(y));

return JSON.stringify(S.end("07-program-m"));
