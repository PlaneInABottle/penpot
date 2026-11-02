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
const pb = S.start("Kurumsal", "01-ana-sayfa", 3896);

/* --------------------------------------------------------- masthead + nav */
S.masthead(pb, null);

/* ------------------------------------------------------------------ hero */
/* Grid-derived: left column w 520, right column x = X+640 w = (CW-80)/2, both inside X..X+CW. */
const GX = S.X, GW = S.CW;
S.text(pb, "hero label", "1998'DEN BERİ · ANKARA", "label", "ink.500", { x: GX, y: 156 });
S.text(pb, "hero title", "Hastanın hekimi.", "display", "ink.900", { x: GX, y: 188, w: 760 });
S.text(pb, "hero lede",
  "1998'den beri iç hastalıkları hekimlerinin camiası: kılavuz, kongre, akademi tek adreste.",
  "lead", "ink.600", { x: GX, y: 292, w: 520 });
S.btn(pb, "hero cta", "Kongreye kayıt ol", GX, 390, 236, 52, "primary");
S.link(pb, "hero cta 2", "Derneği tanı", 388, 404, "ink.900");
S.photo(pb, "img-echo", GX + 640, 156, (GW - 80) / 2, 384);

/* ------------------------------------------- hero congress note: white card, not a band */
const heroBand = S.board(pb, "hero band", GX, 564, GW, 80, "white");
S.stroke(heroBand, "line.strong", 1);
S.ecg(heroBand, "hero band ecg", 144, 580, 400, 40, "red.600");
S.text(heroBand, "hero band label", "12. ULUSAL KONGRE", "label", "ink.500", { x: 580, y: 584 });
S.text(heroBand, "hero band date", "22–25 Nisan 2027 · Antalya Kongre Merkezi", "body", "ink.900", { x: 580, y: 604, w: 420 });
S.link(heroBand, "hero band cta", "Kayıt ol →", 1200, 600, "red.700");

/* ------------------------------------------------------------------ stats */
S.rule(pb, "stats top", GX, 664, GW, "ink.900", 1);
const stats = [
  ["6.847", "üye"],
  ["41", "il"],
  ["12", "çalışma grubu"],
  ["10", "kılavuz"],
];
stats.forEach((s, i) => {
  S.stat(pb, "stat " + i, s[0], s[1], GX + i * (GW / 4) + (i ? 24 : 0), 696, 240);
  if (i) S.vrule(pb, "stat div " + i, GX + i * (GW / 4), 696, 76, "line.soft");
});
S.rule(pb, "stats bottom", GX, 804, GW, "ink.900", 1);

/* ---------------------------------------------------------------- gündem */
let y = S.head(pb, 120, 876, "GÜNDEM", "Bu hafta", { link: "Tüm haberler →", next: 124 });
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
const bandY = 1404;
const band = S.board(pb, "kongre band", 0, bandY, 1440, 380, "red.600");
S.text(band, "band label", "12. ULUSAL KONGRE", "label", "on.red", { x: 120, y: bandY + 56 });
S.text(band, "band title", "22–25 Nisan 2027", "h2", "on.red", { x: 120, y: bandY + 96, w: 720 });
S.text(band, "band venue", "Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı", "body", "on.red", { x: 120, y: bandY + 176, w: 560, opacity: 0.9 });
S.btn(band, "band cta", "Kayıt ol", 120, bandY + 268, 168, 52, "onred");
S.link(band, "band cta 2", "Programı gör", 312, bandY + 284, "on.red");

const counter = S.board(band, "countdown block", 880, bandY + 56, 440, 192, "red.700");
S.text(counter, "cd label", "KONGREYE KALAN", "label", "on.red", { x: 912, y: bandY + 88, opacity: 0.55 });
S.text(counter, "cd value", "147", "stat", "on.red", { x: 908, y: bandY + 112 });
S.text(counter, "cd unit", "GÜN", "label", "on.red", { x: 912, y: bandY + 164 });
S.text(counter, "cd note", "Erken kayıt 31 Ocak 2027'de kapanıyor.", "meta", "on.red", { x: 912, y: bandY + 198, w: 376, opacity: 0.65 });

