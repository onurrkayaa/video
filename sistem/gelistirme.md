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
- **Y** `medya temizle --uygula`: `uv cache clean`'e `--cache-dir` açıkça verilsin. Hedef bugün `UV_CACHE_DIR`'den
  geliyor; ortam yüklenmeden çalışırsa stüdyo dışı `~/.cache/uv`'yi siler, yol bekçisi yalnız `.uv/cache`'i denetliyor
  (`env -u UV_CACHE_DIR arac/uv cache dir` → `~/.cache/uv`, 2026-10-08; o gün 16 KB). Sınama: alt süreç argümanı.
- **O** Ağır ML disk koşulu (5 + 3 = 8 GB) kodda yok: `disk_bekcisi` görsel üretimini 3,0, seslendirmeyi 2,5 GB altında
  durduruyor (`medya/ortak.py:78`, `gorsel_uret.py:32`, `seslendir.py:132`). Tek VoxCPM2 sınaması 2 × 1 GiB takas açtı
  (2026-10-08, dersler.md).
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
  sıfırlıyor; proje fps'i `duration().rate`'ten; klip işaretine kırpılmış başlangıcı yeniden ekliyor) KDE'ye
  bildirilebilir — hesap gerekir, kullanıcının kararı. Düzelirse `-kdenlive.otio` uyarlaması sadeleşir.
- **O** `medya nle` devrinde ölçülmeyenler — bir sonraki içe aktarmada (kullanıcı adımı ~3 dk): Kdenlive'da 2026-10-08
  düzeltilmiş klip işareti (`testler/nle_olc.py <proje> --kdenlive-xml <proje.kdenlive>` işareti klibin giriş karesinde
  bulmalı), ölçü başı kılavuzları (`--muzik`; Kdenlive yeniden ölçeklemeden okuyor, `-kdenlive.otio` zaman çizelgesi
  hızında yazıyor), görüntü izinde boşluk; Resolve'da tek sayılı erime (11 kare → 5/6), klip işaretleri, kılavuzlar.
  Bunlar `testler/nle_sinama.py` planına eklenirse var olan çizimler (`cikti/nle/`) yeniden alınmalı.
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
- **D** `medya yaziya-dok`: HyperFrames'in kelime biçimini (`[{text,start,end}]`) de yazsın. Bugün stüdyo JSON'u doğrudan
  içe aktarılmıyor ("Unrecognized JSON transcript format"), `.srt` içe aktarımı işaret düzeyinde (7 kelime → 2 öğe);
  kelime zamanı için tek satırlık dönüşüm gerekiyor (medya-studyo "Alt yazı istenirse"; ölçüldü 2026-10-08).
- **D** `voxcpm2` sağlık denetimi yorumlayıcıya `ls` ile bakıyor (`ls .uv/tools/mlx-audio/bin/python`): kopuk bağda 0
  döner (`flux2-klein` 2026-10-08'de `ls -L`'ye geçti). Bugün `test_python_ortamlari_studyonun_yorumlayicisinda`
  yakalar, `medya yetenekler` yakalamaz.
- **D** gorsel-uretim ve arac-radari belgelerinde FLUX.2 için eski durum kaldı: `gorsel-uretim/references/araclar.md`
  "Üretici" başlığı ("çalıştırılmadı", "yalnız harici SSD", "bu Mac'te koşturulmadı"), `references/teknikler.md` §10
  ("Üretici kurulu değil"), `arac-radari/references/bilinen-kararlar.md` ("FLUX.2 klein Q4 … yalnız harici SSD").
  Sağlayıcı 2026-10-07'den beri iç diskte kurulu ve sınanıyor (`yetenekler.toml` flux2-klein); karar satırı kullanıcının
  verdiği onayla güncellenmeli.

## Koruma kancası
- **O** Kancalar sistem Python'una bağlı: `medya-koruma.py` ve `oturum-ozeti.py` `#!/usr/bin/env python3`,
  `.claude/settings.json` `python3 …/oturum-ozeti.py`; `kur.sh` de `python3` çağırıyor. python.org kaldırılırsa geriye
  `/usr/bin/python3` kalır, o da Xcode lisansı yüzünden 69 ile çıkıyor (ölçüldü 2026-10-08); PreToolUse'da 2 dışındaki
  çıkış engellemez (Claude Code kanca belgesi), yani koruma sessizce düşer. Kanca ortamında hangi `python3`'ün
  seçildiği ölçülmedi. Aday: yorumlayıcı `.uv/python`'dan (ör. `$MEDYA/.venv/bin/python`) + sınama.
- **O** Alt süreçte indiren diğer satıcı betikleri kancaya girmedi: media-use `audio/scripts/audio.mjs` (faceless-explainer,
  pr-to-video, product-launch-video `scripts/audio.mjs` buna devreder) `npx hyperframes tts` (Kokoro) ve `npx hyperframes
  transcribe` çalıştırıyor (`audio/scripts/lib/tts.mjs`:289–292, :363–365; kodda okundu, çalıştırılmadı). Kanca alt
  süreci görmez; `audio.mjs` genel ad olduğu için `prepare.sh` gibi beceri adı bağlamıyla `SATICI_BETIK`'e eklenebilir.
