# Dersler

Her projeden sonra kısa, ölçülmüş dersler. Tekrar eden ya da genel ders ilgili beceriye taşınır (taşındıysa
"→ beceri" notu). En yeni üstte.

## 2026-10-08 — HyperFrames 0.8.124 → 0.8.140, çizim sınaması, sabit satıcı becerileri
- **Sınama fikstürünün kendisi ızgara dışıydı.** `testler/hyperframes-baslik` sesleri 0,25 ve 1,55 sn'de başlıyordu:
  çizimde 7,5. ve 46,5. kare (çapraz ilintiyle örnek kesinliğinde ölçüldü). Zamanlar k/30'a çekildi (0,3 / 1,5; GSAP
  0,2 ve 4,3) ve başvuru bundan sonra alındı; yeni sınama eski fikstürde kırmızı. → arac-radari güncelleme-ve-disk §3.
- **Yükseltme kare kare ölçüldü:** 0.8.124 ve 0.8.140 taslak çizimi 150/150 kare piksel piksel, ses örnek örnek aynı;
  mp4'lerde yalnız `hyperframes_version` etiketinin 2 baytı farklı. Aynı sürümde iki çizim bayt bayt aynı (donanım GPU
  yakalaması bu fikstürde belirlenimci). Sürüm notundaki düzeltmeler bu yüzden ölçülmedi, yalnız iddia (gelistirme.md).
- **VMAF eşitliği göstermez:** dosyanın kendisiyle VMAF 97,60 (en düşük 97,42), yani aynı karelerde 100 çıkmıyor.
  Eşitlik için `-f framemd5` ya da doğrudan çözülmüş kareler. → güncelleme-ve-disk §3.
