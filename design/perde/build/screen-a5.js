// A5 · figur pins in pixel — the token sheet for A1.
__SPRITES__
const CAT = { tiyatro: "#8E3B46", konser: "#B5762F", sergi: "#4C7A63", sahne: "#4A5C8C" };
const P = { paper: "#FCF8EF", paperAlt: "#F3EBDA", ink: "#2A2419", soft: "#6E6450", line: "#CFBE9C" };

const page = penpot.currentPage;
["A5-figur"].forEach(function (n) {
  for (const c of page.findShapes({ name: n })) c.remove();
});

function figToken(b, name, x, y, kind, color, scale) {
  const w = SPRITES[kind].rows[0].length * scale;
  plinth(b, name + "-base", x, y - 2, color, w * 0.60);
  spriteMap(b, name, x, y, SPRITES[kind], scale);
}

const b = board("A5-figur", 1000, 1000, 1200, 880, P.paper);

txt(b, "t", "Pin yerine figür", 40, 30, 600, { font: "Fraunces", size: 30, weight: 600, color: P.ink, track: -0.4 });
txt(b, "s", "Pixel sprite, kategori rengi tabanda. A1'deki mevcut pinler yerinde duruyor.", 40, 70, 900, {
  font: "Work Sans", size: 12, weight: 400, color: P.soft,
});

const KINDS = [
  ["penguen", "penguen", "tiyatro"],
  ["marti", "martı", "sergi"],
  ["kedi", "kedi", "tiyatro"],
  ["vapur", "vapur", "sahne"],
  ["simit", "simit", "konser"],
  ["lale", "lale", "sergi"],
  ["fincan", "fincan", "konser"],
  ["maske", "maske", "tiyatro"],
  ["plak", "plak", "konser"],
  ["nazar", "nazar", "sahne"],
];

KINDS.forEach(function (k, i) {
  const col = i % 5, row = Math.floor(i / 5);
  const x = 130 + col * 232;
  const y = 250 + row * 170;
  figToken(b, "tok-" + k[0], x, y, k[0], CAT[k[2]], 6);
  txt(b, "tok-l-" + k[0], k[1], x - 70, y + 8, 140, {
    font: "Work Sans", size: 11, weight: 500, color: P.soft, align: "center",
  });
});

// real size strip
box(b, "strip", 40, 522, 1120, 94, { fill: P.paperAlt, radius: 12, stroke: P.line });
txt(b, "strip-k", "GERÇEK BOYUT · 48 PX", 60, 536, 400, { font: "Work Sans", size: 9, weight: 700, color: P.soft, track: 1.4 });
KINDS.forEach(function (k, i) {
  figToken(b, "sm-" + k[0], 90 + i * 106, 602, k[0], CAT[k[2]], 3);
});

// on the map — a nested board crops the image at its real aspect, never stretches it
const band = nestedBoard(b, "map-band", 0, 630, 1200, 250, "#EFE5D3");
const bandMap = box(band, "map", -120, -200, 1440, 900, {});
bandMap.fills = [{ fillOpacity: 1, fillImage: mapMedia() }];
box(band, "map-fade", 0, 0, 1200, 250, { fill: "#F2E8D4", opacity: 0.14 });
txt(band, "band-k", "HARİTADA", 40, 16, 300, { font: "Work Sans", size: 9, weight: 700, color: P.ink, track: 1.4 });
[[300, 180, "penguen", "tiyatro"], [560, 150, "marti", "sergi"], [800, 208, "fincan", "konser"], [1020, 156, "maske", "tiyatro"]]
  .forEach(function (m, i) {
    figToken(band, "band-tok-" + i, m[0], m[1], m[2], CAT[m[3]], 3);
  });

return { ok: true, boards: [b.name] };
