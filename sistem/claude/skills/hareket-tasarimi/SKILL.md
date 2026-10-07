---
name: hareket-tasarimi
description: Use when a motion graphic or code-made animation is wanted - product or feature promo from screenshots, explainer or algorithm animation, UI or logo animation, loader or spinner, terminal demo GIF, data viz, requested kinetic type, 3D logo spin, App Store preview, GIF/WebP/APNG/Lottie export - or when choosing between HyperFrames, Remotion, Manim, Three.js and Blender (hareket tasarımı, animasyon, tanıtım videosu, logo animasyonu, yükleniyor, terminal GIF, 3B).
---

# Hareket tasarımı

**İlke:** motor HyperFrames'tir (Apache-2.0, kurulu); başka araç yalnız açıkça daha iyiyse ve lisansı izin veriyorsa.
Her görsel iddia bir snapshot ya da temas sayfasına dayanır. Yazı yalnız istenirse; anlatımı hareket, kadraj ve sıra taşır.

## Ne zaman / ne zaman değil
- **Evet:** tanıtım, açıklayıcı, UI/logo, yükleniyor, terminal, veri, 3B logo, mağaza önizlemesi, GIF/Lottie.
- **Değil:** gerçek çekim `kurgu-zanaati`; ses `ses-tasarimi`; fotoğraf `gorsel-uretim`; teslim `teslim-denetimi`; kurulum `arac-radari`; Remotion kodu `remotion-best-practices` (önce lisans kapısı).

**Yalnız bunları sor** (tek mesaj, varsayılanlı):
- Platform, en-boy (vars. 16:9; UI 60 fps, sinematik 24–30).
- Yazı olacak mı (vars. yok)?
- Ses kaynağı (`ses-tasarimi`).
- Yükleniyor platformu: web, iOS, Android, RN, Flutter.
- Marka rengi, yazı tipi, lisansı.
- Eksik girdi: logo SVG; demolanacak komut ve depo (yan etkisiz mi?).
- Remotion düşünülüyorsa `BRIEF.md` → Lisans bağlamı.

## Hızlı başvuru
| İş | Araç | Durum |
|---|---|---|
| Tanıtım, UI, logo, veri, denklemsiz graf | HyperFrames + GSAP/SVG | kurulu |
| React, veriyle şablon, açık istek | Remotion 4.0.533 | kurulu, lisans kapısı |
| Denklem, morf | Manim CE 0.21 | yok |
| 3B logo | Three.js, HyperFrames içinde | yok (20 MB) |
| Gerçekçi 3B | Blender | yok (~1,3 GB) |
| Terminal | gerçek çıktı + `code-terminal-run`; agg | agg, mono yazı tipi yok |
| Web yakalama | puppeteer-core `page.screencast` | kurulu |
| Uygulama içi yükleniyor | web SVG + CSS; native Lottie | lottie yok |
| GIF/WebP/APNG | `render --format gif`, ffmpeg, `img2webp` | kurulu |

Kurulum, lisans, Remotion: [araçlar](references/araclar.md).

## Kurallar
1. **Remotion (4.x) lisans kapısı:** kişisel, yalnız dosya teslimli serbest ya da ≤3 kişilik iş. Şirket 4+ kişi, müşteri kodu çalıştıracak ya da bağlam bilinmiyor → HyperFrames (sor). 5.x yok.
2. **Yönlendirme bu becerindir.** `hyperframes` yönlendiricisi (intake, Studio tanıtımı) atlanır; `motion-graphics`, `general-video`, `product-launch-video`, `faceless-explainer`, `pr-to-video` yalnız başvurudur. Atlanır: `auth`/`usage`/`feedback`, `/media-use`, `audio.mjs` (HeyGen, NC müzik), `fetch-sfx`, onaysız `catalog --on-device`; `capture` yalnız `--skip-vision`.
3. **Yerel varlık:** CDN'deki GSAP → `vendor/`; yazı tipleri yerel latin + latin-ext woff2 (mono: [araçlar](references/araclar.md)); kökeni belirsiz registry GLB/ikonu iş için kullanılmaz.
4. **Zaman:** tek duraklatılmış GSAP zaman çizelgesi; zamanlar k/fps; `Math.random`, `Date`, rAF yok.
   Vuruşa oturtma yalnız `medya muzik` güveni `yuksek`; `hyperframes beats`/BPM ızgarası yok.
