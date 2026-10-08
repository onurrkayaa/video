# Stüdyo durumu — kaldığımız yer

**2026-10-08 — ÖNERİLER UYGULANIYOR: dalga 1 (O1, O2, O7) bitti, yerel commit'lendi; sırada dalga 2 (O4, O5).**
Kullanıcı: "hepsini sırayla uygula", Resolve kur (en iyisi), GitHub'a gönder, Z-Image-Turbo + VoxCPM2 8-bit + Remotion
3B/Lottie kur ("Z-Image-Turbo'dan sonra FLUX.2'ye gerek kalmıyorsa sil, gerek varsa dursun"). Kullanıcı adımları bitti
(Mac yeniden başlatıldı, Resolve App Store'dan kuruldu, Kdenlive içe aktarımı yapıldı, VS Code'a erişilebilirlik izni verildi).
Yapıldı: O5 (NLE devri ölçüldü: Resolve kare-kesin; Kdenlive için `-kdenlive.otio`), Resolve kaydı + Media Storage
(`projeler/`), npm önbelleği, dalga 1. Sıra: dalga 2 O4 → O5 doğrulaması · dalga 3 O3 (şüpheci düzeltmeli) → O6 · dalga 4
ekler (`sistem/yonetim/2026-10-08-ekler.json`: VoxCPM2 8-bit → Z-Image-Turbo → Remotion 3B/Lottie) · sonda tam sınama +
git push. Her dalga `medya-guncelle`, args `sistem/devam/guncelle-dalga<N>-args.json` (commit: true, push yok).
Dalga 2'den önce önerilen: O1 düzeltme turu (aşağıda "Öneriler" 1).
(Uzun bir iş yarıda kalırsa bu dosyaya "DURAKLATILDI" + devam sırası yazılır; kurallar CLAUDE.md "Uzun işler".)

## Dalga 1 sonucu (2026-10-08, iş akışı wf_01974d14-cc6)
- O1 koruma kancası, sessiz indirme ve sabit sürüm: uygulandı; bağımsız doğrulama bir düzeltme turundan sonra da
  GEÇMEDİ (açık bulgular "Kalanlar"da). Kanca artık şunları engelliyor: ses/video girdili `hyperframes transcribe`
  (.json/.srt/.vtt serbest), `init --video|--audio` (`--skip-transcribe` yoksa), `tts`, `models install`, `upgrade`,
  `skills` (`check` dışında), embedded-captions `prepare.sh`/`transcribe.cjs`/`matte.cjs`, media-use `transcribe.mjs`,
  sürüm sabitli whisperx. `medya test koruma` 65 → 131. Alt yazı yolu: medya-studyo "Alt yazı istenirse".
- O2 disk payı: tamam. `medya temizle --uygula` +0,25 GB açtı, geçici (`medya test` geri dolduruyor); npm `_cacache`
  silindi, `_npx` bilerek kaldı. Ders + arac-radari §6; gelistirme.md'ye 2 madde.
- O7 mflux stüdyonun Python'una: tamam. CPython 3.13.16 (`.uv/python`, SHA-256 yayımlananla aynı); mflux 0.21.0 ortamı
  yeniden kuruldu, 56 paket `sistem/kisitlar/mflux-0.21.0.txt`'e sabit; `ortam.sh` → `UV_MANAGED_PYTHON=1`; 2 yeni
  sınama (kırmızı→yeşil denendi); CLAUDE.md "Ortam gerçekleri" güncellendi. Aynı tohum taşımadan önce/sonra piksel
  piksel aynı (256²; 1024² ölçülmedi).
- Kapanış sınaması (12:35–12:37): `medya test` 172 geçti, 2 atlandı (ikisi de `--agir` ister), 70,4 sn, çıkış 0.
  Ağır sınamalar dalga içinde geçti: `medya test gorsel --agir` (O7), VoxCPM2 Türkçe sınaması (O2).

