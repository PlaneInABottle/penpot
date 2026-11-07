// D · Konsol — daylight instrument: app bar, rail, time scrubber, dense table.
const P = {
  bg: "#F2F4F2",
  white: "#FFFFFF",
  ink: "#14181A",
  soft: "#68726E",
  line: "#DCE1DD",
  signal: "#1F6B4A",
  signalSoft: "#DCEBE3",
  cat: { tiyatro: "#8E3B46", konser: "#B5762F", sergi: "#4C7A63", sahne: "#4A5C8C" },
};

const page = penpot.currentPage;
["D1-harita", "D2-detay", "D3-liste", "D4-parcalar"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

function paintDay(b) {
  const m = box(b, "map", 0, 0, 1440, 900, {});
  m.fills = [{ fillOpacity: 1, fillImage: mapMedia() }];
  const d = box(b, "map-flat", 0, 0, 1440, 900, { fill: "#E8EDEA", opacity: 0.55 });
  d.blendMode = "saturation";
  box(b, "map-light", 0, 0, 1440, 900, { fill: "#FFFFFF", opacity: 0.28 });
}

function appBar(b) {
  box(b, "bar", 0, 0, 1440, 64, { fill: P.white });
  box(b, "bar-line", 0, 63, 1440, 1, { fill: P.line });
  txt(b, "bar-brand", "perde", 24, 20, 120, { font: "Sora", size: 19, weight: 600, color: P.ink, track: -0.4 });
  box(b, "bar-dot", 106, 30, 6, 6, { fill: P.signal, radius: 3 });
  txt(b, "bar-city", "İstanbul", 120, 25, 90, { font: "Work Sans", size: 11, weight: 500, color: P.soft });
  box(b, "bar-search", 520, 15, 400, 34, { fill: P.bg, radius: 8, stroke: P.line });
  txt(b, "bar-search-ph", "Etkinlik, mekân veya semt ara", 536, 24, 360, {
    font: "Work Sans", size: 12, weight: 400, color: P.soft,
  });
  txt(b, "bar-date", "Cuma 7 Kasım", 1240, 24, 176, {
    font: "Work Sans", size: 11.5, weight: 500, color: P.soft, align: "right",
  });
}

const CATS = [["tiyatro", "Tiyatro", "5"], ["konser", "Konser", "3"], ["sergi", "Sergi", "2"], ["sahne", "Sahne", "2"]];

function rail(b) {
  box(b, "rail", 0, 64, 216, 836, { fill: P.white });
  box(b, "rail-line", 215, 64, 1, 836, { fill: P.line });
  txt(b, "rail-k", "KATMAN", 20, 88, 160, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.6 });
  CATS.forEach(function (c, i) {
    const y = 112 + i * 38;
    box(b, "cb-" + c[0], 20, y, 16, 16, { fill: P.signalSoft, radius: 3, stroke: P.signal, sw: 1.4 });
    box(b, "cb-tick-" + c[0], 23, y + 5, 10, 2, { fill: P.signal });
    box(b, "cb-tick2-" + c[0], 27, y + 1, 2, 10, { fill: P.signal });
    txt(b, "cb-l-" + c[0], c[1], 46, y + 1, 100, { font: "Work Sans", size: 12, weight: 500, color: P.ink });
    txt(b, "cb-n-" + c[0], c[2], 168, y + 1, 28, { font: "Work Sans", size: 11, weight: 500, color: P.soft, align: "right" });
  });
  box(b, "rail-div", 20, 280, 176, 1, { fill: P.line });
  txt(b, "rail-k2", "SAAT", 20, 300, 160, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.6 });
  txt(b, "rail-time", "18.00 — 24.00", 20, 318, 180, { font: "Work Sans", size: 13, weight: 600, color: P.ink });
  txt(b, "rail-count", "12 etkinlik", 20, 344, 180, { font: "Work Sans", size: 11, weight: 400, color: P.soft });
  box(b, "rail-div2", 20, 380, 176, 1, { fill: P.line });
  txt(b, "rail-k3", "YAKINLIK", 20, 400, 160, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.6 });
  txt(b, "rail-near", "Beyoğlu · 2 km", 20, 418, 180, { font: "Work Sans", size: 12, weight: 500, color: P.ink });
}

function chipPin(b, name, x, y, n, selected) {
  box(b, name + "-line", x - 0.75, y - 26, 1.5, 26, { fill: P.soft });
  box(b, name + "-c", x - 16, y - 54, 32, 28, {
    fill: selected ? P.signal : P.white, radius: 6,
    stroke: selected ? P.signal : "#C9D0CB", sw: 1.5, shadow: SHADOW_TIGHT,
  });
  txt(b, name + "-t", String(n), x - 16, y - 46, 32, {
    font: "Work Sans", size: 12, weight: 700, color: selected ? P.white : P.ink, align: "center",
  });
}

