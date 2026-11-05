/**
 * M8 prototype flows — İHKD. Link map only; no rebuild wiring.
 * Run: python3 scripts/penpot_exec.py --file design/ihkd/build/flows.js
 * Idempotent: H.link replaces the same trigger+action-type; flows are
 * created only when their name is absent. Verify in a LATER call
 * (Penpot commits asynchronously: reads in this call may look stale).
 *
 * Map: SAME-PAGE ONLY (cross-page navigate-to via the API stores a hollow
 * destination proxy {id:"",name:null} — verified live 2026-11-02; cross-page
 * journeys stay unwired by design):
 *   keşif (Kurumsal, start 01-ana-sayfa):
 *     "groups all" @ 01-ana-sayfa (12 çalışma grubu) -> 04-calisma-gruplari
 *     "board all" @ 02-dernek (Tüm kurullar)     -> 03-yonetim
 *   kayıt (Kongre, start 09-kayit):
 *     "k cta" @ 09-kayit (Kaydı tamamla)         -> 10-konaklama
 *   kurs (Akademi, start 11-akademi):
 *     "f cta" @ 11-akademi (Devam et)            -> 12-kurs-detay
 *   oku (İçerik, start 15-haberler):
 *     "f cta" @ 15-haberler (Haberi oku)         -> 16-makale
 *   üye (Üyelik, start 19-giris):
 *     "f submit" @ 19-giris (Giriş yap)          -> 20-panel
 *   menü (Mobil, start 01-ana-sayfa-m):
 *     "masthead menu" @ 01-ana-sayfa-m (MENÜ)    -> 01-ana-sayfa-m-menu
 *     "menu close" @ 01-ana-sayfa-m-menu (KAPAT) -> 01-ana-sayfa-m
 *
 * Hygiene: drops auto-named "Flow N" flows (null starting board, created as a
 * side effect of addInteraction) so exactly 5 flows remain.
 */
const H = storage.H;
const NAV = (dest) => ({
  type: "navigate-to",
  destination: dest,
  animation: { type: "dissolve", duration: 300, easing: "ease-out" },
});
const file = penpot.currentFile;
const page = (n) => file.pages.filter((p) => p.name === n)[0];
const board = (pg, n) => (pg.root.children || []).filter((c) => c.name === n)[0];
const kid = (b, n) => (b.children || []).filter((c) => c.name === n)[0];
const need = (v, what) => { if (!v) throw new Error("M8 missing " + what); return v; };
const ensureFlow = (pg, name, start) => {
  const names = (pg.flows || []).map((f) => f.name);
  if (names.indexOf(name) === -1) {
    try {
      pg.createFlow(name, start);
    } catch (e) {
      // Penpot 2.19 bridge: createFlow serialises the Board proxy and the
      // backend rejects it (`Value not valid … :createFlow-frame`). The
      // addInteraction calls above already created a flow that starts on the
      // wired source board — adopt and rename that one instead.
      const auto = (pg.flows || []).filter(
        (f) => f.startingBoard && f.startingBoard.name === start.name)[0];
      if (!auto) throw e;
      auto.name = name;
    }
  }
};
const links = [];
const errors = [];
const byBoard = {};
const wire = (label, shapeName, srcBoard, destBoard) => {
  const s = need(kid(srcBoard, shapeName), "shape " + shapeName);
  const r = H.link(s, "click", NAV(destBoard));
  links.push(label + " -> " + destBoard.name + " (replaced " + r.replaced + ")");
  (byBoard[srcBoard.name] = byBoard[srcBoard.name] || []).push(
    { shape: shapeName, dest: destBoard.name });
};
const section = (pageName, fn) => {
  try {
    const pg = need(page(pageName), "page " + pageName);
    penpot.openPage(pg);
    fn(pg);
  } catch (e) { errors.push(pageName + ": " + String((e && e.message) || e).slice(0, 200)); }
};

section("Kurumsal", (pg) => {
  const b01 = need(board(pg, "01-ana-sayfa"), "board 01-ana-sayfa");
  const b02 = need(board(pg, "02-dernek"), "board 02-dernek");
  const b03 = need(board(pg, "03-yonetim"), "board 03-yonetim");
  const b04 = need(board(pg, "04-calisma-gruplari"), "board 04-calisma-gruplari");
  // "Üye ol", the hero primary (Kongreye kayıt ol) and the hero ghost
  // (Programı gör) all leave the Kurumsal page, and cross-page navigation is
  // unwired by design. The same-page route off 01 is the groups link, which
  // keeps the discovery flow real: 01 -> 04 -> (05).
  wire("01 groups all", "groups all", b01, b04);
  wire("02 board all", "board all", b02, b03);
  ensureFlow(pg, "kayıt", b01);
  ensureFlow(pg, "keşif", b01);
  (pg.flows || []).filter((f) => /^Flow \d+$/.test(f.name)).forEach((f) => {
    pg.removeFlow(f);
    links.push("dropped junk flow " + f.name);
  });
});
section("Kongre", (pg) => {
  const b09 = need(board(pg, "09-kayit"), "board 09-kayit");
  const b10 = need(board(pg, "10-konaklama"), "board 10-konaklama");
  wire("09 k cta", "k cta", b09, b10);
});
section("Akademi", (pg) => {
  const b11 = need(board(pg, "11-akademi"), "board 11-akademi");
  const b12 = need(board(pg, "12-kurs-detay"), "board 12-kurs-detay");
  wire("11 f cta", "f cta", b11, b12);
});
section("İçerik", (pg) => {
  const b15 = need(board(pg, "15-haberler"), "board 15-haberler");
  const b16 = need(board(pg, "16-makale"), "board 16-makale");
  wire("15 f cta", "f cta", b15, b16);
  ensureFlow(pg, "oku", b15);
});
section("Üyelik", (pg) => {
  const b19 = need(board(pg, "19-giris"), "board 19-giris");
  const b20 = need(board(pg, "20-panel"), "board 20-panel");
  const b18 = need(board(pg, "18-uyelik"), "board 18-uyelik");
  wire("19 f submit", "f submit", b19, b20);
  wire("20 p cta", "p cta", b20, b18);
  ensureFlow(pg, "üye", b19);
});
section("Mobil", (pg) => {
  const home = need(board(pg, "01-ana-sayfa-m"), "board 01-ana-sayfa-m");
  const menu = need(board(pg, "01-ana-sayfa-m-menu"), "board 01-ana-sayfa-m-menu");
  wire("menu open", "masthead menu", home, menu);
  wire("menu close", "menu close", menu, home);
  ensureFlow(pg, "menü", home);
  (pg.flows || []).filter((f) => /^Flow \d+$/.test(f.name)).forEach((f) => {
    pg.removeFlow(f);
    links.push("dropped junk flow " + f.name);
  });
});
return JSON.stringify({ links: links, errors: errors, byBoard: byBoard });
