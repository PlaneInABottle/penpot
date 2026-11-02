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

/* The cover figure is a local drawing: lib.js is shared, and the ECG plate is
   the only place this page needs a grid + sampled trace. pb = the board origin
   (shape coords in this file are page-absolute once the board is placed). */
function coverGrid(parent, name, x, y, w, h, step, skip, colorToken) {
  const lines = [];
  for (let gx = 0; gx <= w; gx += step) {
    if (skip && gx % skip === 0) continue;
    lines.push('<line x1="' + gx + '" y1="0" x2="' + gx + '" y2="' + h + '"/>');
  }
  for (let gy = 0; gy <= h; gy += step) {
    if (skip && gy % skip === 0) continue;
    lines.push('<line x1="0" y1="' + gy + '" x2="' + w + '" y2="' + gy + '"/>');
  }
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h +
    '" viewBox="0 0 ' + w + " " + h + '" stroke="#DDE1E4" stroke-width="1">' + lines.join("") + "</svg>";
  const g = penpot.createShapeFromSvg(svg);
  g.name = name;
  parent.appendChild(g);
  g.x = pb.x + S.snap(x);
  g.y = pb.y + S.snap(y);
  const walk = (s) => {
    if (s.strokes && s.strokes.length) {
      s.strokes = [{ strokeColor: "#000000", strokeOpacity: 1, strokeStyle: "solid", strokeWidth: 1, strokeAlignment: "center" }];
      S.bind(s, colorToken, ["strokeColor"]);
    }
    (s.children || []).forEach(walk);
  };
  walk(g);
  return g;
}


/* The cover masthead is the brand wordmark at display size (JetBrains Mono 600),
   not the display face: the cover is a publication of the same mark as the nav. */
function coverMark(parent, name, chars, x, y, size) {
  const t = penpot.createText(String(chars));
  t.name = name;
  t.fontId = "gfont-jetbrains-mono";
  t.fontFamily = "JetBrains Mono";
  t.fontVariantId = "600";
  t.fontSize = String(size);
  t.lineHeight = "1.0";
  t.letterSpacing = "2";
  parent.appendChild(t);
  t.growType = "auto-width";
  t.resize(Math.ceil(String(chars).length * size * 0.62) + 8, Math.ceil(size));
  t.x = pb.x + S.snap(x);
  t.y = pb.y + S.snap(y);
  S.paint(t, "ink.900");
  S.bind(t, "fs.80", ["fontSize"]);
  return t;
}

function coverTrace(parent, name, x, base, w, amp, beats) {
  const H = amp * 2 + 16, N = Math.round(beats * 300);
  const bump = (t, c, s) => Math.exp(-Math.pow((t - c) / s, 2));
  const pts = [];
  for (let i = 0; i <= N; i += 1) {
    const t = (i / N) * beats, p = t % 1;
    const v = 0.07 * bump(p, 0.20, 0.030) - 0.06 * bump(p, 0.355, 0.010) + 0.62 * bump(p, 0.373, 0.009) -
      0.14 * bump(p, 0.392, 0.011) + 0.17 * bump(p, 0.66, 0.050);
    pts.push([(i / N) * w, H / 2 - v * amp]);
  }
  const d = pts.map((q, i) => (i ? "L" : "M") + q[0].toFixed(1) + " " + q[1].toFixed(1)).join(" ");
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + H +
    '" viewBox="0 0 ' + w + " " + H + '"><path d="' + d +
    '" fill="none" stroke="#C4122F" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  const sh = penpot.createShapeFromSvg(svg);
  sh.name = name;
  parent.appendChild(sh);
  sh.x = pb.x + S.snap(x);
  sh.y = pb.y + S.snap(base - H / 2);
  const walk = (s) => {
    if (s.strokes && s.strokes.length) {
      s.strokes = [{ strokeColor: "#000000", strokeOpacity: 1, strokeStyle: "solid", strokeWidth: 1, strokeAlignment: "center" }];
      S.bind(s, "red.600", ["strokeColor"]);
    }
    (s.children || []).forEach(walk);
  };
  walk(sh);
  return sh;
}

S.masthead(pb, null, { cta: "ghost" });