function scrubber(b, x, y) {
  const W = 1160;
  box(b, "sc", x, y, W, 76, { fill: P.white, opacity: 0.96, radius: 10, stroke: P.line, shadow: SHADOW_TIGHT });
  txt(b, "sc-k", "SAAT", x + 20, y + 16, 80, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.4 });
  const x0 = x + 24, x1 = x + W - 24;
  box(b, "sc-track", x0, y + 48, x1 - x0, 2, { fill: P.line });
  box(b, "sc-win", x0 + (x1 - x0) * 0.5, y + 46, (x1 - x0) * 0.25, 6, { fill: P.signal });
  for (let i = 0; i <= 12; i++) {
    const hx = x0 + (x1 - x0) * (i / 12);
    box(b, "sc-tick-" + i, hx, y + 44, 1, 10, { fill: P.soft });
    txt(b, "sc-h-" + i, String(12 + i), hx - 12, y + 56, 24, {
      font: "Work Sans", size: 8.5, weight: 500, color: P.soft, align: "center",
    });
  }
  [0.18, 0.26, 0.31, 0.44, 0.52, 0.61, 0.72, 0.86].forEach(function (f, i) {
    box(b, "sc-ev-" + i, x0 + (x1 - x0) * f, y + 34, 3, 10, { fill: P.cat.tiyatro, opacity: 0.5, radius: 1 });
  });
}

function detailCard(b, x, y) {
  const W = 328, H = 206;
  box(b, "dc", x, y, W, H, { fill: P.white, radius: 10, shadow: SHADOW_SOFT, stroke: P.line });
  box(b, "dc-bar", x + 1, y + 1, W - 2, 4, { fill: P.signal, radius: 2 });
  txt(b, "dc-cat", "TİYATRO", x + 22, y + 18, 140, { font: "Work Sans", size: 9, weight: 700, color: P.cat.tiyatro, track: 1.6 });
  txt(b, "dc-time", "20.30", x + 240, y + 16, 66, { font: "Work Sans", size: 10.5, weight: 600, color: P.soft, align: "right" });
  txt(b, "dc-title", "Godot'yu Beklerken", x + 22, y + 34, 280, { font: "Sora", size: 18, weight: 600, color: P.ink });
  txt(b, "dc-venue", "Kenter Tiyatrosu · Beyoğlu", x + 22, y + 62, 280, { font: "Work Sans", size: 11.5, weight: 400, color: P.soft });
  box(b, "dc-track", x + 22, y + 96, 284, 5, { fill: P.line, radius: 2 });
  box(b, "dc-fill", x + 22 + 284 * 0.35, y + 96, 284 * 0.22, 5, { fill: P.signal, radius: 2 });
  txt(b, "dc-t1", "20.30", x + 22, y + 106, 60, { font: "Work Sans", size: 9, weight: 500, color: P.soft });
  txt(b, "dc-t2", "22.45", x + 246, y + 106, 60, { font: "Work Sans", size: 9, weight: 500, color: P.soft, align: "right" });
  txt(b, "dc-meta", "2sa 15dk · 2 perde", x + 22, y + 130, 180, { font: "Work Sans", size: 11, weight: 400, color: P.soft });
  txt(b, "dc-price", "₺240", x + 246, y + 126, 60, { font: "Work Sans", size: 13, weight: 700, color: P.ink, align: "right" });
  box(b, "dc-cta", x + 22, y + 156, 120, 34, { fill: P.signal, radius: 7 });
  txt(b, "dc-cta-t", "Bilet al", x + 22, y + 165, 120, { font: "Work Sans", size: 12, weight: 600, color: P.white, align: "center" });
  txt(b, "dc-alt", "Takvime ekle", x + 158, y + 165, 120, { font: "Work Sans", size: 11.5, weight: 600, color: P.signal });
}

const ROWS = [
  ["20.00", "Martı", "Moda Sahnesi", P.cat.tiyatro, "₺220"],
  ["20.30", "Godot'yu Beklerken", "Kenter Tiyatrosu", P.cat.tiyatro, "₺240"],
  ["21.00", "Anadolu Ateşi", "Cemal Reşit Rey", P.cat.sahne, "₺320"],
  ["22.00", "Baba Zula", "Babylon", P.cat.konser, "₺450"],
  ["23.00", "Gece Sefası", "Salon İKSV", P.cat.konser, "₺380"],
  ["18.30", "Kentin Sessizliği", "Pera Müzesi", P.cat.sergi, "₺120"],
];

