---
name: teslim-denetimi
description: Use when a finished edit or render must be exported for a destination (Instagram Reels/feed/story, TikTok, YouTube/Shorts, WhatsApp, iMessage/AirDrop, presentation, archive), when iPhone HDR/VFR footage is delivered, or before any deliverable is called done or audited (teslim, dışa aktar, platforma hazırla, son kontrol, kalite kontrol, denetim, rapor ver).
---

# Teslim ve denetim

**İlke:** her teslim tek ustadan (SDR bt709, CFR) türetilir; her iddia bir ölçüme ya da açılmış temas
sayfasına dayanır; ölçülemeyen, izlenecek saniyeleriyle "ölçülemedi" yazılır. Proje klasöründe, her kabukta:
`source /Users/onurkaya/Projects/video/ortam.sh; P=$MEDYA/.venv/bin/python; T=$MEDYA/sistem/claude/skills/teslim-denetimi/scripts/teslim.py`

## Ne zaman / ne zaman değil
- **Ne zaman:** teslim dosyası, son denetim (`medya-denetci`), rapor.
- **Değil:** sıra, geçiş, kadraj, en-boy değişimi → `kurgu-zanaati`; miks, tık onarımı →
  `ses-tasarimi`; animasyon → `hareket-tasarimi`; fotoğraf → `gorsel-uretim`.

## Yalnız bunları sor
- **Gizlilik:** kişisel klipte kare/sayfa açmadan sor; istemezse yalnız sayısal mod (PNG açılmaz, kullanıcı izler).
- WhatsApp: Belge mi, sohbete mi (sınır doğrulanmadı → `--mb`)? E-posta: kaç MB? Herkese açıksa müzik lisansı.
- YouTube: Shorts mu (dikey dosya), 16:9 mu (yeniden kurgu)? Arşiv: harici disk var mı?
- Varsayılan: SDR, ustanın fps'i, yazı yok. HDR'de mobius ile sürdür; A/B dosyaları raporda, başka seçilirse yeniden kodla.

## Hızlı başvuru
| Hedef | `kodla --hedef` | `medya ustala` | `denetle --hedef` |
|---|---|---|---|
| Reels, TikTok, Shorts, Story (9:16) | `dikey` 1080x1920 | `--hedef -14 --tepe -1.5` | `sosyal` |
| Instagram akış 4:5 | `dikey --boyut 1080x1350` | -14 / -1.5 | `sosyal` |
| YouTube 16:9 | `youtube` | -14 / -1.5 | `youtube` |
| WhatsApp sohbet | `whatsapp --mb N` (720p) | -14 / **-2.0** | `sosyal` |
| E-posta, küçük iş kopyası | `kucuk --mb N` (1080p) | -16 / **-2.0** | `web` |
| iMessage, AirDrop | `apple` (HEVC hvc1) | -14 / -1.5 | `sosyal` |
| Sunum, iş, web | `youtube` / `dikey` | -16 / -1.5 | `web` |

Sınırlar, güvenli alan, HDR kopya, arşiv (`--hedef arsiv`), ProRes: [platformlar](references/platformlar.md).

## Bitirme sırası
1. **Usta:** bitmiş video → `medya proje yeni "<ad>" --tur video --kaynak <dosya>`, `medya incele`; SDR+CFR ise usta
   odur, HDR/VFR ise `medya sdr` / `medya cfr` ([hazırlık](references/hazirlik.md)). HyperFrames: HDR klipler önce
   `medya sdr kaynak/X.MOV --cikti calisma/sdr/X.mp4`, kompozisyon bunları kullanır (`--sdr` emniyettir, hable). Disk tahmini, sonra:
   `caffeinate -i hyperframes render calisma/kompozisyon --sdr --quality delivery --video-frame-format png --frames-cache-dir off -o calisma/usta.mp4`.
2. **Tek karelik flaş/siyah** silinmez, önceki karenin kopyası olur (silmek kesimleri kaydırır).
3. **Kesimdeki tık** `ustala`dan önce onarılır (`ses-tasarimi`).
4. **Ses:** `ffmpeg -nostdin -i calisma/usta.mp4 -map 0:a:0 -c:a pcm_s24le calisma/ses.wav`, sonra
   `medya ustala calisma/ses.wav --hedef -14 --tepe -1.5 --cikti calisma/ses-usta.wav`; ≤ 128k (whatsapp, kucuk) için ayrı `--tepe -2.0` WAV.
5. **Kodla = son yazma** (üst veri silinir, moov başa): `$P $T kodla calisma/usta.mp4 --hedef dikey --ses calisma/ses-usta.wav --cikti cikti/<ad>-reels.mp4`.
   Kodlanmayan teslimde en son `medya meta-temizle` (`ustala` konum etiketini korur).

## Doğrulama (her dosya)
1. `medya denetle X --hedef sosyal --boyut 1080x1920 --fps 30 --sure S [--plan plan/kurgu.json] [--muzik analiz/muzik.json] --json cikti/denetim/X-denetim.json`
   → GEÇTİ; ✓ satırlarındaki tık/donma/sessizlik bulgularını da oku; "renk etiketleri boş" gerçek eksik etikettir (2026-10-05'te yanlış alarm düzeltildi).
2. `uygunluk` ✗ yok (`kodla` çalıştırır; elle `$P $T uygunluk X --hedef dikey --usta calisma/usta.mp4`); `--mb`'li hedefte `--vmaf`.
3. "Vuruşa oturdu" yalnız `medya muzik` güveni `yuksek` ve `medya senkron` `vurusta` ise.
4. İzin varsa Read ile aç: denetle sayfası, kesim anları (`medya kontak X --anlar …`), dikeyde `$P $T guvenli X --cikti …`.
5. `Workflow({scriptPath: '/Users/onurkaya/Projects/video/.claude/workflows/medya-denetim.js', args: {cikti, proje, hedef, brief}})` → GECTI (yalnız sayısal modda `brief`: "kare açma").

**Ölçülemez:** hareket akıcılığı, sesin kulağa gelişi, platformun sıkıştırması, HDR ekran, ışığa duyarlılık, müzik hakları.

## Rapor (Türkçe; "mükemmel" yok)
Künye (yol, MB, boyut, fps, süre, LUFS/dBTP), denetle/uygunluk, açılan sayfalar ya da "yalnız sayısal mod",
ölçülemeyenler + izlenecek saniyeler, kararlar. Eşik, düzeltme, şablon: [denetim](references/denetim.md).

## Sık hatalar
- Elle uzun ffmpeg zinciri: SAR 256:81, renk etiketi, seviye, faststart kaçar → `kodla`.
- HDR: avconvert varsayılanı (Y 148), `--sdr`'siz çizim (MP4 HDR olur), HDR kaynağı doğrudan `--sdr` ile çizmek (hable, Y 182), kaynak temas sayfasından renk yargısı.
- `--hedef`siz `denetle` (web: -17…-15) ya da varsayılan -16'lık `ustala` ile sosyal teslim.
- Doğrulanmamış sınırı kesin söylemek (WhatsApp, e-posta, Shorts çözünürlüğü); CRF ustayı "kayıpsız" demek.
- İstenmeden bulanık arka plan, yazı, renk eşleme, yeniden kurgu.

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/delivery-qa.md` (+ video-framework.md, audio-production.md); eskidiyse `arac-radari`.
