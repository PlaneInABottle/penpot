/**
 * 01-bos — ana sayfanın boş durumu (Kurumsal, 1440).
 *
 *   python3 design/ihkd/build/build.py screen-state-01
 *
 * `Bu hafta` gündemi boşken: masthead + boş-durum kartı (metin + tek eylem).
 * Eylem linktir, doygun buton değil — sayfada ikinci bir primary yok.
 * Fotoğraf yok: boş durum bir belge, bir sahne değil.
 */
const S = IK;
const pb = S.start("Kurumsal", "01-bos", 760);

S.masthead(pb, null, { cta: "ghost" });

const CY = 184, CH = 320;
S.text(pb, "empty label", "GÜNDEM · BU HAFTA", "label", "ink.500", { x: S.X, y: 156 });

const card = S.board(pb, "empty card", S.X, CY, S.CW, CH, "white");
S.stroke(card, "line.soft", 1);
S.text(card, "empty kicker", "YAYIMLANMIŞ GÜNDEM YOK", "label", "ink.500", { x: S.X + 48, y: CY + 48 });
S.text(card, "empty title", "Bu hafta gündem yok.", "display", "ink.900", { x: S.X + 48, y: CY + 76, w: 900 });
S.text(card, "empty body",
  "Duyurular Pazartesi 09:00'da yayımlanır. Arşivde 148 haber ve 12 çalışma grubu duyurusu var.",
  "lead", "ink.600", { x: S.X + 48, y: CY + 178, w: 760 });
S.link(card, "empty cta", "Arşivi aç →", S.X + 48, CY + 268, "red.700");
S.text(card, "empty meta", "Son yayım 4 Mart 2027.", "meta", "ink.500",
  { x: S.X + S.CW - 300, y: CY + 276, w: 252, align: "right" });

let y = CY + CH + 40;
S.text(pb, "empty note", "Veri güncellemesi her Pazartesi 09:00'da yayımlanır; bu tahta o an boş görünür.",
  "meta", "ink.500", { x: S.X, y: y, w: S.CW });
y += 48;

pb.resize(S.W, S.snap(y));

return JSON.stringify(S.end("01-bos"));
