# Araçlar, lisanslar, kurulum

Kurulum kuralları:
- Homebrew kilitli (Xcode lisansı kabul edilmedi). Kurulum yalnız npm, uv ya da resmî ikili ile yapılır.
- Kurmadan önce boyut kullanıcıya söylenir. 2 GB'ın üstünde ise sorulur.
- Benimsenen araç `arac-radari` becerisiyle kaydedilir.

Kanıtlar: `sistem/arastirma/2026-10-05/animation-motion.md` (Şüpheci doğrulama bölümü seçimlerin önüne geçer) ve `sistem/devam/ham/arastir-remotion.json`.

## Remotion 4.0.533 — lisans kapılı ikinci motor
- **Ne zaman HyperFrames yerine:**
  - Ürünün gerçek React bileşenleri videoda kullanılacaksa.
  - Veri güdümlü çok sürümlü şablon gerekiyorsa. HyperFrames'te de `--variables` ve `--batch` var.
  - `@remotion/transitions`, `effects` ya da `motion-blur` paketleri isteniyorsa.
  - Kullanıcı açıkça Remotion istiyorsa.
- **Kapı (Remotion License 4.x):**
  - Ücretsiz kullananlar: birey; en çok 3 çalışanlı kâr amaçlı kuruluş; kâr amacı gütmeyen kuruluş.
  - `BRIEF.md` → Lisans bağlamı `kişisel`, `serbest` (tek kişi, yalnız bitmiş dosya teslimi) ya da `iş ≤3 kişi` ise Remotion kullanılır.
  - Şirket 4+ kişiyse, müşteri Remotion kodunu alıyor ya da çalıştırıyorsa, bağlam bilinmiyorsa HyperFrames kullanılır. Bağlam boşsa sorulur.
  - Mevcut Remotion kodu kapıdan geçmezse `remotion-to-hyperframes` ile taşınır.
  - Fiyatlar yalnız rapor içindir: Creators 25 $/koltuk/ay, Automators en az 100 $/ay.
  - 5.x şartları yürürlükte değil; 5.x'te yükleniciler de ekip sayısına giriyor. Lisans incelemesi yapılmadan 5.x'e yükseltilmez.
- **Proje:** `medya proje yeni <ad> --motor remotion` şablonu `calisma/remotion/` altına kopyalar. Bileşenler:
  - `remotion.config.ts`: HyperFrames'in Chrome'u, bt709, angle, eşzamanlılık 4.
  - Yerel Inter woff2 dosyaları, kopya olarak; symlink 404 verir.
  - Yazısız `Ornek.tsx`; 3B ve Lottie örnekleri `Ornek3B.tsx`, `OrnekLottie.tsx` (`public/lottie/ornek.json`).
    Kullanılmıyorsa `Kok.tsx` satırı ve dosyası silinir: 2B çizim paket yüzünden ~0,2 sn uzar (3 koşu ölçüldü).

  Komutlar proje klasöründen `$MEDYA/node_modules/.bin/remotion …` biçiminde çalıştırılır; `npx` kullanılmaz.
- **Doğrulama:**
  - `remotion still src/index.ts <Id> ../../analiz/kare-N.png --frame=N` çıktısı Read ile incelenir.
  - Çizimden sonra `medya kontak` çalıştırılır.
- **Son çizim:** `remotion render src/index.ts <Id> ../../cikti/x.mp4 --image-format=png --color-space=bt709`. WebGL için `--gl` gerekmez, şablonun ayarı `angle`;
  komut satırındaki bayrak ayarı ezer.
- **Ölçülenler:**
  - Varsayılan renk uzayı BT.601'i etiketsiz yazar ve HD oynatıcıda renk kayar. Bu yüzden bt709 açıkça verilir.
  - png+bt709 VMAF 98,80, jpeg 96,97 (en kötü kare 92,98 → 95,06); süre ×1,24.
  - Çekim kareleri birebir çıktı (108/108); `<Audio>` örnek doğruluğunda; iki çizim aynı (150/150).
  - `--gl=angle` WebGL'de 3,6 kat hızlı.
  - `angle` WebGL'i Apple GPU'sunda çalıştırır (ANGLE Metal, 2026-10-09). Ayarsız 4.0.533 CPU'ya (SwiftShader) düşer.
    `swiftshader`, `egl`, `vulkan` ve `angle-egl`'de WebGL hiç yok. R3F sahnesi, 90 kare 1080x1920: angle 3,9 sn,
    ayarsız 6,3 sn, swangle 15,2 sn. angle'ın iki koşusu 90/90 kare bit düzeyinde aynı.
  - Ara kare üretmez: 30 fps kaynak 0,5x'te 60 karede 30 eşsiz kare verdi. Ağır çekim önce `medya yavaslat` ile üretilir.
  - `trimBefore` ve `trimAfter` kompozisyon karesi cinsindendir.
