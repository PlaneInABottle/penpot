/**
 * Components — İHKD bileşen kitaplığı (`component sheet`, sayfa `Components`).
 *
 *   python3 design/ihkd/build/build.py screen-components
 *
 * Her tahta gerçek bir Penpot kütüphane bileşenidir (`penpot.library.local
 * .createComponent`), adı `aile-durum` şemasındadır:
 *   button-primary · button-primary-hover · field-error · chip-active · tag …
 * Varsayılan durum yalnız taban adını taşır (`button-primary`), etkileşim
 * durumları `-durum` ile eklenir.
 *
 * NEDEN TİRE, EĞİK ÇİZGİ DEĞİL (2026-11-03, canlı): Penpot bir tahta/bileşen
 * adındaki `/` karakterini path ayırıcısı sayıp adı `button / primary`ya
 * normalize ediyor (bilinen `nav/top` → `nav / nav` hatası). İlk build'de 30
 * tahtanın 15'i (`button/*`) bu yüzden bileşene dönüşmedi: script adı
 * `button/primary` ile aradı, tahta `button / primary` adıyla duruyordu ve
 * eşleşme sessizce boş döndü. Aile kimliği artık ön ekte taşınır
 * (`button-`, `field-`, `row-`, `chip-`); eski normalize adlı tahtalar build
 * başında temizlenir.
 *
 * KİMLİK KORUNUR: ekranlar bu bileşenleri HENÜZ KULLANMAZ (instance'a geçmek
 * kırıcı bir değişiklik; sonraki iş). Bu sayfa tasarımcı devri için kütüphanedir.
 *
 * Yeniden çalıştırma kayıpsızdır: tahtalar adla bulunur, çocukları temizlenip
 * yeniden çizilir; bileşen yalnız eksikse yaratılır (kütüphanede adı varsa
 * ikinci bir kopya açılmaz). async commit yüzden ilk çağrıda bileşen
 * yaratılamayan tahta ikinci çalıştırmada tamamlanır.
 */
const S = IK;

const PAGE = "Components";
const SHEET = "component sheet";
const p = (penpot.currentFile.pages || []).filter((x) => x.name === PAGE)[0];
if (!p) throw new Error("page not found: " + PAGE);
penpot.openPage(p);

let sheet = (p.root.children || []).filter((x) => x.name === SHEET)[0];
if (!sheet) {
  sheet = penpot.createBoard();
  sheet.name = SHEET;
  p.root.appendChild(sheet);
  sheet.fills = [];
  S.paint(sheet, "paper");
}
sheet.x = 0;
sheet.y = 0;
sheet.resize(1440, 2400);

/* The 2026-11-03 first run left 15 slot boards + their captions whose names
   Penpot normalised to "button / primary". They are this script's own
   leftovers, not design: drop anything on the sheet that still carries the
   path separator before the re-layout. */
(sheet.children || []).filter((c) => c.name.indexOf("/") >= 0).forEach((c) => c.remove());

/* The sheet is authored here and never cleared by S.start: labels, rules and
   captions are re-created on every run, so a second run doubled them (16 high
   text.overlap findings). Drop every non-board child; the slot boards stay,
   because the 30 library components are their main instances. */
(sheet.children || []).filter((c) => c.type !== "board").forEach((c) => c.remove());


/* --------------------------------------------------------------- tahta yerleşimi */
/** Adla bul-veya-yarat, çocukları temizle, boyut/konum yaz (idempotent). */
function slot(name, x, y, w, h) {
  let b = (sheet.children || []).filter((c) => c.name === name)[0];
  if (!b) {
    b = penpot.createBoard();
    b.name = name;
    sheet.appendChild(b);
  } else {
    (b.children || []).slice().forEach((c) => c.remove());
  }
  b.fills = [];
  b.strokes = [];
  b.resize(w, h);
  b.x = x;
  b.y = y;
  return b;
}

const STATES = ["default", "hover", "focus", "active", "disabled"];
const stateName = (base, state) => (state === "default" ? base : base + "-" + state);

/* ------------------------------------------------------------------- çizimler */
const BTN = {
  primary: { label: "Kongreye kayıt ol", fill: "red.600", ink: "on.red" },
  secondary: { label: "Taslak kaydet", fill: "white", ink: "ink.900", stroke: "line.strong" },
  ghost: { label: "Derneği tanı", fill: "white", ink: "ink.900", stroke: "red.600" },
};

