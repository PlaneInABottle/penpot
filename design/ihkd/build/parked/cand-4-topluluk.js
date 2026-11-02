/**
 * Parked hero — "Topluluk haritası" (hero candidate 4), kept on request.
 *
 * This page is the society's map with its people around it: 41 province dots on
 * the Turkey outline, 12 working-group cards as the key, three real photographs
 * of the community (poster session, audience, hall) and the congress as one line.
 *
 * When to use it: the opening of the Dernek / Üyelik pages, or when the story is
 * the "tek çatı" (one roof) argument rather than the next congress. Not while the
 * congress poster (cand-1) is the live hero.
 *
 * Run: python3 scripts/penpot_exec.py --file design/ihkd/build/parked/cand-4-topluluk.js
 * Idempotent: reuses the `cand-4-topluluk` board on `_scratch`, clears its
 * children and rebuilds them. A first run may only switch the page (Penpot
 * switches asynchronously); run it once more.
 *
 * Photos: Pexels 12319354 (poster session, Roxanne Minnish), 15325468 (audience,
 * Luis Quintero), 35138560 (convention hall, Tahir Xələfquliyev). The map outline
 * is Natural Earth 110m admin-0 (public domain); the dots are a field inside the
 * outline, not exact province positions.
 * Slots are built empty; place the photographs with
 *   python3 design/ihkd/tools/media.py --restore --board cand-4-topluluk --page _scratch
 * Render: shots/hero-candidates-4/cand-4-topluluk.png
 */


