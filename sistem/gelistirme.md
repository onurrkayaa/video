# Geliştirme listesi

Beceri yazıcılarının, inceleyicilerin ve araştırmanın önerdiği, henüz yapılmamış işler. Bir madde yapılınca buradan
silinir ve `sistem/dersler.md`'ye ölçümüyle yazılır. Öncelik: **Y** yüksek (doğruluk), **O** orta (yetenek), **D** düşük.
Kurulum gerektirenlerde boyut ve lisans `yetenekler.toml`'a girer; 2 GB üstü ve ücretli olanlar kullanıcıya sorulur.

## Yetenek katmanı (`medya` komutları)
- **O** `medya ciz` kalanları (çekirdek 2026-10-08'de kuruldu ve ölçüldü: dersler.md, `medya test ciz`):
  - `siyah-dip`/`beyaz-dip`: önce sözleşme kararı (dip kesimin iki yanında mı, `sure_kare` toplam mı; ilk çekimde
    siyahtan açılış). HyperFrames kompozisyonunda da tanımsız; iki motor aynı tanımla + `nle_olc`'ye dip ölçümü.
  - Fotoğraf: EXIF yönü (tarayıcı uygular, ffmpeg 6.0'ın uyguladığı ölçülmedi), HEIC → `sips`; Ken Burns'ün asıl yeri.
  - J/L kesim (planda ayrı ses kaynağı alanı yok: aşağıdaki O maddesi), kadraj pan/takip (anahtar kare alanı yok).
  - Sabit kadraj tamsayı (çift) kırpma: HyperFrames'in alt piksel `object-position`'ından ≤ 1 kaynak pikseli (ölçülen
    0,6 çıktı pikseli). İstenirse perspective yolu (bir yeniden örnekleme daha, hafif yumuşar) — ölçerek.
  - Ses: miksin PCM'ini de yazmak (`ustala` + `teslim.py kodla --ses` ile tek AAC kuşağı; bugün ciz AAC 320k yazar,
    `ustala` yeniden AAC kodlar). Erimede iki `kendi` çekimin sesi toplanır (HyperFrames gibi); ses çapraz geçişi yok.
  - `.claude/workflows/medya-uretim.js`'in atlanan aşama özetleri hâlâ `calisma/kompozisyon/` diyor.
  - Radar notu: Kdenlive içindeki melt 7.41.0 (MLT, GPL) de başsız ve kare dökmeden çizebilir; değerlendirilmedi
    (ffmpeg yolu daha az bağımlılık getirdiği için seçildi; MLT erimesi ilk karede ağırlık 0, son kare kapsayıcı).
- **Y** `kisma.py --bas` işareti: ses-tasarimi SKILL.md (Kısma adımı), teknikler.md §5 ve kisma.py'nin parantez notu
  `--bas <plan muzik.bas>` diyor; betiğin kendi tanımına göre doğrusu −`muzik.bas`. `muzik.bas` 0,5 iken `--bas 0.5`
  kısmayı 1 sn erken koydu (ölçüldü 2026-10-08, dersler.md). Önerilen `bas: 0`'da etkisiz. Düzeltme + sınama.
- **O** HyperFrames 0.8.140 PNG kipi (`--video-frame-format png`, CLAUDE.md'nin gerçek çekim son çizim önerisi):
  Y'de kazanç sıkışması: 1080p bt709 gerçek çekimde ortalama −1,9 düzey (O6); sentetik bt709 rampada Y=50 −0,5,
  128 −1,8, 200 −3,1, yani sabit kayma değil ~%1,7 sıkışma (dalga 3 doğrulaması; JPEG de nötr değil: +1,4 / +0,06 /
  −1,2; ciz +0,02); nedeni ayrılmadı;
  4K kaynakta 5 işçiyle takas 0,9 → 15,9 GB, SIGABRT; çöken çizimin Chrome süreçleri kapanmadı, `work-…` klasörü
  (3,5 GB) çıktı klasöründe kaldı (2026-10-08). Öneri güncellendi (CLAUDE.md, kurgu-zanaati, medya-uretim: gerçek
  çekimde `medya ciz`; HyperFrames'te ≤ 1080p kaynakta PNG, 4K'da JPEG + `--workers 1`); nedeni ve 4K PNG + 1 işçi
  ölçülmedi.
- **Y** `medya temizle --uygula`: `uv cache clean`'e `--cache-dir` açıkça verilsin. Hedef bugün `UV_CACHE_DIR`'den
  geliyor; ortam yüklenmeden çalışırsa stüdyo dışı `~/.cache/uv`'yi siler, yol bekçisi yalnız `.uv/cache`'i denetliyor
  (`env -u UV_CACHE_DIR arac/uv cache dir` → `~/.cache/uv`, 2026-10-08; o gün 16 KB). Sınama: alt süreç argümanı.
- **O** Ağır ML disk koşulu (5 + 3 = 8 GB) kodda yok: `disk_bekcisi` görsel üretimini 3,0, seslendirmeyi 2,5 GB altında
  durduruyor (`medya/ortak.py:78`, `gorsel_uret.py` `gorsel_uret()` içinde, `seslendir.py:132`). Tek VoxCPM2 sınaması
  2 × 1 GiB takas açtı (2026-10-08, dersler.md).
- **O** `medya seslendir` bellek tepesi: MLX önbelleği 10 cümlelik koşuda işçinin tepesini 13–14 GB'a çıkarıyor (MLX
  etkin tepe 5,0–6,5 GB; 4-bit'te de aynıydı), takas koşularda 2,5 → 4,65 GB büyüdü (kayıtlı en yüksek 4654,56 MiB). Aynı koşul
  `mx.set_cache_limit(0)` ile: 6,1 GB, takas büyümedi, çıktı bit düzeyinde aynı, üretim %20 yavaş (127 → 153 sn /
  51,8 sn ses; 2026-10-08; kanıt `sistem/devam/ham/ses-ab/onbellek0/`, taban `ses-ab/olcumler.json`). Ara sınır
  (1–2 GB) ölçülmedi. Öneri: `ses_uret_isci.py`'ye sınır, `/usr/bin/time -l` ile tepe ve hız ölçümü.
- **D** Türkçe normalleştirici (`medya/turkce.py`): sıra sayısı "3." "üç" okunuyor ("üçüncü" geçen cümlede her koşuda
  %5,3 yalancı CER), "-yken" ile "iken" ayrı sayılıyor. Ayrıca `medya seslendir` kapısı, toplam CER > %3 olup hiçbir
  cümle %8'i aşmayınca yeniden üretmeden kalıyor (2026-10-08 ağsız denemede 2 cümle, %4,6, çıkış 1).
- **O** İndirmesiz komut paketi (kurulu araçlarla): `sabitle` (vidstab), `gurultu` (video gürültüsü: hqdn3d/nlmeans),
  `eski` (bwdif + büyütme), `dikey` (konu takipli 9:16), `renk-esle` (çekimler arası renk eşleme), `bosluk-kes`
  (konuşmalı videoda ölü sessizlikleri kesme), `gizlilik` (Vision yüz bulanıklaştırma), `plaka`, App Store ön ayarı.
- **O** `medya plan denetle`: `kurgu-zanaati/scripts/plan_denetle.py` CLI'ye taşınsın (senkron, denetle ve nle aynı
  sözleşmeyi okuyor; tek doğrulayıcı olsun).
- **O** `medya teslim`: `teslim-denetimi/scripts/teslim.py` (kodla / uygunluk / güvenli ön ayarları) CLI'ye taşınsın.
- **O** `medya sabitle`: titreme ölçümü (önce/sonra) + iki geçişli vidstab (bugün `kurgu-zanaati/scripts/titreme.py`).
- **O** Hız rampası yeteneği (`medya yavaslat --rampa`): 30 fps kaynaklar için ML ara kareli rampa (bugün `rampa.py`
  yalnız gerçek yüksek fps kaynakta).
- **O** 1x 4K çekimler için teslim boyutunda ara klip (kırp/ölçek; `yavaslat`ın `_kirp_olcek` süzgeci ve renk ayarı
  yeniden kullanılır; `medya ciz` ile birlikte düşünülebilir): HyperFrames 1x 4K HEVC'yi PNG son çizimde kare başı
  11,8 MB'a açıyor (denemenin 237 karesi 2,8 GB; ağır çekim `.mp4` 1080x1920 ile 0,6 GB, 2026-10-08 borudan ölçüldü).
  Ağır çekim tek başına PNG'li son çizimi diske sığdırmaz. `medya ciz` kapsamındaki planlarda gerekmez (4K'yı kare
  dökmeden çiziyor, 2026-10-08); yalnız HyperFrames'e girecek 1x 4K çekimler için.
