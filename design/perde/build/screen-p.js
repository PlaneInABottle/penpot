// P · Piksel — 8-bit city, hard shadows, sprite pins. A test, not a full direction yet.
const P = {
  ink: "#1E1B2E",
  paper: "#F6F0E1",
  white: "#FFFFFF",
  soft: "#5F5A6B",
  red: "#D1495B",
  yellow: "#F2C14E",
  green: "#4C956C",
  blue: "#3D5A80",
  grey: "#A8A29A",
};
const CAT = { tiyatro: P.red, konser: P.yellow, sergi: P.green, sahne: P.blue };

const PIN_ROWS = [
  "..#####..",
  ".#######.",
  "##.###.##",
  "##.###.##",
  "#########",
  ".#######.",
  "..#####..",
  "...###...",
  "....#....",
  "....#....",
  "....#....",
];

const page = penpot.currentPage;
["P1-harita", "P2-parcalar"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

const HARD = {
  style: "drop-shadow", offsetX: 5, offsetY: 5, blur: 0, spread: 0,
  color: { color: "#1E1B2E", opacity: 1 },
};
const HARD_SM = {
  style: "drop-shadow", offsetX: 3, offsetY: 3, blur: 0, spread: 0,
  color: { color: "#1E1B2E", opacity: 1 },
};

function panel(b, name, x, y, w, h, fill, opts) {
  opts = opts || {};
  return box(b, name, x, y, w, h, {
    fill: fill, radius: 0, stroke: P.ink, sw: 2,
    shadow: opts.flat ? null : (opts.small ? HARD_SM : HARD),
  });
}

function pix(b, name, text, x, y, size, color, opts) {
  opts = opts || {};
  return txt(b, name, text, x, y, opts.w || 500, {
    font: opts.font || "Silkscreen", size: size, weight: opts.weight || 400,
    color: color, track: opts.track == null ? 0 : opts.track, align: opts.align,
  });
}

function skullPin(b, name, x, y, color) {
  sprite(b, name, x, y, PIN_ROWS, color, 4);
}

// ---- P1 · the map ----------------------------------------------------------
const p1 = board("P1-harita", 0, 3600, 1440, 900, P.paper);
const map = box(p1, "map", 0, 0, 1440, 900, {});
map.fills = [{ fillOpacity: 1, fillImage: assetMedia("__map-pixel") }];
box(p1, "scan", 0, 0, 1440, 900, { fill: "#F6F0E1", opacity: 0.18 });

// wordmark
panel(p1, "brand", 28, 28, 236, 64, P.paper);
pix(p1, "brand-t", "PERDE", 44, 40, 20, P.ink, { w: 200, track: 1 });
pix(p1, "brand-s", "İSTANBUL KÜLTÜR HARİTASI", 44, 66, 9, P.soft, { w: 210, font: "VT323" });

// search
panel(p1, "search", 1032, 28, 380, 46, P.white);
pix(p1, "search-ph", "Mekân, etkinlik veya semt ara", 1050, 36, 22, P.soft, { font: "VT323", w: 320 });
box(p1, "search-key", 1360, 38, 36, 26, { fill: P.paper, radius: 0, stroke: P.ink, sw: 2 });
pix(p1, "search-key-t", "K", 1372, 44, 12, P.ink);

// time tabs
[["BU AKŞAM", true, 0], ["YARIN", false, 1], ["BU HAFTA", false, 2]].forEach(function (t) {
  const w = 104, x = 1032 + t[2] * (w + 4);
  if (t[1]) panel(p1, "tab-" + t[2], x, 88, w, 30, P.red, { small: true });
  else panel(p1, "tab-" + t[2], x, 88, w, 30, P.paper, { small: true, flat: true });
  pix(p1, "tab-t-" + t[2], t[0], x + 8, 95, 10, t[1] ? P.paper : P.ink, { w: w - 16, align: "center" });
});

// categories
[["Tiyatro", "5", P.red], ["Konser", "3", P.yellow], ["Sergi", "2", P.green], ["Sahne", "2", P.blue]]
  .forEach(function (c, i) {
    const x = 28 + i * 118;
    panel(p1, "cat-" + i, x, 826, 108, 40, P.paper, { small: true });
    box(p1, "cat-dot-" + i, x + 12, 843, 8, 8, { fill: c[2] });
    pix(p1, "cat-t-" + i, c[0], x + 26, 836, 10, P.ink, { w: 70 });
    pix(p1, "cat-n-" + i, c[1], x + 78, 836, 10, P.soft, { w: 24, align: "right" });
  });

[[260, 230, "sergi"], [610, 180, "konser"], [430, 330, "sahne"],
 [300, 470, "tiyatro"], [520, 560, "tiyatro"], [230, 650, "tiyatro"]]
  .forEach(function (p, i) { skullPin(p1, "pin-" + i, p[0], p[1], CAT[p[2]]); });

pix(p1, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 28, 880, 18, P.soft, {
  font: "VT323", w: 520,
});

// ---- P2 · parts ------------------------------------------------------------
const p2 = board("P2-parcalar", 1520, 3600, 760, 520, P.paper);
pix(p2, "s-title", "PİKSEL PARÇALAR", 28, 24, 16, P.ink, { track: 1 });

[["tiyatro", P.red], ["konser", P.yellow], ["sergi", P.green], ["sahne", P.blue]]
  .forEach(function (c, i) {
    const x = 70 + i * 90;
    skullPin(p2, "p-" + c[0], x, 140, c[1]);
    pix(p2, "p-l-" + c[0], c[0].toUpperCase(), x - 44, 150, 8, P.soft, { w: 88, align: "center" });
  });

// dialog
panel(p2, "dlg", 28, 200, 360, 220, P.paper);
box(p2, "dlg-head", 28, 200, 360, 30, { fill: P.red, radius: 0 });
pix(p2, "dlg-cat", "TİYATRO · 20.30", 42, 208, 9, P.paper, { w: 300 });
pix(p2, "dlg-title", "GODOT'YU", 42, 246, 18, P.ink, { w: 300 });
pix(p2, "dlg-title2", "BEKLERKEN", 42, 268, 18, P.ink, { w: 300 });
pix(p2, "dlg-venue", "Kenter Tiyatrosu · Beyoğlu", 42, 300, 19, P.soft, { font: "VT323", w: 300 });
pix(p2, "dlg-len", "2 perde · 2sa 15dk", 42, 324, 19, P.soft, { font: "VT323", w: 220 });
pix(p2, "dlg-price", "₺240", 250, 318, 26, P.ink, { font: "VT323", w: 100, align: "right" });
panel(p2, "dlg-cta", 42, 352, 140, 38, P.ink, { small: true });
pix(p2, "dlg-cta-t", "BİLET AL", 42, 363, 11, P.paper, { w: 140, align: "center", track: 1 });
panel(p2, "dlg-alt", 196, 352, 140, 38, P.paper, { small: true, flat: true });
pix(p2, "dlg-alt-t", "DETAY", 196, 363, 11, P.ink, { w: 140, align: "center", track: 1 });

// list row
panel(p2, "row", 420, 200, 312, 96, P.paper);
pix(p2, "row-time", "20.30", 436, 214, 14, P.red, { w: 80 });
pix(p2, "row-title", "GODOT'YU BEKLERKEN", 436, 236, 10, P.ink, { w: 270 });
pix(p2, "row-venue", "Kenter Tiyatrosu", 436, 258, 18, P.soft, { font: "VT323", w: 200 });
pix(p2, "row-price", "₺240", 620, 250, 22, P.ink, { font: "VT323", w: 96, align: "right" });

return { ok: true, boards: [p1.name, p2.name] };
