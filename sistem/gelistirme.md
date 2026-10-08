# Geliştirme listesi

Beceri yazıcılarının, inceleyicilerin ve araştırmanın önerdiği, henüz yapılmamış işler. Bir madde yapılınca buradan
silinir ve `sistem/dersler.md`'ye ölçümüyle yazılır. Öncelik: **Y** yüksek (doğruluk), **O** orta (yetenek), **D** düşük.
Kurulum gerektirenlerde boyut ve lisans `yetenekler.toml`'a girer; 2 GB üstü ve ücretli olanlar kullanıcıya sorulur.

## Yetenek katmanı (`medya` komutları)
- **Y** `medya yavaslat --kirp x,y,w,h --olcek WxH`: 4K kaynağın ağır çekimini teslim boyutunda üret (HyperFrames 4K
  ProRes'i kare başı ~33 MB PNG'ye açıyor; uçtan uca denemede disk doldu, vekil klip gerekti).
- **Y** `medya ciz` (ffmpeg EDL çizicisi): uzun ve çekim ağırlıklı kurgularda planı doğrudan ffmpeg'le çiz (kesim,
  xfade, ölçek/kırpma, ses miksi); HyperFrames 45 dk'lık işte ~1,9 saat sürüyor (kapsam incelemesi, doğrulanmadı).
  Ölçüt hazır: `testler/nle_olc.py` (Resolve çizimi geçiyor). Dikkat (ölçüldü 2026-10-08): elle kurulan
  `concat → xfade → concat` zinciri erimeden sonra 1 kare kaydı (gelen klip 1 kare erken içerik, sonraki kesim 1 kare
  geç, toplam +1 kare) — zaman tabanlarını kare ızgarasına oturtup 0 kareye indirmeden yayımlama.
- **O** İndirmesiz komut paketi (kurulu araçlarla): `sabitle` (vidstab), `gurultu` (video gürültüsü: hqdn3d/nlmeans),
  `eski` (bwdif + büyütme), `dikey` (konu takipli 9:16), `renk-esle` (çekimler arası renk eşleme), `bosluk-kes`
  (konuşmalı videoda ölü sessizlikleri kesme), `gizlilik` (Vision yüz bulanıklaştırma), `plaka`, App Store ön ayarı.
- **O** `medya plan denetle`: `kurgu-zanaati/scripts/plan_denetle.py` CLI'ye taşınsın (senkron, denetle ve nle aynı
  sözleşmeyi okuyor; tek doğrulayıcı olsun).
- **O** `medya teslim`: `teslim-denetimi/scripts/teslim.py` (kodla / uygunluk / güvenli ön ayarları) CLI'ye taşınsın.
- **O** `medya sabitle`: titreme ölçümü (önce/sonra) + iki geçişli vidstab (bugün `kurgu-zanaati/scripts/titreme.py`).
- **O** Hız rampası yeteneği (`medya yavaslat --rampa`): 30 fps kaynaklar için ML ara kareli rampa (bugün `rampa.py`
  yalnız gerçek yüksek fps kaynakta).
- **O** Yeniden kadraj yolu: `medya analiz` konu kutularından yumuşatılmış kırpma/anahtar kare JSON'u (16:9 → 9:16).
- **O** `medya nle`: müzik seviyesi/kısma ve J/L kesim sesi taşınsın; `--paket` (.otioz), `--pisir` (hareket ve hızı
  pişmiş ara klipler); Resolve_OTIO efekt üst verisi (Dynamic Zoom, faders) — her biri `testler/nle_olc.py` ile Resolve
  ve Kdenlive'da ölçülerek (sınama medyası: `testler/nle_sinama.py`).
- **D** `medya nle`: başlangıç zaman kodlu gerçek kamera medyası (TC kare alanı zaman çizelgesi fps'inden büyük, ör.
  60 fps kamera) Resolve ve Kdenlive'da sınanmadı; `-kdenlive.otio` TC'yi Kdenlive'ın hesabıyla yazıyor.
- **D** Kdenlive OTIO içe aktarım hataları (son klibin kaydırması kayboluyor; erime isteği başarısız olup sonraki klibi
  sıfırlıyor; proje fps'i `duration().rate`'ten) KDE'ye bildirilebilir — hesap gerekir, kullanıcının kararı. Düzelirse
  `-kdenlive.otio` uyarlaması sadeleşir.
