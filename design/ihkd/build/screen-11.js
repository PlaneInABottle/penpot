/**
 * 11 — Akademi kataloğu. Search and topic chips, one featured course with progress,
 * a six-row catalogue, three steps.
 */
const S = IK;
const pb = S.start("Akademi", "11-akademi", 2488);

S.masthead(pb, "Akademi");
S.pageHead(pb, "AKADEMİ", "Kurslar ve STE",
  "46 kurs, 12.400 tamamlama. Üyeler için ücretsiz; STE kredisi kurs bitiminde yüklenir.",
  { w: 900, ledeW: 760 });

S.field(pb, "search", "ARA", "Kurs, modül veya eğitmen", 120, 400, 400, { placeholder: true });

let fx = 120;
["Tümü 46", "Kalp yetersizliği 9", "Görüntüleme 8", "Aritmi 7", "Metabolik 6", "Geriatri 5"].forEach((f, i) => {
  const w = Math.round(f.length * 8.6) + 32;
  const b = S.board(pb, "cat " + i, fx, 488, w, 34, i === 0 ? "red.600" : "white");
  if (i) S.stroke(b, "line.strong", 1);
  S.text(b, "cat text " + i, f, "label", i === 0 ? "on.red" : "ink.700", { x: fx + 16, y: 497 });
  fx += w + 8;
});

/* ------------------------------------------------------------------ öne çıkan */
S.photo(pb, "img-seminar", 120, 600, 640, 360, "Kalp yetersizliği kursu, Ankara");
S.text(pb, "f label", "ÖNE ÇIKAN KURS", "label", "red.600", { x: 800, y: 600 });
S.text(pb, "f title", "Kalp yetersizliğinde güncel tedavi", "h3", "ink.900", { x: 800, y: 628, w: 520 });
const meta = [["8", "modül"], ["6", "STE"], ["4s 20dk", "süre"], ["%40", "tamamlandı"]];
meta.forEach((m, i) => {
  S.text(pb, "fm v " + i, m[0], "h3", "ink.900", { x: 800 + i * 130, y: 732, w: 120 });
  S.text(pb, "fm l " + i, m[1], "meta", "ink.500", { x: 800 + i * 130, y: 772, w: 120 });
});
S.progress(pb, "f prog", 800, 824, 520, 40);
S.text(pb, "f by", "Eğitmen: Prof. Dr. Murat Şen · Ankara Üniversitesi", "meta", "ink.600", { x: 800, y: 844, w: 520 });
S.btn(pb, "f cta", "Devam et", 800, 888, 180, 48, "primary");

/* -------------------------------------------------------------------- katalog */
S.head(pb, 120, 1040, "TÜM KURSLAR", "Kurs listesi", { index: "46 kurs" });
const courses = [
  ["Ekokardiyografi: temelden ileriye", "12 modül · 9 STE · 7s 05dk", "Görüntüleme"],
  ["Antikoagülasyon yönetimi", "5 modül · 3 STE · 2s 40dk", "Aritmi"],
  ["Kardiyometabolik risk", "7 modül · 4 STE · 3s 10dk", "Metabolik"],
  ["Geriatride ilaç yönetimi", "6 modül · 4 STE · 2s 55dk", "Geriatri"],
  ["Yapısal kalp girişimleri", "9 modül · 6 STE · 5s 30dk", "Girişimsel"],
  ["Kardiyo-onkoloji temelleri", "5 modül · 3 STE · 2s 15dk", "Onkoloji"],
];
courses.forEach((c, i) => {
  const cy = 1164 + i * 64;
  S.text(pb, "c title " + i, c[0], "bodyMed", "ink.900", { x: 120, y: cy, w: 560 });
  S.text(pb, "c meta " + i, c[1], "data", "ink.500", { x: 760, y: cy + 2, w: 300, align: "right" });
  S.text(pb, "c cat " + i, c[2], "meta", "ink.500", { x: 1100, y: cy + 2, w: 100, align: "right" });
  S.text(pb, "c go " + i, "→", "nav", "red.600", { x: 1252, y: cy, w: 68, align: "right" });
  S.rule(pb, "c rule " + i, 120, cy + 44, 1200, "line.soft");
});

/* ------------------------------------------------------- tüm kurslar bağı */
S.text(pb, "courses all", "Tüm kurslar →", "nav", "red.600", { x: 120, y: 1552 });

/* ------------------------------------------------------------- nasıl çalışır */
S.head(pb, 120, 1640, "NASIL ÇALIŞIR", "Üç adımda STE belgesi", { index: "3 adım" });
const how = [
  ["01", "Kursa yazıl", "Üye girişi yeterli; ek ödeme yok."],
  ["02", "Modülleri tamamla", "Her modül 12–30 dakika, ilerleme kaydedilir."],
  ["03", "STE belgesini al", "Bitiminde e-Devlet'e işlenir, PDF indirilir."],
];
how.forEach((h, i) => {
  const hx = 120 + i * 400;
  S.text(pb, "how n " + i, h[0], "data", "ink.500", { x: hx, y: 1772 });
  S.text(pb, "how h " + i, h[1], "bodyMed", "ink.900", { x: hx, y: 1800, w: 320 });
  S.text(pb, "how p " + i, h[2], "body", "ink.600", { x: hx, y: 1830, w: 320 });
});

/* ------------------------------------------------------------- STE açıklaması */
// measured ink ends at rel 2019 (1 line; estLines overestimates Turkish
// copy — frozen from measurement, dead-space lint guards drift)
const ste = S.board(pb, "ste", 120, 1912, 1200, 132, "white");
S.stroke(ste, "line.strong", 1);
S.text(ste, "ste label", "STE NEDİR", "label", "red.600", { x: 152, y: 1940 });
S.text(ste, "ste title", "Sürekli tıp eğitimi kredisi", "bodyMed", "ink.900", { x: 152, y: 1968, w: 1136 });
S.text(ste, "ste body", "Her kursun kredisi modül listesinde yazar. Kursu bitirdiğinizde kredi e-Devlet'e işlenir ve PDF belgeniz oluşur. Üyeler için tüm kurslar ücretsizdir.", "body", "ink.700", { x: 152, y: 1996, w: 1136 });

S.footer(pb, S.snap(1912 + 132 + 48));

return JSON.stringify(S.end("11-akademi"));
