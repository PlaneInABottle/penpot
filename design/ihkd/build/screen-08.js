/**
 * 08 — Bildiri gönderimi. Deadline, süreç, konular, form, kurallar.
 */
const S = IK;
const pb = S.start("Kongre", "08-bildiri", 2566);

S.masthead(pb, "Kongre");
S.pageHead(pb, "BİLDİRİ", "Bildiri gönderimi",
  "Özetler kör değerlendirmeye girer; kabul edilen bildiriler 8 dakikalık sözlü sunum veya poster olarak programlanır.",
  { w: 900, ledeW: 720 });

/* ------------------------------------------------------------------ deadline */
S.board(pb, "deadline", 120, 396, 1200, 72, "red.100");
S.rect(pb, "dl bar", 120, 396, 4, 72, "red.600");
S.text(pb, "dl label", "SON GÖNDERİM", "label", "red.700", { x: 148, y: 414 });
S.text(pb, "dl value", "15 Şubat 2027, 23:59 (TSİ)", "bodyMed", "ink.900", { x: 300, y: 412 });
S.text(pb, "dl note", "Süre uzatılmayacaktır.", "meta", "ink.700", { x: 900, y: 416, w: 400, align: "right" });

/* -------------------------------------------------------------------- süreç */
let y = S.head(pb, 120, 524, "SÜREÇ", "Dört adım, dört tarih");
const steps = [
  ["01", "Özet gönderimi", "15 Şubat 2027"],
  ["02", "Kör değerlendirme", "16–28 Şubat 2027"],
  ["03", "Kabul bildirimi", "8 Mart 2027"],
  ["04", "Tam metin", "5 Nisan 2027"],
];
steps.forEach((st, i) => {
  const sx = 120 + i * 306;
  S.text(pb, "st n " + i, st[0], "data", "ink.500", { x: sx, y: y });
  S.text(pb, "st h " + i, st[1], "bodyMed", "ink.900", { x: sx, y: y + 24, w: 260 });
  S.text(pb, "st d " + i, st[2], "meta", "ink.500", { x: sx, y: y + 48, w: 260 });
  if (i < 3) S.rule(pb, "st bar " + i, sx + 260, y + 32, 40, "line.strong");
});

/* ------------------------------------------------------------------- konular */
const topicsY = S.head(pb, 120, 788, "KONULAR", "Hangi konu?");
const topics = ["Kalp yetersizliği", "Görüntüleme", "Aritmi", "Hipertansiyon", "Metabolik", "Geriatri", "Kardiyo-onkoloji", "Yapısal kalp"];
let tox = 120;
let toy = topicsY;
topics.forEach((tp, i) => {
  const w = Math.round(tp.length * 8.6) + 32;
  if (tox + w > 1320) { tox = 120; toy += 44; }
  const b = S.board(pb, "topic " + i, tox, toy, w, 36, "white");
  S.stroke(b, "line.strong", 1);
  S.text(pb, "topic text " + i, tp, "label", "ink.700", { x: tox + 16, y: toy + 12 });
  tox += w + 8;
});

/* ---------------------------------------------------------------------- form */
const f = S.head(pb, 120, toy + 84, "GÖNDERİM", "Özet formu");
S.field(pb, "f title", "BİLDİRİ BAŞLIĞI", "Örn. STE olmayan hastada BKA kararı", 120, f, 760, { placeholder: true });
S.field(pb, "f track", "KONU", "Kalp yetersizliği", 920, f, 400);
S.field(pb, "f a1", "YAZAR 1 · SUNAN", "Aydın S.", 120, f + 92, 360);
S.field(pb, "f a2", "YAZAR 2", "Tunç A.", 520, f + 92, 360);
S.field(pb, "f a3", "YAZAR 3", "Şen M.", 920, f + 92, 400);
S.field(pb, "f org", "KURUM", "Hacettepe Üniversitesi Tıp Fakültesi", 120, f + 184, 760);