- **Ev kuralları** (kanca bir kısmını engeller):
  - Kullanılmayanlar: `licenseKey`, `--public-license-key`, `setPublicLicenseKey`. "free-license" de remotion.pro'ya kullanım olayı gönderir (ölçüldü).
  - Studio'da "Render in browser" ve `@remotion/web-renderer` kullanılmaz; ikisi de her zaman telemetri yollar.
  - Lambda, Cloud Run ve Vercel kullanılmaz.
  - `@remotion/google-fonts`, `remotion.media` varlıkları, `@remotion/sfx`, ElevenLabs, Mapbox ve MapTiler kullanılmaz.
  - `create-video`, `remotion upgrade`, `npx skills` ve `@latest` kullanılmaz.
  - Studio kendiliğinden açılmaz: npm'e ve bugs.remotion.dev'e istek atar, yerel ağdan dinler. Kullanıcı isterse: `$MEDYA/node_modules/.bin/remotion studio --no-open`.
- **3B ve Lottie ekleri (kurulu, 2026-10-09; 20 npm paketi, +62 MiB):** @remotion/three, three 0.178.0, @react-three/fiber
  9.2.0, @remotion/lottie, lottie-web 5.13.0. Bunlar Remotion 4.0.533'ün kendi sınadığı sürümler; Remotion'la birlikte
  yükseltilir (`yetenekler.toml` → remotion). `npx remotion add` kullanılmaz.
  - 3B: `<ThreeCanvas width height>` ve ışık kullanılır. Hareket yalnız `useCurrentFrame()`'den gelir; R3F `useFrame`
    çizimde titrer. İçerideki `<Sequence>`'lar `layout="none"` olur. Model ve doku yerel dosyadan (`public/`) gelir.
  - Lottie: JSON `public/` altına kopyalanır, `staticFile` + `delayRender` ile yüklenir; lottiefiles adresi kullanılmaz.
    1 Remotion karesi = 1 Lottie karesi, JSON'daki `fr` yok sayılır. `fr` fps'ten farklıysa `playbackRate={fr / fps}`
    verilir (60 fps JSON, 30 fps kompozisyon, hız 2: 12. kare JSON'un 24. karesiyle piksel piksel aynı).
  - Sınama: `medya test remotion` (3B'de sürücü ANGLE Metal mi, ışık, dönüş; Lottie'de bilinen alan ±%2).
    Kanıt: `sistem/devam/remotion-3b/2026-10-09/`.

## Manim CE 0.21 — denklem ve matematik
- **Ne zaman:** denklem, koordinat düzlemi, fonksiyon grafiği, Transform morfları. Denklemsiz algoritma ya da graf (ör. Dijkstra) HyperFrames'te SVG + GSAP ile yapılır.
- **Araştırmadan sapma (gerekçe):** araştırma algoritma ve graf için Manim CE seçiyor. Stüdyoda denklemsiz graf HyperFrames'te kalır, çünkü kurulum gerektirmez, tek motorla çalışır, 3B logo ve kamera aynı kompozisyonda olur. Durumlar küçük bir Python betiğinde algoritma gerçekten çalıştırılarak üretilir. Kullanıcı Manim görünümü isterse aşağıdaki ~350 MB kurulum önerilir ve sorulur.
- **Lisans:** MIT; ticari kullanım serbest. Typst eklentisi LaTeX gerektirmez; MacTeX (çok GB) kurulmaz.
- **Kurulum (~350 MB, Homebrew'suz yol sınanmadı):**
  ```
  source /Users/onurkaya/Projects/video/ortam.sh
  $MEDYA/arac/uv venv -p 3.12 $MEDYA/.venv-manim
  VIRTUAL_ENV=$MEDYA/.venv-manim $MEDYA/arac/uv pip install pkgconf
  DEVELOPER_DIR=/Library/Developer/CommandLineTools PKG_CONFIG_PATH=/opt/homebrew/lib/pkgconfig \
    VIRTUAL_ENV=$MEDYA/.venv-manim $MEDYA/arac/uv pip install 'manim[typst]'
  $MEDYA/.venv-manim/bin/manim checkhealth
  ```
  pycairo 1.29.2 yalnız kaynak olarak geliyor ve derlenir; `/opt/homebrew/lib/pkgconfig/cairo.pc` mevcut. typst tekerleği 30,5 MB.
- **Kullanım:**
  - Taslak: `manim -ql sahne.py Sahne`.
  - Son kare PNG: `-s` → Read.
  - Son çizim: `-qh --fps 30 -r 1920,1080`.
  - Saydam bindirme: `-t --format mov`. Ardından HyperFrames'e sessiz `<video>` olarak konur; kamera ve geçiş orada yapılır.
- **Denetim:** ffprobe `nb_frames` = süre × fps olmalı; saydam çıktıda pix_fmt alfa içermeli.
- **0.21 notu:** Code nesnesinin renkleri artık Pygments stilinden gelir.

## Three.js — HyperFrames içinde hafif 3B
- **Lisans ve boyut:** MIT. Kökte `three@0.178.0` kurulu (Remotion 3B eki, 2026-10-09); ayrıca kurulmaz. Kökte başka
  sürüme geçmek Remotion'un sınadığı sürümü bozar.
- **Vendor kopyası:**
  ```
  mkdir -p kompozisyon/vendor/three/addons/loaders
  cp $MEDYA/node_modules/three/build/{three.module.js,three.core.js} kompozisyon/vendor/three/
  cp $MEDYA/node_modules/three/examples/jsm/loaders/SVGLoader.js kompozisyon/vendor/three/addons/loaders/
  grep -oE "from '[^']+'" kompozisyon/vendor/three/three.module.js | sort -u   # yalnız ./three.core.js beklenir
  ```
  importmap: `"three": "./vendor/three/three.module.js"`, `"three/addons/": "./vendor/three/addons/"`.
  - 0.178.0'da `three.module.js` (0,60 MB) yalnız `./three.core.js`'i (1,39 MB) içe aktarır. `.min.js` çifti de var
    (0,34 + 0,38 MB); bu durumda importmap `three.module.min.js`'i gösterir. Çekirdek kopyalanmazsa 404 olur ve sahne
    boş çizilir (yapı klasörü ve içe aktarma satırı okunarak doğrulandı, 2026-10-09).
  - Tarif stüdyoda **denenmedi**: ilk `snapshot --describe false` karesi Read ile açılıp tuvalin boş olmadığı denetlenir.
- **SVG logodan 3B:** `SVGLoader` + `ExtrudeGeometry`. HDRI gerekiyorsa Poly Haven'den (CC0) bir kez indirilip projede tutulur.
- Kurallar ve denetim için [hyperframes](hyperframes.md) → Adaptörler.

## Blender 5.2.2 LTS — gerçekçi 3B
- **Lisans:** uygulama GPL'dir, render çıktısı kullanıcınındır.
- **Kurulum:** blender.org'dan 330 MB'lık DMG indirilip /Applications'a kopyalanır (kurulu ~1,3 GB, tahmin). Hesap gerekmez.
- **Çalıştırma:** `/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --offline-mode --python-exit-code 1 -P sahne.py -- --out <mutlak>/kareler/`
  - Cycles: `compute_device_type='METAL'`, `scene.cycles.device='GPU'`.
  - Çıktı PNG dizisidir; sonra ffmpeg ya da HyperFrames.
  - Uzun çizimden önce `-f 1` ile tek kare denenir.
- **5.x API tuzakları:**
  - Motor adı `BLENDER_EEVEE`.
  - `file_format`'tan önce `image_settings.media_type`.
  - `scene.node_tree` yerine `scene.compositing_node_group`.
- **MCP for Blender** yalnız keşif içindir. Kullanılacaksa `DISABLE_TELEMETRY=true` ve `BLENDER_MCP_SAFE_MODE=1` verilir; Sketchfab, Rodin ve Hunyuan araçları kullanılmaz.

## Terminal demosu (çıktı asla uydurulmaz)
- **A. Kurulumsuz:**
  1. Gerçek çıktıyı yakala: `script -q kayit.txt <komut>`.
  2. Kişisel bilgi tara: `LC_ALL=C grep -a -nE "$USER|/Users/|@|token|secret|key" kayit.txt`. Bulunanlar nötrleştirilir ve kullanıcıya söylenir.
  3. HyperFrames'te `code-terminal-run` ya da `terminal-simulator` öğesi bu çıktıyla doldurulur.
  4. Bekleme kısaltılırsa bu açıkça belirtilir.
- **B. asciinema 3.2.1 + agg 1.9.0** (GPL; çıktı kullanıcının; 6,8 + 13,8 MB):
  ```
  curl -L -o $MEDYA/arac/asciinema https://github.com/asciinema/asciinema/releases/download/v3.2.1/asciinema-aarch64-apple-darwin && chmod +x $MEDYA/arac/asciinema
  curl -L -o $MEDYA/arac/agg https://github.com/asciinema/agg/releases/download/v1.9.0/agg-aarch64-apple-darwin && chmod +x $MEDYA/arac/agg
  asciinema rec --idle-time-limit 1 -c '<komut>' demo.cast
  agg --font-size 28 --theme monokai demo.cast demo.gif
  ```
  - `asciinema upload`, `auth`, `stream` ve `session` kullanılmaz (sunucuya bağlanırlar).
  - agg olay zamanlamasıyla değişken gecikmeli GIF yazar (stüdyoda ölçülmedi). `dongu.py --tek-sefer` bunu bekleme olarak sayar; gecikmeler taban gecikmenin tam katı olmalıdır.
- **C. VHS 0.12.1:** ttyd'nin macOS ikilisi yok. Bu yüzden ancak kullanıcı `sudo xcodebuild -license accept` çalıştırdıktan sonra `HOMEBREW_NO_ANALYTICS=1 brew install vhs` (~150 MB) ile kurulur. `vhs publish` kullanılmaz.
- **README:** GitHub .mp4, .mov ve .webm kabul eder (ücretsiz planda 10 MB). GIF yalnız istenirse yapılır.

## Monospace yazı tipi (terminal, kod)
- Stüdyoda yerel mono yazı tipi yok (`varliklar/yazitipleri`: Inter, Cormorant, Great Vibes). Registry terminal blokları Google Fonts ya da sistem yazı tipi çekebilir.
- Varsayılan: JetBrains Mono (OFL-1.1). Kullanıcıya boyutu söylenerek kurulur: `cd $MEDYA && npm i --save-exact @fontsource/jetbrains-mono@5.3.0` (paket 1,8 MB). Ardından `files/jetbrains-mono-latin{,-ext}-400-normal.woff2` ve lisans `kompozisyon/fonts/` altına kopyalanır.
- Kurulmazsa açık karar: `font-family: Menlo, "SF Mono", monospace`. Bu makinede çizilir ama başka makinede deterministik değildir; `KARARLAR.md`'ye yazılır.

## Arayüz yakalama
- **Ekran görüntüsü verildiyse yakalama gerekmez.**
  - Yoğunluk `sips -g pixelWidth -g pixelHeight <png>` ile okunur; `medya incele` video içindir.
  - En büyük yakınlık = kaynak px / ekrandaki px.
- **Web uygulaması:**
  - Kurulu puppeteer-core 25.12.0 kullanılır: `page.screencast({path: 'x.webm', fps, crop, scale})`. Bu yol stüdyoda denenmedi.
  - Alternatif: bir demo klasöründe `npm i -D playwright@1.63.0`, `channel: 'chrome'`, `page.screencast` + `showActions`. 2x DPR keskinliği kanıtlanmadı.
  - **Boyut her zaman açıkça verilir** (`size`/`scale`): Playwright varsayılanı 800×800'e sığdırır ve JPEG karelerden WebM yapar → bulanık. Yoğunluk ffprobe ile ölçülür, yakınlaştırılmış bir kare Read ile açılır.
  - En keskin yol: `screencapture -v -C -k` ya da arayüzü HyperFrames'te yeniden kurmak.
  - Her eylem `{t, x, y, w, h}` olarak `actions.json`'a yazılır.
  - Kompozisyondan önce `medya cfr` uygulanır; çizimde `--video-frame-format png` verilir.
- **macOS uygulaması:** `screencapture -v`. Ekran Kaydı izni gerekir; izni yalnız kullanıcı verebilir.

## Lottie / dotLottie — uygulama içi animasyon
- **Çalışma zamanı (MIT):** lottie-web 5.13.0 kökte kurulu (Remotion Lottie eki, 2026-10-09). dotlottie-web gerekiyorsa
  `cd $MEDYA && npm i --save-exact @lottiefiles/dotlottie-web@0.80.0` (7,4 MB). dist dosyaları `vendor/` altına kopyalanır.
- **Uygulamalarda:** lottie-ios, lottie-android, lottie-react-native ya da dotLottie oynatıcıları.
- **Yazım:**
  - Şekil katmanlı Lottie JSON elle ya da kodla yazılır. Örnek üretici (trim path ve ölçek anahtar kareleri):
    `sistem/devam/remotion-3b/2026-10-09/lottie_uret.py`.
  - `python-lottie[gif]` arm64'te kurulamıyor.
  - After Effects, LottieFiles Creator ve Rive hesap ya da ücret ister; kullanılmaz.
- **Denetim:**
  - `fr`, `ip`, `op`, `w`, `h` alanları denetlenir.
  - Aynı kareler lottie-web ve dotlottie-web ile HyperFrames'te çizilir; SSIM ≥ 0,98 olmalı.
  - Bayt bütçesi: arayüz için ≤100 KB.

## GIF, WebP, APNG (bu stüdyoda çalıştırıldı)
```
ffmpeg -nostdin -y -i x.mp4 -vf "fps=20,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" -loop 0 x.gif
ffmpeg -nostdin -y -framerate 25 -i kareler/frame_%06d.png -plays 0 -f apng x.png
ffmpeg -nostdin -y -framerate 25 -i kareler/frame_%06d.png -c:v libwebp_anim -lossless 1 -loop 0 x.webp
img2webp -loop 0 -lossy -q 75 -d 40 kareler/frame_*.png -o x.webp
```
- Düz arayüz görüntüsünde `bayer` titreşimi kullanılır. HyperFrames'in GIF'i `sierra2_4a` kullanır.
- gifski ve gifsicle yalnız Homebrew ile kurulabiliyor.
- Kişisel çıkartma sınırları:
  - Telegram: VP9 WebM, bir kenar 512 px, ≤3 sn, ≤30 fps, ≤256 KB.
  - WhatsApp: 512×512 WebP, ≤500 KB (üçüncü taraf kaynağı).

## Mağaza önizlemesi
- **App Store:**
  - 15–30 sn, ≤30 fps.
  - H.264 High ≤L4.0, 10–12 Mbps; AAC 256k stereo.
  - Boyut: 886x1920 / 1920x886 (iPhone), 1200x1600 (iPad), 1920x1080 (Mac).
  - Kodlama: `ffmpeg -nostdin -i usta.mov -c:v libx264 -profile:v high -level:v 4.0 -b:v 11M -maxrate 12M -bufsize 24M -pix_fmt yuv420p -r 30 -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart onizleme.mp4`
  - Doğrulama: ffprobe JSON.
- **Google Play:** önizleme bir YouTube bağlantısıdır; öne çıkan grafik 1024x500.

## Lisans özeti
| Araç | Lisans | Ticari çıktı |
|---|---|---|
| HyperFrames | Apache-2.0 | evet |
| GSAP 3.15 + eklentiler | Standard no-charge | evet (Webflow rakibi araç hariç) |
| Remotion 4.x (+ @remotion/three, @remotion/lottie) | Remotion License (@remotion/three package.json'da MIT; çekirdeğe bağlı) | yalnız kapı geçerse |
| Manim, Three.js, lottie-web, dotlottie-web | MIT | evet |
| Blender | GPL (uygulama) | evet |
| asciinema, agg | GPL-3 | evet (bağımsız CLI) |
| Registry GLB/ikon varlıkları | belirsiz | hayır |
| MusicGen (`audio.mjs` yedeği) | CC-BY-NC | hayır |