/* ------------------------------------------------------------------- hero */
/* M7 (2026-11-02): the home page opens as the society's own issue. The hero
   is a cover — masthead, coverlines, a self-drawn ECG plate as the cover
   figure, and "Bu sayıda" as the page's table of contents. No photo, no
   proof strip, no congress band: the cover carries the date, the countdown
   and the one primary. The page's sections resume on paper below. */
const COVER_Y = 140, COVER_H = 740, FIG_Y = COVER_Y + 382;
S.rect(pb, "cover sheet", S.X, COVER_Y, 1200, COVER_H, "white",
  { stroke: "line.soft", radius: "radius.2" });
coverMark(pb, "cover mast", "İHKD", 160, COVER_Y + 36, 80);
S.text(pb, "cover journal", "KARDİYOVASKÜLER KLİNİK", "label", "ink.500", { x: 160, y: COVER_Y + 142 });
S.text(pb, "cover issue", "Cilt 12 · Sayı 1 · Mart 2027", "data", "ink.500", { x: 160, y: COVER_Y + 164 });
S.text(pb, "cover line", "Hastanın hekimi.", "h2", "ink.900", { x: 160, y: COVER_Y + 200, w: 620 });
S.text(pb, "cover congress label", "12. ULUSAL KONGRE", "label", "ink.500", { x: 160, y: COVER_Y + 260 });
S.text(pb, "cover congress date", "22–25 Nisan 2027 · Antalya", "h3", "ink.900",
  { x: 160, y: COVER_Y + 280, w: 620 });
S.text(pb, "cover countdown", "147 gün · erken kayıt 31 Ocak 2027'de kapanıyor · 96 oturum",
  "meta", "ink.600", { x: 160, y: COVER_Y + 322, w: 600 });

/* the cover figure: a three-lead strip drawn here, 25 mm/s · 10 mm/mV */
S.text(pb, "cover figure label", "KAPAK · EKG KAYDI", "label", "ink.500", { x: 160, y: COVER_Y + 360 });
coverGrid(pb, "cover ecg minor", 160, FIG_Y, 640, 220, 8, 40, "line.soft");
coverGrid(pb, "cover ecg major", 160, FIG_Y, 640, 220, 40, 0, "line.300");
["I", "II", "III"].forEach((lead, i) => {
  S.text(pb, "cover lead " + i, lead, "label", "ink.500", { x: 168, y: FIG_Y + 26 + i * 70 });
  coverTrace(pb, "cover trace " + i, 200, FIG_Y + 48 + i * 70, 580, [52, 64, 44][i], 4);
});
S.text(pb, "cover caption", "25 mm/s · 10 mm/mV", "meta", "ink.500",
  { x: 160, y: COVER_Y + 620 });

/* the contents column: the issue's pages are the site's paths */
S.text(pb, "cover toc label", "BU SAYIDA", "label", "ink.500", { x: 880, y: COVER_Y + 142 });
const coverToc = [
  ["Kongre", "s. 01", "Program ve kayıt"],
  ["Kılavuzlar", "s. 12", "2027 hipertansiyon"],
  ["Akademi", "s. 30", "KKY kursu · 6 STE"],
  ["Yayın", "s. 38", "Dergi ve kılavuz"],
  ["Topluluk", "s. 44", "41 il · 12 çalışma grubu"],
  ["Haberler", "s. 50", "Bu hafta"],
];
coverToc.forEach((t, i) => {
  const ty = COVER_Y + 180 + i * 64;
  S.text(pb, "toc name " + i, t[0], "bodyMed", "ink.900", { x: 880, y: ty });
  S.text(pb, "toc page " + i, t[1], "data", "ink.500", { x: 1180, y: ty + 2, w: 100, align: "right" });
  S.text(pb, "toc note " + i, t[2], "meta", "ink.500", { x: 880, y: ty + 24, w: 280 });
  S.rule(pb, "toc rule " + i, 880, ty + 54, 400, "line.soft", 1);
});
S.ctaRow(pb, "hero cta", 880, COVER_Y + 620, "Kongreye kayıt ol",
  { w: 236, link: "Derneği tanı", gap: 24 });
S.text(pb, "cover imprint", "6.847 üye · 41 il · 12 çalışma grubu · 10 kılavuz", "meta", "ink.500",
  { x: 160, y: COVER_Y + 680, w: 700 });
let y = COVER_Y + COVER_H;
/* --------------------------------------------------------------- gündem */
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
