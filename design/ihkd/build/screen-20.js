/**
 * 20 — Üye masası. Genel bakış: membership card, dues, courses, upcoming, notices, ECG.
 */
const S = IK;
const pb = S.start("Üyelik", "20-panel", 1680);

S.sidebar(pb, "Genel bakış", 1680);

/* --------------------------------------------------------------------- başlık */
S.text(pb, "p greet", "İyi günler, Dr. Selin Aydın", "h2", "ink.900", { x: 300, y: 64 });
S.text(pb, "p date", "Cuma, 30 Ekim 2026 · 08:15", "meta", "ink.500", { x: 300, y: 122 });
S.btn(pb, "p cta", "Kongreye kayıt ol", 1044, 64, 276, 52, "secondary");

/* ---------------------------------------------------------------- üyelik kartı */
const card = S.board(pb, "member card", 300, 196, 520, 300, "red.600");
S.text(card, "mc label", "İHKD ÜYE KARTI", "label", "on.red", { x: 332, y: 228, opacity: 0.72 });
S.text(card, "mc name", "Dr. Selin Aydın", "h3", "on.red", { x: 332, y: 262, w: 300 });
S.text(card, "mc no", "İHKD-24817", "dataLg", "on.red", { x: 332, y: 310 });
S.text(card, "mc group", "Kardiyoloji · Kalp yetersizliği grubu", "meta", "on.red", { x: 332, y: 344, w: 290, opacity: 0.88 });
S.text(card, "mc valid", "Geçerli: 31.12.2027", "meta", "on.red", { x: 332, y: 436, opacity: 0.88 });
S.rect(card, "qr bg", 640, 268, 140, 140, "white");
[[0,0],[2,0],[4,0],[0,2],[4,2],[0,4],[2,4],[4,4],[2,2]].forEach((c, i) =>
  S.rect(card, "qr cell " + i, 640 + c[0] * 28, 268 + c[1] * 28, 28, 28, "ink.900"));
S.text(card, "qr note", "Girişte gösterin", "meta", "on.red", { x: 640, y: 416, w: 140, align: "center", opacity: 0.85 });

/* ----------------------------------------------------------------------- aidat */
const aidat = S.board(pb, "aidat", 852, 196, 468, 300, "white");
S.stroke(aidat, "line.strong", 1);
S.text(aidat, "ai label", "AİDAT", "label", "ink.500", { x: 884, y: 228 });
S.text(aidat, "ai year", "2027", "h3", "ink.900", { x: 884, y: 256 });
S.text(aidat, "ai state", "Ödendi", "bodyMed", "ink.900", { x: 1148, y: 262, w: 140, align: "right" });
S.text(aidat, "ai amt", "3.400 TL · 14 Ocak 2027", "meta", "ink.500", { x: 884, y: 296, w: 400 });
S.rule(aidat, "ai rule", 884, 330, 404, "line.soft");
S.text(aidat, "ai y2", "2026", "body", "ink.700", { x: 884, y: 348 });
S.text(aidat, "ai s2", "Ödendi", "meta", "ink.500", { x: 1148, y: 350, w: 140, align: "right" });
S.rule(aidat, "ai rule 2", 884, 384, 404, "line.soft");
S.text(aidat, "ai y3", "2025", "body", "ink.700", { x: 884, y: 402 });
S.text(aidat, "ai s3", "Ödendi", "meta", "ink.500", { x: 1148, y: 404, w: 140, align: "right" });
S.link(aidat, "ai cta", "Makbuzları gör", 884, 444, "ink.900");