## Kalanlar (doğrulama bulguları; uygulanmadı)
- O1 kanca. Kapanışta çalışan kancayla yeniden ölçüldü: 15 durumdan 13'ü beklenenden farklı çıktı.
  - Yanlış engel (yeni gerileme): indirmesiz içe aktarım yönlendirme ya da satır devamı eklenince engelleniyor:
    `… transcribe a.srt -d komp 2>&1 | tail -5`, `>/dev/null 2>&1`, `2>/dev/null`, `t.json --to srt --json > x.json`,
    `a.srt \` + satır sonu. Kök neden `indirme_denetle`: shlex jetonları (`2`, `>&`, `1`, `>`, hedef, `\n`) girdi
    sayılıyor. Engel iletisi .srt girdisine de "ses/video girdisinde" diyor.
  - Kaçak: girdisi görünmeyen `ls *.wav | xargs -n1 npx hyperframes transcribe` geçiyor. Girdi listesi boşken de
    engellenmeli; CLI girdisiz çağrıda zaten düşüyor.
  - Önceden var olan kaçaklar (yeni kuralları da aşıyor, gelistirme.md'de yok): `timeout`/`caffeinate`/`nice`
    sarmalayıcıları (`timeout 600 npx hyperframes cloud render` dahil), ikili adından hemen sonra satır devamı,
    `pip install whisperX`, `python3 -m pip install whisperx`.
  - Belge: "`init -vv.mp4`/`-yv v.mp4` video atıyor" yalnız parseArgs için doğru; gerçek CLI (`cli.js`
    assertKnownFlags) bu bayrakları reddediyor. dersler.md, `testler/test_koruma.py:89` ve kanca belge dizisi "parseArgs
    böyle okur, cli.js reddeder, kanca temkinli engeller" diye düzeltilmeli.
- O2 belge: "takas iş bitince bırakmaz" kesin kural gibi yazılmış (dersler.md, guncelleme-ve-disk §6). Ölçülen:
  takas ≥ 19 dk yerinde kaldı; yeniden başlatmadan geri alınıp alınmadığı ölçülmedi. "Yeniden başlatma `$TMPDIR`
  artıklarını götürdü": olası mekanizma dirhelper, o da yalnız 3 günden eski dosyaları siler. §6'da birimler karışık
  (`df -h` / `df -k`); `arac/uv cache clean` için de "önce source ortam.sh" uyarısı gerek. CLAUDE.md "Disk" satırı eskidi
  ("~3–7 GB boş"; 8 GB ağır ML kuralı yok). CLAUDE.md, README ve `medya/ortak.py` disk iletisi hâlâ `medya temizle
  --uygula`yı çare gösteriyor; ölçülen kazanç ~0,25 GB ve geçici.
- O7 belge: `gorsel-uretim/references/araclar.md` "Üretici" bölümü kendi içinde çelişkili ("çalıştırılmadı", "yalnız
  harici SSD"); aynı eski ifade teknikler.md §10 ve bilinen-kararlar.md'de de var. dersler.md'de `UV_MANAGED_PYTHON=1`
  neden-sonucu yanlış: `uv python find 3.13` değişkensiz de stüdyonunkini buluyor; değişkenin ölçülen etkisi sistem
  yorumlayıcılarını dışlamak. voxcpm2 kaydında `--managed-python` yok, kontrolü hâlâ `ls` (`ls -L` olmalı).
- gelistirme.md'ye yazılanlar: `medya temizle` için `--cache-dir`; 8 GB koşulu kodda yok; kancalar sistem `python3`'üne
  bağlı; media-use `audio.mjs` alt süreçte `tts`/`transcribe` çalıştırıyor.

## Öneriler (ölçülmüş bulgulara dayanır; onaysız uygulanmaz)
1. Dalga 2'den önce O1 düzeltme turu: önce yönlendirme/satır devamı yanlış engeli ve girdisiz `xargs` kaçağı;
   sarmalayıcı kaçakları ya kapatılsın ya gelistirme.md'ye yazılsın. Ölçüt: kapanıştaki 15 durum sınamaya girsin
   (bugün 13 uyumsuz → 0).
2. Belge düzeltmeleri tek turda: yukarıdaki O1/O2/O7 belge maddeleri. Bugün "ölçmeden iddia yok" ilkesine aykırı cümleler var.
3. `medya temizle`: `uv cache clean`'e `--cache-dir KOK/.uv/cache` verilsin, alt süreç argümanı sınansın (gelistirme.md Y).
4. voxcpm2 kaydına `--managed-python` ve `ls -L`: dalga 4'teki VoxCPM2 8-bit kurulumuyla birlikte.
5. Dalga 3 (ağır çekim) ve dalga 4 öncesi diski o an ölç: 12:40'ta 13,1 GB boştu. Dalga 4 kurulumları ~6,9 GB alır,
   geriye ~6,3 GB kalır; bu, ağır ML'nin 8 GB koşulunun altında. Yer açma yolları: yeniden başlatma (takas 2 GiB) ya da
   kullanıcının FLUX.2 kuralı.

## Son durum (sınandı)
- Kuruldu ve ölçüldü: FLUX.2 [klein] 4B (`medya gorsel-uret`; 1024² ~84 sn, 8,8 GB bellek; aynı tohum = aynı görsel;
  2026-10-08'den beri stüdyonun Python 3.13.16'sında), VoxCPM2 4-bit (`medya seslendir`; Türkçe CER %0, ses kimliğiyle
  konuşmacı benzerliği 0,73–0,76), Kdenlive 26.08.1, DaVinci Resolve 21.1.0 (App Store; `medya nle` devri ölçüldü 2026-10-08).
- Baş ajan `medya-yonetici` + iş akışları `medya-yonetim` (öneri) ve `medya-guncelle` (onaylananı uygula);
  oturum özeti kancası. GitHub: https://github.com/onurrkayaa/video (herkese açık, main).
- `medya test`: hafif takım 172 geçti, 2 atlandı (2026-10-08). Ağır üretici sınamaları `medya test --agir` (FLUX.2 ve
  VoxCPM2, 2026-10-08 geçti).

## Kullanıcının kararını bekleyenler
- O1 (isteğe bağlı, genel ayar) · `~/.claude/settings.json` → `skillOverrides`'a iki anahtar: `"embedded-captions": "user-invocable-only"` ve
  `"talking-head-recut": "user-invocable-only"`. Başka hiçbir şey değişmez; kuru birleştirme yapıldı, dosyaya yazılmadı.
- O7 · Kancaların yorumlayıcısı: `medya-koruma.py` ve `oturum-ozeti.py` PATH'teki `python3` ile çalışıyor. O kalkarsa geriye
  `/usr/bin/python3` kalır; o da Xcode lisansı yüzünden 69 ile çıkar ve koruma sessizce düşer. Stüdyonun Python'una
  almak `.claude/settings.json` ve `~/.claude/settings.json` kanca komutlarını değiştirir.
- O7 · python.org 3.13.1 (`/Library/Frameworks/Python.framework/Versions/3.13`) artık stüdyoda kullanılmıyor. Başka
  projelerde kullanılıp kullanılmadığı bilinmiyor; kaldırma kararı kullanıcının. 3.14 (`/usr/local/bin/python3`)
  kancalar yüzünden kalmalı.
- O2 · Disk: dalga 4'ten önce Mac'i yeniden başlatmak (VoxCPM2 sınamasının açtığı 2 × 1 GiB takas duruyor);
  `~/.cache/huggingface` (0,48 GB, stüdyo dışı, sahibi belirsiz); `sleepimage` 2 GiB (`hibernatemode 3`, `sudo pmset`).
- Resolve'da üç sınama projesi kaldı (medya-nle-sinama, -2, -3): Project Manager'dan silinebilir (ajan silmedi: özel
  arayüz, kör tıklama riskli).
- DaVinci Resolve Studio + yerleşik MCP (295 $, ücretli → kapalı) — yalnız açık istekle.

## Arşiv
Ham araştırma/ölçüm: `sistem/devam/` (beceri tanımları `beceri-tanimlari.json`; ağır çekim ölçümü `yavas-cekim/`;
dalga argümanları `guncelle-dalga*-args.json`; iş akışı kimlikleri `ham/calisan-is-akislari.txt`).
