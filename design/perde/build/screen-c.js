// C · Rizo — two-ink zine, numbered annotations, contents page.
// map: rizo
const P = {
  paper: "#F1EBDD",
  paperAlt: "#E8DFC9",
  ink: "#2B3A55",
  red: "#C0533A",
  soft: "#6B6A62",
  cat: { tiyatro: "#C0533A", konser: "#B4692F", sergi: "#3F6B55", sahne: "#2B3A55" },
};

const page = penpot.currentPage;
["C1-harita", "C2-detay", "C3-icindekiler", "C4-parcalar"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

function paintRiso(b) {
  const m = box(b, "map", 0, 0, 1440, 900, {});
  m.fills = [{ fillOpacity: 1, fillImage: mapMedia() }];
  const c = box(b, "map-ink1", 0, 0, 1440, 900, { fill: "#C0533A", opacity: 0.62 });
  c.blendMode = "color";
  const d = box(b, "map-ink2", 0, 0, 1440, 900, { fill: "#2B3A55", opacity: 0.16 });
  d.blendMode = "multiply";
  box(b, "map-paper", 0, 0, 1440, 900, { fill: "#F1EBDD", opacity: 0.10 });
}

function masthead(b, x, y) {
  txt(b, "brand", "Perde", x, y, 420, { font: "Fraunces", size: 54, weight: 600, color: P.ink, track: -1 });
  box(b, "brand-rule", x, y + 66, 420, 2, { fill: P.ink });
  txt(b, "brand-sub", "SAYI 07  ·  7 KASIM CUMA  ·  İSTANBUL KÜLTÜR HARİTASI", x, y + 78, 460, {
    font: "Work Sans", size: 8.5, weight: 600, color: P.soft, track: 1.6,
  });
}

function searchBox(b, x, y) {
  box(b, "search", x, y, 372, 46, { fill: P.paper, radius: 0, stroke: P.ink, sw: 1.6 });
  box(b, "search-glass", x + 20, y + 16, 12, 12, { stroke: P.ink, sw: 1.4, radius: 6 });
  txt(b, "search-ph", "Mekân, etkinlik veya semt ara", x + 44, y + 15, 300, {
    font: "Work Sans", size: 12.5, weight: 400, color: P.soft,
  });
}

const CATS = [["tiyatro", "Tiyatro", "5"], ["konser", "Konser", "3"], ["sergi", "Sergi", "2"], ["sahne", "Sahne", "2"]];

function numbered(b, name, x, y, n, color, selected) {
  const e = penpot.createEllipse();
  e.name = name;
  b.appendChild(e);
  e.resize(30, 30);
  place(e, b, x - 15, y - 15);
  e.fills = [{ fillColor: selected ? color : "#F1EBDD" }];
  e.strokes = [{ strokeColor: "#2B3A55", strokeWidth: 1.8, strokeAlignment: "center" }];
  txt(b, name + "-n", String(n), x - 15, y - 9, 30, {
    font: "Work Sans", size: 11, weight: 700, color: selected ? "#F1EBDD" : "#2B3A55", align: "center",
  });
  return e;
}

function note(b, x, y) {
  const W = 366, H = 226;
  box(b, "note", x, y, W, H, { fill: P.paper, radius: 2, shadow: SHADOW_SOFT, stroke: P.ink, sw: 1.6 });
  const tape = box(b, "tape", x + 22, y - 11, 92, 24, { fill: P.red, opacity: 0.65 });
  tape.rotation = -4;
  txt(b, "note-tag", "NOT · 07", x + 24, y + 24, 140, { font: "Work Sans", size: 9, weight: 700, color: P.red, track: 1.8 });
  txt(b, "note-title", "Godot'yu Beklerken", x + 24, y + 42, 300, { font: "Fraunces", size: 25, weight: 600, color: P.ink, line: 1.05 });
  box(b, "note-rule", x + 24, y + 82, 318, 1, { fill: P.ink, opacity: 0.4 });
  txt(b, "note-venue", "Kenter Tiyatrosu · Beyoğlu", x + 24, y + 92, 300, { font: "Work Sans", size: 12, weight: 400, color: P.soft });
  txt(b, "note-time", "20.30", x + 24, y + 116, 100, { font: "Fraunces", size: 30, weight: 600, color: P.ink });
  txt(b, "note-day", "Cuma 7 Kasım", x + 110, y + 128, 140, { font: "Work Sans", size: 11.5, weight: 400, color: P.soft });
  txt(b, "note-len", "2 perde · 2sa 15dk", x + 24, y + 156, 180, { font: "Work Sans", size: 11.5, weight: 400, color: P.soft });
  txt(b, "note-price", "₺240", x + 250, y + 150, 96, { font: "Work Sans", size: 18, weight: 700, color: P.red, align: "right" });
  txt(b, "note-cta", "BİLET AL  →", x + 24, y + 188, 160, { font: "Work Sans", size: 12, weight: 700, color: P.ink, track: 1 });
  box(b, "note-cta-rule", x + 24, y + 206, 88, 2, { fill: P.red });
}

const ROWS = [
  ["01", "20.00", "Martı", "Moda Sahnesi", "04"],
  ["02", "20.30", "Godot'yu Beklerken", "Kenter Tiyatrosu", "06"],
  ["03", "21.00", "Anadolu Ateşi", "Cemal Reşit Rey", "08"],
  ["04", "22.00", "Baba Zula", "Babylon", "11"],
  ["05", "23.00", "Gece Sefası", "Salon İKSV", "13"],
];

function contents(b, x, y) {
  const W = 404, H = 640;
  box(b, "idx", x, y, W, H, { fill: P.paper, radius: 2, stroke: P.ink, sw: 1.6, shadow: SHADOW_SOFT });
  txt(b, "idx-t", "İÇİNDEKİLER", x + 24, y + 26, 260, { font: "Work Sans", size: 9.5, weight: 700, color: P.ink, track: 2.2 });
  txt(b, "idx-n", "12", x + 24, y + 42, 90, { font: "Fraunces", size: 40, weight: 600, color: P.red });
  txt(b, "idx-n-l", "etkinlik · bu akşam", x + 78, y + 62, 220, { font: "Work Sans", size: 11, weight: 400, color: P.soft });
  box(b, "idx-rule", x + 24, y + 96, W - 48, 2, { fill: P.ink });
  ROWS.forEach(function (r, i) {
    const ry = y + 112 + i * 78;
    txt(b, "idx-i-" + i, r[0], x + 24, ry + 6, 32, { font: "Work Sans", size: 10, weight: 700, color: P.red });
    txt(b, "idx-ti-" + i, r[2], x + 52, ry + 2, 210, { font: "Fraunces", size: 16, weight: 600, color: P.ink });
    txt(b, "idx-ve-" + i, r[1] + " · " + r[3], x + 52, ry + 26, 220, { font: "Work Sans", size: 10, weight: 400, color: P.soft });
    for (let k = 0; k < 9; k++) box(b, "idx-d-" + i + "-" + k, x + 244 + k * 8, ry + 12, 2, 2, { fill: P.soft });
    txt(b, "idx-p-" + i, r[4], x + 330, ry + 4, 50, { font: "Work Sans", size: 11, weight: 700, color: P.ink, align: "right" });
    if (i === 1) box(b, "idx-hi-" + i, x + 24, ry + 52, 356, 2, { fill: P.red });
    box(b, "idx-line-" + i, x + 24, ry + 66, W - 48, 1, { fill: P.ink, opacity: 0.18 });
  });
  txt(b, "idx-more", "TÜM HAFTA  →", x + 24, y + 540, W - 48, { font: "Work Sans", size: 10, weight: 700, color: P.red, track: 1.6, align: "center" });
  txt(b, "idx-foot", "pin 01–12 bu sayfalarla eşleşir", x + 24, y + 570, W - 48, { font: "Work Sans", size: 10, weight: 400, color: P.soft, align: "center" });
}

// ---- C1 map ---------------------------------------------------------------
const c1 = board("C1-harita", 0, 3200, 1440, 900, P.paper);
paintRiso(c1);
box(c1, "head-band", 0, 0, 600, 196, { fill: P.paper });
box(c1, "head-rule", 0, 196, 600, 2, { fill: P.ink });
masthead(c1, 40, 24);
searchBox(c1, 1030, 34);
CATS.forEach(function (c, i) {
  const x = 40 + i * 142;
  txt(c1, "cat-" + c[0], c[1].toUpperCase(), x, 164, 110, {
    font: "Work Sans", size: 10, weight: 700, color: i === 0 ? P.red : P.ink, track: 1.4,
  });
  txt(c1, "cat-n-" + c[0], c[2], x + 74, 164, 24, { font: "Work Sans", size: 10, weight: 700, color: P.soft });
  if (i === 0) box(c1, "cat-line", x, 180, 100, 2, { fill: P.red });
});
[[260, 230, "sergi", 1], [610, 180, "konser", 2], [430, 330, "sahne", 3],
 [300, 470, "tiyatro", 4], [520, 560, "tiyatro", 5], [230, 650, "tiyatro", 6]]
  .forEach(function (p) { numbered(c1, "pin-" + p[3], p[0], p[1], p[3], P.cat[p[2]], false); });
txt(c1, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 40, 872, 520, {
  font: "Work Sans", size: 9.5, weight: 400, color: P.soft,
});

// ---- C2 note --------------------------------------------------------------
const c2 = board("C2-detay", 1520, 3200, 1440, 900, P.paper);
paintRiso(c2);
box(c2, "head-band", 0, 0, 600, 152, { fill: P.paper });
box(c2, "head-rule", 0, 152, 600, 2, { fill: P.ink });
masthead(c2, 40, 24);
searchBox(c2, 1030, 34);
[[260, 250, "sergi", 1], [900, 250, "konser", 2], [380, 720, "sahne", 3], [700, 560, "tiyatro", 4]]
  .forEach(function (p) { numbered(c2, "pin-" + p[3], p[0], p[1], p[3], P.cat[p[2]], false); });
box(c2, "note-link", 499, 520, 2, 56, { fill: P.red });
numbered(c2, "pin-sel", 500, 600, 5, P.red, true);
note(c2, 324, 282);
txt(c2, "attr", "Yer tutucu harita: isometricistanbul.com · örnek etkinlik verisi", 40, 872, 520, {
  font: "Work Sans", size: 9.5, weight: 400, color: P.soft,
});

// ---- C3 contents ----------------------------------------------------------
const c3 = board("C3-icindekiler", 3040, 3200, 520, 760, P.paperAlt);
contents(c3, 58, 40);

// ---- C4 parts -------------------------------------------------------------
const c4 = board("C4-parcalar", 0, 4200, 900, 420, P.paper);
txt(c4, "s-title", "Numaralı işaretler", 40, 28, 400, { font: "Fraunces", size: 26, weight: 600, color: P.ink });
[["01", false], ["02", true], ["03", false], ["04", false]].forEach(function (s, i) {
  const x = 90 + i * 120;
  numbered(c4, "st-" + i, x, 130, s[0], P.red, s[1]);
  txt(c4, "st-l-" + i, i === 1 ? "seçili" : "varsayılan", x - 56, 152, 112, {
    font: "Work Sans", size: 10, weight: 500, color: P.soft, align: "center",
  });
});
txt(c4, "s-sub", "Kategori alt çizgisi", 40, 220, 300, { font: "Work Sans", size: 9.5, weight: 700, color: P.soft, track: 1.6 });
[["TİYATRO", true], ["KONSER", false], ["SERGİ", false]].forEach(function (c, i) {
  const x = 40 + i * 132;
  txt(c4, "c-" + i, c[0], x, 244, 120, { font: "Work Sans", size: 10, weight: 700, color: c[1] ? P.red : P.ink, track: 1.4 });
  if (c[1]) box(c4, "c-line-" + i, x, 260, 108, 2, { fill: P.red });
});

return { ok: true, boards: [c1.name, c2.name, c3.name, c4.name] };
