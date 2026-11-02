/**
 * 01 — Ana sayfa, mobil 390 (`01-ana-sayfa-m`, sayfa `Mobil`).
 *
 *   python3 design/ihkd/build/build.py screen-m01
 *
 * Masaüstü 01'in hikâyesi tek kolonda: hook → proof → path → action.
 * Tek kırmızı buton: `hero cta` (Kongreye kayıt ol). Kongre bandı sayfanın tek
 * kırmızı alanı; bandın butonu bone (`onred`), doygun değil.
 *
 * Görsel dil (2026-11-02 yön değişikliği): hasta, steteskop-göğüs, el ve
 * muayene sahnesi YASAK. Hero'nun görsel yuvası `heroM()` içinde parametrik:
 *   - "figure" (bugünkü varsayılan): kendi vektörümüz — EKG trace, 1 mV
 *     kalibrasyon, 5 mm ızgara, ölçüm satırı; bilimsel figür.
 *   - "photo": kongre/dergi fotoğrafı yuvası (`img-hero`), provenance satırı
 *     hero ajanının dosyasında. brief.md'de "Hero görsel sözleşmesi" satırı
 *     yazıldığında yalnız `HERO_VISUAL` değişir.
 */
const S = IK;
const M = IKM;
const pb = M.start("Mobil", "01-ana-sayfa-m", 4600);

/* brief.md § hero görsel sözleşmesi: henüz yazılmadı → bilimsel figür. */
const HERO_VISUAL = "figure";

/**
 * Hero bloğu tek yerde: masaüstü hero kararı (M6) buraya yansıtılacak, sayfa
 * gövdesi yalnız dönüş y'sini kullanır. Dönüş: figürden sonraki ilk y.
 */
function heroM(board, y0, opts) {
  const o = opts || {};
  const visual = o.visual || HERO_VISUAL;
  let y = y0;

  S.text(board, "hero label", "1998'DEN BERİ · ANKARA", "label", "ink.500", { x: M.G, y: y });
  /* display 80/0.98: bilinçli iki satır ("Hastanın" / "hekimi."), masaüstü lockup'ı */
  S.text(board, "hero title", "Hastanın hekimi.", "display", "ink.900", { x: M.G, y: y + 24, w: M.CW });
  y += 24 + 156;

  S.text(board, "hero lede",
    "1998'den beri iç hastalıkları hekimlerinin camiası: kılavuz, kongre, akademi tek adreste.",
    "lead", "ink.600", { x: M.G, y: y + 20, w: M.CW });
  y += 20 + 99 + 24;

  /* proof: sayının kendisi kanıt; 2x2 ızgara (390'da dört kolon okunmaz) */
  y = M.stats(board, "hero proof", [
    ["6.847", "üye"], ["41", "il"], ["12", "çalışma grubu"], ["10", "kılavuz"],
  ], y, { after: 28 });

  y = M.btn(board, "hero cta", "Kongreye kayıt ol", y) + 12;
  y = M.btn(board, "hero ghost", "Derneği tanı", y, { kind: "ghost" }) + 32;

  if (visual === "figure") {
    y = M.plate(board, "hero figure", 0, y, M.W, 232, {
      label: "EKG · II. DERİVASYON · 25 mm/s",
      read: "HR 72 · PR 160 ms · QRS 92 ms · QT 400 ms",
      caption: "Kalibrasyon 10 mm/mV · 5 mm ızgara",
    });
  } else {
    /* fotoğraf yuvası: boş mat + caption; gerçek görsel build.py'nin
       provenance onarımıyla gelir (hero satırı hero ajanının dosyasında). */
    S.photo(board, "img-hero", M.G, y, M.CW, 280, "Kongre salonu, poster oturumu");
    y += 280 + 40;
  }
  return y + 32;
}

let y = heroM(pb, 96);

/* --------------------------------------------------------------- kongre bandı */
/* Sayfanın tek kırmızı alanı. Buton bone, ikinci eylem link: doygun primary 1. */
const BAND_H = 336;
const BY = y + M.SECTION;
const band = S.board(pb, "kongre band", 0, BY, M.W, BAND_H, "red.600");
S.text(band, "band label", "12. ULUSAL KONGRE", "label", "on.red", { x: M.G, y: BY + 24 });
S.text(band, "band title", "22–25 Nisan 2027", "h3", "on.red", { x: M.G, y: BY + 48, w: M.CW });
S.text(band, "band venue", "Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı",
  "body", "on.red", { x: M.G, y: BY + 96, w: M.CW, opacity: 0.92 });