const PAGE = "_scratch";
const BOARD = "cand-4-topluluk";
const W = 1440, H = 900;
const SET = "ihkd";
const DATA = [
  { k: "rect", name: "top bar", x: 0, y: 0, w: 1440, h: 4, fill: "#C4122F", tok: "red.600" },
  { k: "text", t: "İHKD", font: ["JetBrains Mono", "600", "22"], lh: "1", ls: "0.6", align: "left", grow: "auto-width", name: "masthead mark", x: 120, y: 36, w: 56, h: 22, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "ÜYE PLATFORMU", font: ["JetBrains Mono", "500", "13"], lh: "1.2", ls: "1.1", align: "left", grow: "auto-width", name: "masthead sub", x: 224, y: 40, w: 116, h: 16, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Dernek", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Dernek", x: 500, y: 32, w: 51, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Çalışma grupları", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Çalışma grupları", x: 576, y: 32, w: 113, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Kongre", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Kongre", x: 732, y: 32, w: 51, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Akademi", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Akademi", x: 808, y: 32, w: 62, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Yayın", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Yayın", x: 892, y: 32, w: 38, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Haberler", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "nav Haberler", x: 956, y: 32, w: 61, h: 23, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Üye girişi", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "masthead login", x: 1084, y: 32, w: 64, h: 23, fill: "#333D45", tok: "ink.700" },
  { k: "board", name: "masthead cta", x: 1184, y: 24, w: 136, h: 40, stroke: "#C4122F", sw: 1, stok: "red.600", radius: 2,
    children: [
    { k: "text", t: "Üye ol", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "center", grow: "auto-height", name: "masthead cta / label", x: 1184, y: 32, w: 136, h: 23, fill: "#0E1318", tok: "ink.900" },
    ] },
  { k: "rect", name: "masthead rule", x: 0, y: 84, w: 1440, h: 1, fill: "#DDE1E4", tok: "line.soft" },
  { k: "text", t: "1998'DEN BERİ · ANKARA", font: ["JetBrains Mono", "500", "13"], lh: "1.2", ls: "1.1", align: "left", grow: "auto-width", name: "c4 label", x: 120, y: 124, w: 196, h: 16, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Hastanın hekimi.", font: ["Inter Tight", "700", "80"], lh: "0.98", ls: "-2.6", align: "left", grow: "auto-height", name: "c4 title", x: 120, y: 152, w: 620, h: 79, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "On iki çalışma grubu, kırk bir il temsilciliği ve tek bir kayıt: iç hastalıkları hekimliğinin çatısı.", font: ["Inter Tight", "regular", "16"], lh: "1.6", align: "left", grow: "auto-height", name: "c4 lede", x: 120, y: 252, w: 520, h: 52, fill: "#55606A", tok: "ink.600" },
  { k: "board", name: "c4 cta", x: 120, y: 344, w: 236, h: 52, fill: "#C4122F", tok: "red.600", radius: 2,
    children: [
    { k: "text", t: "Kongreye kayıt ol", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "center", grow: "auto-height", name: "c4 cta / label", x: 120, y: 360, w: 236, h: 23, fill: "#FFFFFF", tok: "on.red" },
    ] },
  { k: "text", t: "Derneği tanı", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "c4 cta link", x: 380, y: 356, w: 85, h: 23, fill: "#8F0F24", tok: "red.700" },
  { k: "rect", name: "c4 cta link under", x: 380, y: 380, w: 114, h: 1, fill: "#8F0F24", tok: "red.700" },
  { k: "text", t: "41 İL TEMSİLCİLİĞİ", font: ["JetBrains Mono", "500", "13"], lh: "1.2", ls: "1.1", align: "left", grow: "auto-width", name: "c4 map label", x: 720, y: 140, w: 161, h: 16, fill: "#5E6A71", tok: "ink.500" },
  { k: "map", name: "c4 map", x: 720, y: 164, w: 600, h: 300,
    dots: [
    [231, 38, 4, "#0E1318"],
    [277, 38, 4, "#0E1318"],
    [185, 75, 4, "#0E1318"],
    [231, 75, 4, "#0E1318"],
    [323, 75, 4, "#0E1318"],
    [369, 75, 4, "#0E1318"],
    [415, 75, 4, "#0E1318"],
    [508, 75, 4, "#0E1318"],
    [554, 75, 4, "#0E1318"],
    [92, 113, 4, "#0E1318"],
    [139, 113, 4, "#0E1318"],
    [185, 113, 4, "#0E1318"],
    [277, 113, 4, "#0E1318"],
    [323, 113, 4, "#0E1318"],
    [415, 113, 4, "#0E1318"],
    [462, 113, 4, "#0E1318"],
    [508, 113, 4, "#0E1318"],
    [46, 150, 4, "#0E1318"],
    [92, 150, 4, "#0E1318"],
    [185, 150, 4, "#0E1318"],
    [231, 150, 4, "#0E1318"],
    [277, 150, 4, "#0E1318"],
    [369, 150, 4, "#0E1318"],
    [415, 150, 4, "#0E1318"],
    [508, 150, 4, "#0E1318"],
    [554, 150, 4, "#0E1318"],
    [46, 188, 4, "#0E1318"],
    [139, 188, 4, "#0E1318"],
    [185, 188, 4, "#0E1318"],
    [277, 188, 4, "#0E1318"],
    [323, 188, 4, "#0E1318"],
    [369, 188, 4, "#0E1318"],
    [462, 188, 4, "#0E1318"],
    [508, 188, 4, "#0E1318"],
    [92, 225, 4, "#0E1318"],
    [139, 225, 4, "#0E1318"],
    [185, 225, 4, "#0E1318"],
    [277, 225, 4, "#0E1318"],
    [323, 225, 4, "#0E1318"],
    [415, 225, 4, "#0E1318"],
    [323, 263, 4, "#0E1318"],
    [323, 150, 7, "#C4122F"],
    ],
    d: "M589.3,220.5L574.4,227.3L563.5,217.1L527.2,211.9L513.9,218.2L478.4,224.4L461.7,223.7L425.8,238.8L400.2,238.9L383.6,231.3L349.3,242.5L339.2,234.7L337.5,257L329.1,265.8L320.8,274.6L309.3,256.4L321.1,241.4L302.1,244.8L276.1,235.6L254.7,258.6L207.4,263.1L182.2,241.6L148.6,240.3L141.4,256.9L119.9,261.7L89.8,240.3L55.8,241.1L37.3,201.2L14.6,179L29.7,147.8L10,128.7L44.5,90.3L92.5,88.7L105.6,58.3L164.9,63.6L202.4,37.6L238.7,26.2L290.2,25.4L344.6,53.6L389.2,69.1L425.5,63L452.3,66.5L489.1,45.6L522.3,43.7L552.3,63.4L557.6,77.5L554.6,97L577.7,107L590,118.7L568.7,130.1L578.4,176L572.3,188.4L589.3,220.5Z" },
  { k: "text", t: "Ankara", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 capital", x: 1060, y: 296, w: 100, h: 20, fill: "#55606A", tok: "ink.600" },
  { k: "text", t: "6.847 üye · 41 il · 12 çalışma grubu · 10 kılavuz", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 proof", x: 720, y: 480, w: 560, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "board", name: "c4 group 0", x: 720, y: 520, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Kardiyovasküler görüntüleme", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 0", x: 732, y: 532, w: 154, h: 39, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 1", x: 904, y: 520, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Kalp yetersizliği", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 1", x: 912, y: 532, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 2", x: 1084, y: 520, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Aritmi ve elektrofizyoloji", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 2", x: 1096, y: 532, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 3", x: 720, y: 588, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Kapak hastalıkları", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 3", x: 732, y: 600, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 4", x: 904, y: 588, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Hipertansiyon", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 4", x: 912, y: 600, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 5", x: 1084, y: 588, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Pulmoner hipertansiyon", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 5", x: 1096, y: 600, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 6", x: 720, y: 656, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Girişimsel kardiyoloji", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 6", x: 732, y: 668, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 7", x: 904, y: 656, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Kardiyometabolik", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 7", x: 912, y: 668, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 8", x: 1084, y: 656, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Lipid ve ateroskleroz", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 8", x: 1096, y: 668, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 9", x: 720, y: 724, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Geriatrik kardiyoloji", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 9", x: 732, y: 736, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 10", x: 904, y: 724, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Onkolojik kardiyoloji", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 10", x: 912, y: 736, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "board", name: "c4 group 11", x: 1084, y: 724, w: 176, h: 60, fill: "#FFFFFF", tok: "white", stroke: "#DDE1E4", sw: 1, stok: "line.soft", radius: 4,
    children: [
    { k: "text", t: "Spor kardiyolojisi", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c4 group name 11", x: 1096, y: 736, w: 154, h: 20, fill: "#333D45", tok: "ink.700" },
    ] },
  { k: "text", t: "12. Kongre · 22–25 Nisan 2027 · Antalya →", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "c4 congress", x: 720, y: 820, w: 296, h: 23, fill: "#8F0F24", tok: "red.700" },
  { k: "rect", name: "c4 congress under", x: 720, y: 844, w: 369, h: 1, fill: "#8F0F24", tok: "red.700" },
  { k: "rect", name: "img-c4-poster", x: 120, y: 440, w: 280, h: 196, fill: "#E8EBED", slot: true, radius: 8 },
  { k: "rect", name: "img-c4-audience", x: 408, y: 440, w: 272, h: 196, fill: "#E8EBED", slot: true, radius: 8 },
  { k: "rect", name: "img-c4-hall", x: 120, y: 644, w: 560, h: 196, fill: "#E8EBED", slot: true, radius: 8 },
];

/* --- page guard: Penpot switches pages asynchronously --------------------- */
const page = penpot.currentFile.pages.find((p) => p.name === PAGE);
if (!page) throw new Error("page not found: " + PAGE);
if (penpot.currentPage.id !== page.id) {
  penpot.openPage(page);
  return JSON.stringify({ status: "page-switch", page: PAGE,
    next: "the page switch is asynchronous: run this file once more" });
}

/* --- tokens: literal first, then bind (a binding alone paints nothing) ---- */
const set = (penpot.library.local.tokens.sets || []).find((s) => s.name === SET);
const byName = {};
if (set) (set.tokens || []).forEach((t) => { byName[t.name] = t; });
const bind = (s, token, props) => { if (token && byName[token]) s.applyToken(byName[token], props); return s; };

/* --- board: reuse and clear, or create below the last one ----------------- */
let board = (page.root.children || []).find((s) => s.name === BOARD);
if (board) {
  (board.children || []).slice().forEach((c) => c.remove());
  board.fills = [];
} else {
  board = penpot.createBoard();
  board.name = BOARD;
  page.root.appendChild(board);
  const bottom = (page.root.children || []).filter((s) => s.type === "board" && s.id !== board.id)
    .reduce((m, s) => Math.max(m, s.y + s.height), 240);
  board.x = 0;
  board.y = Math.round(bottom + 240);
}
board.resize(W, H);
board.fills = [{ fillColor: "#F2F4F5", fillOpacity: 1 }];
bind(board, "paper", ["fill"]);
const OX = board.x, OY = board.y;

/* --- builders ------------------------------------------------------------- */
const fill = (s, c, tok) => {
  if (!c) { s.fills = []; return s; }
  s.fills = [{ fillColor: c, fillOpacity: 1 }];
  return bind(s, tok, ["fill"]);
};
const stroke = (s, c, tok, w) => {
  s.strokes = [{ strokeColor: c, strokeOpacity: 1, strokeStyle: "solid", strokeWidth: w || 1, strokeAlignment: "inner" }];
  return bind(s, tok, ["strokeColor"]);
};
const FONT = { "Inter Tight": "gfont-inter-tight", "JetBrains Mono": "gfont-jetbrains-mono" };

function place(node, parent, ox, oy) {
  let s;
  if (node.k === "text") {
    const [fam, variant, size] = node.font;
    s = penpot.createText(node.t);
    s.name = node.name;
    s.fontId = FONT[fam];
    s.fontFamily = fam;
    s.fontVariantId = variant;
    s.fontSize = size;
    if (node.lh) s.lineHeight = node.lh;
    if (node.ls) s.letterSpacing = node.ls;
    if (node.align) s.align = node.align;
    parent.appendChild(s);
    s.growType = node.grow;
    s.resize(node.w, node.h);
  } else if (node.k === "board") {
    s = penpot.createBoard();
    s.name = node.name;
    parent.appendChild(s);
    s.fills = [];
    s.resize(node.w, node.h);
  } else if (node.k === "map") {
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + node.w + '" height="' + node.h +
      '" viewBox="0 0 ' + node.w + " " + node.h + '">' +
      '<path d="' + node.d + '" fill="#FFFFFF"/>' +
      node.dots.map((c) => '<circle cx="' + c[0] + '" cy="' + c[1] + '" r="' + c[2] + '" fill="' + c[3] + '"/>').join("") +
      "</svg>";
    s = penpot.createShapeFromSvg(svg);
    s.name = node.name;
    parent.appendChild(s);
  } else {
    s = penpot.createRectangle();
    s.name = node.name;
    parent.appendChild(s);
    s.resize(node.w, node.h);
  }
  s.x = ox + node.x;
  s.y = oy + node.y;
  if (s.type !== "board") s.x = ox + node.x;
  if (node.k !== "map") {
    fill(s, node.fill, node.tok);
    if (node.stroke) stroke(s, node.stroke, node.stok, node.sw);
  }
  if (node.radius) s.borderRadius = node.radius;
  if (node.opacity !== undefined) s.opacity = node.opacity;
  (node.children || []).forEach((c) => place(c, s, ox, oy));
  return s;
}

DATA.forEach((n) => place(n, board, OX, OY));
return JSON.stringify({ board: board.name, children: (board.children || []).length,
  photoSlots: DATA.filter((n) => n.slot).map((n) => n.name) });
