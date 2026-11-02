/**
 * 16 — Makale detayı. Reading surface: the body sits on one bone sheet, the TOC rail and
 * related rows stay on the dark canvas.
 */
const S = IK;
const pb = S.start("İçerik", "16-makale", 2540);

S.masthead(pb, "Haberler");
S.crumbs(pb, ["Haberler", "Kongre", "Program yayınlandı"], 120, 136);
S.text(pb, "a kicker", "KONGRE · 12 MART 2027", "label", "red.700", { x: 120, y: 176 });
S.text(pb, "a title", "Program yayınlandı: 96 oturum, dört salon", "h2", "ink.900", { x: 120, y: 200, w: 760 });
S.text(pb, "a meta", "Dr. Selin Aydın · 6 dk okuma · 12 Mart 2027", "meta", "ink.500", { x: 120, y: 316 });
S.text(pb, "a share label", "Paylaş", "label", "ink.500", { x: 120, y: 352 });
S.link(pb, "a share li", "LinkedIn", 200, 348, "ink.900");
S.link(pb, "a share x", "X", 312, 348, "ink.900");
S.link(pb, "a share mail", "e-posta", 360, 348, "ink.900");
S.rule(pb, "a rule", 120, 400, 1200, "line.strong", 1);

S.photo(pb, "img-team", 0, 432, 1440, 420);
S.text(pb, "img-team caption", "Kongre programı çalışması, Ankara", "meta", "ink.500", { x: 120, y: 864, w: 1200 });

/* ------------------------------------------------------------------ TOC rail (canvas) */
S.text(pb, "rail label", "BU YAZIDA", "label", "ink.500", { x: 120, y: 932 });
S.rect(pb, "rail active", 120, 972, 4, 20, "red.600");
["Program nasıl değişti", "Konsey oturumları", "Salonlar ve tercüme", "Kayıt ve ücretler"].forEach((t, i) => {
  S.text(pb, "rail " + i, t, "body", i === 0 ? "ink.900" : "ink.600", { x: 136, y: 972 + i * 40, w: 220 });
});

/* ---------------------------------------------------------- article body (bone sheet) */
const sheet = S.sheet(pb, "article sheet", 420, 932, 900, 860);
const cx = 468;
const cw = 804;

/* One paragraph rhythm for the whole sheet. The old fixed y's left 75px of air
   between p1 and p2 but 33px between p4 and p5 in the same column (lint:
   intra-card gap 80px). PARA_GAP 30 is measured between ink boxes, which is
   what the eye reads: 26 + 30 - 19.5 = 36.5px of air, under the 1.5x line
   "drifting copy" threshold. A paragraph's height comes from its own line
   count, at the measured 6.54px/char for this face. */
const PARA_GAP = 30, BODY_LINE = 26;
const CHARS_PER_LINE = Math.floor(cw / 6.6);
const linesOf = (t) => Math.max(1, Math.ceil(String(t).length / CHARS_PER_LINE));
let by = 980;
const para = (name, copy) => {
  S.text(sheet, name, copy, "body", "doc.text", { x: cx, y: by, w: cw });
  by += linesOf(copy) * BODY_LINE + PARA_GAP;
};

para("p1", "Program dört gün, 96 oturum, dört paralel salonla yayında. Konsey oturumları günün 11:00 ve 16:00 bloklarında.");
para("p2", "Salonlar A'dan D'ye; C ve D salonlarında çeviri kabini var.");

/* The pull quote is its own block: bar, quote and attribution in one container,
   so its generous air belongs to the quote and not to the paragraph above it. */
by += 8;
const quote = S.board(sheet, "quote block", cx, by, cw - 44, 128);
S.rect(quote, "q bar", cx, by, 4, 128, "red.600");
S.text(quote, "q text", "“İyi program salonda belli olur.”", "lead", "doc.text", { x: cx + 28, y: by + 24, w: 700 });
S.text(quote, "q by", "Prof. Dr. Murat Şen · Genel sekreter", "meta", "doc.muted", { x: cx + 28, y: by + 104 });
by += 128 + 40;

para("p3", "Konsey oturumları toplam 14 saat; bunun 6 saati vaka tartışması. Kabul edilen 780 bildirinin 240'ı konsey havuzunda değerlendiriliyor.");

by += 8;
S.text(sheet, "dl label", "SAYILARLA PROGRAM", "label", "doc.muted", { x: cx, y: by });
[["96", "oturum"], ["14 saat", "konsey"], ["240", "konsey bildirisi"]].forEach((d, i) => {
  S.text(sheet, "dl v " + i, d[0], "figure", "doc.text", { x: cx + i * 248, y: by + 32, w: 232 });
  S.text(sheet, "dl l " + i, d[1], "meta", "doc.muted", { x: cx + i * 248, y: by + 72, w: 232 });
});
S.rule(sheet, "dl rule", cx, by + 116, cw, "doc.rule", 1);
by += 116 + 32;

para("p4", "Kayıt ücretleri 31 Ocak 2027'ye kadar erken dönem tarifesinde. Üyeler için fark 700 TL; asistan tarifesinde 500 TL, öğrenci tarifesinde 300 TL. Konaklama kayıtla birlikte yapılıyor.");
para("p5", "Salon C ve D'de simultane çeviri var; kulaklık kayıt sırasında talep ediliyor. Bildiri sunumları 8 dakika sürer, ardından 4 dakika tartışma yapılır.");

/* the sheet ends where its copy ends, plus the same 48px it opens with */
const sheetH = S.snap(by - PARA_GAP + 48 - 932);
sheet.resize(900, sheetH);
const sheetBottom = 932 + sheetH;

/* ------------------------------------------------------------------- ilgili (canvas) */
const relY = sheetBottom + 48;
S.text(pb, "rel label", "İLGİLİ", "label", "red.700", { x: 120, y: relY });
[
  ["Bildiri gönderimi için son iki hafta", "2 dk · Kongre"],
  ["Hipertansiyon kılavuzu taslağı görüşe açıldı", "5 dk · Kılavuz"],
  ["STE kredileri e-Devlet'e işlendi", "3 dk · Akademi"],
].forEach((r, i) => {
  const ry = relY + 36 + i * 56;
  S.text(pb, "rel t " + i, r[0], "body", "ink.900", { x: 120, y: ry, w: 700 });
  S.text(pb, "rel m " + i, r[1], "meta", "ink.500", { x: 900, y: ry + 4, w: 420, align: "right" });
  S.rule(pb, "rel r " + i, 120, ry + 40, 1200, "line.soft");
});

/* ------------------------------------------------------------------- yazar (surface.alt) */
/* 24px top and bottom: the old 120px card left 48px of white under the bio
   against 24 above it (lint: dead space 50px) */
const auY = relY + 36 + 2 * 56 + 40 + 40;
const author = S.board(pb, "author", 120, auY, 1200, 100, "surface.alt");
S.text(author, "au name", "Dr. Selin Aydın", "bodyMed", "ink.900", { x: 152, y: auY + 24 });
S.text(author, "au bio", "Kardiyoloji asistanı, Ankara Üniversitesi. İHKD genç hekimler komisyonu üyesi.", "meta", "ink.600", { x: 152, y: auY + 52, w: 700 });

const footY = auY + 100 + 32;
S.footer(pb, footY);
pb.resize(1440, footY + 320);

return JSON.stringify(S.end("16-makale"));
