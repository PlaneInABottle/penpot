/**
 * 01 — Ana sayfa.
 *
 *   python3 design/ihkd/build/build.py screen-01
 *
 * Masthead → claim → scale → gündem → congress → groups → academy → publication.
 * Ink rules, one grid-contained photograph, one red band (the congress band); the hero
 * congress note is a white card so the page keeps a single red field.
 * Vertical rhythm: 96 between blocks, 128 from a section rule to its first row.
 */
const S = IK;
const pb = S.start("Kurumsal", "01-ana-sayfa", 3952);

/* --------------------------------------------------------- masthead + nav */
/* Home converts once, in the hero: the masthead carries a quiet ghost action. */
S.masthead(pb, null, { cta: "ghost" });

/* ------------------------------------------------------------------ hero */
/* Candidate A (chosen): proof strip docked to the hero. Left message column
   (top-anchored), right full-height photo, dark proof strip as the base.
   Single red action on the board: hero "Üye ol". */
const GX = S.X, GW = S.CW;
S.text(pb, "hero label", "1998'DEN BERİ · ANKARA", "label", "ink.500", { x: GX, y: 156 });
S.text(pb, "hero title", "Hastanın hekimi.", "display", "ink.900", { x: GX, y: 188, w: 560 });
S.text(pb, "hero lede",
  "1998'den beri iç hastalıkları hekimlerinin camiası: kılavuz, kongre, akademi tek adreste.",
  "lead", "ink.600", { x: GX, y: 368, w: 520 });
S.btn(pb, "hero cta", "Üye ol", GX, 470, 236, 52, "primary");
S.link(pb, "hero ghost", "Derneği tanı", 380, 482, "ink.900");
S.photo(pb, "img-hero", GX + 620, 156, 580, 560, null);

/* proof strip: the numbers are part of the hero, not a section below it */
const proof = S.board(pb, "hero proof", 0, 780, 1440, 104, "ink.900");
const proofStats = [["6.847", "üye"], ["41", "il"], ["12", "çalışma grubu"], ["10", "kılavuz"]];
proofStats.forEach((s, i) => {
  S.text(proof, "proof v " + i, s[0], "dataLg", "white", { x: 120 + i * 300, y: 806, w: 260 });
  S.text(proof, "proof l " + i, s[1], "meta", "white", { x: 120 + i * 300, y: 842, w: 260 });
});

/* ---------------------------------------------------------------- gündem */
let y = S.head(pb, 120, 932, "GÜNDEM", "Bu hafta", { link: "Tüm haberler →", next: 124 });
const news = [
  ["12 Mart 2027", "Kongre", "Program yayınlandı: 96 oturum, dört salon", "6 dk"],
  ["4 Mart 2027", "Akademi", "Kalp yetersizliği kursu için kayıtlar açıldı", "2 dk"],
  ["26 Şubat 2027", "Dernek", "Çalışma grubu başkanları belirlendi", "4 dk"],
];
news.forEach((n, i) => {
  S.text(pb, "news date " + i, n[0], "data", "ink.500", { x: 120, y: y + 26 });
  S.text(pb, "news cat " + i, n[1], "label", "ink.500", { x: 236, y: y + 26 });
  S.text(pb, "news title " + i, n[2], "h3", "ink.900", { x: 352, y: y + 22, w: 740 });
  S.text(pb, "news time " + i, n[3], "data", "ink.500", { x: 1190, y: y + 34, w: 90, align: "right" });
  S.rule(pb, "news rule " + i, 120, y + 88, 1200, "line.soft");
  y += 96;
});
S.text(pb, "news note", "Duyurular Pazartesi 09:00'da yayımlanır.", "meta", "ink.500", { x: 120, y: y + 16 });