function tableRow(b, x, y, w, r, selected) {
  if (selected) box(b, "tr-bg-" + r[0], x, y, w, 48, { fill: P.signalSoft });
  if (selected) box(b, "tr-bar-" + r[0], x, y, 3, 48, { fill: P.signal });
  txt(b, "tr-t-" + r[0], r[0], x + 16, y + 15, 52, { font: "Work Sans", size: 12, weight: 600, color: P.ink });
  txt(b, "tr-n-" + r[0], r[1], x + 74, y + 13, 220, { font: "Work Sans", size: 12.5, weight: 600, color: P.ink });
  txt(b, "tr-v-" + r[0], r[2], x + 74, y + 29, 220, { font: "Work Sans", size: 10, weight: 400, color: P.soft });
  box(b, "tr-dot-" + r[0], x + 58, y + 21, 7, 7, { fill: r[3], radius: 3.5 });
  txt(b, "tr-p-" + r[0], r[4], x + w - 92, y + 15, 76, { font: "Work Sans", size: 11.5, weight: 600, color: P.ink, align: "right" });
  box(b, "tr-line-" + r[0], x, y + 48, w, 1, { fill: P.line });
}

// ---- D1 map ---------------------------------------------------------------
const d1 = board("D1-harita", 0, 4800, 1440, 900, P.bg);
paintDay(d1);
appBar(d1);
rail(d1);
[[430, 300, 1], [760, 240, 2], [980, 400, 3], [560, 470, 4], [1180, 320, 6]]
  .forEach(function (p, i) { chipPin(d1, "pin-" + i, p[0], p[1], p[2], false); });
scrubber(d1, 240, 804);

// ---- D2 detail -------------------------------------------------------------
const d2 = board("D2-detay", 1520, 4800, 1440, 900, P.bg);
paintDay(d2);
appBar(d2);
rail(d2);
[[430, 300, 1], [980, 280, 2], [1180, 470, 3], [420, 620, 4]]
  .forEach(function (p, i) { chipPin(d2, "pin-" + i, p[0], p[1], p[2], false); });
chipPin(d2, "pin-sel", 620, 600, 5, true);
box(d2, "dc-link", 619, 546, 1.5, 30, { fill: P.signal });
detailCard(d2, 340, 320);
scrubber(d2, 240, 804);

// ---- D3 table --------------------------------------------------------------
const d3 = board("D3-liste", 3040, 4800, 520, 820, P.bg);
box(d3, "sheet", 40, 40, 440, 520, { fill: P.white, radius: 12, stroke: P.line, shadow: SHADOW_SOFT });
txt(d3, "sh-k", "BU AKŞAM · 12", 64, 64, 240, { font: "Work Sans", size: 9.5, weight: 700, color: P.soft, track: 1.4 });
txt(d3, "sh-t", "Akış", 64, 82, 200, { font: "Sora", size: 20, weight: 600, color: P.ink });
txt(d3, "sh-h1", "SAAT", 64, 120, 52, { font: "Work Sans", size: 8.5, weight: 700, color: P.soft, track: 1 });
txt(d3, "sh-h2", "ETKİNLİK", 138, 120, 160, { font: "Work Sans", size: 8.5, weight: 700, color: P.soft, track: 1 });
txt(d3, "sh-h3", "FİYAT", 366, 120, 76, { font: "Work Sans", size: 8.5, weight: 700, color: P.soft, track: 1, align: "right" });
box(d3, "sh-rule", 64, 138, 392, 1, { fill: P.line });
ROWS.forEach(function (r, i) { tableRow(d3, 52, 146 + i * 48, 376, r, i === 1); });
txt(d3, "sh-foot", "Haritadaki 12 işaret bu akışla eşleşir", 64, 470, 392, {
  font: "Work Sans", size: 10, weight: 400, color: P.soft, align: "center",
});

// ---- D4 parts --------------------------------------------------------------
const d4 = board("D4-parcalar", 0, 5700, 900, 460, P.white);
txt(d4, "s-title", "İşaret ve kontrol", 40, 28, 400, { font: "Sora", size: 20, weight: 600, color: P.ink });
[["1", false], ["2", true], ["3", false], ["4", false]].forEach(function (s, i) {
  const x = 90 + i * 120;
  chipPin(d4, "st-" + i, x, 140, s[0], s[1]);
  txt(d4, "st-l-" + i, i === 1 ? "seçili" : "varsayılan", x - 56, 152, 112, {
    font: "Work Sans", size: 10, weight: 500, color: P.soft, align: "center",
  });
});
txt(d4, "s-sub", "Zaman şeridi", 40, 220, 300, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.4 });
scrubber(d4, 40, 240);

return { ok: true, boards: [d1.name, d2.name, d3.name, d4.name] };
