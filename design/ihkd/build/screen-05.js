/**
 * 05 — Çalışma grubu detayı. Kardiyovasküler görüntüleme.
 *
 * All repeating rows (join, facts, plan, events, pubs) go through S.rows():
 * one pitch per list, separators on block bottoms, positions accumulate —
 * no hand-written rule y anywhere.
 */
const S = IK;
const pb = S.start("Kurumsal", "05-grup-detay", 2684);

S.masthead(pb, "Çalışma grupları");
S.crumbs(pb, ["Dernek", "Çalışma grupları", "Kardiyovasküler görüntüleme"], 120, 132);

S.text(pb, "g label", "ÇALIŞMA GRUBU · KURULUŞ 2009", "label", "red.700", { x: 120, y: 180 });
S.text(pb, "g title", "Kardiyovasküler görüntüleme", "h2", "ink.900", { x: 120, y: 204, w: 900 });
S.text(pb, "g chair", "Başkan Doç. Dr. Elif Karaca · Sekreter Dr. Onur Kılıç · 412 üye", "meta", "ink.500", { x: 120, y: 268, w: 760 });
S.btn(pb, "g cta", "Gruba katıl", 1104, 204, 216, 52, "primary");
S.rule(pb, "g rule", 120, 316, 1200, "line.strong", 1);

S.text(pb, "g lede",
  "Grup, ekokardiyografi raporunun standart dilini yazar: aynı rapor, her klinikte aynı anlam.",
  "lead", "ink.700", { x: 120, y: 348, w: 720 });

/* ------------------------------------------------------------ üyelik koşulları */
S.text(pb, "join label", "ÜYELİK KOŞULLARI", "label", "red.700", { x: 120, y: 500 });
S.rows(pb, "join", 120, 540, 700, [
  "Dernek üyesi olmak (aidat güncel)",
  "Kardiyoloji veya iç hastalıkları uzmanlığı",
  "Yılda en az bir toplantıya katılım",
].map((c, i) => ({
  h: 40,
  draw(yRow) {
    S.rect(pb, "join dot " + i, 120, yRow + 6, 6, 6, "red.600");
    S.text(pb, "join text " + i, c, "body", "ink.700", { x: 144, y: yRow, w: 700 });
  },
})), { rule: "line.soft" });

/* ------------------------------------------------------------------ künye */
const facts = S.board(pb, "facts", 940, 348, 380, 320, "surface.alt");
S.text(facts, "facts label", "GRUP KÜNYESİ", "label", "red.700", { x: 972, y: 380 });
const rows = [
  ["Kuruluş", "2009"],
  ["Üye", "412"],
  ["Toplantı", "6 / yıl"],
  ["Başkan", "Doç. Dr. Elif Karaca"],
];
S.rows(facts, "fact", 972, 420, 316, rows.map((r, i) => ({
  h: 56,
  draw(yRow) {
    S.text(facts, "fact k " + i, r[0], "meta", "ink.500", { x: 972, y: yRow });
    S.text(facts, "fact v " + i, r[1], "body", "ink.900", { x: 972, y: yRow + 20, w: 316 });
  },
})), { rule: "line.soft" });

/* ------------------------------------------------------------ 2027 planı */
let y = S.head(pb, 120, 760, "2027 PLANI", "2027 çalışma planı");
const plan = [
  ["Mart", "Ekokardiyografi raporlama standardı, 2. sürüm", "Çalışma grubu yayını"],
  ["Nisan", "Kongrede dört saatlik uygulamalı oturum", "Salon C · 22 Nisan 2027 · 14:00"],
  ["Haziran", "BT ve MR'da kontrast protokolü anketi", "41 il temsilciliğine gönderilecek"],
  ["Ekim", "Yıllık görüntüleme sempozyumu", "İzmir · 2 gün · 180 kontenjan"],
];
y = S.rows(pb, "plan", 120, y, 1200, plan.map((p, i) => ({
  h: 64,
  draw(yRow) {
    S.text(pb, "plan month " + i, p[0], "data", "ink.500", { x: 120, y: yRow + 4 });
    S.text(pb, "plan title " + i, p[1], "bodyMed", "ink.900", { x: 240, y: yRow, w: 800 });
    S.text(pb, "plan note " + i, p[2], "meta", "ink.500", { x: 240, y: yRow + 26, w: 800 });
  },
})), { rule: "line.soft" });

/* ------------------------------------------------------------- etkinlikler */
y = S.head(pb, 120, y + 48, "ETKİNLİKLER", "Etkinlikler");
const events = [
  ["22 Nisan 2027", "Kongre oturumu · Salon C", "Antalya"],
  ["18 Haziran 2027", "Vaka konseyi · çevrim içi", "19:00"],
  ["02 Ekim 2027", "Görüntüleme sempozyumu", "İzmir"],
];
y = S.rows(pb, "ev", 120, y, 1200, events.map((e, i) => ({
  h: 48,
  draw(yRow) {
    S.text(pb, "ev date " + i, e[0], "data", "ink.500", { x: 120, y: yRow + 2 });
    S.text(pb, "ev title " + i, e[1], "body", "ink.900", { x: 300, y: yRow, w: 560 });
    S.text(pb, "ev where " + i, e[2], "meta", "ink.500", { x: 1000, y: yRow + 4, w: 320, align: "right" });
  },
})), { rule: "line.soft" });

/* ---------------------------------------------------------------- yayınlar */
y = S.head(pb, 120, y + 48, "YAYINLAR", "Yayınlar");
const pubs = [
  ["Ekokardiyografi raporlama standardı", "2026 · 24 sayfa"],
  ["Kontrastlı BT'de böbrek fonksiyonu kontrol listesi", "2025 · 8 sayfa"],
  ["Stres ekokardiyografi uygulama rehberi", "2024 · 16 sayfa"],
];
y = S.rows(pb, "pub", 120, y, 1200, pubs.map((p, i) => ({
  h: 48,
  draw(yRow) {
    S.text(pb, "pub title " + i, p[0], "body", "ink.900", { x: 120, y: yRow, w: 640 });
    S.text(pb, "pub meta " + i, p[1], "data", "ink.500", { x: 800, y: yRow + 2, w: 240 });
    S.text(pb, "pub fmt " + i, "İndir", "nav", "red.700", { x: 1220, y: yRow, w: 100, align: "right" });
  },
})), { rule: "line.soft" });

S.photo(pb, "img-cath", 120, y + 48, 1200, 300, "Kateter laboratuvarı, Ankara");
const fy05 = S.snap(y + 48 + 300 + 48);
S.footer(pb, fy05);
pb.resize(1440, fy05 + 320);

return JSON.stringify(S.end("05-grup-detay"));
