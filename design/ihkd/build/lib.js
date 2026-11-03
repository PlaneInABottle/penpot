/**
 * İHKD build library — daylight clinical viewer. Runs inside the Penpot plugin.
 *
 *   python3 design/ihkd/build/build.py screen-01
 *
 * One surface: cool clinical paper, near-black ink, one arterial red. Cards and
 * 1px rules carry the structure; the spine is an oversized graphite section
 * numeral plus full-bleed photography with no frame.
 *
 * Six type sizes: 13 / 16 / 22 / 30 / 44 / 80. One 13px microcopy size covers kickers,
 * helper text, captions, time gutter, IDs and prices; the 13→16 step (1.23) is the
 * documented body/meta-pair exception. Text boxes are seeded from an estimated
 * line count; `IK.fit()` re-measures them after commit.
 */
const IK = (function () {
  const H = storage.H;
  const SET = "ihkd";
  const W = 1440;
  const X = 120;
  const CW = 1200;

  const FONT = {
    sans: { id: "gfont-inter-tight", family: "Inter Tight" },
    mono: { id: "gfont-jetbrains-mono", family: "JetBrains Mono" },
  };

  const ROLE = {
    label:  { font: "mono", variant: "500", size: 13, lh: 1.2, track: 1.1, upper: true },
    meta:   { font: "sans", variant: "regular", size: 13, lh: 1.5 },
    data:   { font: "mono", variant: "400", size: 13, lh: 1.5, track: 0.2 },
    dataLg: { font: "mono", variant: "500", size: 16, lh: 1.4, track: 0.2 },
    body:   { font: "sans", variant: "regular", size: 16, lh: 1.6 },
    bodyMed:{ font: "sans", variant: "600", size: 16, lh: 1.5 },
    nav:    { font: "sans", variant: "500", size: 16, lh: 1.4 },
    lead:   { font: "sans", variant: "regular", size: 22, lh: 1.5 },
    h3:     { font: "sans", variant: "600", size: 30, lh: 1.2, track: -0.6 },
    h2:     { font: "sans", variant: "600", size: 44, lh: 1.06, track: -1.3 },
    figure: { font: "mono", variant: "500", size: 30, lh: 1.1, track: -0.6 },
    stat:   { font: "mono", variant: "500", size: 44, lh: 1.1, track: -0.6 },
    display:{ font: "sans", variant: "700", size: 80, lh: 0.98, track: -2.6 },
    wordmark:{ font: "mono", variant: "600", size: 22, lh: 1.0, track: 0.6 },
  };

  const warnings = [];
  const gaps = [];
  let OX = 0, OY = 0, PB = null, NUM = 0;

  const snap = (v) => Math.round(v / 4) * 4;
  const nrm = (n) => String(n).replace(/\s*\/\s*/g, " / ");

  function token(name) {
    return H.tokens(SET).byName[name] || null;
  }

  function bind(shape, name, props) {
    const r = H.apply(shape, SET, name, props);
    if (!r.applied) { warnings.push("missing token " + name + " on " + shape.name); gaps.push(name); }
    return r;
  }

  const paint = (shape, name) => bind(shape, name, ["fill"]);

  function corners(shape, name) {
    ["borderRadiusTopLeft", "borderRadiusTopRight", "borderRadiusBottomRight", "borderRadiusBottomLeft"]
      .forEach((p) => bind(shape, name, [p]));
    return shape;
  }

  function stroke(shape, name, width, align) {
    shape.strokes = [{ strokeColor: "#000000", strokeOpacity: 1, strokeStyle: "solid", strokeWidth: width || 1, strokeAlignment: align || "inner" }];
    bind(shape, name, ["strokeColor"]);
    return shape;
  }

  function page(name) {
    const p = penpot.currentFile.pages.filter((x) => x.name === name)[0];
    if (!p) throw new Error("page not found: " + name);
    return p;
  }

  function start(pageName, boardName, height) {
    const p = page(pageName);
    penpot.openPage(p);
    const wanted = nrm(boardName);
    let b = (p.root.children || []).filter((s) => s.name === wanted)[0] || null;
    if (!b) {
      b = penpot.createBoard();
      b.name = wanted;
      p.root.appendChild(b);
      const bottom = (p.root.children || []).filter((s) => s.type === "board" && s.id !== b.id)
        .reduce((m, s) => Math.max(m, s.y + s.height), 200);
      b.x = 0;
      b.y = snap(bottom + 240);
    } else {
      (b.children || []).slice().forEach((c) => c.remove());
    }
    b.fills = [];
    b.resize(W, snap(height));
    PB = b; OX = b.x; OY = b.y; NUM = 0;
    paint(b, "paper");
    return b;
  }

  function rect(parent, name, x, y, w, h, fillToken, opts) {
    const o = opts || {};
    const r = penpot.createRectangle();
    r.name = nrm(name);
    (parent || PB).appendChild(r);
    r.resize(w, h);
    // raw: a bullet dot is centred on a line's ink, and the 4px grid would
    // pull it up to 2px off that centre — dots opt out, layout does not.
    r.x = OX + (o.raw ? Math.round(x) : snap(x));
    r.y = OY + (o.raw ? Math.round(y) : snap(y));
    if (fillToken) paint(r, fillToken); else r.fills = [];
    if (o.stroke) stroke(r, o.stroke, o.strokeWidth || 1);
    if (o.radius) corners(r, o.radius);
    return r;
  }

  function board(parent, name, x, y, w, h, fillToken) {
    const b = penpot.createBoard();
    b.name = nrm(name);
    (parent || PB).appendChild(b);
    b.fills = [];
    b.resize(snap(w), snap(h));
    b.x = OX + snap(x);
    b.y = OY + snap(y);
    if (fillToken) paint(b, fillToken);
    return b;
  }

  function estLines(chars, w, size, mono) {
    const cpl = Math.max(6, Math.floor(w / (size * (mono ? 0.62 : 0.5))));
    return String(chars).split("\n").reduce((n, line) => n + Math.max(1, Math.ceil(line.length / cpl)), 0);
  }

  function text(parent, name, chars, roleName, colorToken, opts) {
    const o = opts || {};
    const r = ROLE[roleName];
    if (!r) throw new Error("unknown role " + roleName + " for " + name);
    const t = penpot.createText(String(chars));
    t.name = nrm(name);
    t.fontId = FONT[r.font].id;
    t.fontFamily = FONT[r.font].family;
    t.fontVariantId = r.variant;
    t.fontSize = String(r.size);
    t.lineHeight = String(r.lh);
    if (r.track) t.letterSpacing = String(r.track);
    if (r.upper) t.textTransform = "uppercase";
    (parent || PB).appendChild(t);
    if (o.w) {
      const lines = estLines(chars, o.w, r.size, r.font === "mono");
      t.resize(o.w, Math.ceil(r.size * r.lh * lines));
      t.growType = "auto-height";
    } else {
      // Never leave a 1x1 box to async layout: a board-scale build can
      // return before unmeasured auto-width texts commit, and the exporter
      // clips them to their box (invisible nav on a finished board). Seed
      // an estimated width now; fit() tightens it once ink commits.
      const est = Math.ceil(String(chars).length * r.size * (r.font === "mono" ? 0.62 : 0.55)) + 8;
      t.resize(Math.max(est, 12), Math.ceil(r.size * r.lh));
      t.growType = "auto-width";
    }
    if (o.align) t.align = o.align;
    t.x = OX + snap(o.x || 0);
    t.y = OY + snap(o.y || 0);
    if (o.opacity !== undefined) t.opacity = o.opacity;
    if (colorToken) paint(t, colorToken);
    bind(t, "fs." + r.size, ["fontSize"]);
    return t;
  }

  const rule = (parent, name, x, y, w, colorToken, thick) =>
    rect(parent, name, x, y, w, thick || 1, colorToken || "line.soft");

  const vrule = (parent, name, x, y, h, colorToken) =>
    rect(parent, name, x, y, 1, h, colorToken || "line.soft");

  /* ------------------------------------------------------------------ atoms */

  function btn(parent, name, label, x, y, w, h, kind) {
    const k = kind || "primary";
    const fill = { primary: "red.600", secondary: null, onred: "bone", ghost: null }[k];
    const ink = { primary: "on.red", secondary: "ink.900", onred: "red.700", ghost: "ink.900" }[k];
    const b = board(parent, name, x, y, w, h, fill);
    if (k === "secondary") stroke(b, "line.strong", 1);
    if (k === "ghost") stroke(b, "red.600", 1);
    corners(b, "radius.2");
    text(b, name + " / label", label, "nav", ink, { x: x, y: y + (h - 20) / 2, align: "center", w: w });
    return b;
  }

  /**
   * A link underline is the label's ink, not a per-character guess: "PDF indir →"
   * advances 82px while the old 8.2px/char model drew 92px. Until layout commits,
   * the text's own seeded width is the closest honest measure; fit() calls the
   * same function again once textBounds exists.
   */
  function underlineWidth(t) {
    const b = t.textBounds;
    if (b && b.height) return Math.ceil(b.width) + 2;
    return Math.max(12, Math.ceil(t.width));
  }

  function fitLink(t) {
    if (t.type !== "text" || !t.textBounds || !t.textBounds.height || !t.parent) return 0;
    const under = (t.parent.children || []).filter((c) => c.name === t.name + " under")[0];
    if (!under) return 0;
    const w = underlineWidth(t);
    if (Math.abs(under.width - w) > 0.5) { under.resize(w, under.height); return 1; }
    return 0;
  }

  function link(parent, name, label, x, y, colorToken) {
    const t = text(parent, name, label, "nav", colorToken || "red.700", { x: x, y: y });
    rect(parent, name + " under", x, y + 24, underlineWidth(t), 1, colorToken || "red.700");
    return t;
  }

  function tag(parent, name, label, x, y, colorToken) {
    rect(parent, name + " dot", x, y + 5, 8, 8, colorToken || "red.600");
    text(parent, name, label, "label", colorToken || "ink.600", { x: x + 16, y: y });
  }

  /**
   * One chip row: pills sized from their label's advance, not from a
   * per-character guess. İHKD 03/04 sized them `length * 7.4 + 32` while the
   * mono label advances 0.6em plus its 1.1px tracking — 8.9px per character
   * at 13px — and the pill carried no right padding at all, so every chip
   * clipped its last word (11 chips, 4-17px short; measured ink 124.6 for 14
   * characters). A monospace advance is exact, so the pill is ink + symmetric
   * pad, rounded UP to the 4px grid the layout snaps to. Throws on a non-mono
   * role: an advance model for proportional text is the same guess in a new
   * coat. `opts.active` marks the filled pill; returns the y below the row.
   */
  function chips(parent, name, items, x, y, opts) {
    const o = opts || {};
    const roleName = o.role || "label";
    const r = ROLE[roleName];
    if (!r) throw new Error("chips: unknown role " + roleName);
    if (r.font !== "mono") throw new Error("chips: role " + roleName + " is not mono, advance is not exact");
    const pad = o.pad === undefined ? 16 : o.pad;
    const gap = o.gap === undefined ? 8 : o.gap;
    const h = o.h === undefined ? 36 : o.h;
    const advance = 0.6 * r.size + (r.track || 0);
    const box = Math.round(r.size * r.lh);
    let cx = x;
    items.forEach((label, i) => {
      const ink = Math.ceil(String(label).length * advance);
      const w = Math.ceil((ink + 2 * pad) / 4) * 4;
      const on = o.active === i;
      const b = board(parent, name + " " + i, cx, y, w, h,
        on ? (o.onFill || "red.600") : (o.fill || "surface.alt"));
      if (!on && o.stroke) stroke(b, o.stroke, o.strokeWidth || 1);
      text(b, name + " text " + i, label, roleName, on ? (o.onInk || "on.red") : (o.ink || "ink.700"),
        { x: cx + pad, y: y + Math.round((h - box) / 2) });
      cx += w + gap;
    });
    return y + h + (o.after || 0);
  }

  /**
   * Section head with the graphite numeral that is this system's spine. The numeral is
   * decorative-structural: it carries the page order, not a section id the copy needs.
   */
  function head(parent, x, y, label, title, opts) {
    const o = opts || {};
    NUM += 1;
    const num = o.num || ("0" + NUM).slice(-2);
    text(parent, "head num " + num, num, "h2", "ink.400", { x: x, y: y - 4 });
    text(parent, "head label " + label, label, "label", "ink.500", { x: x + 148, y: y + 4 });
    if (o.link) link(parent, "head link " + label, o.link, X + CW - 40 - Math.round(o.link.length * 8.2), y + 2, "ink.900");
    if (o.index && !o.link) text(parent, "head index " + label, o.index, "data", "ink.500", { x: X + CW - 140, y: y + 6, w: 140, align: "right" });
    text(parent, "head title " + label, title, "h2", "ink.900", { x: x + 148, y: y + 26, w: o.w || 760 });
    rule(parent, "head rule " + label, x, y + (o.ruleAt || 92), CW, "line.strong", 1);
    return y + (o.next || 132);
  }

  function pageHead(parent, label, title, lede, opts) {
    const o = opts || {};
    const role = o.role || "h2";
    text(parent, "ph label", label, "label", "ink.500", { x: X, y: 156 });
    text(parent, "ph title", title, role, "ink.900", { x: X, y: 188, w: o.w || 900 });
    if (lede) text(parent, "ph lede", lede, "lead", "ink.600", { x: X, y: o.ledeY || 262, w: o.ledeW || 640 });
    rule(parent, "ph rule", X, o.ruleY || 352, CW, "line.strong", 1);
    rect(parent, "ph bar", X, (o.ruleY || 352) - 2, 96, 3, "red.600");
    return o.next || 412;
  }

  function stat(parent, name, value, label, x, y, w) {
    text(parent, name + " value", value, "stat", "ink.900", { x: x, y: y });
    text(parent, name + " label", label, "meta", "ink.600", { x: x, y: y + 56, w: w || 240 });
  }

  function field(parent, name, label, value, x, y, w, opts) {
    const o = opts || {};
    text(parent, name + " label", label, "label", o.error ? "red.700" : "ink.500", { x: x, y: y });
    text(parent, name + " value", value, "body", o.placeholder ? "ink.500" : "ink.900", { x: x, y: y + 22 });
    rect(parent, name + " line", x, y + 52, w, 1, o.error ? "red.600" : "line.strong");
    if (o.hint) text(parent, name + " hint", o.hint, "meta", "red.700", { x: x, y: y + 60, w: w });
    return null;
  }

  function photo(parent, name, x, y, w, h, caption) {
    const slot = rect(parent, name, x, y, w, h, "surface.alt");
    if (caption) text(parent, name + " caption", caption, "meta", "ink.500", { x: x, y: y + h + 12, w: w });
    return slot;
  }

  function masthead(parent, active, opts) {
    const o = opts || {};
    rect(parent, "top bar", 0, 0, W, 4, "red.600");
    text(parent, "masthead mark", "İHKD", "wordmark", "ink.900", { x: X, y: 34 });
    text(parent, "masthead sub", "ÜYE PLATFORMU", "label", "ink.500", { x: X + 104, y: 38 });
    const links = ["Dernek", "Çalışma grupları", "Kongre", "Akademi", "Yayın", "Haberler"];
    let x = 500;
    links.forEach((l) => {
      const on = l === active;
      text(parent, "nav " + l, l, "nav", on ? "ink.900" : "ink.500", { x: x, y: 32 });
      const w = Math.round(l.length * 8.2);
      if (on) rect(parent, "nav active " + l, x, 56, w, 2, "red.600");
      x += w + 26;
    });
    text(parent, "masthead login", "Üye girişi", "nav", "ink.700", { x: X + CW - 236, y: 32 });
    // cta: "primary" (default, converting pages) or "ghost" (a quiet white
    // button where the screen already carries its own red action, e.g. home).
    // Dominance is visual: the ux-gate counts only saturated-fill buttons.
    if (o.cta !== false) btn(parent, "masthead cta", "Üye ol", X + CW - 136, 22, 136, 40, o.cta === "ghost" ? "ghost" : "primary");
    rule(parent, "masthead rule", 0, 84, W, "line.soft");
    return 108;
  }

  /** A bone sheet inside the viewer: the publication/record mode (journal, guideline, article). */
  function sheet(parent, name, x, y, w, h) {
    const b = board(parent, name, x, y, w, h, "bone");
    return b;
  }

  function footer(parent, y) {
    const h = 320;
    const b = board(parent, "footer", 0, y, W, h, "white");
    rect(b, "footer bar", 0, y, W, 2, "red.600");
    text(b, "footer mark", "İHKD", "wordmark", "ink.900", { x: X, y: y + 56 });
    text(b, "footer claim", "Hastanın hekimi.", "lead", "ink.900", { x: X, y: y + 96, w: 380 });
    text(b, "footer address", "Meşrutiyet Cad. 24/7, 06420 Çankaya, Ankara\n+90 312 425 18 40 · info@ihkd.org.tr", "meta", "ink.500", { x: X, y: y + 156, w: 380 });
    const cols = [
      ["Dernek", ["Hakkında", "Yönetim", "Çalışma grupları", "Tüzük"]],
      ["Kongre", ["12. Kongre", "Program", "Bildiri", "Kayıt"]],
      ["Akademi", ["Kurslar", "Kılavuzlar", "Dergi", "STE"]],
      ["Üyelik", ["Başvuru", "Aidat", "Üye girişi", "İletişim"]],
    ];
    cols.forEach((c, i) => {
      const cx = X + 600 + i * 150;
      text(b, "footer col " + i, c[0], "label", "ink.500", { x: cx, y: y + 56 });
      c[1].forEach((it, j) => text(b, "footer " + i + "." + j, it, "meta", "ink.600", { x: cx, y: y + 84 + j * 26 }));
    });
    rule(b, "footer rule", X, y + 248, CW, "line.soft");
    text(b, "footer legal", "© 2026 İHKD · KVKK · Çerez politikası", "data", "ink.500", { x: X, y: y + 268 });
    text(b, "footer legal 2", "Tasarım çalışması — kurum ve kişiler kurgudur.", "data", "ink.500", { x: X + CW - 420, y: y + 268, w: 420, align: "right" });
    return b;
  }

  function sidebar(parent, active, height) {
    const w = 264;
    const b = board(parent, "sidebar", 0, 0, w, height, "white");
    rect(b, "sidebar edge", 263, 0, 1, height, "line.soft");
    text(b, "sidebar mark", "İHKD", "wordmark", "ink.900", { x: 28, y: 28 });
    text(b, "sidebar sub", "ÜYE MASASI", "label", "red.700", { x: 28, y: 62 });
    rule(b, "sidebar rule", 28, 92, w - 56, "line.soft");
    text(b, "sidebar member", "Dr. Selin Aydın", "bodyMed", "ink.900", { x: 28, y: 116 });
    text(b, "sidebar no", "İHKD-24817 · Kardiyoloji", "data", "ink.500", { x: 28, y: 142, w: 208 });
    const items = ["Genel bakış", "Üyelik kartım", "Aidatlarım", "Kurslarım", "Bildirilerim", "Belgelerim", "Ayarlar"];
    items.forEach((it, i) => {
      const iy = 196 + i * 40;
      const on = it === active;
      if (on) rect(b, "sidebar active", 0, iy - 10, 264, 36, "red.600");
      text(b, "sidebar " + it, it, "nav", on ? "on.red" : "ink.500", { x: 28, y: iy - 4 });
    });
    rule(b, "sidebar rule 2", 28, height - 84, w - 56, "line.soft");
    text(b, "sidebar signout", "Çıkış", "nav", "ink.500", { x: 28, y: height - 60 });
    return b;
  }

  function crumbs(parent, items, x, y) {
    let cx = x;
    items.forEach((it, i) => {
      const last = i === items.length - 1;
      text(parent, "crumb " + i, it, "meta", last ? "ink.500" : "red.700", { x: cx, y: y });
      cx += Math.round(it.length * 6.6) + 6;
      if (!last) { text(parent, "crumb sep " + i, "/", "meta", "ink.500", { x: cx, y: y }); cx += 14; }
    });
    return cx;
  }

  function progress(parent, name, x, y, w, pct) {
    rect(parent, name + " track", x, y, w, 4, "line.soft");
    rect(parent, name + " fill", x, y, Math.max(4, Math.round((w * pct) / 100)), 4, "red.600");
    return y + 4;
  }

  function ecg(parent, name, x, y, w, h, tone) {
    const shape = [[0, 0.55], [0.07, 0.55], [0.09, 0.5], [0.11, 0.8], [0.13, 0.12], [0.15, 0.9], [0.18, 0.55]];
    const n = 10;
    const d = [];
    let began = false;
    for (let i = 0; i < n; i++) {
      shape.forEach(([sx, sy], k) => {
        const px = ((i + sx) * w) / n;
        const py = sy * h;
        d.push((began || k > 0 ? "L" : "M") + px.toFixed(1) + " " + py.toFixed(1));
        began = true;
      });
    }
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '"><path d="' + d.join(" ") + '" fill="none" stroke="#E0364B" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    const g = penpot.createShapeFromSvg(svg);
    g.name = nrm(name);
    parent.appendChild(g);
    g.x = OX + snap(x);
    g.y = OY + snap(y);
    const walk = (s) => {
      if (s.strokes && s.strokes.length) {
        s.strokes = [{ strokeColor: "#000000", strokeOpacity: 1, strokeStyle: "solid", strokeWidth: 1.5, strokeAlignment: "center" }];
        bind(s, tone || "red.600", ["strokeColor"]);
      }
      (s.children || []).forEach(walk);
    };
    walk(g);
    return g;
  }

  function row(parent, name, x, y, w, title, meta, opts) {
    const o = opts || {};
    const h = o.h || 96;
    text(parent, name + " title", title, o.role || "h3", "ink.900", { x: x, y: y + (o.titleOffset || 18), w: w - (o.metaW || 320) });
    if (meta) text(parent, name + " meta", meta, "data", "ink.500", { x: x + w - (o.metaW || 320), y: y + (o.metaOffset || 28), w: o.metaW || 320, align: o.metaAlign || "left" });
    if (o.action) text(parent, name + " action", o.action, "nav", "red.700", { x: x + w - 40, y: y + (o.metaOffset || 28), w: 40, align: "right" });
    rule(parent, name + " rule", x, y + h - 1, w, "line.soft");
    return y + h;
  }

  /**
   * One list, one pitch discipline. items: [{h, draw}] where h is the
   * content-derived block height (estimate with estLines, add padding,
   * snap) and draw(yRow, hRow) places the row's shapes starting at yRow.
   * The separator always lands on the block's bottom edge — callers never
   * write a manual rule y, so a rule can never drift into a text's middle.
   * In fixed-pitch mode (opts.pitch) content taller than the pitch THROWS:
   * a grid that cannot hold its content is a build error, not an overlap.
   * Center content with vcenter(hRow, estH). Returns the y below the
   * last row (gap included). Pass {rule: false} (or {bare: true}) for a
   * rule-less list: uniform pitch carries the rhythm, not separators.
   */
  function rows(parent, name, x, y, w, items, opts) {
    const o = opts || {};
    const wantRule = !o.bare && o.rule !== false;
    let cy = y;
    items.forEach((it, i) => {
      let h = it.h;
      if (o.pitch) {
        if (it.h > o.pitch + 1) {
          throw new Error("rows: " + name + " row " + i + " needs " + Math.round(it.h) +
            "px in a fixed " + o.pitch + "px pitch — shorten the copy or grow the pitch");
        }
        h = o.pitch;
      }
      it.draw(snap(cy), snap(h));
      if (wantRule && (i < items.length - 1 || o.trailing)) rule(parent, name + " rule " + i, x, snap(cy) + snap(h) - 1, w, o.rule || "line.soft");
      cy = snap(cy + h + (o.gap || 0));
    });
    return cy;
  }

  /**
   * One bullet list, one alignment. The dot's centre sits on the first line's
   * cap centre — the ink is centred in its line box, so the centre is
   * `lineBox / 2` below the box top, not "row + 6" — and an optional
   * separator lands on the block's bottom edge with the same air above it as
   * below. Hand-placed dots sat 2-4px high and hand-written rule y landed 3px
   * above the next line (İHKD 05). Items are strings, or {text, sub} for a
   * title+note feature cell; the block height comes from estLines, and `pad`
   * keeps an existing pitch when a list migrates (h = 2*pad + lines*lb).
   * Returns the y below the last row, like rows().
   */
  function bullets(parent, name, x, y, w, items, opts) {
    const o = opts || {};
    const role = o.role || "body";
    const subRole = o.subRole || "meta";
    const r = ROLE[role], sr = ROLE[subRole];
    const pad = o.pad === undefined ? 6 : o.pad;
    const textX = o.textX === undefined ? 20 : o.textX;
    const textW = w - textX;
    const lb = r.size * r.lh, slb = sr.size * sr.lh;
    const dot = o.dot || 6;
    return rows(parent, name, x, y, w, items.map((it, i) => {
      const main = typeof it === "string" ? it : it.text;
      const sub = typeof it === "string" ? null : it.sub;
      const lines = estLines(main, textW, r.size, r.font === "mono");
      const subLines = sub ? estLines(sub, textW, sr.size, sr.font === "mono") : 0;
      return {
        h: Math.ceil((2 * pad + lines * lb + (sub ? 4 + subLines * slb : 0)) / 4) * 4,
        draw(yRow) {
          const ty = snap(yRow + pad);
          rect(parent, name + " dot " + i, x, ty + lb / 2 - dot / 2, dot, dot,
            o.color || "red.600", { raw: true });
          text(parent, name + " item " + i, main, role, o.ink || "ink.700",
            { x: x + textX, y: yRow + pad, w: textW });
          if (sub) text(parent, name + " sub " + i, sub, subRole, o.subInk || "ink.600",
            { x: x + textX, y: yRow + pad + lines * lb + 4, w: textW });
        },
      };
    }), { rule: o.rule === undefined ? false : o.rule, bare: o.bare });
  }

  /**
   * Proof strip: the figures a page is making a claim with, at the `stat` role
   * and divided on the section grid. Cells are whole 12-column groups, so a
   * divider lands on a cell boundary and every figure keeps the same 12px
   * inset on both sides of it (a divider parked at "column minus a guess"
   * drifts with digit width and reads accidental). Height is its own rhythm —
   * pad / value / gap / label / pad — never the neighbouring section's.
   * `opts.bleed` paints a full-width surface behind the cells (a white strip
   * on the paper canvas); returns the strip's bottom y.
   */
  function statsStrip(parent, name, x, y, w, items, opts) {
    const o = opts || {};
    const n = items.length;
    const gutter = o.gutter === undefined ? 24 : o.gutter;
    const pitch = (w + gutter) / n;
    const cellW = pitch - gutter;
    const pad = o.pad === undefined ? 28 : o.pad;
    const vH = Math.round(ROLE.stat.size * ROLE.stat.lh);
    const lH = Math.round(ROLE.meta.size * ROLE.meta.lh);
    const gap = o.gap === undefined ? 10 : o.gap;
    const h = pad + vH + gap + lH + pad;
    if (o.bleed) rect(parent, name + " surface", 0, y, o.bleed, h, o.surface || "white");
    if (o.rule !== false) rule(parent, name + " rule", x, y, w, o.rule || "line.soft");
    items.forEach((it, i) => {
      const cx = x + i * pitch;
      if (i && o.divide !== false) rect(parent, name + " div " + i, cx - gutter / 2, y + pad, 1, vH + gap + lH, "line.soft");
      text(parent, name + " value " + i, it[0], "stat", o.valueInk || "ink.900", { x: cx, y: y + pad });
      text(parent, name + " label " + i, it[1], "meta", o.labelInk || "ink.600", { x: cx, y: y + pad + vH + gap, w: cellW });
    });
    return y + h;
  }

  /**
   * One CTA group: the button and its ghost link share a single vertical
   * centre and one fixed gap, so the link can never float above the button
   * (İHKD 01: "Programı gör" sat 50px above "Kayıt ol"). The button sizes
   * itself from its label; returns {w, h} so the caller can ride a cursor.
   */
  function ctaRow(parent, name, x, y, label, opts) {
    const o = opts || {};
    const h = o.h || 52;
    const bw = o.w || Math.max(168, Math.round(label.length * 8.2) + 64);
    const gap = o.gap === undefined ? 32 : o.gap;
    btn(parent, name, label, x, y, bw, h, o.kind || "primary");
    if (!o.link) return { w: bw, h: h };
    const lh = Math.round(ROLE.nav.size * ROLE.nav.lh);
    const lw = Math.round(o.link.length * 8.2) + 2;
    link(parent, name + " link", o.link, x + bw + gap, y + Math.round((h - lh) / 2), o.linkInk || "red.700");
    return { w: bw + gap + lw, h: h };
  }

  /**
   * Section head with the order numeral on the kicker's own line, in mono at
   * the figure size. A 44px sans numeral beside a 44px title reads as a second
   * headline (İHKD 01, 2026-11-02); bound to its kicker it is wayfinding
   * again, and the title can start on the page's left edge. Same rhythm as
   * head(): title, rule, `next` below the rule.
   */
  function headIndex(parent, x, y, label, title, opts) {
    const o = opts || {};
    NUM += 1;
    const num = o.num || ("0" + NUM).slice(-2);
    text(parent, "head num " + num, num, "figure", "ink.400", { x: x, y: y });
    text(parent, "head label " + label, label, "label", "ink.500", { x: x + 52, y: y + 4 });
    if (o.link) link(parent, "head link " + label, o.link, X + CW - 40 - Math.round(o.link.length * 8.2), y + 8, "ink.900");
    text(parent, "head title " + label, title, "h2", "ink.900", { x: x, y: y + 44, w: o.w || 760 });
    rule(parent, "head rule " + label, x, y + (o.ruleAt || 108), CW, "line.strong", 1);
    return y + (o.next || 148);
  }

  const vcenter = (hRow, contentH) => Math.max(0, Math.round((hRow - contentH) / 2));

  /**
   * Resizes texts to their measured ink. `boardName` scopes the pass to one
   * board: a build only moved that board, and fitting every board on the page
   * costs the other screens' geometry for nothing.
   */
  function fit(pageName, boardName) {
    const p = page(pageName);
    const roots = boardName
      ? (p.root.children || []).filter((b) => b.name === boardName)
      : (p.root.children || []);
    let n = 0;
    const walk = (s) => {
      if (s.type === "text" && s.textBounds && s.textBounds.height) {
        const b = s.textBounds;
        if (s.growType === "auto-width") {
          const w = Math.ceil(b.width) + 2;
          const h = Math.ceil(b.height) + 2;
          if (Math.abs(s.width - w) > 1 || Math.abs(s.height - h) > 1) { s.resize(w, h); n++; }
        } else {
          const h = Math.ceil(b.height) + 2;
          if (Math.abs(s.height - h) > 1) { s.resize(s.width, h); n++; }
        }
      }
      n += fitLink(s);
      (s.children || []).forEach(walk);
    };
    roots.forEach(walk);
    return n;
  }

  function end(name) { return { board: name, warnings: warnings.slice(0, 20), gaps: gaps.slice(0, 20) }; }

  /**
   * Post-fit pass: thin accent bars ("<base> bar <i>") resize to the measured
   * ink union of their "<base> title <i>" / "<base> meta <i>" siblings.
   * Bars are drawn from estimates; ink is truth. A bar that cannot find its
   * texts is left alone (naming, not geometry, is wrong there).
   */
  function fitBars(pageName, boardName) {
    const p = page(pageName);
    const roots = boardName
      ? (p.root.children || []).filter((b) => b.name === boardName)
      : (p.root.children || []);
    let n = 0;
    const walk = (s) => {
      (s.children || []).forEach(walk);
      const m = s.type === "rectangle" && s.width <= 3 ? s.name.match(/^(.*) bar (\d+)$/) : null;
      if (!m || !s.parent) return;
      const texts = (s.parent.children || []).filter((c) =>
        c.type === "text" && (c.name === m[1] + " title " + m[2] || c.name === m[1] + " meta " + m[2]) &&
        c.textBounds && c.textBounds.height);
      if (!texts.length) return;
      const top = Math.min(...texts.map((t) => t.textBounds.y));
      const bot = Math.max(...texts.map((t) => t.textBounds.y + t.textBounds.height));
      const h = Math.ceil(bot - top) + 2;
      const y = Math.floor(top) - 1;
      if (Math.abs(s.height - h) > 1 || Math.abs(s.y - y) > 1) {
        s.resize(s.width, h);
        s.y = y;
        n++;
      }
    };
    roots.forEach(walk);
    return n;
  }

  /**
   * Post-fit pass: a card seeded from estimated line counts settles on its
   * measured ink. Only boards named "<base> card <i>" are touched (the
   * schedule's session cards): height = ink bottom − card top + pad, up to
   * 4px. The row pitch keeps its estimate, so the air a conservative
   * estimate leaves behind falls OUTSIDE the card, never inside it.
   *
   * A card that carries a "<base> title <i>" and a "<base> meta <i>" gets its
   * meta re-settled on the title's measured ink first: the build places it
   * from an estimated line count, and a character model cannot tell where a
   * title wraps, so two one-line titles carried 24px of slack (İHKD 07 sess
   * card 2/8: 128px card and a 40px joint while the row's cards read 104/16).
   * The joint is 14 = a 16px ink gap after the 2px ink offset inside the box.
   * The accent bar keeps its padding when the card shrinks.
   */
  function fitCards(pageName, boardName, pad) {
    const p = page(pageName), gap = pad === undefined ? 14 : pad;
    const roots = boardName
      ? (p.root.children || []).filter((b) => b.name === boardName)
      : (p.root.children || []);
    let n = 0;
    const walk = (s) => {
      (s.children || []).forEach(walk);
      if (s.type !== "board" || !/ card \d+$/.test(s.name)) return;
      const texts = (s.children || []).filter((c) => c.type === "text" && c.textBounds && c.textBounds.height);
      if (!texts.length) return;
      const title = texts.filter((t) => / title \d+$/.test(t.name))[0];
      const meta = texts.filter((t) => / meta \d+$/.test(t.name))[0];
      let metaBottom = 0;
      if (title && meta) {
        const want = Math.round((title.textBounds.y + title.textBounds.height + 14) / 4) * 4;
        if (Math.abs(meta.y - want) > 1) {
          const offset = meta.textBounds.y - meta.y;   // ink offset inside the box
          const mh = meta.textBounds.height;
          meta.y = want;
          metaBottom = want + offset + mh;
          n++;
        }
      }
      const rest = texts.filter((t) => t !== meta);
      const restBottom = rest.length ? Math.max(...rest.map((t) => t.textBounds.y + t.textBounds.height)) : 0;
      const movedBottom = metaBottom || (meta ? meta.textBounds.y + meta.textBounds.height : 0);
      const bottom = Math.max(restBottom, movedBottom);
      const h = Math.ceil((bottom - s.y + gap) / 4) * 4;
      if (Math.abs(s.height - h) > 1) {
        const dh = s.height - h;
        (s.children || []).filter((c) => c.type === "rectangle" && / bar \d+$/.test(c.name))
          .forEach((b) => { if (b.height - dh > 8) b.resize(b.width, b.height - dh); });
        s.resize(s.width, h);
        n++;
      }
    };
    roots.forEach(walk);
    return n;
  }

  /**
   * Canvas spacing after a rebuild. A board that changes height leaves its
   * followers where they were: 06-kongre grew past 07-program and 07 past
   * 08-bildiri (08 hovered at y7220 over 07's bottom 7336 — 116px of overlap,
   * 2026-11-03). Screen scripts own their board's contents, never the canvas,
   * so the runner calls this once the final height has settled: walk the
   * rebuilt board's vertical column (same x, top-level boards only), keep their
   * order, and move only the boards that would sit closer than `gap` to the
   * board above. Positions that already clear the gap stay untouched (a large
   * intentional gap is never compacted), and a board in another column is never
   * considered. Moving a board translates its children (verified live: a +300
   * board move shifted a child by exactly 300), so ids, sizes, interactions and
   * relative geometry survive a pure translation.
   */
  function reflowColumn(pageName, boardName, gap) {
    const p = page(pageName);
    const g = gap === undefined ? 240 : gap;
    const all = (p.root.children || []).filter((b) => b.type === "board");
    const target = all.filter((b) => b.name === boardName)[0];
    if (!target) return { gap: g, moves: [], error: "board not found: " + boardName };
    const column = all.filter((b) => Math.abs(b.x - target.x) < 1).sort((a, b) => a.y - b.y);
    const moves = [];
    let bottom = null;
    column.forEach((b) => {
      if (bottom !== null) {
        const want = snap(bottom + g);
        if (b.y < want - 0.5) {
          const from = b.y;
          b.y = want;
          moves.push({ name: b.name, from: Math.round(from), to: Math.round(want) });
        }
      }
      bottom = b.y + b.height;
    });
    return { gap: g, moves: moves };
  }

  function report(pageName) {
    return page(pageName).root.children.map((b) => ({ name: b.name, x: b.x, y: b.y, w: b.width, h: b.height, children: (b.children || []).length }));
  }

  /** Bumped when this file changes: build.py re-sends it only on a mismatch. */
  const VERSION = "1.2.3";

  return {
    SET, W, X, CW, ROLE, FONT, warnings, gaps, VERSION, HELPERS: H.version,
    start, end, fit, fitBars, fitCards, reflowColumn, report, page, rect, board, text, rule, vrule, bind, paint, stroke, corners,
    btn, link, tag, head, pageHead, stat, field, photo, sheet, masthead, footer, sidebar, crumbs,
    progress, ecg, row, rows, bullets, vcenter, snap, nrm, token, estLines,
    statsStrip, ctaRow, headIndex,
    chips,
  };
})();

// build.py polls fit without re-sending these 15 KB: keep the library in the
// plugin's storage and refuse it when the helpers behind it changed.
storage.IK = IK;
storage.IK_VERSION = IK.VERSION;
storage.IK_HELPERS = IK.HELPERS;
