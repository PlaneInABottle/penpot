/**
 * 01 — Ana sayfa.
 *
 *   python3 design/ihkd/build/build.py screen-01
 *
 * Story (brief §5, M8): hook → proof → path → action.
 *   hook    hero — the 12th congress as a poster over a full hall, one primary
 *   proof   hero proof — 6.847 / 41 / 12 / 10 as a 44px stat strip on paper
 *   path    çalışma grupları, akademi, yayın, then this week's gündem
 *   action  membership band, one link
 *
 * The hero is the user's choice (cand-1-afis): a 1440×668 photo (Pexels
 * 20733081) under white type, the edition numeral as a vector layer and one
 * white ECG trace across the audience. The photo is `img-hero`, a full-bleed
 * rect inside the `hero scene` board: build.py restores it from provenance and
 * verifies it, and the board's ink.900 fill is the surface the type sits on —
 * no scrim, no gradient.
 * Every y below the masthead comes from the cursor; the board is resized to the
 * footer at the end, so no height literal can outlive a copy change.
 */
const S = IK;
const pb = S.start("Kurumsal", "01-ana-sayfa", 4300);
const RHYTHM = 112;   // section gap, brief §3

/* The poster numeral is a path, not a text node: at 520px it would be the
   board's seventh type size (design_lint type.sizes, max 6), and the numeral is
   a graphic layer of the poster, not copy. Outlines: Inter Tight 700, 520px,
   tracking −16, baked here so the build needs no font file. */
const TWELVE_D = "M183.3 -378.3V0.0H103.6V-302.4H101.4L14.9 -247.9V-319.0L108.5 -378.3Z M213.7 0.0V-57.4L348.4 -18" +
  "2.3Q365.5 -198.9 377.3 -212.1Q389.0 -225.4 395.0 -238.3Q401.1 -251.1 401.1 -266.1Q401.1 -282.8 3" +
  "93.6 -294.8Q386.0 -306.8 373.1 -313.3Q360.1 -319.8 343.3 -319.8Q326.1 -319.8 313.1 -312.8Q300.2 " +
  "-305.9 293.1 -292.9Q286.0 -279.9 286.0 -261.6H210.1Q210.1 -298.8 227.0 -326.1Q243.8 -353.4 274.1" +
  " -368.4Q304.4 -383.4 343.9 -383.4Q384.5 -383.4 414.7 -369.1Q444.9 -354.8 461.7 -329.5Q478.4 -304" +
  ".2 478.4 -271.3Q478.4 -249.8 470.0 -229.1Q461.6 -208.4 440.2 -182.9Q418.8 -157.5 379.8 -122.1L32" +
  "4.5 -68.0V-65.3H483.5V0.0Z";
const TWELVE = { d: TWELVE_D, w: 469, h: 384, view: "14.9 -383.4 468.6 383.4" };

function posterNumeral(parent, name, x, y, size, colorToken) {
  /* `size` is the type size the outlines were drawn from: the path keeps the
     poster's ratio (520 in the candidate) inside a shorter poster. */
  const w = Math.round((TWELVE.w * size) / 520);
  const h = Math.round((TWELVE.h * size) / 520);
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h +
    '" viewBox="' + TWELVE.view + '"><path d="' + TWELVE.d + '" fill="#FFFFFF"/></svg>';
  const g = penpot.createShapeFromSvg(svg);
  g.name = name;
  parent.appendChild(g);
  // the importer sizes the group from the viewBox, not the svg's width/height:
  // the group resize is what actually scales the outlines
  g.resize(w, h);
  g.x = pb.x + S.snap(x);
  g.y = pb.y + S.snap(y);
  const walk = (s) => {
    if (s.type === "path") {
      s.fills = [{ fillColor: "#FFFFFF", fillOpacity: 1 }];
      S.bind(s, colorToken, ["fill"]);
    } else if (s.type === "rectangle") {
      s.fills = [];
    }
    (s.children || []).forEach(walk);
  };
  walk(g);
  return g;
}

