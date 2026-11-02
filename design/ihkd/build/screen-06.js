/**
 * 06 — Kongre. The one page where the photograph is the loud moment.
 */
const S = IK;
const pb = S.start("Kongre", "06-kongre", 3840);

S.masthead(pb, "Kongre");
S.text(pb, "ph label", "12. ULUSAL KONGRE · 22–25 NİSAN 2027", "label", "red.700", { x: 120, y: 156 });
S.text(pb, "ph title", "Dört gün, tek program", "display", "ink.900", { x: 120, y: 188, w: 860 });
S.text(pb, "ph lede", "Dört gün, 96 oturum, 214 konuşmacı. Vaka konseyleri ve kılavuz atölyeleriyle.", "lead", "ink.600", { x: 120, y: 376, w: 760 });
S.rule(pb, "ph rule", 120, 496, 1200, "line.strong", 1);
S.rect(pb, "ph bar", 120, 494, 96, 3, "red.600");
S.btn(pb, "c cta", "Kayıt ol", 120, 412, 216, 52, "primary");

/* full-bleed declared by the brief: 1440 wide, y 524–984 */
S.photo(pb, "img-cath", 0, 524, 1440, 460);
S.text(pb, "img-cath caption", "Kateter laboratuvarı, Antalya Kongre Merkezi", "meta", "ink.500", { x: 120, y: 996, w: 1200 });

/* ------------------------------------------------------------------ sayılar */
[["96", "oturum"], ["214", "konuşmacı"], ["780", "bildiri"], ["9", "ülke"]].forEach((f, i) => {
  S.stat(pb, "cf " + i, f[0], f[1], 120 + i * 300, 1064, 240);
  if (i) S.vrule(pb, "cf div " + i, 120 + i * 300 - 40, 1064, 76, "line.soft");
});
S.rule(pb, "c rule", 120, 1168, 1200, "line.strong", 1);
S.photo(pb, "img-hall", 120, 1216, 1200, 240, "Antalya Kongre Merkezi");

/* -------------------------------------------------------------------- neden */
let y = S.head(pb, 120, 1542, "NEDEN", "Program soruya göre kurulur.");
const why = [
  ["01", "Konsey oturumu", "Her gün en az iki oturum konsey düzeninde tartışılır."],
  ["02", "Vaka konseyi", "Gerçek hasta dosyaları, konseyde vaka tartışmasıyla."],
  ["03", "Kılavuz atölyesi", "2027 kılavuzlarının taslakları salonda tartışılıyor."],
];
why.forEach((w, i) => {
  const wx = 120 + i * 400;
  S.text(pb, "why n " + i, w[0], "data", "red.700", { x: wx, y: y });
  S.text(pb, "why h " + i, w[1], "bodyMed", "ink.900", { x: wx, y: y + 24, w: 320 });
  S.text(pb, "why p " + i, w[2], "body", "ink.600", { x: wx, y: y + 52, w: 320 });
});

/* ------------------------------------------------------------------- track */
let t = S.head(pb, 120, 1858, "TRACK'LER", "Beş track", { ruleAt: 156 });
S.text(pb, "track h0", "TRACK", "label", "ink.500", { x: 120, y: t });
S.text(pb, "track h1", "OTURUM", "label", "ink.500", { x: 780, y: t });
const tracks = [
  ["Kalp yetersizliği ve metabolik hastalıklar", "20 oturum"],
  ["Görüntüleme ve yapısal girişimler", "24 oturum"],
  ["Nefroloji, hipertansiyon ve damar", "18 oturum"],
  ["Aritmi ve ani ölüm", "21 oturum"],
  ["Geriatri ve çoklu ilaç kullanımı", "13 oturum"],
];
tracks.forEach((tr, i) => {
  const ty = t + 40 + i * 60;
  S.text(pb, "track name " + i, tr[0], "body", "ink.900", { x: 120, y: ty, w: 760 });
  S.text(pb, "track count " + i, tr[1], "data", "ink.500", { x: 780, y: ty + 4, w: 120 });
  S.rule(pb, "track row " + i, 120, ty + 44, 1200, "line.soft");
});

