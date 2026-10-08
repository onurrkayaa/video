# Stüdyo durumu — kaldığımız yer

**2026-10-08 — ÖNERİLER UYGULANIYOR (dalgalar hâlinde, `medya-guncelle`).** Kullanıcı: "hepsini sırayla uygula",
Resolve kur (en iyisi), GitHub'a gönder, Z-Image-Turbo + VoxCPM2 8-bit + Remotion 3B/Lottie kur ("Z-Image-Turbo'dan sonra
FLUX.2'ye gerek kalmıyorsa sil, gerek varsa dursun"). Kullanıcı adımları bitti (Mac yeniden başlatıldı, Resolve App
Store'dan kuruldu, Kdenlive içe aktarımı yapıldı, VS Code'a erişilebilirlik izni verildi).
Yapıldı: O5 (NLE devri ölçüldü: Resolve kare-kesin; Kdenlive için `-kdenlive.otio`), Resolve kaydı + Media Storage
(`projeler/`), npm önbelleği. Sıra: dalga 1 O1 → O2 (kalan) → O7 · dalga 2 O4 → O5 doğrulaması · dalga 3 O3 (şüpheci
düzeltmeli) → O6 · dalga 4 ekler (`sistem/yonetim/2026-10-08-ekler.json`: VoxCPM2 8-bit → Z-Image-Turbo → Remotion
3B/Lottie) · sonda tam sınama + git push.
(Uzun bir iş yarıda kalırsa bu dosyaya "DURAKLATILDI" + devam sırası yazılır; kurallar CLAUDE.md "Uzun işler".)

## Son durum (sınandı)
- Kuruldu ve ölçüldü: FLUX.2 [klein] 4B (`medya gorsel-uret`; 1024² ~84 sn, 8,8 GB bellek; aynı tohum = aynı görsel),
  VoxCPM2 4-bit (`medya seslendir`; Türkçe CER %0, ses kimliğiyle konuşmacı benzerliği 0,73–0,76), Kdenlive 26.08.1,
  DaVinci Resolve 21.1.0 (App Store; `medya nle` devri ölçüldü 2026-10-08).
- Baş ajan `medya-yonetici` + iş akışları `medya-yonetim` (öneri) ve `medya-guncelle` (onaylananı uygula);
  oturum özeti kancası. GitHub: https://github.com/onurrkayaa/video (herkese açık, main).
- `medya test`: hafif takım geçiyor; ağır üretici sınamaları `medya test --agir` (FLUX.2 + VoxCPM2, 2026-10-07 geçti).

## Kullanıcının kararını bekleyenler
- Resolve'da üç sınama projesi kaldı (medya-nle-sinama, -2, -3): Project Manager'dan silinebilir (ajan silmedi: özel
  arayüz, kör tıklama riskli).
- DaVinci Resolve Studio + yerleşik MCP (295 $, ücretli → kapalı) — yalnız açık istekle.

## Arşiv
Ham araştırma/ölçüm: `sistem/devam/` (beceri tanımları `beceri-tanimlari.json`; ağır çekim ölçümü `yavas-cekim/`).
