# Dersler

Her projeden sonra kısa, ölçülmüş dersler. Tekrar eden ya da genel ders ilgili beceriye taşınır (taşındıysa
"→ beceri" notu). En yeni üstte.

## 2026-10-09 — Remotion 3B/Lottie ekleri (E3): kuruldu, gl ayarı ölçüldü
- **Kurulum:** `medya kur remotion --yeniden` (kayıttaki satıra beş paket eklendi): @remotion/three ve @remotion/lottie
  4.0.533, three 0.178.0, @react-three/fiber 9.2.0, lottie-web 5.13.0. Sürümler Remotion 4.0.533'ün kendi
  devDependencies'inden alındı; en yeniler (three 0.186.1, R3F 9.8.1) sınanmadığı için alınmadı. Eş bağımlılıklar npm
  view ile uyumlu, `npm ls` çıkışı 0. Kilit dosyasında 20 paket eklendi; silinen ve değişen yok, yalnız kök girdisi
  değişti. 20 paketin bütünlük özeti (sha512) npm kayıt defteriyle aynı. node_modules 422,5 → 484,7 MiB (+62,2 MiB), kurulum
  2,4 sn. Paketlerin hiçbirinde kurulum betiği yok.
- **gl ayarı (ana ajan notu: ölçülerek doğrula):** sürücü adı sayfadan alındı. Sayfadaki `console.log` `remotion still
  --log=verbose` çıktısında görünmedi (tek deneme); ad PNG'nin ilk satırına karakter kodu olarak yazdırılıp okundu. Şablonun `angle`
  ayarında WebGL Apple M2 GPU'sunda (ANGLE Metal). Ayarsız Remotion 4.0.533 (gl null) ve swangle'da SwiftShader, yani
  CPU. swiftshader, egl, vulkan ve angle-egl'de WebGL hiç yok. Komut satırındaki `--gl` ayarı eziyor. Ornek3B (90 kare,
  1080x1920 mp4), 3'er dönüşümlü koşu: angle 3,88–3,97 sn, ayarsız 6,30–6,34 sn, swangle 15,2 sn. angle'ın iki
  koşusu 90/90 kare bit düzeyinde aynı; angle ile swangle arasında PSNR en düşük 61,3 dB.
- **Lottie:** @remotion/lottie Remotion karesini doğrudan Lottie karesi yapıyor (`goToAndStop(kare, true)`). JSON'un
  `fr`'sini 30'dan 60'a çevirmek aynı karede aynı görüntüyü verdi. 60 fps JSON 30 fps kompozisyonda
  `playbackRate={2}` ile doğru hızda: 12. kare, 24. Lottie karesiyle piksel piksel aynı.
- **Şablon:** `Ornek3B` (ışıklı düğüm, yay girişi, kareyle tam tur) ve `OrnekLottie` (`public/lottie/ornek.json`,
  stüdyoda kodla yazıldı: trim path halka + yaylanan nokta). İkisi de yazısız. `Kok.tsx`'te kayıtlıyken 2B `Ornek`
  çizimi 2,81–2,87 sn'den 3,04–3,05 sn'ye çıktı (paket yükü). Ağ kapalıyken (yalnız localhost açık, sandbox-exec)
  iki örnek de çizildi.
- **Sınama:** `test_remotion_3b_ornegi_gpu_da_cizer` sürücü adında ANGLE Metal, ışık, dönüş, yay girişi ve saydam
  tuvali denetler. `test_remotion_lottie_ornegi_yerel_ve_olcusu_dogru` halkanın ilerlemesine ve son karenin bilinen
  alanına bakar: halka 0,998, nokta 0,994 (sınır ±%2). Dokuz mutasyonun dokuzu da sınamayı kırdı. Bunlar: gl swangle,
  gl satırı yok, ışık yok, dönüş yok, yay girişi yok, Lottie kutusu 800 px, çizgi 25, trim animasyonsuz, uzak
  adres. Tam `medya test` 308 geçti, 3 atlandı (`--agir`; E2 kapanışında 306). Kanıt: `sistem/devam/remotion-3b/2026-10-09/`.
  → remotion-ev-kurallari başlığı, hareket-tasarimi, arac-radari (yükseltme), `yetenekler.toml`.

