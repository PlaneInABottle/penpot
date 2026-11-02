/**
 * 07-program-loading — bilimsel programın yüklenme durumu (Kongre, 1440).
 *
 *   python3 design/ihkd/build/build.py screen-state-07
 *
 * Kabuk yüklenmiş, veri gelmemiş: gün sekmeleri ve salon filtresi gerçek (şablon
 * onlardan gelir), oturum yerleri düz gri blok. Shimmer yok — hareket bir
 * durumdur, ekran görüntüsünde kanıtlanamaz; blok kendi boyunu söyler.
 * Metin içermeyen bloğa yazı girmez, böylece yükleme durumu oturum iddia etmez.
 */
const S = IK;
const pb = S.start("Kongre", "07-program-loading", 1300);

S.masthead(pb, "Kongre");
S.text(pb, "p label", "BİLİMSEL PROGRAM", "label", "ink.500", { x: 120, y: 156 });
S.text(pb, "p title", "22–25 Nisan 2027", "h2", "ink.900", { x: 120, y: 188, w: 700 });
S.text(pb, "p note", "Son güncelleme 12 Mart 2027 · program yükleniyor", "meta", "ink.500",
  { x: 760, y: 220, w: 560, align: "right" });
S.rule(pb, "p rule", 120, 260, 1200, "line.strong", 2);

/* -------------------------------------------------------------- gün sekmeleri */
const days = [["21", "Nisan"], ["22", "Nisan"], ["23", "Nisan"], ["24", "Nisan"], ["25", "Nisan"]];
let dx = 120;
days.forEach((d, i) => {
  const on = i === 1;
  const b = S.board(pb, "day " + i, dx, 292, 168, 64, on ? "red.600" : "white");
  if (!on) S.stroke(b, "line.strong", 1);
  S.text(b, "day num " + i, d[0], "dataLg", on ? "on.red" : "ink.900", { x: dx + 16, y: 304 });
  const mon = S.text(b, "day month " + i, d[1], "meta", on ? "on.red" : "ink.500", { x: dx + 56, y: 308 });
  mon.y -= 2;
  dx += 176;
});

/* ---------------------------------------------------------------- filtre şeridi */
const cw = (s) => Math.round(s.length * 8.6) + 32;
let fx = 120;
["Tüm salonlar", "Salon A", "Salon B", "Salon C", "Salon D"].forEach((f, i) => {
  const w = cw(f);
  const b = S.board(pb, "hall " + i, fx, 380, w, 32, i === 0 ? "red.050" : "white");
  if (i !== 0) S.stroke(b, "line.soft", 1);
  S.text(b, "hall text " + i, f, "label", i === 0 ? "red.700" : "ink.600", { x: fx + 14, y: 388 });
  fx += w + 6;
});

/* -------------------------------------------------------------------- iskelet */
const HALLS = ["SALON A", "SALON B", "SALON C", "SALON D"];
const HX = [240, 512, 784, 1056];
const HW = 240, ROW = 92, BLOCK_H = 72, TOP = 476, ROWS = 8;

S.text(pb, "th time", "SAAT", "label", "ink.500", { x: 120, y: 448 });
HALLS.forEach((h, i) => S.text(pb, "th hall " + i, h, "label", "ink.500", { x: HX[i], y: 448 }));
S.rule(pb, "th rule", 120, 472, 1200, "line.strong", 1);

for (let r = 0; r < ROWS; r += 1) {
  const ry = TOP + r * ROW;
  S.rect(pb, "skeleton time " + r, 120, ry + 12, 48, 16, "surface.alt");
  for (let h = 0; h < HX.length; h += 1) {
    S.rect(pb, "skeleton card " + r + "." + h, HX[h], ry + 8, HW, BLOCK_H, "surface.alt");
  }
}

let y = TOP + ROWS * ROW + 40;
S.text(pb, "load note", "Oturumlar yükleniyor; gün sekmeleri ve salon filtresi hazır.", "meta", "ink.500",
  { x: 120, y: y, w: S.CW });
y += 48;

pb.resize(S.W, S.snap(y));

return JSON.stringify(S.end("07-program-loading"));
