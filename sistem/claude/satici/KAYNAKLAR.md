# Satıcı (vendor) bileşenleri — sabit sürümler

| Bileşen | Sürüm / commit | Kaynak | Doğrulama | Nerede |
|---|---|---|---|---|
| Remotion resmî becerisi `remotion-best-practices` | remotion-dev/skills @0b5db9daae40f42c73544d1cc0a8c733bd530eaa (2026-10-05; Remotion 4.0.532) | `git fetch` ile commit kimliğinden (`satici.py`) | commit kimliği (içerik doğrulaması git'te); tarball SHA-256 `1eb509ec…` (2026-10-05) | `sistem/claude/skills/remotion-best-practices/` — **depoda tutulmaz** (satıcı deposunda lisans yok); `python3 sistem/claude/satici/satici.py kur` üretir: başa `remotion-ev-kurallari.md`, `agents/` silinir |
| GSAP `gsap.min.js` | 3.15.0 (npm) | `node_modules/gsap/dist/` | npm kilit dosyası | `varliklar/js/` — depoda tutulmaz; `kur.sh` kopyalar |
| HyperFrames becerileri | 2026-10-04T19:03Z `hyperframes skills` ile kuruldu (CLI 0.8.124); commit kaydı yok | heygen-com/hyperframes GitHub HEAD (sabitsiz). `hyperframes skills` (alt komutsuz/update) 2026-10-08'den beri kancada engelli; yalnız `skills check` serbest | yok — `~/.agents/.skill-lock.json` yalnız klasör özetini (`skillFolderHash`) tutuyor; sabit commit + SHA-256'ya geçiş bekliyor | `~/.claude/skills/hyperframes*`, `media-use`, `embedded-captions`, `talking-head-recut`… (21 beceri) |

Güncelleme: `arac-radari` becerisi. `satici.py` içindeki commit'i değiştir, `kur --zorla`, stüdyo başlığını koru, satıcı metnini
yasaklara karşı tara (Google Fonts, Studio açma, lisans anahtarı, uzak varlık, `@latest`).
