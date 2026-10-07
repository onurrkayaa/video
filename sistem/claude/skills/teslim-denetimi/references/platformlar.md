# Platformlar, ön ayarlar, güvenli alanlar, HDR ve arşiv

Kanıt: `sistem/arastirma/2026-10-05/delivery-qa.md` (T3, T5, T6, T7, "Şüpheci doğrulama"). "Doğrulandı" = birincil
kaynaktan alınıp şüpheci geçişte yeniden okundu. "Doğrulanmadı" sayıyı kullanıcıya kesin bilgi diye söyleme;
"uygulamada teyit et" de. Komutlardan önce `source /Users/onurkaya/Projects/video/ortam.sh; P=$MEDYA/.venv/bin/python;
T=$MEDYA/sistem/claude/skills/teslim-denetimi/scripts/teslim.py`.

## `teslim.py kodla` ön ayarları (ne yapar)

| Ön ayar | Video | Ses |
|---|---|---|
| `dikey` 1080x1920 | libx264 slow, High, seviye 4.2 (daha büyük karede 5.x), CRF 17, maxrate 20M / bufsize 40M, GOP 0,5 sn, 2 B-kare, ustanın fps'i | aac_at 320k, 48 kHz, stereo |
| `youtube` 1920x1080 | aynı, CRF 16; 3840x2160 usta → 4K, seviye 5.1, maxrate 60M | aac 384k (aac_at 320k'da durur; günlüğe yazar) |
| `whatsapp` 720x1280 / 1280x720 | libx264 iki geçiş, seviye 4.0, `b:v = MB×8000×0,97/süre − 128` kb/s, maxrate 1,5×, GOP 2 sn, en çok 30 fps | aac_at 128k |
| `kucuk` 1080x1920 / 1920x1080 | whatsapp gibi iki geçiş, ama seviye 4.2+ ve ustanın fps'i; VMAF telefon modelsiz (93/85) | aac_at 128k |
| `apple` ustanın boyutu | hevc_videotoolbox `-q:v 65`, Main, `hvc1`, GOP 2 sn | aac_at 320k |

Hepsinde: `scale=…:flags=lanczos,setsar=1`, yuv420p, bt709 etiketleri (tv aralığı), `-map_metadata -1`, bitexact,
`+faststart`. Usta VFR, HDR etiketli ya da farklı en-boyda ise reddeder (doğrudan ölçek 16:9→9:16'da SAR 256:81
üretti). Çıktı varsa üzerine yazmaz. WhatsApp'ta `--mb` zorunlu; video bit hızı 300 kb/s altına düşerse reddeder
(Belge yolu). `--mb`'li hedefte dosya sınırı aşarsa bir kez `b:v × sınır/gerçek × 0,98` ile yeniden kodlar
(yama ile sınandı; 1 sn 4K→1080p'de 1,06/1 MB aşım denetimde görülmüştü). Bu Mac'te 12 sn'lik 1080p fikstürde kodlama + uygunluk 4–9 sn sürdü.

**Kodlayıcı seçimi (ölçüldü, sentetik zor içerik):** ~4 Mb/s'de VMAF x265 49,8 · x264 slow 47,0 · VideoToolbox HEVC
44,9 · VideoToolbox H.264 41,1; ~20 Mb/s'de VideoToolbox 63,2 ≈ x264 64,2. Boyut sınırlı (WhatsApp) → x264;
yüksek bit hızlı hızlı kopya (AirDrop) → VideoToolbox. Kaçın: H.264 High10 / 4:2:2 teslim (telefon çözücüleri),
HEVC'de `hev1` etiketi (Apple `hvc1` ister), `-vsync` (yerine `-fps_mode`).

## Platform sınırları (2026-10-05)

| Platform | Değer | Durum |
|---|---|---|
| YouTube yükleme | MP4, moov başta, düzenleme listesi yok (aşağıdaki nota bak), progresif, High, 2 ardışık B-kare, kapalı GOP = fps/2, CABAC, 4:2:0; AAC-LC 48 kHz stereo 384 kb/s | doğrulandı (Google yardım) |
| YouTube SDR bit hızı | 1080p 8 Mb/s (24–30 fps) / 12 (48–60); 2160p 35–45 / 53–68 | doğrulandı |
| YouTube HDR bit hızı | 1080p 10 / 15; 2160p 44–56 / 66–85 | doğrulandı |
| Shorts | ≤ 3 dk (2024-10-15 sonrası yüklemeler) | doğrulandı; "en çok 1080p" sayfada YOK |
| Meta Reels reklam | 1440x2560 önerilir, 9:16, ≤ 4 GB, 0–15 dk, H.264, kare piksel, sabit fps, progresif, stereo AAC ≥ 128 kb/s | doğrulandı |
| Reels organik | 20 dk'ya kadar, tam erişim ~3 dk | doğrulanmadı (ikincil kaynak) |
| TikTok reklam (Haziran 2026) | ≥ 540x960, ≤ 500 MB, ≤ 10 dk, ≥ 516 kb/s | araştırmacı resmî sayfadan; yeniden doğrulanmadı |
| TikTok uygulama | 10 dk (web 60), ~288 MB iOS / 72 MB Android / 4 GB web | doğrulanmadı |
| WhatsApp Belge | 2 GB'a kadar (Mayıs 2022'den beri), yeniden sıkıştırılmaz | araştırma |
| WhatsApp sohbet/HD/Durum | sınırlar | doğrulanmadı → kullanıcıya sor, `--mb` |
| iMessage medya | uygulama yeniden kodlar → kalite için AirDrop / iCloud bağlantısı | araştırma |
| Ses yüksekliği | Instagram/TikTok yayımlamaz; YouTube ~-14 LUFS topluluk ölçümü | -14 LUFS / ≤ -1 dBTP güvenli uzlaşma, garanti değil |
| E-posta eki | sınır sağlayıcıya göre değişir | araştırılmadı → kullanıcıya sor, `kucuk --mb N`; büyükse bağlantı/AirDrop |

**Düzenleme listesi (elst):** `kodla` çıktısında 2 `elst` var (AAC ön dolgusu + B-kare gecikmesi; ölçüldü). Kaldırma:
`-use_editlist 0` ile yeniden paketlenen dosyada `uygunluk --usta` KALDI verdi (video başı 33 ms geç, ses kayması
-0,8…19 ms). Yalnız YouTube işleme gerçekten hata verirse dene, sonra `uygunluk --usta` ve A/V'yi yeniden ölç.

Dikey usta YouTube'a Shorts olarak gider (`dikey` dosyası). Yatay 16:9 isteniyorsa yeniden kurgudur: sor, `kurgu-zanaati`.

## Güvenli alanlar (dikey)
- **Kırmızı** (Meta Reels reklam rehberi, doğrulandı): üst %14, alt %35, yanlar %6 boş kalmalı.
- **Sarı çerçeve** (muhafazakâr birleşim; TikTok %12,5/%34/~%11 + sağ düğme sütunu, Shorts orta 4:5 — ikincil):
  1080x1920'de x 120–960, y 285–1248.
- Instagram ızgarası Reels'i 3:4 orta kırpımla gösterir → kapak öznesi y 240–1680 (ikincil).
- Komut: `$P $T guvenli X.mp4 --cikti cikti/denetim/X-guvenli.png [--analiz analiz/X-analiz.json]`
  (18 eşit aralıklı kare). `--analiz` = `medya analiz X.mp4 --cikti analiz/X-analiz.json` (Apple Vision; kutular
  sol-üst kökenli): yüz merkezlerinin ≥ %95'i sarı kutuda ve alt %35'te ≤ 1 sn (araştırma eşikleri). Yüz yoksa yalnız
  sayfa; yalnız sayısal modda PNG açılmaz, `--analiz` sayısı raporlanır.

## HDR teslim politikası
- **Varsayılan SDR bt709** (araştırma önerisi). WhatsApp'a asla HEVC/HDR.
- HDR kopya yalnız istenirse: iPhone→iPhone (AirDrop/iMessage) ya da YouTube HDR. Kaynaklar HLG kalmalı:
  `hyperframes render <kompozisyon> --hdr -o calisma/usta-hdr.mp4` (HLG, BT.2020, HEVC Main10, hvc1) →
  `medya meta-temizle calisma/usta-hdr.mp4 --cikti cikti/<ad>-hdr.mp4` (hvc1 etiketi korunur; ölçüldü) →
  `$P $T uygunluk cikti/<ad>-hdr.mp4 --hedef hdr`.
- `medya denetle` HDR etiketli çıktıyı teknik satırında tasarım gereği ✗ sayar: bu satırı raporda "beklenen" diye
  yaz, diğer satırlar geçmeli. HDR'ye karşı SDR VMAF geçersiz. HDR rozeti ve görünüm iPhone'da kullanıcıya bırakılır
  (ölçülemez). VideoToolbox MaxCLL yazmaz; HLG'de gerekmez.

## Arşiv
- Arşiv = dokunulmamış kaynaklar + kompozisyon kaynağı (HTML/JS/varlıklar, plan, vuruş ızgarası) + araç sürümleri
  (`ffmpeg -version`, `hyperframes --version`) + tek SDR usta (CRF 14–16; `--quality delivery` = CRF 15).
  `medya denetle <usta> --hedef arsiv` (-24…-12 LUFS).
- **"Kayıpsıza yakın" istenirse:** CRF 15 usta görsel olarak kayıpsıza yakındır ("kayıpsız" deme). ProRes 422 HQ/LT
  yalnız harici diske ve doğrudan kaynaktan/çizimden (HyperFrames `--format mov` her zaman ProRes 4444 + alfa yazar,
  `--help` ile doğrulandı; 422 HQ değil, daha büyük); CRF ustayı ProRes'e çevirmek kalite eklemez, yalnız boyut. Harici disk yoksa CRF usta + kaynaklar arşivdir; raporda söyle.
- ProRes yalnız başka kurgucuya elden teslim ya da harici disk (4K30 HQ ≈ 6,6 GB/dk: ~10 GB boşlukta 1 dk bile
  5 GB tabanını deler):
  `ffmpeg -nostdin -i calisma/usta.mp4 -map 0:v:0 -map 0:a:0 -c:v prores_videotoolbox -profile:v hq -c:a pcm_s24le cikti/<ad>-prores.mov`
  (ölçüldü: HQ, yuv422p10le, 1080x1920 30p ~217 Mb/s ≈ 98 GB/sa; 4K30 HQ ≈ 398 GB/sa). Önce `df -h`; yazdıktan
  sonra ≥ 5 GB boş kalmalı. Bütünlük: `shasum -a 256 X > X.sha256` ve `ffmpeg -i X -map 0:v -f framemd5 X.framemd5`.
