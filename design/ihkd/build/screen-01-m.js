/**
 * 01-m — Ana sayfa, mobil (390 wide, 844 viewport). M3: copy fidelity + measured rows.
 *
 *   python3 design/ihkd/build/build.py screen-01-m
 *
 * Story (desktop §5, stacked): hook = the congress poster; path = çalışma
 * grupları → akademi → yayın → gündem; action = the white membership band.
 * Section rhythm 64 at the board edge, one column, every tap row ≥44; only the
 * footer's four link groups keep two columns (169 + 12 + 169 = 350).
 *
 * Copy is the desktop board's, verbatim — a mobile screen may refold a line, it
 * may not reword one. The only strings that differ are MENÜ / KAPAT (the menu
 * control), the forced two-line date, and the `12` numeral, which is dropped.
 *
 * Slot heights are measured, not modelled. Penpot lays out a text when the page
 * updates, so the strings whose wrap decides a slot (head titles, row titles,
 * the member block, the notes, the legal) are created once, `waitForLayoutUpdate`
 * settles them, their heights are read, and they are removed before the build.
 * A char model cannot do this: `S.estLines` gives cpl 31 at 22px/350 and would
 * reserve two lines for `Kalp yetersizliğinde güncel tedavi` (34 chars), which
 * measures one line (316px) — the 35–37px title→meta gaps of M2. The mobile
 * copy is longer than M2's, so every height below comes from the same pass.
 *
 * Poster (M2 fix, unchanged): H 928 → 64..992; photo band 0..320 on `ink.900`,
 * copy from +344 (the fallback offset that held AA), foot at H−188/H−128/H−56,
 * so the fold at 844 shows the label through the society line and the ECG sits
 * below it. No scrim, no gradient.
 */
const S = IK;
const M = S.M;

const X = M.X, CW = M.CW, W = M.W, RHYTHM = M.RHYTHM;
const HERO_Y = 64, HERO_H = 928, FOLD = 844;
const COPY = 344;   // fallback copy top: the photo holds 0..320, then 24px air
const PIC_H = 320;

/* ---------------------------------------------------------------- content */
const GROUPS = [
  ["01", "Kardiyovasküler görüntüleme", "412 üye · Doç. Dr. Elif Karaca"],
  ["02", "Kalp yetersizliği", "508 üye · Prof. Dr. Murat Şen"],
  ["03", "Aritmi ve elektrofizyoloji", "287 üye · Prof. Dr. Ayşe Tunç"],
  ["04", "Kardiyometabolik", "366 üye · Doç. Dr. Kerem Yalçın"],
  ["05", "Hipertansiyon", "341 üye · Prof. Dr. Sema Yıldız"],
  ["06", "Geriatrik kardiyoloji", "198 üye · Doç. Dr. Deniz Arslan"],
];
const COURSES = [
  ["Kalp yetersizliğinde güncel tedavi", "8 modül · 6 STE · 4s 20dk"],
  ["Ekokardiyografi: temelden ileriye", "12 modül · 9 STE · 7s 05dk"],
  ["Antikoagülasyon yönetimi", "5 modül · 3 STE · 2s 40dk"],
];
const AK_NOTE = "Kurslar üyeler için ücretsiz; STE kredisi kurs bitiminde yüklenir.";
const TOC = [
  ["12", "STE olmayan hastada BKA: 2027 uzlaşısı"],
  ["28", "KKY'de SGLT2 inhibitörleri:\ngerçek yaşam verisi"],
  ["41", "Genç sporcularda EKG taramasının maliyeti"],
];
const GUIDE_TITLE = "Hipertansiyon tanı ve tedavi kılavuzu";
const GUIDE_BODY = "Ev ölçümü, ofis dışı tansiyon ve tedavi eşikleri üzerine İHKD kılavuzu.";
const NEWS = [
  ["12 Mart 2027", "Kongre", "Program yayınlandı:\n96 oturum, dört salon", "6 dk"],
  ["4 Mart 2027", "Akademi", "Kalp yetersizliği kursu için\nkayıtlar açıldı", "2 dk"],
  ["26 Şubat 2027", "Dernek", "Çalışma grubu başkanları belirlendi", "4 dk"],
];
const NEWS_NOTE = "Duyurular Pazartesi 09:00'da yayımlanır.";
const MB_TITLE = "Yazan, toplayan, öğreten.";
const MB_LEDE = "Üyelik; kılavuz arşivini, kongre ücretini ve STE kredili kursları açar.";
const MB_GAIN = [
  "Kılavuzların ve dergi arşivinin tamamı",
  "Kongre kaydında üye ücreti",
  "Akademi kursları ücretsiz, STE kredisi bitiminde",
];
const MB_FEE = "Yıllık aidat 2.400 TL · Öğrenci 600 TL · Başvuru 3 adım";
const FOOT_LEGAL = "© 2026 İHKD · KVKK · Çerez politikası\nTasarım çalışması\n— kurum ve kişiler kurgudur.";

