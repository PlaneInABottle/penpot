// B · Gece — dusk marquee, glowing bulbs, ticket stubs.
// map: gece
const P = {
  night: "#0F1D24",
  deep: "#0A141A",
  panel: "#13242C",
  panelHi: "#192E37",
  line: "#274450",
  amber: "#F2B45E",
  amberDim: "#C08A45",
  cream: "#F5ECDC",
  ink: "#16262D",
  soft: "#93A6AD",
  cat: { tiyatro: "#E07C8C", konser: "#F2B45E", sergi: "#86C0A4", sahne: "#93ADEA" },
};

const page = penpot.currentPage;
["B1-harita", "B2-detay", "B3-liste", "B4-bilet"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

function paintNight(b) {
  const m = box(b, "map", 0, 0, 1440, 900, {});
  m.fills = [{ fillOpacity: 1, fillImage: mapMedia() }];
  const mul = box(b, "map-multiply", 0, 0, 1440, 900, { fill: "#1E3C48", opacity: 1 });
  mul.blendMode = "multiply";
  box(b, "map-deep", 0, 0, 1440, 900, { fill: "#0A141A", opacity: 0.18 });
  box(b, "map-warm", 0, 0, 1440, 900, { fill: "#3A2A18", opacity: 0.16 });
}

function masthead(b, x, y) {
  txt(b, "brand", "Perde", x, y, 260, { font: "Bodoni Moda", size: 38, weight: 500, color: P.cream, track: 0.4 });
  box(b, "brand-rule", x, y + 52, 56, 1.4, { fill: P.amber });
  txt(b, "brand-sub", "İSTANBUL KÜLTÜR HARİTASI", x, y + 62, 260, { font: "Work Sans", size: 8.5, weight: 600, color: P.soft, track: 2.2 });
}

function searchBar(b, x, y) {
  box(b, "search", x, y, 412, 50, { fill: "#13242C", radius: 25, stroke: P.line });
  box(b, "search-glass", x + 24, y + 18, 13, 13, { stroke: P.soft, sw: 1.4, radius: 7 });
  box(b, "search-handle", x + 34, y + 29, 7, 1.4, { fill: P.soft });
  txt(b, "search-ph", "Mekân, etkinlik veya semt ara", x + 52, y + 17, 320, { font: "Work Sans", size: 13, weight: 400, color: P.soft });
}

const CATS = [["tiyatro", "Tiyatro", "5"], ["konser", "Konser", "3"], ["sergi", "Sergi", "2"], ["sahne", "Sahne", "2"]];

function glowPin(b, name, x, y, color, selected, n) {
  const s = selected ? 1.35 : 1;
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">' +
    '<circle cx="48" cy="48" r="' + 30 * s + '" fill="' + color + '" opacity="0.10"/>' +
    '<circle cx="48" cy="48" r="' + 20 * s + '" fill="' + color + '" opacity="0.18"/>' +
    '<circle cx="48" cy="48" r="' + 11 * s + '" fill="' + color + '" opacity="0.42"/>' +
    '<circle cx="48" cy="48" r="' + 6 * s + '" fill="' + color + '"/>' +
    "</svg>";
  const g = svgAt(b, name, svg, x - 48, y - 48);
  if (n != null) {
    txt(b, name + "-n", String(n), x - 16, y - 9, 32, {
      font: "Work Sans", size: 10, weight: 700, color: P.deep, align: "center",
    });
  }
  return g;
}

function ticket(b, x, y) {
  const W = 396, H = 224;
  box(b, "tk", x, y, W, H, { fill: P.cream, radius: 8, shadow: SHADOW_SOFT });
  box(b, "tk-stub", x + 292, y, 104, H, { fill: "#F0D9B4", radius: 8 });
  box(b, "tk-stub-fix", x + 292, y, 12, H, { fill: "#F0D9B4" });
  for (let i = 0; i < 8; i++) {
    box(b, "tk-perf-" + i, x + 291, y + 14 + i * 26, 1.4, 12, { fill: "#B08A5A" });
  }
  txt(b, "tk-cat", "TİYATRO", x + 24, y + 20, 200, { font: "Work Sans", size: 9.5, weight: 700, color: P.amberDim, track: 2 });
  txt(b, "tk-title", "Godot'yu Beklerken", x + 24, y + 38, 250, { font: "Bodoni Moda", size: 25, weight: 500, color: P.ink, line: 1.05 });
  txt(b, "tk-venue", "Kenter Tiyatrosu · Beyoğlu", x + 24, y + 78, 260, { font: "Work Sans", size: 12, weight: 400, color: "#5C6B6A" });
  txt(b, "tk-meta", "SALON 2  ·  SIRA 8  ·  KOLTUK 14", x + 24, y + 104, 260, {
    font: "Work Sans", size: 9.5, weight: 600, color: "#7A8785", track: 1.1,
  });
  for (let i = 0; i < 18; i++) box(b, "tk-rule-" + i, x + 24 + i * 14, y + 128, 7, 1, { fill: "#D9C9A8" });
  txt(b, "tk-time", "20.30", x + 24, y + 140, 90, { font: "Work Sans", size: 24, weight: 600, color: P.ink, track: -0.6 });
  txt(b, "tk-day", "Cuma 7 Kasım", x + 108, y + 150, 130, { font: "Work Sans", size: 11.5, weight: 400, color: "#5C6B6A" });
  box(b, "tk-cta", x + 24, y + 176, 132, 34, { fill: P.ink, radius: 6 });
  txt(b, "tk-cta-t", "Bilet al", x + 24, y + 185, 132, { font: "Work Sans", size: 12.5, weight: 600, color: P.cream, align: "center" });
  txt(b, "tk-more", "Detaylar  →", x + 172, y + 186, 110, { font: "Work Sans", size: 11.5, weight: 600, color: P.ink });
  txt(b, "tk-stub-t", "BİLET", x + 304, y + 22, 84, { font: "Work Sans", size: 9, weight: 700, color: P.amberDim, track: 2 });
  txt(b, "tk-price", "₺240", x + 304, y + 42, 84, { font: "Work Sans", size: 22, weight: 700, color: P.ink });
  txt(b, "tk-date", "07.11", x + 304, y + 84, 84, { font: "Work Sans", size: 13, weight: 700, color: P.ink });
  txt(b, "tk-dow", "CUMA", x + 304, y + 104, 84, { font: "Work Sans", size: 9, weight: 600, color: "#7A8785", track: 1.6 });
  txt(b, "tk-code", "P-0142", x + 304, y + 178, 84, { font: "Work Sans", size: 9, weight: 600, color: "#7A8785", track: 1.2 });
}

const ROWS = [
  ["20.00", "Martı", "Moda Sahnesi", "₺220", false],
  ["20.30", "Godot'yu Beklerken", "Kenter Tiyatrosu", "₺240", true],
  ["21.00", "Anadolu Ateşi", "Cemal Reşit Rey", "₺320", false],
  ["22.00", "Baba Zula", "Babylon", "₺450", false],
  ["23.00", "Gece Sefası", "Salon İKSV", "₺380", false],
];

function billRow(b, x, y, w, r) {
  if (r[4]) box(b, "bill-sel-" + r[0], x, y, w, 72, { fill: "#182D36" });
  if (r[4]) box(b, "bill-bar-" + r[0], x, y, 3, 72, { fill: P.amber });
  txt(b, "bill-time-" + r[0], r[0], x + 22, y + 14, 56, { font: "Work Sans", size: 12, weight: 600, color: P.amber });
  txt(b, "bill-title-" + r[0], r[1], x + 22, y + 32, 216, { font: "Bodoni Moda", size: 16, weight: 500, color: P.cream });
  txt(b, "bill-venue-" + r[0], r[2], x + 22, y + 54, 190, { font: "Work Sans", size: 10.5, weight: 400, color: P.soft });
  txt(b, "bill-price-" + r[0], r[3], x + w - 118, y + 34, 96, { font: "Work Sans", size: 12, weight: 600, color: P.cream, align: "right" });
  box(b, "bill-line-" + r[0], x, y + 72, w, 1, { fill: P.line });
}

function playbill(b, x, y) {
  const W = 392, H = 588;
  box(b, "pb", x, y, W, H, { fill: P.panel, radius: 10, stroke: P.line, shadow: SHADOW_SOFT });
  txt(b, "pb-kick", "BU AKŞAM", x + 24, y + 22, 200, { font: "Work Sans", size: 9.5, weight: 700, color: P.amber, track: 2.2 });
  txt(b, "pb-num", "12", x + 24, y + 38, 90, { font: "Bodoni Moda", size: 40, weight: 500, color: P.cream });
  txt(b, "pb-num-l", "etkinlik · Beyoğlu", x + 76, y + 56, 240, { font: "Work Sans", size: 11.5, weight: 400, color: P.soft });
  txt(b, "pb-sort", "SAATE GÖRE", x + 250, y + 26, 118, { font: "Work Sans", size: 9, weight: 600, color: P.soft, track: 1.4, align: "right" });
  box(b, "pb-head", x + 24, y + 88, W - 48, 1, { fill: P.line });
  ROWS.forEach(function (r, i) { billRow(b, x + 24, y + 96 + i * 72, W - 48, r); });
  txt(b, "pb-more", "Tüm haftayı gör  →", x + 24, y + 476, W - 48, {
    font: "Work Sans", size: 11.5, weight: 600, color: P.amber, align: "center",
  });
  txt(b, "pb-foot", "Haritadaki 12 ışık bu listeyle eşleşir", x + 24, y + 512, W - 48, {
    font: "Work Sans", size: 10, weight: 400, color: P.soft, align: "center",
  });
}

// ---- B1 map ----------------------------------------------------------------
const b1 = board("B1-harita", 0, 1600, 1440, 900, P.night);
paintNight(b1);
masthead(b1, 40, 36);
searchBar(b1, 988, 32);
["Bu akşam", "Yarın", "Bu hafta"].forEach(function (w, i) {
  const x = 988 + i * 138;
  txt(b1, "tab-" + i, w, x, 98, 134, {
    font: "Work Sans", size: 11, weight: 600, color: i === 0 ? P.amber : P.soft, track: 1.4, align: "center",
  });
  if (i === 0) box(b1, "tab-line", x + 34, 118, 66, 2, { fill: P.amber });
});
CATS.forEach(function (c, i) {
  const x = 40 + i * 150;
  box(b1, "leg-dot-" + c[0], x, 846, 7, 7, { fill: P.cat[c[0]], radius: 3.5 });
  txt(b1, "leg-t-" + c[0], c[1], x + 14, 838, 90, { font: "Work Sans", size: 11, weight: 500, color: P.cream });
  txt(b1, "leg-n-" + c[0], c[2], x + 14, 856, 90, { font: "Work Sans", size: 10, weight: 500, color: P.soft });
});
[[260, 230, "sergi"], [610, 180, "konser"], [430, 330, "sahne"],
 [300, 470, "tiyatro"], [520, 560, "tiyatro"], [230, 650, "tiyatro"]]
  .forEach(function (p, i) { glowPin(b1, "pin-" + i, p[0], p[1], P.cat[p[2]], false); });
txt(b1, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 40, 880, 520, {
  font: "Work Sans", size: 9.5, weight: 400, color: "#6C8087",
});

// ---- B2 ticket -------------------------------------------------------------
const b2 = board("B2-detay", 1520, 1600, 1440, 900, P.night);
paintNight(b2);
masthead(b2, 40, 36);
searchBar(b2, 988, 32);
[[260, 250, "sergi"], [900, 250, "konser"], [380, 720, "sahne"], [700, 560, "tiyatro"]]
  .forEach(function (p, i) { glowPin(b2, "pin-" + i, p[0], p[1], P.cat[p[2]], false); });
ring(b2, "pin-ring", 500, 600, 46, P.amber);
glowPin(b2, "pin-selected", 500, 600, P.cat.tiyatro, true);
box(b2, "tk-link", 499, 512, 1.6, 56, { fill: P.amber });
ticket(b2, 324, 276);
txt(b2, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 40, 880, 520, {
  font: "Work Sans", size: 9.5, weight: 400, color: "#6C8087",
});

// ---- B3 playbill -----------------------------------------------------------
const b3 = board("B3-liste", 3040, 1600, 520, 820, P.night);
playbill(b3, 56, 40);

// ---- B4 ticket and bulb states --------------------------------------------
const b4 = board("B4-bilet", 0, 2600, 900, 460, P.night);
txt(b4, "s-title", "Işık ve kupon", 40, 30, 400, { font: "Bodoni Moda", size: 28, weight: 500, color: P.cream });
[["varsayılan", P.cat.tiyatro, false], ["seçili", P.cat.tiyatro, true],
 ["küme · 3", P.cat.tiyatro, true], ["konser", P.cat.konser, false], ["sahne", P.cat.sahne, false]]
  .forEach(function (s, i) {
    const x = 100 + i * 155;
    if (i === 1) ring(b4, "st-ring-" + i, x, 230, 46, P.amber);
    glowPin(b4, "st-pin-" + i, x, 230, s[1], s[2], i === 2 ? 3 : null);
    txt(b4, "st-label-" + i, s[0], x - 60, 258, 120, { font: "Work Sans", size: 10.5, weight: 500, color: P.soft, align: "center" });
  });
txt(b4, "s-sub", "Kupon kırılımı", 40, 320, 300, { font: "Work Sans", size: 9.5, weight: 700, color: P.soft, track: 2 });

return { ok: true, boards: [b1.name, b2.name, b3.name, b4.name] };