/* -------------------------------------------------------------- konuşmacılar */
let s = S.head(pb, 120, 2372, "KONUŞMACILAR", "Davetli konuşmacılar");
const speakers = [
  ["Prof. Dr. Ayşe Tunç", "Hacettepe · Kardiyoloji", "Açılış: kalp yetersizliğinde yeni eşikler"],
  ["Prof. Dr. Marc Dubois", "Paris Descartes · İç hastalıkları", "Metabolik sendromda konsey kararı"],
  ["Prof. Dr. Murat Şen", "Ankara · İç hastalıkları", "Böbrek ve kalp: iki hedef, tek plan."],
  ["Doç. Dr. Elif Karaca", "Ege · Kardiyoloji", "Görüntülemede standart rapor"],
];
speakers.forEach((sp, i) => {
  const sx = 120 + i * 306;
  S.text(pb, "spk name " + i, sp[0], "bodyMed", "ink.900", { x: sx, y: s, w: 280 });
  S.text(pb, "spk org " + i, sp[1], "meta", "ink.500", { x: sx, y: s + 24, w: 280 });
  S.text(pb, "spk talk " + i, sp[2], "body", "ink.700", { x: sx, y: s + 56, w: 280 });
});

/* ------------------------------------------------------------------- program */
let p = S.head(pb, 120, 2660, "PROGRAM", "Program önizleme", { link: "Tam program" });
const prev = [
  ["22 Nisan · 09:30", "Açılış oturumu", "Salon A · Prof. Dr. Ayşe Tunç, Prof. Dr. Murat Şen"],
  ["22 Nisan · 14:00", "Kalp yetersizliğinde konsey kararı", "Salon C · konsey"],
  ["23 Nisan · 11:00", "Vaka konseyi: nefes darlığı", "Salon B · 6 vaka"],
];
prev.forEach((pr, i) => {
  const py = p + i * 64;
  S.text(pb, "prev time " + i, pr[0], "data", "ink.500", { x: 120, y: py + 2, w: 160 });
  S.text(pb, "prev title " + i, pr[1], "bodyMed", "ink.900", { x: 300, y: py, w: 460 });
  S.text(pb, "prev where " + i, pr[2], "meta", "ink.500", { x: 780, y: py + 4, w: 540 });
  S.rule(pb, "prev rule " + i, 120, py + 48, 1200, "line.soft");
});

/* -------------------------------------------------------------- sponsorlar */
S.text(pb, "spo label", "SPONSORLAR", "label", "red.700", { x: 120, y: 3016 });
["TKD Yayın", "Medikal A", "Cardio Tek", "Nefro İlaç", "Görüntü Sistem", "Lab Grup"].forEach((sp, i) => {
  S.text(pb, "spo " + i, sp, "bodyMed", "ink.500", { x: 120 + i * 200, y: 3052, w: 180 });
});

/* ------------------------------------------------------------------- ücretler */
let f = S.head(pb, 120, 3140, "ÜCRETLER", "Erken kayıt 31 Ocak 2027'de kapanır", { ruleAt: 156 });
S.text(pb, "fee h1", "ERKEN · 31 OCAK 2027", "label", "ink.500", { x: 720, y: f, w: 240, align: "right" });
S.text(pb, "fee h2", "STANDART", "label", "ink.500", { x: 1060, y: f, w: 260, align: "right" });
const fees = [
  ["Üye", "3.400 TL", "4.100 TL"],
  ["Üye olmayan", "4.600 TL", "5.400 TL"],
  ["Asistan / öğrenci", "1.900 TL", "2.400 TL"],
];
fees.forEach((fe, i) => {
  const fy = f + 52 + i * 56;
  S.text(pb, "fee name " + i, fe[0], "body", "ink.900", { x: 120, y: fy });
  S.text(pb, "fee early " + i, fe[1], "data", "ink.900", { x: 720, y: fy, w: 240, align: "right" });
  S.text(pb, "fee std " + i, fe[2], "data", "ink.700", { x: 1060, y: fy, w: 260, align: "right" });
  S.rule(pb, "fee row " + i, 120, fy + 36, 1200, "line.soft");
});

S.footer(pb, 3520);

return JSON.stringify(S.end("06-kongre"));
