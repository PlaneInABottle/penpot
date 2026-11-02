/**
 * 15 — Haberler ve duyurular. Featured story with photo, six list rows, a bulletin band
 * with an email field, pagination.
 */
const S = IK;
const pb = S.start("İçerik", "15-haberler", 2080);

S.masthead(pb, "Haberler");
S.pageHead(pb, "HABERLER", "Duyurular ve haberler", "Kongre, akademi ve dernekten haftanın duyuruları.", { ruleY: 352, next: 412 });

let fx = 120;
["Tümü", "Kongre", "Akademi", "Dernek", "Kılavuz", "Basın"].forEach((f, i) => {
  const w = Math.round(f.length * 8.6) + 32;
  const b = S.board(pb, "f " + i, fx, 380, w, 34, i === 0 ? "red.600" : "white");
  if (i) S.stroke(b, "line.strong", 1);
  S.text(b, "f text " + i, f, "label", i === 0 ? "on.red" : "ink.700", { x: fx + 16, y: 389 });
  fx += w + 8;
});

/* ------------------------------------------------------------------ öne çıkan */
S.photo(pb, "img-round", 120, 452, 700, 400, "İç hastalıkları servisi, Ankara");
S.text(pb, "f label", "ÖNE ÇIKAN · 12 MART 2027", "label", "red.600", { x: 860, y: 452 });
S.text(pb, "f title", "Kongre programı yayınlandı: 96 oturum, dört salon", "h3", "ink.900", { x: 860, y: 480, w: 460 });
S.text(pb, "f lede", "Program yayında: 96 oturum, dört salon, konsey oturumlarıyla.", "body", "ink.600", { x: 860, y: 600, w: 460 });
S.text(pb, "f meta", "6 dk okuma · Kongre", "meta", "ink.500", { x: 860, y: 720 });
S.link(pb, "f cta", "Haberi oku", 860, 760, "ink.900");

/* -------------------------------------------------------------------- liste */
S.text(pb, "l h1", "TARİH", "label", "ink.500", { x: 120, y: 920 });
S.text(pb, "l h2", "KATEGORİ", "label", "ink.500", { x: 260, y: 920 });
S.rule(pb, "l rule", 120, 944, 1200, "ink.900", 1);
const news = [
  ["4 Mart 2027", "Akademi", "Kalp yetersizliği kursu için kayıtlar açıldı", "2 dk"],
  ["26 Şubat 2027", "Dernek", "Çalışma grubu başkanları belirlendi", "4 dk"],
  ["18 Şubat 2027", "Kılavuz", "Hipertansiyon kılavuzu 2027 taslağı görüşe açıldı", "5 dk"],
  ["9 Şubat 2027", "Basın", "Kardiyovasküler ölümlerde bölgesel fark raporu", "6 dk"],
  ["2 Şubat 2027", "Kongre", "Bildiri gönderimi için son iki hafta", "2 dk"],
  ["21 Ocak 2027", "Akademi", "STE kredileri e-Devlet'e işlendi", "3 dk"],
];
news.forEach((n, i) => {
  const ny = 976 + i * 68;
  S.text(pb, "nw date " + i, n[0], "data", "ink.500", { x: 120, y: ny + 2 });
  S.text(pb, "nw cat " + i, n[1], "label", "red.700", { x: 260, y: ny + 2 });
  S.text(pb, "nw title " + i, n[2], "bodyMed", "ink.900", { x: 420, y: ny - 2, w: 700 });
  S.text(pb, "nw time " + i, n[3], "data", "ink.500", { x: 1200, y: ny + 2, w: 120, align: "right" });
  S.rule(pb, "nw rule " + i, 120, ny + 48, 1200, "line.soft");
});

/* -------------------------------------------------------------------- bülten */
// legibility: measured ink ends at rel 1560 (CTA bottom; estLines
// overestimates Turkish copy by ~1 line, so this height is frozen from
// measurement — the dead-space lint flags any future drift)
const y = 1424;
const bulBottom = 1560 + 24;
const bul = S.board(pb, "bulletin", 0, y, 1440, S.snap(bulBottom - y), "white");
S.text(bul, "bul label", "BÜLTEN", "label", "red.700", { x: 120, y: y + 40 });
S.text(bul, "bul title", "Ayda bir, yalnızca üyelere", "h3", "ink.900", { x: 120, y: y + 68, w: 520 });
S.text(bul, "bul body", "Kongre takvimi, yeni kılavuzlar ve STE kursları. Abonelikten tek tıkla çıkılır.", "body", "ink.600", { x: 120, y: y + 112, w: 520 });
S.field(bul, "bul email", "E-POSTA", "ad.soyad@kurum.edu.tr", 720, y + 60, 400, { placeholder: true });
S.btn(bul, "bul cta", "Abone ol", 1140, y + 84, 180, 52, "primary");

/* -------------------------------------------------------------------- sayfalama */
const pgY = S.snap(bulBottom + 44);
S.text(pb, "page", "1 / 14", "data", "ink.500", { x: 120, y: pgY });
S.text(pb, "page next", "Sonraki →", "nav", "red.600", { x: 1140, y: pgY - 2, w: 180, align: "right" });

S.footer(pb, S.snap(bulBottom + 116));

return JSON.stringify(S.end("15-haberler"));