/* One layout pass is awaited for the measure pass. `build.py --dry-run`
   runs `node --check`, which rejects top-level await in a CommonJS file,
   so the build is a single async IIFE; the plugin runner resolves the
   returned promise (the path media.py and flows.js already use). */
return (async () => {
  const pb = M.start("Mobil", "01-ana-sayfa-m", FOLD);

  /* ------------------------------------------------------------ measure pass */
  /* One text per slot that a wrap decides. Same role, width and string as the
     real node, so the laid-out height is the height the real node will take. */
  const MEASURE = [
    { k: "h01", role: "h2", w: CW, text: "On iki grup, on iki soru." },
    { k: "h02", role: "h2", w: CW, text: "Kurs, kılavuz, STE" },
    { k: "h03", role: "h2", w: CW, text: "Dergi ve kılavuz" },
    { k: "h04", role: "h2", w: CW, text: "Bu hafta" },
    ...GROUPS.map((g, i) => ({ k: "g" + i, role: "h3", w: 278, text: g[1] })),
    ...COURSES.map((c, i) => ({ k: "c" + i, role: "h3", w: CW, text: c[0] })),
    ...NEWS.map((n, i) => ({ k: "n" + i, role: "h3", w: CW, text: n[2] })),
    { k: "jt", role: "h3", w: CW, text: "Kardiyovasküler Klinik" },
    { k: "gt", role: "h3", w: CW, text: GUIDE_TITLE },
    { k: "gb", role: "body", w: CW, text: GUIDE_BODY },
    { k: "an", role: "meta", w: CW, text: AK_NOTE },
    { k: "nn", role: "meta", w: CW, text: NEWS_NOTE },
    { k: "mt", role: "h2", w: CW, text: MB_TITLE },
    { k: "ml", role: "lead", w: CW, text: MB_LEDE },
    ...MB_GAIN.map((s, i) => ({ k: "mg" + i, role: "body", w: CW - 20, text: s })),
    { k: "mf", role: "meta", w: CW, text: MB_FEE },
    { k: "fl", role: "data", w: CW, text: FOOT_LEGAL },
  ];
  const probes = MEASURE.map((s) => M.textM(pb, "__measure__ " + s.k, s.text, s.role, "ink.900",
    { x: X, y: 0, w: s.w }));
  await penpot.waitForLayoutUpdate();
  const H = {};
  probes.forEach((t, i) => { H[MEASURE[i].k] = Math.round(t.height); });
  probes.forEach((t) => t.remove());

  M.masthead(pb);

  /* ------------------------------------------------------------------- poster */
  const hero = S.board(pb, "hero scene", 0, HERO_Y, W, HERO_H, "ink.900");
  /* the photo slot: restored from provenance (Pexels 20733081, centre crop) by
     build.py; it is a 390×320 band, not the poster's backdrop */
  S.rect(hero, "img-hero", 0, HERO_Y, W, PIC_H, "surface.alt");

  /* the label runs two lines at 350; it is the poster's only 13px mono line */
  M.textM(hero, "hero label", "12. ULUSAL İÇ HASTALIKLARI VE KARDİYOLOJİ KONGRESİ",
    "label", "on.ink", { x: X, y: HERO_Y + COPY, w: CW });
  /* forced two lines: the edition's last figure sits under the date, not after it */
  M.textM(hero, "hero date", "22–25 Nisan\n2027", "display", "on.ink",
    { x: X, y: HERO_Y + COPY + 44, w: CW });
  M.textM(hero, "hero venue", "Antalya Kongre Merkezi, Belek · 96 oturum\n· 214 konuşmacı",
    "body", "on.ink", { x: X, y: HERO_Y + COPY + 146, w: CW });
  /* one figure + one note: the value carries the sentence, as on the desktop */
  M.textM(hero, "hero countdown value", "147", "stat", "on.ink",
    { x: X, y: HERO_Y + COPY + 214 });
  M.textM(hero, "hero countdown note", "gün kaldı · erken kayıt\n31 Ocak 2027'de kapanıyor",
    "meta", "on.ink", { x: 110, y: HERO_Y + COPY + 216, w: 250 });
  /* the one saturated action; the ghost route sits under it as a 44px row */
  S.btn(hero, "hero cta", "Kongreye kayıt ol", X, HERO_Y + COPY + 276, CW, 52, "primary");
  S.link(hero, "hero cta link", "Programı gör", X, HERO_Y + COPY + 340 + 11, "on.ink");
  /* the society speaks at the poster's foot: signature, trace, imprint — the
     signature closes 21px under the ghost route and 13px above the fold */
  M.textM(hero, "hero society", "Hastanın hekimi.", "h3", "on.ink",
    { x: X, y: HERO_Y + HERO_H - 188, w: CW });
  S.ecg(hero, "hero ecg", 0, HERO_Y + HERO_H - 128, W, 24, "on.ink");
  M.textM(hero, "hero society line", "İHKD · İç Hastalıkları ve Kardiyoloji Derneği · 1998'den beri Ankara",
    "label", "on.ink", { x: X, y: HERO_Y + HERO_H - 56, w: CW });

  /* ---------------------------------------------------------------- section head */
  /**
   * Mobile head: order numeral (figure 22, ink.400) at 20, kicker at 56, title
   * (h2 30) 40 below the head top on the full 350 measure, `line.strong` under
   * the measured title box (12px), content 40 under the rule. No right link.
   */
  let NUM = 0;
  function head(y, key, label, title) {
    NUM += 1;
    const num = ("0" + NUM).slice(-2);
    M.textM(pb, "head num " + num, num, "figure", "ink.400", { x: X, y: y });
    M.textM(pb, "head label " + label, label, "label", "ink.500", { x: 56, y: y + 4 });
    M.textM(pb, "head title " + label, title, "h2", "ink.900", { x: X, y: y + 40, w: CW });
    const ruleY = y + 40 + H[key] + 12;
    S.rule(pb, "head rule " + label, X, ruleY, CW, "line.strong", 1);
    return ruleY + 40;
  }

  /* --------------------------------------------------------- §01 çalışma grupları */
  let y = HERO_Y + HERO_H;
  y = head(y + RHYTHM, "h01", "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.");

  /* index column 32 at 20, title from 72 to the arrow's box at 350, arrow on the
     right grid edge. The title measure stops at 278 so no line can run into it. */
  const GTW = 278;
  y = S.rows(pb, "group", X, y, CW, GROUPS.map((g, i) => {
    const th = H["g" + i];
    return {
      h: 20 + th + 8 + 20 + 16,
      draw(yRow) {
        M.textM(pb, "group idx " + i, g[0], "data", "ink.500", { x: X, y: yRow + 22 });
        M.textM(pb, "group name " + i, g[1], "h3", "ink.900", { x: 72, y: yRow + 20, w: GTW });
        M.textM(pb, "group meta " + i, g[2], "meta", "ink.500",
          { x: 72, y: yRow + 20 + th + 8, w: GTW });
        M.textM(pb, "group arrow " + i, "→", "nav", "ink.500",
          { x: X + CW - 20, y: yRow + 22, w: 20, align: "right" });
      },
    };
  }), { rule: "line.soft" });
  S.link(pb, "groups all", "12 çalışma grubunun tümü →", X, y + 11, "red.700");
  y += 44;

  /* --------------------------------------------------------------- §02 akademi */
  y = head(y + RHYTHM, "h02", "AKADEMİ", "Kurs, kılavuz, STE");
  /* meta left, action right on one line under the title */
  const CMW = 230, CAW = 120;
  y = S.rows(pb, "course", X, y, CW, COURSES.map((c, i) => {
    const th = H["c" + i];
    return {
      h: 20 + th + 8 + 24 + 16,
      draw(yRow) {
        const my = yRow + 20 + th + 8;
        M.textM(pb, "course title " + i, c[0], "h3", "ink.900", { x: X, y: yRow + 20, w: CW });
        M.textM(pb, "course meta " + i, c[1], "data", "ink.500", { x: X, y: my + 2, w: CMW });
        M.textM(pb, "course cta " + i, "Başla →", "nav", "red.700",
          { x: X + CW - CAW, y: my - 1, w: CAW, align: "right" });
      },
    };
  }), { rule: "line.soft" });
  M.textM(pb, "akademi note", AK_NOTE, "meta", "ink.500", { x: X, y: y + 24, w: CW });
  y += 24 + H.an;

  /* ----------------------------------------------------------------- §03 yayın */
  y = head(y + RHYTHM, "h03", "YAYIN", "Dergi ve kılavuz");
  const JY = y;
  S.photo(pb, "img-journal", X, JY, CW, 300, "Kardiyovasküler Klinik, cilt 12");
  let jy = JY + 300 + 12 + 20 + 16;
  M.textM(pb, "journal title", "Kardiyovasküler Klinik", "h3", "ink.900", { x: X, y: jy, w: CW });
  jy += H.jt + 8;
  M.textM(pb, "journal meta", "Cilt 12 · Sayı 1 · Mart 2027 · TR Dizin", "data", "ink.500",
    { x: X, y: jy, w: CW });
  jy += 20 + 16;
  /* page gutter 40, body title from 68; one 80px row per article */
  jy = S.rows(pb, "toc", X, jy, CW, TOC.map((t, i) => ({
    h: 80,
    draw(yRow) {
      M.textM(pb, "toc page " + i, "s. " + t[0], "data", "ink.500", { x: X, y: yRow + 16, w: 40 });
      M.textM(pb, "toc title " + i, t[1], "body", "ink.700", { x: 68, y: yRow + 14, w: CW - 48 });
    },
  })), { rule: "line.soft" });
  S.link(pb, "journal cta", "Sayıyı oku", X, jy + 11, "red.700");
  jy += 44;

  /* the guide is a second publication, not a continuation of the issue */
  S.rule(pb, "pub div", X, jy, CW, "line.soft", 1);
  M.textM(pb, "guide label", "AYIN KILAVUZU", "label", "ink.500", { x: X, y: jy + 24 });
  let gy = jy + 24 + 16 + 8;
  M.textM(pb, "guide title", GUIDE_TITLE, "h3", "ink.900", { x: X, y: gy, w: CW });
  gy += H.gt + 10;
  M.textM(pb, "guide meta", "2027 · Kanıt A · 48 sayfa · 3,2 MB", "data", "ink.500",
    { x: X, y: gy, w: CW });
  gy += 20 + 16;
  /* the ECG is an instrument on the one guideline the page features */
  S.ecg(pb, "guide ecg", X, gy, CW, 32, "red.600");
  gy += 32 + 16;
  M.textM(pb, "guide body", GUIDE_BODY, "body", "ink.600", { x: X, y: gy, w: CW });
  gy += H.gb + 12;
  S.link(pb, "guide cta", "Kılavuzu indir", X, gy + 11, "ink.900");
  y = gy + 44;

  /* ---------------------------------------------------------------- §04 gündem */
  y = head(y + RHYTHM, "h04", "GÜNDEM", "Bu hafta");
  /* line 1 is the record (date, category, reading time); the title owns line 2+ */
  y = S.rows(pb, "news", X, y, CW, NEWS.map((n, i) => {
    const th = H["n" + i];
    return {
      h: 44 + th + 20,
      draw(yRow) {
        M.textM(pb, "news date " + i, n[0], "data", "ink.500", { x: X, y: yRow + 20, w: 110 });
        M.textM(pb, "news cat " + i, n[1], "label", "ink.500", { x: 136, y: yRow + 20 });
        M.textM(pb, "news time " + i, n[3], "data", "ink.500",
          { x: X + CW - 100, y: yRow + 20, w: 100, align: "right" });
        M.textM(pb, "news title " + i, n[2], "h3", "ink.900", { x: X, y: yRow + 44, w: CW });
      },
    };
  }), { rule: "line.soft" });
  S.link(pb, "news all", "Tüm haberler →", X, y + 11, "ink.900");
  y += 44;
  M.textM(pb, "news note", NEWS_NOTE, "meta", "ink.500", { x: X, y: y + 16, w: CW });
  y += 16 + H.nn;

  /* --------------------------------------------------------------- üyelik band */
  /* White band, 20/56 padding, no saturated button: the route is a text row. */
  const bandY = y + RHYTHM;
  const band = S.board(pb, "uyelik band", 0, bandY, W, 300, "white");
  M.textM(band, "member label", "ÜYELİK", "label", "ink.500", { x: X, y: bandY + 56 });
  const mbTitleY = bandY + 56 + 16 + 12;
  M.textM(band, "member title", MB_TITLE, "h2", "ink.900", { x: X, y: mbTitleY, w: CW });
  const mbLedeY = mbTitleY + H.mt + 16;
  M.textM(band, "member lede", MB_LEDE, "lead", "ink.600", { x: X, y: mbLedeY, w: CW });
  const mbBulY = mbLedeY + H.ml + 24;
  /* the shared S.bullets sizes each row from estLines (0.5em); the third line is
     50 chars and estimates two lines while it measures one. The block is drawn
     from the measured heights instead — dot 6, text at +20, 6px pad, as bullets(). */
  let by = mbBulY;
  MB_GAIN.forEach((item, i) => {
    const th = H["mg" + i];
    M.textM(band, "member gain item " + i, item, "body", "ink.700",
      { x: X + 20, y: by + 6, w: CW - 20 });
    S.rect(band, "member gain dot " + i, X, by + 6 + 16 * 1.6 / 2 - 3, 6, 6,
      "red.600", { raw: true });
    by += 12 + th;
  });
  const mbLinkY = by - 6 + 12;
  S.link(band, "member cta", "Başvuruyu başlat →", X, mbLinkY + 11, "red.700");
  const mbFeeY = mbLinkY + 44 + 8;
  M.textM(band, "member fee", MB_FEE, "meta", "ink.500", { x: X, y: mbFeeY, w: CW });
  const mbBottom = mbFeeY + H.mf + 56;
  band.resize(W, S.snap(mbBottom - bandY));

  /* -------------------------------------------------------------------- footer */
  const FY = S.snap(mbBottom + 56);
  const fCol = 169, fGap = 12, fLinkH = 44;   // every footer link is a 44px tap row
  const fMarkY = FY + 40, fClaimY = FY + 76, fAddrY = FY + 125;
  const fGroupsY = FY + 189;
  const fGroupH = 16 + 8 + 4 * fLinkH;        // label, gap, four tap rows
  const fRow2Y = fGroupsY + fGroupH + 28;
  const fRuleY = fRow2Y + fGroupH + 28;
  const fLegalY = fRuleY + 24;
  const FB_H = fLegalY + H.fl + 32 - FY;     // height, not a page coordinate

  const fb = S.board(pb, "footer", 0, FY, W, FB_H, "white");
  S.rect(fb, "footer bar", 0, FY, W, 2, "red.600");
  M.textM(fb, "footer mark", "İHKD", "wordmark", "ink.900", { x: X, y: fMarkY });
  M.textM(fb, "footer claim", "Hastanın hekimi.", "lead", "ink.900", { x: X, y: fClaimY, w: CW });
  M.textM(fb, "footer address",
    "Meşrutiyet Cad. 24/7, 06420 Çankaya, Ankara\n+90 312 425 18 40 · info@ihkd.org.tr",
    "meta", "ink.500", { x: X, y: fAddrY, w: CW });
  const footCols = [
    ["Dernek", ["Hakkında", "Yönetim", "Çalışma grupları", "Tüzük"]],
    ["Kongre", ["12. Kongre", "Program", "Bildiri", "Kayıt"]],
    ["Akademi", ["Kurslar", "Kılavuzlar", "Dergi", "STE"]],
    ["Üyelik", ["Başvuru", "Aidat", "Üye girişi", "İletişim"]],
  ];
  footCols.forEach((c, i) => {
    const cx = X + (i % 2) * (fCol + fGap);
    const cy = i < 2 ? fGroupsY : fRow2Y;
    M.textM(fb, "footer col " + i, c[0], "label", "ink.500", { x: cx, y: cy });
    c[1].forEach((it, j) => M.textM(fb, "footer " + i + "." + j, it, "meta", "ink.600",
      { x: cx, y: cy + 24 + j * fLinkH, w: fCol }));
  });
  S.rule(fb, "footer rule", X, fRuleY, CW, "line.soft", 1);
  M.textM(fb, "footer legal", FOOT_LEGAL, "data", "ink.500", { x: X, y: fLegalY, w: CW });

  /* the board ends on the footer's bottom pad: no paper strip under the white */
  pb.resize(W, S.snap(FY + FB_H));

  return JSON.stringify(S.end("01-ana-sayfa-m"));
})();