## 2026-10-08 — Z-Image-Turbo (E2): kuruldu, yedek oldu; FLUX.2 kaldı
- **Kurulum:** `mflux-community/z-image-turbo-mflux-q4` sabit commit f427e257d8e6…, 13 dosya 5,90 GB; `medya kur
  z-image-turbo` 105 sn (uv adımı "already installed": mflux ortamı flux2-klein ile ortak, değişmedi); boş disk
  46,68 → 40,76 GB. 6 LFS dosyasının SHA-256'sı ve 7 küçük dosyanın git blob kimliği HF API ile aynı. Lisans: kart ve
  README apache-2.0, base_model Tongyi-MAI/Z-Image-Turbo (ana kart f332072: apache-2.0). Ağ kapalıyken (sandbox-exec)
  üretti. Tokenizer FLUX.2 ile aynı blob (paylaşılan depo, 11 MB); metin kodlayıcılar farklı (yer paylaşımı yok).
- **A/B (karar kuralı ölçümden önce yazıldı: `sistem/devam/ham/gorsel-ab/KARAR-KURALI.md`):** 3 istem (ürün, manzara,
  İngilizce afiş) × 2 tohum × 2 model, 1024², `--low-ram`, sırası değişen çiftler; mflux süreci `/usr/bin/time -l` ile.

  | | FLUX.2 [klein] 4B Q4 | Z-Image-Turbo 6B Q4 |
  |---|---|---|
  | süre (6'şar koşu) | 83–107 sn (ort 97) | 275–383 sn (ort 344); çift içi oran 3,3–3,7 |
  | bellek tepesi (peak memory footprint) | 9,0–10,8 GB | 6,3 GB |
  | takas | bir koşuda +0,38 GB | büyümedi |
  | İngilizce afiş, gözle | 0/2 doğru ("SUM MER", "MUIC", "NIGHT") | 2/2 harfi harfine doğru |
  | tesseract psm 11 / psm 6 (12 kelime) | 6 / 3 | 10 / 4 |
  | Vision istem etiketi | mug/tableware, lake/water | aynı |
  | Apple estetik ort | 0,61 | 0,65 |

  Kural sonucu: Z-Image yazıda, istem uyumunda ve bellekte geçti; "1024² ≤ 4 dk" koşulunda kaldı → varsayılan FLUX.2,
  Z-Image yedek ve `--model z-image`. Fotogerçekçilik farkı ölçülmedi (görseller git dışı, kullanıcı bakar). A/B boyunca
  boş disk en az 41,75 GB, takas 2,8–3,2 GB.
- **FLUX.2 kaldı (kullanıcı kuralı "gerek varsa dursun"):** referanslı düzenleme yalnız FLUX.2'de. Tongyi-MAI'nin HF'deki
  modelleri 2026-10-08'de Z-Image-Turbo, Z-Image (taban), MAI-UI; Z-Image-Edit kartta "To be released". mflux 0.21.0'da
  Z-Image için yalnız `--image` (görselden görsele) var, talimatlı düzenleme yok.
- **Sürekli yükte süre uzaması (nedeni ölçülmedi; ısı/saat hızı olası):** 44 dk sürekli GPU yükünde süre ilk koşudan sonuncuya FLUX.2'de %28,6, Z-Image'da %39,5 uzadı
  (fansız M2). Seri üretimin süresini ilk görselden tahmin etme.
- **Bellek ölçümü:** `/usr/bin/time -l medya …` `peak memory footprint` olarak yalnız doğrudan alt süreci verir (20 MB);
  MLX'in Metal belleği RSS'ye girmiyor (RSS FLUX.2 2,5, Z-Image 3,0–4,1 GB; ayak izi 9,0–10,8 / 6,3 GB). Üreteci doğrudan
  sar. FLUX.2'nin kayıttaki 8,8 GB'ının (2026-10-07) yöntemi yazılmamış; bu yöntemle 9,0–10,8 GB.
- **Sınama:** `medya test --agir gorsel` 6/6 (iki modelde de aynı tohum piksel piksel aynı görsel), tam `medya test`
  306 geçti, 3 atlandı; yeni hafif sınamalar mutasyonla denendi (kod/kayıt commit kayması, `--referans`'ın Z-Image'a
  gitmesi, yedeğe düşmenin kaldırılması: hepsi kırıldı). → `medya gorsel-uret`, `yetenekler.toml`, gorsel-uretim,
  arac-radari bilinen kararlar.

## 2026-10-08 — VoxCPM2 8-bit (E1): A/B ile varsayılan oldu, 4-bit silindi
- **Kurulum:** `mlx-community/VoxCPM2-8bit` sabit commit d52725898a06…, 3,23 GB, 57 sn; `model.safetensors` SHA-256
  HF `lfs.sha256` ile aynı (c07c59ac…), küçük dosyaların git blob kimlikleri API ile aynı; config'te tek fark
  `quantization.bits` 4 → 8 (yalnız LM katmanları). Lisans: kart + README apache-2.0, ana kart (openbmb/VoxCPM2,
  32279ef) "Apache-2.0, free for commercial use". mlx-audio 0.5.8 ağ kapalıyken yükledi ve konuştu.
- **A/B (karar kuralı ölçümden önce yazıldı):** iki kimlik (aynı tarif ve tohum; birini 4-bit, birini 8-bit tasarladı)
  × iki model × iki tohum takımı × 10 Türkçe cümle, yeniden üretimsiz, ABBA sırası. Her cümleden önce
  `mx.random.seed`: aynı koşul bit düzeyinde aynı çıktıyı verdi (yinelenebilir A/B).

  | | 4-bit | 8-bit |
  |---|---|---|
  | toplam CER (40 cümle) | %0,97 | %0,74 |
  | en kötü cümle CER | %11,7 | %5,3 |
  | benzerlik ort / en düşük | 0,815 / 0,721 | 0,819 / 0,732 |
  | ilk geçişte kapıdan kalan cümle | 1 | 0 |
  | 1 sn ses için üretim | 2,38 sn | 2,47 sn |
  | bellek tepesi: kimlik / 10 cümle | 7,5 / 13,5–13,9 GB | 8,6 / 13,1–14,0 GB |

  Eşli benzerlik farkı (8 − 4) +0,004, %95 önyükleme aralığı −0,003…+0,011: fark gürültü içinde; 8-bit "kötü değil",
  "daha iyi" kanıtlanmadı. Satıcı tablosundaki RTF 0,90 / 0,85 (donanım belirtilmemiş); bu Mac'te 0,42 / 0,40. KAPI:
  `medya test --agir seslendir` 8-bit'le iki kez geçti (biri ağ kapalıyken). 4-bit silindi: +2,30 GB. Dinleme
  örnekleri git dışı: `sistem/devam/ham/ses-ab/` (doğallık ölçülmedi). → `medya seslendir`, `yetenekler.toml`.
- **CER'in yarısı ölçüm hatası:** "üçüncü" → Whisper "3.", normalleştirici "üç": sekiz koşunun hepsinde aynı cümlede
  %5,3. Kalan hatalar cümle başında: aynı tohumda (3006) iki modelin dökümünde de fazladan hece ("Nes öğretmenimiz",
  "Daç da ödetmenimiz") — "devam" kipinde başlangıç kararsızlığı olabilir, dinlenmedi. → ses-tasarimi, gelistirme.md.
- **Bellek tepesinin yarısı MLX önbelleği:** 10 cümlede işçi 13–14 GB (MLX etkin tepesi 5,0–6,5 GB); aynı koşul
  `mx.set_cache_limit(0)` ile 6,1 GB, çıktı bit düzeyinde aynı, üretim %20 yavaş (kanıt
  `sistem/devam/ham/ses-ab/onbellek0/`). A/B boyunca takas 2,5 → 4,65 GB (kayıtlı en yüksek 4654,56 MiB), boş disk en az 43,3 GB. CLAUDE.md'deki
  "VoxCPM2 ~7 GB" kısa işler içindi. → CLAUDE.md, gelistirme.md (O).
- **Paylaşılan blob deposu (huggingface_hub 1.x):** model klasörünü silmek yer açmaz; ağırlık
  `modeller/hf/hub/blobs/<2 hane>/<xet>` altında, model klasöründe yalnız bağ var. `scan_cache_dir().delete_revisions(
  <commit>)` önce kuru (`expected_freed_size`, blobun `.refs` manifesti), sonra `.execute()`: başvurusu kalmayan blobu
  süpürür (bugün 3 blob, 2,30 GB).

## 2026-10-08 — `medya ciz` (O6): planı HyperFrames'siz, kare dökmeden çizmek
- **Açık GOP'lu HEVC'de "iki karenin ortasına ara" yetmez.** mov araması DTS'e göre: anahtar karenin hemen önündeki
  kareye (`-ss` o karenin ortası) aranınca ffmpeg sonraki anahtar kareye iniyor, onun öncü kareleri çözülemiyor ve çıktı
  2 kare geç başlıyor (deneme kaynağı 4096x2160 60 fps, 4 sn GOP: 248, 249 → 250; 34 aramanın 10'u). Çözüm: 0,5 sn
  önceye ara (`-copyts`), ilk kareyi tam pts ile seç (`select=gte(pts,P)`); kare zamanları ffmpeg 6.0'ın paket
  damgalarından (`-c copy -f framemd5`), ilk kare `showinfo` ile. Sınama: tam çözümün kare özetlerine karşı 19 konumun
  (8'i anahtar kare önü) hepsi doğru. ffprobe ayrı paket (4.4.1), kare zamanına kullanılmadı. → medya ciz.
- **Kare kuralı "zamanı ≤ t olan son kare" (HyperFrames gibi) tam kesirle hesaplanınca kayma kalmıyor.** Kare kodlu
  sınama projesi (`testler/nle_olc.py`): 228 karenin hepsi beklenen kaynak karesi (A/B 30, C 60, D 24 fps; Resolve
  D'nin 24 karesini 1 erken veriyordu), kesimler 0, 60, 168 (erimeden sonraki kesim dahil; elle `concat → xfade →
  concat` +1 kare kaydırmıştı), erime rampadan 11,9 kare, ortası 114,05 (kesim 114). Ses: müzik `medya senkron` ses
  hizasıyla 0,0 ms, tonlar 1,0–1,1 ms; çekim sesi 4,0 / 1,5 ms (ilki 8 ms giriş geçişinin eşik etkisi).
- **perspective süzgecinin kuralı ölçüldü:** hedef piksel x → kaynak `x0 + x·s` (piksel dizini; merkez değil), `in`
  1'den sayar. Piksel merkezi eşlemesi için köşeye `s/2 − ½` eklenir; eklenmezse Ken Burns'te 0,077 px hata (sınama
  yakaladı). Lekeli kayıpsız kaynakla (CRF 1) konum hatası ≤ 0,02 px, artığın ikinci farkı p95 0,032–0,037 px
  (doğrulamanın ölçtüğü 0,039 ile aynı; zoompan 0,94); CRF 16'da 0,055–0,062 (kodlayıcı gürültüsü). Sabit kadraj
  tamsayı kırpma (çift piksel): ≤ 0,5 px.
- **Karşılaştırma, 1080p gerçek çekim 10 sn** (deneme kaynağının ölçeksiz 1920x1080 kesiti, yalnız sayısal; aynı
  x264 ayarı: medium, CRF 16, B kare yok; kayıpsız başvuruya karşı):

  | Çizim | Süre | Disk tepesi | RSS tepesi | VMAF ort / en az | Y-PSNR | Y kayması |
  |---|---|---|---|---|---|---|
  | `medya ciz` | 5,8 sn | 0,02 GB | 0,97 GB | 96,21 / 94,69 | 47,1 dB | +0,02 |
  | HyperFrames PNG | 34,6 sn | 1,11 GB | 3,2 GB | 95,98 / 94,48 | 40,9 dB | ort. −1,9 düzey (sabit değil, aşağıda) |
  | HyperFrames JPEG (varsayılan) | 18,4 sn | 0,18 GB | 2,6 GB | 94,77 / 93,56 | 45,3 dB | +0,04 |

  Üçü de kareye hizalı (−1/0/+1 kaymada en iyi 0). VMAF farkı ciz − HF PNG +0,23 (ölçütün ≥ −0,3). PNG kipinin Y
  kayması VMAF'ta görünmüyor, PSNR'de görünüyor. Dalga 3 doğrulaması sentetik bt709 rampada bunun sabit kayma değil
  ~%1,7 kazanç sıkışması olduğunu ölçtü (Y=50 −0,5, 128 −1,8, 200 −3,1; JPEG +1,4 / +0,06 / −1,2); nedeni ayrılmadı →
  gelistirme.md.
- **4K → 1080x1920 dikey 10 sn (2 Ken Burns + erime):** `medya ciz` 12,6 sn, disk 0,02 GB, RSS 1,45 GB (çözücü
  `-threads 4`: 2,36 → 1,70 GB, kareler bit bit aynı; iki çekim kuralı 1,51; x264 `-threads 8` 1,45). HyperFrames PNG (5 işçi) 100 sn sonra SIGABRT ile çöktü:
  4096x2160 8 bit RGB PNG kare başı 11,3 MB (312 kare 3,5 GB, çizimin yanındaki `work-…` klasöründe kaldı), takas 0,9 →
  15,9 GB, boş disk 50,9 → 31,5 GB (tepe 19,4 GB); çöken çizimin Chrome süreçleri belleği tutmaya devam etti, öldürülünce takas 5 GB'a
  indi. Aynı plan HyperFrames JPEG `--workers 1`: 35,8 sn, 0,37 GB, 4,55 GB. İki motor aynı geometriyi çiziyor: ciz ↔
  HyperFrames Y-PSNR ort. 42,05 dB; Ken Burns çekimlerinde ≤ 0,2 px, sabit çekimde ≤ 0,6 px (tamsayı kırpma).
  → kurgu-zanaati (gerçek çekimde önce ciz), CLAUDE.md HyperFrames notları.
- **Uzun plan (300 sn, 112 çekim, 37 Ken Burns, 16 erime; 4K60 HEVC, 4 sn GOP; doğrulama ölçütü RSS ≤ 2 GB, takas
  büyümez, disk ≈ çıktı):** ilk koşu 404 sn (0,74x), takas büyümedi ama süreç ağacı RSS toplamı 2,25 GB: erimede
  üçüncü çözücü (önden açılan) açıktı. "Aynı anda en çok iki çekim" kuralıyla 2,04 GB, x264 `-threads 8` ile 1,92 GB
  (kodlayıcı 662 → 558 MB; çizim çözücüde darboğazlı, süre 410 sn, 0,73x). Takas 3,00 → 2,98 GB, disk tepesi 0,47 GB
  (çıktı 461 MB). RSS toplamı paylaşılan kitaplıkları süreç başı sayar (gerçek bellek daha az). 95 sert kesimin 95'inde
  kare farkı tepesi tam planlı karede (tepe/çevre ≥ 17); `medya denetle`'nin kesim bulucusu aynı sahneden gelen benzer
  çekimler arasında 13'ünü görmedi (plan_denetle `--denetim` ⚠), plansız kesim, siyah, donma, flaş yok. İlk koşunun
  `df` ölçümü takas dosyası küçüldüğü için yanıltıcıydı (−0,6 GB "kalıcı"); sessiz planda ses ara dosyası artık yok.
- **`kisma.py --bas` işareti:** tanımı "yatağın 0. sn'si videoda kaçıncı sn" = −`muzik.bas`; ses-tasarimi belgesi
  `--bas <plan muzik.bas>` diyor. `muzik.bas` 0,5 iken `--bas 0.5` kısmayı 1 sn erkene (1,53–3,53 sn), `--bas −0.5` doğru
  yere (2,53–4,53) koydu (müzik dosyası zamanı; konuşma 2,0–4,0 sn video). `bas: 0`'da (önerilen) etkisiz → gelistirme.md.
- Kanıt (betikler + JSON): `sistem/devam/ciz/2026-10-08/`. Deneme kaynağının karelerine bakılmadı (yalnız sayısal);
  sınamalar: `testler/test_ciz.py` (`medya test ciz`).

## 2026-10-08 — `yavaslat --kirp/--olcek` (O3) ve ara kare yolunda gerçek kareler
- **Kırp/ölçek doğal yola da girmeli.** Önerinin ilk hâli yalnız `_hazirla`'yı değiştiriyordu; denemenin ağır çekimi
  (gerçek 60 fps, 0,5x) `_hazirla`'yı hiç çağırmayan doğal yoldan geçtiği için değişiklik onu hiç etkilemeyecekti
  (şüpheci doğrulama buldu). Artık iki yolda da ton eşlemeden sonra, ara kareden önce. Yöntem sırası, RIFE disk tahmini
  ve UHD kipi hazır kareye baktığından 1080x1920'de RIFE ilk sırada.
- **Disk yükü çözünürlükten çok kodekten.** HyperFrames 0.8.140 ProRes'i her kipte 16 bit PNG'ye açıyor
  (`resolveFrameFormat`). Deneme A kesitinde, HyperFrames'in çıkarma ayarlarıyla borudan ölçüldü (kare başı MB / denemenin
  237 ağır çekim karesi): ProRes 4096x2160 33,05 / 7,83 GB; ProRes 1080x1920 6,86 / 1,63 GB; `.mp4` (H.264 CRF 12)
  1080x1920 PNG'de 2,53 / 0,60 GB, taslak JPEG'de 0,22 / 0,05 GB. ProRes dosyası 676 → 136 MB. 1x 4K HEVC de PNG'de
  11,72–11,96 MB/kare, ortalama 11,84 (237 kare 2,81 GB; taslak JPEG 0,97 MB/kare; bütün klip 8 kesitte,
  `olc_1x4k.json`): PNG'li son çizimin sığması 1x çekimlerin de inmesini ister (gelistirme.md).
  → kurgu-zanaati teknikler Hız, CLAUDE.md.
- **4K'da RIFE (ölçüm borcu kapandı):** 1 sn'lik kesit (30 → 60 kare) 4096x2160 `-u` 36,6 sn, geçici disk tepesi 1,25 GB;
  aynı kesit 1080x1920'ye kırpılıp ölçeklenince 10,2 sn, 0,27 GB. Takas değişmedi (820 MB).
- **Ölçek renk ayarı ve etiketi şart.** HDR yolunda `scale` ton eşlenmiş RGB'yi YUV'ye çeviriyor: başvuruya karşı (kare
  ortalaması) ayarsız Y 24,1 dB (U/V 30,7), `out_color_matrix=bt709:out_range=tv` ile 51,1 dB (U/V 39,3 / 39,0); ara
  kare yolunda 24,1 → 49,9. Doğal yol ProRes'inde matris etiketi yine "unknown" kaldı → `setparams=colorspace=bt709:
  range=tv` (piksel değişmedi). Sınama ikisini de tutuyor (ters sınamada gri ölçütü 22,7 dB ve "matris None" ile kaldı).
  İlk yazılan "24,0 → 52,7 dB"nin dosyası yoktu; düzeltme turunda yeniden ölçüldü (`olc_renk.json` → hdr). Döndürme:
  ffmpeg 6.0 kareyi süzgeçten önce döndürüyor, kırpım görünen yönde.
- **SDR'de giriş matrisi de açık verilmeli** (düzeltme turu; şüpheci doğrulama buldu). Çıkış matrisi verilince `scale`'in
  giriş matrisi 'auto' kalıyor ve ffmpeg 6.0 etiketsiz kareyi BT.601 okuyup BT.709'a çeviriyor. Etiketsiz 1280x720 renk
  çubuklarında `--olcek`, HyperFrames'in göreceği rengi kaydırıyordu: kırmızı 189 → 168, mavi 189 → 178, camgöbeğinin
  G'si 189 → 208; Y/U/V düz ölçeğe 31,16 / 36,05 / 35,31 dB (en kötü kare). Artık giriş matrisi etiketten, etiketsizse
  HyperFrames'in tahmininden geliyor (chromeGuessForUntaggedMatrix: ≥ 720 satır BT.709, altı BT.601). Sonuç 62,99 /
  61,51 / 63,34 dB, çubuklar kaynakla aynı. bt709 etiketli kaynakta süzgeç sonucu değişmedi (sentetikte aynı sayılar;
  denemenin 4K kaynağında 30 kare bit bit aynı). Yeni sınama dört durumu ayırıyor: ters sınamada eski süzgeç etiketsiz
  HD'de, etiketi yok sayan süzgeç bt601 etiketli ve etiketsiz SD'de kalıyor. `medya test yavaslat` 10 → 14; tam `medya
  test` 293 geçti, 2 atlandı. Kapsam dışı gözlem (→ gelistirme.md): bt601 etiketli kaynakta ffmpeg 6.0'ın 601→709
  çevirisi yaklaşık (%75 beyaz 189 → 185/187/187). `--olcek`'siz yol ise hiç çevirmeden bt709 etiketliyor (kırmızı 173
  yerine 189).
- **Kırp-önce kalitesi** (aynı yöntem RIFE, gerçek 60 fps karelerinin aynı kırpımına karşı, kareler ham çözülerek):
  gerçek çekimde (denemenin en hareketli penceresi) 1216x2160'ta −0,01, 1080x1920'de 0,00 dB; RIFE'nin kendi PNG
  çıktısında −0,02. Sentetik aşırı dokuda (mandelbrot) kırpımda −1,4 dB (RIFE'de −0,24; kalanı ProRes ara dosyası:
  kırpık karede 35,6, tam karede 37,5), 1080x1920'de −4,1 dB (ölçekte örtüşme; σ=1,5 bulanık dokuda −0,5). Büyük
  hareketli gerçek çekimle ölçülmedi: stüdyoda yok, denemenin en hareketli penceresinde bile önceki kare 41,6 dB.
- **Ara kare yolu 60 fps kaynağı 30'a indiriyordu** (0,25x'te gerçek karelerin yarısı atılıp × 4). Artık kaynağın tam
  böleni olan en yüksek hız (60 × 2). Yarı ölçekli eşdeğerde (30 fps → 15 fps çıktı, 0,25x; gerçek 60 fps karelerine
  karşı) tüm kareler: gerçek çekimde 40,57 → 41,26 dB (en kötü %5: 39,47 → 40,72), sentetikte 35,68 → 36,69. 720p
  sentetikte eski yolda gerçek kare olması gereken konumlarda en düşük 28,7 dB, yenide 41,1 (sınamanın ölçütü: 640x360 gri, 0,5 sn, hareket60'a karşı; 1280x720'de 26,7 / 40,0, olc_720.json'daki 1 sn'lik koşu 25,5 / 39,3).
- **Sayı düzeltmesi:** "kaydırmada en kötü %5 kare 28,8 / 26,2" birincil veriyle tutmuyordu; `ozet.jsonl` 27,28 / 26,23
  (46 ara karenin en kötü 2'si). Aşağıdaki 2026-10-05 dersinde ve `yavaslat.py`'de düzeltildi.
- Kanıt (betikler + JSON): `sistem/devam/yavas-cekim/2026-10-08-kirp/` — `olc_hf` (geçici alan), `olc_1x4k` (1x 4K),
  `olc_renk` (ölçek rengi, SDR ve HDR), `olc_4k_b`/`olc_720`/`tani2`/`tani3` (kalite, hız, disk tepesi). Deneme
  kaynağının karelerine bakılmadı (yalnız sayısal).

## 2026-10-08 — koruma kancası ek turu: snapshot gizliliği, sabit sürüm, fd ve satır devamı
- **Kapatma değeri birebir okunur.** 0.8.140 Gemini açıklamasını yalnız `String(args.describe) === "false"` ile kapatıyor
  (`snapshot-SD5R3NWX.js`:729). citty 0.2.2 ayrıştırıcısıyla 16 biçim ölçüldü (snapshot çalıştırılmadan): `0`, `no`,
  `False`, boş değer ve `--describe --at 1` (değer "--at") açıklamayı açık bırakıyor; tekrar eden bayrakta son değer
  geçiyor (`--describe false --describe x` açık); `--` sonrası konumsal (`-- --describe false` açık, snapshot fazla
  konumsalı ayrıca reddediyor). Eski düzenli ifade `0`/`no`'yu ve metnin herhangi bir yerindeki `--describe false`'u kabul
  ediyordu. Yeni denetim jeton tabanlı: `--`'dan önceki her değer `false` olmalı. → kanca, medya-studyo yönlendirmesi.
- **Sürüm belirteci komut tanımayı da bozuyordu.** `HF` düzenli ifadesi `hyperframes@^0.8`'i tanımıyordu, `npx
  hyperframes@^0.8 cloud render` bulut kuralını bile geçiyordu. Artık tam sürüm dışı her `hyperframes@` (npx/dlx/npm exec,
  `-p/--package` değeri) ve npm/pnpm/yarn/bun'da tam sürümsüz kurulum ya da yükseltme önce engelleniyor. Sürümsüz ad da
  engelli, çünkü latest kurup `^` ile kaydediyor. `-p/--package`'in değeri artık komut sanılmıyor; bu, aynı yoldan kaçan
  `npx -p hyperframes hyperframes cloud render` ve `npx -p @remotion/cli remotion lambda …`'yı da kapattı. → arac-radari
  güncelleme-ve-disk §3.
- **fd ayrımı jetonlamadan önce yapılır.** shlex boşluğu saklıyor: `2>/dev/null` ile `600 >/dev/null` aynı jetonları
  veriyordu. `timeout 600 >/dev/null hyperframes cloud render`'da süre fd sanılıp silinince önek komutu süre diye atladı.
  Artık işlece bitişik fd rakamı, tırnak dışında, metinde boşluğa çevriliyor. Bu `$(… 2>&1)` içinde de yapılmalı: yoksa
  dış geçiş `2`'yi transcribe girdisi sanıyor (sınamada). Ön süzgeç ve beceri bağlamı satır devamı silinmiş metinde
  çalışıyor; önceden `npx hyper\` + satır sonu + `frames cloud render` geçiyordu.
- **Derlem:** oturum kayıtlarındaki 30.019 benzersiz Bash komutu (bütün projeler) ve 11.282 belge parçası iki kancaya
  verildi (çalıştırılmadan, 1,9 sn). 5 fark çıktı, hepsi 0 → 2 yönünde. İkisi başka bir projede sürümsüz `npm install -D
  hyperframes`, yani kuralın hedefi. Üçü belgede `hyperframes@<sürüm>` yer tutucusu: kabukta `<` yönlendirmedir, gerçek
  sürümle geçer. 2 → 0 yönünde fark ve çökme yok; 30.000 rastgele girdide de çökme yok. `medya test koruma` 170 → 236
  (66 yeni sınama; 44'ü özgün kancada kırmızı); `medya test` 282 geçti, 2 atlandı (`--agir`).

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
  Düzeltme 2026-10-08 22:13'te gerçek içe aktarmayla doğrulandı (ana ajan): kaydedilen .kdenlive'da işaret kaynak 21 →
  zaman çizelgesi 114, beklenen 114 (düzeltmeden önceki içe aktarmada 42 → 135); melt çizimi `--erime-kesim
  --son-tolerans 2` ile geçti ve öncekiyle bayt düzeyinde aynı (işaret görüntüyü değiştirmez). `cikti/nle/
  kurgu-kdenlive.otio`'da işaret klibe göreli 0 (klip kaynak başı 21). Kanıt: `projeler/2026-10-08-nle-sinama/analiz/
  olcum-kdenlive-isaret-xml.json`, `olcum-kdenlive-isaret.json`. Kılavuzlar hâlâ denetlenmiyor. → testler/nle_olc.py
  --kdenlive-xml, medya nle.
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
  Ağır çekimi teslim boyutunda üret (`yavaslat --kirp/--olcek`, 2026-10-08'de eklendi). Düzeltme (2026-10-08 ölçümü):
  tek başına yetmez — 1x 4K HEVC çekimler de PNG'de 11,8 MB/kare (237 kare 2,8 GB) tutuyor; gerçek çekimde `medya ciz`.
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
  (el kamerası 37,7 / 36,4 / 32,6 dB; kaydırmada en kötü %5 kare 27,3 / 26,2 [2026-10-08 düzeltildi: önce 28,8 yazıyordu;
  `ozet.jsonl` 27,28 / 26,23] — Apple'da bozuk kareler); yalnız 540p
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
