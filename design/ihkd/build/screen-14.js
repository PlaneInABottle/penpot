/**
 * 14 — Dergi sayısı. Cover photo, the issue's contents on a bone sheet, editor's note,
 * archive and author notes.
 */
const S = IK;
const pb = S.start("Akademi", "14-dergi", 2000);

S.masthead(pb, "Yayın");
S.pageHead(pb, "KARDİYOVASKÜLER KLİNİK", "Cilt 12 · Sayı 1 · Mart 2027",
  "Üç ayda bir, hakemli, TR Dizin. Editör: Prof. Dr. Nihal Özkan.",
  { w: 900, ledeW: 760 });

S.photo(pb, "img-issue", 120, 412, 360, 480, "Kardiyovasküler Klinik, cilt 12 kapak");
S.btn(pb, "j cta", "Sayıyı oku", 120, 952, 200, 48, "primary");

/* ------------------------------------------------------------------ içindekiler */
const sx = 560, sy = 412;
const toc = S.sheet(pb, "toc sheet", sx, sy, 760, 616);
S.text(toc, "toc label", "İÇİNDEKİLER", "label", "doc.muted", { x: sx + 48, y: sy + 48 });
S.text(toc, "toc h", "SAYFA · TÜR", "label", "doc.muted", { x: sx + 512, y: sy + 48, w: 200, align: "right" });
S.rule(toc, "toc rule", sx + 48, sy + 80, 664, "doc.rule");
const rows = [
  ["12", "Editörden", "Kanıt, kılavuz ve klinik arasındaki mesafe", "Prof. Dr. Nihal Özkan"],
  ["18", "Orijinal", "STE olmayan hastada BKA kararı: 1.284 hasta", "Dr. Elif Karaca, Dr. Deniz Arslan"],
  ["28", "Orijinal", "KKY'de SGLT2 inhibitörleri: gerçek yaşam verisi", "Prof. Dr. Ayşe Tunç, Dr. Onur Kılıç"],
  ["41", "Derleme", "Genç sporcularda EKG taramasının maliyeti", "Prof. Dr. Sema Yıldız"],
  ["52", "Olgu", "Nefrotik sendromda kalp yetersizliği", "Dr. Zeynep Kaya"],
  ["58", "Mektup", "Hipertansiyon kılavuzuna dair iki not", "Prof. Dr. Kerem Yalçın"],
];
rows.forEach((t, i) => {
  const ry = sy + 104 + i * 84;
  S.text(toc, "toc p " + i, t[0], "dataLg", "doc.text", { x: sx + 48, y: ry });
  S.text(toc, "toc k " + i, t[1], "label", "doc.muted", { x: sx + 112, y: ry + 4 });
  S.text(toc, "toc t " + i, t[2], "body", "doc.text", { x: sx + 252, y: ry, w: 460 });
  S.text(toc, "toc a " + i, t[3], "meta", "doc.muted", { x: sx + 252, y: ry + 28, w: 460 });
  S.rule(toc, "toc r " + i, sx + 48, ry + 68, 664, "doc.rule");
});

/* -------------------------------------------------------------------- editör */
/* the attribution belongs to the quote: 46px under its last line, and the card
   ends 26px under the signature (it sat 70px below the quote with the same pad,
   so the signature floated — lint: intra-card gap 70px, then dead space) */
const ed = S.board(pb, "editor", 120, 1072, 1200, 204, "surface.alt");
S.text(ed, "ed label", "EDİTÖRDEN", "label", "red.700", { x: 152, y: 1096 });
S.text(ed, "ed text", "“Bu sayıda kliniğin üç güncel sorusuna yanıt arayan çalışmalar var. Kılavuz, yanıtları tek kararda toplar.”", "lead", "ink.800", { x: 152, y: 1124, w: 760 });
S.text(ed, "ed by", "Prof. Dr. Nihal Özkan · Editör", "meta", "ink.500", { x: 152, y: 1232 });

/* --------------------------------------------------------------------- arşiv */
S.text(pb, "arch label", "ARŞİV", "label", "red.600", { x: 120, y: 1352 });
const arch = [["2026", "Cilt 11 · 4 sayı"], ["2025", "Cilt 10 · 4 sayı"], ["2024", "Cilt 9 · 4 sayı"], ["2023", "Cilt 8 · 4 sayı"]];
arch.forEach((a, i) => {
  const ay = 1388 + i * 44;
  S.text(pb, "arch y " + i, a[0], "data", "ink.900", { x: 120, y: ay });
  S.text(pb, "arch m " + i, a[1], "meta", "ink.500", { x: 200, y: ay + 2, w: 320 });
  S.text(pb, "arch c " + i, "Aç →", "meta", "red.700", { x: 520, y: ay + 2, w: 80, align: "right" });
});

S.vrule(pb, "arch div", 700, 1352, 220, "line.soft");
S.text(pb, "sub label", "YAZARA NOTLAR", "label", "red.600", { x: 740, y: 1352 });
["Yapılandırılmış özet zorunlu (AMAÇ/YÖNTEM/BULGULAR/SONUÇ).", "Etik kurul numarası ve çıkar çatışması beyanı ekte.", "Değerlendirme süresi ortalama 28 gün."].forEach((t, i) => {
  S.text(pb, "sub " + i, t, "body", "ink.700", { x: 740, y: 1388 + i * 64, w: 540 });
});
S.link(pb, "sub cta", "Yazım kuralları", 740, 1588, "ink.900");

S.footer(pb, 1680);

return JSON.stringify(S.end("14-dergi"));