/* --------------------------------------------------- çalışma grupları */
y = S.head(pb, 120, 1880, "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.", { next: 128 });
const groups = [
  ["01", "Kardiyovasküler görüntüleme", "412 üye · Doç. Dr. Elif Karaca"],
  ["02", "Kalp yetersizliği", "508 üye · Prof. Dr. Murat Şen"],
  ["03", "Aritmi ve elektrofizyoloji", "287 üye · Prof. Dr. Ayşe Tunç"],
  ["04", "Kardiyometabolik", "366 üye · Doç. Dr. Kerem Yalçın"],
  ["05", "Hipertansiyon", "341 üye · Prof. Dr. Sema Yıldız"],
  ["06", "Geriatrik kardiyoloji", "198 üye · Doç. Dr. Deniz Arslan"],
];
groups.forEach((g, i) => {
  const gx = 120 + (i % 2) * 620;
  const gy = y + Math.floor(i / 2) * 96;
  S.text(pb, "group idx " + i, g[0], "data", "ink.500", { x: gx, y: gy + 34 });
  S.text(pb, "group name " + i, g[1], "h3", "ink.900", { x: gx + 48, y: gy + 20, w: 400 });
  S.text(pb, "group meta " + i, g[2], "meta", "ink.500", { x: gx + 48, y: gy + 60, w: 400 });
  S.text(pb, "group arrow " + i, "→", "nav", "ink.500", { x: gx + 540, y: gy + 28 });
  S.rule(pb, "group rule " + i, gx, gy + 88, 560, "line.soft");
});
S.text(pb, "groups all", "12 çalışma grubunun tümü →", "nav", "red.600", { x: 120, y: y + 312 });

/* -------------------------------------------------------------- akademi */
y = S.head(pb, 120, 2444, "AKADEMİ", "Kurs, kılavuz, STE", { next: 120 });
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
y = S.head(pb, 120, 2986, "YAYIN", "Dergi ve kılavuz", { next: 128 });
S.photo(pb, "img-journal", 120, y, 300, 380, "Kardiyovasküler Klinik, cilt 12");
S.text(pb, "journal title", "Kardiyovasküler Klinik", "h3", "ink.900", { x: 460, y: y });
S.text(pb, "journal meta", "Cilt 12 · Sayı 1 · Mart 2027 · TR Dizin", "data", "ink.500", { x: 460, y: y + 40, w: 320 });
const toc = [
  ["12", "STE olmayan hastada BKA: 2027 uzlaşısı"],
  ["28", "KKY'de SGLT2 inhibitörleri: gerçek yaşam verisi"],
  ["41", "Genç sporcularda EKG taramasının maliyeti"],
];
toc.forEach((t, i) => {
  S.text(pb, "toc page " + i, "s. " + t[0], "data", "ink.500", { x: 460, y: y + 92 + i * 78 });
  S.text(pb, "toc title " + i, t[1], "body", "ink.700", { x: 508, y: y + 92 + i * 78 - 3, w: 280 });
  S.rule(pb, "toc rule " + i, 460, y + 166 + i * 78, 300, "line.soft");
});
S.link(pb, "journal cta", "Sayıyı oku", 460, y + 340, "red.600");

S.vrule(pb, "pub div", 800, y, 380, "line.soft");
S.text(pb, "guide label", "AYIN KILAVUZU", "label", "ink.500", { x: 840, y: y });
S.text(pb, "guide title", "Hipertansiyon tanı ve tedavi kılavuzu", "h3", "ink.900", { x: 840, y: y + 32, w: 480 });
S.text(pb, "guide meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "ink.500", { x: 840, y: y + 156 });
S.text(pb, "guide body", "Ev ölçümü, ofis dışı tansiyon ve tedavi eşikleri üzerine İHKD kılavuzu.", "body", "ink.600", { x: 840, y: y + 188, w: 440 });
S.link(pb, "guide cta", "Kılavuzu indir", 840, y + 296, "ink.900");

/* --------------------------------------------------------------- footer */
S.footer(pb, 3576);

return JSON.stringify(S.end("01-ana-sayfa"));
