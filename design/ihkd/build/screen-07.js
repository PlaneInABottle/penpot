/**
 * 07 — Bilimsel program. 22 Nisan: içerikten türeyen satır yüksekliği;
 * her satır en uzun oturum içeriğini taşır, boş dilimler öğle/kahve bandıdır.
 */
const S = IK;
const pb = S.start("Kongre", "07-program", 3000);

const cw = (s) => Math.round(s.length * 8.6) + 32;

S.masthead(pb, "Kongre");
S.text(pb, "p label", "BİLİMSEL PROGRAM", "label", "ink.500", { x: 120, y: 156 });
S.text(pb, "p title", "22–25 Nisan 2027", "h2", "ink.900", { x: 120, y: 188, w: 700 });
S.text(pb, "p note", "Son güncelleme 12 Mart 2027 · 22 Nisan 19 oturum · dört gün toplam 96 oturum", "meta", "ink.500", { x: 760, y: 220, w: 560, align: "right" });
S.rule(pb, "p rule", 120, 260, 1200, "line.strong", 2);

/* -------------------------------------------------------------- gün sekmeleri */
const days = [["21", "Nisan", "Kurs günü"], ["22", "Nisan", "Açılış"], ["23", "Nisan", ""], ["24", "Nisan", ""], ["25", "Nisan", "Kapanış"]];
let dx = 120;
days.forEach((d, i) => {
  const on = i === 1;
  const b = S.board(pb, "day " + i, dx, 292, 168, 64, on ? "red.600" : "white");
  if (!on) S.stroke(b, "line.strong", 1);
  S.text(b, "day num " + i, d[0], "dataLg", on ? "on.red" : "ink.900", { x: dx + 16, y: 304 });
  S.text(b, "day month " + i, d[1], "meta", on ? "on.red" : "ink.500", { x: dx + 56, y: 308 });
  if (d[2]) S.text(b, "day tag " + i, d[2], "meta", on ? "on.red" : "ink.500", { x: dx + 56, y: 326 });
  dx += 176;
});

/* ------------------------------------------------------------------ filtreler */
let fx = 120;
["Tüm salonlar", "Salon A", "Salon B", "Salon C", "Salon D"].forEach((f, i) => {
  const w = cw(f);
  const b = S.board(pb, "hall " + i, fx, 380, w, 32, i === 0 ? "red.050" : "white");
  if (i !== 0) S.stroke(b, "line.soft", 1);
  S.text(b, "hall text " + i, f, "label", i === 0 ? "red.700" : "ink.600", { x: fx + 14, y: 388 });
  fx += w + 6;
});
let tx = 800;
["Konsey oturumu"].forEach((f, i) => {
  S.rect(pb, "track dot " + i, tx, 392, 8, 8, "red.600");
  S.text(pb, "track leg " + i, f, "meta", "ink.600", { x: tx + 14, y: 388 });
  tx += Math.round(f.length * 6.6) + 40;
});
S.btn(pb, "prog add", "Seçili oturumları programa ekle", S.X + S.CW - 300, 376, 300, 40, "secondary");

/* -------------------------------------------------------------------- tablo */
/* Satır yüksekliği içerikten türer: her oturumun başlık+meta bloğu ölçülür,
   30 dakikalık dilim, başlayan en uzun bloğu taşıyacak boya kurulur.
   Boş dilimler gerçek içeriktir (öğle arası, kahve arası) — boş satır yok. */

// [slot, dilim sayısı, salon 0-3, başlık, konuşmacı / kapsam, konsey mi]
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
const HALLS = ["SALON A", "SALON B", "SALON C", "SALON D"];
const HX = [240, 510, 780, 1050];
const HW = 240;
const TOP = 476;

const tstr = (s) => {
  const m = 9 * 60 + s * 30;
  return ("0" + Math.floor(m / 60)).slice(-2) + ":" + ("0" + (m % 60)).slice(-2);
};

// İçerik ölçümü: başlık satırları + aralık + meta satırları. Süre etiketi
// metanın parçasıdır ('09:00–10:00 · 60 dk · Konuşmacı').
const metaOf = (s) => tstr(s[0]) + "–" + tstr(s[0] + s[1]) + " · " + (s[1] * 30) + " dk · " + s[4];
const contentH = (s) => S.estLines(s[3], HW - 24, 16, false) * 24 + 10
  + S.estLines(metaOf(s), HW - 24, 13, false) * 20;