- **Başvuru küçük ve duyarlı tutulabilir:** kare başına 16x9 hücre ortalaması (gri, 44 KB JSON) yazı tipi değişimini
  (başlık Inter'e çevrilince) 134/150, 1 kare kaymayı 23/149 karede yakalıyor (≤ 3 düzey eşik); aynı 64x36 tabandan 4x4
  ızgara kaymayı hiç görmüyor (0/149, en büyük fark 3 düzey).
- **Sabit kopya sessizce devre dışı kalabilir:** `kur.sh` bagla gerçek klasörü atladığı için `~/.claude/skills`'teki
  eski `npx skills --copy` kopyaları (21 beceri × 2 yer, 33 MB; v0.8.124 etiketiyle blob blob aynı) etkin kalır.
  `satici.py dogrula` bunu söylüyor, `bagla --uygula` yedekleyip bağlıyor (sahte ev klasöründe sınandı). Seyrek çekim
  (`--filter=blob:none`, yalnız 21 klasör) 6,5 sn; 931 dosyanın blob SHA'sı commit ağacıyla aynı.
- **Geri alma komutu da sınanır.** `bagla --uygula`'nın yazdığı `tar -xzf <arşiv> -C ~` çalışmıyordu: `~/.claude/skills/<ad>`
  artık bağlantı, bsdtar 3.5.3 içine açmıyor ("Cannot extract through symlink", çıkış 1; yalnız `~/.agents` geri geliyor).
  Python `tarfile` (filter="data") bağlantıyı izleyip eski içeriği sabit kopyanın üzerine yazıyor, çünkü
  `sistem/claude/skills` ev klasörünün içinde. Çözüm `bagla --geri <arşiv> [--uygula]`: önce yalnız sabit kopyayı gösteren
  bağlantı kalkar, sonra arşiv açılır; yerde gerçek klasör varsa hiçbir şeye dokunmaz. Gerçek boyutta karalama kopyasıyla
  (42 klasör, 1.852 dosya, 33 MB) bağlama 1,4 sn, geri alma 0,7 sn; dosyalar ve kipleri asıllarla aynı.

## 2026-10-08 — koruma kancası düzeltme turu: yönlendirme, satır devamı, sarmalayıcılar
- **shlex jetonları kabuk gibi okunmalı.** `punctuation_chars` yönlendirmeyi ayrı jetonlara böler (`2>&1` → `2` `>&`
  `1`), satır devamı (`\` + satır sonu) `\n` jetonu olur; ikisi de argüman sayıldı. Etki iki yönlüydü: indirmesiz
  `transcribe a.srt … 2>&1 | tail`, `> sonuc.json` ve satır devamlı içe aktarım engellendi; `npx hyperframes \` + satır
  sonu + `cloud render` geçti. Çözüm: işleç + hedef + önündeki fd rakamı bölümden çıkar (`bash < betik` girdisi betik
  olarak denetlenir), satır devamı ayrıştırmadan önce silinir. Kapanış ölçümünün 15 durumu: 13 uyumsuz → 0. → kanca.
- **Önek = sarmalayıcı + bayrak değeri.** `timeout 600`, `caffeinate -i -t 3600`, `nice -n 10`, `/usr/bin/env -u X`,
  `xargs -n 1`: değer atlanmayınca değer komut sanıldı ve `cloud render` dahil her kural aşıldı. Önek tablosu artık değer
  alan bayrakları tutuyor (bu Mac'in man sayfaları; timeout GNU/FreeBSD, bu Mac'te yok), yolun son parçasıyla eşleşiyor.
- **Görünmeyen girdi denetlenemez:** `xargs … transcribe` girdiyi stdin'den alır; girdisiz çağrı artık engelli. Bedeli
  yok: CLI girdisizi 'Missing required positional', fazla girdiyi 'Unexpected extra argument' ile çalıştırmadan
  reddediyor (kodda okundu). PyPI adı büyük/küçük harf duyarsız: `pip install whisperX` ve `python3 -m pip install
  whisperx` ön süzgeçten bile geçiyordu.
- **Yanlış engeli gerçek komutlarla ölç:** oturum kayıtlarındaki 6.942 benzersiz Bash komutu ve 10.804 belge parçası iki
  kancaya verildi (çalıştırılmadan): oturum komutlarında karar farkı 0, belgede 2 (ikisi de girdisiz `transcribe`). 39
  yeni sınamanın 30'u özgün kancada kırmızı; `medya test koruma` 131 → 170. Kalan kaçaklar gelistirme.md'de.
- **Kancayı canlı yoklama:** `true || <komut>` biçimli canlı deneme (komut çalışmaz) otomatik kipte "Self-Modification"
  diye reddedildi (ilk deneme geçmişti). Kanca kararı JSON stdin sınamalarıyla doğrulanır. Bağımsız doğrulayıcı aynı
  biçimle 3 canlı yoklama yaptı: yönlendirmeli `… transcribe a.srt -d komp >/dev/null 2>&1` geçti; `timeout 600 npx
  hyperframes cloud render` ve `ls *.wav | xargs -n1 npx hyperframes transcribe` doğru iletiyle engellendi (özgün kanca
  ikisini de geçiriyordu).

## 2026-10-08 — mflux ortamı stüdyonun Python'una taşındı
- **Ortam stüdyo dışındaki Python'a bağlıydı, sağlık denetimi bunu göremiyordu.** `.uv/tools/mflux` python.org
  3.13.1'i gösteriyordu (sistem `python3` 3.14'e geçmişti); `ls` kopuk bağda 0 döndürür (`ls -L` 1), yani 3.13
  kaldırılsa `gorsel-uret` bozulur ama sağlayıcı "kurulu" görünürdü. Kontrol `ls -L` + yorumlayıcı; yeni sınama bütün
  ortamların `.uv/python`'da olduğunu denetliyor (eski ortamın klonuyla kırmızıda sınandı). → arac-radari (benimseme §1–2).
- **Taşıma ölçüldü:** 56 paket `sistem/kisitlar/mflux-0.21.0.txt`'e donduruldu; `--managed-python --python 3.13.16
  -c …` 13,8 sn, `uv pip freeze` önce/sonra aynı; 256², 2 adım, tohum 3: çözülmüş pikseller aynı (en büyük fark 0).
  CPython arşivi SHA256SUMS ile aynı (`9e01f63b…`), uv bozuk arşivi "Hash mismatch" ile reddetti; ama `uv tool
  install` kısıttaki yanlış `--hash`'le kurdu (paket SHA'sı bu yolla sabitlenemez). Takas 988 MiB'da kaldı; ağır görsel
  sınaması 19 sn, tepe yerleşik bellek 2,5 GB (256²; 1024² ölçülmedi).
- **APFS klonları ve yer:** eski ortamın `cp -c` yedeği kopyalanırken 0 MB tuttu, silinince 0,85 GB açtı (eski blokları
  o tutuyordu); uv önbelleği "1,1 GiB" silindi ama yalnız 0,04 GB açtı (bloklar ortamla paylaşılıyor). `du` iki kez
  sayar; yer kararı `df` ile.
- **`UV_MANAGED_PYTHON=1` (ortam.sh):** `uv python find 3.13` artık stüdyonunkini buluyor (önce python.org); ortam
  yorumlayıcıları `uv pip --python` ile kabul ediliyor, `uv sync --dry-run` değişiklik yok, hafif takım 172 geçti.
  Kancalar ve `kur.sh` hâlâ PATH'teki `python3`'e bağlı (gelistirme.md).

## 2026-10-08 — disk payı: yeniden başlatma, npm önbelleği, ağır ML takası
- **Takas diskten yer alır ve iş bitince bırakmaz.** Yönetici incelemesinde (01:06) 5 × 1 GiB takas dosyası, 3721 MiB
  kullanımda, boş disk 7,80 GB; yeniden başlatmadan sonra (11:22) takas 0, `/System/Volumes/VM` boş, boş disk 15,47 GB.
  Arada npm önbelleği silindi (1,09 GB), Resolve kuruldu (3,12 GB), Claude masaüstü verisi 11,53 GB'a çıktı: fark
  kalemlere ayrıştırılamadı. Hafif takım (170 sınama) ve FLUX.2 256² sınaması takas açmadı; VoxCPM2 sınaması (iki
  Türkçe cümle + Whisper + ECAPA, 41 sn) ≤ 8 sn içinde 2 × 1 GiB dosya açtı (tepe 1132 MiB), boş disk 15,69 → 13,55 GB;
  iş bitince bellek %74 boşken dosyalar yerinde kaldı. 5 + 3 GB payı bunu karşılıyor; 1024² ve art arda üretimde
  takas ölçülmedi. → arac-radari (güncelleme-ve-disk §6).
- **`npm cache clean --force` yalnız `~/.npm/_cacache`'i siler** (npm 11.19 `cache.js:143`); `_npx` (0,81 GB) npx
  kurulumlarıdır (çalışan Playwright MCP dahil) ve kalır. İlk rapordaki "1,8 GB" ikisinin toplamıydı. → arac-radari.
- **Yeniden başlatma `$TMPDIR` artıklarını da götürdü:** 2026-10-05 tarihli `pytest-of-onurkaya` (0,37 GB) ve 218
  onnxruntime dosyası (0,57 GB) açılıştan sonra yoktu; elle silmeye gerek kalmadı (silen mekanizma doğrulanmadı).
- **`medya temizle --uygula` kalıcı yer açmaz:** 0,25 GB açtı, sonraki `medya test` `testler/.gecici`'yi aynı boyuta
  geri doldurdu. `uv cache clean` hedefini `UV_CACHE_DIR`'den alır; ortam yüklenmeden stüdyo dışı `~/.cache/uv`'yi
  hedefler (gelistirme.md).

## 2026-10-08 — koruma kancası: sessiz indirme ve sabit sürüm boşlukları
- **Kanca alt süreci görmez; satıcı komutu kendi kurulumunu yapar.** Eski kanca yeni 36 engel durumunun hepsini geçirdi
  (çıkış 0): ses/video girdili `hyperframes transcribe` ve `init --video` → sessiz `brew install whisper-cpp` + ggml modeli
  (bugün yalnız Xcode lisansı durduruyor), `tts` → Kokoro, `models install` → Parakeet, `skills` → sabitsiz GitHub HEAD,
  embedded-captions `prepare.sh` → `uvx whisperx==3.8.6` (sürüm sabitli biçim eski whisperx kuralından da kaçıyordu).
  Kural artık girdiye bakıyor: `transcribe` yalnız .json/.srt/.vtt; değer alan bayrakların değeri girdi sayılmıyor
  (`-d out.srt ses.wav` yakalanıyor); `--help`/`-h` serbest (cli.js: argv'de varsa komut çalışmaz). `medya test koruma`
  65 → 131. → kanca, medya-studyo.
- **SRT içe aktarımı kelime zamanını kaybeder:** `hyperframes transcribe x.srt` her işareti tek öğe yapıyor (7 kelime → 2
  öğe); stüdyo JSON'u doğrudan tanınmıyor. `kelimeler` → `[{text,start,end}]` .json ağsız 7/7 kelime, zamanlar birebir.
  Önerilen kaçış yolunu da ölç: engel iletisi yanlış yolu gösterirse ajan çıkmaza girer. → medya-studyo "Alt yazı istenirse".
- **Satıcı betiklerinin dört adı da genel** (`prepare.sh`, `transcribe.cjs`, `matte.cjs`, `transcribe.mjs`): yalnız bağlamla
  tutulur (yolda, komutta ya da kancanın `cwd`'sinde beceri adı). İlk sürüm üçünü yalnız adla tutuyordu ve başka projenin
  `node scripts/transcribe.mjs`'ini engelliyordu (bağımsız doğrulama buldu). `node --check` / `bash -n` serbest.
- **shlex, kaçışlı `\(`'yi de `'('`'yi de alt kabuk `(`'iyle aynı jetona çevirir.** `find … \( -name transcribe.mjs \)`
  ayırıcıdan sonraki çıplak adı komut başı sandı; salt okunur arama, doğrulama sırasında canlı oturumda engellendi. Çıplak
  ad PATH'ten aranır, bu yüzden komut başında yalnız `/` içeren yol tutulur. Aynı kök neden `find . \( -name skills \)`'i
  eskiden beri engelliyor (gelistirme.md).
- **Kısa bayrağı CLI'nin kendi yoluyla ölç (ayrıştırıcı + denetim):** citty parseArgs (util.parseArgs, strict:false)
  `init -vv.mp4` ve `init -yv v.mp4`'te video=v.mp4 okur (gruptaki bilinmeyen harf geçilir, `e`/`t`/`V` kalanı yutar);
  gerçek CLI (`cli.js` assertKnownFlags) ikisini de çalıştırmadan reddeder ('Unknown flag: -.' / '-y'; kod metinleriyle
  ölçüldü, init çalıştırılmadı). Yani parseArgs böyle okur, cli.js reddeder, kanca temkinli engeller (denetim bir sürümde
  gevşerse diye); düzenli ifade yalnız `-v`'yi tutuyordu. İletideki iddia da koddan doğrulanır: `tts` Python paketi
  kurmuyor, yalnız `pip install` ipucu veriyor.

## 2026-10-08 — kurgu programına devir ölçümü (Resolve 21.1, Kdenlive 26.08)
- **Sınama sinyali periyodikse kaymayı göremez.** İlk ölçümde müzik tıkları 0,5 sn'de bir, çekim bip'leri saniyede birdi;
  Kdenlive müziği 0,5 sn, çekim sesini 1 sn erken başlattığı hâlde ölçüm "0,5 ms" dedi. Sinyaller numaralandı (k. müzik
  tonu 1500 + 100·k Hz, kaynak saniyesi s'de s+1 bip) ve kasıtlı kaydırılmış başvuruyla doğrulandı (+501 / +1001 ms
  yakalandı). Ölçüm aracını önce bilerek bozulmuş girdiyle sına. → testler/nle_sinama.py, nle_olc.py.
- **Kdenlive 26.08 OTIO içe aktarımı (src/otio/otioimport.cpp):** proje fps'ini `timeline.duration().rate`'ten alıyor
  (kaynak hızında yazılan aralıklar 60 fps proje açtırdı); her izin SON klibinin giriş noktası kayboluyor (tek klipli
  dosyada bile); erime isteği (luma mix) başarısız olup sonraki klibi 0'a çekiyor. Kaynak kod okunup tek değişkenli
  dosyalarla ayrıldı. Çözüm `-kdenlive.otio`: aralıklar zaman çizelgesi hızında, iz sonuna 1 karelik "SON — sil" klibi,
  erime yerine kesim + işaret. Uyarlanmış dosya ölçümde geçti. → medya nle, motor-ve-nle.
- **Resolve 21.1 düz .otio'yu kare-kesin açtı.** 24 fps kaynağın 0,25 sn giriş noktasını 30 fps ızgarasına aşağı yuvarladı
  (7,5 → 7 kare): 60 karenin 24'ü bir kaynak karesi erken, tamamı bu yuvarlamayla açıklanıyor. MLT (Kdenlive) ise en
  yakın kareyi alıyor. Ölçüt ±1 kare.
- **App Store Resolve kum havuzlu:** yalnız seçilen dosyalar, `~/Movies` ve Tercihler > Media Storage'a eklenen klasörler
  okunur. `projeler/` eklenince .otio stüdyo klasöründen doğrudan açıldı. Tercihlerde güncelleme/kullanım verisi/çökme
  raporu seçeneği yok.
- **Ücretsiz Resolve erişilebilirlikle sürülebiliyor:** menüler, NSOpen/SavePanel (⌘⇧G + metin alanına değer yaz) ve
  Qt pencereleri (içe aktarma, Quick Export, Tercihler) AX ağacında görünüyor; sayfa düğmeleri gibi özel çizimler
  `click at` ile değil CGEvent ile tıklanıyor (System Events tıklaması Qt listesinde işlemedi). Konsol görünmüyor (ekran
  kaydı izni yokken kör). Kırılgan; ölçüm için yeterli.
- Kdenlive projesini pencere açmadan çizmek: `kdenlive.app/Contents/MacOS/melt proje.kdenlive -consumer avformat:…`
  (son kare kapsayıcı: +1 kare).
- **Çizim işaretleri göstermez: kaydedilen projenin XML'i birincil denetim.** Kdenlive çizimi "GEÇTİ" dedi; kaydedilen
  .kdenlive'da ise klip işareti girişin iki katındaydı (giriş 21 → işaret 42, zaman çizelgesinde 0,7 sn geç).
  otioimport.cpp:365 `pos = start + işaret`: OTIO'da işaret klibin kaynak saatinde, Kdenlive onu kırpılmış başlangıca
  göreli okuyor. Gerçek planda (deniz-kenari) asıl medyadan kesilen 3 notlu klibin biri 8 kare geç, ikisi hiçbir
  klibin aralığına düşmüyordu (biri medyanın dışında; formülle hesaplandı). `-kdenlive.otio` işareti göreli yazar (TC
  düşülerek); yeni sınama eski kodda 60 + 60 ≠ 60 ile düştü.
  Düzeltme Kdenlive'da yeniden içe aktarılarak doğrulanmadı. → testler/nle_olc.py --kdenlive-xml, medya nle.
- **Erime uzunluğu karışık kare sayısı değildir.** Resolve'un 12 karelik erimesinde kodu okunamayan kare 6'ydı; iki
  klibin farklı kimlik bitinden ağırlık rampası ölçülünce 11,85 kare, ortası 113,5 (kesim 114; kare merkezinde
  örnekliyor). Rampa doğrusal (artık ≤ 0,002) ama ideal 12 kareden %1,3 dik; nedeni ayrılmadı. MLT ilk karede ağırlığı
  0 alır, sayım orada 1 kare eksik verir (kodda okundu: MLT v7.40.0, ilerleme = (konum − giriş)/(çıkış − giriş + 1);
  kurulu 7.41.0; bu işte MLT erimesi çizilip ölçülmedi). → nle_olc.py.

## 2026-10-07 — üretici modeller (FLUX.2 klein, VoxCPM2) ve depo
- **Bellek tepesi diski de yer:** FLUX.2 (8,8 GB) ve VoxCPM2 (7 GB) art arda çalışınca macOS takası 6 GB'a çıktı; takas
  dosyaları diskten yer aldı, boş disk 6,9 → 1,4 GB. Yeniden başlatınca geri gelir. Önlem: `disk_bekcisi` (görsel
  üretimi 3 GB, seslendirme 2,5 GB altında çalışmaz), ağır sınamalar yalnız `medya test --agir`; ağır ML'yi sırayla
  çalıştır, çizimle aynı anda değil. → CLAUDE.md disk notu.
- **VoxCPM2 aynı tarifle her çağrıda başka ses üretir** (konuşmacı benzerliği 0,29). Ses kimliği bir kez üretilip bütün
  cümleler ondan türetilince 0,73–0,76 (ECAPA). Anlaşılırlık iki yolda da CER %0. → `medya seslendir`, ses-tasarimi.
- **HF çevrimdışı kip:** sabit commit'le indirilen modelde `refs/main` yazılmaz; `HF_HUB_OFFLINE=1` ile repo adı
  çözülmez. Komutlar modeli yerel anlık görüntü yoluyla çağırır (sabit sürüm + çevrimdışı). SpeechBrain'de
  `overrides={"pretrained_path": yerel}` gerekir, yoksa ağdan arar.
- **Herkese açık depo:** lisanssız satıcı içeriği (Remotion becerileri: depoda lisans yok) ve GSAP dağıtılmaz; kurulumda
  sabit commit'ten üretilir (`satici.py`). Commit kimliği GitHub noreply (e-posta herkese açık olmasın).

## 2026-10-05 — uçtan uca sınama (deniz kenarı Reels, 15 sn)
- Boru hattı baştan sona çalıştı; 3 bağımsız denetçi GEÇTİ. Süre ~3,7 saat (13 ajan), çoğu ölçüm ve 1 düzeltme turu.
- **HyperFrames `-q delivery` 1080x1920'de H.264 seviye 5.0 verir** → dikey teslim kapısı (≤ 4.2) KALDIRIR. Doğrudan
  teslimde `-q standard` (VMAF 95,89 → 95,88, fark yok); delivery yalnız usta + `teslim.py kodla` yolunda. → kompozisyon.md, iş akışı.
- **`medya ustala` davullu müzikte hedefe ulaşamıyordu** (−16,1 / −14): kazanç her turda baştan hesaplanıyor, sınırlayıcının
  yuttuğu geri konmuyordu; kazanç 0'da da AAC yeniden kodlanıyordu. Düzeltildi (yinelemeli + kopya yolu), sınama var.
- **`medya senkron` çizimdeki sesin kaymasını görmüyordu:** kesimler vuruşta olsa da ses kaymışsa "vurusta" derdi.
  Artık müzik WAV'ına çapraz ilintiyle hiza ölçülüyor (kapsayıcı düzeyi kayma dahil); 40 ms kayma → kayik.
- **HyperFrames 4K ProRes ağır çekimi kare başı ~33 MB PNG'ye açıyor** → disk doldu (ENOSPC), vekil klip gerekti.
  Ağır çekimi teslim boyutunda üret (gelistirme.md: `yavaslat --kirp/--olcek`).
- **Reels güvenli alanı kadraj seçiminde baştan düşünülmeli:** B çekiminin öznesi alt %35'te (arayüzün altında) kaldı.
- **Sessiz yedeğe düşme:** cv2 silinmişti, `sahneler` haftalarca fark edilmeden ffmpeg yedeğiyle çalışabilirdi →
  "birincil sağlayıcı kurulu" sınaması eklendi.

## 2026-10-05 — stüdyonun kuruluşu
- **İş akışı devamı (resumeFromRunId) sıraya bağlı:** önbellek, ilk değişen ya da bitmemiş ajan çağrısına kadar
  geçerli; ondan sonraki her çağrı (önceden bitmiş olsa bile) yeniden koşar. Araştırmadan bir görevi çıkarınca
  bitmiş "boşluk" araştırması baştan koştu. Bağımsız işleri ayrı küçük iş akışlarına böl; yarıda kalan beceride
  `yazildi: true`, üretimde `atla` kullan. → CLAUDE.md.
- **Apple Neural Engine derleyicisi takılabilir:** `ANECompilerService` 18 saat %100 CPU'da kaldı; `medya analiz`
  ve Apple ağır çekimi model yüklerken (`_ANEDaemonConnection loadModel`) hiç hata vermeden sonsuza dek bekledi
  (`sample <pid>` yığını gösterdi). ffmpeg'in VideoToolbox kodlama/çözmesi etkilenmedi. Çözüm kullanıcıda:
  `sudo killall ANECompilerService`. Önlem: `apple_calistir` bekçisi (takılıysa başlamaz, süre aşımında öldürür),
  ağır çekimde Neural Engine'den bağımsız RIFE yedeği; Apple ML sınamaları bu durumda nedeniyle atlanır.
- **Ağır çekim ölçümü 2 (yalnız ara kareler, ham çözülerek):** gerçek kamerada RIFE v4.6 > Apple > minterpolate
  (el kamerası 37,7 / 36,4 / 32,6 dB; kaydırmada en kötü %5 kare 28,8 / 26,2 — Apple'da bozuk kareler); yalnız 540p
  çizgi filmde Apple önde; sakin çekimde fark yok. → yavaslat varsayılanı ≤2000 px'te RIFE, 4K'da Apple (hız, disk).
- **Bitirme sırası (bağımsız denetimden):** görüntü düzeltmeleri → ses kusuru onarımı → `ustala` →
  `meta-temizle` EN SON → `denetle`. `ustala`nın yeniden paketlemesi GPS (udta/loci) etiketini korur;
  `meta-temizle` hem siler hem moov'u başa alır (faststart). → teslim-denetimi.
- **Tek karelik flaş/siyah kare silinmez, önceki karenin kopyasıyla değiştirilir:** silmek sonraki her kesimi
  1 kare kaydırır (müzik senkronu bozulur). → kurgu-zanaati, teslim-denetimi.
- **Kesimdeki tık sınırlayıcıya bırakılmaz:** +1,2 dB kazançta sınırlayıcı tıkı yalnız ~4,7 dB bastırır, tık
  duyulur ve çevresinde kazanç çukuru açılır. `ustala`dan önce onar (yeniden üret ya da 0,5 ms'yi ara değerle);
  ses dikişi yoksa çapraz geçiş işe yaramaz. → ses-tasarimi.
- **Türkçe büyük harf:** HyperFrames (Chrome 152) `text-transform: uppercase` `lang="en"` iken "istanbul" →
  "ISTANBUL" (yanlış), `lang="tr"` iken "İSTANBUL". → CLAUDE.md, hareket-tasarimi.
- **Denetim iş akışı kendi araçlarımızın hatalarını buldu** (kusurlu fikstürde 3 mercek, bütün dikilmiş kusurları
  bağımsız buldu): `ffmpeg -ss t` ekrandaki kareyi değil t'den SONRAKİ ilk kareyi verir → `kare_al` karenin
  başlangıcına arar; temas sayfası etiketi karenin sol üstünü örtüyordu → etiket alttaki şeride; `denetle`
  faststart eksikliğini yazıp geçiriyordu → web/sosyal/youtube'da kaldırır. Sınamalar eklendi.
- **DeepFilterNet:** sınırsız bastırma gürültüyü en çok azaltır ama konuşmayı bozar (Whisper 12/15 → 10/15);
  12 dB sınır hem gürültüyü (SI-SDR 1,8 → 10,1 dB) hem anlaşılırlığı (13/15) iyileştirdi. `-D` olmadan çıktı 30 ms gecikir.
- **HyperFrames gerçek çekimi JPEG ara karelerle çıkarır:** aynı CRF 12'de VMAF 95,0 (PNG ile 96,6, ffmpeg doğrudan
  96,8). Son çizimde `--video-frame-format png`. → CLAUDE.md, kurgu-zanaati.
- **Apple süper çözünürlük durağan görüntüde işe yaramadı** (yalnız 4x; gölgeler koyulaştı; PSNR bikübikten
  kötü); süper çözünürlük çıktısı alfa yazmaz (PNG'de 0 alfa → beyaz patlama). Araçtan çıkarıldı.
- **ffmpeg `psnr` süzgeci kareleri kaydırır** (farklı zaman damgalı akışlarda `setpts=N/…` ile bile). Ağır çekim
  karşılaştırmasında bu yüzden ilk çıkan "Apple en kötü karede çok daha iyi" sonucu YANLIŞTI; kareler doğrudan
  çözülünce Apple ML ≈ minterpolate çıktı. Karşılaştırmayı kareleri ham çözerek yap. → yavaslat, testler.
- **Kancanın kabuk ayrıştırması tırnağa duyarlı olmalı.** İlk sürüm çok satırlı komutta alt satırdaki yasak
  komutu kaçırıyor, tırnaklı heredoc içindeki metni de komut sanıyordu. Kendi komutumuz engellenince fark edildi;
  sınamalar eklendi (46).
- **Satıcı becerileri kurallarla çelişebilir:** HyperFrames `media-use` HeyGen hesabı ister; `music-to-video`
  sabit tempo ızgarası kurar; yönlendirici beceri `usage`/`feedback` çalıştırır. Kurmadan önce becerinin
  dış istek/hesap adımlarını oku. → skillOverrides, kanca.
- **AVFoundation `naturalSize` piksel en-boy oranını uygular** (2048×1080 göründü, tampon 1920×1080): boyutu ilk
  çözülen kareden al.
- **PySceneDetect AdaptiveDetector varsayılanı (3,0)** düşük kontrastlı bir kesimi kaçırdı; 2,0 bütün kesimleri buldu.
- **`alimiter` varsayılanı sesi ~4 ms geciktirir** → `latency=1`. Ölçüm: örnek düzeyinde çapraz ilinti.
- **Kayıtlı iş akışları:** kullanıcı düzeyindeki `~/.claude/workflows/` oturum içinde yüklenmedi; proje
  düzeyindeki `.claude/workflows/` yüklendi. Başka klasörden `scriptPath` ile çağır.
- Kayıpsız deneme videoları diski hızla doldurur (2,3 GB): denemeleri geçici klasörde yap ve hemen sil.

## 2026-10-04 — ilk montaj denemesi (kapatıldı)
- **"Sesler kaymış":** kesimler kendi yazdığımız sabit BPM ızgarasına (76,005 BPM) dizildi; canlı çalınan yumuşak
  şarkıda tempo kaydığı için ızgara 10 sn'lik pencerelerde −390…+300 ms saptı. Çözüm: ritim komitesi + güven
  kapısı (`medya muzik`) ve kesim sonrası ölçüm (`medya senkron`). → kurgu-zanaati, medya-studyo, CLAUDE.md.
- **İstenmeyen yazı:** "daha iyi yap" isteğine başlık/bölüm adı/kapanış yazısıyla cevap verildi; kullanıcı
  sıralama, geçiş, yakınlaştırma, ağır çekim gibi zanaat istiyordu. Yazı yalnız istenirse. → bütün beceriler.
- HyperFrames varsayılan kalitesi (CRF 16) 4:48'lik grenli videoyu 2,5 GB yaptı; `--video-bitrate 8M` ile 275 MB.
- ffmpeg döngüde `-nostdin` olmadan `while read` satırlarını yer; zsh değişkeni sözcüklere bölmez.