function buttonStyle(spec, state) {
  const s = { fill: spec.fill, ink: spec.ink, stroke: spec.stroke || null, strokeW: 1 };
  if (state === "hover") s.fill = spec.fill === "white" ? "red.050" : "red.700";
  /* A focus ring on the saturated primary must be white: red.600 on red.600
     painted nothing and the focus variant read identical to default (1:1
     sheet check, 2026-11-03). Ghost/secondary keep the red ring. */
  if (state === "focus") { s.stroke = spec.fill === "red.600" ? "on.red" : (spec.stroke === "red.600" ? "red.700" : "red.600"); s.strokeW = 2; }
  if (state === "active") { s.fill = spec.fill === "white" ? "red.050" : "red.700"; s.stroke = spec.stroke || (spec.fill === "red.600" ? "on.red" : "red.600"); s.strokeW = 2; }
  if (state === "disabled") { s.fill = "surface.alt"; s.ink = "ink.400"; s.stroke = "line.soft"; s.strokeW = 1; }
  return s;
}

function drawButton(variant) {
  return (b, x, y, w, h, state) => {
    const spec = BTN[variant];
    const st = buttonStyle(spec, state);
    S.paint(b, st.fill);
    if (st.stroke) S.stroke(b, st.stroke, st.strokeW);
    S.corners(b, "radius.2");
    S.text(b, "label", spec.label, "nav", st.ink, { x: x, y: y + Math.round((h - 20) / 2), w: w, align: "center" });
  };
}

const FIELD_STATES = {
  default: { label: "ink.500", value: "ink.900", line: "line.strong", lineW: 1 },
  hover: { label: "ink.700", value: "ink.900", line: "ink.500", lineW: 1 },
  focus: { label: "red.700", value: "ink.900", line: "red.600", lineW: 2 },
  error: { label: "red.700", value: "ink.900", line: "red.600", lineW: 1, hint: "Geçerli bir e-posta girin." },
  disabled: { label: "ink.400", value: "ink.400", line: "line.soft", lineW: 1 },
};

function drawField(b, x, y, w, h, state) {
  const st = FIELD_STATES[state] || FIELD_STATES.default;
  b.fills = [];
  S.text(b, "label", "E-POSTA", "label", st.label, { x: x + 20, y: y + 20, w: w - 40 });
  S.text(b, "value", "selin.aydin@ankara.edu.tr", "body", st.value, { x: x + 20, y: y + 44, w: w - 40 });
  S.rect(b, "line", x + 20, y + 74, w - 40, st.lineW, st.line);
  if (st.hint) S.text(b, "hint", st.hint, "meta", "red.700", { x: x + 20, y: y + 84, w: w - 40 });
}

const ROW_STATES = {
  default: { fill: "white", stroke: null, title: "ink.900" },
  hover: { fill: "red.050", stroke: null, title: "ink.900" },
  focus: { fill: "white", stroke: "red.600", title: "ink.900" },
};

function drawRow(b, x, y, w, h, state) {
  const st = ROW_STATES[state] || ROW_STATES.default;
  S.paint(b, st.fill);
  if (st.stroke) S.stroke(b, st.stroke, 2);
  S.text(b, "title", "Kalp yetersizliği", "bodyMed", st.title, { x: x + 20, y: y + 20, w: w - 76 });
  S.text(b, "meta", "508 üye · Prof. Dr. Murat Şen", "meta", "ink.500", { x: x + 20, y: y + 46, w: w - 76 });
  S.text(b, "arrow", "→", "nav", "ink.500", { x: x + w - 44, y: y + 24, w: 24, align: "right" });
}

const CHIP_STATES = {
  default: { fill: "surface.alt", ink: "ink.700", stroke: null },
  hover: { fill: "red.050", ink: "red.700", stroke: null },
  active: { fill: "red.600", ink: "on.red", stroke: null },
  disabled: { fill: "white", ink: "ink.400", stroke: "line.soft" },
};

function drawChip(b, x, y, w, h, state) {
  const st = CHIP_STATES[state] || CHIP_STATES.default;
  S.paint(b, st.fill);
  if (st.stroke) S.stroke(b, st.stroke, 1);
  S.text(b, "label", "Tümü 12", "label", st.ink,
    { x: x, y: y + Math.round((h - 20) / 2), w: w, align: "center" });
}

function drawTag(b, x, y) {
  S.tag(b, "tag", "KONGRE", x, y, "red.600");
}

