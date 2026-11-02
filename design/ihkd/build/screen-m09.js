/**
 * 09 — Kayıt ve ücretler, mobil 390 (`09-kayit-m`, sayfa `Mobil`).
 *
 *   python3 design/ihkd/build/build.py screen-m09
 *
 * Masaüstü 09'un içeriği (5 ücret satırı, dahil/değil, grup kaydı, iptal
 * koşulları) + kayıt formu tek kolonda. Hiyerarşiyi sayı taşır: erken kayıt
 * son günü 80px, ücret satırları 16px mono.
 *
 * Tek doygun buton alt çubukta (`reg cta`); üye satırı red.050 tint, doygun
 * değil. Fotoğraf yok: form ekranı kendi belgesi.
 */
const S = IK;
const M = IKM;
const pb = M.start("Mobil", "09-kayit-m", 3000);

M.masthead(pb);

/* ------------------------------------------------------------------ sayfa başı */
S.text(pb, "p label", "ERKEN KAYIT · SON GÜN", "label", "ink.500", { x: M.G, y: 96 });
S.text(pb, "p title a", "31 Ocak", "display", "ink.900", { x: M.G, y: 120, w: M.CW });
S.text(pb, "p title b", "Kayıt ve ücretler", "h3", "ink.900", { x: M.G, y: 214, w: M.CW });
S.text(pb, "p lede", "Erken kayıt 31 Ocak 2027'de kapanır. Ücretler kişi başı ve KDV dahildir.",
  "lead", "ink.600", { x: M.G, y: 268, w: M.CW });
S.rule(pb, "p rule", M.G, 392, M.CW, "line.strong", 2);

/* --------------------------------------------------------------------- ücretler */
let y = 416;
S.text(pb, "fee label", "ÜCRETLER · ERKEN · STANDART · GEÇ", "label", "ink.500", { x: M.G, y: y });
const fees = [
  ["Üye", "3.400 TL", "ÜYE · Standart 4.100 TL · Geç 4.800 TL", true],
  ["Üye olmayan", "4.600 TL", "Standart 5.400 TL · Geç 6.100 TL", false],
  ["Asistan", "1.900 TL", "Standart 2.400 TL · Geç 2.900 TL", false],
  ["Öğrenci", "1.200 TL", "Standart 1.500 TL · Geç 1.900 TL", false],
  ["Hemşire / teknisyen", "1.600 TL", "Standart 2.000 TL · Geç 2.400 TL", false],
];
y = S.rows(pb, "fee", M.G, y + 28, M.CW, fees.map((f, i) => ({
  h: 84,
  draw(yRow) {
    if (f[3]) S.rect(pb, "fee tint " + i, M.G, yRow + 4, M.CW, 76, "red.050");
    S.text(pb, "fee name " + i, f[0], "bodyMed", "ink.900", { x: M.G + 12, y: yRow + 16, w: 200 });
    S.text(pb, "fee a " + i, f[1], "dataLg", "ink.900", { x: M.G + M.CW - 136, y: yRow + 14, w: 124, align: "right" });
    S.text(pb, "fee meta " + i, f[2], "meta", "ink.500", { x: M.G + 12, y: yRow + 44, w: M.CW - 24 });
  },
})), { rule: "line.soft" });

/* -------------------------------------------------------------- dahil / değil */
y += 24;
S.text(pb, "inc label", "ÜCRETE DAHİL", "label", "red.700", { x: M.G, y: y });
y = S.bullets(pb, "inc", M.G, y + 28, M.CW, [
  "Tüm bilimsel oturumlar", "Kongre çantası ve program", "22–25 Nisan öğle yemekleri",
  "Kabul edilen bildiri sunumu", "STE kredisi (24 saat)", "Salon C–D çeviri hizmeti",
], { pad: 3, textX: 24 });
y += 20;
S.text(pb, "exc label", "DAHİL DEĞİL", "label", "ink.500", { x: M.G, y: y });
["Konaklama ve ulaşım", "21 Nisan kurs günü", "Akşam programı ve gala"].forEach((c, i) => {
  S.text(pb, "exc " + i, c, "body", "ink.600", { x: M.G, y: y + 28 + i * 32, w: M.CW });
});
y += 28 + 3 * 32 + 24;

/* ---------------------------------------------------------------- grup kaydı */
const GH = 272;
const grp = S.board(pb, "group", M.G, y, M.CW, GH, "surface.alt");
S.text(grp, "grp label", "GRUP KAYDI", "label", "red.700", { x: M.G + 20, y: y + 24 });
S.text(grp, "grp title", "10 kişiden fazla ekipler için tek fatura", "bodyMed", "ink.900",
  { x: M.G + 20, y: y + 48, w: M.CW - 40 });
S.text(grp, "grp body", "Kurum adına toplu kayıt, tek fatura ve kişi bazlı STE belgesi. Form 15 Mart 2027'ye kadar gönderilmeli.",
  "body", "ink.600", { x: M.G + 20, y: y + 100, w: M.CW - 40 });
S.link(grp, "grp cta", "Grup kayıt formu", M.G + 20, y + 224, "ink.900");
y += GH + 24;

/* -------------------------------------------------------------- iptal koşulları */
S.text(pb, "can label", "İPTAL KOŞULLARI", "label", "red.700", { x: M.G, y: y });
const cancel = [
  ["31 Ocak 2027'ye kadar", "Ücretin tamamı iade edilir."],
  ["1–31 Mart 2027", "Ücretin %50'si iade edilir."],
  ["1 Nisan 2027 sonrası", "İade yapılmaz; kayıt devredilebilir."],
];
y = S.rows(pb, "can", M.G, y + 28, M.CW, cancel.map((c, i) => ({
  h: 84,
  draw(yRow) {
    S.text(pb, "can when " + i, c[0], "data", "ink.500", { x: M.G, y: yRow + 16, w: M.CW });
    S.text(pb, "can what " + i, c[1], "body", "ink.700", { x: M.G, y: yRow + 40, w: M.CW });
  },
})), { rule: "line.soft" });

/* ---------------------------------------------------------------- kayıt formu */
y = M.sectionHead(pb, y + M.SECTION, "KAYIT FORMU", "Katılımcı bilgileri");
y = M.field(pb, "f ad", "AD SOYAD", "Dr. Selin Aydın", y);
y = M.field(pb, "f mail", "E-POSTA", "selin.aydin@ankara.edu.tr", y);
y = M.field(pb, "f kurum", "KURUM", "Ankara Üniversitesi Tıp Fakültesi", y);
y = M.field(pb, "f unvan", "UNVAN", "Uzm. Dr.", y);
S.text(pb, "f type label", "KATILIMCI TÜRÜ", "label", "ink.500", { x: M.G, y: y });
y = M.chips(pb, "f type", ["Üye", "Üye olmayan", "Asistan", "Öğrenci", "Hemşire / teknisyen"],
  M.G, y + 24, { active: 0, h: M.TOUCH });
y = M.check(pb, "f kvkk", "KVKK aydınlatma metnini okudum, kişisel verilerimin işlenmesini onaylıyorum.", y + 12, { on: true });
y += 8;
S.text(pb, "f legal", "Ödeme havale veya kredi kartı ile. Kayıt 5 iş günü içinde onaylanır.",
  "meta", "ink.500", { x: M.G, y: y, w: M.CW });
y += 44;

/* Altına yapışan eylem çubuğu: tahtanın son bloğu, tek doygun buton. */
y = M.stickyBar(pb, y, "reg cta", "Kaydı tamamla");
pb.resize(M.W, S.snap(y));

return JSON.stringify(S.end("09-kayit-m"));
