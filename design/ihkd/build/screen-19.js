/**
 * 19 — Üye girişi. Split screen: red panel with the mark and claim, form on paper.
 */
const S = IK;
const pb = S.start("Üyelik", "19-giris", 1024);

/* ------------------------------------------------------------------ sol panel */
const left = S.board(pb, "auth left", 0, 0, 720, 1024, "red.600");
S.text(left, "al mark", "İHKD", "h3", "on.red", { x: 72, y: 64 });
S.text(left, "al sub", "ÜYE MASASI", "label", "on.red", { x: 72, y: 104 });
S.text(left, "al claim", "Hekimin evi.", "display", "on.red", { x: 72, y: 228, w: 576 });
S.text(left, "al body", "Kılavuzlar, kurslar ve kongre kaydı tek hesapta. 6.847 hekim tek adreste.", "lead", "on.red", { x: 72, y: 400, w: 480, opacity: 0.88 });
S.photo(pb, "img-auth", 72, 520, 576, 240);
S.text(left, "al caption", "Kardiyoloji monitörü, hastane", "meta", "on.red", { x: 72, y: 856, w: 576 });
S.text(left, "al foot", "© 1998'den beri · Ankara · KVKK", "meta", "on.red", { x: 72, y: 944 });

/* --------------------------------------------------------------------- sağ form */
S.text(pb, "r title", "Üye girişi", "h2", "ink.900", { x: 808, y: 232 });
S.text(pb, "r sub", "E-posta veya üye numaranızla giriş yapın.", "body", "ink.500", { x: 808, y: 290, w: 480 });

S.field(pb, "f mail", "E-POSTA VEYA ÜYE NO", "selin.aydin@ankara.edu.tr", 808, 356, 500);
S.field(pb, "f pass", "ŞİFRE", "••••••••", 808, 452, 500, { error: true, hint: "Şifre en az 8 karakter olmalı." });

S.rect(pb, "f rem box", 808, 584, 16, 16, "white", { stroke: "line.strong" });
S.text(pb, "f remember", "Beni hatırla", "meta", "ink.600", { x: 836, y: 584 });
S.text(pb, "f forgot", "Şifremi unuttum", "meta", "red.700", { x: 1180, y: 584, w: 128, align: "right" });

S.btn(pb, "f submit", "Giriş yap", 808, 632, 500, 52, "primary");

S.rule(pb, "f div", 808, 724, 220, "line.soft");
S.text(pb, "f or", "veya", "meta", "ink.500", { x: 1040, y: 716, w: 36, align: "center" });
S.rule(pb, "f div 2", 1088, 724, 220, "line.soft");

S.btn(pb, "f edevlet", "e-Devlet ile giriş", 808, 760, 500, 52, "secondary");

S.text(pb, "f note", "İki adımlı doğrulama zorunludur.", "meta", "ink.500", { x: 808, y: 848, w: 500 });
S.text(pb, "f join", "Üye değil misiniz?", "meta", "ink.600", { x: 808, y: 900 });
S.text(pb, "f join cta", "Başvuru →", "meta", "red.700", { x: 940, y: 900 });
S.text(pb, "f legal", "© 2026 İHKD · KVKK · Çerez politikası", "data", "ink.500", { x: 808, y: 960 });

return JSON.stringify(S.end("19-giris"));
