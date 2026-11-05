/**
 * 01-m menu — the open menu state of the mobile home (390×844, paper).
 *
 *   python3 design/ihkd/build/build.py screen-state-01-m
 *
 * A state board, not a second home: it carries the same top bar and mark, the
 * menu control flips to `KAPAT` in the same 60×44 slot, and the six routes are
 * 72px rows from 96 — one tap target per destination. The account pair and the
 * congress date sit under a 552 rule; the imprint closes the sheet.
 *
 * Flow (flows.js): home "masthead menu" → this board; this board "menu close"
 * → home; flow `menü` starts on the home board.
 */
const S = IK;
const M = S.M;

const X = M.X, CW = M.CW, W = M.W;
const ROWS = ["Dernek", "Çalışma grupları", "Kongre", "Akademi", "Yayın", "Haberler"];
const ROW_H = 72, ROW_TOP = 96;
const IMPRINT = "İHKD · İç Hastalıkları ve Kardiyoloji Derneği · 1998'den beri Ankara";

const pb = M.start("Mobil", "01-ana-sayfa-m-menu", 844);

/* the closed masthead's lockup, with the menu control flipped to KAPAT */
S.rect(pb, "top bar", 0, 0, W, 4, "red.600");
M.textM(pb, "masthead mark", "İHKD", "wordmark", "ink.900", { x: X, y: 16 });
M.textM(pb, "masthead sub", "ÜYE PLATFORMU", "label", "ink.500", { x: 91, y: 20 });
const close = S.board(pb, "menu close", 310, 10, 60, 44);
M.textM(close, "menu close label", "KAPAT", "label", "ink.900",
  { x: 310, y: 24, w: 60, align: "right" });

/* six routes, one 72px row each, the hairline on the row's bottom edge */
ROWS.forEach((label, i) => {
  const ry = ROW_TOP + i * ROW_H;
  M.textM(pb, "menu nav " + i, label, "nav", "ink.900", { x: X, y: ry + 25, w: CW });
  S.rule(pb, "menu nav rule " + i, X, ry + ROW_H - 1, CW, "line.soft", 1);
});

/* the account block is not a route: the hairline under `Haberler` already
   separates the list from it, so the login row follows on the same rhythm */
M.textM(pb, "menu signin", "Üye girişi", "nav", "ink.900", { x: X, y: 568 + 11, w: CW });
S.btn(pb, "menu join", "Üye ol", X, 624, CW, 48, "ghost");
M.textM(pb, "menu date", "22–25 Nisan 2027", "body", "ink.700", { x: X, y: 720, w: CW });
M.textM(pb, "menu imprint", IMPRINT, "label", "ink.500", { x: X, y: 792, w: CW });

pb.resize(W, 844);

return JSON.stringify(S.end("01-ana-sayfa-m-menu"));
