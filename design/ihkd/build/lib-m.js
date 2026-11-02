/**
 * İHKD mobil 390 kütüphanesi — `lib-m.js`.
 *
 *   python3 design/ihkd/build/build.py screen-m01
 *
 * build.py bu dosyayı `lib.js`den SONRA enjekte eder; dosya yoksa enjeksiyon
 * hiçbir şey değiştirmez. `lib.js` DEĞİŞTİRİLMEZ: burada yalnız onun atomları
 * (S = IK) çağrılır ve 390 tahtasına ölçeklenmiş bloklar kurulur.
 *
 * Geometri tek kaynaktan: tahta 390 · kenar 16 · içerik 358 · bölüm aralığı 56
 * (masaüstü 112'nin tek kolon karşılığı). 390 - 2*16 = 358 dörde bölünmediği
 * için `S.board`un 4px snap'i tam genişlikli bloklarda geri alınır (`exact`):
 * içerik her zaman 16..374 arasında kalır, iki kenar boşluğu eşittir.
 *
 * Dokunma hedefi 44px (`M.TOUCH`), gövde metni 16px, yalnız meta/etiket 13px.
 * Görsel dil: hasta/muayene/steteskop fotoğrafı YOK. Figür kendi vektörümüzdür
 * (`plate`, `trace`): EKG trace + kalibrasyon + ölçüm satırı.
 */
