---
name: remotion-best-practices
description: Use when writing, editing, previewing or rendering Remotion (React/TSX) video code in this studio — compositions, sequences, springs, transitions, captions, media, charts, maps. Load hareket-tasarimi first for engine choice and the license gate. (Remotion, React video, TSX animasyon)
version: 4.0.532
---

> **Stüdyo kuralları — önce bunlar; aşağıdaki satıcı metniyle çelişirse bunlar geçerlidir.**
> - Remotion yalnız lisans kapısı geçilince: kişisel iş, yalnız dosya teslim edilen tek kişilik serbest iş ya da
>   en çok 3 kişilik şirket/ekip (`BRIEF.md` → Lisans bağlamı; boşsa sor, yanıt yoksa HyperFrames). Ayrıntı: hareket-tasarimi.
> - Studio'yu kendiliğinden AÇMA (yerel ağa açılır; npm ve bugs.remotion.dev'e istek atar). Doğrulama:
>   `remotion still` + `medya kontak`. Kullanıcı isterse: `$MEDYA/node_modules/.bin/remotion studio --no-open`.
> - `licenseKey`, `--public-license-key`, `Config.setPublicLicenseKey` ASLA ('free-license' de kullanım olayı gönderir).
>   "Render in browser" / `@remotion/web-renderer`, Lambda, Cloud Run, Vercel yok.
> - Google Fonts yok → `@remotion/fonts` + `public/fonts/` (latin + latin-ext woff2; symlink değil kopya). Uzak varlık
>   yok (remotion.media, `@remotion/sfx`, Mapbox/MapTiler, ElevenLabs) → yerel, CC0 ya da kodla üretilmiş.
> - `npx create-video`, `remotion upgrade`, `npx skills`, `@latest` yok: proje `medya proje yeni … --motor remotion`
>   ile açılır; sürüm sabit (4.0.533; beceri metni 4.0.532 için, yama farkı). Komutlar `$MEDYA/node_modules/.bin/remotion …` (proje klasöründen).
> - Ekrana yazı yalnız istenirse. Son çizimde `--image-format=png --color-space=bt709` (bt709 şart; PNG bağımsız ölçümde
>   VMAF 96,97 → 98,80, süre ×1,24). `Math.random` yerine `random(seed)`.
> - 3B ve Lottie kurulu (2026-10-09): @remotion/three, three 0.178.0, R3F 9.2.0, @remotion/lottie, lottie-web 5.13.0.
>   Örnekleri `src/Ornek3B.tsx` ve `src/OrnekLottie.tsx`. `npx remotion add` kullanılmaz. 3B'de `--gl` gerekmez (bayrak ayarı ezer):
>   şablonun `angle` ayarı WebGL'i GPU'da çalıştırır (ANGLE Metal). Ayarsız Remotion CPU'ya (SwiftShader) düşer; 90 karede
>   6,3 sn, angle'da 3,9 sn. Lottie JSON'u yerelde durur (`public/` + `staticFile`); lottiefiles adresi kullanılmaz.
>   1 Remotion karesi = 1 Lottie karesi; JSON'un `fr`'si fps'ten farklıysa `playbackRate={fr / fps}`.
> - Satıcı kaynağı: remotion-dev/skills @0b5db9d (2026-10-05, tarball SHA-256 1eb509ec…); güncelleme arac-radari ile.

