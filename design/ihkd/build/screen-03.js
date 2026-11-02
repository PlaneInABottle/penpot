/**
 * 03 — Yönetim. Kurullar, bilim kurulu tablosu, komisyonlar.
 */
const S = IK;
const pb = S.start("Kurumsal", "03-yonetim", 2296);

S.masthead(pb, "Dernek");
let y = S.pageHead(pb, "YÖNETİM", "Kurullar ve sorumluluklar",
  "Yönetim kurulu 2025 genel kurulunda seçildi; görev süresi 24 Nisan 2027'de sona eriyor.",
  { next: 400 });

/* ------------------------------------------------------- yönetim kurulu */
S.text(pb, "yk label", "YÖNETİM KURULU · 7 ÜYE", "label", "red.600", { x: 120, y: y });
const board = [
  ["Prof. Dr. Ayşe Tunç", "Başkan", "Hacettepe Üniversitesi · Kardiyoloji"],
  ["Prof. Dr. Murat Şen", "Genel sekreter", "Ankara Üniversitesi · İç hastalıkları"],
  ["Doç. Dr. Elif Karaca", "Sayman", "Ege Üniversitesi · Kardiyoloji"],
  ["Prof. Dr. Kerem Yalçın", "Üye", "Gazi Üniversitesi · İç hastalıkları"],
  ["Prof. Dr. Sema Yıldız", "Üye", "Marmara Üniversitesi · Nefroloji"],
  ["Doç. Dr. Deniz Arslan", "Üye", "Dokuz Eylül Üniversitesi · Geriatri"],
  ["Dr. Öğr. Üyesi Cem Aydın", "Üye", "Akdeniz Üniversitesi · Kardiyoloji"],
];
board.forEach((p, i) => {
  const col = i < 4 ? 0 : 1;
  const row = i < 4 ? i : i - 4;
  const px = 120 + col * 620;
  const py = y + 40 + row * 88;
  S.text(pb, "member name " + i, p[0], "bodyMed", "ink.900", { x: px, y: py, w: 360 });
  S.text(pb, "member role " + i, p[1], "label", "red.600", { x: px, y: py + 26 });
  S.text(pb, "member org " + i, p[2], "meta", "ink.500", { x: px, y: py + 50, w: 420 });
  S.text(pb, "member mail " + i, "E-posta →", "meta", "red.700", { x: px + 440, y: py + 26, w: 80, align: "right" });
  S.rule(pb, "member rule " + i, px, py + 76, 520, "line.soft");
});

/* ---------------------------------------------------------- denetim kurulu */
y = 876;
S.text(pb, "dk label", "DENETİM KURULU", "label", "red.600", { x: 120, y: y });
["Prof. Dr. Hakan Erdem · Başdenetçi", "Doç. Dr. Zeynep Kaya · Üye", "Dr. Burak Şahin · Üye"].forEach((d, i) => {
  S.text(pb, "dk " + i, d, "body", "ink.700", { x: 120, y: y + 36 + i * 40 });
});

/* ------------------------------------------------------------ bilim kurulu */
y = 1110;
S.text(pb, "bk label", "BİLİM KURULU · 12 ÜYE", "label", "red.600", { x: 120, y: y });
const head = ["AD", "KURUM", "ALAN", "GRUP"];
S.text(pb, "bk h0", head[0], "label", "ink.500", { x: 120, y: y + 36 });
S.text(pb, "bk h1", head[1], "label", "ink.500", { x: 420, y: y + 36 });
S.text(pb, "bk h2", head[2], "label", "ink.500", { x: 800, y: y + 36 });
S.text(pb, "bk h3", head[3], "label", "ink.500", { x: 1040, y: y + 36 });
S.rule(pb, "bk head rule", 120, y + 58, 1200, "ink.900", 1);
const science = [
  ["Prof. Dr. Ayşe Tunç", "Hacettepe", "Görüntüleme", "Görüntüleme"],
  ["Prof. Dr. Murat Şen", "Ankara", "Kalp yetersizliği", "Kalp yetersizliği"],
  ["Prof. Dr. Kerem Yalçın", "Gazi", "Metabolik", "Kardiyometabolik"],
  ["Prof. Dr. Sema Yıldız", "Marmara", "Hipertansiyon", "Hipertansiyon"],
  ["Doç. Dr. Deniz Arslan", "Dokuz Eylül", "Geriatri", "Geriatrik"],
  ["Dr. Cem Aydın", "Akdeniz", "Aritmi", "Aritmi"],
  ["Prof. Dr. Nihal Özkan", "İstanbul", "Lipit", "Lipit"],
  ["Doç. Dr. Barış Demir", "Ege", "Girişimsel", "Girişimsel"],
  ["Prof. Dr. Leyla Aksoy", "Çukurova", "Tromboz", "Tromboz"],
  ["Doç. Dr. Onur Kılıç", "Erciyes", "Kardiyo-onkoloji", "Kardiyo-onkoloji"],
  ["Prof. Dr. Selma Uçar", "Karadeniz", "Yapısal kalp", "Yapısal"],
  ["Dr. Emre Bozkurt", "Uludağ", "Spor kardiyolojisi", "Spor"],
];
science.forEach((s, i) => {
  const sy = y + 72 + i * 44;
  S.text(pb, "sc name " + i, s[0], "body", "ink.900", { x: 120, y: sy, w: 280 });
  S.text(pb, "sc org " + i, s[1], "body", "ink.700", { x: 420, y: sy, w: 340 });
  S.text(pb, "sc field " + i, s[2], "body", "ink.700", { x: 800, y: sy, w: 220 });
  S.text(pb, "sc group " + i, s[3], "meta", "ink.500", { x: 1040, y: sy + 2, w: 260 });
  if (i < science.length - 1) S.rule(pb, "sc rule " + i, 120, sy + 36, 1200, "line.soft");
});

/* ------------------------------------------------------------- komisyonlar */
y = 1784;
S.text(pb, "kom label", "KOMİSYONLAR", "label", "red.600", { x: 120, y: y });
const kom = [
  ["Eğitim", "9 üye"], ["Kılavuz", "11 üye"], ["Etik", "5 üye"],
  ["Genç hekimler", "7 üye"], ["Yayın", "6 üye"],
];

S.chips(pb, "kom", kom.map((k) => k[0] + " · " + k[1]), 120, y + 36);
S.text(pb, "sec note", "Genel kurul: 24 Nisan 2027, Antalya Kongre Merkezi · Salt çoğunluk aranmaz.", "meta", "ink.500", { x: 120, y: y + 108 });

S.footer(pb, 1976);

return JSON.stringify(S.end("03-yonetim"));
