/**
 * 18 — Üyelik başvurusu. Benefits, fee tiers, application form, FAQ.
 */
const S = IK;
const pb = S.start("Üyelik", "18-uyelik", 2292);

S.masthead(pb, "Dernek");
S.text(pb, "u label", "ÜYELİK", "label", "red.700", { x: 120, y: 156 });
S.text(pb, "u title", "Üyelik başvurusu", "display", "ink.900", { x: 120, y: 188 });
S.text(pb, "u lede", "Başvuru üç adımda tamamlanır; belgeler yüklendikten sonra yönetim kurulu 15 gün içinde karar verir.", "lead", "ink.600", { x: 120, y: 300, w: 720 });
S.text(pb, "u steps", "3 ADIM", "label", "ink.500", { x: 920, y: 308 });
S.rule(pb, "u rule", 120, 420, 1200, "line.strong", 1);
S.rect(pb, "u bar", 120, 418, 96, 3, "red.600");

/* ------------------------------------------------------------------ avantajlar */
S.text(pb, "ben label", "ÜYELİK NE VERİR", "label", "red.700", { x: 120, y: 468 });
const benefits = [
  ["Kongre indirimi", "Erken kayıtta üyelere 700 TL avantaj."],
  ["Kılavuzlara erken erişim", "Yayından 30 gün önce."],
  ["Akademi", "46 kurs, ücretsiz, STE kredili."],
  ["Dergi", "Basılı ve dijital abonelik."],
  ["Çalışma grupları", "12 grupta sınırsız üyelik."],
  ["Mentorluk", "Genç hekim–kıdemli eşleşmesi."],
].map((b) => ({ text: b[0], sub: b[1] }));
S.bullets(pb, "ben l", 120, 512, 540, benefits.filter((b, i) => i % 2 === 0),
  { role: "bodyMed", pad: 6, dot: 8, textX: 24, ink: "ink.900" });
S.bullets(pb, "ben r", 720, 512, 540, benefits.filter((b, i) => i % 2 === 1),
  { role: "bodyMed", pad: 6, dot: 8, textX: 24, ink: "ink.900" });

/* ------------------------------------------------------------------- aidat */
S.text(pb, "tier label", "YILLIK AİDAT", "label", "red.700", { x: 120, y: 720 });
[
  ["Asistan", "1.200 TL", "Uzmanlık eğitimi süresince"],
  ["Uzman", "3.400 TL", "Kardiyoloji veya iç hastalıkları"],
  ["Öğretim üyesi", "3.400 TL", "Kurum faturası kesilebilir"],
  ["Emekli", "1.700 TL", "65 yaş üstü indirimi dahil"],
].forEach((t, i) => {
  const tx = 120 + i * 306;
  S.text(pb, "tier name " + i, t[0], "label", "ink.500", { x: tx, y: 756 });
  S.text(pb, "tier price " + i, t[1], "h3", "ink.900", { x: tx, y: 780, w: 280 });
  S.text(pb, "tier note " + i, t[2], "meta", "ink.500", { x: tx, y: 820, w: 260 });
  if (i < 3) S.vrule(pb, "tier div " + i, tx + 282, 836, 96, "line.soft");
});

/* -------------------------------------------------------------------- form */
const fy = 880;
const form = S.board(pb, "form", 120, fy, 1200, 760, "white");
S.stroke(form, "line.strong", 1);
S.text(form, "form title", "Başvuru formu", "h3", "ink.900", { x: 156, y: fy + 24 });
S.text(form, "form step", "ADIM 1 / 3 · KİŞİSEL", "label", "red.700", { x: 1000, y: fy + 34, w: 284, align: "right" });
S.rule(form, "form rule", 156, fy + 72, 1128, "line.soft");

S.field(form, "f name", "AD SOYAD", "Dr. Selin Aydın", 156, fy + 96, 540);
S.field(form, "f mail", "E-POSTA", "selin.aydin@ankara.edu.tr", 736, fy + 96, 548);
S.field(form, "f phone", "TELEFON", "+90 5•• ••• •• 40", 156, fy + 192, 540, { placeholder: true });
S.field(form, "f org", "KURUM", "Ankara Üniversitesi Tıp Fakültesi", 736, fy + 192, 548);
S.field(form, "f title", "UNVAN", "Araştırma görevlisi", 156, fy + 288, 540);
S.field(form, "f city", "İL", "Ankara", 736, fy + 288, 548);
S.field(form, "f dip", "DİPLOMA NUMARASI", "1234567", 156, fy + 384, 540);
S.field(form, "f group", "ÇALIŞMA GRUBU (İSTEĞE BAĞLI)", "Kalp yetersizliği", 736, fy + 384, 548);

S.text(form, "doc label", "BELGELER", "label", "ink.500", { x: 156, y: fy + 480 });
["Diploma fotokopisi (PDF)", "Uzmanlık belgesi veya asistanlık yazısı", "Nüfus cüzdanı fotokopisi"].forEach((d, i) => {
  S.rect(form, "doc box " + i, 156, fy + 508 + i * 34, 16, 16, "white", { stroke: "line.strong" });
  S.text(form, "doc t " + i, d, "meta", "ink.700", { x: 184, y: fy + 506 + i * 34, w: 500 });
});
S.rect(form, "kvkk box", 156, fy + 632, 16, 16, "white", { stroke: "line.strong" });
S.text(form, "kvkk", "KVKK aydınlatma metnini okudum.", "meta", "ink.600", { x: 184, y: fy + 630, w: 600 });

S.btn(form, "u next", "Devam et", 1044, fy + 680, 276, 52, "primary");
S.text(form, "u save", "Taslağı kaydet ve sonra devam et", "meta", "ink.500", { x: 700, y: fy + 696, w: 320, align: "right" });

/* --------------------------------------------------------------------- SSS */
S.text(pb, "faq label", "SSS", "label", "red.700", { x: 120, y: 1688 });
[
  ["Başvuru ne kadar sürer?", "Belgeler tamamsa 15 gün."],
  ["Asistanlıkta üyelik başlar mı?", "Evet, asistan tarifesi geçerli."],
  ["Aidat iadesi var mı?", "Yıllık aidat iade edilmez."],
  ["Yurt dışı üyelik?", "Evet, 90 EUR/yıl."],
].forEach((f, i) => {
  const qy = 1724 + i * 56;
  S.text(pb, "faq q " + i, f[0], "bodyMed", "ink.900", { x: 120, y: qy, w: 500 });
  S.text(pb, "faq a " + i, f[1], "meta", "ink.600", { x: 640, y: qy + 2, w: 680 });
  S.rule(pb, "faq r " + i, 120, qy + 40, 1200, "line.soft");
});

S.footer(pb, 1972);

return JSON.stringify(S.end("18-uyelik"));