/* -------------------------------------------------------------------- kurslarım */
let y = 560;
S.text(pb, "k label", "KURSLARIM", "label", "red.700", { x: 300, y: y });
S.link(pb, "k all", "Tümü", 1248, y - 4, "ink.900");
[
  ["Kalp yetersizliğinde güncel tedavi", "3 / 8 modül", 40, "Devam et"],
  ["Ekokardiyografi: temelden ileriye", "12 / 12 modül", 100, "Belgeyi indir"],
].forEach((k, i) => {
  const ky = y + 40 + i * 100;
  S.text(pb, "k title " + i, k[0], "bodyMed", "ink.900", { x: 300, y: ky, w: 460 });
  S.progress(pb, "k prog " + i, 300, ky + 36, 420, k[2]);
  S.text(pb, "k pct " + i, "%" + k[2], "meta", "ink.500", { x: 740, y: ky + 26 });
  S.text(pb, "k meta " + i, k[1], "data", "ink.500", { x: 800, y: ky + 2, w: 140 });
  S.text(pb, "k cta " + i, k[3] + " →", "nav", "red.700", { x: 1060, y: ky, w: 260, align: "right" });
  S.rule(pb, "k rule " + i, 300, ky + 64, 1020, "line.soft");
});

/* -------------------------------------------------------------------- yaklaşan */
y = 840;
S.text(pb, "y label", "YAKLAŞAN", "label", "red.700", { x: 300, y: y });
[
  ["22 Nisan 2027", "12. Kongre açılışı", "Antalya · 09:30"],
  ["18 Nisan 2027", "Kalp yetersizliği grup toplantısı", "Çevrim içi · 19:00"],
  ["12 Mayıs 2027", "Webinar: KKY'de demir tedavisi", "Çevrim içi · 20:00"],
].forEach((n, i) => {
  const ny = y + 40 + i * 52;
  S.text(pb, "n date " + i, n[0], "data", "ink.500", { x: 300, y: ny + 2 });
  S.text(pb, "n title " + i, n[1], "body", "ink.900", { x: 480, y: ny, w: 520 });
  S.text(pb, "n where " + i, n[2], "meta", "ink.500", { x: 1020, y: ny + 3, w: 300, align: "right" });
  S.rule(pb, "n rule " + i, 300, ny + 36, 1020, "line.soft");
});

/* --------------------------------------------------------------------- EKG kartı */
y = 1080;
/* white like every other card on the desk: a 1020x200 alt field read as a wide
   grey band, not an inset (lint: large surface.alt card beside white cards) */
const ecgCard = S.board(pb, "ecg card", 300, y, 1020, 200, "white");
S.stroke(ecgCard, "line.strong", 1);   /* same border as the aidat card beside it */
S.text(ecgCard, "ec label", "KAYITLI EKG · 12.10.2026", "label", "ink.500", { x: 332, y: y + 24 });
S.ecg(ecgCard, "ec trace", 332, y + 56, 700, 90, "red.600");
S.text(ecgCard, "ec cal", "25 mm/s · 10 mm/mV · II. derivasyon", "data", "ink.500", { x: 332, y: y + 160 });
S.link(ecgCard, "ec cta", "Kaydı aç", 1120, y + 24, "ink.900");

/* -------------------------------------------------------------------- duyurular */
y = 1340;
S.text(pb, "d label", "DUYURULAR", "label", "red.700", { x: 300, y: y });
[
  ["28 Ekim 2026", "2027 aidat dönemi açıldı; erken ödemede %5 indirim."],
  ["20 Ekim 2026", "Kongre bildiri gönderimi 15 Şubat'ta kapanıyor."],
].forEach((d, i) => {
  const dy = y + 40 + i * 48;
  S.text(pb, "d date " + i, d[0], "data", "ink.500", { x: 300, y: dy + 2 });
  S.text(pb, "d t " + i, d[1], "body", "ink.700", { x: 480, y: dy, w: 840 });
  S.rule(pb, "d r " + i, 300, dy + 36, 1020, "line.soft");
});

S.text(pb, "foot", "Üye masası · 08:00–18:00 · uye@ihkd.org.tr · +90 312 425 18 41", "meta", "ink.500", { x: 300, y: 1560 });

return JSON.stringify(S.end("20-panel"));
