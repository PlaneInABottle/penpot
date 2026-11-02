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
 *     "hero ghost" @ 01-ana-sayfa (Derneği tanı) -> 02-dernek
 *     "board all" @ 02-dernek (Tüm kurullar)     -> 03-yonetim
 *   kayıt (Kongre, start 09-kayit):
 *     "k cta" @ 09-kayit (Kaydı tamamla)         -> 10-konaklama
 *   kurs (Akademi, start 11-akademi):
 *     "f cta" @ 11-akademi (Devam et)            -> 12-kurs-detay
 *   oku (İçerik, start 15-haberler):
 *     "f cta" @ 15-haberler (Haberi oku)         -> 16-makale
 *   üye (Üyelik, start 19-giris):
 *     "f submit" @ 19-giris (Giriş yap)          -> 20-panel
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
  if (names.indexOf(name) === -1) pg.createFlow(name, start);
};
const links = [];
const errors = [];
const wire = (label, shapeName, srcBoard, destBoard) => {
  const s = need(kid(srcBoard, shapeName), "shape " + shapeName);
  const r = H.link(s, "click", NAV(destBoard));
  links.push(label + " -> " + destBoard.name + " (replaced " + r.replaced + ")");
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
  // "Üye ol" is the membership journey (cross-page, unwired by design); the
  // same-page route off 01 is the ghost link "Derneği tanı" -> 02-dernek.
  wire("01 hero ghost", "hero ghost", b01, b02);
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
return JSON.stringify({ links: links, errors: errors });
