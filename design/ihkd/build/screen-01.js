/**
 * 01 — Ana sayfa.
 *
 *   python3 design/ihkd/build/build.py screen-01
 *
 * Story (brief §5): hook → proof → path → action.
 *   hook    hero — the society's sentence, one primary action
 *   proof   figures strip docked to the hero's bottom edge + the congress band
 *   path    gündem, working groups, academy, publication
 *   action  membership band, one link
 *
 * One red field (the congress band), one saturated primary (the hero's congress
 * registration). The figures strip is a white band on the paper: the page's
 * near-black surface was killed in this milestone (principles §6).
 * Every y below the masthead comes from the cursor; the board is resized to the
 * footer at the end, so no height literal can outlive a copy change.
 */
const S = IK;
const pb = S.start("Kurumsal", "01-ana-sayfa", 4200);
const RHYTHM = 112;   // section gap, brief §3
const HEAD = 148;     // headIndex → first row (rule at +108, 40 below it)

S.masthead(pb, null, { cta: "ghost" });

/* ------------------------------------------------------------------- hero */
/* Candidate A (chosen, 2026-11-02): the message column is centred against a
   full-height cardiology frame; the figures strip docks to the photo's
   bottom edge and closes the hero on a single horizontal. */
const HERO_TOP = 156, PHOTO_X = 760, PHOTO_W = 560, PHOTO_H = 560;
/* Committed ink heights, not the declared line-height multipliers: fit()
   shrinks a text box to its painted ink, so display 80/2 lines = 178,
   lead 22/2 lines = 62, label 13 = 20, nav 16 = 22. */
const HERO_BLOCK = 20 + 28 + 178 + 32 + 62 + 40 + 52; // kicker → CTA
let hy = Math.round((HERO_TOP + (PHOTO_H - HERO_BLOCK) / 2) / 4) * 4;
S.text(pb, "hero label", "1998'DEN BERİ · ANKARA", "label", "ink.500", { x: S.X, y: hy });
S.text(pb, "hero title", "Hastanın hekimi.", "display", "ink.900", { x: S.X, y: hy + 48, w: 560 });
S.text(pb, "hero lede",
  "1998'den beri iç hastalıkları hekimlerinin camiası: kılavuz, kongre, akademi tek adreste.",
  "lead", "ink.600", { x: S.X, y: hy + 48 + 178 + 32, w: 520 });
S.ctaRow(pb, "hero cta", S.X, hy + 48 + 178 + 32 + 62 + 40, "Kongreye kayıt ol",
  { w: 236, link: "Derneği tanı" });
S.photo(pb, "img-hero", PHOTO_X, HERO_TOP, PHOTO_W, PHOTO_H, null);

/* proof: the numbers are the hero's evidence, not a section below it */
let y = S.statsStrip(pb, "hero proof", S.X, HERO_TOP + PHOTO_H, S.CW, [
  ["6.847", "üye"], ["41", "il"], ["12", "çalışma grubu"], ["10", "kılavuz"],
], { bleed: S.W, surface: "white" });

/* --------------------------------------------------------------- kongre */
/* The page's only red field. Two balanced columns: the date/destination on the
   left, the countdown instrument on the right; CTA and its ghost link share one
   row (ctaRow owns both centres — no hand-written y). */
const BY = y + RHYTHM;
const BAND_H = 316;
const band = S.board(pb, "kongre band", 0, BY, S.W, BAND_H, "red.600");
S.text(band, "band label", "12. ULUSAL KONGRE", "label", "on.red", { x: S.X, y: BY + 56 });
S.text(band, "band title", "22–25 Nisan 2027", "h2", "on.red", { x: S.X, y: BY + 92, w: 720 });
S.text(band, "band venue", "Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı",
  "body", "on.red", { x: S.X, y: BY + 159, w: 600, opacity: 0.92 });
S.ctaRow(band, "band cta", S.X, BY + 205, "Kayıt ol",
  { w: 168, kind: "onred", link: "Programı gör", linkInk: "on.red", gap: 32 });

const CB = { x: 840, w: 480 }, CB_H = 204;
const cby = BY + Math.round((BAND_H - CB_H) / 2);
const counter = S.board(band, "countdown block", CB.x, cby, CB.w, CB_H, "red.700");
S.text(counter, "cd label", "KONGREYE KALAN", "label", "on.red", { x: CB.x + 28, y: cby + 28, opacity: 0.7 });
S.text(counter, "cd value", "147", "stat", "on.red", { x: CB.x + 28, y: cby + 60 });
S.text(counter, "cd unit", "GÜN", "label", "on.red", { x: CB.x + 28, y: cby + 120, opacity: 0.8 });
S.text(counter, "cd note", "Erken kayıt 31 Ocak 2027'de kapanıyor.", "meta", "on.red",
  { x: CB.x + 28, y: cby + 156, w: 424, opacity: 0.85 });

