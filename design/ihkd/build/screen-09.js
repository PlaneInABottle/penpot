/**
 * 09 — Kayıt ve ücretler.
 */
const S = IK;
const pb = S.start("Kongre", "09-kayit", 2000);

S.masthead(pb, "Kongre");
S.pageHead(pb, "KAYIT", "Kayıt ve ücretler",
  "Erken kayıt 31 Ocak 2027'de kapanır. Ücretler kişi başı ve KDV dahildir.",
  { w: 900, ledeW: 760 });

/* --------------------------------------------------------------------- tablo */
const hy = 400;
const cols = [["KATILIMCI", 120, 400, "left"], ["ERKEN · 31 OCAK", 720, 200, "right"], ["STANDART", 940, 200, "right"], ["GEÇ · 15 NİSAN", 1160, 160, "right"]];
cols.forEach((c, i) => S.text(pb, "fee h " + i, c[0], "label", "ink.500", { x: c[1], y: hy, w: c[2], align: c[3] }));
S.rule(pb, "fee head rule", 120, hy + 24, 1200, "line.strong", 1);

const fees = [
  ["Üye", "3.400 TL", "4.100 TL", "4.800 TL", true],
  ["Üye olmayan", "4.600 TL", "5.400 TL", "6.100 TL", false],
  ["Asistan", "1.900 TL", "2.400 TL", "2.900 TL", false],
  ["Öğrenci", "1.200 TL", "1.500 TL", "1.900 TL", false],
  ["Hemşire / teknisyen", "1.600 TL", "2.000 TL", "2.400 TL", false],
];
fees.forEach((f, i) => {
  const fy = 468 + i * 64;
  if (f[4]) S.rect(pb, "fee tint " + i, 120, fy - 12, 1200, 60, "red.050");
  S.text(pb, "fee name " + i, f[0], "body", "ink.900", { x: 120, y: fy, w: 180 });
  if (f[4]) S.text(pb, "fee badge " + i, "ÜYE", "label", "red.700", { x: 168, y: fy + 4 });
  S.text(pb, "fee a " + i, f[1], "data", "ink.900", { x: 720, y: fy, w: 200, align: "right" });
  S.text(pb, "fee b " + i, f[2], "data", "ink.700", { x: 940, y: fy, w: 200, align: "right" });
  S.text(pb, "fee c " + i, f[3], "data", "ink.700", { x: 1160, y: fy, w: 160, align: "right" });
  S.rule(pb, "fee rule " + i, 120, fy + 40, 1200, "line.soft");
});

/* ---------------------------------------------------------- dahil / değil */
const iy = 816;
S.text(pb, "inc label", "ÜCRETE DAHİL", "label", "red.700", { x: 120, y: iy });
S.bullets(pb, "inc", 120, iy + 28, 560, ["Tüm bilimsel oturumlar", "Kongre çantası ve program", "22–25 Nisan öğle yemekleri", "Kabul edilen bildiri sunumu", "STE kredisi (24 saat)", "Salon C–D çeviri hizmeti"], { pad: 3, textX: 24 });

S.vrule(pb, "inc div", 700, iy, 200, "line.soft");
S.text(pb, "exc label", "DAHİL DEĞİL", "label", "ink.500", { x: 740, y: iy });
["Konaklama ve ulaşım", "21 Nisan kurs günü", "Akşam programı ve gala"].forEach((c, i) => {
  S.text(pb, "exc " + i, c, "body", "ink.600", { x: 740, y: iy + 28 + i * 32, w: 540 });
});

/* ------------------------------------------------------------ grup kaydı */
const gy = 1072;
const grp = S.board(pb, "group", 120, gy, 1200, 200, "surface.alt");
S.text(grp, "grp label", "GRUP KAYDI", "label", "red.700", { x: 152, y: gy + 32 });
S.text(grp, "grp title", "10 kişiden fazla ekipler için tek fatura", "h3", "ink.900", { x: 152, y: gy + 60, w: 620 });
S.text(grp, "grp body", "Kurum adına toplu kayıt, tek fatura ve kişi bazlı STE belgesi. Form 15 Mart 2027'ye kadar gönderilmeli.", "body", "ink.600", { x: 152, y: gy + 112, w: 620 });
S.link(grp, "grp cta", "Grup kayıt formu", 960, gy + 112, "ink.900");

/* ----------------------------------------------------------------- iptal */
const cny = 1320;
S.text(pb, "can label", "İPTAL KOŞULLARI", "label", "red.700", { x: 120, y: cny });
const cancel = [
  ["31 Ocak 2027'ye kadar", "Ücretin tamamı iade edilir."],
  ["1–31 Mart 2027", "Ücretin %50'si iade edilir."],
  ["1 Nisan 2027 sonrası", "İade yapılmaz; kayıt devredilebilir."],
];
cancel.forEach((c, i) => {
  const cy = cny + 44 + i * 44;
  S.text(pb, "can when " + i, c[0], "data", "ink.500", { x: 120, y: cy, w: 260 });
  S.text(pb, "can what " + i, c[1], "body", "ink.700", { x: 400, y: cy, w: 700 });
  S.rule(pb, "can rule " + i, 120, cy + 32, 1200, "line.soft");
});

S.btn(pb, "k cta", "Kaydı tamamla", 1044, 1532, 276, 52, "primary");
S.text(pb, "k cta note", "Ödeme havale veya kredi kartı ile.", "meta", "ink.500", { x: 720, y: 1548, w: 300, align: "right" });

S.footer(pb, 1648);

return JSON.stringify(S.end("09-kayit"));