- **O** Önceden var olan kaçaklar (özgün kancada da çıkış 0; bağımsız doğrulama 2026-10-08, JSON stdin ile ölçüldü):
  `node node_modules/hyperframes/dist/cli.js cloud` (HF düzenli ifadesi `dist/cli.js`'i tanımıyor; ücretli/bulut kuralı da
  kaçıyor), `find … -exec npx hyperframes … \;` (`-exec` sonrası komut sayılmıyor), `cat …/prepare.sh | bash -s p` (boruyla
  kabuğa), `npx zx …/transcribe.mjs` (node dışı çalıştırıcı), `env HYPERFRAMES_SKIP_SKILLS=0 hyperframes init …` (init'in
  GitHub HEAD'den beceri tazelemesini yalnız bu değişken durduruyor). Her biri için ENGELLENMELI'ye örnek + düzeltme.
- **Y** Birleşik noktalama kaçağı (O1 düzeltme turundan sonra da çıkış 0; 2026-10-08, JSON stdin ile ölçüldü): shlex
  (`punctuation_chars`) ardışık noktalamayı tek jeton yapıyor, `);` ya da `)>` ayırıcı sayılmıyor: `echo $(date);
  hyperframes publish` ve `(cd x); npx hyperframes cloud render` geçiyor. Aday: yalnız noktalamadan oluşan jetonu bilinen
  işleçlere bölmek (`);` → `)` `;`). Sınama: bu iki örnek engellenir; `;;`, `|&`, `>&`, `&>` ve heredoc örnekleri aynı kalır.
- **O** Kalan önek ve biçim kaçakları (aynı ölçüm, özgün ve yeni kancada çıkış 0): değer bayrağı önek tablosunda olmayan
  önekler (`sudo -u onur …`, `/usr/bin/time -o t.txt …`, `npx -p hyperframes hyperframes cloud render`); here-string ve
  `env -S` (`bash <<< 'npx hyperframes cloud render'`, `env -S '…'`); whisperx'in ilk üç jetondan sonra gelmesi (`pip
  install -q -U whisperx`, `uv pip install --python ortamlar/ses/bin/python whisperx`; sürümlü biçim yakalanıyor);
  `init … --skip-transcribe --no-skip-transcribe` (citty `--no-` olumsuzlaması dökümü geri açıyor; kodda okundu);
  heredoc işaretinden önce satır devamı (`bash \` + satır sonu + `<<'EOF'` gövdesi kabuğa gidiyor ama veri sayılıyor:
  heredoc ayıklayıcı satır devamı silinmeden önce çalışıyor).
- **D** `find . \( -name skills \)` / `-name heygen` / `-name whisperx` yanlış engelleniyor (özgün kancada da): shlex
  kaçışlı `\(`'yi ve `'('`'yi alt kabuk `(`'iyle aynı jetona çeviriyor, ayırıcıdan sonraki çıplak ad komut başı sanılıyor.
  Satıcı betik adları için çıplak ad artık tutulmuyor; kökten çözüm "`(` yalnız komut başında ayırır" kuralı, ama `eval \(
  … \)`, `elif (…)`, `time -p (…)` istisnalarıyla sınanmalı (yer tutucuyla çevirmek `eval \( hyperframes cloud \)`'u kaçırıyor).
- **D** Canlı oturumda `cd ~/.claude/skills/embedded-captions` sonrası ayrı çağrıda `bash scripts/prepare.sh p`
  için kancaya gelen `cwd`'nin yeni klasörü gösterip göstermediği ölçülmedi (alt ajan kabuğu her çağrıda sıfırlanıyor;
  yalnız sentetik `cwd` sınandı). Göreli satıcı betiği engeli buna dayanıyor.
- **D** `hyperframes open` (projeyi HyperFrames masaüstü uygulamasına devretme) kancada serbest; v0.8.140 becerileri iş
  sonunda bunu ve `catch-up`'ı önermeye başladı. Bugün uygulama kurulu değil, komut yalnız indirme adresini yazıyor
  (`open-*.js`, kodda okundu 2026-10-08); uygulamanın hesap ve ağ davranışı incelenmedi. medya-studyo yönlendirmesi
  "masaüstü uygulaması tanıtımı atlanır" diyor; uygulama kurulursa kural kararı gerekir.
- **D** `ortam.sh` `HYPERFRAMES_NO_UPDATE_CHECK=1`'i koymuyor (yalnız `~/.claude/settings.json` env'i koyuyor): Claude Code
  dışındaki kabukta CLI günde bir npm kayıt defterine sürüm sorar (0.8.140 `chunk-DDQ4LOML.js`:258-262 yalnız bu
  değişkene, CI'ye ve geliştirici kipine bakıyor; kodda okundu, ölçülmedi). Yerel kurulum kendini güncellemez
  (araştırma 2026-10-05). Çizim sınaması değişkenleri kendisi veriyor.

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
- HyperFrames 0.8.140 çizim düzeltmeleri için hedefli fikstür yok: GSAP ile kırpılan clip-path/inset öğe (#5010), geç
  başlayan `fromTo` (#5125), video üstünde hareket bulanıklığı (#5150), yavaş belge (#5168), 16 GB'ta ağır sahnede
  otomatik işçi sayısı ve takas (#5149). `testler/hyperframes-baslik` bunlara dokunmuyor (0.8.124 ile kare kare aynı);
  kazanımlar yalnız sürüm notu. #5033'ün (betik hatasında çizim düşer) eski proje kompozisyonlarına etkisi ölçülmedi.
