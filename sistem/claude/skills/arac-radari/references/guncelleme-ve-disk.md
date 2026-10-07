# Güncelleme ve disk bütçesi

İçindekiler: 1 Güncellik denetimi · 2 Yükseltme kuralları · 3 HyperFrames (3b Remotion) · 4 ffmpeg · 5 Python ortamları · 6 Disk

## 1. Güncellik denetimi (salt okunur)
- `npm outdated` (package.json tam sürüme sabit; sonucu her seferinde yeniden çalıştır, eski çıktıya güvenme).
- `npm view <paket> version license time.modified`
- `arac/uv pip list --outdated --python ortamlar/ses/bin/python` ve `--python .venv/bin/python`
  (örnek, yeniden çalıştır: ses ortamında dolaylı bağımlılık mpmath).
- İkililer: `arac/ffmpeg -version | head -1` (6.0, 2023), `arac/ffprobe -version | head -1` (4.4.1, 2021). npm
  sarmalayıcısı güncel görünse de içindeki ikili eski olabilir.
- Satıcı becerileri: `hyperframes skills check` (yalnız denetler; güncelleme §3.6).
- Son radar: `ls sistem/radar/ 2>/dev/null` — yoksa ya da en yenisi 30 günden eskiyse radar öner.
Bulguyu liste olarak sun; her yükseltme ayrı onayla.

## 2. Yükseltme kuralları
- Bir seferde tek bileşen. Öncesi: sürümler, `medya test` sonucu ve değişecek dosyaların kopyası (`package.json`,
  `package-lock.json`, `uv.lock`, `pyproject.toml`, `yetenekler.toml`). Sonrası: aynı ölçümler. Geri dönüş komutu
  başlamadan yazılı.
- Gerekçe yoksa dolaylı bağımlılığı (ör. mpmath) yükseltme.
- Deneme çıktıları sabit geçici klasörde: `G="$TMPDIR/medya-yukseltme"; mkdir -p "$G"`. Bash çağrıları arasında
  değişken korunmaz: her komutta `G`'yi yeniden tanımla. İş bitince `rm -rf "$TMPDIR/medya-yukseltme"` (yalnız kendi
  deneme dosyaların).

## 3. HyperFrames
1. Önce: `hyperframes --version`; `hyperframes --help > "$G/yardim-once.txt"`; sürüm notlarını oku
   (github.com/heygen-com/hyperframes/releases): varsayılan değişikliği, telemetri, yeni ağ ya da hesap komutu.
2. Deneme projesi: `hyperframes lint testler/hyperframes-baslik`, `hyperframes check testler/hyperframes-baslik`,
   `hyperframes render testler/hyperframes-baslik --quality draft -o "$G/once.mp4"`.
3. `npm install -D --save-exact hyperframes@<sürüm>`
4. Sonra: `hyperframes doctor`; aynı lint, check ve render → `"$G/sonra.mp4"`; ikisinde `medya incele` (süre, fps,
   boyut) ve `medya denetle`; kare karşılaştırması kareler doğrudan çözülerek (`testler/test_temel.py` `_kareler`),
   ffmpeg `psnr` süzgeciyle değil.
5. `hyperframes --help | diff "$G/yardim-once.txt" -` → sunucuya ya da hesaba giden yeni alt komut varsa
   `sistem/claude/hooks/medya-koruma.py` içindeki `YASAK` kümesine ekle, `testler/test_koruma.py` `ENGELLENMELI`
   listesine örnek koy, `medya test koruma` (öncesi ve sonrası sınama sayısını o an `medya test koruma` çıktısından al). Not: `events` ve `upgrade` bugün `YASAK`
   içinde değil; araştırma ikisinin de engellenmesini önerdi.
6. Satıcı becerileri: `hyperframes skills update` en yeniyi çeker (yardım metni) — yalnız hyperframes yükseltmesiyle
   birlikte, bilerek; ardından [değerlendirme](degerlendirme.md) §4 taraması (`~/.claude/skills/hyperframes*`,
   `media-use`, `music-to-video`…) ve `sistem/claude/satici/KAYNAKLAR.md` satırını yeni sürümle güncelle. Satıcı
   dosyalarını düzenleme (güncelleme ezer); çelişkiyi kanca ve `medya-studyo` yönlendirmesi karşılar.
7. Diğer satıcı becerileri (ör. `remotion-best-practices`): sabit commit'in tarball'ı
   (`https://codeload.github.com/<kurum>/<depo>/tar.gz/<commit>`) → `shasum -a 256` → commit ve SHA-256
   `KAYNAKLAR.md`'ye; stüdyo kuralları bloğunu koru; metni yasaklara karşı tara (Google Fonts, Studio açma,
   lisans anahtarı, uzak varlık, `@latest`). `npx skills` asla: telemetri ve sabitsiz sürüm (kanca engeller).
Geri dönüş: `npm install -D --save-exact hyperframes@<eski>`, sonra 2. adımı yinele.

