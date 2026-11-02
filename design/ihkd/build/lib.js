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
    const set = penpot.library.local.tokens.sets.filter((s) => s.name === SET)[0];
    return set ? set.tokens.filter((t) => t.name === name)[0] || null : null;
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
    r.x = OX + snap(x);
    r.y = OY + snap(y);
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

  function link(parent, name, label, x, y, colorToken) {
    const t = text(parent, name, label, "nav", colorToken || "red.700", { x: x, y: y });
    const w = Math.round(label.length * 8.2) + 2;
    rect(parent, name + " under", x, y + 24, w, 1, colorToken || "red.700");
    return t;
  }

  function tag(parent, name, label, x, y, colorToken) {
    rect(parent, name + " dot", x, y + 5, 8, 8, colorToken || "red.600");
    text(parent, name, label, "label", colorToken || "ink.600", { x: x + 16, y: y });
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

  function masthead(parent, active) {
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
    btn(parent, "masthead cta", "Üye ol", X + CW - 136, 22, 136, 40, "primary");
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

  function fit(pageName) {
    const p = page(pageName);
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
      (s.children || []).forEach(walk);
    };
    (p.root.children || []).forEach(walk);
    return n;
  }

  function end(name) { return { board: name, warnings: warnings.slice(0, 20), gaps: gaps.slice(0, 20) }; }

  function report(pageName) {
    return page(pageName).root.children.map((b) => ({ name: b.name, x: b.x, y: b.y, w: b.width, h: b.height, children: (b.children || []).length }));
  }

  return {
    SET, W, X, CW, ROLE, FONT, warnings, gaps,
    start, end, fit, report, page, rect, board, text, rule, vrule, bind, paint, stroke, corners,
    btn, link, tag, head, pageHead, stat, field, photo, sheet, masthead, footer, sidebar, crumbs,
    progress, ecg, row, snap, nrm, token, estLines,
  };
})();