S.masthead(pb, null, { cta: "ghost" });

/* ------------------------------------------------------------------- hero */
/* M8 (2026-11-03): the user chose the poster. Poster = photo scene board +
   white type + vector numeral + one white trace; the society is the signature
   line at the poster's foot, the congress is the message. Proof leaves the
   photo: the numbers are a stat strip on paper under the poster's edge. */
const HERO_Y = 108, HERO_H = 668;
const hero = S.board(pb, "hero scene", 0, HERO_Y, S.W, HERO_H, "ink.900");
/* the photo slot: restored from provenance by build.py; the board clips it */
S.rect(hero, "img-hero", 0, HERO_Y, S.W, HERO_H, "surface.alt");

S.text(hero, "hero label", "12. ULUSAL İÇ HASTALIKLARI VE KARDİYOLOJİ KONGRESİ",
  "label", "on.ink", { x: 120, y: HERO_Y + 40, w: 760 });
S.text(hero, "hero date", "22–25 Nisan 2027", "display", "on.ink",
  { x: 120, y: HERO_Y + 72, w: 760 });
S.text(hero, "hero venue", "Antalya Kongre Merkezi, Belek · 96 oturum · 214 konuşmacı",
  "body", "on.ink", { x: 120, y: HERO_Y + 176, w: 680 });
/* the countdown is one figure + one note: the candidate repeated "147 gün"
   twice (a 13px sentence above the 44px value); the value carries it now. */
S.text(hero, "hero countdown value", "147", "stat", "on.ink", { x: 120, y: HERO_Y + 216 });
S.text(hero, "hero countdown note", "gün kaldı · erken kayıt 31 Ocak 2027'de kapanıyor",
  "meta", "on.ink", { x: 216, y: HERO_Y + 244, w: 420 });
S.ctaRow(hero, "hero cta", 120, HERO_Y + 300, "Kongreye kayıt ol",
  { w: 236, link: "Programı gör", gap: 24, linkInk: "on.ink" });
/* the society speaks in the first viewport, second to the date (M8: it was a
   13px kicker in the candidate) */
S.text(hero, "hero society", "Hastanın hekimi.", "h3", "on.ink",
  { x: 120, y: HERO_Y + 420, w: 560 });
/* the identity line is an imprint: below the trace, on the poster's darkest
   band (mean luminance 28 of 255 at 1:1), so 13px white keeps its AA ratio
   without a scrim; on the crowd above it dropped to 3.2:1 at the bright pixels */
S.text(hero, "hero society line", "İHKD · İç Hastalıkları ve Kardiyoloji Derneği · 1998'den beri Ankara",
  "label", "on.ink", { x: 120, y: HERO_Y + 624, w: 720 });
/* the numeral keeps the candidate's share of the poster (435 in 668 = 520 in
   792), right edge on 1294 so the audience's faces stay outside its left half */
posterNumeral(hero, "hero twelve", 902, HERO_Y + 130, 435, "on.ink");
S.ecg(hero, "hero ecg", 0, HERO_Y + 540, S.W, 30, "on.ink");

/* proof: 44px figures on paper, the poster's edge is the joint */
let y = S.statsStrip(pb, "hero proof", S.X, HERO_Y + HERO_H, S.CW, [
  ["6.847", "Üye"],
  ["41", "İl temsilcisi"],
  ["12", "Çalışma grubu"],
  ["10", "Kılavuz"],
], { pad: 20, rule: false });

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

/* --------------------------------------------------------------- gündem */
/* The news moves behind the three routes: the hero already announced the
   congress, so the page proves its numbers, names its paths, and only then
   reports this week. One row may mention the programme; no repeated band. */
y = S.headIndex(pb, S.X, y + RHYTHM, "GÜNDEM", "Bu hafta", { link: "Tüm haberler →" });
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
