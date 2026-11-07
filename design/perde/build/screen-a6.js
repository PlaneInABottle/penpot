// A6 · pixel components — an 8-bit layer that could sit on top of the Maket world.
__SPRITES__
const P = {
  bg: "#EDE6D6",
  paper: "#F6F0E1",
  white: "#FFFFFF",
  ink: "#1E1B2E",
  soft: "#5F5A6B",
  red: "#D1495B",
  yellow: "#F2C14E",
  green: "#4C956C",
  blue: "#3D5A80",
  grey: "#A8A29A",
};
const CAT = { tiyatro: P.red, konser: P.yellow, sergi: P.green, sahne: P.blue };

const page = penpot.currentPage;
for (const c of page.findShapes({ name: "A6-piksel" })) c.remove();

const HARD = { style: "drop-shadow", offsetX: 4, offsetY: 4, blur: 0, spread: 0, color: { color: "#1E1B2E", opacity: 1 } };
const HARD_SM = { style: "drop-shadow", offsetX: 3, offsetY: 3, blur: 0, spread: 0, color: { color: "#1E1B2E", opacity: 1 } };

function px(b, name, x, y, w, h, fill, o) {
  o = o || {};
  return box(b, name, x, y, w, h, {
    fill: fill, radius: 0,
    stroke: o.stroke === null ? null : (o.stroke || P.ink),
    sw: o.sw || 2,
    shadow: o.flat ? null : (o.small ? HARD_SM : HARD),
  });
}

function vt(b, name, text, x, y, size, color, o) {
  o = o || {};
  return txt(b, name, text, x, y, o.w || 400, {
    font: "VT323", size: size, weight: 400, color: color,
    align: o.align, track: o.track == null ? 0 : o.track,
  });
}

function sil(b, name, text, x, y, size, color, o) {
  o = o || {};
  return txt(b, name, text, x, y, o.w || 400, {
    font: "Silkscreen", size: size, weight: 400, color: color,
    align: o.align, track: o.track == null ? 0 : o.track,
  });
}

function section(b, name, x, y, text) {
  sil(b, name, text, x, y, 9, P.soft, { track: 1.2, w: 400 });
}

const b = board("A6-piksel", 2400, 1000, 1200, 900, P.bg);

txt(b, "t", "Piksel parçalar", 40, 26, 600, { font: "Fraunces", size: 30, weight: 600, color: P.ink });
txt(b, "s", "Maket dünyasının üstüne konabilecek 8-bit katman: düğme, çip, sekme, arama, dialog, satır, etiket.", 40, 66, 1000, {
  font: "Work Sans", size: 12, weight: 400, color: P.soft,
});

// --- buttons ---------------------------------------------------------------
section(b, "s-btn", 40, 108, "DÜĞMELER");
px(b, "btn-p", 40, 130, 132, 40, P.ink);
sil(b, "btn-p-t", "BILET AL", 40, 143, 10, P.paper, { w: 132, align: "center" });
px(b, "btn-s", 188, 130, 132, 40, P.paper);
sil(b, "btn-s-t", "DETAY", 188, 143, 10, P.ink, { w: 132, align: "center" });
txt(b, "btn-g-t", "Haritada gör →", 336, 138, 140, { font: "VT323", size: 20, weight: 400, color: P.ink });
px(b, "btn-d", 500, 130, 132, 40, P.grey, { stroke: P.grey, flat: true });
sil(b, "btn-d-t", "TÜKENDİ", 500, 143, 10, "#F6F0E1", { w: 132, align: "center" });
txt(b, "btn-note-t", "2px kenar · 4px sert gölge", 652, 138, 300, { font: "VT323", size: 19, weight: 400, color: P.soft });

// --- chips -----------------------------------------------------------------
section(b, "s-chip", 40, 194, "ÇİPLER");
[["Tiyatro", P.red, false, 40], ["Tiyatro", P.paper, true, 176], ["Sergi", P.green, false, 312]].forEach(function (c, i) {
  px(b, "chip-" + i, c[3], 216, 124, 36, c[2] ? P.ink : P.paper, { small: true, stroke: c[2] ? P.ink : P.ink });
  box(b, "chip-d-" + i, c[3] + 12, 231, 7, 7, { fill: c[1] });
  sil(b, "chip-t-" + i, c[0].toUpperCase(), c[3] + 26, 227, 9, c[2] ? P.paper : P.ink, { w: 88 });
});
px(b, "chip-more", 456, 216, 56, 36, P.paper, { small: true });
sil(b, "chip-more-t", "+3", 456, 227, 9, P.ink, { w: 56, align: "center" });

