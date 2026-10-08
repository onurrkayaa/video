# HyperFrames — ajan için özler (0.8.124)

Motor sözleşmesinin tamamı satıcı becerilerindedir: `hyperframes-core` (yapı, `data-*`), `hyperframes-animation`
(kurallar, blueprint'ler, adaptörler), `hyperframes-keyframes` (punch-in, kamera, maske, SVG), `hyperframes-registry`.
Bu dosya stüdyoya özgü düzeltmeleri ve ölçülmüş tuzakları içerir. Her kabukta önce
`source /Users/onurkaya/Projects/video/ortam.sh`.

## Proje
```
cd $MEDYA/projeler/<tarih-ad>/calisma
HYPERFRAMES_SKIP_SKILLS=1 hyperframes init kompozisyon --non-interactive --example=blank --resolution=landscape
mkdir -p kompozisyon/vendor kompozisyon/fonts
cp $MEDYA/varliklar/js/gsap.min.js kompozisyon/vendor/            # GSAP 3.15.0
cp $MEDYA/node_modules/gsap/dist/{DrawSVGPlugin,MorphSVGPlugin,MotionPathPlugin,SplitText,CustomEase}.min.js kompozisyon/vendor/
cp $MEDYA/varliklar/yazitipleri/inter-latin{,-ext}-{400,600}-normal.woff2 $MEDYA/varliklar/yazitipleri/OFL-Inter.txt kompozisyon/fonts/
```
- `HYPERFRAMES_SKIP_SKILLS=1` olmadan `init` her çalıştırmada becerileri GitHub HEAD'e karşı tazeler (`keepSkillsCurrent` →
  `updateSkills`). `ortam.sh` ve `~/.claude/settings.json` (env) bunu 1 yapar; kanca bu alt süreci görmez, tek koruma bu
  değişkendir. Ortamı yüklenmemiş bir kabuktan da çağrılabileceği için komutta yine açık yaz.
- `--resolution` seçenekleri: `landscape`, `portrait`, `square`, `*-4k`. App Store gibi başka bir boyut gerekirse kökteki `data-width` ve `data-height` elle yazılır.
- **Boş şablonda düzeltilecekler** (`init` çıktısı okunarak doğrulandı):
  - `<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/…">` satırı `vendor/gsap.min.js` ile değiştirilir.
  - `<html lang="en">` ve örnek `<h1>Title</h1>` kaldırılır. Yazı yoksa h1 tamamen silinir; Türkçe yazı varsa `lang="tr"` olur.
  - Köke `data-fps` eklenir; yoksa çizim 30 fps varsayar.
  - Arka plan `#root`'a verilir. Yalnız `body`/`html` arka planı GIF ve png-sequence'ta saydam çıktı (ölçüldü). GitHub'ın beyaz zemininde koyu terminal kaybolur.
  - `init` kompozisyon içine `CLAUDE.md` ve `AGENTS.md` (8 KB) yazar: `preview --background`, `npm run publish`, `skills update`, `docs` önerir. Claude Code alt klasördeki CLAUDE.md'yi yüklediği için ikisi silinir (`rm kompozisyon/CLAUDE.md kompozisyon/AGENTS.md`; kullanıcı dosyası değil, `init` ürünü).
  - `package.json`'dan `publish` ve `dev` betikleri silinir. `npm run …` kullanılmaz; doğrudan `hyperframes <komut> kompozisyon` çalıştırılır.
  - `hyperframes.json` içindeki `$schema` ve registry adresi beklenir, dokunulmaz. URL denetimi yalnız çalışan dosyalarda yapılır: `grep -rnoE "https?://[^\"' )]+" kompozisyon --include='*.html' --include='*.js' --include='*.mjs' --include='*.css' | grep -v w3.org` boş olmalı.
- **Ölçülmüş tuzaklar (0.8.124):** GIF fps'i 10, 20, 25 ya da 50 olmalı; 15 fps'te gecikmeler 60/70 ms karışık çıktı. Türkçe yazı varsa `<html lang="tr">`.
- **Yalnız CSS ya da WAAPI ile animasyonlanan kök** (ör. yükleniyor animasyonu) GSAP zaman çizelgesi kaydetmez. Bu durumda köke `data-no-timeline` konur; konmazsa lint `missing_timeline_registry` hatası verir ve her çizime 45 sn bekleme eklenir.
- **GSAP eklentileri:** `gsap.registerPlugin(DrawSVGPlugin)` ile kaydedilir. Kullanım: `drawSVG: "0%" → "100%"`, `morphSVG`, `motionPath`. Kapalı bir SVG yolunda DrawSVG başlangıç köşesinde çentik bıraktı. `stroke-linejoin: round` ile dene, sonra snapshot'la doğrula.
- **GSAP lisansı:** Standard "no charge" lisansı; ticari kullanım serbest. Tek yasak, Webflow'un görsel animasyon aracıyla rekabet eden bir araç yapmak. Ürün içinde OSI lisansı gerekiyorsa anime.js (MIT) kullanılır.

