// A · Maket — paper diorama. Four separate boards, one idea each.
// map: maket
const P = {
  table: "#E7DBC4",
  paper: "#FCF8EF",
  paperAlt: "#F3EBDA",
  ink: "#2A2419",
  soft: "#6E6450",
  line: "#CFBE9C",
  accent: "#B4553C",
  cat: { tiyatro: "#8E3B46", konser: "#B5762F", sergi: "#4C7A63", sahne: "#4A5C8C" },
};

const page = penpot.currentPage;
["A1-harita", "A2-detay", "A3-liste", "A4-pinler"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

// ---------------------------------------------------------------------------
// shared pieces
// ---------------------------------------------------------------------------
function paintMap(b) {
  const m = box(b, "map", 0, 0, 1440, 900, {});
  m.fills = [{ fillOpacity: 1, fillImage: mapMedia() }];
  const d = box(b, "map-desat", 0, 0, 1440, 900, { fill: "#8E8163", opacity: 0.30 });
  d.blendMode = "saturation";
  box(b, "map-wash", 0, 0, 1440, 900, { fill: "#F2E8D4", opacity: 0.24 });
}

function brandBlock(b, x, y) {
  box(b, "brand-card", x, y, 244, 78, { fill: P.paper, radius: 12, shadow: SHADOW_SOFT, stroke: P.line });
  txt(b, "brand", "Perde", x + 20, y + 14, 200, { font: "Fraunces", size: 30, weight: 600, color: P.ink, track: -0.4 });
  txt(b, "brand-sub", "İstanbul kültür haritası", x + 21, y + 50, 210, { font: "Work Sans", size: 11.5, weight: 500, color: P.soft, track: 0.3 });
}

function searchBlock(b, x, y) {
  box(b, "search", x, y, 412, 54, { fill: P.paper, radius: 27, shadow: SHADOW_SOFT, stroke: P.line });
  searchIcon(b, "search-glass", x + 33, y + 27, 6.5, P.soft, 1.6);
  txt(b, "search-ph", "Mekân, etkinlik veya semt ara", x + 54, y + 18, 280, { font: "Work Sans", size: 13.5, weight: 400, color: P.soft });
  keycap(b, "search-kbd", x + 356, y + 13, 34, 28, "/", P.paperAlt, P.soft, P.line);
}

const CATS = [["tiyatro", "Tiyatro", "5"], ["konser", "Konser", "3"], ["sergi", "Sergi", "2"], ["sahne", "Sahne", "2"]];

function rail(b, x, y) {
  box(b, "rail-chip", x, y, 178, 26, { fill: P.paper, radius: 7, opacity: 0.94, stroke: P.line });
  txt(b, "rail-title", "KATMANLAR · 12", x + 12, y + 7, 150, { font: "Work Sans", size: 10, weight: 700, color: P.ink, track: 1.6 });
  CATS.forEach(function (c, i) {
    const ty = y + 34 + i * 44;
    box(b, "tag-" + c[0], x, ty, 178, 36, { fill: P.paper, radius: 9, shadow: SHADOW_TIGHT, stroke: P.line });
    box(b, "tag-dot-" + c[0], x + 16, ty + 15, 7, 7, { fill: P.cat[c[0]], radius: 3.5 });
    txt(b, "tag-t-" + c[0], c[1], x + 32, ty + 10, 90, { font: "Work Sans", size: 12.5, weight: 500, color: P.ink });
    txt(b, "tag-n-" + c[0], c[2], x + 132, ty + 10, 30, { font: "Work Sans", size: 12, weight: 600, color: P.soft, align: "right" });
  });
}

function popover(b, x, y) {
  const W = 352, H = 236;
  box(b, "pop", x, y, W, H, { fill: P.paper, radius: 16, shadow: SHADOW_SOFT, stroke: P.line });
  box(b, "pop-bar", x, y + 14, 5, H - 28, { fill: P.cat.tiyatro, radius: 3 });
  txt(b, "pop-cat", "TİYATRO", x + 26, y + 20, 200, { font: "Work Sans", size: 10, weight: 700, color: P.cat.tiyatro, track: 1.6 });
  txt(b, "pop-title", "Godot'yu Beklerken", x + 26, y + 38, 300, { font: "Fraunces", size: 24, weight: 600, color: P.ink, line: 1.05 });
  txt(b, "pop-venue", "Kenter Tiyatrosu · Beyoğlu", x + 26, y + 76, 300, { font: "Work Sans", size: 12.5, weight: 400, color: P.soft });
  for (let i = 0; i < 21; i++) {
    box(b, "pop-rule-" + i, x + 26 + i * 15, y + 104, 8, 1.2, { fill: P.line });
  }
  txt(b, "pop-time", "20.30", x + 26, y + 116, 90, { font: "Work Sans", size: 23, weight: 600, color: P.ink, track: -0.6 });
  txt(b, "pop-day", "Cuma 7 Kasım", x + 112, y + 126, 130, { font: "Work Sans", size: 12, weight: 400, color: P.soft });
  txt(b, "pop-len", "2 perde · 2sa 15dk", x + 26, y + 150, 180, { font: "Work Sans", size: 12, weight: 400, color: P.soft });
  txt(b, "pop-price", "₺240", x + 230, y + 144, 96, { font: "Work Sans", size: 14, weight: 600, color: P.ink, align: "right" });
  box(b, "pop-cta", x + 26, y + 178, 132, 40, { fill: P.ink, radius: 10 });
  txt(b, "pop-cta-t", "Bilet al", x + 26, y + 189, 132, { font: "Work Sans", size: 13, weight: 600, color: P.paper, align: "center" });
  box(b, "pop-ghost", x + 170, y + 178, 112, 40, { fill: P.paper, radius: 10, stroke: P.line });
  txt(b, "pop-ghost-t", "Detaylar", x + 170, y + 189, 112, { font: "Work Sans", size: 13, weight: 600, color: P.ink, align: "center" });
  box(b, "pop-stamp", x + W - 40, y - 18, 56, 56, { fill: P.paper, radius: 28, stroke: P.accent, sw: 1.8 });
  txt(b, "pop-stamp-t", "07.11", x + W - 40, y + 1, 56, { font: "Work Sans", size: 12, weight: 700, color: "#9B4630", align: "center" });
}

const ROWS = [
  ["20.00", "Martı", "Moda Sahnesi", "tiyatro", "₺220", false],
  ["20.30", "Godot'yu Beklerken", "Kenter Tiyatrosu", "tiyatro", "₺240", true],
  ["21.00", "Anadolu Ateşi", "Cemal Reşit Rey", "sahne", "₺320", false],
  ["22.00", "Baba Zula", "Babylon", "konser", "₺450", false],
  ["23.00", "Gece Sefası", "Salon İKSV", "konser", "₺380", false],
];

function listRow(b, x, y, w, r) {
  box(b, "row-" + r[0], x, y, w, 88, {
    fill: P.paper, radius: 12, shadow: SHADOW_TIGHT,
    stroke: r[5] ? P.ink : "#E3D7BF", sw: r[5] ? 1.6 : 1,
  });
  txt(b, "row-time-" + r[0], r[0], x + 18, y + 15, 56, { font: "Work Sans", size: 12.5, weight: 600, color: P.ink });
  box(b, "row-dot-" + r[0], x + 84, y + 20, 7, 7, { fill: P.cat[r[3]], radius: 3.5 });
  txt(b, "row-cat-" + r[0], r[3].toUpperCase(), x + 98, y + 16, 100, { font: "Work Sans", size: 9.5, weight: 700, color: P.soft, track: 1.2 });
  txt(b, "row-title-" + r[0], r[1], x + 18, y + 37, 220, { font: "Fraunces", size: 17, weight: 600, color: P.ink });
  txt(b, "row-venue-" + r[0], r[2], x + 18, y + 62, 180, { font: "Work Sans", size: 11.5, weight: 400, color: P.soft });
  txt(b, "row-price-" + r[0], r[4], x + w - 114, y + 39, 96, { font: "Work Sans", size: 13, weight: 600, color: P.ink, align: "right" });
}

// ---------------------------------------------------------------------------
// A1 · the map screen: pins only
// ---------------------------------------------------------------------------
const a1 = board("A1-harita", 0, 0, 1440, 900, P.table);
paintMap(a1);
brandBlock(a1, 28, 28);
searchBlock(a1, 1000, 28);
rail(a1, 28, 130);
box(a1, "when-pill", 1000, 96, 412, 40, { fill: P.paper, radius: 20, shadow: SHADOW_TIGHT, stroke: P.line });
[["Bu akşam", true, 4], ["Yarın", false, 141], ["Bu hafta", false, 278]].forEach(function (w) {
  const x = 1000 + w[2];
  if (w[1]) box(a1, "when-" + w[2], x + 3, 99, 134, 34, { fill: P.ink, radius: 17 });
  txt(a1, "when-t-" + w[2], w[0], x + 3, 108, 134, {
    font: "Work Sans", size: 12, weight: 600, color: w[1] ? P.paper : P.soft, align: "center",
  });
});

[
  [260, 230, "sergi"], [610, 180, "konser"], [430, 330, "sahne"],
  [300, 470, "tiyatro"], [520, 560, "tiyatro"], [230, 650, "tiyatro"],
].forEach(function (p, i) { pin(a1, "pin-" + i, p[0], p[1], P.cat[p[2]], false); });
box(a1, "attr-chip", 28, 852, 452, 26, { fill: P.paper, opacity: 0.9, radius: 6 });
txt(a1, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 38, 858, 440, {
  font: "Work Sans", size: 10, weight: 400, color: P.soft,
});

// ---------------------------------------------------------------------------
// A2 · pin + popover only
// ---------------------------------------------------------------------------
const a2 = board("A2-detay", 1520, 0, 1440, 900, P.table);
paintMap(a2);
brandBlock(a2, 28, 28);
searchBlock(a2, 1000, 28);
[[260, 250, "sergi"], [900, 250, "konser"], [380, 720, "sahne"], [700, 560, "tiyatro"]]
  .forEach(function (p, i) { pin(a2, "pin-" + i, p[0], p[1], P.cat[p[2]], false); });
ring(a2, "pin-ring", 500, 600, 38, P.accent);
pin(a2, "pin-selected", 500, 600, P.cat.tiyatro, true);
box(a2, "pop-link", 499, 512, 2, 54, { fill: P.accent });
popover(a2, 324, 276);
box(a2, "attr-chip", 28, 852, 452, 26, { fill: P.paper, opacity: 0.9, radius: 6 });
txt(a2, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 38, 858, 440, {
  font: "Work Sans", size: 10, weight: 400, color: P.soft,
});

// ---------------------------------------------------------------------------
// A3 · the list, alone
// ---------------------------------------------------------------------------
const a3 = board("A3-liste", 3040, 0, 520, 820, P.table);
box(a3, "list-panel", 56, 40, 408, 690, { fill: P.paperAlt, radius: 20, shadow: SHADOW_SOFT, stroke: P.line });
txt(a3, "list-kicker", "CUMA 7 KASIM · BU AKŞAM", 78, 66, 260, { font: "Work Sans", size: 10, weight: 700, color: P.soft, track: 1.4 });
txt(a3, "list-title", "12 etkinlik", 78, 84, 240, { font: "Fraunces", size: 26, weight: 600, color: P.ink });
txt(a3, "list-sort", "Saate göre  ⌄", 300, 96, 142, { font: "Work Sans", size: 11, weight: 500, color: P.soft, align: "right" });
ROWS.forEach(function (r, i) { listRow(a3, 74, 132 + i * 96, 372, r); });
box(a3, "list-more", 74, 620, 372, 44, { radius: 10, stroke: P.line });
txt(a3, "list-more-t", "Tüm haftayı gör", 74, 633, 372, { font: "Work Sans", size: 12, weight: 600, color: P.ink, align: "center" });
txt(a3, "list-foot", "Haritadaki 12 pin bu listeyle eşleşir", 74, 686, 372, {
  font: "Work Sans", size: 11, weight: 400, color: P.soft, align: "center",
});

// ---------------------------------------------------------------------------
// A4 · pin and filter states
// ---------------------------------------------------------------------------
const a4 = board("A4-pinler", 600, 1000, 900, 440, P.paper);
txt(a4, "s-title", "Pin durumları", 40, 32, 400, { font: "Fraunces", size: 26, weight: 600, color: P.ink });
const states = [
  ["varsayılan", P.cat.tiyatro, false],
  ["seçili", P.cat.tiyatro, true],
  ["küme · 3", P.cat.tiyatro, true],
  ["konser", P.cat.konser, false],
  ["sergi", P.cat.sergi, false],
  ["sahne", P.cat.sahne, false],
];
states.forEach(function (s, i) {
  const x = 90 + i * 145;
  if (i === 1) ring(a4, "st-ring-" + i, x, 230, 38, P.accent);
  if (i === 2) clusterPin(a4, "st-pin-" + i, x, 230, s[1], 3);
  else pin(a4, "st-pin-" + i, x, 230, s[1], s[2]);
  txt(a4, "st-label-" + i, s[0], x - 60, 252, 120, { font: "Work Sans", size: 11, weight: 500, color: P.soft, align: "center" });
});
// hover: the pin grows a name chip
box(a4, "st-hover-chip", 29, 146, 122, 26, { fill: P.ink, radius: 8 });
txt(a4, "st-hover-t", "Martı · 20.00", 29, 153, 122, { font: "Work Sans", size: 10.5, weight: 600, color: P.paper, align: "center" });
box(a4, "st-hover-tail", 89, 172, 2, 10, { fill: P.ink });

txt(a4, "s-sub", "Kategori çipleri", 40, 316, 300, { font: "Work Sans", size: 10, weight: 700, color: P.soft, track: 1.4 });
CATS.slice(0, 2).forEach(function (c, i) {
  const x = 40 + i * 150;
  box(a4, "chip-" + i, x, 336, 132, 36, { fill: i === 0 ? P.ink : P.paper, radius: 9, stroke: i === 0 ? P.ink : P.line });
  box(a4, "chip-dot-" + i, x + 14, 351, 7, 7, { fill: i === 0 ? P.paper : P.cat[c[0]], radius: 3.5 });
  txt(a4, "chip-t-" + i, c[1], x + 30, 346, 90, { font: "Work Sans", size: 12.5, weight: 500, color: i === 0 ? P.paper : P.ink });
});
box(a4, "chip-hover", 340, 336, 132, 36, { fill: P.paper, radius: 9, stroke: P.ink, sw: 1.4, shadow: SHADOW_TIGHT });
box(a4, "chip-hover-dot", 354, 351, 7, 7, { fill: P.cat.sergi, radius: 3.5 });
txt(a4, "chip-hover-t", "Sergi", 370, 346, 90, { font: "Work Sans", size: 12.5, weight: 500, color: P.ink });

return { ok: true, boards: [a1.name, a2.name, a3.name, a4.name] };
