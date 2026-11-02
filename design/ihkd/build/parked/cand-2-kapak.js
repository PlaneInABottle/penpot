/**
 * Parked hero — "Dergi kapağı" (hero candidate 2), kept on request.
 *
 * This page is a journal cover: the society's own issue (İHKD, Cilt 12 · Sayı 1),
 * coverline "Hastanın hekimi.", a real ECG print as the cover figure and
 * "Bu sayıda" as the table of contents/routes.
 *
 * When to use it: after the congress (the home page stops being a congress
 * announcement), or as the opening of the publication/Yayın area. Not while the
 * congress poster (cand-1) is the live hero — the same page cannot carry two
 * cover objects.
 *
 * Run: python3 scripts/penpot_exec.py --file design/ihkd/build/parked/cand-2-kapak.js
 * Idempotent: reuses the `cand-2-kapak` board on `_scratch`, clears its children
 * and rebuilds them. A first run may only switch the page (Penpot switches
 * asynchronously); run it once more.
 *
 * Photo: Pexels 415779 by Pixabay — an ECG print close-up, no patient, no hand.
 * The slot `img-c2-ecg` is built empty; place the image with
 *   python3 design/ihkd/tools/media.py --restore --board cand-2-kapak --page _scratch
 * (provenance records the pinned source). Render: shots/hero-candidates-4/cand-2-kapak.png
 */


const PAGE = "_scratch";
const BOARD = "cand-2-kapak";
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
  { k: "rect", name: "cover page", x: 0, y: 108, w: 1440, h: 792, fill: "#FFFFFF", tok: "white" },
  { k: "text", t: "İHKD", font: ["JetBrains Mono", "600", "80"], lh: "1.0", ls: "2", align: "left", grow: "fixed", name: "c2 mark", x: 120, y: 140, w: 200, h: 80, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "KARDİYOVASKÜLER KLİNİK", font: ["JetBrains Mono", "500", "13"], lh: "1.2", ls: "1.1", align: "left", grow: "auto-width", name: "c2 journal", x: 120, y: 252, w: 196, h: 16, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Cilt 12 · Sayı 1 · Mart 2027", font: ["JetBrains Mono", "regular", "13"], lh: "1.5", ls: "0.2", align: "left", grow: "auto-width", name: "c2 issue", x: 120, y: 272, w: 224, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Hastanın hekimi.", font: ["Inter Tight", "600", "44"], lh: "1.06", ls: "-1.3", align: "left", grow: "auto-height", name: "c2 line", x: 120, y: 304, w: 560, h: 47, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "İç hastalıkları ve kardiyolojinin yayını: kılavuz, kongre, akademi.", font: ["Inter Tight", "regular", "16"], lh: "1.6", align: "left", grow: "auto-height", name: "c2 sub", x: 120, y: 364, w: 500, h: 26, fill: "#55606A", tok: "ink.600" },
  { k: "text", t: "BU SAYIDA", font: ["JetBrains Mono", "500", "13"], lh: "1.2", ls: "1.1", align: "left", grow: "auto-width", name: "c2 toc label", x: 120, y: 440, w: 81, h: 16, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Kongre", font: ["Inter Tight", "600", "16"], lh: "1.5", align: "left", grow: "auto-width", name: "c2 toc name 0", x: 120, y: 472, w: 52, h: 24, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "s. 01", font: ["JetBrains Mono", "regular", "13"], lh: "1.5", ls: "0.2", align: "right", grow: "auto-height", name: "c2 toc page 0", x: 500, y: 472, w: 100, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "22–25 Nisan 2027 · Antalya", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 toc note 0", x: 120, y: 492, w: 380, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "rect", name: "c2 toc rule 0", x: 120, y: 516, w: 480, h: 1, fill: "#DDE1E4", tok: "line.soft" },
  { k: "text", t: "Kılavuzlar", font: ["Inter Tight", "600", "16"], lh: "1.5", align: "left", grow: "auto-width", name: "c2 toc name 1", x: 120, y: 524, w: 71, h: 24, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "s. 12", font: ["JetBrains Mono", "regular", "13"], lh: "1.5", ls: "0.2", align: "right", grow: "auto-height", name: "c2 toc page 1", x: 500, y: 524, w: 100, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "2027 hipertansiyon", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 toc note 1", x: 120, y: 544, w: 380, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "rect", name: "c2 toc rule 1", x: 120, y: 568, w: 480, h: 1, fill: "#DDE1E4", tok: "line.soft" },
  { k: "text", t: "Akademi", font: ["Inter Tight", "600", "16"], lh: "1.5", align: "left", grow: "auto-width", name: "c2 toc name 2", x: 120, y: 576, w: 64, h: 24, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "s. 30", font: ["JetBrains Mono", "regular", "13"], lh: "1.5", ls: "0.2", align: "right", grow: "auto-height", name: "c2 toc page 2", x: 500, y: 576, w: 100, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "KKY kursu · 6 STE", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 toc note 2", x: 120, y: 596, w: 380, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "rect", name: "c2 toc rule 2", x: 120, y: 620, w: 480, h: 1, fill: "#DDE1E4", tok: "line.soft" },
  { k: "text", t: "Topluluk", font: ["Inter Tight", "600", "16"], lh: "1.5", align: "left", grow: "auto-width", name: "c2 toc name 3", x: 120, y: 628, w: 62, h: 24, fill: "#0E1318", tok: "ink.900" },
  { k: "text", t: "s. 44", font: ["JetBrains Mono", "regular", "13"], lh: "1.5", ls: "0.2", align: "right", grow: "auto-height", name: "c2 toc page 3", x: 500, y: 628, w: 100, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "41 il · 12 çalışma grubu", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 toc note 3", x: 120, y: 648, w: 380, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "rect", name: "c2 toc rule 3", x: 120, y: 672, w: 480, h: 1, fill: "#DDE1E4", tok: "line.soft" },
  { k: "board", name: "c2 cta", x: 120, y: 700, w: 236, h: 52, fill: "#C4122F", tok: "red.600", radius: 2,
    children: [
    { k: "text", t: "Kongreye kayıt ol", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "center", grow: "auto-height", name: "c2 cta / label", x: 120, y: 716, w: 236, h: 23, fill: "#FFFFFF", tok: "on.red" },
    ] },
  { k: "text", t: "Derneği tanı", font: ["Inter Tight", "500", "16"], lh: "1.4", align: "left", grow: "auto-width", name: "c2 cta link", x: 380, y: 716, w: 85, h: 23, fill: "#8F0F24", tok: "red.700" },
  { k: "rect", name: "c2 cta link under", x: 380, y: 740, w: 114, h: 1, fill: "#8F0F24", tok: "red.700" },
  { k: "text", t: "6.847 üye · 41 il · 12 çalışma grubu · 10 kılavuz", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 imprint", x: 120, y: 852, w: 520, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "text", t: "Kapak: EKG kaydı · 25 mm/s · 10 mm/mV", font: ["Inter Tight", "regular", "13"], lh: "1.5", align: "left", grow: "auto-height", name: "c2 caption", x: 700, y: 812, w: 560, h: 20, fill: "#5E6A71", tok: "ink.500" },
  { k: "rect", name: "img-c2-ecg", x: 700, y: 160, w: 620, h: 640, fill: "#E8EBED", slot: true, radius: 8 },
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