- **O** Plan sözleşmesine görüntüden ayrı ses kaynağı alanı (b-roll altında röportaj sesi, J/L).
- **D** `medya denetle`: planın `hiz<1` aralıklarında yinelenen kare oranı (`yinelenen.py`).
- **D** `medya kontak`: HDR kaynakta ton eşlemeli kareler (bugün soluk görünür).
- **D** `medya sdr --bas/--sure`: 4K HDR'de yalnız seçilen bölümü çevirmek (disk).
- **D** `medya incele` görselde görünen (yöne göre) boyut ve ICC adı; `medya analiz` görselde EXIF yönünü uygulasın.
- **D** Görsel teslim denetimi: `medya-denetim` iş akışına durağan görsel merceği (`gorsel-uretim/scripts/olc.py --teslim`).
- **D** `rampa.py`'deki ton eşleme zinciri `yavaslat.py`'deki ile ortak bir yerden gelsin.
- **D** `medya muzik-kisalt`: `ses-tasarimi/scripts/kisalt.py` (ölçü başında çoklu ek) yeteneğe dönüşebilir.
- **O** `medya gif` / döngü denetimi: GIF/WebP/APNG dışa aktarım + `hareket-tasarimi/scripts/dongu.py` ölçümleri
  (eşit gecikme, loop=0, bayt bütçesi, dikiş, son kare ≠ ilk kare) CLI'ye.
- **O** `medya hareket yeni <ad>`: HyperFrames init + yerel GSAP/yazı tipi kopyası + satıcı dosyalarını (CLAUDE.md,
  AGENTS.md, publish betikleri) temizleme + URL taraması tek komutta.
- **O** `medya-uretim` iş akışına isteğe bağlı kapak/görsel aşaması (medya-gorsel + gorsel-uretim).
- **D** `medya proje motor <p> remotion`: sonradan motor değiştirme (şablon kopyası + BRIEF satırı).
- **D** `medya incele` durağan görsel künyesi (piksel, 2x yoğunluk, ICC/P3, alfa; SVG'de script/dış bağlantı/<text>).

## Sağlayıcılar (kurulmadı — gerektiğinde, lisans/boyut söylenerek)
| Ne | Amaç | Lisans | Boyut |
|---|---|---|---|
| gorsel-ortami (rembg, onnxruntime, rawpy, vtracer) | arka plan (BiRefNet), RAW, vektör | MIT / LibRaw LGPL | 372 MB |
| birefnet-general-lite | saç/cam kenarlarında ikinci görüş | MIT | 224 MB |
| realesrgan-ncnn | eski/düşük çözünürlüklü fotoğraf büyütme | kod MIT, ağırlık BSD-3 | 58 MB |
| lama-onnx | nesne silme | Apache-2.0 | 208 MB |
| depth-anything-v2-small | 2.5D paralaks için derinlik | Apache-2.0 | 50 MB |
| resvg | vektörleştirilmiş logoyu geri çizip denetleme | MPL-2.0 | 5 MB |
| @remotion/three, three, R3F, @remotion/lottie, lottie-web | Remotion'da 3B ve Lottie | Remotion License + MIT | 62 MB |
| three 0.186.1 (HyperFrames içinde) | hafif 3B: dönen logo, parçacık | MIT | 20 MB |
| Manim Community 0.21 [typst] | matematik/algoritma açıklayıcı | MIT | ~350 MB (Homebrew'suz yol sınanmadı) |
| asciinema 3.2.1 + agg 1.9.0 | gerçek terminal oturumu → README GIF'i | GPL-3 (çıktı serbest) | 21 MB |
| lottie-web 5.13.0 + dotlottie-web 0.80.0 | uygulama içi Lottie oynatma/doğrulama | MIT | 33 MB |
| Blender 5.2.2 LTS | gerçekçi 3B (Cycles Metal) | GPL (çıktı serbest) | ~1,3 GB |
| VoxCPM2 8-bit | dış ses (4-bit CER %0 ölçüldü; doğallık için) | Apache-2.0 | +0,9 GB — kullanıcı dinleyip isterse |
| Z-Image-Turbo Q4 | fotogerçekçilik/görselde yazı (FLUX.2 klein'ın yanına) | Apache-2.0 | 5,9 GB — disk yetince |
| DaVinci Resolve Studio + yerleşik MCP | ajanın Resolve'u sürmesi | ücretli 295 $ | 6,7 GB — yalnız açık onayla |

## Ölçüm borçları
- `medya seslendir`: doğallık ölçülemez (kullanıcı dinler); konuşmacı benzerliği eşiği (0,5) 5 cümlelik örnekten — uzun
  metinlerde (≥ 30 cümle) ölç; isteğe bağlı MOS tahmincisi (UTMOS) değerlendir.
- `medya gorsel-uret --referans`: düzenlemede kenar kalıntısı görüldü (mermerde ahşap dokusu izi) — maske/kompozit yolu.
- 4K kaynakta RIFE'nin (UHD kipi) süre/disk ölçümü; şimdilik 4K'da Apple önce (`yavaslat` docstring'i).
- Remotion'da gerçek telefon HEVC/HDR çekimi (yalnız sayısal modda, mahrem olmayan bir klip).