/* --------------------------------------------------------------- gündem */
y = S.headIndex(pb, S.X, BY + BAND_H + RHYTHM, "GÜNDEM", "Bu hafta", { link: "Tüm haberler →" });
const news = [
  ["12 Mart 2027", "Kongre", "Program yayınlandı: 96 oturum, dört salon", "6 dk"],
  ["4 Mart 2027", "Akademi", "Kalp yetersizliği kursu için kayıtlar açıldı", "2 dk"],
  ["26 Şubat 2027", "Dernek", "Çalışma grubu başkanları belirlendi", "4 dk"],
];
/* One shared top per row: title box at +24, the 13px meta rides +4 from it
   (the pair reads on one baseline at 1:1; the old +26 date sat low). */
y = S.rows(pb, "news", S.X, y, S.CW, news.map((n, i) => ({
  h: 24 + 36 + 24,
  draw(yRow) {
    S.text(pb, "news date " + i, n[0], "data", "ink.500", { x: S.X, y: yRow + 28 });
    S.text(pb, "news cat " + i, n[1], "label", "ink.500", { x: S.X + 180, y: yRow + 28 });
    S.text(pb, "news title " + i, n[2], "h3", "ink.900", { x: S.X + 320, y: yRow + 24, w: 760 });
    S.text(pb, "news time " + i, n[3], "data", "ink.500", { x: S.X + S.CW - 80, y: yRow + 28, w: 80, align: "right" });
  },
})), { rule: "line.soft" });
S.text(pb, "news note", "Duyurular Pazartesi 09:00'da yayımlanır.", "meta", "ink.500", { x: S.X, y: y + 24 });
y += 24 + 20;

/* ------------------------------------------------------- çalışma grupları */
y = S.headIndex(pb, S.X, y + RHYTHM, "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.");
const groups = [
  ["01", "Kardiyovasküler görüntüleme", "412 üye · Doç. Dr. Elif Karaca"],
  ["02", "Kalp yetersizliği", "508 üye · Prof. Dr. Murat Şen"],
  ["03", "Aritmi ve elektrofizyoloji", "287 üye · Prof. Dr. Ayşe Tunç"],
  ["04", "Kardiyometabolik", "366 üye · Doç. Dr. Kerem Yalçın"],
  ["05", "Hipertansiyon", "341 üye · Prof. Dr. Sema Yıldız"],
  ["06", "Geriatrik kardiyoloji", "198 üye · Doç. Dr. Deniz Arslan"],
];
/* Two columns on the grid: 588 + 24 gutter + 588 = 1200, so the row rule ends
   on the content edge for both columns. The title band is derived from the
   column (band − inset − arrow gutter); the meta sits one 12px step under the
   title's line box, never the 5px it had (İHKD 01: the two lines touched). */
const GBAND = 576, GCOL = 624, GINSET = 48, GARROW = 28, TLH = 39, MLH = 20, MGAP = 12;
const GTITLE = GBAND - GINSET - GARROW;
const gTop = y;
const groupColumn = (c) => {
  const items = [];
  for (let r = 0; r < groups.length / 2; r += 1) {
    const i = r * 2 + c, g = groups[i], gx = S.X + c * GCOL;
    const lines = S.estLines(g[1], GTITLE, 30, false);
    if (lines > 2) throw new Error("group name needs " + lines + " lines in a " + GTITLE + "px column");
    const h = 20 + lines * TLH + MGAP + MLH + 20;
    items.push({
      h,
      draw(yRow) {
        S.text(pb, "group idx " + i, g[0], "data", "ink.500", { x: gx, y: yRow + 22 });
        S.text(pb, "group name " + i, g[1], "h3", "ink.900", { x: gx + GINSET, y: yRow + 20, w: GTITLE });
        S.text(pb, "group meta " + i, g[2], "meta", "ink.500",
          { x: gx + GINSET, y: yRow + 20 + lines * TLH + MGAP, w: GTITLE });
        S.text(pb, "group arrow " + i, "→", "nav", "ink.500",
          { x: gx + GBAND - GARROW, y: yRow + 28, w: GARROW, align: "right" });
      },
    });
  }
  return items;
};
y = S.rows(pb, "group a", S.X, gTop, GBAND, groupColumn(0), { rule: "line.soft" });
S.rows(pb, "group b", S.X + GCOL, gTop, GBAND, groupColumn(1), { rule: "line.soft" });
S.link(pb, "groups all", "12 çalışma grubunun tümü →", S.X, y + 28, "red.700");
y += 28 + 30;

/* -------------------------------------------------------------- akademi */
y = S.headIndex(pb, S.X, y + RHYTHM, "AKADEMİ", "Kurs, kılavuz, STE");
const courses = [
  ["Kalp yetersizliğinde güncel tedavi", "8 modül · 6 STE · 4s 20dk"],
  ["Ekokardiyografi: temelden ileriye", "12 modül · 9 STE · 7s 05dk"],
  ["Antikoagülasyon yönetimi", "5 modül · 3 STE · 2s 40dk"],
];
/* One right edge per row group: meta ends at 1200, the action column starts
   there and ends on the 1320 grid edge. */