function drawCard(b, x, y, w, h) {
  S.paint(b, "white");
  S.stroke(b, "line.soft", 1);
  S.text(b, "kicker", "ÇALIŞMA GRUBU", "label", "ink.500", { x: x + 20, y: y + 24, w: w - 40 });
  S.text(b, "title", "Kardiyovasküler görüntüleme", "bodyMed", "ink.900", { x: x + 20, y: y + 48, w: w - 40 });
  S.text(b, "meta", "412 üye · Doç. Dr. Elif Karaca", "meta", "ink.500", { x: x + 20, y: y + 100, w: w - 40 });
  S.link(b, "cta", "Grubu gör →", x + 20, y + 128, "red.700");
}

function drawStat(b, x, y) {
  S.text(b, "value", "6.847", "stat", "ink.900", { x: x + 20, y: y + 20 });
  S.text(b, "label", "üye", "meta", "ink.600", { x: x + 20, y: y + 72, w: 160 });
}

/* ------------------------------------------------------------------- aileler */
const FAMILIES = [
  { base: "button-primary", w: 240, h: 52, states: STATES, draw: drawButton("primary") },
  { base: "button-secondary", w: 240, h: 52, states: STATES, draw: drawButton("secondary") },
  { base: "button-ghost", w: 240, h: 52, states: STATES, draw: drawButton("ghost") },
  { base: "field", w: 320, h: 104, states: ["default", "hover", "focus", "error", "disabled"], draw: drawField },
  { base: "row", w: 320, h: 84, states: ["default", "hover", "focus"], draw: drawRow },
  { base: "chip", w: 160, h: 44, states: ["default", "hover", "active", "disabled"], draw: drawChip },
  { base: "tag", w: 160, h: 24, states: ["default"], draw: drawTag },
  { base: "card", w: 320, h: 160, states: ["default"], draw: drawCard },
  { base: "stat", w: 200, h: 96, states: ["default"], draw: drawStat },
];

/* --------------------------------------------------------------- kitap başlığı */
S.text(sheet, "sheet label", "BİLEŞEN KİTAPLIĞI · İHKD", "label", "ink.500", { x: 40, y: 64 });
S.text(sheet, "sheet title", "Bileşen kitaplığı", "display", "ink.900", { x: 40, y: 88, w: 900 });
S.text(sheet, "sheet lede",
  "Dokuz aile, durum varyantlarıyla. Her tahta bir kütüphane bileşenidir; ad `aile-durum` şemasını izler.",
  "body", "ink.600", { x: 40, y: 190, w: 760 });
S.rule(sheet, "sheet rule", 40, 288, 1360, "line.strong", 2);

const COL = 340, CELLX = 40, CAPGAP = 12, ROWGAP = 40;
let familyY = 320;
const names = [];

FAMILIES.forEach((fam) => {
  S.text(sheet, "family label " + fam.base, fam.base.toUpperCase(), "label", "ink.500", { x: CELLX, y: familyY });
  const rows = Math.ceil(fam.states.length / 4);
  fam.states.forEach((state, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = CELLX + col * COL;
    const cy = familyY + 32 + row * (fam.h + CAPGAP + ROWGAP);
    const name = stateName(fam.base, state);
    const b = slot(name, x, cy, fam.w, fam.h);
    fam.draw(b, x, cy, fam.w, fam.h, state);
    S.text(sheet, "caption " + name, name, "meta", "ink.500", { x: x, y: cy + fam.h + CAPGAP, w: fam.w });
    names.push(name);
  });
  familyY += 32 + rows * (fam.h + CAPGAP + ROWGAP) + 24;
});

/* ------------------------------------------------------- kütüphane bileşenleri */
const lib = penpot.library.local;
const known = {};
(lib.components || []).forEach((c) => { known[c.name] = c; });
const created = [], present = [], failed = [];
names.forEach((name) => {
  const b = (sheet.children || []).filter((c) => c.name === name)[0];
  if (!b) return;
  let isMain = false;
  try { isMain = b.isComponentMainInstance(); } catch (e) { isMain = false; }
  if (isMain || known[name]) { present.push(name); return; }
  try {
    lib.createComponent([b]);
    created.push(name);
  } catch (e) {
    failed.push(name + ": " + e.message);
    S.warnings.push("component not created: " + name + " (" + e.message + ") — run screen-components once more");
  }
});

const y = familyY + 32;
sheet.resize(1440, S.snap(y));

return JSON.stringify({
  board: SHEET,
  warnings: S.warnings.slice(0, 20),
  gaps: [],
  components: { total: names.length, created, present, failed },
});
