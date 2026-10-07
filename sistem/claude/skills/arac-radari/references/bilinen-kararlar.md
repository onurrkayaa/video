# Bilinen kararlar (2026-10-05)

Değerlendirmeden önce bak. Satır varken aynı aracı yeniden araştırma; yalnız "yeniden bak" tetiği gerçekleştiyse
kapılara dön. Yeni kararı (benimseme ya da red) kaynağı ve "yeniden bak" tetiğiyle bir satır olarak ekle. Alanların
seçtiği araçların ayrıntısı ilgili kardeş beceride ve `yetenekler.toml`'dadır.

Kaynak kısaltmaları (`sistem/arastirma/2026-10-05/`): CCE = claude-code-ecosystem.md, VF = video-framework.md,
EE = eksiklik-elestirisi.md, EC = editing-craft.md, D = `sistem/dersler.md`, T = `yetenekler.toml`,
YC = `sistem/devam/yavas-cekim/` (`ozet.jsonl`), NLE = `sistem/devam/ham/arastir-davinci.json` (`notlar_md`).

## 2026-10-05 kararları (benimsenen ve reddedilen)
| Araç | Karar | Neden / ölçüm | Yeniden bak | Kaynak |
|---|---|---|---|---|
| Remotion 4.0.533 (sabit) | ikinci motor, lisans kapılı: `medya proje yeni <ad> --motor remotion` yalnız kişisel / ≤3 kişi / yalnız dosya teslimi; değilse HyperFrames | ücretsiz lisans koşullu; 4+ kişilik işveren adına ya da müşteri kodu → ücretli Company License; lisans anahtarı, lambda/cloudrun/web-renderer/google-fonts kancayla kapalı | 5.x'e yükseltme ya da lisans metni değişikliği → önce lisans incelemesi | T, VF |
| RIFE v4.6 (rife-ncnn-vulkan 20221029, kod + ağırlık MIT, zip SHA-256 doğrulanmış) | ağır çekimde Apple FRC'den sonra ilk yedek | yalnız ara kareler, ham çözülerek: Apple ≈ RIFE > minterpolate (yüksek harekette 1,5–2 dB; el kamerasında RIFE 37,7 / minterpolate 32,6 dB); sakin çekimde fark yok; Neural Engine kullanmaz | Apple FRC el kamerası kliplerinde (YC `tos_*`) ölçülünce sıra yeniden değerlendirilir; yeni RIFE sürümü aynı fikstürde | T, YC, D |
| DaVinci Resolve Studio + MCP (`resolve-studio-mcp`) | ret (ücretli, 295 $): `tur = "uygulama"`, `etkin = false` | ücretsiz kuralı; dış betik yalnız Studio'da | yalnız kullanıcı açıkça satın almayı seçerse önerilir | T, NLE |
| Kdenlive, ücretsiz DaVinci Resolve | kullanıcının seçimi, elle bitirme için: `medya nle` (.otio) → içe aktarma; `tur = "uygulama"`, `etkin = false`, kullanıcı kurar | ajan süremez (dış betik ve Python yalnız Studio'da; ücretsiz 21.1'de Workspace ▸ Scripts içindeki Lua menü betikleri belgesiz ve elle başlatılan köprülerle çalışıyor — altyapı sayılmaz) | kullanıcı uygulamayı kurdu ya da sürüm değişti → .otio içe aktarmayı yeniden sına | T, NLE, VF |
| FCPXML uyarlayıcısı | ret | erimeyi düşürdü; 29,97 ve 23,976 fps'te çöktü | OTIO fcpx_xml eklentisinin yeni sürümü | NLE |
| Apple süper çözünürlük (VTSuperResolution, medya-apple) | ret (daha önce çıkarıldı) | durağan görüntüde PSNR bikübikten kötü, yalnız 4x, alfa yazmıyor | yeni macOS → yeniden ölç | D |

## Bu Mac'e sığmayanlar (16 GB RAM, fansız)

Boş disk sabit değildir: karar anında `df -h` ya da `medya temizle` ile ölç.
| Araç / sınıf | Karar | Neden | Yeniden bak | Kaynak |
|---|---|---|---|---|
| Yerel video difüzyonu (her model) | yok | çekirdek kurulum + bir proje (15–19 GB) boş alanı zaten doldurur; RAM ve takas | donanım ya da harici SSD değişti; ya da şunların hepsini birden karşılayan sürüm: izinli lisans, Apple Silicon portu, satıcının Apple Silicon'da ölçtüğü tepe bellek ≤ ~11 GB, yayımlanan boyutu (indirmeden) çekirdek + bir proje (15–19 GB) bütçesiyle birlikte kapı 3'ün disk koşulunu sağlıyor (o an ölçülen boş alanla). Yalnız disk koşulu tetik değildir; deneme yine kullanıcı kararı | EE §6–7 |
| ACE-Step, FLUX.2 klein Q4, Z-Image Q4, SeedVR2, MOSS-SFX | yalnız harici SSD (kullanıcı kararı) | adet başına 4,6–9,5 GB (+ ortam) | harici disk | EE §6–7 |
| ComfyUI + comfy-mcp | kaçın | disk ve hız; ComfyUI GPL-3.0, comfy-mcp AGPL-3.0-or-later ya da ticari; partner düğümleri kredi + hesap | — | CCE Düzeltmeler |
| İkinci Whisper kopyası (ggml ~1,6 GB, satıcı altyazı akışlarının kendi modelleri) | yok | `medya yaziya-dok` (MLX turbo) var, Türkçe sınandı | — | EE §3e, §7 |