## Registry
- Arama: `hyperframes catalog --query "<sözcük>"`. Yerel sözcük eşleşmesiyle çalışır. `--on-device` 33 MB'lık bir model indirir, bu yüzden önce kullanıcıya sorulur. Çıktıdaki `npx hyperframes feedback` önerisi uygulanmaz.
- Kurulum: `hyperframes add <öğe> --dir kompozisyon --no-clipboard --json`.
- **Kurduktan sonra:**
  1. `grep -rnoE "https?://[^\"' )]+" kompozisyon/compositions | grep -v w3.org` çalıştırılır. Örneğin `code-terminal-run` GSAP'ı jsdelivr'den çekiyordu; bulunan adres `vendor/` yoluyla değiştirilir.
  2. Kod Apache-2.0'dır. Gömülü GLB, cihaz modeli, ikon ve görsellerin lisans bilgisi yoktur (`vfx-iphone-device`, `ios26-liquid-glass`): iş için kullanılmaz.
  3. Kaynağı ve lisansı `KARARLAR.md`'ye yazılır.
- İşe yarayan öğeler:
  - Terminal: `terminal-simulator`, `code-terminal-run`, `code-snippet-apple-terminal-pro`.
  - Kod: `code-typing`, `code-diff`, `code-morph`.
  - Ayrıca `motion-blur`, `cinematic-zoom`, `data-chart`.
- Blueprint'ler (`hyperframes-animation/blueprints/`): `cursor-ui-demo`, `device-surface-showcase`, `zoom-out-workspace-reveal`, `logo-assemble-lockup`, `dataviz-countup`, `camera-journey`, `spatial-pan-stations`.

## Adaptörler
- **Three.js** (`hyperframes-animation/adapters/three.md`):
  - Kurulum gerekir ([araçlar](araclar.md)).
  - Satıcı örneğindeki jsdelivr importmap yerel `vendor/three/` yoluna çevrilir.
  - Kökte `data-duration` zorunludur.
  - Sahne `hf-seek` olayında, `window.__hfThreeTime` zamanına göre çizilir; `requestAnimationFrame` kullanılmaz.
  - Çizimde `--browser-gpu` verilir. Günlükte SwiftShader yazıyorsa çizim çok yavaştır; ağır 3B Blender'a taşınır.
- **Lottie:** `autoplay: false`, açık bir `loop` ayarı ve `window.__hfLottie.push(anim)`.
- **CSS @keyframes / WAAPI:** zamana göre deterministik aranır (ölçüldü: 1,2 sn periyotlu dönüşte 0 ile T kareleri piksel piksel aynı çıktı).

## Çizim
| Amaç | Komut |
|---|---|
| Taslak | `hyperframes render kompozisyon -o ../cikti/taslak.mp4 --quality draft` |
| Son (grafik) | `… --quality delivery --strict -o ../cikti/x.mp4` |
| Ekran kaydı / çekim içeren son | bir önceki satıra ek olarak `--video-frame-format png` (önce `medya cfr`) |
| Saydam bindirme | `--format mov` (ProRes 4444) ya da `--format webm` |
| GIF | `--format gif --fps 20 --gif-loop 0` |
| Kareler | `--format png-sequence --fps 25 -o ../calisma/kareler` |
| Uzun iş | `--video-bitrate 8M`; disk için `--frames-cache-dir off`, sonra `hyperframes clean` |

- Aynı anda tek çizim yapılır: her worker yaklaşık 256 MB'lık bir Chrome'dur, makinede 16 GB RAM var.
- `--skill` bayrağı yalnız telemetriye etiket ekler; kullanılmaz.

## Doğrulama ayrıntısı
- **Kesin kesim anları:** `cd kompozisyon && hyperframes timeline --json` klip başlangıçlarını verir. Snapshot'lar kesimden −0,1 ve +0,2 sn sonra, geçişlerin ise tam ortasında alınır. `snapshot` sona kendiliğinden bir kare ekler; yalnız istenen anlar için `--no-end`.
- **Hareket denetimi:**
  - `hyperframes keyframes kompozisyon --json` her tween'in süresini ve ease'ini listeler; bunlar [ilkeler](ilkeler.md)'e göre denetlenir.
  - `hyperframes keyframes kompozisyon --selector "#x" --shot ../analiz/k.png` soğan kabuğu görüntüsü üretir. Aralıklar uçlarda sıklaşmalıdır; eşit adım lineer demektir.
  - Canvas ve WebGL için `--ghost`, 3B derinlik için `--angle iso` eklenir.
- **Yazı keskinliği:** `snapshot --describe false --at T --zoom "#hedef" --zoom-scale 3`.
- **Seçenek karşılaştırma:** `hyperframes compare a b c --at 0.6 --labels "A,B,C" --out ../analiz/secenekler.png`.
- **Determinizm:** iki çizim `--no-browser-gpu --experimental-fast-capture=false` ile alınır. Her biri için `ffmpeg -nostdin -i dN.mp4 -map 0:v -f framemd5 dN.md5`, sonra `diff`. Fikstürde 45/45 kare aynı çıktı. Donanım GPU'su ile bire bir aynılık beklenmez.
- **Önizleme:** `hyperframes preview` yalnız kullanıcı isterse açılır.
