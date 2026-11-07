// Shared drawing helpers for the Perde exploration boards.
// Every screen file is concatenated after this prelude by tools/proto.py.

// Shape x/y are page-absolute in Penpot even when the shape sits inside a board,
// so every placement adds the parent board's offset.
function place(shape, parent, x, y) {
  const ox = parent && parent.type === "board" ? parent.x : 0;
  const oy = parent && parent.type === "board" ? parent.y : 0;
  shape.x = x + ox;
  shape.y = y + oy;
}

function board(name, x, y, w, h, fill) {
  const b = penpot.createBoard();
  b.name = name;
  b.x = x;
  b.y = y;
  b.resize(w, h);
  b.fills = [{ fillColor: fill }];
  b.clipContent = true;
  return b;
}

function box(parent, name, x, y, w, h, o) {
  o = o || {};
  const r = penpot.createRectangle();
  r.name = name;
  parent.appendChild(r);
  r.resize(w, h);
  place(r, parent, x, y);
  r.fills = o.fill ? [{ fillColor: o.fill, fillOpacity: o.opacity == null ? 1 : o.opacity }] : [];
  if (o.radius != null) r.borderRadius = o.radius;
  if (o.stroke) {
    r.strokes = [{ strokeColor: o.stroke, strokeWidth: o.sw == null ? 1 : o.sw, strokeAlignment: "inner" }];
  }
  if (o.shadow) r.shadows = [o.shadow];
  return r;
}

function txt(parent, name, s, x, y, w, o) {
  o = o || {};
  const t = penpot.createText(s);
  t.name = name;
  parent.appendChild(t);
  t.resize(w, o.h == null ? 24 : o.h);
  t.growType = "auto-height";
  place(t, parent, x, y);
  if (o.font) t.fontFamily = o.font;
  if (o.size) t.fontSize = String(o.size);
  if (o.weight) t.fontWeight = String(o.weight);
  if (o.color) t.fills = [{ fillColor: o.color }];
  if (o.track != null) t.letterSpacing = String(o.track);
  if (o.line != null) t.lineHeight = String(o.line);
  if (o.align) t.align = o.align;
  if (o.upper) t.textTransform = "uppercase";
  return t;
}

function svgAt(parent, name, svg, x, y) {
  const g = penpot.createShapeFromSvg(svg);
  parent.appendChild(g);
  g.name = name;
  place(g, parent, x, y);
  return g;
}

const SHADOW_SOFT = {
  style: "drop-shadow", offsetX: 0, offsetY: 10, blur: 28, spread: 0,
  color: { color: "#3B2C16", opacity: 0.16 },
};
const SHADOW_TIGHT = {
  style: "drop-shadow", offsetX: 0, offsetY: 3, blur: 10, spread: 0,
  color: { color: "#3B2C16", opacity: 0.16 },
};

// Block maps live once on the off-canvas `__assets` board (tools/mapasset.py).
function assetMedia(name) {
  const src = penpot.currentPage.findShapes({ name: name })[0];
  if (!src) throw new Error("map asset missing: run tools/mapasset.py");
  return src.fills[0].fillImage;
}
function mapMedia() { return assetMedia("__map-src"); }

// Pixel sprite: one SVG, a hard ink silhouette offset 1px, then the colour cells.
function sprite(parent, name, x, y, rows, color, scale) {
  const h = rows.length, w = rows[0].length;
  let silhouette = "", cells = "";
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) {
      if (rows[r][c] === ".") continue;
      const px = c * scale, py = r * scale;
      silhouette += '<rect x="' + (px + 1) + '" y="' + (py + 1) + '" width="' + scale + '" height="' + scale + '"/>';
      cells += '<rect x="' + px + '" y="' + py + '" width="' + scale + '" height="' + scale + '"/>';
    }
  }
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="' + w * scale + '" height="' + (h * scale + 2) +
    '" viewBox="0 0 ' + w * scale + ' ' + (h * scale + 2) + '" shape-rendering="crispEdges">' +
    '<g fill="#1E1B2E">' + silhouette + '</g>' +
    '<g fill="' + color + '">' + cells + '</g></svg>';
  return svgAt(parent, name, svg, x - (w * scale) / 2, y - h * scale);
}

// A flag pin: ground shadow, ink stem, coloured pennant.
function flag(parent, name, x, y, color, selected) {
  const s = selected ? 1.0 : 0.86;
  const h = 42 * s;
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="46" height="48" viewBox="0 0 46 48">' +
    '<ellipse cx="22" cy="43" rx="7" ry="2.6" fill="#3B2C16" opacity="0.18"/>' +
    '<rect x="21" y="14" width="2" height="28" fill="#2A2419"/>' +
    '<path d="M22 4 L22 18 L4 11 Z" fill="' + color + '"/>' +
    '<path d="M22 4 L22 18 L16 15 Z" fill="#000000" opacity="0.14"/>' +
    "</svg>";
  return svgAt(parent, name, svg, x - 22, y - 44);
}

