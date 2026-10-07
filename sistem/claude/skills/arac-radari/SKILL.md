---
name: arac-radari
description: Use when a new media tool, model, app, plugin or MCP server is mentioned or requested (including paid or cloud services such as Higgsfield, Runway, ElevenLabs), when asked whether to add, replace or upgrade a tool or to keep the studio current, when the periodic tech radar is due, when disk space runs low, or when a media project has just finished (yeni araç, yeni model, sisteme ekleyelim mi, güncelle, daha iyisi var mı, radar, disk doldu, ders).
---

# Araç radarı

Değerlendirme, benimseme, yükseltme, radar, ücretli araçlar, disk, dersler.
**İlke:** beceriler aracı değil yeteneği çağırır (`medya <komut>`). Araç ancak birincil kaynaklı lisans, bu Mac'te
ölçüm ve bilinen-cevaplı sınamayla mevcut sağlayıcıyı geçerse kayda girer. İndirme, kurulum, silme, geçiş: boyutu
söyle, kullanıcı onaylasın.

## Ne zaman / ne zaman değil
- **Ne zaman:** araç/model adı; "ekleyelim mi", "güncel tut"; yetenek yetersiz; radar; disk azaldı; proje bitti.
- **Değil:** medya işi → `medya-studyo`, `kurgu-zanaati`, `hareket-tasarimi`, `ses-tasarimi`, `gorsel-uretim`, `teslim-denetimi`.

## Hızlı başvuru
| Durum | Yap |
|---|---|
| Ad yok ("yeni bir model çıkmış") | Adı/bağlantıyı ve amacı sor; aday taraması yapma |
| Ad belli | Önce [bilinen kararlar](references/bilinen-kararlar.md); karar yoksa kapılar (`medya-gozcu` ajanı ya da doğrudan) |
| Toplu / aylık | `Workflow({scriptPath: '/Users/onurkaya/Projects/video/.claude/workflows/medya-radar.js', args: {}})` (tek araç: `{konu: '<ad>'}`) — kurmaz, rapor `sistem/radar/` |
| Onaylı benimseme | [benimseme](references/benimseme.md) |
| Ücretli/bulut araç | İstek açık onay değil; kapı 1'de dur. Yerel karşılık: görsel → `gorsel-uretim` (ağır üreteç yalnız harici SSD, kullanıcı kararı), video → `hareket-tasarimi` (HyperFrames); üretken video yok. Kayıt kapalı ([benimseme](references/benimseme.md) §7) |
| GUI uygulaması (Resolve, Kdenlive) | `tur = "uygulama"`, kapalı; köprü `medya nle` (.otio) |
| Sürüm yükseltme (HyperFrames, Remotion), disk | [güncelleme ve disk](references/guncelleme-ve-disk.md); disk raporu `medya temizle` |
| Proje bitti | `sistem/dersler.md` en üstüne `## YYYY-AA-GG — <proje>`: ne oldu, ölçüm, çözüm; tekrar eden ders beceriye (`→ <beceri>`) |

## Kapılar — sırayla, ilk "hayır"da dur
1. **Yerel, ücretsiz:** hesap, giriş, kredi, kapılı (gated) indirme yok.
2. **Lisans:** kod ve ağırlık ayrı, LICENSE/model kartından; etiket yetmez, yeniden yüklemede upstream'e git. `ticari`: bölge/gelir/çıktı kısıtı → `kosullu`; NC → `hayir` (yalnız kişisel iş, açıkça söyle); belirsiz → girmez.
3. **Bu Mac:** M2, 16 GB, fansız; Metal/MLX/CoreML/MPS yolu şart. Kurulumdan sonra ≥5 GB + beklenen çıktının 2 katı boş kalmalı. Yerel video difüzyonu: yok; büyük üreteçler yalnız harici SSD'de (kullanıcı kararı).
4. **Gizlilik:** telemetri kapatma değişkeni aracın kendi kodundan (DO_NOT_TRACK her araçta çalışmaz); ağsız çalışmalı.
5. **Ajan sürülebilir, bakımlı:** başsız CLI/API, yakın tarihli sürüm.
6. **Ölçülebilir üstün:** aynı fikstürde eski/yeni A/B; satıcı sayısı kanıt değil.

Her kapıya kaynak URL + tarih. Komutlar: [değerlendirme](references/degerlendirme.md). Red kararı bilinen kararlara satır olur.

## Benimseme kuralları
- `[[saglayici]]` yalnız `ad tur lisans ticari kurulum kontrol boyut_mb etkin onay not`; `[[yetenek]]`'te `aciklama` zorunlu. Aksi hâlde `kayit.yukle()` TypeError verir: `medya yetenekler`/`kur` durur, `sahneler` sessizce ffmpeg'e düşer. Sürüm/ölçüm `not`'a.
- `boyut_mb` ilk kullanımda inen modelleri de sayar. Ağır Python `ortamlar/<alan>`; `.venv`'e elle kurma (`uv sync` siler).
- Sıra: kayıt → `medya kur <ad>` → uyarlayıcı `medya/komutlar/` → sınama `testler/` → eski sağlayıcı `yedek` → kardeş beceri + `sistem/arastirma/<YYYY-AA-GG>/`.
- İstenmeden yeni komut, kayıt alanı ya da klasör icat etme.
- **Ücretli/bulut:** yalnız `tur = "bulut-ucretli"`, `etkin = false`, `onay` (maliyet + giden kişisel medya); uyarlayıcı yok. Açmadan önce maliyet, çıktı hakları ve giden medya gösterilir; açılsa bile stüdyo sürmez, kullanıcı kendi hesabında üretir (§7).
- **Apple ML sağlayıcısı:** `apple_calistir` bekçisi + Neural Engine'siz yedek (derleyici sessizce asılabilir).
- **Satıcı becerisi:** sabit commit + tarball SHA-256, `sistem/claude/satici/KAYNAKLAR.md`; `npx skills` asla (kanca engeller).

## Doğrulama — "tamam" demeden
- Her kapıda tarihli birincil kaynak; şüpheci ikinci geçiş aynı sonuç.
- `medya yetenekler --saglayicilar` → kurulu; `medya test <yetenek>` ve tam `medya test` geçti (önce/sonra sayısı).
- Bu Mac'te `/usr/bin/time -l` (süre, tepe bellek), `sysctl vm.swapusage`, `df -h` önce/sonra.
- Ağsız: `sandbox-exec -p '(version 1)(allow default)(deny network*)' <komut>` biter.
- Doğrulanamayanı yaz: uzun işte ısıl kısılma, öznel kalite (kullanıcı izler/dinler), lisansın hukuki yorumu.

## Sık hatalar
- Verilmiş "yok" kararını yeniden açıp büyük indirme önermek.
- Yeniden yükleyenin kartını lisans saymak.
- Yükseltmede birden çok bileşen (Remotion paketleri istisna: hepsi birlikte); satıcı becerisini taramadan güncellemek.
- Benimsemeyi tek büyük iş akışına koymak; bağımsız işleri küçük akışlara böl (devam önek tabanlı).
- Eski durum ya da bayat sayı (disk, sınama, sürüm) üzerine plan: o an ölç.
- Onaysız `medya temizle --uygula`.

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/` (claude-code-ecosystem.md, video-framework.md, eksiklik-elestirisi.md), `sistem/devam/`; eskidiyse `medya-radar` çalıştır.
