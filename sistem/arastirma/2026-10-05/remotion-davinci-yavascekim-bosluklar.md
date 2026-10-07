# Remotion, DaVinci/NLE, ağır çekim motoru ve kapsam boşlukları (2026-10-05)

> Girdiler: `sistem/devam/ham/arastir-remotion.json` + `dogrula-remotion.json`, `arastir-davinci.json` + `dogrula-davinci.json` (şüpheci doğrulama), `arastir-bosluk.json` (kapsam incelemesi, doğrulanmadı), ana ajanın ağır çekim ölçümü (`sistem/devam/yavas-cekim/`). Doğrulayıcının çürüttüğü iddialar çıkarıldı ya da onun değeriyle düzeltildi.
> Etiketler: **[ölçüm]** araştırmacı bu Mac'te ölçtü · **[doğrulandı]** bağımsız doğrulayıcı yeniden ölçtü/okudu · **[düzeltildi]** doğrulayıcı çürüttü, onun değeri yazılı · **(doğrulanmadı)** belirsiz ya da tek kaynak · **[yerel]** düz yerel olgu · **[yazım anı]** bu belge yazılırken yerelde yeniden bakıldı.

## Sonuç

- **Remotion (karar, uygulandı):** lisans kapılı İKİNCİ kompozisyon motoru; varsayılan HyperFrames kalır. `remotion@4.0.533` stüdyo köküne sabit (4.0.533 uzun render'da giderek yavaşlamayı düzeltiyor); şablon `sablonlar/remotion` (HyperFrames Chrome'u `setBrowserExecutable` + yedek, rspack, angle, bt709, eşzamanlılık 4); `medya proje yeni … --motor remotion`; BRIEF'te "Lisans bağlamı"; vendor beceri `remotion-best-practices` @0b5db9d + stüdyo kuralları; PreToolUse kancası bulut, lisans anahtarı, yükseltme, `npx skills`, `create-video` ve yasak `@remotion` paketlerini engelliyor; sınama şablonu çiziyor. 3D/Lottie kurulmadı (istek gelince, ~62 MB).
- **DaVinci (karar):** "Claude Resolve'da kurgu yapar" yolu gerçek, ama yalnız ücretli Resolve Studio 21.1'in yerleşik MCP'siyle (File > Setup AI Assistants; ~295 $) → `resolve-studio-mcp` etkin=false, yalnız kullanıcı açıkça isterse. Ücretsiz Resolve ve Kdenlive kullanıcının kuracağı uygulamalar (tur=uygulama, etkin=false). `medya nle` doğrulamaya göre düzeltildi, `otio-fcpx-xml-adapter` kaldırıldı. Sonraya: `--paket` (.otioz), `--pisir`, FCP7 xmeml, Resolve_OTIO.
- **Ağır çekim (karar, son ölçümle):** dogal → ≤2000 px kaynakta RIFE v4.6 (`arac/rife`, 36 MB) önce, 4K'da Apple önce → diğeri → minterpolate; başarısız ya da asılan basamak atlanır. Gerçek kamerada RIFE en iyi (el kamerası 37,7 / Apple 36,4 dB).
- **Neural Engine bekçisi:** bu Mac'te `ANECompilerService` 18 saat %100 CPU'da takılı bulundu; Apple ML komutları artık asılmıyor, çözümü söyleyen bir hatayla hemen düşüyor.
- **İlk 5 kapsam boşluğu** (kapsam incelemesi, doğrulanmadı; 1–4'ün hâlâ açık olduğu yazım anında yerelde görüldü):
  1. `medya sahneler`: PySceneDetect kırık (`import cv2` hata veriyor, komut sessizce ffmpeg'e düşüyor). Onarım ~120 MB yeniden kurulum; kullanıcı kararı gerekmez.
  2. İndirmesiz komut paketi (sabitle, gurultu, eski = bwdif + Apple LL-SR 2x, dikey, renk-esle, bosluk-kes, gizlilik, plaka, App Store ön ayarı): 0 MB; karar gerekmez.
  3. Uzun ve çekim ağırlıklı işler için ffmpeg EDL çizicisi (45 dk HyperFrames'te ~1,9 saat): 0 MB; karar gerekmez.
  4. Sessiz kurulum kapısı (`remove-background` sormadan ~394 MB, embedded-captions `uvx whisperx` ile ~2 GB kuruyor): 0 MB; karar gerekmez.
  5. Türkçe dış ses (VoxCPM2 4-bit): ~3 GB; **kullanıcı kararı**. Kullanıcıya ayrıca: görsel ortamı (~400 MB, boyut söylenip sorulur), Xcode lisansı (sudo), işverenin kişi sayısı (Remotion'un iş kullanımı).

## Remotion: lisans kapılı ikinci motor

**Karar (2026-10-05, uygulandı).**
- Motor: `remotion` ve `@remotion/*` **4.0.533**, `--save-exact` ile stüdyo köküne. 4.0.533 (2026-10-05T07:27Z) "@remotion/renderer: Fix progressive slowdown in long renders" (#11912) ve "@remotion/licensing: Add idempotency keys to billable events" getiriyor [doğrulandı] (https://github.com/remotion-dev/remotion/releases). Bu bölümdeki ölçümler 4.0.532 ile yapıldı.
- Şablon `sablonlar/remotion`: HyperFrames'in Chrome Headless Shell'i `Config.setBrowserExecutable` ile (bulunamazsa yedek yol), rspack, `angle`, `bt709`, eşzamanlılık 4. `medya proje yeni … --motor remotion` şablonu kopyalar. BRIEF.md'de **Lisans bağlamı** alanı (aşağıdaki kapı).
- Beceri: resmî `remotion-best-practices` @0b5db9d vendor olarak, başında stüdyo kuralları bloğu. Beceri commit'i 4.0.532 ile eşlenik, motor 4.0.533: bir yama farkı; sonraki yükseltmede ikisi aynı sürüme sabitlenir.
- Kanca (PreToolUse) engelliyor: `remotion lambda|cloudrun|upgrade|skills`, `--public-license-key`/`--license-key`, `create-video`, `npx skills`, `@remotion/(web-renderer|google-fonts|lambda|cloudrun|vercel|sfx)` kurulumu. Kanca yalnız komut satırını görür; kod içindeki `Config.setPublicLicenseKey`, `remotion.media/` uzak varlıkları ve `@remotion/mcp` kancada yok [yazım anı] → stüdyo kuralları ve `src/` taraması (`https?://|google-fonts|web-renderer|Math.random`) ile yakalanmalı.
- Sınama şablonu çiziyor. 3D/Lottie ekleri kurulmadı.
- Henüz yok [yazım anı]: `medya remotion` uyarlayıcısı (`medya/komutlar/` altında Remotion'u yalnız `proje.py` anıyor). Remotion yerel ikiliyle çağrılır: `$MEDYA/node_modules/.bin/remotion` (`npx` değil: paket yerelde yoksa npm'e gider).

### Sürüm ve 5.0
- npm: latest 4.0.533; 4.0.532 (2026-10-01) bir önceki; 1269 sürüm, 2026-08-26 ile 10-01 arasında 15 sürüm; 5.x yok; `alpha`=4.1.0-alpha12 (2023) bayat [doğrulandı] (https://registry.npmjs.org/remotion).
- 5.0'ın tarihi yok: PR [#3750](https://github.com/remotion-dev/remotion/pull/3750) 2024-04-22'den beri açık, son güncelleme 2026-08-10 [doğrulandı]; [#3310](https://github.com/remotion-dev/remotion/issues/3310) açık; [5-0-migration](https://www.remotion.dev/docs/5-0-migration) "not yet released" diyor; 4.0.532'de `ENABLE_V5_BREAKING_CHANGES=false`.
- 5.0'da planlananlar:
  - Lisans: yükleniciler ekip sayısına girer, lisans yeni Şartlar'a bağlanır, Company License'ta telemetri zorunlu. Migration belgesi ücretsiz kullanıcıya da `"free-license"` anahtarını "Required action" olarak yazıyor [doğrulandı]. Bu değer her render'da remotion.pro'ya POST gönderir; 5.0'a geçerken lisans kapısında ayrıca ele alınır.
  - Varsayılanlar: `gl='angle'` (yedek swangle), renk uzayı `bt709`, Sequence'larda 1 s premount.
  - API: `@remotion/google-fonts` ağırlık ve alt küme ister; layout-utils `validateFontIsLoaded=true`; `selectComposition`/`getCompositions` inputProps ister, `bundle()` seçenek nesnesi alır; TransitionSeries `layout='none'` ve measureSpring from/to kalkar; path örneklemesi sonda null döner; `getVideoMetadata` renderer'dan kalkar.
  - Yayımı kesilen paketler: `@remotion/light-leaks`, `starburst` (yerine `@remotion/effects`), `media-parser`, `webcodecs` (yerine Mediabunny).
- Pratik: 4.x kodunu şimdiden 5.0 tarzında yaz: `bt709` ve `angle` açık, `premountFor`, `@remotion/effects`, media-parser yok.

### Lisans
- **4.x LICENSE.md (bugün geçerli)** [doğrulandı]: ücretsiz lisans birey, "for-profit organization with up to 3 employees", kâr amacı gütmeyen kuruluş ve henüz ticari kullanmayan değerlendirici içindir. Ticari dahil video ve görsel üretimi serbest. Remotion türevini satmak, kiralamak ya da yeniden lisanslamak yasak. Diğer herkes Company License alır (https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).
- npm lisans alanları paketten pakete değişiyor: çekirdek "SEE LICENSE IN LICENSE.md"; fonts, gsap, three, paths, shapes, noise, captions, zod-types, studio ve sfx MIT; transitions ve effects "UNLICENSED"; light-leaks ve media-parser "Remotion License". Hepsi `remotion` çekirdeğine bağlı olduğu için yığının tamamı fiilen Remotion License altında.
- **İşveren adına, çalışan olarak üretim:** kullanıcı işverendir. İşveren 4 ve üzeri kişiyse lisans ücretlidir, stüdyo kuralı gereği HyperFrames kullanılır. Bugünkü dayanak 4.x LICENSE.md ("up to 3 employees") ve [FAQ](https://www.remotion.dev/docs/license/faq). "Seat … creating media for their organization" ve TeamSize tanımları [v5.0 Şartları](https://www.remotion.dev/docs/terms)'ndan; bu Şartlar 5.0 ile yürürlüğe girecek [doğrulandı; güven orta-yüksek].
- **Serbest iş, yalnız bitmiş dosya teslimi:** projeyi kendi makinesinde işletip müşteriye yalnız MP4 teslim eden ≤3 kişilik ekip ücretsiz kullanır; müşteri sayılmaz. Müşteri Remotion kodunu alır, sahiplenir ya da çalıştırırsa iki tarafın kişi sayısı toplanır ve lisansı fikri mülkiyet sahibi alır [doğrulandı; FAQ bugün geçerli].
- **Fiyatlar** ([remotion.pro/license](https://www.remotion.pro/license), 2026-10-05) [doğrulandı]: Creators 25 $/ay/koltuk; Automators 0,01 $/render, 1000'lik dilimlerle, en az 100 $/ay; Enterprise 500 $/ay'dan başlıyor; iade yok. FAQ'ın otomasyon tanımı `npx remotion render/still`'i programla çağırmayı da kapsıyor. Bu yüzden şirket kullanımında `medya` sarmalayıcısı Automators planına düşebilir. Ücretsiz lisansta otomasyon serbest.
- **5.0 Şartları** [doğrulandı]: yükleniciler ve yarı zamanlılar sayılır. Yazılı izin yoksa son kullanıcının kendi Remotion kodunu yüklediği render hizmeti yasak. Kâr amaçlı şirketin iç araçları da ticari kullanım sayılır.
- Diğer: `cube()` geçişi ve Editor Starter ücretli ürün. Gömülü FFmpeg 7.1 GPLv2+ (x264/x265, fdk-aac-free; patent lisansı kapsam dışı; https://www.remotion.dev/docs/miscellaneous/ffmpeg-license). Üretilen medya üzerinde Remotion kısıtı yok (Şartlar §Ownership).

**Lisans kapısı (ajanlar için).**
- Remotion yalnız şu işlerde kullanılır: (a) kişisel iş; (b) tek kişilik serbest iş, müşteriye YALNIZ bitmiş dosya; (c) toplam ≤3 kişilik ekip ya da şirket işi; (d) kâr amacı gütmeyen kuruluş işi.
- Şu durumlarda HyperFrames kullanılır: işveren ≥4 kişi; müşteri Remotion kodunu alacak; aynı projede yükleniciler dahil ≥4 kişi çalışıyor.
- "Lisans bağlamı" boşsa sorulur; yanıt yoksa HyperFrames.
- Her durumda:
  - Lisans anahtarı hiç ayarlanmaz, `"free-license"` dahil.
  - Studio'da "Render in browser" ve `@remotion/web-renderer` kullanılmaz. Studio'nun sunucu bağlantısı koptuysa render başlatılmaz, çünkü düğme o durumda client-render'a düşüyor.
  - Google Fonts, remotion.media, `@remotion/sfx`'in CC0 olmayan sesleri, ElevenLabs, MapTiler, Mapbox, Lambda, Cloud Run ve Vercel kullanılmaz.
  - Lisans ve Şartlar incelenmeden 5.x'e geçilmez.

### Ağ ve telemetri

| Tetikleyici | Hedef | Ne zaman | Stüdyo kuralı |
|---|---|---|---|
| `--public-license-key`, `licenseKey`, `Config.setPublicLicenseKey` ("free-license" dahil) | POST https://www.remotion.pro/api/track/register-usage-point (+IP), 1+3 deneme | her başarılı render/still sonrası | Hiç ayarlanmaz. [doğrulandı] Kod: `render-media.js:494-503`, `render-still.js:290-295`. free-license ile sandbox'ta "Failed to send usage event … EPERM"; anahtarsız 0 deneme. CLI render yalnız `--public-license-key`'i okuyor; `--license-key` render'da etkisiz |
| tarayıcı yolu verilmemiş | Chrome Headless Shell 149.0.7790.0 zip (98 MB), storage.googleapis.com → en yakın package.json klasöründe `node_modules/.remotion` | ilk render | şablon HyperFrames Chrome'unu veriyor |
| Studio açık | Node: GET registry.npmjs.org/remotion; tarayıcı: GET bugs.remotion.dev/api/<sürüm> | her bağlanışta; kapatan ortam değişkeni ya da bayrak yok [doğrulandı] | Studio yalnız kullanıcı isterse |
| Studio'da kullanıcı eylemi | Algolia belge araması; api.github.com sürüm notları; fonts.googleapis.com (zaman çizelgesi yazı tipi alanı); remotion.pro/api/validate-license-key | eylemle | bilinçli kullanım |
| Studio "Render in browser", `@remotion/web-renderer` | remotion.pro kullanım olayı + `window.location.origin` + IP | **her zaman**, anahtarsız da [doğrulandı] (https://www.remotion.dev/docs/telemetry) | yasak |
| `@remotion/google-fonts` | fonts.googleapis.com, fonts.gstatic.com | önizleme ve render | yasak → `@remotion/fonts` + yerel woff2 |
| `@remotion/sfx`, beceri örnekleri | https://remotion.media/ (wav, mp4) | render'da | yasak |
| `npx remotion skills add` | `npx skills@1.5.26 add remotion-dev/skills --yes`; skills CLI, DISABLE_TELEMETRY/DO_NOT_TRACK yoksa add-skill.vercel.sh/t ve /audit'e veri gönderir; `update` sabitlemesiz | komutla | engelli |
| `npx remotion upgrade`, `create-video@latest` | npm ve GitHub; upgrade becerileri de günceller | komutla | engelli |
| `@remotion/mcp` | mcp.remotion.dev; kullanımdan kalktı, en erken 2026-08-31'de kapanacak (https://www.remotion.dev/docs/ai/mcp) | — | kullanılmaz |

- Chrome arka plan ağı kapalı açılıyor (`--disable-background-networking --disable-component-update --no-pings --disable-domain-reliability --metrics-recording-only --disable-sync --disable-breakpad`). Compositor ve ffmpeg ikililerinde telemetri adresi yok.
- **LAN'a açıklık:** Studio ve render sırasındaki statik sunucu `::` ya da 0.0.0.0'a bağlanıyor. Studio "Network: http://<LAN-IP>:3999" yazdı. Yalnız localhost'a bağlama seçeneği yok; `--ipv4` yalnız 0.0.0.0'a geçirir. Studio açıkken ve render sürerken public/ yerel ağdan erişilebilir. Önlem: güvenilir ağ ve macOS güvenlik duvarı.
- **Çevrimdışı** [ölçüm]: `sandbox-exec` ile dış ağ kapalıyken şunların hepsi başarılı oldu: hareket, çekim, WebGL efekti, HTML-in-canvas, R3F, ProRes, VideoToolbox, still ve Studio başlatma.

### Tarayıcı
- 4.0.532'de `TESTED_VERSION=149.0.7790.0` [doğrulandı]. HyperFrames 0.8.124'ün tarayıcısı: `~/.cache/hyperframes/chrome/chrome-headless-shell/mac_arm-152.0.7977.30` (193 MB).
- `setBrowserExecutable` ile 152: `<Video>` (60/30 fps), WebGL kanvas, JPEG/PNG ve bt709 render'ları geçti; `.remotion` indirmesi oluşmadı [doğrulandı]. Yazı tipi, R3F, ProRes ve VideoToolbox alt testleri yalnız araştırmacının [ölçüm]'ü.
- Uyarılar: 152, Remotion'un test matrisinde değil. `remotion gpu` bu tarayıcıyla düşüyor [doğrulandı].
- Yedek: `remotion browser ensure` test edilen 149'u indirir (zip 98 MB, açılmış ~190 MB).

### Resmî beceriler
- Depo [remotion-dev/skills](https://github.com/remotion-dev/skills/tree/0b5db9daae40f42c73544d1cc0a8c733bd530eaa): commit 0b5db9d (2026-10-01; ön bilgide `version: 4.0.532`), her sürümde otomatik eşitleniyor.
  - 12 beceri. `remotion-best-practices` öteki 11'ini REFERENCE.md olarak içeriyor (141 dosya, 1,4 MB), tek başına yeterli [doğrulandı].
  - codeload tarball sha256 `1eb509ecc59c68163c171b52cc46fa3d0bd2dddf0d6371af97710004a2d06866` (anlık değer; asıl sabit olan commit SHA'sı) [doğrulandı].
- Lisans: depoda LICENSE dosyası ve package.json lisans alanı yok. MIT dayanağı ayrı depolarda: [claude-code-plugin](https://github.com/remotion-dev/claude-code-plugin) `plugin.json` ve monorepodaki [packages/agent-plugin/LICENSE](https://github.com/remotion-dev/remotion/blob/main/packages/agent-plugin/LICENSE) (güven orta).
- Studio beceri sürümünü `.agents/skills` altında denetliyor, `.claude/skills`'e bakmıyor. WebMCP (Studio ajan araçları) belgeye göre yalnız Codex'te.
- Ajan belgeleri: https://www.remotion.dev/llms.txt ve belge URL'lerinin `.md` sürümü (ikisi de 200 döndü). `/remotion-docs` Algolia kullanıyor; sorguya kullanıcı içeriği konmaz.
- **Ne öğretiyor:**
  - Her şey `useCurrentFrame()` + `interpolate()` ile sürülür. CSS transition, CSS animation ve Tailwind animasyonu kullanılmaz.
  - `Easing.bezier`, `Easing.spring`, `interpolate(..., {output:'perceptual-scale'})`. Transform yerine `scale/translate/rotate` CSS özellikleri.
  - Zamanlı her öğede `premountFor={fps}`. Studio'da düzenlenebilir bileşenler için `Interactive.withSchema`/`Interactive.Div`.
  - Medya için `@remotion/media` `<Video>/<Audio>`; görsel için `CanvasImage/AnimatedImage`.
  - Geçişler `TransitionSeries` + overlay; efektler `effects` prop'u; motion blur için `HtmlInCanvasMotionBlur`. Ayrıca calculateMetadata, zod ve metin ölçümü.
  - Düzen: 1080 genişlikte güvenli alan yanlarda 80 px, üst ve altta 100 px; başlık ≥84 px, destek metni ≥44 px. Stüdyo kuralı: istenmedikçe ekranda yazı yok.
- **Stüdyo kurallarıyla çatışmalar** (sayımlar [doğrulandı]):

| Beceri ne diyor | Stüdyoda |
|---|---|
| "Google Fonts is the recommended way" (remotion-markup, google-fonts.md) | `@remotion/fonts` + yerel woff2. @fontsource latin-ext tek başına A–Z içermiyor, serif yedeğe düşüyor; latin ve latin-ext `unicodeRange` ile birlikte yüklenir (İ Ş Ğ Ç Ö Ü doğru) [ölçüm] |
| ElevenLabs seslendirme (2 dosya) | yasak (ücretli, API anahtarı) |
| MapTiler (59 dosya), Mapbox (8), Cesium ion, Google 3D tiles | yasak; yalnız yerel verili static-map ya da MapLibre |
| remotion.media uzak varlıkları (38 dosya), `@remotion/sfx` | yasak; CC0 olanlar kaynak kaydıyla bir kez indirilir ya da ses kodla üretilir |
| `@remotion/whisper-webgpu` (HF modeli indirir) | `medya yaziya-dok` (mlx-whisper) çıktısı Caption JSON'a çevrilir |
| `create-video@latest` (6 dosya), `npx remotion add/upgrade`, `npx skills update` (2) | yalnız sürümü sabit açık kurulum |
| "Don't render … unless they are very explicit", "open the Studio" (SKILL.md:40, :70) | ajan `remotion still` ya da `render --frames=0,30,90 --image-format=png` + Read ile doğrular, `medya denetle` koşar; Studio yalnız kullanıcı isterse |
| remotion-saas: Lambda, Vercel, Cloud Run | yasak |

- `@remotion/sfx` [doğrulandı]: 32 sesin 25'i myinstants.com kaynaklı ve ses sayfalarında "not explicitly released under a free license" yazıyor. Yalnız 7'si CC0 (freesound/kenney): whoosh, whip, mouse-click, page-turn, shutter-modern, shutter-old, ui-switch. Ana sayfadaki "All files can be used without attribution" ifadesi ses sayfalarıyla çelişiyor. npm'deki MIT yalnız URL listesini kapsıyor (https://www.remotion.dev/docs/sfx).

### Yapı taşları
- Desenler:
  - Öğe başına kaydırma: `spring({frame: frame - i*2, fps, config:{damping:200}})`.
  - Deterministik sapma: `random('seed-i')`. Yumuşatma: `Easing.bezier(0.65,0,0.35,1)`.
  - Kurgu yapısı: `Sequence`, `Series`, `TransitionSeries` + overlay (kesimde ışık sızması).
  - Veri güdümlü süre: `calculateMetadata`. Parametreli şablon: zod şeması.
- `@remotion/transitions` (https://www.remotion.dev/docs/transitions/presentations):
  - 20 sunum. Klasik: fade, slide, wipe, flip, clock-wipe, iris, none, push-cut.
  - 12'si HTML-in-canvas shader'lı: blur-slide, book-flip, cross-zoom, crosswarp, dissolve, dreamy-zoom, film-burn, linear-blur, ripple, swap, zoom-blur, zoom-in-out.
  - Zamanlama `linearTiming`, `springTiming`. `cube()` ücretli.
- `@remotion/effects` (https://www.remotion.dev/docs/effects/api):
  - ~70 GPU efekti: chromatic-aberration, color-correction, lut, glow, halftone, light-leak, light-trail, noise, vignette, zoom-blur, starburst, shine, scanlines, tv-signal-off, levels, white-balance…
  - Solid, Video, Img, HtmlInCanvas ve shapes üzerinde `effects` prop'u ile uygulanır; özel efekt `createEffect()` ile.
  - `@remotion/light-leaks` yerine `lightLeak()` (`@remotion/effects/light-leak`) [ölçüm: WebGL ile çalıştı].
- `@remotion/motion-blur`:
  - `HtmlInCanvasMotionBlur` (4.0.529+): 16 örnekte pürüzsüz [ölçüm].
  - `CameraMotionBlur`: 8 örnekte basamaklı hayalet görüntü. Animasyonlu değer çocuk bileşende `useCurrentFrame` ile okunmazsa hiç bulanıklık oluşmuyor [ölçüm].
  - `Trail`.
- `@remotion/gsap` `useGsapTimeline` (MIT, 4.0.517+): duraklatılmış GSAP zaman çizelgesini kareye sarar, yani HyperFrames'teki GSAP bilgisi taşınır [ölçüm: doğru render] (https://www.remotion.dev/docs/gsap).
- `@remotion/three` (R3F): `angle` ile render edildi, 60/60 deterministik [ölçüm].
- Diğer paketler: lottie, noise, paths (evolvePath, interpolatePath), shapes, layout-utils (fitText, measureText), animation-utils, captions (Caption tipi, TikTok tarzı sayfalar), rough-notation, svg-3d-engine, mac-cursors, rounded-text-box, zod-types.
- Dürüst not: görsel tavan HyperFrames ile aynı, çünkü ikisi de headless Chrome'da çiziyor. Fark birinci taraf yapı taşlarında ve React/TSX tür denetiminde.

### Proje düzeni ve ayarlar
```
projeler/<p>/calisma/remotion/
  package.json      {"private":true,"type":"module"}   # klasörü Remotion kökü yapar; public/, config ve Chrome indirme yeri projeye taşınır
  tsconfig.json     # ZORUNLU: yoksa CLI .ts girişini reddediyor [ölçüm]
  remotion.config.ts
  src/index.ts      # registerRoot(Kok)
  src/Kok.tsx, src/sahneler/*.tsx
  public/           # woff2 (latin + latin-ext), HARD-LINK çekim, ses
  out/
```
- Modüller `$MEDYA/node_modules`'tan çözülüyor [ölçüm].
- Araştırmacının sınadığı config (şablon bunun üzerine kuruldu):
```ts
import {Config} from '@remotion/cli/config';
import {readdirSync} from 'node:fs'; import {homedir} from 'node:os'; import {join} from 'node:path';
const k = join(homedir(), '.cache/hyperframes/chrome/chrome-headless-shell');
const s = readdirSync(k).filter((d) => d.startsWith('mac_arm-')).sort().at(-1);
if (!s) throw new Error('HyperFrames Chrome bulunamadı');
Config.setBrowserExecutable(join(k, s, 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell'));
Config.setRspack(true);                     // ~0,6 s paketleme, kalıcı önbellek yok
Config.setChromiumOpenGlRenderer('angle');  // WebGL belirgin hızlı
Config.setColorSpace('bt709');              // yuv420p, tv, bt709 etiketli çıktı
Config.setConcurrency(4);
Config.setOverwriteOutput(false);           // kullanıcı dosyasının üzerine yazma
// Lisans anahtarı ASLA ayarlanmaz.
```
- **public/ ve symlink** [doğrulandı]:
  - Göreli ve mutlak symlink, 404 ve "Could not extract frame from compositor" ile render'ı düşürüyor.
  - Hard link çalışıyor (`ln projeler/<p>/kaynak/x.mp4 …/public/x.mp4`) ve kaynak salt okunur kalıyor.
  - CLI render public/'i kopyalamıyor, bağlıyor (`symlinkPublicDir`); büyük çekimde disk kopyası oluşmuyor. Bundler'ın copy-dir'i içteki symlink'leri symlink olarak taşıdığı için 404 alınıyor.
- **Paketleme önbelleği** [doğrulandı]: webpack `node_modules/.cache/webpack` her paketlemede ~18 MB büyüyor (10 paketlemede 183 MB, ~30'da ~450 MB). `--rspack` ile paketleme 0,6–0,7 s sürüyor, önbellek 0 MB; çıktı webpack ile kare kare aynı.
- **Kurulum** [doğrulandı, 4.0.532]:
  - Önerilen 17 paket: 262 npm paketi, 234 MB, 18 s. 3D/Lottie ile ~297 MB [ölçüm].
  - Yaşam döngüsü betiği olan tek paket `esbuild@0.28.1` (postinstall). `allowScripts`'e `"esbuild@0.28.1": true` eklenir ya da `npm install-scripts approve` çalıştırılır.
  - Stüdyo kökünde çözümleme ERESOLVE vermiyor. esbuild 0.28.1 `@remotion/bundler/node_modules` altına iniyor, kökte HyperFrames'in 0.25.12'si kalıyor. zod 4.5.4 kökte; chromium-bidi'nin zod 3.25.76'sı iç içe kalıyor.
  - Kurulumdan sonra bir `hyperframes render` duman testi önerildi.
- Komutlar (yerel ikiliyle):
  - `remotion render src/index.ts <Id> out/x.mp4 --color-space=bt709 [--image-format=png] [--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le]`
  - `remotion still src/index.ts <Id> out/k.png --frame=90`
  - `remotion render … out/kareler --frames=0,30,90 --image-format=png`
  - `remotion compositions`; `remotion versions` ("All packages have the correct version" demeli)

### Kalite, hız, doğruluk
- **Varsayılanlar** [doğrulandı]:
  - Video ara karesi JPEG kalite 80; still'de PNG. h264 CRF 18.
  - Renk uzayı "default" (BT.601 matrisi) → çıktı yuvj420p, pc, bt470bg. Yalnız `--image-format=png` → yuv420p ve renk etiketi YOK. `--color-space=bt709` → yuv420p, tv, bt709.
  - Eşzamanlılık `round(min(8, max(1, cpus/2)))`, yani M2'de 4. Ses AAC 48 kHz stereo.
- **Çekim kalitesi** [düzeltildi]: araştırmacının "PNG + bt709 → VMAF 95,80'den 99,54'e, süre ~1,9 kat" sayıları yinelenemedi. Doğrulayıcının ölçüm koşulları: testsrc2 + gren, 1080p30, 90 kare, CRF 18, kare hizası 90/90, aralık ve matris dönüşümü doğru yapıldı.

| Varyant | VMAF ort / en kötü kare |
|---|---|
| JPEG + default | 97,78 / 92,98 |
| PNG + default | 97,44 / 93,23 |
| JPEG + bt709 | 96,97 / 93,08 |
| PNG + bt709 | **98,80 / 95,06** |

  - Süre 17,75 s'den 22,06 s'ye çıktı (×1,24, paketleme dahil).
  - Matris dönüşümü yapılmadan karşılaştırınca JPEG + default 65,63'e düşüyor. Yani VMAF farkını büyük ölçüde renk matrisi ve aralık işlemesi belirliyor.
  - **Kural:** bt709 doğruluk için zorunlu. "default" BT.601 matrisiyle kodluyor; PNG ile çıktı etiketsiz kalıyor ve HD oynatıcı bt709 varsayınca renk kayıyor. Bu yüzden her çağrıda `--color-space=bt709` açıkça verilir, config'e güvenilmez.
  - PNG ikincil: bu ölçümde ortalamada ~+1, en kötü karede ~+2 VMAF getirdi. Çekimli son çizimde PNG + bt709, taslakta JPEG yeter.
- **Hız** [ölçüm]:
  - Eşzamanlılık (150 karelik 1080p30 hareket sahnesi): c1 11,8 s, c2 8,6, c4 6,8, c6 6,7, c8 7,3 → fansız M2 için 4. Uzun render'da ısıl kısılma ölçülmedi.
  - `--gl=angle` belirgin hızlı, ama oran sahneye bağlı. Araştırmacı: WebGL/HTML-in-canvas ağırlıklı 80 kare 27,2 s → 7,6 s (×3,6; swangle 44,5 s). Doğrulayıcı: 1280x720 ağır shader 11,38 s → 4,40 s (×2,6) [doğrulandı].
  - Varsayılan gl'nin "Automatic fallback to software WebGL" uyarısı doğrulayıcıda görülmedi (doğrulanmadı).
- **Kodlayıcı** [ölçüm]: `--hardware-acceleration=if-possible` ile h264_videotoolbox ve prores_videotoolbox gerçekten devrede; CRF yerine `--video-bitrate` verilir. ProRes 4444 alfa yazılım kodlayıcısı `prores_ks` ile çıkıyor (yuva444p12le).
- **Çekim doğruluğu:**
  - 60 fps kaynak, 0,5x, 30 fps kompozisyon: 90/90 kare benzersiz ve beklenen sırada [doğrulandı].
  - trimBefore 15 ve 90 + 12 karelik fade: 108/108 kare doğru [ölçüm].
  - `trimBefore` birimi **kompozisyon karesi**: 30 fps'te `trimBefore={30}` → 60 fps kaynağın 60. karesi [doğrulandı].
  - **Remotion ara kare üretmez.** Kaynak fps < kompozisyon fps / hız ise kare tekrarlar: 30 fps kaynak 0,5x'te 60 karede yalnız 30 benzersiz kare (0,0,1,1,…) [doğrulandı]. Ağır çekim önce `medya yavaslat` ile üretilir.
  - `@remotion/media`'da playbackRate perdeyi de değiştirir (https://www.remotion.dev/docs/video-tags).
- **Ses** [ölçüm]: `<Sequence from={45}>` içindeki `<Audio>` 1,50006 s'de başladı (beklenen 1,5 s).
- **Determinizm** (framemd5) [ölçüm]:
  - spring + random(seed) + CameraMotionBlur + WebGL lightLeak sahnesi: 150/150 (varsayılan gl ve angle).
  - R3F 60/60; zoomBlur tek başına 80/80; HtmlInCanvasMotionBlur tek başına 60/60.
  - İç içe HTML-in-canvas (motion blur'lu sahneye zoomBlur geçişi): iki denemede de 77/80 (kare 46–49, PSNR 46–71 dB) ve hata fırlatmadı → iç içe HTML-in-canvas kullanılmaz.
- **Kaynak** [ölçüm]: 1080p çekim render'ında (c4, PNG) node + Chrome + compositor toplam ~1,6 GB RSS. macOS düşük "free memory" bildirince paralel kodlama kendiliğinden kapandı.
- **Determinizm kuralları** (https://www.remotion.dev/docs/flickering, https://www.remotion.dev/docs/using-randomness):
  - `Math.random` ve `Date` yok; yerine `random(seed)`.
  - CSS animation ve transition yok.
  - Asenkron veride `delayRender`; yazı tipi yüklenmeden `measureText` yok.
  - Medya premount edilir; iç içe HTML-in-canvas yok.

### HyperFrames ile karşılaştırma

| Konu | Remotion 4.0.533 | HyperFrames 0.8.124 |
|---|---|---|
| Çizim | headless Chrome + FFmpeg 7.1 (Rust compositor) | headless Chrome + FFmpeg |
| Hareket | ~70 GPU efekti, 20 geçiş, HTML-in-canvas motion blur, R3F, Lottie, GSAP köprüsü, Studio'da düzenlenebilir Interactive | GSAP + adaptörler (Lottie, Three, Anime, CSS, WAAPI, TypeGPU), ~386–394 kayıt öğesi, geçiş kataloğu, 22 blueprint |
| Çekim | kare-doğru; kaynakta yeterli kare varsa hız değişiminde tekrar yok; `<Video>` üzerinde efekt; HEVC'de OffthreadVideo yedeği (belge) | rate < 1'de yeterli kare varken de tekrar (60 fps 0,5x → saniyede 15 benzersiz kare); zamanlar kare ızgarasına oturmazsa ≤1 kare gecikme |
| Ses | örnek doğruluğunda | örnek doğruluğunda; hyperframes-audio miks zinciri daha zengin |
| Ajan araçları | resmî beceri, TS tür denetimi, still / `--frames`; kontak sayfası ve düzen lint'i yok | 21 beceri; lint, check, snapshot, keyframes, compare |
| İş lisansı | birey ve ≤3 kişi ücretsiz; aksi 25 $/koltuk/ay ya da ≥100 $/ay | Apache-2.0 (GSAP standart lisansı) |
| Telemetri | SSR'de anahtarsız yok; tuzaklar yukarıda | `HYPERFRAMES_NO_TELEMETRY=1` |
| Disk | +235–297 MB | ~390 MB |

- **Seçim:** varsayılan HyperFrames. İş videosu ya da lisans belirsizse HyperFrames.
- Remotion ne zaman seçilir:
  1. Kişisel ya da tek kişilik serbest işte yoğun çekim kurgusu, değişken hız, kare-doğru A/V.
  2. zod + calculateMetadata ile veri güdümlü, parametreli seri şablonlar.
  3. React UI bileşenlerinin yeniden kullanıldığı ürün videoları.
  4. Remotion'a özgü efekt ya da geçiş paketinin istendiği işler.
- "Ajanlar HTML+GSAP'i TSX'ten iyi yazar" iddiası kanıtsız; seçimi belirlemez.

### Açık kalanlar
- Bu bölümdeki sayılar 4.0.532 ile ölçüldü. 4.0.533'te çevrimdışı çizim, telemetri yokluğu ve kare eşleme yinelenmedi (doğrulanmadı). Stüdyo sınaması şablonu çiziyor; bu denetimlerin sınamada olup olmadığına bu belgede bakılmadı.
- Test edilmeyenler: gerçek iPhone HEVC/HDR çekimi (belgeye göre HEVC'de OffthreadVideo yedeğine düşülüyor; HDR'de önce `medya sdr`); uzun render'da ısıl kısılma; 4K'da bellek.
- Kullanıcıya sorulacaklar:
  - İşveren kaç kişi; Remotion iş için kullanılacak mı?
  - Serbest işte müşteriye proje kodu gidiyor mu?
  - Studio istenecek mi? LAN'a açık ve npm ile bugs.remotion.dev'e istek atıyor; güvenlik duvarı kararı.
  - 5.0 çıkınca 4.x'te kalınsın mı?

## DaVinci Resolve ve NLE köprüsü

**Karar (2026-10-05).**
- "Claude, DaVinci'de kurgu yapar" yolu gerçek, ama yalnız **ücretli Resolve Studio 21.1**'in yerleşik MCP sunucusuyla (File > Setup AI Assistants; ~295 $). Kayıtta `resolve-studio-mcp` sağlayıcısı **etkin=false**; yalnız kullanıcı açıkça isterse açılır.
- Ücretsiz Resolve ve Kdenlive, kullanıcının kendi kuracağı uygulamalar olarak kayıtlı (tur=uygulama, etkin=false; kurulum kullanıcının kararı).
- İş akışı: ajan kurguyu HyperFrames/ffmpeg ile yapar. Elle ince ayar istenirse `medya nle` .otio/.edl üretir; kullanıcı NLE'de açar, gerekirse .otio olarak geri verir.
- `medya nle` doğrulamaya göre düzeltildi:
  - düz mutlak medya yolu (file:// değil);
  - işaret metni `comment` alanına da yazılıyor;
  - EDL makarası kaynak dosya başına (A001…);
  - ASCII EDL adları ve işaretleri;
  - `FCM: NON-DROP FRAME` başlığı ve `:` zaman kodları;
  - `#`, `%`, `?` içeren medya `cikti/nle/medya/` altına bağlanıyor;
  - `otio-fcpx-xml-adapter` kaldırıldı.
- Sonraya: `--paket` (.otioz), `--pisir`, FCP7 xmeml, Resolve_OTIO efekt metadata.

### Resolve: sürüm, betik ve MCP
- **Sürümler** (https://www.blackmagicdesign.com/api/support/us/downloads.json, https://www.blackmagicdesign.com/api/support/latest-stable-version/davinci-resolve/mac): güncel **21.1.1** (2026-10-02, Mac build 10); 21.1 2026-09-08 (build 14); 21.0.4 2026-08-05; 21.0 2026-06-03.
- **Gereksinimler** [doğrulandı]: 21.1 macOS 15+, Apple Silicon ve 8 GB RAM ister (Fusion 16 GB). Studio'nun gelişmiş AI araçları ≥16 GB, arka plan render ve analizi ≥32 GB ister. Ücretsiz sürümün çıktısı UHD ile sınırlı; 60 fps üstü zaman çizelgesi Studio'da.
- **Ücretsiz 21.1 sürüm notları** [doğrulandı] (https://www.blackmagicdesign.com/support/content/readme/59dd4eef1f4941c29fb8dc48b33f5c87): "Advanced scripting now requires DaVinci Resolve Studio." ve "We have moved the ability to script in Python to the Studio version. The Python API was being used to hack studio features into the free version."
- **Studio 21.1 notları** [doğrulandı] (…/readme/baf7c071c0524fbf8ccc961925c9f443):
  - "Native MCP server for interacting with AI assistants."
  - "Built in Python support for console scripting."; Python 2 desteği yok.
  - Yeni API'ler: geçiş ekleme, klip fade sorgulama/ayarlama, hız değişimi sorgulama/ayarlama, konuşmacı ve zaman bilgili transkript, multicam oluşturma/düzleştirme, ses normalleştirme, render ve proje ön ayarları, medya klonlama, DCTL doğrulama/şifreleme.
- **Studio 21.1.1** (…/readme/dfbb6e4233c144d1b328c109c7ebc11e): quick export, transkripsiyon, sahne kesimi algılama, Smart Reframe ve alt yazı için async API'ler.
- **Ücretsiz 21.1.1** (…/readme/62817b75bdf744718e93909ca6d58f0d): notlarda hâlâ "ApplyGradeFromDRX API option…" var. Yani bir miktar API yüzeyi ücretsizde kalıyor, muhtemelen Lua üzerinden (doğrulanmadı).
- **Özellik tablosu** "DaVinci Resolve 21.1 Studio and iPad Features" (Eylül 2026; https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_Studio_21_Features.pdf) [doğrulandı]:
  - "Scripting API: Studio (7)"; "AI Assistants — Requires an MCP-compatible AI assistant: Studio".
  - Dipnot (7): Mac App Store kurulumlarında yok.
  - "AI Assistants" satırında (7) dipnotu yok. App Store'daki Studio'da MCP'nin durumu belgelenmemiş (doğrulanmadı); betik API'si orada kesin olarak yok.
- **Kılavuz s.106** [doğrulandı] (https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_21.1_Reference_Manual.pdf): "External Scripting Using: (Resolve Studio only) … None, Local, and Network. When set to None, only scripting in the Console window is allowed."

| Yol | Ücretsiz ≤21.0.x | Ücretsiz 21.1+ | Studio 21.1+ (doğrudan indirme) | Mac App Store |
|---|---|---|---|---|
| Başka süreçten betik (`DaVinciResolveScript`, Local/Network) | hayır (2024 tablosunda da Studio) | hayır | **evet** | hayır (dipnot 7, Studio dahil) |
| Workspace > Scripts, Python | evet (ücretsiz 21.0.3.7'de üçüncü taraf ölçümü) | hayır; .py listelenmiyor (birincil kaynak yalnız Linux, #203; macOS için dolaylı; doğrulanmadı) | evet | Lite 21.1+'da Python engelli (2sem README) |
| Workspace > Scripts / Console, Lua | evet | çalışıyor, yalnız köprü yazarlarının ölçümü (21.1.0.14, 21.1.0.17); bu Mac'te ölçülmedi (doğrulanmadı) | evet | doğrulanmadı |
| Console Python | evet (Python kuruluysa) | doğrulanmadı (muhtemelen hayır) | evet, 21.1'den beri yerleşik | doğrulanmadı |
| Yerleşik MCP / AI asistanları | — | **hayır** | **evet** | belgelenmemiş |

- Kılavuz, Console'da Lua 5.1'i ve Lua/Python betiklerini genel olarak anlatıyor (Fusion Console; Deliver "Trigger script": "Python or Lua"). Belgelenmeyen şey, ücretsiz 21.1'de Lua'nın Resolve API'sine erişiminin süreceği. Python da bir nokta sürümde kaldırıldı.

**Yerleşik MCP: belgelenen** (kılavuz s.4318, Bölüm 201) [doğrulandı].
- "DaVinci Resolve Studio supports integration with AI assistants like Claude Desktop and Claude Code".
- Kurulum: "File > Setup AI Assistants".
- "If DaVinci Resolve is not running, the extension may opt to launch the application as needed".
- "Any scripts created by the AI assistant share the same access permissions to disk, network and other resources as the AI assistant."
- Örnek istemler:
  - ProRes 422 HQ + H.265 4K + 1080p H.264 proxy render;
  - zaman çizelgesi dökümü (klip sayısı, süre, çevrimdışı medya, işaretler);
  - V1 kliplerini yeniden adlandırma;
  - her kesime işaret koyup CSV'ye aktarma;
  - her klibin 2. düğümüne LUT;
  - Netflix teslim ayarı denetimi;
  - "Reframe this timeline for 9:16 vertical".
- Basın bülteni (https://www.blackmagicdesign.com/media/release/20260908-03): "create highlight edits from long form video, remove unwanted clips and render deliverables". ChatGPT Codex adı yalnız ikincil kaynaklarda (orta güven); kılavuz Codex'i saymıyor.
- **Belgelenmeyenler:**
  - araç listesi, taşıma, kurulumun yazdığı yapılandırma ve ağ davranışı;
  - bloglardaki "88 araç" (doğrulanmadı; muhtemelen 88 araç ve 20 kaynak sunan üçüncü taraf DigitalWorkflowCompany/resolve-mcp ile karıştırılıyor);
  - "External scripting: Local" ayarının MCP için gerekip gerekmediği (gerekebilir).
- **Yapılandırma ve gizlilik:** Setup AI Assistants, Claude Code/Desktop yapılandırmasına kendisi yazar. Bu bir yapılandırma değişikliğidir; açılırsa kullanıcıya açıkça söylenir. Analizde Read ile açılan kareler modele gider (görüntü gizliliği kuralı).
- **Demolar gerçekte ne:** ajan NLE'yi betik API'siyle sürüyor (düzen, toplu iş, render, basit montaj, işaret; 21.1'den beri geçiş, fade ve hız). Hareket tasarımı motoru değil.
- **Satın alma ve kurulum** [doğrulandı]:
  - 295 $'lık kalıcı fiyat yalnız ikincil kaynaklara dayanıyor; almadan önce Blackmagic mağazasından bakılır.
  - Mac App Store'daki Studio 299,99 $ ve 6.692 MB, ama betik API'si yok → alınmaz. Doğrudan indirilen Studio yükleyicisinin boyutu ölçülmedi.
  - Ücretsiz sürümün doğrudan indirmesi kayıt formu istiyor (`requiresRegistration: true`; ad, e-posta); Studio istemiyor.
  - Mac App Store'daki ücretsiz "DaVinci Resolve" (id 571213070): 21.1, 2.512 MB, macOS 15+, yalnız Apple ID. Doğrudan indirmenin (21.1.1) bir nokta sürüm gerisinde.
  - Formda "yalnız indir" seçeneği olup olmadığı doğrulanmadı.
- **Ağ davranışı** (kılavuz s.106):
  - "Automatically Check for Updates";
  - "Automatically opt-in for new beta program notifications";
  - "Send report when application quits unexpectedly" (kullanıcı doldurup gönderir);
  - Blackmagic Cloud (isteğe bağlı); Studio'da Extras Download Manager (AI paketleri).
  - Analitik belgelenmemiş, trafik ölçülmedi. Kurulumdan sonra ilk üç seçenek kapatılır.
- **Ücretsiz sürümün ticari kullanımı:** Blackmagic personeli resmî forumda serbest olduğunu yazdı (2018, 2020; forum.blackmagicdesign.com viewtopic p=405106, p=658009, p=421366). 21.1 EULA'sı okunmadı.

### Resolve için MCP sunucuları (GitHub, 2026-10-05)

| Depo | ★ | Lisans | Yol | Not |
|---|---|---|---|---|
| Blackmagic yerleşik | — | özel | Studio 21.1+ | araç listesi belgelenmemiş |
| samuelgursky/davinci-resolve-mcp v4.8.28 | 3.348 | MIT | Studio (dış betik); ücretsizde yalnız ≤21.0.x, uygulama içi köprüyle | Ayrıntı aşağıda |
| barckley75/resolve-claude-mcp | 374 | MIT | Studio 18+ | 52 araç; "do not use in production" |
| hiteshK03 / apvlv / mhadifilms/dvr / lordhoell | 116 / 78 / 15 / 13 | MIT | dış betik | sırasıyla 44 araç / Resolve + Fusion / CLI + MCP / 440+ araç |
| wassermanproductions/unofficial-davinci-mcp | 35 | Apache-2.0 | Studio canlı; ücretsiz için FCPXML 1.9, EDL, işaret CSV | FCPXML yazıcısı yalnız kesim, işaret ve bağlı ses yazıyor (geçiş, dönüşüm, ses düzeyi yok) |
| flamexnreal / 2sem | 26 / 5 | MIT | ücretsiz, Python menü betiği | yalnız ≤21.0.x; 21.1+'da çalışmıyor |
| saadk408/davinci-resolve-lua-mcp | 4 | MIT | **ücretsiz 21.1, Lua** (Workspace > Scripts), dosya tabanlı IPC, "no telemetry" | 21.1.0.17'de yazarın ölçümü; her oturum elle başlatılır |
| ET-sec/resolve-console-bridge | 2 | LICENSE MIT (GitHub: NOASSERTION) | **ücretsiz 21.1, Lua**; imzalı loopback soket | Workspace > Console'a `dofile(...)` yapıştırılarak başlatılır; 21.1.0.14 |
| hoyt-harness/davinci-mcp-professional | 25 | GPL-3.0 | Studio | 6 çekirdek araç, 289'u isteğe bağlı |
| Tooflex, DigitalWorkflowCompany | 19, 2 | lisans yok | — | kullanılamaz; ikincisi "88 araç" efsanesinin kaynağı |
| danielbaldwin47/resolve-mcp | — | — | Studio 21.0.3 | 21.1 öncesi API geçiş ekleyemediği için erimeyi OTIO dışa aktar → düzenle → içe aktar ile ekledi |

**samuelgursky/davinci-resolve-mcp ayrıntısı:**
- 37 bileşik / 389 ayrıntılı araç + .drp/.drt/.drx dosyalarını çevrimdışı düzenleyen 18 araçlı sunucu.
- Canlı sınamalar Studio 19.1.3.7, 20.3.2 ve 21.0.2.4'te; README'de 21.1 Studio sınaması yok.
- GitHub'dan güncelleme denetimi yapıyor (kapatılabilir).
- `analyze_media` varsayılan olarak kareleri sohbet modeline veriyor → `include_visuals=false`.
- install.py Python 3.10+ istiyor → `arac/uv run --python 3.12 python install.py`. Kurucu Claude Code yapılandırmasına yazabiliyor.
- README ticari "Bradford" ürününü tanıtıyor.

### Ücretsiz yol: dosya değişimi
- **Resolve'un içe/dışa aktarımı ücretsiz sürümde de aynı** [doğrulandı]:
  - OTIO 18.5'ten beri; OTIO'da bileşik klip ve klip işareti 18.6.5'ten beri.
  - FCPXML 1.10 (18.0), 1.11 (18.6), 1.13 (19.1.1) ve "Final Cut Pro 12 FCPXML" (21.0).
  - `.otioz` medyası dosyanın yanına açılıp kendiliğinden bağlanıyor (s.530; "Ensure you have enough storage space").
- **OTIO içe aktarma iletişim kutusu** (s.527–530):
  - zaman çizelgesi adı ve başlangıç TC'si dosyadan;
  - "Automatically set project settings";
  - gömülü yollarla medya havuzuna alma ve yeniden bağlama klasörü;
  - uzantıyı yok sayarak eşleme (proxy ↔ asıl);
  - çok kanallı ses bağlı gruplar halinde;
  - çözünürlük, kare hızı ve drop-frame "dosyadan" alınıyor; ama OTIO'da çözünürlük alanı yok → 1080×1920 iletişim kutusunda denetlenir.
- **Belgelenen efekt aktarımı** (s.468–472; OTIO bu tabloda yok) [doğrulandı]:

| Özellik | EDL | FCP7 XML | FCPX XML | AAF |
|---|---|---|---|---|
| Çok iz | hayır | evet | evet | evet |
| Görüntü geçişi | yalnız Cross Dissolve | 10 tür | 10 tür | 9 tür |
| Ses geçişi | hayır | hayır | hayır | evet |
| Opaklık | hayır | evet | evet | 3D Warp/Superimpose ile |
| Konum/ölçek/dönme (anahtar kareli) | hayır | evet | evet | 3D Warp ile |
| Doğrusal hız | evet | evet | evet | evet |
| Değişken hız | hayır | evet | evet | evet (Timewarp) |
| Dondurulmuş kare | hayır | hayır | hayır | evet |
| İç içe / bileşik | hayır | evet | evet | hayır |
| Karışık kare hızı | hayır | evet | evet | evet |
| Yazı üreteci | hayır | evet | evet | hayır |
| Renk düzeltme | hayır | hayır | evet (renk panosu → birincil) | hayır |

  - FCPX ayrıca Ken Burns'ü Dynamic Zoom olarak ve klip fade tutamaçlarını kendiliğinden getiriyor (s.1113–1114).
  - Desteklenmeyen XML efektleri içeride saklanıp geri dışa aktarılıyor.
  - Dışa aktarım biçimleri: .otio/.otioz, AAF, FCP7/FCPX XML, EDL (yalnız hedef atanmış tek iz) (s.4160–4162).
- **OTIO'yu Resolve'a alırken:**
  - **Yol:** Resolve 20.2'nin `file://` önekli OTIO'yu reddettiğine dair tek bir kullanıcı raporu var; önek silinince düzelmiş ([OTIO #1985](https://github.com/AcademySoftwareFoundation/OpenTimelineIO/issues/1985)). Bakımcılar iki biçimi de geçerli URL sayıyor ama Resolve davranışını doğrulamıyor; raporda file:// biçimi ve yüzde kodlaması ayrıştırılmamış (doğrulanmadı). "Resolve kendi dışa aktarımında düz mutlak POSIX yolu yazar" iddiası da doğrulanmadı. Stüdyo kuralı düz mutlak yol; Kdenlive file:// çözemediği için (kaynak kod) bu zaten gerekli.
  - **Hız** ([time-warp test suite #3](https://github.com/jminor/otio-time-warp-test-suite/issues/3), Resolve 19 dönemi, Aralık 2024):
    - yavaşlatmalar (%99/90/50/10), dondurma ve fit-to-fill doğru;
    - hızlandırmalar (%101–1000) klip sonunda 1–9 kare kayık;
    - ters hız yanlış;
    - hız değişen klipteki işaretler kayık.
    - Stüdyo ağır çekimi önceden ürettiği için bu nadiren önemli.
  - **Erime:** `SMPTE_Dissolve` erime olarak geliyor (danielbaldwin47 uygulaması).
  - **Taşınamayanlar:** dönüşüm, opaklık, ses kazancı ve klip rengi için OTIO standardı yok, ajanın yazdığı OTIO'da taşınmaz. Resolve bunları yalnız kendi `metadata.Resolve_OTIO` alanında taşıyor.
  - **Resolve'un OTIO dışa aktarımı:** kaynak ASWF "AWS Picchu Edit" .otio örneği (https://dpel.aswf.io/aws-picchu-edit/). Araştırmacı bunu yerelde inceledi. Doğrulayıcı lisans kabulü gerektiği için yeniden bakamadı; proje Resolve Studio 17 ile kurulmuş ve .otio'yu hangi sürümün yazdığı belirsiz.
    - Zaman çizelgesi metadata'sı yalnız `{"Resolve_OTIO": {"Resolve OTIO Meta Version": "1.0"}}`; `global_start_time` 86400@24.
    - Yapı: 26 iz, 508 klip, 382 boşluk, 7 `SMPTE_Dissolve`, 8 `LinearTimeWarp`.
    - 3.334 "Resolve Effect" kaydı:
      - görüntü: `Transform` (zoom anahtar kareleri), `Dynamic Zoom` (merkez ve ölçek, kare numarasıyla), `Video Faders` (giriş/çıkış kare), Cropping, Composite, Lens Correction, Retime and Scaling;
      - ses: "Fairlight Clip Volume and Fades" (dB), Pan, Pitch, EQ.
    - Medya referansları: 256 External, 239 Missing.
    - Kaynak aralıkları kesirli olabilir (37008.099992); geri okurken yuvarlanır.
- **Kdenlive 26.08.1 içe aktarması** (kaynak: https://invent.kde.org/multimedia/kdenlive/-/blob/v26.08.1/src/otio/otioimport.cpp) [doğrulandı]:
  - Yalnız `.otio`, yalnız menüden. Komut satırından OTIO içe aktarma yok: `kdenlive --help` yalnız `--render`/`--render-preset` gösteriyor, konumsal argüman "Kdenlive document to open".
  - İz adları ve görüntü/ses türleri geliyor. Klipler `ExternalReference`'tan; üreteçlerden yalnız `kdenlive:SolidColor`.
  - **Her** Transition aynı izde "luma" karışımına (erime) çevriliyor.
  - Zaman çizelgesi işaretleri kılavuz çizgisi, klip işaretleri klip işareti oluyor; metin `marker.comment()`'ten okunuyor.
  - Klipler medyanın başlangıç TC'sine göre kaydırılıyor.
  - fps zaman çizelgesinden, çözünürlük ilk görüntü klibinden alınıyor.
  - `resolveFile()` = `QUrl::fromLocalFile(...)`: `file://` çözülmüyor, göreli yol sayılıyor ve medya bulunamıyor.
  - Efekt, time warp, dönüşüm ve ses düzeyi yok sayılıyor.
  - Dışa aktarım (`otioexport.cpp`): düz yollar, boşluklar, karışımlar `SMPTE_Dissolve` olarak, işaretler comment + `kdenlive.type` ile.
- **Kdenlive macOS yapısı** [doğrulandı]:
  - `kdenlive-26.08.1-arm64.dmg` 144.419.895 B; SHA-256 `b606beaf42c0482a07c052bd2da384587b3aedcc948e7c885f954e195ff10bda`, KDE'nin `.sha256` dosyasıyla eşleşiyor (https://download.kde.org/stable/kdenlive/26.08/macOS/).
  - Kurulu .app 620–621 MB; notarize ("K Desktop Environment e.V. (5433B4KXM8)"); `--license` GPL v3; hesap gerekmiyor.
  - İçinde libopentimelineio 0.18.1, MLT 7.41.0 (`melt`), FFmpeg 8.1.1 ve `kdenlive_render` var; KUserFeedback (telemetri) kütüphanesi yok.
- **Fırsat** (doğrulayıcı önerisi, sınanmadı): ajan doğrudan `.kdenlive` (MLT XML) proje yazabilir. Kdenlive bunu konumsal argümanla açıyor; `kdenlive --render` ve paketteki `melt` başsız çiziyor. "Sonra" deneyi; sürüm bağımlılığı riski var.
- **Final Cut Pro 12.4:** 299,99 $, 6,41 GB, macOS 26.6+ → ücretli kuralının dışında. FCPXML onun yerel biçimi.

**Hangi biçim:**
- **En zengin:** Blackmagic belgesine göre FCPX ve FCP7 XML. Ama bakımlı açık yazıcı yok (OTIO'nun fcpx uyarlayıcısı kırık). Özel yazıcı da burada doğrulanamaz: Resolve yok, FCP ücretli, FCPXML DTD'si FCP'nin içinde.
- **Bugün en sağlam:** `.otio`. Yapı (kesim, iz, erime, işaret, başlangıç TC) OTIO içinde birebir gidiş-dönüş yapıyor; Resolve ve Kdenlive yerel olarak içe aktarıyor. Gerisi pişirilir ya da işaretle taşınır. Remotion'un OTIO dışa aktarımı da yazı, şekil, animasyon, efekt, geçiş ve dönüşümü medyaya pişiriyor; Resolve 18.5+ ve Premiere 25.6+ ile çalıştığı belgelenmiş (https://www.remotion.dev/docs/export-opentimeline).
- **EDL:** evrensel yedek, ama tek görüntü izi.
- **AAF:** Resolve iyi içe aktarıyor (ses geçişleri dahil), ama OTIO'nun AAF yazıcısı geçiş yazamıyor ve mob ID istiyor → ajan kullanamaz.

### OpenTimelineIO 0.18.1: paket ve gidiş-dönüş
- **Paket:**
  - `opentimelineio` 0.18.1: PyPI 2025-11-09; GitHub'da "Beta 18.1 – Python Wheel Fixes" ön sürüm olarak işaretli ve 2026-10-05'te en günceli. Apache-2.0.
  - cp39–cp313 wheel (cp312 arm64 1.236.369 B, kurulu ~3,6 MB); cp314 wheel yok.
  - Çekirdekte yalnız `otio_json`, `otioz` ve `otiod` uyarlayıcıları var.
- **`opentimelineio-plugins` 0.18.1:**
  - getirdikleri: aaf 2.0.0 (pyaaf2 1.7.1), ale 1.1.0, burnins 1.0.0, **cmx3600 1.0.0** (EDL), **fcp 1.0.0** (FCP7 xmeml), maya-sequencer, svg, xges;
  - getirmedikleri: `otio-fcpx-xml-adapter` 1.0.0 (2023-07; depo 2024-06) ve kendini eskimiş ilan eden `otio-kdenlive-adapter` 0.0.3.
- **Stüdyo `nle` ekstrası** (karar): `opentimelineio==0.18.1`, `otio-cmx3600-adapter==1.0.0`.
- **Gidiş-dönüş ölçümü** [doğrulandı]:
  - Hızlar: 30, 29.97, 23.976 ve 60 fps.
  - V1: A → 15 karelik `SMPTE_Dissolve` → B → C (`LinearTimeWarp(0.5)`).
  - V2: boşluk + bindirme; A1: müzik.
  - Bir klip işareti, bir zaman çizelgesi işareti; başlangıç TC 01:00:00:00.

| Biçim | Sonuç |
|---|---|
| .otio | `is_equivalent_to == True` (dört hızda); iz adı, erime, hız, işaret, metadata ve başlangıç TC korunuyor |
| .otioz | yazıyor; medya `media/…` altına zipleniyor, URL'ler göreli yapılıyor |
| FCP7 xmeml | kesim, 3 iz, Cross Dissolve, klip ve sekans işareti, başlangıç TC korunuyor; **iz adları ve hız düşüyor**; `<width>/<height>` yazılmıyor; hız geri okunurken 30000/1001 yerine 29.97 |
| EDL (cmx_3600) | birden çok görüntü izinde hata ("Only a single video track is supported"); erime `D 015`, `M2`, `* LOC:`; kayıt TC'si hep 00:00:00:00'dan; M2'de kaynak çıkışı tutarsız → hız EDL ile verilmez; geri okumada `rate=` zorunlu |
| FCPXML (otio-fcpx-xml-adapter) | 29.97 ve 23.976'da çöküyor (ValueError); erime, hız, zaman çizelgesi işareti ve başlangıç TC düşüyor; müzik "gap/audio" hilesi, `hasAudio="0"`; PATH'teki ffprobe'u çağırıyor; 1080×1920'yi yatay "1080p" yazıyor → **kaldırıldı** |
| otio-kdenlive-adapter 0.0.3 | eskimiş uyarısı basıyor; geçiş ve klip işaretleri düşüyor, zaman çizelgesi işareti korunuyor [düzeltildi]; klip adları bozuluyor |
| AAF (otio-aaf-adapter 2.0.0) | "Cannot find mob ID"; `use_empty_mob_ids=True` ile yalnız kesim; her OTIO geçişi doğrulamada düşüyor |

- **Yoldaki özel karakterler** [doğrulandı]:
  - Düz yolda `#`, `?` ve düz `%xx` OTIO URL araçlarını bozuyor: `/tmp/a#1.mov` → `/tmp/a`, `/tmp/q?x.mov` → `/tmp/q`, `/tmp/a%20b.mov` → `/tmp/a b.mov`; .otioz `NotAFileOnDisk` veriyor.
  - Yüzde kodlanmış URI'de (`Path.as_uri()`) `#` ve `?` çalıştı; düz `%xx` iki biçimde de başarısız.
  - Yani düz yola geçiş `#` ve `?` için bir gerileme. Bu yüzden böyle medya güvenli adla `cikti/nle/medya/` altına bağlanıyor. `os.link` farklı disk bölümünde başarısız olur; o durumda symlink ya da kopya, boyut söylenerek.
  - Türkçe harf, boşluk ve `&` çalışıyor.
- **29.97 zaman kodu** [doğrulandı]:
  - `RationalTime.to_timecode()` 29.97'de varsayılan olarak drop-frame basıyor: 108000 kare ("01:00:00:00" NDF) → `01:00:03;18`. `drop_frame` açıkça verilmeli; tamsayı hız (30/60) sorunu tümden önler.
  - OTIO JSON'da DF/NDF alanı yok.
  - otio-cmx3600, 29.97 ve 59.94'te EDL'yi hep `;` ile ve FCM satırı olmadan yazıyor (kaynakta TODO). Stüdyo EDL'yi sonradan işleyip `FCM: NON-DROP FRAME` ekliyor ve `:` koyuyor.
  - Medyadaki DF zaman kodu (`01:00:00;00`) `from_timecode` ile 107892 kare, `:` ile 108000 kare veriyor. TC ayrıştırması bu ayrımı korumalı (stüdyodaki durumuna bu belgede bakılmadı).
- **xmeml yolları:** Apple'ın FCP7 XML belirtimi `pathurl`'ü `file://localhost/...` biçiminde ve yüzde kodlamalı yazıyor (https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/FinalCutPro_XML/Basics/Basics.html). OTIO uyarlayıcısı dönüştürmüyor.

```python
import opentimelineio as otio
RT, TR = otio.opentime.RationalTime, otio.opentime.TimeRange
fps = 30                                                   # tamsayı hız DF belirsizliğini önler
tc0 = otio.opentime.from_timecode("01:00:00:00", fps)      # medya başlangıç TC'si (ffprobe tags.timecode), yoksa RT(0, fps)
ref = otio.schema.ExternalReference(target_url="/mutlak/yol/klip.mov",   # düz mutlak yol, file:// YOK
                                    available_range=TR(tc0, RT(180, fps)))
a = otio.schema.Clip(name="A", media_reference=ref, source_range=TR(tc0 + RT(30, fps), RT(60, fps)))
a.markers.append(otio.schema.Marker(name="vuruş", comment="vuruş",       # Kdenlive comment'i gösterir
                 marked_range=TR(tc0 + RT(45, fps), RT(0, fps)), color=otio.schema.MarkerColor.RED))
d = otio.schema.Transition(transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                           in_offset=RT(7, fps), out_offset=RT(8, fps))    # kesimde ortalanmış 15 kare
tl = otio.schema.Timeline(name="kurgu", global_start_time=otio.opentime.from_timecode("01:00:00:00", fps))
v1 = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video); v1.extend([a, d, b]); tl.tracks.append(v1)  # b: a gibi kurulur
otio.adapters.write_to_file(tl, "kurgu.otio")
assert otio.adapters.read_from_file("kurgu.otio").is_equivalent_to(tl)
otio.adapters.write_to_file(tek_izli_tl, "kurgu.edl", adapter_name="cmx_3600", rate=fps, style="avid")
```

### `medya nle`: çalıştırılarak denetlendi
- **Zaten iyiydi:**
  - kare ızgarası hesabı; plan örtüşmeleri kesimde ortalanmış erimeye çevriliyor;
  - başlangıç TC'si ffprobe `tags.timecode`'dan; NTSC hızları tam;
  - önceden üretilmiş ağır çekim klibi kullanılıyor; pişirilmemiş hız 1x + kırmızı işaretle aktarılıyor;
  - `kadraj` ve `hareket` işaret olarak taşınıyor;
  - yazdıktan sonra OTIO geri okuma denetimi var.
- **Bulunan kusurlar** [doğrulandı] **ve yapılan düzeltmeler:**
  1. `target_url=m.yol.as_uri()` yüzde kodlu file:// yazıyordu (nle.py:90) → düz mutlak yol.
  2. İşaretlerde yalnız `name` vardı (nle.py:97, 176), Kdenlive metni boş gösterirdi → `comment` de dolduruluyor.
  3. EDL makaraları yüzde kodlu dosya adından bozuk çıkıyordu ("C4B0C49F", "a231mp4") → kaynak dosya başına `A001…`. Makara çekimi değil kaynak dosyayı tanımlar; cmx3600 `clip.metadata['cmx_3600']['reel']`'i okuyor.
  4. EDL LOC satırları `str.upper()` ile büyütülüyor ve ASCII dışı karakter içeriyordu ("HIZ 2X — KURGU PROGRAMINDA…"; i→İ dönüşümü yerel ayara duyarsız) → ASCII adlar ve işaretler.
  5. 29.97 EDL `;` ile ve FCM satırsız yazılıyordu → `FCM: NON-DROP FRAME` + `:`.
  6. `#`, `%`, `?` koruması yoktu → `cikti/nle/medya/` altına güvenli adla bağlama.
  7. Kullanılmayan ve kırık `otio-fcpx-xml-adapter` kuruluydu → kaldırıldı. uv.lock değişir; pyproject yorumunun ve nle.py docstring'inin de güncellenmesi önerildi.
  8. Çözünürlük OTIO'da taşınmıyor → çıktı ipucuna "Resolve'da içe aktarma iletişim kutusunda çözünürlüğü denetle; Kdenlive ilk klipten alır" notunun eklenmesi önerildi (bu belgede denetlenmedi).
- Bu Mac'te Resolve ve Kdenlive kurulu olmadığı için içe aktarma sınanmadı.

### Doğrulanamayanlar (bir NLE kurulunca)
- Resolve 21.1.1, düz yollu ve Türkçe karakterli/boşluklu .otio'yu doğru alıyor mu: yeniden bağlama, erime, işaret, başlangıç TC, NTSC. OTIO'da alan yokken çözünürlüğü nereden alıyor?
- Resolve, ajanın yazdığı Resolve_OTIO efektlerini (Transform/Dynamic Zoom, Video Faders, Fairlight Clip Volume) okuyor mu?
- Kdenlive 26.08.1'in bizim dosyalarla gerçek davranışı (yalnız kaynak kodu okundu).
- xmeml'de `file://localhost` ile düz `pathurl` arasındaki fark.
- Yerleşik MCP'nin araç listesi, yazdığı yapılandırma ve ağ trafiği (yalnız kurulu bir Studio'da ölçülebilir).
- Ücretsiz 21.1'de Lua kullanımının Blackmagic EULA'sıyla uyumu ve ne kadar süreceği.
- Kullanıcıya sorulacaklar:
  - Elle bitirme için ücretsiz bir NLE kurulsun mu? Seçenekler: Kdenlive (620 MB, hesapsız); Resolve App Store'dan (2,5 GB, Apple ID) ya da doğrudan indirmeyle (kayıt formu).
  - Studio alınacak mı? 295 $, ücretli kuralına bilinçli bir istisna; App Store sürümü değil, doğrudan indirme.
  - Bir iş bağlamı Premiere/FCP aktarımı istiyor mu? İsterse FCP7/FCPXML yazıcısı öne çıkar.

## Ağır çekim motoru

**Karar (2026-10-05, son ölçümle):** `dogal` (gerçek yüksek fps kaynak) → ≤ 2000 px kaynakta **RIFE v4.6** önce, 4K'da
Apple önce (hız, disk) → (rife-ncnn-vulkan 20221029, MIT; ikili + model SHA-256 doğrulandı, `arac/rife`, 36 MB) → ffmpeg
minterpolate. Biri başarısız olur ya da asılırsa sıradakine düşülür (`medya yavaslat`; sınama: `test_yavaslat_rife_yedegi`).

**Yöntem:** gerçek 60/24 fps kareler → her N'inci kare girdi → yöntem N kat ara kare üretir → YALNIZ üretilen ara
kareler atılan gerçek karelerle karşılaştırılır; kareler ham çözülür (ffmpeg `psnr` süzgeci kullanılmadı: farklı zaman
damgalarında kare kaydırır). Ölçüt PSNR-Y ve SSIM-Y. Betikler ve ham CSV: `sistem/devam/yavas-cekim/`.

| Klip (kaynak, kat) | Apple | RIFE v4.6 | RIFE v4.22 | minterpolate | karıştırma |
|---|---|---|---|---|---|
| Big Buck Bunny 1080p60, yüksek hareket, ×4 (ort / en kötü %5) | 35,03 / 33,09 | 35,22 / 33,40 | **35,79** / 33,86 | 33,46 / 31,94 | 22,81 |
| aynı, 540p, ×4 | **33,77** / 31,77 | 33,09 / 31,01 | 33,34 / 31,29 | 31,19 / 29,74 | 22,51 |
| Gerçek sakin çekim (IMG_4021, 1024×540), ×4 | 40,87 | 40,71 | 40,46 | **40,99** | 40,28 |
| Sentetik hareket 720p, ×4 | 28,52 | **28,81** | 28,22 | 28,33 | 25,89 |
| Tears of Steel el kamerası 24 fps, ×2 | 36,43 / 32,81 | **37,71** / 33,86 | 37,13 | 32,59 / 27,08 | 23,00 |
| Tears of Steel kaydırma 24 fps, ×2 | 30,99 / 26,23 (SSIM en kötü 0,81) | **31,63** / 28,84 | 31,55 | 30,11 | 23,85 |

Apple'ın gerçek kamera satırları Neural Engine düzelince (18:25) ölçüldü; ilk denemede `ANECompilerService` 18 saat takılı olduğu için asılmıştı → bekçi ve RIFE yedeği eklendi.

**Hız** (1080p ×4, 84 ara kare): Apple 25 sn, RIFE v4.25 41 sn, v4.6 62 sn, minterpolate 39 sn. 540p'de RIFE v4.6 en hızlı (8 sn).

**Sonuç:** gerçek kamera görüntüsünde RIFE v4.6 > Apple > minterpolate (el kamerası 37,7 / 36,4 / 32,6 dB; kaydırmada Apple'ın en kötü kareleri bozuk: en kötü %5 26,2 dB, SSIM 0,81). Apple yalnız 540p çizgi filmde önde; sakin çekimde fark yok. Varsayılan: ≤2000 px'te RIFE (kalite, Neural Engine'den bağımsız), 4K'da Apple (hız; RIFE'nin PNG ara kareleri 4K'da GB'larca yer ister). v4.22 yüksek harekette +0,6 dB ama yalnız topluluk çatalında; resmî nihui sürümündeki v4.6 seçildi. Karıştırma (frame blending) hiç kullanılmaz.

## Kapsam boşlukları

> **Kaynak:** tek bir incelemecinin kapsam taraması (2026-10-05, 09:15–09:40). Okunanlar: CLAUDE.md, README, yetenekler.toml, eksiklik-elestirisi.md, alan raporlarının özetleri, satıcı becerileri, HyperFrames dist kodu. Denemeler scratchpad'de yapılıp silindi.
> **Bağımsız doğrulamadan geçmedi:** aksi yazılmadıkça bu bölümdeki her iddia (doğrulanmadı). [yerel] = düz yerel olgu; [yazım anı] = bu belge yazılırken yerelde yeniden bakıldı.

### Önce onarılacaklar
1. **`medya sahneler`in PySceneDetect'i kırık** [yerel]:
   - `.venv`'de `opencv_python-5.0.0.93.dist-info` duruyor, ama RECORD'daki 138 `cv2/` dosyasının hiçbiri diskte yok.
   - `medya yetenekler --saglayicilar` → `pyscenedetect✗, ffmpeg✓`; komut sessizce ffmpeg yedeğine düşüyor.
   - [yazım anı] `import cv2` hâlâ `ModuleNotFoundError` veriyor.
   - Olası neden: opencv-python ile opencv-python-headless aynı `cv2/` klasörünü paylaşır; headless kaldırılınca dosyalar da gitti.
   - Onarım: `arac/uv sync --all-extras --reinstall-package opencv-python` → `import cv2, scenedetect` → `medya test sahneler`. Ekstrasız bir `uv sync` analiz ve nle paketlerini yeniden siler.
2. **Bilgi katmanı** [yerel, 09:34]: o saatte yalnız `arac-radari/SKILL.md` vardı. [yazım anı] medya-studyo, hareket-tasarimi, kurgu-zanaati, ses-tasarimi, gorsel-uretim, teslim-denetimi ve remotion-best-practices oturumda yüklü → kapandı.
3. **Sessiz kurulumlar** (HyperFrames dist kodu okundu):
   - `hyperframes remove-background` ilk çalışmada sormadan `onnxruntime-node` 1.21.1'i (MIT, açılmış 217,9 MB) npm ile `~/.cache/hyperframes/optional` içine kuruyor ve `u2net_human_seg.onnx`'i (176,0 MB) indiriyor.
   - `HYPERFRAMES_NO_AUTO_INSTALL=1` yalnız CLI'nin kendini güncellemesini durduruyor.
   - `embedded-captions`, kelime zamanlı `transcript.json` yoksa `uvx whisperx` çalıştırıyor: ikinci bir Whisper, torch~=2.8, ~2 GB. Bu, tek-Whisper kararıyla çelişiyor.
   - [yazım anı] `medya-koruma` kancasında uvx, pip ya da npm kurulum kuralı yok.
4. **ffmpeg lisans etiketi** [yerel]: `arac/ffmpeg -L` şunu yazıyor: "This version of ffmpeg has nonfree parts compiled in. Therefore it is not legally redistributable." `yetenekler.toml` ise yalnız "GPL-3.0" diyor → "GPL-3.0 + nonfree (ikili dağıtılamaz; çıktı serbest)" olmalı.
5. **Disk** [yerel, anlık]:
   - Boş alan 09:15'te 16 GiB, 09:40'ta 11 GiB; Remotion görevi sonunda 7,7 GiB.
   - Paralel denemeler 5,9 GB tutuyordu (vfi 2,7; remotion 1,0; gorsel 0,7). Takas 2,8/4,0 GB.
   - Kurulum bütçesi güncel `df` ile hesaplanır.

### 25 olası istek
- Durum anahtarı (incelemecinin değerlendirmesi):
  - **ÇALIŞIR:** uçtan uca yol var.
  - **ELLE:** araç var ama `medya` sarmalayıcısı ya da ölçüm kapısı yok.
  - **KURULUM:** bir şey indirilmeli.
  - **YOK:** ticari kullanıma uygun yerel yol yok.
- Sayım: 12 ÇALIŞIR, 9 ELLE, 4 KURULUM.
- [yazım anı] `medya/komutlar/` altında sabitle, gurultu, eski, dikey, renk-esle, bosluk-kes, gizlilik, plaka, cokkamera ve EDL çizicisi yok → ELLE satırları hâlâ açık.

| # | İstek | Durum | Eksik / gereken |
|---|---|---|---|
| 1 | Sevgiliye şarkılı montaj | ÇALIŞIR | — (telifli şarkı yalnız kişisel hediyede) |
| 2 | Gezi filmi (iPhone + foto) | ÇALIŞIR, harita KISMİ | yerel harita kiti; Photos kütüphanesi için osxphotos (macOS 27'de denenmedi) |
| 3 | Aile olayı özeti | ÇALIŞIR | konuşmacı ayırma (sherpa-onnx, kurulu değil); çoklu telefon senkronu komutu (`axcorrelate` süzgeci var) |
| 4 | Foto slayt: Ken Burns + 2.5D | Ken Burns ÇALIŞIR; 2.5D KURULUM | Depth Anything V2 Small CoreML + LaMa; `slideshow` becerisi MP4 değil sunum üretir |
| 5 | Şarkı sözü / vuruşa kurgu | ÇALIŞIR (kapılı) | — |
| 6 | Ağır çekim, hız rampası | ÇALIŞIR | — (artık RIFE yedekli zincir, bkz. "Ağır çekim motoru") |
| 7 | Titrek çekim | ELLE | `medya sabitle` (vidstab var; `titreme.py` ≥%50 düşüşü ölçüyor) |
| 8 | Gece gürültüsü | ELLE | `medya gurultu` + ölçülmüş varsayılan; Apple'ın zamansal gürültü süzgeci bu M2'de yok |
| 9 | Eski video (VHS/DV) + büyütme | ELLE | bwdif → gürültü → seviye; Apple LL-SR 2x (0 MB) |
| 10 | Eski fotoğraf onarımı | KURULUM | LaMa + maske; Real-ESRGAN ncnn (isteğe bağlı); DDColor tiny; yüz onarımı yok (CodeFormer NC) |
| 11 | Nesne / kişi silme | foto KURULUM; durağan video ELLE; hareketli kamera YOK | LaMa + Vision ya da SAM 2.1 tiny; `tmedian` temiz plaka + `maskedmerge` |
| 12 | Videoda arka plan silme | ELLE | Vision kişi bölütlemesi video kipi; yedek RVM CoreML; yeşil perde süzgeçleri var |
| 13 | Renk düzeltme / çekim eşleme | ELLE | `medya renk-esle` + ΔE2000 kapısı |
| 14 | Dikey yeniden kadraj | ELLE | `medya dikey` (analiz → yumuşatılmış kırpma yolu); SAR tuzağı (256:81) |
| 15 | Sosyal medya paketi | ÇALIŞIR | kurgu.json'da varyant matrisi |
| 16 | Web uygulaması demosu | ÇALIŞIR | Puppeteer screencast tarifi |
| 17 | Ekran kaydı cilası (macOS/iOS) | ELLE | `bosluk-kes`; PII/sır bulanıklaştırma kapısı; `xcrun simctl` Xcode lisansı yüzünden tıkalı [yerel] |
| 18 | Özellik lansmanı | ÇALIŞIR | App Store pazarlamasında Apple cihazının 3D canlandırması kullanılmaz |
| 19 | App Store / Google Play önizlemesi | ÇALIŞIR, ön ayar yok | `teslim.py --hedef appstore` |
| 20 | README GIF / terminal demosu | ÇALIŞIR; gerçek terminal kaydı KURULUM | asciinema + agg; tek aralıklı yazı tipi |
| 21 | Konferans / uzun kayıt | ELLE | ffmpeg EDL çizicisi, `bosluk-kes`, PDF slayttan PNG'ye (Swift PDFKit) |
| 22 | Konuşan kafa + alt yazı | ÇALIŞIR | libass woff2 açamıyor → TTF/OTF; `bosluk-kes`, `dikey` |
| 23 | Açıklayıcı animasyon | ÇALIŞIR | Manim CE (isteğe bağlı) |
| 24 | Türkçe yapay zekâ dış sesi | KURULUM (kullanıcı kararı) | VoxCPM2 4-bit; `say -v Yelda` yalnız kişisel taslak |
| 25 | Müzik yatağı, cıngıl, SFX | ELLE / KISMİ | MIDI + SoundFont kiti, Kenney CC0; Magenta RT2 (kullanıcı kararı); MusicGen asla (CC-BY-NC) |

- Listede olmayan: dudak senkronlu dublaj → YOK. Wav2Lip yalnız kişisel/araştırma kullanımına açık; diğerleri difüzyon ya da CUDA istiyor.

### İncelemecinin ölçümleri (bu Mac, scratchpad; silindi; doğrulanmadı)
- **Apple VTLowLatencySuperResolutionScaler** (macOS 26+; https://developer.apple.com/documentation/videotoolbox/vtlowlatencysuperresolutionscalerconfiguration):
  - Destek: `isSupported=true`. 720x480, 720x576 ve 960x540'ta 1,5x ve 2x; 1280x720'de yalnız 1,5x; 1920x1080'de hiç yok.
  - Sınırlar: yalnız `420v` piksel biçimi; kaynak 96–1280 px, 2x için en çok 960 px.
  - Hız: oturum 0,041 s'de açıldı, indirme istemedi; 720x480 → 1440x960 kare başına 1,4–1,8 ms.
  - 2x testi: 7 kare (Golden Gate.mov ve DefaultAerial.jpg); kazanç/ofset düzeltmeli Y-PSNR.

| Girdi | PSNR-Y lanczos / LL-SR | SSIM lanczos / LL-SR | Netlik (Laplace oranı) lanczos / LL-SR |
|---|---|---|---|
| Temiz LR | 33,26 / 32,15 dB | 0,9329 / 0,9187 | 0,19 / 0,49 |
| Sıkıştırılmış LQ (gblur + x264 CRF 30) | 27,81 / 27,85 dB | 0,7688 / 0,7735 | 0,05 / 0,11 |

  - Görsel kontrol: kenarlar daha net, halka ya da hale yok; HR'deki ayrıntı geri gelmiyor.
  - CoreImage RGB→420v→RGB yolu ortalama RGB'yi +8…+16 kaydırdı; kayma modelden değil dönüşüm yolundan. Uyarlayıcı kareleri AVAssetReader'dan doğrudan 420v almalı.
  - Gerçek VHS/DV ile A/B gerekli. 4x `VTSuperResolutionScaler`'ın reddi geçerli.
- **Öteki VideoToolbox işlemcileri:** `VTLowLatencyFrameInterpolation` true, `VTSuperResolutionScaler` (4x) true, `VTTemporalNoiseFilter` false.
- **Vision kişi bölütlemesi** (`GeneratePersonSegmentationRequest`, 1080p, PNG çözme dahil): fast 37,5, balanced 55,3, accurate 129,4 ms/kare. Karede insan yoktu, kalite ölçülmedi.
- **tmedian ile temiz plaka** (sentetik 960x640, 260 px/s hızla geçen engel):
  - `tmedian=radius=60` sonrası engelin kare payı %6,84'ten %0,00'a indi.
  - Temiz kareye göre PSNR 36,82 dB (engelli kare 18,06 dB).
  - 180 karelik girdiden 60 kare çıkıyor; plaka tek kare olarak alınır.
- **Puppeteer ile ekran kaydı:**
  - puppeteer-core 25.12.0 sistemdeki Chrome 154'ü geçici profille sürdü.
  - `page.screencast`: 1280x720 VP9 30 fps CFR (2,93 s'de 89 kare).
  - `page.record`: 800x450 AV1 VFR; paketteki ffprobe 4.4 bunu çözemedi.
  - HyperFrames'in Chrome'u 152; screencast belgesi "Works in Chrome 153+" diyor.
- **libass ve woff2:** "Error opening memory font …woff2" hatası; çizim sessizce sistem yazı tipine düşüyor. Türkçe glifler yedekte doğru (tesseract tur "İSTANBUL ışığı ğüşöç" okudu).
- **ffmpeg-static 6.0** [yerel]:
  - Var olan süzgeçler:
    - sabitleme ve tarama: vidstabdetect/transform, deshake, bwdif/yadif/w3fdif/estdif/nnedi;
    - gürültü: nlmeans/hqdn3d/atadenoise/bm3d/fftdnoiz/vaguedenoiser/chromanr;
    - anahtarlama: chromakey/colorkey/despill/hsvkey;
    - renk: lut3d/haldclut, colorcorrect/grayworld/colortemperature/colorbalance/curves;
    - plaka ve maske: tmedian/maskedmerge/alphamerge/removelogo/delogo;
    - yazı: subtitles/ass/drawtext;
    - diğer görüntü: xfade/minterpolate/scdet/photosensitivity/libvmaf/coreimage/sendcmd/zoompan/v360/lenscorrection/perspective;
    - ses: silencedetect/silenceremove/axcorrelate/sidechaincompress/dialoguenhance/speechnorm/afftdn/anlmdn/arnndn.
  - Kodlayıcılar: libwebp_anim, gif, apng, prores_videotoolbox, qtrle, libsvtav1.
  - Olmayanlar: libplacebo, tonemap_opencl, rubberband, super2xsa. nnedi'nin ağırlık dosyası da yok.
- **Kayıt defteri** (386 öğe: 164 blok, 222 bileşen):
  - `world-map` çizim sırasında jsDelivr'dan d3@7, topojson-client@3.1.0 ve world-atlas@2'yi, ayrıca Google Fonts'u yüklüyor.
  - `vfx-iphone-device`, jsDelivr'dan three@0.147.0 + GLTF/Draco yükleyicilerini, gstatic'ten Draco çözücüyü alıyor. GLB'lerde "apple-logo" düğümü var; lisans ya da atıf yok.
  - `nyc-paris-flight`, üzerinde "© OpenStreetMap contributors © CARTO" yazan hazır bir PNG kullanıyor.
  - `hyperframes lint` bunların hiçbirini bildirmedi.
- **Ağ yasağı:** `sandbox-exec -p '(version 1)(allow default)(deny network*)'` altında curl 000 döndü (çıkış 6); yasak işliyor. Chrome'un bunun altında çalışıp çalışmadığı denenmedi.
- **Sistem** [yerel]:
  - `xcrun simctl` → "You have not agreed to the Xcode license agreements" (Xcode 27.0 kurulu).
  - `screencapture` video bayrakları var; `say` için Yelda (tr_TR) sesi var; tesseract'ta eng, osd ve tur.
  - Kurulu uygulamalar: Keynote, PowerPoint, Docker.app. Kurulu olmayanlar: iMovie, Final Cut, DaVinci, Blender, Kdenlive.

### Değer/emek sırasıyla ilk 10 ekleme
P0 olarak opencv onarımı önce yapılır.

| # | Ne | Boyut | Kullanıcı kararı | Bilgi tabanında karar | Durum [yazım anı] |
|---|---|---|---|---|---|
| 1 | Bilgi katmanı (yönlendirici + beceriler + bağlantılar) | 0 | hayır | evet (EE §1, §7.1) | kapandı |
| 2 | İndirmesiz komut paketi | 0 | hayır | kısmen (renk eşleme, PII OCR, WCAG: EE §4b/§4c/§7.5; dikey: EE §5) | açık |
| 3 | ffmpeg EDL çizicisi; HyperFrames yalnız grafik katmanı (ProRes 4444) | 0 | hayır | evet, kural olarak (EE §3a); uygulanmamış | açık |
| 4 | Sessiz kurulum kapısı | 0 | hayır | yeni (tek-Whisper kararını uygular: EE §3e) | açık |
| 5 | Demo ve terminal kiti | ~25 MB | hayır | kısmen (AM) | — |
| 6 | Müzik/SFX kiti | ~45 MB | hayır | evet (AP) | — |
| 7 | Yerel harita kiti | ~15 MB | hayır | yeni | — |
| 8 | Görsel ortamı çekirdeği | ~400 MB | boyut söylenip sorulur | evet (EE §3i, §7; IP) | — |
| 9 | Videoda kişi matı | ~8 MB | hayır | yeni | — |
| 10 | Türkçe dış ses | ~3.000 MB | **evet** (>2 GB) | evet (EE §3h, §7; AP) | — |

Ayrıntı (sürüm ve revizyonlar sabit; Homebrew kullanılmaz):
- **#2 İndirmesiz komut paketi.** Her komut = `medya/komutlar/<ad>.py` + `yetenekler.toml` kaydı + `testler/` altında doğruluk sınaması.
  - `sabitle` (vidstab); `gurultu`; `dikey`; `renk-esle`; `bosluk-kes`.
  - `eski`: `bwdif=mode=send_field` → `hqdn3d` → `medya-apple buyut` (VTLowLatencySuperResolutionScaler 2x; kaynak ≤960 px; kareler AVAssetReader'dan doğrudan 420v).
  - `gizlilik`: OCR + PII, yabancı yüz bulanıklaştırma. `plaka`: tmedian. `cokkamera`: axcorrelate.
  - `denetle`'ye WCAG 2.3.1 flaş sayacı.
  - `teslim.py --hedef appstore`: 886x1920 ya da 1920x886, 30 fps, libx264 High L4.0, `-b:v 11M -maxrate 12M`, AAC 256k 48 kHz stereo, 15–30 s, ≤500 MB (https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications).
- **#3 ffmpeg EDL çizicisi** (`ciz.py`).
  - Gerekçe: 45 dakika 30 fps'te 81.000 kare eder. HyperFrames'in ~12 fps hızıyla bu, ısıl kısılma öncesi ~1,9 saat; üstelik JPEG ara karelerle.
  - Yapı: trim/setpts kare ızgarasına oturtulur; xfade; tek 48 kHz WAV ses ustası; AAC bir kez kodlanır. Grafikler `hyperframes render --format mov` (ProRes 4444 alfa) ile çizilip bindirilir.
  - Sınama: scdet kesim kareleri ve axcorrelate ile ≤1 ms gecikme.
  - `medya-uretim.js`'ye "uzun ya da çekim ağırlıklı" dalı eklenir. Geçişlerin iki yolda aynı görünmesi için A/B yapılır (VMAF + temas sayfası).
- **#4 Sessiz kurulum kapısı.**
  - Kanca `deny` değil `ask` döndürür. Kapsam: `uvx`, `uv tool install`, `uv pip install`, `pip install`, `npm i/install/add`, `npx -y`; hedef yoksa `hyperframes remove-background|models install|tts|transcribe|catalog --on-device`.
  - Mesajda boyut ve hedef klasör yazılır; `testler/test_koruma.py`'ye örnekler eklenir.
  - embedded-captions'tan önce `medya yaziya-dok <ses> --dil tr` çıktısı `transcript.json` olarak verilir.
- **#5 Demo ve terminal kiti.**
  - asciinema 3.2.1 + agg 1.9.0: resmî aarch64-apple-darwin ikilileri (6,8 + 13,8 MB, GPL-3.0). SHA-256 ilk indirmede kaydedilir. `asciinema upload/stream` asla kullanılmaz.
  - Yazı tipleri: `@fontsource/jetbrains-mono` 5.3.0; libass için Inter 4.1 TTF (Regular/SemiBold).
  - Puppeteer screencast: puppeteer-core `createRequire` ile, sistem Chrome'u, geçici `userDataDir` (kullanıcı profili asla).
  - VHS 0.12.1 ttyd istiyor; ttyd 1.7.7'nin macOS ikilisi yok.
- **#6 Müzik/SFX kiti.**
  - `tinysoundfont==0.3.7` ve `pretty_midi==0.2.11.post0` (`ortamlar/ses`).
  - GeneralUser GS v2.0.3 (32,3 MB, commit 9704918): müzik üretimine izinli; yazılım ürününe gömmek ayrı konu.
  - Kenney CC0 paketleri (https://kenney.nl/assets/interface-sounds).
  - Her paket için manifest: URL, lisans, tarih, SHA-256.
- **#7 Yerel harita kiti.**
  - `d3@7.9.0`, `topojson-client@3.1.0`, `world-atlas@2.0.2` stüdyoya kopyalanır.
  - Natural Earth `ne_10m_admin_1_states_provinces` (14,9 MB zip; Türkiye illeri GeoJSON'a ayıklanır). Kamu malı; ticari dahil izin ve atıf gerekmez (https://www.naturalearthdata.com/about/terms-of-use/).
  - Kural: kompozisyonda `src`, `href` ya da `url()` içinde http(s):// varsa çizimden önce kopyalanır ya da reddedilir.
- **#8 Görsel ortamı çekirdeği** (`ortamlar/gorsel`, Python 3.12).
  - `onnxruntime==1.30.0`, `numpy==2.5.3`, `pillow==12.3.0`.
  - Carve/LaMa-ONNX @c3c0c9e `lama_fp32.onnx` (207,5–208 MB). Girdi 512x512; kırp, büyüt, yapıştır tekniği gerekir.
  - apple/coreml-depth-anything-v2-small @cfef6f6 F16 (49,4 MB). Yalnız Small Apache-2.0; Base/Large/Giant NC.
  - apple/coreml-sam2.1-tiny @39ae0a8 FLOAT16 (79,7 MB).
  - CoreML modeli Swift'te `MLModel.compileModel` ile derlenir (xcrun gerekmez). Gerekirse sonra BiRefNet-lite. Kurulumdan sonra en az 5 GB boş kalmalı.
- **#9 Videoda kişi matı.**
  - Yeni alt komut: `medya-apple kisi-maske <video> <cikti.mov> [--kalite fast|balanced|accurate]`, çıktı ProRes 4444 alfa.
  - Kenar titremesi kötü çıkarsa yedek: RVM mobilenetv3 1920x1080 fp16 mlmodel v1.0.0 (7,49 MB, GPL-3.0). Çözünürlüğü sabit ve yatay; dikey videoda döndürmek gerekir.
  - Kişi içeren bir klip ile kalite (komşu kare IoU, kenar titremesi) ölçülmedi.
  - Satıcı becerisine göre remove-background CPU'da 1080p'de ~2 fps.
- **#10 Türkçe dış ses.**
  - `mlx-audio[tts,stt,sts]==0.5.7` (`uv tool install --prerelease=allow`) ve mlx-community/VoxCPM2-4bit @dc9e5c1 (2.302 MB). Kod ve ağırlık Apache-2.0.
  - Kabul kapısı: `ses-tasarimi/scripts/cer.py --kapi tts`.
  - 16 GB RAM'de başka ağır işle aynı anda çalıştırılmaz. Ses klonlama yalnız sesin sahibinin rızasıyla.
  - Kokoro'da Türkçe yok; macOS sesleri yalnız kişisel ve ticari olmayan kullanıma açık.

### Diğer kullanıcı kararları
- **Xcode lisansı** (`sudo xcodebuild -license accept`): `simctl` (App Store önizlemesi için iOS Simulator kaydı), Homebrew, ttyd/VHS ve whisper-cli bunun arkasında kilitli. Homebrew'un açılması "Homebrew yok" politikasını kendiliğinden değiştirmez.
- **Magenta RT2** (`magenta-rt[mlx]==2.0.3`, ~2,4 GB):
  - Kod Apache-2.0, ağırlık CC-BY-4.0.
  - Modeller varsayılan olarak `~/Documents/Magenta` altına iniyor; stüdyoya yönlendirme seçeneği kurulumdan önce `mrt --help` ile doğrulanmalı.
  - BPM parametresi yok.
- **ACE-Step, FLUX.2 klein, SeedVR2:** yalnız harici SSD ile.
- **Blender 5.2** (~1,3 GB, tahmini) ve **Manim CE** (~0,3 GB): isteğe bağlı.
- **osxphotos 0.77.2** (MIT): README "Tested … through macOS Sequoia (15.7.2)" diyor ve macOS 26.x'te paylaşılan albümleri okuyamıyor. macOS 27'de denenmedi. Mahrem kütüphaneye erişim kullanıcının kararı.
- **Docker Desktop:** yalnız kişisel kullanım, küçük işletme (<250 çalışan VE <10 milyon $ gelir), eğitim ve ticari olmayan açık kaynak için ücretsiz (https://docs.docker.com/subscription/desktop-license/).
- **DDColor tiny** (220 MB, Apache-2.0 etiketli): ImageNet ile eğitildiği için iş kullanımında çekince var. Ağırlıklar pickle → `torch.load(weights_only=True)`. Önce kişisel işte.
- İş videoları hangi şirket için ve şirket kaç kişi (sözleşmeliler dahil)? Bu, Remotion ve Docker Desktop kararını belirler.

### Reddedilenler ve yönlendirme kuralları
- **Ticari olmayan lisanslar:** ProPainter (S-Lab License 1.0), E2FGVI (CC BY-NC 4.0), MatAnyone ve MatAnyone2 (NTU S-Lab License 1.0), Wav2Lip (yalnız kişisel/araştırma; LRS2 verisi) kullanılmaz. Difüzyon tabanlı video silgileri "yerel video difüzyonu yok" kararına takılıyor.
- **Harita:** CARTO altlıkları API anahtarı istiyor; ayda 1M karodan fazla ticari kullanım ücretli (https://github.com/CartoDB/basemap-styles). Kayıt defterindeki CARTO/OSM PNG'si iş için kullanılmaz; Natural Earth kullanılır.
- **Apple cihazları:** App Store pazarlama kuralları Apple ürününün 3D çizimini ya da benzetimini, ürün görselini değiştirmeyi ve canlandırmayı yasaklıyor; yalnız Apple'ın verdiği bezel'ler değiştirilmeden kullanılabilir (https://developer.apple.com/app-store/marketing/guidelines/). `vfx-iphone-device` App Store pazarlamasında kullanılmaz; kişisel işte sorun yok.
- **Uzak referanslar:** kayıt defteri bloklarındaki http(s) referansları (CDN, Google Fonts, gstatic) stüdyoya kopyalanmadan çizilmez.
- **Slayt gösterisi:** `slideshow` becerisi gezinilebilir sunum üretir. Fotoğraf slayt gösterisi videosu general-video ve keyframes ile yapılır.
- **Alt yazı çevirisi:** Whisper turbo ile yapılmaz, çeviri için eğitilmemiş (https://github.com/openai/whisper). SRT metnini Claude çevirir; metin Anthropic'e gider.
- **Alt yazı gömme:** ffmpeg ile gömülürken TTF/OTF yazı tipi `fontsdir` ile verilir.
- **Google Play önizlemesi:** bir YouTube URL'si olmak zorunda: herkese açık ya da liste dışı, reklamsız, gömülebilir; yalnız ilk 30 s otomatik oynar (https://support.google.com/googleplay/android-developer/answer/9866151). Yüklemeyi kullanıcı kendi hesabından yapar.

## Öneriler

Kapsam satırlarının öncelikleri incelemecinindir (doğrulanmadı).

| Ne | Öncelik | Boyut | Lisans | Ticari |
|---|---|---|---|---|
| Remotion 4.0.533 2D set, stüdyo kökünde sabit | yapıldı | ~235 MB (4.0.532'de ölçüldü) | Remotion License (bazı yardımcılar MIT; hepsi çekirdeğe bağlı) | koşullu: birey, ≤3 kişi, yalnız dosya teslim eden serbest iş |
| `sablonlar/remotion`, `--motor remotion`, BRIEF "Lisans bağlamı", lisans kapısı | yapıldı | <1 MB | stüdyo | evet |
| `remotion-best-practices` @0b5db9d vendor + stüdyo kuralları | yapıldı | 1,4 MB | MIT (güven orta) | evet |
| Kanca: Remotion bulut, telemetri, yükseltme ve yasak paket kalıpları | yapıldı | 0 | stüdyo | evet |
| Sınama: şablon çizimi | yapıldı | 0 | stüdyo | evet |
| `medya remotion render/still/kontak` uyarlayıcısı (her çağrıda `--color-space=bt709`, son çizimde PNG, ardından `medya denetle`) | simdi | 0 | stüdyo | evet |
| 4.0.533'te ek Remotion sınamaları: dış ağ kapalı çizim, kare eşleme, ses ±1 ms, framemd5, ffprobe bt709/tv, "usage event" yokluğu | simdi | ~5 MB | stüdyo | evet |
| Beceri commit'ini motor sürümüyle eşlemek | sonra (sonraki yükseltmede) | 1,4 MB | MIT | evet |
| 3D/Lottie ekleri (@remotion/three, three, R3F, @remotion/lottie, lottie-web) | sonra (istek gelince) | ~62 MB | MIT + Remotion License | koşullu |
| Remotion Studio (insan önizlemesi; LAN'a açık) | kullanici-karari | 0 | Remotion License | koşullu |
| licenseKey ve "free-license", web-renderer, google-fonts, sfx ve remotion.media, @remotion/mcp, npx skills, create-video, upgrade, Lambda/Cloud Run/Vercel, cube(), Editor Starter, ElevenLabs/MapTiler/Mapbox; ≥4 kişilik işveren işi | hayir | — | — | — |
| `medya nle` düzeltmeleri (düz yol, comment, kaynak başına makara, ASCII EDL, NDF, # % ? bağlama) | yapıldı | 0 | Apache-2.0 + stüdyo | evet |
| `otio-fcpx-xml-adapter` kaldırma | yapıldı | 0 | Apache-2.0 | evet |
| Resolve Studio 21.1.1 + yerleşik MCP (`resolve-studio-mcp`, etkin=false) | kullanici-karari | ölçülmedi (App Store sürümü 6.692 MB, o alınmaz) | özel, ücretli (~295 $, ikincil kaynak) | evet |
| Ücretsiz Resolve 21.1.1, elle bitirme için (etkin=false) | kullanici-karari | 2.512 MB (App Store, 21.1) | özel ücretsiz (21.1 EULA'sı okunmadı) | evet (satıcının forum açıklaması) |
| Kdenlive 26.08.1 (etkin=false) | kullanici-karari | 620 MB (DMG 144 MB) | GPL-3.0 | evet |
| samuelgursky/davinci-resolve-mcp 4.8.28 (yalnız Studio alınırsa; `include_visuals=false`) | sonra | ölçülmedi | MIT | evet |
| `medya nle --paket` (.otioz) | sonra | 0 + medyanın tam kopyası | Apache-2.0 | evet |
| `medya nle --pisir` (tutamaçlı ProRes ara klipler) | sonra | 0 (ProRes büyük) | ffmpeg GPL | evet |
| `medya nle oku` + NLE içe aktarma doğrulaması (kare sayacı + Vision OCR) | sonra (NLE kurulunca) | 0 | Apache-2.0 | evet |
| FCP7 xmeml (otio-fcp-adapter 1.0.0 + Basic Motion, Opacity, Audio Levels) ya da özel FCPXML 1.10/1.11 yazıcısı | sonra (Resolve'da doğrulanmadan sunulmaz) | 0,15 MB | Apache-2.0 | evet |
| Resolve_OTIO efekt metadata deneyi | sonra | 0 | — | evet |
| `.kdenlive` (MLT XML) proje yazıcısı deneyi | sonra | 0 | — | evet |
| Ücretsiz 21.1 Lua köprüleri; otio-kdenlive-adapter; OTIO AAF yazıcısı | hayir | 0 | MIT / Apache-2.0 | belirsiz / evet |
| Ağır çekim zinciri dogal → Apple → RIFE v4.6 → minterpolate | yapıldı | 36 MB (`arac/rife`) | RIFE MIT; Apple SDK; ffmpeg GPL | evet |
| Neural Engine bekçisi | yapıldı | 0 | stüdyo | evet |
| Apple FRC'yi Tears of Steel kliplerinde yeniden ölçmek (Neural Engine düzelince) | sonra | 0 | — | — |
| RIFE v4.22/v4.25 (TNTwise topluluk çatalı) | hayir (resmî v4.6 seçildi) | — | MIT | evet |
| Kare karıştırma (frame blending) | hayir | — | — | — |
| opencv-python yeniden kurulumu (PySceneDetect) | simdi | ~120 MB | Apache-2.0 / BSD-3 | evet |
| İndirmesiz komut paketi | simdi | 0 | stüdyo + ffmpeg + Apple | evet |
| ffmpeg EDL çizicisi | simdi | 0 | stüdyo + ffmpeg | evet |
| Sessiz kurulum kapısı (kancada `ask`) | simdi | 0 | stüdyo | evet |
| yetenekler.toml'da ffmpeg lisansı "GPL-3.0 + nonfree" | simdi | 0 | — | — |
| Demo ve terminal kiti | simdi | ~25 MB | GPL-3.0 (araçlar), OFL-1.1 (yazı tipleri) | evet |
| Müzik/SFX kiti | simdi | ~45 MB | MIT / GeneralUser GS / CC0 | evet |
| Yerel harita kiti | simdi | ~15 MB | kamu malı + ISC | evet |
| Görsel ortamı çekirdeği (boyut söylenip sorulur) | simdi | ~400 MB | Apache-2.0 / MIT | evet |
| Videoda kişi matı (Vision; yedek RVM) | simdi | ~8 MB | macOS / GPL-3.0 | koşullu |
| Türkçe dış ses VoxCPM2 4-bit | kullanici-karari | ~3.000 MB | Apache-2.0 / MIT | evet |
| Xcode lisansını kabul etmek | kullanici-karari | 0 | Xcode SLA | evet |
| Magenta RT2 | kullanici-karari | ~2.400 MB | Apache-2.0 + CC-BY-4.0 | evet |
| Blender 5.2 LTS + Manim CE | sonra | ~1.600 MB | GPL-2.0+ / MIT | evet |
| DDColor tiny | sonra | 220 MB | Apache-2.0 (ImageNet çekincesi) | koşullu |
| osxphotos 0.77.2 | sonra | ~40 MB | MIT | evet |
| ProPainter, E2FGVI, MatAnyone/MatAnyone2, Wav2Lip | hayir | — | NC | hayir |

## Mevcut bilgi tabanındaki düzeltmeler

Satırlar `sistem/arastirma/2026-10-05/` içindeki eski dosyalardandır. Biçim: `dosya:satır`: eski → doğrusu.

**Remotion**
- `video-framework.md:111`, `animation-motion.md:16, 71, 81, 496`: güncel sürüm 4.0.532 → güncel 4.0.533 (2026-10-05; uzun render'da giderek yavaşlama düzeltildi). Stüdyo 4.0.533'e sabit.
- `video-framework.md:113, 287, 307`: "sabit playbackRate de kare tekrarlar, ara kare yok" ([uncertain]) ve "kare tekrarı HyperFrames'e özgü" → ölçüldü:
  - Remotion her çıktı karesinde kaynak zamanını doğru örnekliyor (60 fps kaynak 0,5x → 90/90 benzersiz kare).
  - Ama ara kare üretmiyor: kaynak fps < kompozisyon fps / hız ise o da tekrarlıyor (30 fps kaynak 0,5x → 60 karede 30 benzersiz).
  - HyperFrames'in farkı: yeterli kare varken de tekrarlıyor (60 fps 0,5x → saniyede 15 benzersiz kare).
- `video-framework.md:113, 116`; `animation-motion.md:74, 80`; `claude-code-ecosystem.md:280`: beceriler `(DO_NOT_TRACK=1) npx skills add remotion-dev/skills` ile kurulur → `npx skills` ve `remotion skills` kancayla engelli. Yalnız `remotion-best-practices` @0b5db9d vendor olarak alındı (1,4 MB, 141 dosya), üstünde stüdyo kuralları.
- `claude-code-ecosystem.md:274, 278`: "Remotion bilgisi yalnız Remotion kullanan iş depoları için"; "skills deposunun lisansı görünmüyor" → Remotion stüdyonun lisans kapılı ikinci motoru. Depoda LICENSE yok; MIT dayanağı resmî claude-code-plugin (güven orta).
- `animation-motion.md:80`, `video-framework.md:116`: kurulum `npx create-video@latest` ile → create-video engelli. Sürümü sabit açık kurulum stüdyo kökünde; projeler `sablonlar/remotion`'dan.
- `animation-motion.md:80-81` (~278 MB / ~400 MB), `video-framework.md:117` (~350 MB) → ölçüldü: 2D set 234–235 MB (262 npm paketi); 3D/Lottie ile ~297 MB.
- `animation-motion.md:79`: "kendi Chrome Headless Shell'ini indirir" → stüdyo HyperFrames'in Chrome 152'sini `setBrowserExecutable` ile kullanıyor, indirme yok. Tarayıcı verilmezse 149 indirilir (98 MB zip).
- `animation-motion.md:82-83`: `npx remotion render/still` → yerel ikili `$MEDYA/node_modules/.bin/remotion` (npx, paket yerelde yoksa npm'e gider). Çekimde her çağrıda `--color-space=bt709`.
- `video-framework.md:114`: "@remotion/* paketleri npm'de UNLICENSED" → npm alanları karışık:
  - transitions ve effects UNLICENSED;
  - fonts, gsap, three, paths, shapes, noise, captions, zod-types, studio, sfx MIT;
  - çekirdek "SEE LICENSE"; light-leaks ve media-parser "Remotion License".
  - Hepsi çekirdeğe bağlı olduğu için yığın fiilen Remotion License altında.
- `video-framework.md:48, 113`: `@remotion/light-leaks` → 5.0'da yayımı kesiliyor; yerine `@remotion/effects` `lightLeak()`.
- `video-framework.md:118`, `animation-motion.md:77, 85`: "licenseKey ayarlanmazsa telemetri yok" → doğru ama eksik:
  - Belgenin önerdiği `"free-license"` değeri de her render'da POST gönderiyor; 5.0 migration bunu ücretsiz kullanıcıya "Required action" olarak yazıyor.
  - Studio açıkken npm'e ve bugs.remotion.dev'e kapatılamayan istekler atıyor.
  - Studio ve render sırasındaki statik sunucu tüm ağ arayüzlerine bağlanıyor.
- `animation-motion.md:56` (zaten `:523`'te [uncertain]; kaynakları `:68`'deki arceapps ve motionflare karşılaştırmaları): "ajanlar HTML+GSAP'i Remotion TSX'ten iyi yazar" → kanıtsız (sayı ve yöntem yok). İki motor da headless Chrome'da çiziyor, görsel tavan aynı. Fark birinci taraf yapı taşlarında ve TSX tür denetiminde. Motoru lisans kapısı ve iş türü seçer.

**DaVinci / NLE**
- `video-framework.md:19, 156, 288`: "ücretsiz Resolve ajanla sürülemez; dış betik Studio'ya özel; 21.1'de Python ücretsiz sürümden kalktı" → birincil kaynaklarla doğrulandı. Ekler:
  - Studio 21.1'deki yerleşik MCP (File > Setup AI Assistants) asıl "Claude Resolve'da kurgu yapar" yolu → `resolve-studio-mcp` etkin=false.
  - Ücretsiz 21.1 Lua betiklerini hâlâ çalıştırıyor; yalnız resmî olmayan köprüler kullanıyor (doğrulanmadı).
  - Mac App Store yapılarında, Studio dahil, betik API'si yok.
  - `:156`'daki "295 $" yalnız ikincil kaynağa dayanıyor. "Birkaç GB" → App Store ücretsiz 2.512 MB, App Store Studio 6.692 MB.
- `claude-code-ecosystem.md:40`: "DaVinci Resolve MCP'den kaçın (ücretli Studio ister)" → üçüncü taraf MCP'ler yerine Blackmagic'in yerleşik MCP'si (Studio 21.1) gerçek yol. Kayıtta etkin=false; yalnız kullanıcı açıkça isterse.
- `claude-code-ecosystem.md:376, 728`: "samuelgursky MCP 4.8.27; ücretsiz sürüm Workspace > Scripts köprüsüyle çalışır" →
  - sürüm 4.8.28 (2026-10-04); köprü yalnız ≤21.0.x'te çalışıyor;
  - README'de 21.1 Studio sınaması yok;
  - `analyze_media` kareleri varsayılan olarak sohbet modeline gönderiyor (`include_visuals=false`);
  - kurucu Claude Code yapılandırmasına yazabiliyor.
- `video-framework.md:101`: alternatif olarak `otio-kdenlive-adapter` 0.0.3 → kendini eskimiş ilan ediyor; geçişi ve klip işaretlerini düşürüyor (ölçüldü). Kdenlive'ın yerel OTIO içe aktarması kullanılır.
- `video-framework.md:102`: "uyarlayıcılar FCP XML, EDL, AAF ve ALE'yi kapsar" → ölçüldü:
  - FCPXML uyarlayıcısı 29,97 ve 23,976'da çöküyor; erime, hız, işaret ve başlangıç TC düşüyor (stüdyodan kaldırıldı);
  - FCP7 xmeml iz adlarını ve hızı düşürüyor;
  - EDL tek görüntü izi taşıyor;
  - AAF yazıcısı her geçişte hata veriyor.
- `video-framework.md:106` (OTIO + Kdenlive ~450 MB), `eksiklik-elestirisi.md:146` (Shotcut/Kdenlive ~1 GB, doğrulanmadı) → ölçüldü: Kdenlive 26.08.1 .app 620–621 MB, DMG 144 MB. OTIO kurulu hâliyle ~3,6 MB.
- `video-framework.md:284`: "25.04 notlarına göre efekt, süzgeç ve geçişler dışa aktarılmaz" → 26.08.1 kaynak kodu: içe aktarmada her Transition luma karışımına (erime) çevriliyor, dışa aktarmada karışımlar `SMPTE_Dissolve` olarak yazılıyor. Efekt, dönüşüm, hız ve ses düzeyi hâlâ taşınmıyor.
- `editing-craft.md:693`, `animation-motion.md:553`, `footage-analysis.md:307`: "hangi NLE'nin içe aktardığı doğrulanmadı / araştırılmadı" →
  - Resolve (ücretsiz dahil) .otio'yu 18.5'ten beri alıyor; .otioz'u medyasını kendisi açarak alıyor (sürüm notları, kılavuz s.530).
  - Kdenlive 26.08.1 .otio'yu yerel olarak alıyor (kaynak kod).
  - Bu Mac'te içe aktarma hâlâ sınanmadı. FCP ücretli.
- `video-framework.md:256, 303`: "EDL ve XML için opentimelineio-plugins kur" → stüdyonun `nle` ekstrası yalnız `opentimelineio==0.18.1` + `otio-cmx3600-adapter==1.0.0`. FCP7 xmeml ileride `otio-fcp-adapter==1.0.0` ile.

**Ağır çekim**
- `footage-analysis.md:11, 167, 259` ("VT 29,6 dB ile minterpolate'ı (28,7) geçti"; zaten `:345`'te çürütülmüştü: testsrc2'de minterpolate +2,4 dB önde) ve `eksiklik-elestirisi.md:61-66` ("ölçümler çelişiyor; gerçek çekimde yeniden ölç") → gerçek ve standart çekimde yeniden ölçüldü:
  - yüksek harekette Apple ≈ RIFE > minterpolate (1,5–2 dB);
  - el kamerasında RIFE, minterpolate'tan +5 dB;
  - sakin çekimde fark yok.
- `video-framework.md:67, 74, 179` ("30 fps kaynakta minterpolate; daha iyi seçenek Apple"), `:308` ("RIFE üçüncü seçenek"), `editing-craft.md:96, 104, 332` ("RIFE yalnız yedek, varsayılan olmasın"), `animation-motion.md:22`, `delivery-qa.md:271` → yeni sıra: dogal → Apple VTFrameRateConversion → RIFE v4.6 → minterpolate. Başarısız ya da asılan basamak atlanır.
- `footage-analysis.md:257`: "ikinci seçenek rife-ncnn-vulkan v4.25" → v4.6 (resmî nihui 20221029) seçildi. v4.25 ve v4.22 yalnız TNTwise çatalında; v4.22 1080p yüksek harekette +0,6 dB önde.
- `footage-analysis.md:166` ("M2'de 1080p için 5–10 kare/s tahmini"; zip 436 MB), `editing-craft.md:62, 104, 332` ("437 MB indirme") → ölçüldü:
  - 1080p ×4, 84 ara kare: RIFE v4.6 62 s (~1,4 kare/s), v4.25 41 s, Apple 25 s, minterpolate 39 s.
  - 540p'de v4.6 en hızlısı (8 s).
  - Stüdyoya yalnız ikili ve v4.6 modeli kuruldu: `arac/rife`, 36 MB, SHA-256 doğrulandı.
- `video-framework.md:68` (alternatif: MLT timeremap `image_mode=blend`, yani kare karıştırma) → karıştırma her ölçümde en kötüsü (yüksek harekette ~22–23 dB; Apple ve RIFE 33–36 dB). Hiçbir durumda kullanılmaz.
- `footage-analysis.md:167` ("ilk çalışmada model ~10 s'de yüklenir, sonra önbellekten gelir") → ek: Neural Engine derleyicisi (`ANECompilerService`) takılırsa model yüklemesi sonsuza dek bekliyor (`_ANEDaemonConnection loadModel`). Bu Mac'te 18 saat %100 CPU'da takılı görüldü. Apple ML komutları artık bekçi sayesinde hemen hata veriyor; `yavaslat` RIFE'a düşüyor.
- `claude-code-ecosystem.md:829` ("RIFE sınıfı ara kare aracı ve OTIO kapsanmadı") → ikisi de bu araştırmada kapsandı.

**Kapsam incelemesinden** (doğrulanmadı; [yerel] olanlar hariç)
- `eksiklik-elestirisi.md:8` (16 GiB boş) → 09:40'ta 11 GiB, Remotion görevi sonunda 7,7 GiB [yerel, anlık].
- `eksiklik-elestirisi.md:126` (package.json `^0.8.124`) → tam `"0.8.124"` [yerel, 09:40].
- `eksiklik-elestirisi.md:68` (`medya sdr` varsayılanı hable) → varsayılan artık mobius [yerel, 09:40].
- `eksiklik-elestirisi.md:143` (Magenta RT2 ~1,84 GB) → audio-production'daki ~2,4 GB esas alınır; 2 GB'ı aştığı için kullanıcı kararı.
- `editing-craft.md:24, 58, 544`, `footage-analysis.md:187` ("süper çözünürlük yalnız 4x") → 4x `VTSuperResolutionScaler` için doğru ve o reddedildi. Ama ayrı bir API olan `VTLowLatencySuperResolutionScaler` (macOS 26+) bu M2'de indirme istemeden şunları veriyor (yerel sonda): 720x480, 720x576 ve 960x540'ta 1,5x ve 2x; 1280x720'de 1,5x.
- `claude-code-ecosystem.md:86`, `video-framework.md:305` (`HYPERFRAMES_NO_AUTO_INSTALL`) → yalnız CLI'nin kendini güncellemesini durduruyor; `remove-background`'ın onnxruntime-node (218 MB) ve u2net (176 MB) indirmesini durdurmuyor (kod okundu).
- `image-photo.md:79` (`remove-background` video matı için alternatif) → ilk çalışmada sormadan ~394 MB kuruyor; yerine Vision kişi bölütlemesi video kipi önerildi.
