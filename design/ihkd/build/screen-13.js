/**
 * 13 — Kılavuzlar. Documents with a decision surface: a featured guideline on a bone
 * sheet with its ECG calibration, ten guideline rows, pocket cards, method note.
 */
const S = IK;
const pb = S.start("Akademi", "13-kilavuzlar", 2400);

S.masthead(pb, "Akademi");
S.pageHead(pb, "KILAVUZLAR", "Klinik kılavuzlar",
  "On kılavuz, dernek imzasıyla. Her satır yıl, kapsam, kanıt düzeyi ve dosya boyutunu verir.",
  { w: 900, ledeW: 760 });

S.field(pb, "search", "ARA", "Kılavuz, kanıt düzeyi veya yıl", 120, 400, 400, { placeholder: true });

let fx = 120;
["Tümü 10", "2027 3", "2026 2", "2025 2", "2024 3"].forEach((f, i) => {
  const w = Math.round(f.length * 8.6) + 32;
  const b = S.board(pb, "yr " + i, fx, 488, w, 34, i === 0 ? "red.600" : "white");
  if (i) S.stroke(b, "line.strong", 1);
  S.text(b, "yr text " + i, f, "label", i === 0 ? "on.red" : "ink.700", { x: fx + 16, y: 497 });
  fx += w + 8;
});

/* ------------------------------------------------------------------ öne çıkan */
const sx = 120, sy = 572;
const sheet = S.sheet(pb, "featured sheet", sx, sy, 760, 360);
S.text(sheet, "feat label", "2027 · İHKD KILAVUZU", "label", "doc.muted", { x: sx + 56, y: sy + 44 });
S.text(sheet, "feat title", "Hipertansiyon tanı ve tedavi kılavuzu", "h3", "doc.text", { x: sx + 56, y: sy + 72, w: 648 });
S.text(sheet, "feat body", "Ev ölçümü, ofis dışı tansiyon, tedavi eşikleri ve dirençli hipertansiyonda dördüncü ilaç.", "body", "doc.muted", { x: sx + 56, y: sy + 120, w: 648 });
S.ecg(sheet, "feat ecg", sx + 56, sy + 188, 648, 64, "red.600");
S.text(sheet, "feat cal", "25 mm/s · 10 mm/mV", "data", "doc.muted", { x: sx + 56, y: sy + 268 });
S.text(sheet, "feat meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "doc.muted", { x: sx + 300, y: sy + 268 });
S.btn(sheet, "feat dl", "Kılavuzu indir", sx + 56, sy + 300, 200, 48, "primary");
S.link(sheet, "feat sum", "Özet", sx + 284, sy + 314, "doc.text");
S.photo(pb, "img-desk", 912, 572, 408, 320, "EKG kaydı · 25 mm/s · 10 mm/mV");

/* -------------------------------------------------------------------- liste */
S.head(pb, 120, 976, "KILAVUZ LİSTESİ", "Yıl · kanıt · sayfa", { index: "2024–2027" });
const guides = [
  ["Hipertansiyon tanı ve tedavi", "2027 · Kanıt A · 48 sayfa · 3,2 MB"],
  ["Kalp yetersizliği tanı ve tedavi", "2027 · Kanıt A · 62 sayfa · 4,1 MB"],
  ["Atriyal fibrilasyonda antikoagülasyon", "2027 · Kanıt A · 38 sayfa · 2,6 MB"],
  ["Lipit bozuklukları ve LDL hedefi", "2026 · Kanıt B · 44 sayfa · 3,0 MB"],
  ["Kronik böbrek hastalığında kalp", "2026 · Kanıt B · 36 sayfa · 2,2 MB"],
  ["Geriatride çoklu ilaç kullanımı", "2025 · Kanıt B · 28 sayfa · 1,7 MB"],
  ["Kardiyo-onkolojide izlem", "2025 · Kanıt C · 32 sayfa · 2,0 MB"],
  ["Yapısal kalp hastalıklarında girişim", "2024 · Kanıt A · 54 sayfa · 3,5 MB"],
  ["Sporcularda kardiyak tarama", "2024 · Kanıt B · 26 sayfa · 1,5 MB"],
  ["Tromboz ve köprüleme kararları", "2024 · Kanıt C · 30 sayfa · 1,9 MB"],
];
guides.forEach((g, i) => {
  const gy = 1120 + i * 64;
  S.text(pb, "gd title " + i, g[0], "bodyMed", "ink.900", { x: 120, y: gy, w: 560 });
  S.text(pb, "gd meta " + i, g[1], "data", "ink.500", { x: 700, y: gy + 2, w: 380, align: "right" });
  S.text(pb, "gd dl " + i, "İndir", "nav", "red.600", { x: 1120, y: gy, w: 90, align: "right" });
  S.text(pb, "gd sum " + i, "Özet", "meta", "ink.500", { x: 1220, y: gy + 2, w: 100, align: "right" });
  S.rule(pb, "gd rule " + i, 120, gy + 44, 1200, "line.soft");
});

/* ------------------------------------------------------------- cep kartları */
const py = 1824;
S.text(pb, "pocket label", "CEP KARTLARI", "label", "red.600", { x: 120, y: 1784 });
const pockets = [
  ["KKY tedavi basamakları", "1 sayfa · A6"],
  ["Antikoagülasyon doz tablosu", "1 sayfa · A6"],
  ["Hipertansiyon eşikleri", "1 sayfa · A6"],
];
pockets.forEach((p, i) => {
  const px = 120 + i * 410;
  /* white card + hairline: these are content cards in a grid, and surface.alt
     is the inset/pocket-card token elsewhere, but three grey tiles beside the
     page's white rows read as a different material without a reason (lint:
     same-size alt cards beside a white card) */
  const pk = S.board(pb, "pocket " + i, px, py, 380, 136, "white");
  S.stroke(pk, "line.soft", 1);
  S.text(pk, "pk title " + i, p[0], "bodyMed", "ink.900", { x: px + 24, y: py + 24, w: 332 });
  S.text(pk, "pk meta " + i, p[1], "meta", "ink.500", { x: px + 24, y: py + 56, w: 332 });
  S.link(pk, "pk dl " + i, "PDF indir →", px + 24, py + 92, "red.700");
});

S.text(pb, "method", "Yöntem: her kılavuz GRADE ile derecelendirilir; kanıt düzeyi ve öneri gücü tabloda belirtilir. Çıkar çatışması beyanları ek 1'dedir.", "meta", "ink.500", { x: 120, y: 2012, w: 900 });

S.footer(pb, 2080);

return JSON.stringify(S.end("13-kilavuzlar"));
