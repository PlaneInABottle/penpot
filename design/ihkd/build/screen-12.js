/**
 * 12 — Kurs detayı. Outcomes and an eight-module curriculum on the left; the progress
 * panel on the right; eligibility and accreditation in one row below.
 *
 * Every repeating row goes through S.rows(): the separator always lands on the
 * block's bottom edge, content is top-anchored or centered by rule, and no
 * shape carries a hand-written rule y. Vertical positions accumulate from a
 * cursor — there is exactly one arithmetic chain from the masthead to the footer.
 */
const S = IK;
const pb = S.start("Akademi", "12-kurs-detay", 1740);

S.masthead(pb, "Akademi");
S.crumbs(pb, ["Akademi", "Kurslar", "Kalp yetersizliğinde güncel tedavi"], 120, 132);
S.text(pb, "k label", "KURS · KALP YETERSİZLİĞİ", "label", "red.600", { x: 120, y: 160 });
S.text(pb, "k title", "Kalp yetersizliğinde güncel tedavi", "h2", "ink.900", { x: 120, y: 188, w: 900 });
S.text(pb, "k meta", "8 modül · 6 STE · 4s 20dk · Türkçe · Üyeler için ücretsiz", "data", "ink.500", { x: 120, y: 264, w: 900 });
S.text(pb, "k instructor", "Eğitmen: Prof. Dr. Murat Şen · Ankara Üniversitesi", "meta", "ink.600", { x: 120, y: 290, w: 900 });
S.rule(pb, "k rule", 120, 334, 1200, "ink.900", 2);

/* ------------------------------------------------------------------- kazanımlar */
S.text(pb, "o label", "BU KURSTA", "label", "red.600", { x: 120, y: 412 });
const out = [
  "EF düşük hastada dört temel ilaç grubunu sıralamak",
  "Hiperkalemi ve hipotansiyonda doz ayarı",
  "Taburculuk sonrası 30 günlük izlem planı",
  "Demir eksikliği ve anemi yönetimi",
  "Cihaz endikasyonunu zamanlamak",
];
S.rows(pb, "o", 120, 444, 740, out.map((t, i) => {
  const lines = S.estLines(t, 740, 16, false);
  return {
    h: S.snap(6 + lines * 26 + 4),
    draw(yRow) {
      S.rect(pb, "o dot " + i, 120, yRow + 6, 6, 6, "red.600");
      S.text(pb, "o " + i, t, "body", "ink.700", { x: 140, y: yRow, w: 740 });
    },
  };
}), { rule: false });

/* -------------------------------------------------------------------- müfredat */
S.text(pb, "cur label", "MÜFREDAT", "label", "red.600", { x: 120, y: 668 });
S.text(pb, "cur count", "3 / 8 tamamlandı", "data", "ink.500", { x: 600, y: 668, w: 300, align: "right" });
S.rule(pb, "cur rule", 120, 700, 780, "line.strong", 1);
const mods = [
  ["01", "Tanı ve evreleme", "28 dk", "tamamlandı"],
  ["02", "Dört temel ilaç", "38 dk", "tamamlandı"],
  ["03", "Doz titrasyonu", "34 dk", "tamamlandı"],
  ["04", "Hiperkalemi yönetimi", "32 dk", "devam"],
  ["05", "Demir ve anemi", "30 dk", "kilitli"],
  ["06", "Cihaz endikasyonu", "36 dk", "kilitli"],
  ["07", "Taburculuk planı", "28 dk", "kilitli"],
  ["08", "Vaka: 68 yaşında KKY", "34 dk", "kilitli"],
];
const mEnd = S.rows(pb, "m", 120, 712, 780, mods.map((m, i) => {
  const locked = m[3] === "kilitli";
  const state = m[3] === "tamamlandı" ? "Tamamlandı" : m[3] === "devam" ? "Devam ediyor" : "Kilitli";
  const stateColor = m[3] === "devam" ? "red.700" : m[3] === "tamamlandı" ? "ink.600" : "ink.500";
  const lines = S.estLines(m[1], 460, 16, false);
  return {
    h: S.snap(10 + lines * 26 + 20),
    draw(yRow) {
      S.text(pb, "m n " + i, m[0], "data", "ink.500", { x: 120, y: yRow + 12 });
      S.text(pb, "m title " + i, m[1], "body", locked ? "ink.500" : "ink.900", { x: 172, y: yRow + 10, w: 460 });
      S.text(pb, "m dur " + i, m[2], "data", "ink.500", { x: 640, y: yRow + 12, w: 80, align: "right" });
      S.text(pb, "m state " + i, state, "meta", stateColor, { x: 740, y: yRow + 14, w: 160, align: "right" });
    },
  };
}), { rule: "line.soft" });