## Lisans ve hesap engelleri
| Araç | Karar | Neden | Yeniden bak | Kaynak |
|---|---|---|---|---|
| MusicGen (media-use BGM yedeği ve otomatik kurulumu) | iş için yok | ağırlık CC-BY-NC-4.0 | — | CCE, EE §7 |
| madmom modelleri, `beat_this --dbn` | yok | modeller CC BY-NC-SA | — | CCE |
| Figma, Canva, Adobe, Runway, Cloudinary, Superdesign eklentileri; media-use HeyGen / ElevenLabs / Lyria; video-use | yalnız `bulut-ucretli`, `etkin = false` | hesap, kredi ya da API anahtarı; kişisel medya dışarı gider | kullanıcı açıkça isterse | CCE, EC |
| HyperFrames cloud, lambda, cloudrun, auth, publish, usage, feedback; `--describe false`'suz snapshot | yasak (kanca engeller) | ücret/hesap/dış istek; feedback herkese açık kanala gider; usage Claude girişini okur | — | CCE, VF |
| Kokoro-82M | Türkçe için yok | Apache-2.0 ama Türkçe ses yok | Türkçe ses eklenirse | CCE Düzeltmeler |
| Piper Türkçe sesleri | iş için yok | ses lisansları ticari değil ya da Lessac tabanlı | ses başına lisans değişirse | EE §3h |

## Koşullu (kullanılabilir; koşulu kayda yaz)
| Araç | Karar | Koşul | Kaynak |
|---|---|---|---|
| Essentia (`ortamlar/ses`) | evet, yerel | AGPL-3.0: dağıtılan yazılıma gömme; önceden eğitilmiş TF modelleri çoğunlukla CC BY-NC-SA (kullanılmıyor) | CCE |
| GSAP 3.15 | evet | Standard no-charge: ticari video serbest; rakip görsel animasyon aracı yasak | VF |
| ffmpeg-static 6.0 | evet | GPL + nonfree: çıktılar serbest, ikiliyi dağıtma | VF, CCE |
| mcp-for-blender 2.1.3 (MIT) | isteğe bağlı | telemetri `BLENDER_MCP_DISABLE_TELEMETRY=1` ile kapanır, DO_NOT_TRACK yok sayılır; Hyper3D, Hunyuan3D, Tripo, Sketchfab özellikleri hesap ister | CCE |
| Playwright MCP (Apache-2.0) | evet | eklenti `@latest` çalıştırır: sürüm sabitle | CCE |

## Bakım ve ajan uyumu
| Araç | Karar | Neden | Kaynak |
|---|---|---|---|
| Motion Canvas | yok | başsız çizim yok (editördeki RENDER düğmesi) | VF |
| Editly | yok | son npm sürümü 2022-12; native gl/canvas derlemesi | VF |
| MoviePy v2 (ana motor olarak) | yok | numpy ile CPU'da kare kare, az geçiş | VF |
| Natron | yok | Homebrew cask 2026-09-01'den beri kapalı; x86_64 | VF |
| `brew install melt`, `brew install mlt` | yok | melt ilgisiz SSH anahtarı aracı; mlt Qt6 + OpenCV 5 çeker | VF |
| Homebrew `ffmpeg` 9.0.2 (yalın) | ffmpeg-static yerine yok | vidstab, zscale, libass, drawtext yok (`ffmpeg-full` için [güncelleme](guncelleme-ve-disk.md) §4) | VF Düzeltmeler |
| ffmpeg MCP sarmalayıcıları | yok | ince sarmalayıcı; örneği 2025-05'ten beri güncellenmedi | CCE |
| ffmpeg-gl-transition | yok | yamalı ffmpeg + GLEW/GLFW, bayat | VF |
| OpenMontage, OpenChatCut, pireel, Kinocut, OpenCut | yok | HyperFrames + ffmpeg ile büyük ölçüde örtüşür, büyük ve hızlı değişir (AGPL yerelde sorun değil); OpenChatCut ve OpenMontage Remotion üzerinden çizer (Remotion lisansı geçerli); Kinocut çok yeni; OpenCut yeniden yazımda | VF |
| Denetlenmemiş topluluk becerileri / MCP listeleri | yok | `!` komut enjeksiyonu, allowed-tools, oturum kancası riski | CCE |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` (telemetri anahtarı olarak) | yok | güncellemeleri, özellik bayraklarını, eklenti ve beceri senkronunu da kapatır | CCE |