// A lollipop pin: cream ring, solid category head, ink stem. Reads on a photo map.
function pin(parent, name, x, y, color, selected) {
  const r = selected ? 16 : 12;
  const cx = 32, cy = 22;
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="60" viewBox="0 0 64 60">' +
    '<ellipse cx="32" cy="56" rx="9" ry="3.4" fill="#3B2C16" opacity="0.24"/>' +
    '<rect x="30.8" y="' + (cy + r - 4) + '" width="2.4" height="' + (54 - cy - r + 4) + '" fill="#2A2419"/>' +
    '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + color + '" stroke="#FCF8EF" stroke-width="4"/>' +
    '<circle cx="' + (cx - r * 0.3) + '" cy="' + (cy - r * 0.3) + '" r="' + (r * 0.3) + '" fill="#FFFFFF" opacity="0.6"/>' +
    "</svg>";
  return svgAt(parent, name, svg, x - 32, y - 56);
}

function ring(parent, name, cx, cy, rx, color) {
  const e = penpot.createEllipse();
  e.name = name;
  parent.appendChild(e);
  e.resize(rx * 2, rx);
  place(e, parent, cx - rx, cy - rx / 2);
  e.fills = [];
  e.strokes = [{ strokeColor: color, strokeWidth: 1.5, strokeAlignment: "center" }];
  return e;
}

// Vertical dashed rule, drawn as segments so it survives SVG-free import.
function dash(parent, name, x, y, h, color) {
  for (let i = 0; i * 12 < h; i++) {
    box(parent, name + "-" + i, x, y + i * 12, 1.2, 6, { fill: color });
  }
}

// Cluster pin: a count inside the head.
function clusterPin(parent, name, x, y, color, n) {
  pin(parent, name, x, y, color, true);
  txt(parent, name + "-count", String(n), x - 16, y - 44, 32, {
    font: "Work Sans", size: 12, weight: 700, color: "#FCF8EF", align: "center",
  });
}

// Multi-colour pixel sprite from a char grid: `rows` + `pal` (char -> #hex).
function spriteMap(parent, name, x, y, sp, scale) {
  const rows = sp.rows, pal = sp.pal;
  const h = rows.length, w = rows[0].length;
  let cells = "";
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) {
      const ch = rows[r][c];
      if (ch === "." || !pal[ch]) continue;
      cells += '<rect x="' + (c * scale) + '" y="' + (r * scale) + '" width="' + scale +
        '" height="' + scale + '" fill="' + pal[ch] + '"/>';
    }
  }
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + (w * scale) + '" height="' +
    (h * scale) + '" viewBox="0 0 ' + (w * scale) + ' ' + (h * scale) +
    '" shape-rendering="crispEdges">' + cells + "</svg>";
  return svgAt(parent, name, svg, x - (w * scale) / 2, y - h * scale);
}

// A category-coloured plinth the sprite stands on.
function plinth(parent, name, x, y, color, w) {
  const h = w * 0.34;
  const e = penpot.createEllipse();
  e.name = name;
  parent.appendChild(e);
  e.resize(w, h);
  place(e, parent, x - w / 2, y - h / 2);
  e.fills = [{ fillColor: color }];
  e.strokes = [{ strokeColor: "#FCF8EF", strokeWidth: 2, strokeAlignment: "center" }];
  return e;
}

// A board inside a board: clips its children, so an image can be cropped instead of
// stretched to the frame.
function nestedBoard(parent, name, x, y, w, h, fill) {
  const b = penpot.createBoard();
  b.name = name;
  parent.appendChild(b);
  b.resize(w, h);
  place(b, parent, x, y);
  b.fills = [{ fillColor: fill }];
  b.clipContent = true;
  return b;
}

// Magnifier: a real circle plus a rotated handle. A stroked rectangle is a box, not a lens.
function searchIcon(parent, name, cx, cy, r, color, sw) {
  const e = penpot.createEllipse();
  e.name = name;
  parent.appendChild(e);
  e.resize(r * 2, r * 2);
  place(e, parent, cx - r, cy - r);
  e.fills = [];
  e.strokes = [{ strokeColor: color, strokeWidth: sw, strokeAlignment: "center" }];
  const h = box(parent, name + "-handle", cx + r * 0.66, cy + r * 0.66, r * 1.0, sw, { fill: color });
  h.rotation = 45;
  return e;
}

// A keycap label is centred by giving the text the full chip width, never a guessed x.
function keycap(parent, name, x, y, w, h, label, fill, ink, border) {
  box(parent, name, x, y, w, h, { fill: fill, radius: 7, stroke: border });
  txt(parent, name + "-t", label, x, y + (h - 15) / 2, w, {
    font: "Work Sans", size: 12, weight: 600, color: ink, align: "center",
  });
}