S.text(band, "band countdown", "KONGREYE KALAN 147 GÜN", "meta", "on.red",
  { x: M.G, y: BY + 168, w: M.CW, opacity: 0.85 });
S.text(band, "band note", "Erken kayıt 31 Ocak 2027'de kapanıyor.", "meta", "on.red",
  { x: M.G, y: BY + 192, w: M.CW, opacity: 0.85 });
M.btn(band, "band cta", "Kayıt ol", BY + 224, { kind: "onred" });
S.link(band, "band cta link", "Programı gör", M.G, BY + 288, "on.red");

/* ------------------------------------------------------------------- gündem */
y = BY + BAND_H;
y = M.sectionHead(pb, y + M.SECTION, "GÜNDEM", "Bu hafta");
const news = [
  ["12 Mart 2027 · KONGRE · 6 dk", "Program yayınlandı: 96 oturum, dört salon"],
  ["4 Mart 2027 · AKADEMİ · 2 dk", "Kalp yetersizliği kursu için kayıtlar açıldı"],
  ["26 Şubat 2027 · DERNEK · 4 dk", "Çalışma grubu başkanları belirlendi"],
];
y = S.rows(pb, "news", M.G, y, M.CW, news.map((n, i) => {
  const lines = S.estLines(n[1], M.CW, 16, false);
  return {
    h: 60 + lines * 24,
    draw(yRow) {
      S.text(pb, "news meta " + i, n[0], "data", "ink.500", { x: M.G, y: yRow + 16, w: M.CW });
      S.text(pb, "news title " + i, n[1], "bodyMed", "ink.900", { x: M.G, y: yRow + 44, w: M.CW });
    },
  };
}), { rule: "line.soft" });
S.link(pb, "news all", "Tüm haberler →", M.G, y + 16, "red.700");
y += 16 + 30 + 16;
S.text(pb, "news note", "Duyurular Pazartesi 09:00'da yayımlanır.", "meta", "ink.500", { x: M.G, y: y, w: M.CW });
y += 40;

/* --------------------------------------------------------- çalışma grupları */
y = M.sectionHead(pb, y + M.SECTION, "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.");
const groups = [
  ["01", "Kardiyovasküler görüntüleme", "412 üye · Doç. Dr. Elif Karaca"],
  ["02", "Kalp yetersizliği", "508 üye · Prof. Dr. Murat Şen"],
  ["03", "Aritmi ve elektrofizyoloji", "287 üye · Prof. Dr. Ayşe Tunç"],
  ["04", "Kardiyometabolik", "366 üye · Doç. Dr. Kerem Yalçın"],
  ["05", "Hipertansiyon", "341 üye · Prof. Dr. Sema Yıldız"],
  ["06", "Geriatrik kardiyoloji", "198 üye · Doç. Dr. Deniz Arslan"],
];
y = S.rows(pb, "group", M.G, y, M.CW, groups.map((g, i) => ({
  h: 80,
  draw(yRow) {
    S.text(pb, "group idx " + i, g[0], "data", "ink.500", { x: M.G, y: yRow + 16 });
    S.text(pb, "group name " + i, g[1], "bodyMed", "ink.900", { x: M.G + 32, y: yRow + 14, w: M.CW - 32 });
    S.text(pb, "group meta " + i, g[2], "meta", "ink.500", { x: M.G + 32, y: yRow + 40, w: M.CW - 32 });
  },
})), { rule: "line.soft" });
S.link(pb, "groups all", "12 çalışma grubunun tümü →", M.G, y + 16, "red.700");
y += 16 + 30 + 16;

/* ------------------------------------------------------------------ akademi */
y = M.sectionHead(pb, y + M.SECTION, "AKADEMİ", "Kurs, kılavuz, STE");
const courses = [
  ["Kalp yetersizliğinde güncel tedavi", "8 modül · 6 STE · 4s 20dk"],
  ["Ekokardiyografi: temelden ileriye", "12 modül · 9 STE · 7s 05dk"],
  ["Antikoagülasyon yönetimi", "5 modül · 3 STE · 2s 40dk"],
];
y = S.rows(pb, "course", M.G, y, M.CW, courses.map((c, i) => ({
  h: 84,
  draw(yRow) {
    S.text(pb, "course title " + i, c[0], "bodyMed", "ink.900", { x: M.G, y: yRow + 16, w: M.CW });
    S.text(pb, "course meta " + i, c[1], "data", "ink.500", { x: M.G, y: yRow + 44, w: 240 });
    S.text(pb, "course cta " + i, "Başla →", "nav", "red.700", { x: M.G + M.CW - 96, y: yRow + 42, w: 96, align: "right" });
  },
})), { rule: "line.soft" });
y += 16;
S.text(pb, "akademi note", "Kurslar üyeler için ücretsiz; STE kredisi kurs bitiminde yüklenir.",
  "meta", "ink.500", { x: M.G, y: y, w: M.CW });