const ay = f + 264;
S.text(pb, "f abs label", "ÖZET", "label", "ink.500", { x: 120, y: ay });
S.text(pb, "f abs text",
  "Amaç: Kalp yetersizliği polikliniğinde izlenen hastalarda SGLT2 inhibitörü başlanan ve başlanmayan grupların 12 aylık hastane yatışını karşılaştırmak. Yöntem: 2019–2025 arası 1.284 hasta, geriye dönük kohort. Bulgular: Yatış oranı %18,4'e karşı %26,1 (p=0,003). Sonuç: Gerçek yaşam verisi, randomize çalışmaların etkisini destekliyor.",
  "body", "ink.700", { x: 120, y: ay + 24, w: 1200 });
S.rule(pb, "f abs line", 120, ay + 112, 1200, "line.strong", 1);
S.text(pb, "f abs count", "248/300 kelime", "data", "ink.500", { x: 1080, y: ay + 120, w: 240, align: "right" });

const uy = ay + 168;
S.text(pb, "up text", "Özet dosyası (DOCX veya PDF, en fazla 5 MB)", "body", "ink.600", { x: 120, y: uy });
S.text(pb, "up cta", "Dosya seç", "nav", "red.700", { x: 1120, y: uy, w: 200, align: "right" });
S.rule(pb, "up rule", 120, uy + 36, 1200, "line.soft");

const cy = uy + 60;
S.rect(pb, "f check", 120, cy, 16, 16, "surface.alt", { stroke: "line.strong" });
S.text(pb, "f check label", "KVKK aydınlatma metnini okudum; verilerin değerlendirme için işlenmesini onaylıyorum.", "meta", "ink.600", { x: 148, y: cy - 2, w: 1000 });

const by = cy + 56;
S.btn(pb, "f draft", "Taslak kaydet", 120, by, 200, 52, "secondary");
S.btn(pb, "f send", "Gönder", 1004, by, 316, 52, "primary");

/* ------------------------------------------------------------- kurallar + SSS */
const ry = S.head(pb, 120, by + 100, "KURALLAR", "Kurallar ve sorular");
const rules = [
  "Özet 300 kelimeyi geçmez; başlık ve kaynaklar sayılmaz.",
  "En fazla 8 yazar; sunan yazar işaretlenir.",
  "Etik kurul onay numarası zorunludur.",
  "Ticari ad kullanılmaz; jenerik isim tercih edilir.",
  "Kabul edilen bildiri için en az bir yazar kayıtlı olmalıdır.",
  "Geri çekme 20 Mart 2027'ye kadar yapılabilir.",
];
rules.forEach((r, i) => {
  S.text(pb, "rule " + i, r, "body", "ink.700", { x: 120, y: ry + i * 40, w: 560 });
});

S.text(pb, "faq label", "SSS", "label", "red.700", { x: 760, y: ry });
const faqs = [
  ["Poster ve sözlü ayrımı nasıl yapılıyor?", "Değerlendirme puanına göre bilim kurulu karar verir."],
  ["Özet dili İngilizce olabilir mi?", "Türkçe zorunlu; İngilizce özet isteğe bağlı."],
  ["Kabul sonrası yazar değişir mi?", "Yalnızca sıralama düzeltmesi yapılabilir."],
  ["Sunum süresi ne kadar?", "8 dakika sunum, 4 dakika tartışma."],
];
/* The answer is content, not meta (TRIAGE 08-bildiri: 13px grey under a 16px
   question read as fine print at 1:1). 16px body needs its own rhythm: the
   answer box sits 26px under the question, the rule 64px, the row 72px. */
faqs.forEach((q, i) => {
  const fy = ry + 32 + i * 72;
  S.text(pb, "faq q " + i, q[0], "bodyMed", "ink.900", { x: 760, y: fy, w: 520 });
  S.text(pb, "faq a " + i, q[1], "body", "ink.600", { x: 760, y: fy + 26, w: 520 });
  S.rule(pb, "faq rule " + i, 760, fy + 64, 520, "line.soft");
});

/* the footer docks to the last rule (the page grew 64px) */
const FAQ_END = ry + 32 + 4 * 72 + 64;
S.footer(pb, FAQ_END);
pb.resize(S.W, S.snap(FAQ_END + 332));

return JSON.stringify(S.end("08-bildiri"));