/* --------------------------------------------------------------- kongre */
const bandY = 1460;
const band = S.board(pb, "kongre band", 0, bandY, 1440, 380, "red.600");
S.text(band, "band label", "12. ULUSAL KONGRE", "label", "on.red", { x: 120, y: bandY + 56 });
S.text(band, "band title", "22–25 Nisan 2027", "h2", "on.red", { x: 120, y: bandY + 96, w: 720 });
S.text(band, "band venue", "Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı", "body", "on.red", { x: 120, y: bandY + 176, w: 560, opacity: 0.9 });
S.btn(band, "band cta", "Kayıt ol", 120, bandY + 268, 168, 52, "onred");
S.link(band, "band cta 2", "Programı gör", 312, bandY + 218, "on.red");

const counter = S.board(band, "countdown block", 880, bandY + 56, 440, 192, "red.700");
S.text(counter, "cd label", "KONGREYE KALAN", "label", "on.red", { x: 912, y: bandY + 88, opacity: 0.55 });
S.text(counter, "cd value", "147", "stat", "on.red", { x: 908, y: bandY + 112 });
S.text(counter, "cd unit", "GÜN", "label", "on.red", { x: 912, y: bandY + 164 });
S.text(counter, "cd note", "Erken kayıt 31 Ocak 2027'de kapanıyor.", "meta", "on.red", { x: 912, y: bandY + 198, w: 376, opacity: 0.65 });

/* --------------------------------------------------- çalışma grupları */
y = S.head(pb, 120, 1936, "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.", { next: 128 });
const groups = [
  ["01", "Kardiyovasküler görüntüleme", "412 üye · Doç. Dr. Elif Karaca"],
  ["02", "Kalp yetersizliği", "508 üye · Prof. Dr. Murat Şen"],
  ["03", "Aritmi ve elektrofizyoloji", "287 üye · Prof. Dr. Ayşe Tunç"],
  ["04", "Kardiyometabolik", "366 üye · Doç. Dr. Kerem Yalçın"],
  ["05", "Hipertansiyon", "341 üye · Prof. Dr. Sema Yıldız"],
  ["06", "Geriatrik kardiyoloji", "198 üye · Doç. Dr. Deniz Arslan"],
];
/* Two columns, one band per visual row: the title box is derived from the
   column band (band − inset − arrow gutter), never a literal 400 that leaves
   21px of slack; the row height comes from the measured title lines, so a
   longer name wraps inside its column and the rule rides down instead of
   cutting the text (2026-11-02: title box ended 21px from its own edge). */
const GBAND = 560, GCOL = 620, GINSET = 48, GARROW = 40, TLH = 36, MLH = 20;
const GTITLE = GBAND - GINSET - GARROW;
const gPitch = [];
for (let r = 0; r < groups.length / 2; r += 1) {
  const pair = [groups[r * 2], groups[r * 2 + 1]];
  const lines = Math.max(...pair.map((g) => S.estLines(g[1], GTITLE, 30, false)));
  if (lines > 2) throw new Error("group name needs " + lines + " lines in a " + GTITLE + "px column");
  gPitch.push(18 + lines * TLH + 6 + MLH + 16);
}
const groupColumn = (c) => gPitch.map((h, r) => {
  const i = r * 2 + c, g = groups[i], gx = 120 + c * GCOL;
  return {
    h,
    draw(yRow) {
      S.text(pb, "group idx " + i, g[0], "data", "ink.500", { x: gx, y: yRow + 34 });
      S.text(pb, "group name " + i, g[1], "h3", "ink.900", { x: gx + GINSET, y: yRow + 18, w: GTITLE });
      S.text(pb, "group meta " + i, g[2], "meta", "ink.500", { x: gx + GINSET, y: yRow + 18 + S.estLines(g[1], GTITLE, 30, false) * TLH + 6, w: GTITLE });
      S.text(pb, "group arrow " + i, "→", "nav", "ink.500", { x: gx + GBAND - GARROW + 8, y: yRow + 26 });
    },
  };
});
const gTop = y;
S.rows(pb, "group a", 120, gTop, GBAND, groupColumn(0), { rule: "line.soft" });
y = S.rows(pb, "group b", 120 + GCOL, gTop, GBAND, groupColumn(1), { rule: "line.soft" });
S.text(pb, "groups all", "12 çalışma grubunun tümü →", "nav", "red.600", { x: 120, y: y + 24 });