y = S.rows(pb, "course", S.X, y, S.CW, courses.map((c, i) => ({
  h: 24 + 36 + 24,
  draw(yRow) {
    S.text(pb, "course title " + i, c[0], "h3", "ink.900", { x: S.X, y: yRow + 24, w: 640 });
    S.text(pb, "course meta " + i, c[1], "data", "ink.500", { x: S.X + 820, y: yRow + 28, w: 260, align: "right" });
    S.text(pb, "course cta " + i, "Başla →", "nav", "red.700", { x: S.X + 1104, y: yRow + 31, w: 96, align: "right" });
  },
})), { rule: "line.soft" });
S.text(pb, "akademi note", "Kurslar üyeler için ücretsiz; STE kredisi kurs bitiminde yüklenir.",
  "meta", "ink.500", { x: S.X, y: y + 24 });
y += 24 + 20;

/* ---------------------------------------------------------------- yayın */
y = S.headIndex(pb, S.X, y + RHYTHM, "YAYIN", "Dergi ve kılavuz");
const PUB = y, COL_H = 300;
S.photo(pb, "img-journal", S.X, PUB, 280, COL_H, "Kardiyovasküler Klinik, cilt 12");
const JX = 440, JW = 480, JRULE = 940;
S.text(pb, "journal title", "Kardiyovasküler Klinik", "h3", "ink.900", { x: JX, y: PUB, w: JW });
S.text(pb, "journal meta", "Cilt 12 · Sayı 1 · Mart 2027 · TR Dizin", "data", "ink.500", { x: JX, y: PUB + 44, w: JW });
const toc = [
  ["12", "STE olmayan hastada BKA: 2027 uzlaşısı"],
  ["28", "KKY'de SGLT2 inhibitörleri: gerçek yaşam verisi"],
  ["41", "Genç sporcularda EKG taramasının maliyeti"],
];
/* Row height from the measured line count: a 2-line article title was being
   cut by a fixed 78px pitch, and the rules sat 17px above the next row. */
y = S.rows(pb, "toc", JX, PUB + 88, JW, toc.map((t, i) => {
  const lines = S.estLines(t[1], JW - 56, 16, false);
  return {
    h: 18 + lines * 26 + 18,
    draw(yRow) {
      S.text(pb, "toc page " + i, "s. " + t[0], "data", "ink.500", { x: JX, y: yRow + 20 });
      S.text(pb, "toc title " + i, t[1], "body", "ink.700", { x: JX + 56, y: yRow + 18, w: JW - 56 });
    },
  };
}), { rule: "line.soft" });
S.link(pb, "journal cta", "Sayıyı oku", JX, PUB + 282, "red.700");

S.vrule(pb, "pub div", JRULE, PUB, COL_H, "line.soft");
const GX2 = 960, GW2 = 360;
S.text(pb, "guide label", "AYIN KILAVUZU", "label", "ink.500", { x: GX2, y: PUB });
S.text(pb, "guide title", "Hipertansiyon tanı ve tedavi kılavuzu", "h3", "ink.900", { x: GX2, y: PUB + 24, w: GW2 });
S.text(pb, "guide meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "ink.500", { x: GX2, y: PUB + 108, w: GW2 });
/* the ECG is an instrument, not a divider: calibration + trace on the one
   guideline the page is featuring (brief §2, move 6) */
S.ecg(pb, "guide ecg", GX2, PUB + 148, 360, 44);
S.text(pb, "guide body", "Ev ölçümü, ofis dışı tansiyon ve tedavi eşikleri üzerine İHKD kılavuzu.",
  "body", "ink.600", { x: GX2, y: PUB + 204, w: GW2 });
S.link(pb, "guide cta", "Kılavuzu indir", GX2, PUB + 282, "ink.900");
y = PUB + 332;

/* -------------------------------------------------------------- üyelik */
/* The story closes on the action the home page exists for. White band, one
   link: a second saturated primary is forbidden and pointless here. */
const MB_H = 72 + 192 + 72;
const MB = y + RHYTHM;
const mb = S.board(pb, "uyelik band", 0, MB, S.W, MB_H, "white");
S.text(mb, "member label", "ÜYELİK", "label", "ink.500", { x: S.X, y: MB + 72 });
S.text(mb, "member title", "Yazan, toplayan, öğreten.", "h2", "ink.900", { x: S.X, y: MB + 96, w: 560 });
S.text(mb, "member lede", "Üyelik; kılavuz arşivini, kongre ücretini ve STE kredili kursları açar.",
  "lead", "ink.600", { x: S.X, y: MB + 160, w: 520 });
S.bullets(mb, "member gain", 760, MB + 72, 560, [
  "Kılavuzların ve dergi arşivinin tamamı",
  "Kongre kaydında üye ücreti",
  "Akademi kursları ücretsiz, STE kredisi bitiminde",
], { ink: "ink.700" });
S.link(mb, "member cta", "Başvuruyu başlat →", 760, MB + 206, "red.700");
S.text(mb, "member fee", "Yıllık aidat 2.400 TL · Öğrenci 600 TL · Başvuru 3 adım",
  "meta", "ink.500", { x: 760, y: MB + 244, w: 560 });

/* --------------------------------------------------------------- footer */
const FY = MB + MB_H + 56;
S.footer(pb, FY);
pb.resize(S.W, S.snap(FY + 320));

return JSON.stringify(S.end("01-ana-sayfa"));