const IKM = (function () {
  const S = IK;
  const W = 390;
  const G = 16;
  const CW = W - 2 * G;          // 358
  const TOUCH = 44;              // en küçük dokunma hedefi
  const BTN_H = 52;
  const SECTION = 56;

  /** `S.board` genişliği 4px'e snap'ler; 358 snap'lenince sağ boşluk 2px kayar. */
  const exact = (b, w, h) => {
    if (Math.abs(b.width - w) > 0.5 || Math.abs(b.height - (h || b.height)) > 0.5) b.resize(w, h || b.height);
    return b;
  };

  /** 390 tahtası: S.start 1440 kurar, burada genişlik 390'a iner. */
  function start(pageName, boardName, height) {
    const b = S.start(pageName, boardName, height);
    b.resize(W, S.snap(height));
    return b;
  }

  /* ------------------------------------------------------------------ masthead */
  /** Hamburger + wordmark. Masthead CTA'sı yok: mobilde eylem gövdelerin içinde. */
  function masthead(pb) {
    S.rect(pb, "top bar", 0, 0, W, 4, "red.600");
    S.text(pb, "masthead mark", "İHKD", "wordmark", "ink.900", { x: G, y: 22 });
    const hb = S.board(pb, "masthead menu", W - G - TOUCH, 14, TOUCH, TOUCH);
    exact(hb, 44, 44);
    [0, 1, 2].forEach((i) => S.rect(hb, "masthead menu bar " + i, W - G - 22, 25 + i * 7, 22, 2, "ink.900"));
    S.rule(pb, "masthead rule", 0, 66, W, "line.soft");
    return 90;
  }

  /* -------------------------------------------------------------------- blocks */
  /** Bölüm başlığı: etiket + h3 + kural. Bağlantı satır sonunda, etiketin yanında değil. */
  function sectionHead(pb, y, label, title, opts) {
    const o = opts || {};
    const role = o.role || "h3";
    const r = S.ROLE[role];
    const lines = S.estLines(title, CW, r.size, r.font === "mono");
    S.text(pb, "head label " + label, label, "label", "ink.500", { x: G, y: y });
    S.text(pb, "head title " + label, title, role, "ink.900", { x: G, y: y + 20, w: CW });
    const ruleY = y + 20 + Math.ceil(lines * r.size * r.lh) + 16;
    S.rule(pb, "head rule " + label, G, ruleY, CW, "line.strong", 1);
    return ruleY + 28;
  }

  function card(pb, name, x, y, w, h, fill) {
    const b = S.board(pb, name, x, y, w, h, fill || "white");
    exact(b, w, S.snap(h));
    S.stroke(b, "line.soft", 1);
    return b;
  }

  /** Tam genişlik buton; dönüş: altındaki y. Dokunma hedefi 52 (>=44). */
  function btn(pb, name, label, y, opts) {
    const o = opts || {};
    const w = o.w || CW;
    const x = o.x === undefined ? G : o.x;
    const h = o.h || BTN_H;
    const b = S.btn(pb, name, label, x, y, w, h, o.kind || "primary");
    exact(b, w, h);
    return y + h;
  }

  /** Form alanı: 52px çizgi + opsiyonel hata ipucu. Dönüş: sonraki alanın y'si. */
  function field(pb, name, label, value, y, opts) {
    const o = opts || {};
    const x = o.x === undefined ? G : o.x;
    const w = o.w || CW;
    S.field(pb, name, label, value, x, y, w, o);
    return y + (o.hint ? 92 : 72);
  }

  /**
   * Bilimsel figür plakası — ürünün kendi görsel dili: 5 mm ızgara, 1 mV
   * kalibrasyon karesi, tek derivasyon trace ve ölçüm satırı. Fotoğraf değil,
   * kendi ürettiğimiz vektör; hasta/muayene sahnesi yok.
   */
  function plate(pb, name, x, y, w, h, opts) {
    const o = opts || {};
    if (h < 232) throw new Error("plate " + name + ": " + h + "px, en az 232px gerekir");
    const b = S.board(pb, name, x, y, w, h, "white");
    exact(b, w, S.snap(h));
    S.stroke(b, "line.soft", 1);
    const pad = 16;
    const iw = w - 2 * pad;
    S.text(b, name + " label", o.label || "EKG · II. DERİVASYON · 25 mm/s", "label", "ink.500", { x: x + pad, y: y + 20 });
    for (let gx = pad; gx <= w - pad; gx += 24) S.rect(b, name + " grid v" + gx, x + gx, y + 56, 1, 96, "line.soft");
    for (let gy = 56; gy <= 152; gy += 16) S.rect(b, name + " grid h" + gy, x + pad, y + gy, iw, 1, "line.soft");
    /* kalibrasyon: 1 mV / 10 mm kare (yüksel, git, in) */
    S.rect(b, name + " cal 0", x + pad, y + 96, 24, 2, "red.600");
    S.rect(b, name + " cal 1", x + pad, y + 72, 2, 24, "red.600");
    S.rect(b, name + " cal 2", x + pad, y + 72, 12, 2, "red.600");
    S.rect(b, name + " cal 3", x + pad + 10, y + 72, 2, 24, "red.600");
    S.ecg(b, name + " trace", x + pad + 28, y + 56, iw - 28, 96);
    S.text(b, name + " read", o.read || "HR 72 · PR 160 ms · QRS 92 ms · QT 400 ms", "data", "ink.700",
      { x: x + pad, y: y + 164, w: iw });
    S.text(b, name + " caption", o.caption || "Kalibrasyon 10 mm/mV · 5 mm ızgara · 25 mm/s", "meta", "ink.500",
      { x: x + pad, y: y + 192, w: iw });
    return y + h;
  }

  /** Kompakt trace kartı (yayın bölümü): 104px, tek satır ölçüm notu. */
  function trace(pb, name, x, y, w) {
    const h = 104;
    const b = S.board(pb, name, x, y, w, h, "white");
    exact(b, w, h);
    S.stroke(b, "line.soft", 1);
    S.ecg(b, name + " ecg", x + 16, y + 16, w - 32, 44);
    S.text(b, name + " read", "Kalibrasyon 10 mm/mV · 25 mm/s", "meta", "ink.500", { x: x + 16, y: y + 68, w: w - 32 });
    return y + h;
  }

  /**
   * Etiket şeridi, satır kaydırmalı. Genişlik lib.chips ile aynı mono modelden
   * türetilir (0.6em + tracking), böylece pill metni kırpılmaz; 390'da tek
   * satıra sığmayan seçenek grubu alt satıra iner.
   */
  function chips(pb, name, items, x, y, opts) {
    const o = opts || {};
    const roleName = o.role || "label";
    const r = S.ROLE[roleName];
    if (r.font !== "mono") throw new Error("chips: role " + roleName + " is not mono, advance is not exact");
    const pad = o.pad === undefined ? 16 : o.pad;
    const gap = o.gap === undefined ? 8 : o.gap;
    const h = o.h === undefined ? TOUCH : o.h;
    const maxW = o.w === undefined ? CW : o.w;
    const advance = 0.6 * r.size + (r.track || 0);
    const box = Math.round(r.size * r.lh);
    let cx = x, cy = y, n = 0;
    items.forEach((label, i) => {
      const w = Math.ceil((Math.ceil(String(label).length * advance) + 2 * pad) / 4) * 4;
      if (w > maxW) throw new Error("chips: " + label + " (" + w + "px) does not fit " + maxW);
      if (n && cx + w > x + maxW) { cx = x; cy += h + gap; }
      const on = o.active === i;
      const b = S.board(pb, name + " " + i, cx, cy, w, h, on ? (o.onFill || "red.600") : (o.fill || "surface.alt"));
      exact(b, w, h);
      if (!on && o.stroke) S.stroke(b, o.stroke, o.strokeWidth || 1);
      S.text(b, name + " text " + i, label, roleName, on ? (o.onInk || "on.red") : (o.ink || "ink.700"),
        { x: cx + pad, y: cy + Math.round((h - box) / 2) });
      cx += w + gap;
      n += 1;
    });
    return cy + h + (o.after === undefined ? 12 : o.after);
  }

  /** 2x2 kanıt ızgarası: sütunlar 16 ve 204, hücre 170 — sağ kenar tam 374. */
  function stats(pb, name, items, y, opts) {
    const o = opts || {};
    const COL2 = 204, COLW = 170, CELL = 88, GAP = 12;
    const vH = Math.round(S.ROLE.stat.size * S.ROLE.stat.lh);
    items.forEach((it, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const cx = col ? COL2 : G;
      const ry = y + row * (CELL + GAP);
      S.text(pb, name + " value " + i, it[0], "stat", "ink.900", { x: cx, y: ry });
      S.text(pb, name + " label " + i, it[1], "meta", "ink.600", { x: cx, y: ry + vH + 4, w: COLW });
    });
    const rows = Math.ceil(items.length / 2);
    return y + rows * (CELL + GAP) + (o.after === undefined ? 12 : o.after);
  }

  /** Satır içi onay kutusu; kutu 18px, satırın dokunma hedefi 44. */
  function check(pb, name, label, y, opts) {
    const o = opts || {};
    const x = o.x === undefined ? G : o.x;
    const w = o.w || CW;
    const lines = S.estLines(label, w - 30, 16, false);
    S.rect(pb, name + " box", x, y + 14, 18, 18, o.on ? "red.600" : "white",
      { stroke: o.on ? "red.600" : "line.strong" });
    S.text(pb, name + " label", label, "body", "ink.700", { x: x + 30, y: y + 12, w: w - 30 });
    const h = Math.max(TOUCH, 12 + lines * 26 + 8);
    return y + h;
  }

  /** Tek kolon footer: mark, cümle, adres, iki link satırı, künye. */
  function footer(pb, y) {
    const h = 348;
    const b = S.board(pb, "footer", 0, y, W, h, "white");
    S.rect(b, "footer bar", 0, y, W, 2, "red.600");
    S.text(b, "footer mark", "İHKD", "wordmark", "ink.900", { x: G, y: y + 32 });
    S.text(b, "footer claim", "Hastanın hekimi.", "lead", "ink.900", { x: G, y: y + 68, w: CW });
    S.text(b, "footer address", "Meşrutiyet Cad. 24/7, 06420 Çankaya, Ankara\n+90 312 425 18 40 · info@ihkd.org.tr",
      "meta", "ink.500", { x: G, y: y + 132, w: CW });
    S.text(b, "footer links 0", "Dernek · Çalışma grupları · Kongre · Akademi", "meta", "ink.600", { x: G, y: y + 196, w: CW });
    S.text(b, "footer links 1", "Yayın · Haberler · Üyelik · İletişim", "meta", "ink.600", { x: G, y: y + 222, w: CW });
    S.rule(b, "footer rule", G, y + 272, CW, "line.soft");
    S.text(b, "footer legal", "© 2026 İHKD · KVKK · Çerez politikası", "data", "ink.500", { x: G, y: y + 292, w: CW });
    S.text(b, "footer legal 2", "Tasarım çalışması — kurum ve kişiler kurgudur.", "data", "ink.500", { x: G, y: y + 312, w: CW });
    return y + h;
  }

  /** Altına yapışan eylem çubuğu: tahtanın son yerleşik bloğu, tam genişlik buton. */
  function stickyBar(pb, y, name, label) {
    const h = 92;
    const b = S.board(pb, "sticky bar", 0, y, W, h, "white");
    S.rule(b, "sticky rule", 0, y, W, "line.soft");
    S.btn(b, name, label, G, y + 20, CW, BTN_H, "primary");
    return y + h;
  }

  return {
    W, G, CW, TOUCH, BTN_H, SECTION, ROLE: S.ROLE,
    start, masthead, sectionHead, btn, field, card,
    plate, trace, chips, stats, check, footer, stickyBar,
    rule: S.rule, text: S.text, rect: S.rect, link: S.link, board: S.board,
    stroke: S.stroke, paint: S.paint, rows: S.rows, bullets: S.bullets,
    vcenter: S.vcenter, snap: S.snap, estLines: S.estLines,
  };
})();
storage.IKM = IKM;