5. **Zanaat** ([ilkeler](references/ilkeler.md)): aynı anda tek odak hareketi; kamera `power2/3.inOut`, giriş `expo.out`; kademe 0,03–0,08 sn; yakınlaştırma ≤ kaynak px / çıktı px; döngü tam bir periyot.
6. **Ölçülmüş tuzaklar** (`#root` arka planı, `data-no-timeline`, GIF 10/20/25/50 fps, `lang="tr"`, init'in CLAUDE.md'si): [hyperframes](references/hyperframes.md) → Proje.

## Uygulama
```
source /Users/onurkaya/Projects/video/ortam.sh
medya proje yeni "<ad>" --tur animasyon --kaynak <ekranlar> <logo.svg>
cd $MEDYA/projeler/<tarih-ad>/calisma
HYPERFRAMES_SKIP_SKILLS=1 hyperframes init kompozisyon --non-interactive --example=blank --resolution=landscape
rm kompozisyon/CLAUDE.md kompozisyon/AGENTS.md   # init ürünü; preview/publish önerir
hyperframes catalog --query "<hareket>"; hyperframes add <öğe> --dir kompozisyon --no-clipboard --json
```
Remotion seçildiyse `init` yerine [araçlar](references/araclar.md) → Remotion. Yapım `medya-hareket` ajanında; büyük işte `medya-uretim`. Şablon düzeltmeleri: [hyperframes](references/hyperframes.md).

## Doğrulama (geçmeden "bitti" denmez)
1. `hyperframes lint kompozisyon` 0 hata; `hyperframes check kompozisyon --at-transitions --json` `"ok": true`. Çalışan dosyalarda dış adres yok ([hyperframes](references/hyperframes.md) → Proje'deki grep boş).
2. `hyperframes snapshot kompozisyon --describe false --at <anlar>` → Read. Hareket: `hyperframes keyframes kompozisyon --selector "#x" --shot ../analiz/k.png`; yazı keskinliği: `snapshot --zoom "#x"`.
3. Render sonrası `medya kontak` → Read; teslimde `teslim-denetimi`. Bilerek sessiz teslimde `medya denetle … --sessiz`.
4. GIF/WebP/APNG: `$MEDYA/.venv/bin/python $MEDYA/sistem/claude/skills/hareket-tasarimi/scripts/dongu.py X.gif --fps F [--opak] [--kb N] [--tek-sefer]` → GEÇTİ (README GIF'i `--opak`).
5. Şablon/toplu işte iki render (`--no-browser-gpu --experimental-fast-capture=false`) framemd5 aynı.

**Ölçülemez:** akıcılık hissi, Safari/iOS görünümü; raporda izlenecek saniyeler yazılır.

## Sık hatalar
- Ekran görüntüsünü kaynak çözünürlüğünün üstünde büyütmek → bulanık yazı.
- Döngünün son karesi = ilk kare → 1 kare takılma.
- Terminal çıktısını uydurmak; doğrusu `script -q` ile gerçek çıktı, kişisel yol temizlenip söylenir.
- Uygulama içi yükleniyor için video/GIF vermek.
- Remotion Studio'yu ya da `preview`'ı kendiliğinden açmak.
- Yayımlanmamış ürün görüntüsünü sormadan Read ile açmak (istenmezse yalnız sayısal mod).

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/animation-motion.md` (+ video-framework.md, claude-code-ecosystem.md, `sistem/devam/ham/arastir-remotion.json`); eskidiyse `arac-radari`.
