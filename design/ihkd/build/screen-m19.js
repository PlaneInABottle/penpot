/**
 * 19 — Üye girişi, mobil 390 (`19-giris-m`, sayfa `Mobil`).
 *
 *   python3 design/ihkd/build/build.py screen-m19
 *
 * Masaüstü 19'un kopyası tek kolonda; kırmızı panel yok (mobilde geniş bir
 * kırmızı alan formu aşağı itiyor), onun yerine 80px cümle: `Hekimin evi.`
 * Hata durumu görünür: şifre alanı `error` + ipucu.
 *
 * Tek doygun buton: `f submit`. e-Devlet ikincil (beyaz + çizgi).
 * Fotoğraf yok — hasta/muayene sahnesi yasak, giriş ekranı kendi belgesi.
 */
const S = IK;
const M = IKM;
const pb = M.start("Mobil", "19-giris-m", 1400);

M.masthead(pb);

S.text(pb, "auth label", "ÜYE MASASI", "label", "ink.500", { x: M.G, y: 96 });
S.text(pb, "auth claim", "Hekimin evi.", "display", "ink.900", { x: M.G, y: 120, w: M.CW });
S.text(pb, "auth body", "Kılavuzlar, kurslar ve kongre kaydı tek hesapta. 6.847 hekim tek adreste.",
  "lead", "ink.600", { x: M.G, y: 296, w: M.CW });
S.rule(pb, "auth rule", M.G, 415, M.CW, "line.strong", 2);

/* -------------------------------------------------------------------- form kartı */
/* Yükseklik içerik zincirinden: her adım bir önceki bloğun altı (elle y yok). */
const CY = 439, PX = 36, PW = 318;
const CT = CY + 24;
const CS = CT + 36 + 12;
const F1 = CS + 52 + 20;
const F2 = F1 + 72 + 8;
const REM = F2 + 92 + 8;
const SUB = REM + 44;
const DIV = SUB + 52 + 24;
const EDV = DIV + 32;
const NOTE = EDV + 52 + 20;
const CH = NOTE + 20 + 24 - CY;

const card = M.card(pb, "auth card", M.G, CY, M.CW, CH);
S.text(card, "r title", "Üye girişi", "h3", "ink.900", { x: PX, y: CT, w: PW });
S.text(card, "r sub", "E-posta veya üye numaranızla giriş yapın.", "body", "ink.500", { x: PX, y: CS, w: PW });
S.field(card, "f mail", "E-POSTA VEYA ÜYE NO", "selin.aydin@ankara.edu.tr", PX, F1, PW);
S.field(card, "f pass", "ŞİFRE", "••••••••", PX, F2, PW, { error: true, hint: "Şifre en az 8 karakter olmalı." });

S.rect(card, "f rem box", PX, REM + 12, 18, 18, "white", { stroke: "line.strong" });
S.text(card, "f remember", "Beni hatırla", "meta", "ink.600", { x: PX + 26, y: REM + 11 });
S.text(card, "f forgot", "Şifremi unuttum", "meta", "red.700", { x: PX + PW - 120, y: REM + 11, w: 120, align: "right" });

M.btn(card, "f submit", "Giriş yap", SUB, { x: PX, w: PW });

S.rule(card, "f div", PX, DIV + 10, 110, "line.soft");
S.text(card, "f or", "veya", "meta", "ink.500", { x: PX + 118, y: DIV, w: 44, align: "center" });
S.rule(card, "f div 2", PX + 164, DIV + 10, PW - 164, "line.soft");

M.btn(card, "f edevlet", "e-Devlet ile giriş", EDV, { x: PX, w: PW, kind: "secondary" });
S.text(card, "f note", "İki adımlı doğrulama zorunludur.", "meta", "ink.500", { x: PX, y: NOTE, w: PW });

/* ------------------------------------------------------------------ alt bilgiler */
let y = CY + CH + 32;
S.text(pb, "f join", "Üye değil misiniz?", "meta", "ink.600", { x: M.G, y: y });
S.text(pb, "f join cta", "Başvuru →", "meta", "red.700", { x: M.G + 140, y: y });
y += 40;
S.text(pb, "f legal", "© 2026 İHKD · KVKK · Çerez politikası", "data", "ink.500", { x: M.G, y: y, w: M.CW });
S.text(pb, "f legal 2", "Tasarım çalışması — kurum ve kişiler kurgudur.", "data", "ink.500", { x: M.G, y: y + 24, w: M.CW });

pb.resize(M.W, S.snap(y + 24 + 48));

return JSON.stringify(S.end("19-giris-m"));