const bySlot = {};
SESS.forEach((s, i) => { (bySlot[s[0]] = bySlot[s[0]] || []).push(i); });
const ROWS = [0, 1, 2, 4, 5, 8, 9, 10, 11, 13, 14, 15];
const rowH = (slot) => S.snap(Math.max(...bySlot[slot].map((i) => contentH(SESS[i]))) + 22);
// Agenda model: one row per START slot — no empty rows, no time math. Row
// height = tallest content in that row + padding (space-between: title top,
// meta bottom-anchored, so bottoms align with < 1 line of slack). A 30-min
// session that cannot use 30 min of height does not exist here: duration
// lives in the meta line ('09:00–10:00 · 60 dk · Speaker'), not in pixels.
// Full-width hour lines separate the row groups; the 48px break markers sit
// between groups with no gap on either side. Zebra and column rules are gone:
// the schedule reads top-to-bottom, not left-to-right.
const BANDS = [
  { after: 5, label: "12:00–13:00 · Öğle arası · poster sunumları" },
  { after: 11, label: "15:00–15:30 · Kahve arası" },
];

S.text(pb, "th time", "SAAT", "label", "ink.500", { x: 120, y: 448 });
HALLS.forEach((h, i) => S.text(pb, "th hall " + i, h, "label", "ink.500", { x: HX[i], y: 448 }));
S.rule(pb, "th rule", 120, 472, 1200, "line.strong", 1);

const drawRow = (slot, yRow, hRow) => {
  const cardH = hRow - 8;
  S.text(pb, "row time " + slot, tstr(slot), "data", "ink.500", { x: 120, y: yRow + 4 });
  bySlot[slot].forEach((i) => {
    const s = SESS[i];
    const cx = HX[s[2]];
    const tl = S.estLines(s[3], HW - 24, 16, false);
    const ml = S.estLines(metaOf(s), HW - 24, 13, false);
    const card = S.board(pb, "sess card " + i, cx, yRow + 4, HW - 8, cardH, "white");
    S.rect(card, "sess bar " + i, cx, yRow + 14, 2, cardH - 20, s[5] ? "red.600" : "line.strong");
    S.text(card, "sess title " + i, s[3], "bodyMed", "ink.900", { x: cx + 14, y: yRow + 14, w: HW - 24 });
    S.text(card, "sess meta " + i, metaOf(s), "meta", s[5] ? "red.700" : "ink.500",
      { x: cx + 14, y: yRow + 4 + cardH - 12 - ml * 20, w: HW - 24 });
  });
};

const band = (label, yBand) => {
  S.rect(pb, "band " + label.slice(0, 5), 240, yBand, 1080, 48, "white");
  S.text(pb, "band text " + label.slice(0, 5), label, "meta", "ink.500",
    { x: 560, y: yBand + S.vcenter(48, 20), w: 600, align: "center" });
  return yBand + 48;
};

let ry = TOP;
const GROUPS = [[0, 1, 2, 4, 5], [8, 9, 10, 11], [13, 14, 15]];
ry = S.rows(pb, "ag0", 120, ry, 1200, GROUPS[0].map((slot) => ({
  h: rowH(slot), draw(yRow) { drawRow(slot, yRow, rowH(slot)); },
})), {});
ry = band(BANDS[0].label, ry);
ry = S.rows(pb, "ag1", 120, ry, 1200, GROUPS[1].map((slot) => ({
  h: rowH(slot), draw(yRow) { drawRow(slot, yRow, rowH(slot)); },
})), {});
ry = band(BANDS[1].label, ry);
ry = S.rows(pb, "ag2", 120, ry, 1200, GROUPS[2].map((slot) => ({
  h: rowH(slot), draw(yRow) { drawRow(slot, yRow, rowH(slot)); },
})), { trailing: true });
/* ------------------------------------------------------------------ notlar */
const notesY = ry + 40;
S.text(pb, "pn label", "PROGRAM NOTLARI", "label", "ink.500", { x: 120, y: notesY });
const notes = [
  "Konsey oturumlarını iki başkan yönetir; konuşmacı listesi oturumdan 15 gün önce kesinleşir.",
  "21 Nisan kurs günü ayrı kayıt gerektirir; kontenjan 180 kişidir.",
  "Salon C ve D çeviri kabini içerir; talep kayıt sırasında alınır.",
  "Bildiri sunumları 8 dakika + 4 dakika tartışma.",
];
const notesEnd = S.rows(pb, "note", 120, notesY + 32, 1000, notes.map((n, i) => ({
  h: S.snap(S.estLines(n, 1000, 16, false) * 26 + 6),
  draw(yRow) {
    S.text(pb, "note " + i, n, "body", "ink.700", { x: 120, y: yRow, w: 1000 });
  },
})), { bare: true });

const footerY = S.snap(notesEnd + 40);
S.footer(pb, footerY);
pb.resize(1440, footerY + 320);

return JSON.stringify(S.end("07-program"));
