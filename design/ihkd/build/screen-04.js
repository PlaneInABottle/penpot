/**
 * 04 — Çalışma grupları. Twelve groups as an index, not as cards.
 */
const S = IK;
const pb = S.start("Kurumsal", "04-calisma-gruplari", 2088);

S.masthead(pb, "Çalışma grupları");
let y = S.pageHead(pb, "ÇALIŞMA GRUPLARI", "On iki grup, on iki soru.",
  "Her grup bir klinik soru etrafında kurulur. Üyelik tek; katılım sınırsız.",
  { next: 420 });

/* ----------------------------------------------------------------- filtre */
const filters = ["Tümü 12", "Görüntüleme 2", "Girişimsel 2", "Ritim 2", "Metabolik 3", "Diğer 3"];
let fx = 120;
filters.forEach((f, i) => {
  const w = Math.round(f.length * 7.4) + 32;
  const b = S.board(pb, "filter " + i, fx, y, w, 36, i === 0 ? "red.600" : "white");
  if (i !== 0) S.stroke(b, "line.strong", 1);
  S.text(b, "filter text " + i, f, "label", i === 0 ? "on.red" : "ink.700", { x: fx + 16, y: y + 10 });
  fx += w + 8;
});

/* ----------------------------------------------------------------- gruplar */
y += 76;
const groups = [
  ["01", "Kardiyovasküler görüntüleme", "412", "Ekokardiyografi, BT ve MR'da standart raporlama."],
  ["02", "Kalp yetersizliği", "508", "KKY klinik yolu ve taburculuk sonrası ilk 30 gün."],
  ["03", "Aritmi ve elektrofizyoloji", "287", "Atriyal fibrilasyonda tarama ve antikoagülasyon."],
  ["04", "Kardiyometabolik", "366", "Diyabet, obezite ve kardiyovasküler risk yönetimi."],
  ["05", "Hipertansiyon", "341", "Ev ölçümü ve ofis dışı tansiyonun tanıya katılması."],
  ["06", "Geriatrik kardiyoloji", "198", "Çoklu ilaç kullanan hastada tedavi sadeleştirme."],
  ["07", "Girişimsel kardiyoloji", "455", "STEMI ağı ve hastane içi transfer süreleri."],
  ["08", "Yapısal kalp hastalıkları", "214", "TAVİ ve mitral girişimlerde hasta seçimi."],
  ["09", "Lipit ve ateroskleroz", "302", "LDL hedeflerinin gerçek yaşamda tutturulması."],
  ["10", "Tromboz ve antikoagülasyon", "176", "BKA'da kanama riski ve köprüleme kararları."],
  ["11", "Kardiyo-onkoloji", "149", "Kemoterapi öncesi kardiyak değerlendirme."],
  ["12", "Spor kardiyolojisi", "128", "Genç sporcularda tarama ve geri dönüş kararı."],
];
groups.forEach((g, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const gx = 120 + col * 620;
  const gy = y + row * 146;
  S.text(pb, "g idx " + i, g[0], "data", "ink.500", { x: gx, y: gy + 28 });
  S.text(pb, "g name " + i, g[1], "h3", "ink.900", { x: gx + 44, y: gy + 14, w: 380 });
  S.text(pb, "g count " + i, g[2] + " üye", "data", "ink.500", { x: gx + 480, y: gy + 28, w: 80, align: "right" });
  S.text(pb, "g line " + i, g[3], "body", "ink.600", { x: gx + 44, y: gy + 52, w: 440 });
  S.text(pb, "g go " + i, "Grubu gör →", "nav", "red.600", { x: gx + 44, y: gy + 84 });
  S.rule(pb, "g rule " + i, gx, gy + 134, 560, "line.soft");
});

/* --------------------------------------------------------- yeni grup önerisi */
y += 6 * 146 + 40;
const propose = S.board(pb, "propose", 120, y, 1200, 260, "white");
S.stroke(propose, "line.strong", 1);
S.text(propose, "prop label", "YENİ GRUP ÖNERİSİ", "label", "red.600", { x: 144, y: y + 40 });
S.text(propose, "prop title", "Bir soru etrafında on iki kişi varsa, grup açılır.", "h3", "ink.900", { x: 144, y: y + 72, w: 560 });
S.bullets(propose, "prop", 760, y + 72, 400, ["En az 12 dernek üyesi", "Tanımlı bir klinik soru ve iki yıllık plan", "Bilim kuruluna yazılı başvuru"], { pad: 5, textX: 20 });
S.link(propose, "prop cta", "Başvuru formu", 144, y + 196, "ink.900");

S.footer(pb, y + 356);

return JSON.stringify(S.end("04-calisma-gruplari"));