y += 40;

/* -------------------------------------------------------------------- yayın */
y = M.sectionHead(pb, y + M.SECTION, "YAYIN", "Dergi ve kılavuz");
S.text(pb, "journal title", "Kardiyovasküler Klinik", "bodyMed", "ink.900", { x: M.G, y: y, w: M.CW });
S.text(pb, "journal meta", "Cilt 12 · Sayı 1 · Mart 2027 · TR Dizin", "data", "ink.500", { x: M.G, y: y + 28, w: M.CW });
const toc = [
  ["12", "STE olmayan hastada BKA: 2027 uzlaşısı"],
  ["28", "KKY'de SGLT2 inhibitörleri: gerçek yaşam verisi"],
  ["41", "Genç sporcularda EKG taramasının maliyeti"],
];
y = S.rows(pb, "toc", M.G, y + 64, M.CW, toc.map((t, i) => {
  const lines = S.estLines(t[1], M.CW - 56, 16, false);
  return {
    h: 16 + lines * 24 + 16,
    draw(yRow) {
      S.text(pb, "toc page " + i, "s. " + t[0], "data", "ink.500", { x: M.G, y: yRow + 16 });
      S.text(pb, "toc title " + i, t[1], "body", "ink.700", { x: M.G + 56, y: yRow + 14, w: M.CW - 56 });
    },
  };
}), { rule: "line.soft" });
S.link(pb, "journal cta", "Sayıyı oku", M.G, y + 16, "red.700");
y += 16 + 30 + 40;

/* ayın kılavuzu: ECG bir enstrüman — kendi vektörümüz, fotoğraf değil */
S.text(pb, "guide label", "AYIN KILAVUZU", "label", "ink.500", { x: M.G, y: y });
S.text(pb, "guide title", "Hipertansiyon tanı ve tedavi kılavuzu", "bodyMed", "ink.900", { x: M.G, y: y + 24, w: M.CW });
S.text(pb, "guide meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "ink.500", { x: M.G, y: y + 76, w: M.CW });
y = M.trace(pb, "guide trace", M.G, y + 104, M.CW) + 24;
S.link(pb, "guide cta", "Kılavuzu indir", M.G, y, "ink.900");
y += 30 + 16;

/* ------------------------------------------------------------------- üyelik */
/* Sayfa üyeliğe bir linkle kapanır: ikinci doygun buton yok. */
const MB_H = 420;
const MB = y + M.SECTION;
const mb = S.board(pb, "uyelik band", 0, MB, M.W, MB_H, "white");
S.text(mb, "member label", "ÜYELİK", "label", "ink.500", { x: M.G, y: MB + 32 });
S.text(mb, "member title", "Yazan, toplayan, öğreten.", "h3", "ink.900", { x: M.G, y: MB + 56, w: M.CW });
S.text(mb, "member lede", "Üyelik; kılavuz arşivini, kongre ücretini ve STE kredili kursları açar.",
  "lead", "ink.600", { x: M.G, y: MB + 140, w: M.CW });
S.bullets(mb, "member gain", M.G, MB + 256, M.CW, [
  "Kılavuzların ve dergi arşivinin tamamı",
  "Kongre kaydında üye ücreti",
  "Akademi kursları ücretsiz, STE kredisi bitiminde",
], { ink: "ink.700", pad: 4 });
S.text(mb, "member fee", "Yıllık aidat 2.400 TL · Öğrenci 600 TL · Başvuru 3 adım",
  "meta", "ink.500", { x: M.G, y: MB + 376, w: M.CW });

/* ------------------------------------------------------------------- footer */
y = MB + MB_H + M.SECTION;
y = M.footer(pb, y);

pb.resize(M.W, S.snap(y));

return JSON.stringify(S.end("01-ana-sayfa-m"));