### 3b. Remotion (sabit ikinci motor)
- `remotion` ve bütün `@remotion/*` paketleri (package.json'da hepsi aynı tam sürüm) tek seferde, aynı sürüme:
  `npm install -D --save-exact remotion@<s> @remotion/cli@<s> …` (package.json'daki her `@remotion/*` satırı).
  Ayrı ayrı yükseltme yok; `remotion upgrade` kancada engelli.
- 5.x'e geçiş ya da lisans metni değişikliği → önce lisans incelemesi ([bilinen kararlar](bilinen-kararlar.md)).
- `react`, `react-dom`, `zod` yalnız Remotion yeni sürümü gerektirirse ve onunla birlikte yükseltilir; `npm outdated`
  satırı tek başına gerekçe değildir.
- Önce/sonra: `medya test` ve kancanın Remotion sınamaları (`medya test koruma`).

## 4. ffmpeg
- Varsayılan ffmpeg-static 6.0 kalır. Homebrew `ffmpeg` 9.0.2'de vidstab, zscale, libass, drawtext yok;
  `ffmpeg-full` 9.0.2'de var ama Homebrew Xcode lisansı ister (kullanıcının kararı). martin-riedl.de 9.0.2 statik
  derleme: zimg ve libass var, vidstab yok → kapıdan geçmez.
- `ffmpeg-full` yolu, yalnız kullanıcı `sudo xcodebuild -license accept` çalıştırdıktan sonra (2026-10-05'te brew
  formül komutları bu yüzden hata veriyor; aşağısı sınanmadı): `brew deps --tree ffmpeg-full` (bağımlılık ağacı;
  boyutu söyle ve sor) → `brew install ffmpeg-full`. Keg-only olduğu için PATH'e bağlanmaz; ikili
  `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`.
- Aday kapısı — 14 süzgecin hepsi listelenmeli (2026-10-05'te `arac/ffmpeg`te 14/14). `medya` kodu zscale, tonemap,
  minterpolate, alimiter, ebur128, blackdetect, freezedetect kullanır; vidstab, xfade, loudnorm, lut3d, libvmaf,
  scdet zanaat ve denetim adımlarının dayanağıdır:
  `<aday>/ffmpeg -hide_banner -filters | awk '{print $2}' | grep -xE "zscale|tonemap|vidstabdetect|vidstabtransform|minterpolate|xfade|loudnorm|alimiter|lut3d|libvmaf|ebur128|blackdetect|freezedetect|scdet"`
- Yan yana kur (ör. `arac/ffmpeg9/`). `medya` önce `arac/` içindeki ikiliyi kullanır: A/B için `arac/ffmpeg`
  bağlantısını geçici olarak adaya çevir, `medya test` ve `medya incele testler/veri/hdr_hlg.mp4` karşılaştır,
  bağlantıyı geri al. Geçiş yalnız ölçülebilir kazançla; eskisi `yedek` olur.
- ffprobe 4.4.1 eski: üst veri çelişirse `arac/ffmpeg -i <dosya>` ile doğrula.
- ffmpeg-static `--enable-nonfree` ile derlenmiş: çıktılar serbest, ikiliyi dağıtma.

## 5. Python ortamları
- `ortamlar/<alan>`: `arac/uv pip install --python ortamlar/<alan>/bin/python '<paket>==<sürüm>'` → `medya test <yetenek>`.
- `.venv`: yalnız `pyproject.toml` + `arac/uv sync --extra analiz` (elle kurulan paket silinir).
- torchaudio 2.9 ve sonrası ses okumada TorchCodec ister; `soundfile` ortamda kalsın, araçlara WAV ver.

## 6. Disk bütçesi
- Ölç: karar anında `df -h /Users/onurkaya/Projects/video` ya da `medya temizle` (sabit sayıya güvenme). `du` uv klonlarını iki kez sayar.
- Rapor: `medya temizle` — yalnız rapor; uv önbelleği, `testler/.gecici`, HyperFrames kare önbelleği; `modeller/`'e
  dokunmaz. Kullanıcı onayıyla `medya temizle --uygula` (uv önbelleğinin tamamını siler; sonraki kurulum yeniden
  indirir). Projelerin `calisma/` klasörleri için `--calisma`, ayrıca sorarak.
- Elle: `hyperframes clean --dry-run [proje]` → onay → `hyperframes clean [proje]` (`--snapshots` snapshot
  klasörlerini de alır); `arac/uv cache size` → `arac/uv cache prune` (yalnız sarkık girdiler) ya da
  `arac/uv cache clean` (tümü).
- Stüdyo dışında, sorarak: `~/.npm` önbelleği (2026-10-05: 1,3 GB) `npm cache clean --force`.
- Kural: kurulumdan sonra ≥5 GB + 2 × beklenen çıktı. Yer yoksa kurma: isteğe bağlı aracı iş için kur, işten sonra
  kaldır, ya da harici SSD (kullanıcı kararı). Silmeden önce ne silineceğini ve boyutunu göster.