- **D** RIFE yolunda ProRes HQ ara dosyası (PNG → `ara.mov` → çıktı) aşırı ayrıntılı kırpılmış karede tam karedekinden
  1,8 dB fazla kaybettiriyor (sentetik 35,6 / 37,5 dB; gerçek çekimde 38,44 / 38,45, fark yok; 2026-10-08). Aday:
  kayıpsız ara dosya (FFV1 ya da x264 `-qp 0`) + önce/sonra ölçümü ve disk payı.
- **D** Ara kare yolunda son çıktı karesinin sağ komşusu yok: minterpolate'te son kare önceki kaynak karesini gösteriyor
  (ölçüldü: HDR sınaması, j=89 → 88, 46,4 dB); RIFE'de son iki çıktı karesi son girdinin birebir aynısı (4 girdi,
  `-n 8`; 2026-10-08), yani klip sonunda 1 karelik duruş. Planda klibin son karesini kullanma ya da
  `--sure`'yu bir kaynak karesi uzun ver; kalıcı çözüm adayı: hazırlıkta bir kare fazla al, çıktıyı kırp.
- **D** bt601 etiketli (ve etiketsiz < 720 satır) SDR kaynakta `yavaslat`ın rengi, HyperFrames'in aynı kameranın 1x
  çekiminde göreceğinden sapıyor. `--olcek`'siz yol pikselleri çevirmeden bt709 etiketliyor: smptehdbars kırmızısı 173
  yerine 189, kare ortalaması 3,5 düzey fark. `--olcek` ffmpeg 6.0'ın ara 8 bit RGB çevirisiyle yaklaşıyor ama griyi
  kaydırıyor: %75 beyaz 189 → 185/187/187, kare ortalaması 2,7 (etiketsiz SD'de 3,3). Ölçüm 2026-10-08:
  `sistem/devam/yavas-cekim/2026-10-08-kirp/olc_renk.json`. Stüdyonun bugünkü kaynakları bt709 etiketli, etkilenmiyor.
  Aday (ölçülmedi): iki yolda da aynı tek adımlı çeviri (zscale ya da swscale `accurate_rnd`) + aynı ölçüm.
- **O** Yeniden kadraj yolu: `medya analiz` konu kutularından yumuşatılmış kırpma/anahtar kare JSON'u (16:9 → 9:16).
- **O** `medya nle`: müzik seviyesi/kısma ve J/L kesim sesi taşınsın; `--paket` (.otioz), `--pisir` (hareket ve hızı
  pişmiş ara klipler); Resolve_OTIO efekt üst verisi (Dynamic Zoom, faders) — her biri `testler/nle_olc.py` ile Resolve
  ve Kdenlive'da ölçülerek (sınama medyası: `testler/nle_sinama.py`).
- **D** `medya nle`: başlangıç zaman kodlu gerçek kamera medyası (TC kare alanı zaman çizelgesi fps'inden büyük, ör.
  60 fps kamera) Resolve ve Kdenlive'da sınanmadı; `-kdenlive.otio` TC'yi Kdenlive'ın hesabıyla yazıyor.
- **D** Kdenlive OTIO içe aktarım hataları (son klibin kaydırması kayboluyor; erime isteği başarısız olup sonraki klibi
  sıfırlıyor; proje fps'i `duration().rate`'ten; klip işaretine kırpılmış başlangıcı yeniden ekliyor) KDE'ye
  bildirilebilir — hesap gerekir, kullanıcının kararı. Düzelirse `-kdenlive.otio` uyarlaması sadeleşir.
- **O** `medya nle` devrinde ölçülmeyenler — bir sonraki içe aktarmada (kullanıcı adımı ~3 dk): Kdenlive'da ölçü başı
  kılavuzları (`--muzik`; Kdenlive yeniden ölçeklemeden okuyor, `-kdenlive.otio` zaman çizelgesi hızında yazıyor),
  görüntü izinde boşluk; Resolve'da tek sayılı erime (11 kare → 5/6), klip işaretleri, kılavuzlar. Bunlar
  `testler/nle_sinama.py` planına eklenirse var olan çizimler (`cikti/nle/`) yeniden alınmalı.
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
  önekler (`sudo -u onur …`, `/usr/bin/time -o t.txt …`); here-string ve
  `env -S` (`bash <<< 'npx hyperframes cloud render'`, `env -S '…'`); whisperx'in ilk üç jetondan sonra gelmesi (`pip
  install -q -U whisperx`, `uv pip install --python ortamlar/ses/bin/python whisperx`; sürümlü biçim yakalanıyor);
  `init … --skip-transcribe --no-skip-transcribe` (citty `--no-` olumsuzlaması dökümü geri açıyor; kodda okundu);
  heredoc işaretinden önce satır devamı (`bash \` + satır sonu + `<<'EOF'` gövdesi kabuğa gidiyor ama veri sayılıyor:
  heredoc ayıklayıcı satır devamı silinmeden önce çalışıyor).
- **O** `remotion add` kuralında kalan kaçaklar (2026-10-09, JSON stdin; yeni kancada çıkış 0): ayrık değerli bayrak
  (`npx remotion --log verbose add …`: `verbose` alt komut sanılıyor), `node node_modules/@remotion/cli/remotion-cli.js
  add …` (RM düzenli ifadesi bin dosyasının adını tanımıyor), yönetici ile ikili arasında bayrak (`pnpm -C p remotion
  add …`, `yarn --cwd p remotion add …`), `bun x remotion add …`, `corepack yarn|pnpm …` (önek tablosunda yok; corepack
  kurulu, denenmedi). yarn, pnpm ve bun bu Mac'te kurulu değil.
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
- **D** Sabit sürümün kancada serbest kalan yolları (2026-10-08 ek turu): `-E`/`--save-exact`'sız tam sürüm (`npm i -D
  hyperframes@0.8.140`) package.json'a `^0.8.140` yazar (npm 11.19.0 arborist `reify.js`:1812-1827 "specific versions save
  with the save-prefix"; stüdyoda `.npmrc` yok, `save-exact` false; kodda okundu); git/URL/tarball kaynağı (`npm i
  github:heygen-com/hyperframes`) tanınmıyor. Aday: tam sürümlü proje kurulumunda `-E` zorunlu + sınama.
- **D** `hyperframes capture`: OPENROUTER/GEMINI/GOOGLE anahtarı ya da Vertex hesabı varsa yakalanan sitenin varlıklarını
  görsel açıklama için dışarı gönderiyor (0.8.140 `capture-EHOMO4MP.js`:1031, :3479; kodda okundu, çalıştırılmadı); kanca
  `--skip-vision` (`capture-5EHGRJZM.js`:73) istemiyor. Kişisel kare değil, kullanıcının verdiği web sitesi; 2026-10-08'de
  dört değişken de tanımsız, `@google/genai` kurulu değil.
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
| three (HyperFrames içinde) | hafif 3B: dönen logo, parçacık | MIT | 0: kökte 0.178.0 (Remotion eki, 2026-10-09); vendor tarifi denenmedi |
| Manim Community 0.21 [typst] | matematik/algoritma açıklayıcı | MIT | ~350 MB (Homebrew'suz yol sınanmadı) |
| asciinema 3.2.1 + agg 1.9.0 | gerçek terminal oturumu → README GIF'i | GPL-3 (çıktı serbest) | 21 MB |
| dotlottie-web 0.80.0 (lottie-web 5.13.0 kökte, 2026-10-09) | uygulama içi Lottie oynatma/doğrulama | MIT | 7,4 MB |
| Blender 5.2.2 LTS | gerçekçi 3B (Cycles Metal) | GPL (çıktı serbest) | ~1,3 GB |
| DaVinci Resolve Studio + yerleşik MCP | ajanın Resolve'u sürmesi | ücretli 295 $ | 6,7 GB — yalnız açık onayla |

## Ölçüm borçları
- `medya seslendir`: doğallık ölçülemez (kullanıcı dinler); konuşmacı benzerliği eşiği (0,5): 2026-10-08'de 80 cümlede
  (iki model, 10'ar cümlelik koşular) en düşük 0,72 — tek uzun metinde (≥ 30 cümle) kimlik kayması ölçülmedi;
  isteğe bağlı MOS tahmincisi (UTMOS) değerlendir.
- `medya gorsel-uret --referans`: düzenlemede kenar kalıntısı görüldü (mermerde ahşap dokusu izi) — maske/kompozit yolu.
- `medya gorsel-uret --model z-image`: fotogerçekçilik farkı FLUX.2'ye karşı ölçülmedi (A/B görselleri
  `sistem/devam/ham/gorsel-ab/`, kullanıcı bakar); `--low-ram`'sız süre ve bellek ölçülmedi (GPU %100; adım süresi 6
  koşu boyunca 29,7'den 41,6 sn'ye düzenli arttı, nedeni — ısı, saat hızı — ölçülmedi: hesap sınırlı görünüyor);
  Türkçe harfli yazı denenmedi (kural gereği çizdirilmiyor).
- Remotion'da gerçek telefon HEVC/HDR çekimi (yalnız sayısal modda, mahrem olmayan bir klip).
- Remotion 3B/Lottie (2026-10-09): yalnız basit sahne ölçüldü (ışıklı tek düğüm, şekil katmanlı Lottie).
  Ölçülmeyenler: doku ya da GLTF modelli ağır 3B sahne; Lottie'de görsel, yazı katmanı ve ifade (expression);
  uzun 3B çizimde Chrome'un bellek tepesi ve ısıl kısılma. `/usr/bin/time -l` yalnız node'u ölçüyor.
- HyperFrames 0.8.140 çizim düzeltmeleri için hedefli fikstür yok: GSAP ile kırpılan clip-path/inset öğe (#5010), geç
  başlayan `fromTo` (#5125), video üstünde hareket bulanıklığı (#5150), yavaş belge (#5168), 16 GB'ta ağır sahnede
  otomatik işçi sayısı ve takas (#5149). `testler/hyperframes-baslik` bunlara dokunmuyor (0.8.124 ile kare kare aynı);
  kazanımlar yalnız sürüm notu. #5033'ün (betik hatasında çizim düşer) eski proje kompozisyonlarına etkisi ölçülmedi.