/* ------------------------------------------------------------------- yan panel */
// Single vertical flow on a cursor: label → %40 → next → progress →
// button → DAHİL list → credit → photo. Block heights are content-derived;
// rows() owns every separator, so nothing can drift onto the button again.
let sc = 436;
const SC_X = 992, SC_W = 296;
const incItems = ["8 video modül", "2 vaka dosyası", "STE belgesi", "Özet PDF"];
const certLines = S.estLines("STE kredisi: 6 · Türk Tabipleri Birliği onaylı", SC_W, 13, false);
const nextLines = S.estLines("Sıradaki: 04 — Hiperkalemi yönetimi", SC_W, 13, false);
const side = S.board(pb, "side", 960, 412, 360, 800, "surface.alt");
S.text(side, "s label", "İLERLEME", "label", "ink.500", { x: SC_X, y: sc }); sc += 20;
S.text(side, "s pct", "%40", "h2", "ink.900", { x: SC_X - 4, y: sc }); sc += 51;
S.text(side, "s next", "Sıradaki: 04 — Hiperkalemi yönetimi", "meta", "ink.600", { x: SC_X, y: sc, w: SC_W }); sc += nextLines * 20 + 16;
S.progress(side, "s prog", SC_X, sc, SC_W, 40); sc += 24;
S.btn(side, "s cta", "Devam et", SC_X, sc, SC_W, 48, "primary"); sc += 68;
S.text(side, "s inc label", "DAHİL", "label", "ink.500", { x: SC_X, y: sc }); sc += 24;
incItems.forEach((t, i) => {
  S.rect(side, "s inc dot " + i, SC_X, sc + 6, 6, 6, "red.600");
  S.text(side, "s inc " + i, t, "meta", "ink.700", { x: SC_X + 16, y: sc, w: SC_W - 16 });
  sc += 28;
});
sc += 16;
S.text(side, "s cert", "STE kredisi: 6 · Türk Tabipleri Birliği onaylı", "meta", "ink.500", { x: SC_X, y: sc, w: SC_W });
const contentBottom = sc + certLines * 20 + 24;
S.photo(side, "img-lab", SC_X, sc + certLines * 20 + 24, SC_W, 160, "Uygulamalı tedavi oturumu, Ankara");
side.resize(360, contentBottom + 160 + 12 + 20 + 24 - 412);
const lowerY = Math.max(contentBottom + 160 + 12 + 20 + 24, mEnd + 48);

/* --------------------------------------------------------------- alt bilgiler */
S.text(pb, "for label", "KİMLER İÇİN", "label", "red.600", { x: 120, y: lowerY });
S.text(pb, "for text", "Kardiyoloji ve iç hastalıkları uzmanları, yan dal asistanları, KKY polikliniğinde çalışan hemşireler.", "body", "ink.700", { x: 120, y: lowerY + 28, w: 360 });
S.text(pb, "pre label", "ÖN KOŞUL", "label", "red.600", { x: 540, y: lowerY });
S.text(pb, "pre text", "Temel ekokardiyografi bilgisi önerilir; zorunlu değildir.", "body", "ink.700", { x: 540, y: lowerY + 28, w: 360 });
S.text(pb, "acc label", "AKREDİTASYON", "label", "red.600", { x: 960, y: lowerY });
S.text(pb, "acc text", "İHKD Akademi, TTB STE kredilendirme programına kayıtlıdır. Kredi kurs bitiminde e-Devlet'e işlenir.", "body", "ink.700", { x: 960, y: lowerY + 28, w: 360 });

const updY = lowerY + 28 + 3 * 26 + 32;
S.text(pb, "upd", "Son güncelleme 18 Ocak 2027 · 5. sürüm", "meta", "ink.500", { x: 120, y: updY });

const footerY = S.snap(updY + 20 + 48);
S.footer(pb, footerY);
pb.resize(1440, footerY + 320);

return JSON.stringify(S.end("12-kurs-detay"));
