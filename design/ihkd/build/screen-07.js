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

// İçerik ölçümü: her oturum bloğu başlık satırları + aralık + meta satırları + padding.
const need = SESS.map((s) => {
  const tl = S.estLines(s[3], HW - 24, 16, false);
  const ml = S.estLines(tstr(s[0]) + "–" + tstr(s[0] + s[1]) + " · " + s[4], HW - 24, 13, false);
  return { slots: s[1], h: tl * 24 + 14 + ml * 20 + 22 };
});
const ROW_H = S.snap(Math.max(92, ...need.map((c) => Math.ceil(c.h / c.slots))));
// NSLOT 17: 09:00–17:30. Grid model: uniform time rows (ROW_H per 30 min,
// derived from the tallest content), NO zebra, NO column rules, NO row
// rules — only faint hour lines. Session cards span their FULL duration, so
// card edges ARE the time boundaries and no text can meet a boundary line.
// The 48px break markers interrupt the grid without consuming time rows;
// slots 6,7,12 hold no rows. A card floating mid-row ("box outside the box"
// feel) is unwritable here: card height comes from the slot span, never
// from the content alone.
const NSLOT = 17;
const BANDS = [
  { at: 6, label: "12:00–13:00 · Öğle arası · poster sunumları" },
  { at: 12, label: "15:00–15:30 · Kahve arası" },
];
const shift = (slot) => 48 * BANDS.filter((b) => b.at < slot).length;
const yOf = (slot) => TOP + slot * ROW_H + shift(slot);
const isBandSlot = (i) => BANDS.some((b) => b.at === i || (b.at === 6 && i === 7));

S.text(pb, "th time", "SAAT", "label", "ink.500", { x: 120, y: 448 });
HALLS.forEach((h, i) => S.text(pb, "th hall " + i, h, "label", "ink.500", { x: HX[i], y: 448 }));
S.rule(pb, "th rule", 120, 472, 1200, "line.strong", 1);

// hour lines on even slots that hold rows; time labels on every held slot
for (let i = 0; i < NSLOT; i++) {
  if (isBandSlot(i)) continue;
  if (i % 2 === 0) S.rule(pb, "hour " + i, 120, yOf(i), 1200, "line.soft");
  S.text(pb, "row time " + i, tstr(i), "data", "ink.500", { x: 120, y: yOf(i) + 12 });
}

BANDS.forEach((b, i) => {
  const y0 = TOP + b.at * ROW_H + shift(b.at);
  S.rect(pb, "band " + i, 240, y0, 1080, 48, "white");
  S.text(pb, "band text " + i, b.label, "meta", "ink.500",
    { x: 560, y: y0 + S.vcenter(48, 20), w: 600, align: "center" });
});

SESS.forEach((s, i) => {
  const ry = yOf(s[0]);
  const cx = HX[s[2]];
  const spanH = s[1] * ROW_H;
  const range = tstr(s[0]) + "–" + tstr(s[0] + s[1]);
  const tl = S.estLines(s[3], HW - 24, 16, false);
  // Full-span card: height comes from the DURATION, position from the time
  // math above. Text sits top-aligned inside its own time box; the accent
  // bar matches the content (fitBars post-pass), not the span.
  const card = S.board(pb, "sess card " + i, cx, ry + 4, HW - 8, spanH - 8, "white");
  S.rect(card, "sess bar " + i, cx, ry + 10, 2, spanH - 20, s[5] ? "red.600" : "line.strong");
  S.text(card, "sess title " + i, s[3], "bodyMed", "ink.900", { x: cx + 14, y: ry + 10, w: HW - 24 });
  S.text(card, "sess meta " + i, range + " · " + s[4], "meta", s[5] ? "red.700" : "ink.500", { x: cx + 14, y: ry + 14 + tl * 24, w: HW - 24 });
});

/* ------------------------------------------------------------------ notlar */
const notesY = yOf(NSLOT - 1) + ROW_H + 40;
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