/* -------------------------------------------------------------- akademi */
y = S.head(pb, 120, 2500, "AKADEMİ", "Kurs, kılavuz, STE", { next: 120 });
const courses = [
  ["Kalp yetersizliğinde güncel tedavi", "8 modül · 6 STE · 4s 20dk"],
  ["Ekokardiyografi: temelden ileriye", "12 modül · 9 STE · 7s 05dk"],
  ["Antikoagülasyon yönetimi", "5 modül · 3 STE · 2s 40dk"],
];
courses.forEach((c, i) => {
  S.text(pb, "course title " + i, c[0], "h3", "ink.900", { x: 120, y: y + 20, w: 640 });
  S.text(pb, "course meta " + i, c[1], "data", "ink.500", { x: 920, y: y + 32, w: 260 });
  S.text(pb, "course cta " + i, "Başla →", "nav", "red.600", { x: 1200, y: y + 30, w: 120, align: "right" });
  S.rule(pb, "course rule " + i, 120, y + 84, 1200, "line.soft");
  y += 92;
});
S.text(pb, "akademi note", "Kurslar üyeler için ücretsiz; STE kredisi kurs bitiminde yüklenir.", "meta", "ink.500", { x: 120, y: y + 16 });

/* ---------------------------------------------------------------- yayın */
y = S.head(pb, 120, 3042, "YAYIN", "Dergi ve kılavuz", { next: 128 });
S.photo(pb, "img-journal", 120, y, 300, 380, "Kardiyovasküler Klinik, cilt 12");
S.text(pb, "journal title", "Kardiyovasküler Klinik", "h3", "ink.900", { x: 460, y: y });
/* Journal column band derived from the grid: x 460 to the divider at 800,
   8px gutter. The meta and the toc rules share it — a 320px box under a
   300px rule ran 12px past the band. */
const JX = 460, JRULE = 800 - 8 - JX;
S.text(pb, "journal meta", "Cilt 12 · Sayı 1 · Mart 2027 · TR Dizin", "data", "ink.500", { x: JX, y: y + 40, w: JRULE });
const toc = [
  ["12", "STE olmayan hastada BKA: 2027 uzlaşısı"],
  ["28", "KKY'de SGLT2 inhibitörleri: gerçek yaşam verisi"],
  ["41", "Genç sporcularda EKG taramasının maliyeti"],
];
toc.forEach((t, i) => {
  S.text(pb, "toc page " + i, "s. " + t[0], "data", "ink.500", { x: JX, y: y + 92 + i * 78 });
  S.text(pb, "toc title " + i, t[1], "body", "ink.700", { x: JX + 48, y: y + 92 + i * 78 - 3, w: JRULE - 48 });
  S.rule(pb, "toc rule " + i, JX, y + 166 + i * 78, JRULE, "line.soft");
});
S.link(pb, "journal cta", "Sayıyı oku", 460, y + 340, "red.600");

S.vrule(pb, "pub div", 800, y, 380, "line.soft");
S.text(pb, "guide label", "AYIN KILAVUZU", "label", "ink.500", { x: 840, y: y });
S.text(pb, "guide title", "Hipertansiyon tanı ve tedavi kılavuzu", "h3", "ink.900", { x: 840, y: y + 32, w: 480 });
S.text(pb, "guide meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "ink.500", { x: 840, y: y + 156 });
S.text(pb, "guide body", "Ev ölçümü, ofis dışı tansiyon ve tedavi eşikleri üzerine İHKD kılavuzu.", "body", "ink.600", { x: 840, y: y + 188, w: 440 });
S.link(pb, "guide cta", "Kılavuzu indir", 840, y + 296, "ink.900");

/* --------------------------------------------------------------- footer */
S.footer(pb, 3632);

return JSON.stringify(S.end("01-ana-sayfa"));