// --- tabs + search ---------------------------------------------------------
section(b, "s-tab", 40, 278, "SEKME VE ARAMA");
[["BU AKŞAM", true, 0], ["YARIN", false, 1], ["BU HAFTA", false, 2]].forEach(function (t) {
  const x = 40 + t[2] * 116;
  sil(b, "tab-" + t[2], t[0], x, 302, 9, t[1] ? P.ink : P.soft, { w: 110 });
  if (t[1]) box(b, "tab-line-" + t[2], x, 320, 92, 3, { fill: P.red });
});
px(b, "search", 420, 296, 360, 44, P.white, { small: true });
searchIcon(b, "search-lens", 442, 316, 6, P.ink, 2);
vt(b, "search-ph", "Mekân, etkinlik veya semt ara", 458, 306, 20, P.soft, { w: 280 });
px(b, "search-key", 736, 304, 30, 28, P.paper, { small: true, flat: true });
sil(b, "search-key-t", "K", 736, 313, 10, P.ink, { w: 30, align: "center" });

// --- dialog ----------------------------------------------------------------
section(b, "s-dlg", 40, 372, "DİALOG");
px(b, "dlg", 40, 394, 380, 244, P.paper);
box(b, "dlg-head", 42, 396, 376, 32, { fill: P.red });
sil(b, "dlg-cat", "TIYATRO · 20.30", 56, 405, 9, P.paper, { w: 320 });
sil(b, "dlg-title", "GODOT'YU", 58, 442, 16, P.ink, { w: 340 });
sil(b, "dlg-title2", "BEKLERKEN", 58, 466, 16, P.ink, { w: 340 });
vt(b, "dlg-venue", "Kenter Tiyatrosu · Beyoğlu", 58, 496, 20, P.soft, { w: 330 });
for (let i = 0; i < 20; i++) box(b, "dlg-dash-" + i, 58 + i * 16, 524, 9, 2, { fill: P.ink, opacity: 0.25 });
vt(b, "dlg-time", "20.30", 58, 536, 30, P.ink, { w: 90 });
vt(b, "dlg-day", "Cuma 7 Kasım", 150, 546, 20, P.soft, { w: 150 });
vt(b, "dlg-price", "₺240", 300, 540, 26, P.red, { w: 100, align: "right" });
px(b, "dlg-cta", 58, 578, 150, 40, P.ink, { small: true });
sil(b, "dlg-cta-t", "BILET AL", 58, 591, 10, P.paper, { w: 150, align: "center" });
px(b, "dlg-alt", 222, 578, 150, 40, P.paper, { small: true, flat: true });
sil(b, "dlg-alt-t", "DETAY", 222, 591, 10, P.ink, { w: 150, align: "center" });

// --- rows ------------------------------------------------------------------
section(b, "s-row", 460, 372, "SATIR");
[[400, false], [506, true]].forEach(function (r, i) {
  const y = r[0];
  px(b, "row-" + i, 460, y, 380, 96, P.paper);
  if (r[1]) box(b, "row-bar-" + i, 462, y + 2, 6, 92, { fill: P.red });
  vt(b, "row-time-" + i, "20.30", 484, y + 14, 22, P.red, { w: 70 });
  box(b, "row-dot-" + i, 556, y + 20, 8, 8, { fill: P.red });
  sil(b, "row-title-" + i, "GODOT'YU BEKLERKEN", 484, y + 42, 10, P.ink, { w: 300 });
  vt(b, "row-venue-" + i, "Kenter Tiyatrosu", 484, y + 64, 19, P.soft, { w: 220 });
  vt(b, "row-price-" + i, "₺240", 700, y + 56, 22, P.ink, { w: 110, align: "right" });
});

// --- badges ----------------------------------------------------------------
section(b, "s-badge", 460, 618, "ETİKET");
[["SON 4 BİLET", P.red, 460, 118], ["ÜCRETSİZ", P.green, 590, 100], ["18+", P.ink, 704, 64]].forEach(function (g, i) {
  px(b, "badge-" + i, g[2], 640, g[3], 28, g[1], { small: true, stroke: g[1], flat: true });
  vt(b, "badge-t-" + i, g[0], g[2], 644, 17, P.paper, { w: g[3], align: "center" });
});

// --- toast -----------------------------------------------------------------
section(b, "s-toast", 820, 618, "TOAST");
px(b, "toast", 820, 640, 340, 60, P.ink);
box(b, "toast-dot", 836, 662, 10, 10, { fill: P.green });
vt(b, "toast-t", "Takvime eklendi · 7 Kasım", 856, 654, 22, P.paper, { w: 290 });
sil(b, "toast-x", "X", 1130, 660, 10, P.soft, { w: 20, align: "center" });

// --- pins ------------------------------------------------------------------
section(b, "s-pin", 40, 672, "PİN · FİGÜR");
[["penguen", "tiyatro", 48], ["marti", "sergi", 48], ["fincan", "konser", 48], ["maske", "tiyatro", 48]].forEach(function (p, i) {
  const x = 90 + i * 120;
  const w = SPRITES[p[0]].rows[0].length * 3;
  plinth(b, "pin-b-" + i, x, 786, CAT[p[1]], w * 0.6);
  spriteMap(b, "pin-s-" + i, x, 786, SPRITES[p[0]], 3);
  vt(b, "pin-l-" + i, p[0], x - 60, 794, 18, P.soft, { w: 120, align: "center" });
});

return { ok: true, boards: [b.name] };
