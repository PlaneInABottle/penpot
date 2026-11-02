/**
 * 09-kayit-hata — kayıt formunun hata durumu (Kongre, 1440).
 *
 *   python3 design/ihkd/build/build.py screen-state-09
 *
 * Hata iki katmanda: üstte özet (signal yüzeyi red.100 + red.700 metin), alanın
 * kendisinde kırmızı çizgi + ipucu. Kırmızı yalnız signal rolünde: özet yüzeyi,
 * hatalı alan çizgisi ve tek doygun eylem `Kaydı tamamla`.
 */
const S = IK;
const pb = S.start("Kongre", "09-kayit-hata", 1100);

S.masthead(pb, "Kongre");
S.text(pb, "p label", "KAYIT", "label", "ink.500", { x: 120, y: 156 });
S.text(pb, "p title", "Kayıt formu", "h2", "ink.900", { x: 120, y: 188 });
S.text(pb, "p note", "Adım 2 / 4 · katılımcı bilgileri", "meta", "ink.500",
  { x: 960, y: 220, w: 360, align: "right" });
S.rule(pb, "p rule", 120, 262, 1200, "line.strong", 2);

/* ---------------------------------------------------------------- hata özeti */
const SY = 300, SH = 100;
const summary = S.board(pb, "error summary", 120, SY, 1200, SH, "red.100");
S.text(summary, "err title", "Form gönderilemedi: 2 alan düzeltilmeli.", "bodyMed", "red.700",
  { x: 152, y: SY + 24, w: 1136 });
S.text(summary, "err list", "1. E-posta adresi geçersiz.  2. Diploma numarası 6 haneli olmalı.", "meta", "red.700",
  { x: 152, y: SY + 60, w: 1136 });

/* ----------------------------------------------------------------- form kartı */
const CY = 432, CH = 576, PX = 152, PW = 1136, COLW = 544, COL2 = 744;
const card = S.board(pb, "reg card", 120, CY, 1200, CH, "white");
S.stroke(card, "line.soft", 1);
S.text(card, "reg label", "KATILIMCI BİLGİLERİ", "label", "ink.500", { x: PX, y: CY + 32 });

S.field(card, "f ad", "AD SOYAD", "Dr. Selin Aydın", PX, CY + 64, COLW);
S.field(card, "f mail", "E-POSTA", "selin.aydin@ankara", PX, CY + 164, COLW,
  { error: true, hint: "Geçerli bir e-posta girin." });
S.field(card, "f kurum", "KURUM", "Ankara Üniversitesi Tıp Fakültesi", PX, CY + 264, COLW);
S.field(card, "f unvan", "UNVAN", "Uzm. Dr.", COL2, CY + 64, COLW);
S.field(card, "f il", "İL", "Ankara", COL2, CY + 164, COLW);
S.field(card, "f diploma", "DİPLOMA NO", "48291", COL2, CY + 264, COLW,
  { error: true, hint: "Diploma numarası 6 haneli olmalı." });

S.text(card, "f type label", "KATILIMCI TÜRÜ", "label", "ink.500", { x: PX, y: CY + 372 });
S.chips(card, "f type", ["Üye", "Üye olmayan", "Asistan", "Öğrenci", "Hemşire / teknisyen"],
  PX, CY + 396, { active: 0 });

S.rect(card, "f kvkk box", PX, CY + 456, 16, 16, "red.600", { stroke: "red.600" });
S.text(card, "f kvkk", "KVKK aydınlatma metnini okudum, kişisel verilerimin işlenmesini onaylıyorum.",
  "meta", "ink.600", { x: PX + 28, y: CY + 454, w: 700 });

S.btn(card, "reg cta", "Kaydı tamamla", PX, CY + 496, 240, 52, "primary");
S.btn(card, "reg draft", "Taslak kaydet", PX + 264, CY + 496, 200, 52, "secondary");

let y = CY + CH + 48;
S.text(pb, "reg note", "Hatalı alanlar düzeltilmeden kayıt gönderilmez; taslak 30 gün saklanır.",
  "meta", "ink.500", { x: 120, y: y, w: S.CW });
y += 48;

pb.resize(S.W, S.snap(y));

return JSON.stringify(S.end("09-kayit-hata"));
