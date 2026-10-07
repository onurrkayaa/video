# Stüdyo durumu — kaldığımız yer

**2026-10-07 — İŞ YOK.** Kullanıcının 2026-10-07 kararları uygulandı; yarım iş yok. Yeni istek gelince yeni proje aç.
(Uzun bir iş yarıda kalırsa bu dosyaya "DURAKLATILDI" + devam sırası yazılır; kurallar CLAUDE.md "Uzun işler".)

## Son durum (sınandı)
- Kuruldu ve ölçüldü: FLUX.2 [klein] 4B (`medya gorsel-uret`; 1024² ~84 sn, 8,8 GB bellek; aynı tohum = aynı görsel),
  VoxCPM2 4-bit (`medya seslendir`; Türkçe CER %0, ses kimliğiyle konuşmacı benzerliği 0,73–0,76), Kdenlive 26.08.1.
- Baş ajan `medya-yonetici` + iş akışları `medya-yonetim` (öneri) ve `medya-guncelle` (onaylananı uygula);
  oturum özeti kancası. GitHub: https://github.com/onurrkayaa/video (herkese açık, main).
- `medya test`: hafif takım geçiyor; ağır üretici sınamaları `medya test --agir` (FLUX.2 + VoxCPM2, 2026-10-07 geçti).

## Kullanıcının kararını bekleyenler
- Disk dar (~3–7 GB boş; takas oynatıyor): Mac'i yeniden başlatmak takası boşaltır. `~/.npm` önbelleği (1,8 GB,
  yeniden indirilebilir) silinsin mi?
- Ücretsiz DaVinci Resolve (2,5 GB; App Store hesabı) — disk yetince; şimdilik Kdenlive.
- Remotion 3B/Lottie ekleri (62 MB) ve VoxCPM2 8-bit (+0,9 GB) — disk açılınca, istenirse.
- DaVinci Resolve Studio + yerleşik MCP (295 $, ücretli → kapalı) — yalnız açık istekle.

## Arşiv
Ham araştırma/ölçüm: `sistem/devam/` (beceri tanımları `beceri-tanimlari.json`; ağır çekim ölçümü `yavas-cekim/`).
