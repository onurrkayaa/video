# Medya Stüdyosu

Bu klasör, Onur'un bu Mac'teki **yerel medya üretim stüdyosudur**: video kurgusu, animasyon ve hareketli grafik,
görsel/fotoğraf, ses — hem kişisel işler hem iş için. Her şey yerelde ve ücretsiz çalışır; araçlar değişebilir,
sistem değişmez: işler **yetenek** adıyla çağrılır (`medya <komut>`), arkasındaki araç kayıt defterinden seçilir.

## Kesin kurallar (kullanıcının)
- Ücretli hizmet, hesap açma, kredi, bulut çizim yok. HyperFrames'in `cloud`, `lambda`, `cloudrun`, `auth`,
  `publish`, `usage`, `feedback` komutları, `heygen` CLI'si ve `hyperframes media-use resolve` (HeyGen kataloğu)
  kullanılmaz — `medya-koruma` kancası bunları engeller; engellenince yolunu değiştir, kancayı aşmaya çalışma.
- Sormadan indirme ve sabit sürüm: ses/video girdili `hyperframes transcribe`, dökümlü `init --video|--audio`,
  `tts`, `models install`, `upgrade`, `skills` (`skills check` dışında) ve satıcı betikleri (embedded-captions
  `prepare.sh`/`transcribe.cjs`/`matte.cjs`, media-use `transcribe.mjs`) kullanılmaz — sormadan model indirir ya da
  sabit sürümü/kaynağı bozar; kanca engeller. Döküm/alt yazı `medya yaziya-dok --dil tr --srt`, dış ses `medya seslendir`.
- Analiz verisi kapalı (`HYPERFRAMES_NO_TELEMETRY=1`, `DO_NOT_TRACK=1`, `HF_HUB_DISABLE_TELEMETRY=1`).
  `hyperframes snapshot` daima `--describe false` (yoksa kareler Google'a gidebilir).
- E-posta ya da kişisel bilgi hiçbir dış isteğe girmez. Bot korumaları aşılmaz.
- Lisansı belirsiz medya indirilmez. Ticari olmayan (NC) lisanslı model/ses/görsel iş için kullanılmaz; kişisel
  işte kullanılacaksa açıkça söylenir. Telifsiz ses gerekiyorsa kodla üretilir ya da CC0 kaynaktan alınır.
- Kullanıcının dosyaları silinmez, üzerine yazılmaz (önce sor). Asıllara dokunulmaz: `medya proje yeni --kaynak`
  salt okunur kopya alır.
- **Görüntü gizliliği:** araçların hepsi yerel çalışır, ama Claude'un Read ile açtığı her kare/temas sayfası modele
  (Anthropic) gider. Mahrem/kişisel kliplerde başlamadan kullanıcıya söyle ve sor; istemezse "yalnız sayısal mod":
  `medya analiz`/`ses-olay`/`sahneler` çıktılarıyla çalış, kareleri açma, sonucu kullanıcı izlesin.
- Kamuya açık paylaşım: telifli şarkı kişisel hediyede sorun değil, herkese açık gönderide risklidir; görüntüdeki
  kişilerin (sevgili, müşteri, yoldan geçen) rızası kullanıcıya hatırlatılır.

## Çalışma ilkeleri (kullanıcı geri bildiriminden — her işte geçerli)
1. **İstenmedikçe ekrana yazı, başlık, alt yazı koyma.** Beklenen değer profesyonel zanaattır: doğru sıra,
   motivasyonlu geçişler, yakınlaştırmalar, ağır çekim, hareket tasarımı. Yazı gerekli görünüyorsa sor.
2. **Ölçmeden iddia yok.** Claude videoyu gerçek zamanlı izleyemez, sesi duyamaz. Her kalite iddiası bir ölçüme
   (`medya denetle`, `senkron`, `ustala`, ffprobe) ya da Read ile açılmış bir temas sayfasına dayanır;
   doğrulanamayan şey "doğrulanamadı" diye raporlanır, kullanıcıya hangi saniyeleri izlemesi/dinlemesi gerektiği söylenir.
3. **Müzik senkron kapısı.** Vuruşa kesim yalnız `medya muzik` güveni `yuksek` iken; sonuç `medya senkron` ile
   ölçülmeden "vuruşa oturdu" denmez. Güven düşükse bölüm/cümle sınırları ve erimeli geçişler. (Sabit BPM
   ızgarası 2026-10-04'te "sesler kaymış" hatasına yol açtı.)
4. Sıralamadan önce `medya ses-turu`: çekim sesi karışıksa ses kendi görüntüsüyle taşınır.
5. Kullanıcıyla Türkçe konuş; raporda dosya yolları, ölçülenler ve ölçülemeyenler olsun; "mükemmel" deme.
6. **İş sonunda öneriler** (kullanıcı özellikle istiyor): ölçülmüş bulgulara dayanan 1–5 somut öneri + kararını
   bekleyen maddeler ayrı liste (boyut, lisans, maliyet). Önerileri onaysız uygulama.

## Mimari (üç katman)
| Katman | Nerede | Ne yapar |
|---|---|---|
| Yetenek | `medya/` (CLI), `yetenekler.toml` (kayıt), `medya/isciler/` (ağır ortam işçileri), `arac/medya-apple` (Swift: VideoToolbox, Vision, SoundAnalysis), `arac/rife` (ağır çekim yedeği) | Araçtan bağımsız komutlar; sağlayıcı değişince komut aynı kalır; asılan/başarısız sağlayıcı yedeğine düşer |
| Motor | HyperFrames (HTML+GSAP, varsayılan) · Remotion 4.0.533 (React/TSX, **lisans kapısıyla**) · ffmpeg (`medya ciz`: gerçek çekim kurgusu, kare dökmez) | Kompozisyon ve çizim |
| Bilgi | Beceriler `sistem/claude/skills/` (→ `~/.claude/skills/` bağlantı; satıcı becerileri sabit commit'ten — HyperFrames'inkiler CLI'nin etiketinden, v0.8.140 @5c7f631 — `satici.py kur` + `bagla`, durum `satici.py dogrula`; `sistem/claude/satici/KAYNAKLAR.md`), bilgi tabanı `sistem/arastirma/<tarih>/`, dersler `sistem/dersler.md` | Zanaat, karar kuralları, araç seçimleri ve gerekçeleri |
| Ajan | Ajanlar `sistem/claude/agents/` (→ `~/.claude/agents/`), iş akışları `.claude/workflows/`, kanca `sistem/claude/hooks/medya-koruma.py` | Uzman roller, uçtan uca boru hattı, kuralların zorlanması |

**Baş ajan:** `medya-yonetici` — bütün sistemi görür; öncelikli, maliyeti belli, kanıtlı öneriler hazırlar; kurmaz,
karar kullanıcının. **Uzman ajanlar:** `medya-analist` (kaynak analizi → `analiz/OZET.md`), `medya-kurgucu` (`plan/kurgu.json`,
`KARARLAR.md`, ara klipler, NLE devri), `medya-hareket` (motor seçimi, kompozisyon, animasyon, çizim), `medya-ses`
(müzik, katman, efekt, miks, ustalık), `medya-gorsel` (görseller), `medya-denetci` (salt okunur, şüpheci denetim),
`medya-gozcu` (yeni araç araştırması; kurmaz).
**İş akışları:** `medya-uretim` (analiz → plan → yapım → çizim → 3 mercekli denetim → düzeltme → rapor),
`medya-denetim` (bağımsız denetim), `medya-radar` (teknoloji radarı), `medya-yonetim` (baş ajan: inceleme + öneriler),
`medya-guncelle` (onaylanan önerileri uygular), `medya-beceri-yaz` (beceri yaz/incele/düzelt;
tanımlar `sistem/devam/beceri-tanimlari.json`). Stüdyo dışından:
`Workflow({scriptPath: '/Users/onurkaya/Projects/video/.claude/workflows/<ad>.js', args: {...}})`.
**Beceriler:** `medya-studyo` (giriş/yönlendirme), `kurgu-zanaati`, `hareket-tasarimi`, `ses-tasarimi`,
`gorsel-uretim`, `teslim-denetimi`, `arac-radari`. Motor becerileri **başvurudur**, yönlendirme `medya-studyo`'dadır:
HyperFrames'inkiler (`hyperframes-core`, `-cli`, `-keyframes`, `-registry`…; usage/feedback/görüşme adımları uygulanmaz)
ve `remotion-best-practices` (başındaki stüdyo kuralları önce gelir).

## Motorlar ve lisans kapısı
- **`medya ciz`** (stüdyonun kodu, ffmpeg): yazısız/grafiksiz gerçek çekim kurgusunda önce bu — planı kompozisyonsuz,
  kare dökmeden çizer (kesim, erime, sabit kadraj, punch/Ken Burns, hazır klipler, `hiz > 1`, kendi sesi + müzik; kısma
  `--yalniz-konusma` → `kisma.py`). Kapsam dışı öğede hata verir → HyperFrames. Ölçüldü (2026-10-08): kare kodlu planda
  her kare tam, ses ≤ 4 ms; 4K → 1080x1920 10 sn 12,6 sn, disk tepesi 0,02 GB, bellek tepesi 1,45 GB; 5 dk'lık
  112 çekimli 4K planda 1,92 GB, takas büyümedi.
- **HyperFrames** her iş için serbest (Apache-2.0) — hareketli grafik, yazı, süslü geçiş için varsayılan.
- **Remotion** yalnız `BRIEF.md` → Lisans bağlamı kişisel, yalnız dosya teslim edilen tek kişilik serbest iş ya da en
  çok 3 kişilik şirket/ekipse. Kullanıcı beyanı (2026-10-07): stüdyoyu yalnız kendisi, kişisel işlerde ve yalnız dosya
  teslim ettiği işlerde kullanıyor → varsayılan bağlam bu; yalnız 4+ kişilik işveren adına ya da müşteri kodu
  alacaksa HyperFrames (o durumda sor).
  Lisans anahtarı ASLA (ücretsiz anahtar da kullanım olayı gönderir); Studio kendiliğinden açılmaz; Google Fonts,
  uzak varlık, web-renderer, Lambda yok (kanca engeller). 5.x'e lisans incelemesiz geçilmez. Son çizimde
  `--image-format=png --color-space=bt709`.
- İki motor da ara kare üretmez: ağır çekim önce `medya yavaslat` (gerçek yüksek fps → doğal; hazır kare ≤2000 px'te
  RIFE, üstünde Apple → diğeri → minterpolate; gerçek kamerada RIFE en iyi ölçüldü). 4K'dan dikey: `--kirp x,y,gen,yük
  --olcek 1080x1920` (ara kareden önce kırpar; RIFE önce, 3,6 kat hızlı).
- **DaVinci Resolve 21.1 (ücretsiz, App Store) kurulu:** API ile yönetilemez (dış betik yalnız Studio'da). Yol: `medya nle`
  → `kurgu.otio` (Resolve; ölçüldü: kare-kesin) ya da `kurgu-kdenlive.otio` (Kdenlive 26.08 içe aktarım hatalarına
  uyarlanmış; "SON — sil" kliplerini sil, erimeleri U ile ekle). Kum havuzu: medya `projeler/` (Media Storage'a eklendi)
  ya da `~/Movies` altında olmalı. Erişilebilirlik izniyle menü/pencere otomasyonu çalışıyor (kırılgan; yalnız sınama ya
  da istek). "Claude Resolve'da kurguluyor" yolu Studio'nun yerleşik MCP'sidir (295 $) — ücretsiz kural gereği kapalı,
  yalnız kullanıcı açıkça isterse (`yetenekler.toml` → `resolve-studio-mcp`).

## Bir işe başlarken
1. Ortam: bu klasörde oturum başında otomatik yüklenir; değilse `source /Users/onurkaya/Projects/video/ortam.sh`.
2. `medya proje yeni "<ad>" --tur video|animasyon|gorsel|ses|karma --kaynak <dosyalar>` →
   `projeler/YYYY-AA-GG-ad/{BRIEF.md, KARARLAR.md, kaynak/, analiz/, plan/, calisma/, cikti/}`.
3. `BRIEF.md`'yi doldur; yalnız gerçekten bilinmeyen ve sonucu değiştiren şeyleri sor (amaç/izleyici,
   platform ve en-boy, süre, yazı olacak mı, müzik kaynağı).
4. Analiz → plan → yapım → çizim → denetim → rapor. Büyük işte `medya-uretim` iş akışı; küçük işte ilgili ajan
   ya da beceri. Denetim (`medya-denetci` / `medya-denetim`) geçmeden "bitti" denmez.

## Komutlar (`medya --help`, ayrıntı `medya <komut> --help`)
| İnceleme | Dönüştürme | Üretim | Ses | Denetim | Sistem |
|---|---|---|---|---|---|
| `incele` `kontak` `sahneler` `analiz` `ses-turu` `ses-olay` `muzik` `yaziya-dok` | `sdr` `cfr` `yavaslat` `meta-temizle` `ayir` `arkaplan-sil` | `ciz` (plan → video, ffmpeg) `gorsel-uret` (FLUX.2 klein) `seslendir` (VoxCPM2) | `ses-temizle` `ustala` | `senkron` `denetle` `zamankodu` | `proje` `yetenekler` `kur` `test [--agir]` `temizle` |
Teslim/devir: `nle` (kurgu planı → .otio Resolve / -kdenlive.otio / .edl). Kompozisyon/çizim: `hyperframes lint|check|snapshot --describe false|render`;
Remotion: proje klasöründen `$MEDYA/node_modules/.bin/remotion still|render src/index.ts <Id> …`.
Apple ML komutları bekçiyle çalışır: Neural Engine derleyicisi (`ANECompilerService`) takılıysa beklemeden hata
verir; çözüm kullanıcıda (`sudo killall ANECompilerService` ya da yeniden başlatma).

## HyperFrames notları (ölçülmüş)
- Bütün zamanları kare ızgarasına oturt (k/fps); aksi hâlde görüntü sesten 1 kareye kadar geç kalır.
- `data-playback-rate` < 1 kareleri tekrarlar → ağır çekimi önce `medya yavaslat` ile üret, `--cikti <ad>.mp4`:
  ProRes klip her kipte 16 bit PNG kareye açılır (çıkarma ayarlarıyla borudan ölçüldü: 4K 33 MB/kare; denemenin 237
  ağır çekim karesi 7,8 GB geçici alan), H.264 1080x1920 PNG'de 2,5 MB, taslak JPEG'de 0,22 MB. `.mov` ProRes yalnız
  NLE devrine.
- Varsayılan çizim kalitesi (CRF 16) uzun/grenli videoda devasa (4:48 → 2,5 GB); teslimde `--video-bitrate`.
- Gerçek çekimli **son** çizimde `--video-frame-format png`: varsayılan JPEG ara kareler VMAF 95,0; PNG 96,6 (ffmpeg doğrudan 96,8), en kötü kare 94,4 → 95,7; bedeli ~2 kat çizim süresi. Taslakta varsayılan yeter.
  2026-10-08 (O6): 1080p gerçek çekimde VMAF JPEG 94,8 / PNG 96,0 / `medya ciz` 96,2, ama PNG kipi Y'yi sabit ~1,9
  düzey düşürüyor; 4K kaynakta (5 işçi) takas 0,9 → 15,9 GB'a çıkıp çöktü → gerçek çekimde önce `medya ciz`.
- Lint 0 hata; tek duraklatılmış GSAP zaman çizelgesi; Math.random/Date yok; yazı tipleri yerel woff2 (latin-ext).
- Türkçe yazı (istenirse): `<html lang="tr">` şart — ölçüldü: `lang="en"` ile büyük harf "ISTANBUL", `tr` ile "İSTANBUL"; JS'te `toLocaleUpperCase('tr-TR')`.

## Uzun işler ve kullanım sınırı (5 saatlik pencere)
- **Başlarken:** `sistem/DURUM.md` "duraklatıldı" diyorsa ya da projede `DURUM.md` varsa önce onu oku, oradan sürdür.
- Uzun işler iş akışıyla yürür ve her aşama sonucunu dosyaya yazar; ajan boş dönerse (sınır/hata) iş akışı yarım
  çıktıyla sürmez, `yarida_kaldi` döner. Uzun ölçümler sonucu adım adım CSV/JSON'a yazar.
- **"Duraklat" denince:** çalışan iş akışlarını durdur (TaskStop) → arta kalan süreçleri kapat → bitmiş ajan
  çıktılarını ve iş akışı args'ını `sistem/devam/`'a kaydet → `sistem/DURUM.md`'yi yaz → büyük geçici dosyaları sil.
- **"Devam et" denince:** aynı oturumda `resumeFromRunId` (args aynı; bitenler önbellekten), yeni oturumda
  `sistem/devam/` args'ı ile yeniden çalıştır (`medya-uretim`: `atla`, `medya-beceri-yaz`: `yazildi`).
- İş akışlarını küçük tut (~10 ajan); bağımsız dalgalar hâlinde çalıştır ki bir kesinti hepsini götürmesin.
  `resumeFromRunId` önbelleği SIRAYA bağlıdır: ilk değişen/bitmemiş ajandan sonrası yeniden koşar.

## Yönetim ve güncelleme (baş ajan)
- **"Öneri / ne yapalım / sistemin durumu"** → `medya-yonetim` iş akışı (radarsız, hızlı). **"Yeni çıkanları araştır,
  sistemi güncelle"** → `medya-yonetim` `{radar: true}`. Rapor: `sistem/yonetim/<tarih>-oneriler.md` + `.json`.
- Kullanıcı önerileri onaylayınca → `medya-guncelle` `{oneriler_json, onaylanan: ['O1', …]}`: öneri başına sabit
  sürümlü kurulum + kayıt + uyarlayıcı + sınama + belge, bağımsız doğrulama, sonda tam `medya test`. Git commit/push
  yalnız kullanıcı isterse (`commit`/`push` argümanları).
- **Oturum özeti (SessionStart kancası `oturum-ozeti.py`):** yarım iş, son incelemeden geçen gün (30+ → incelemeyi
  öner), bekleyen kararlar, disk, git. Ağır işten önce disk düşükse kullanıcıya söyle.

## Bakım ve gelişim
- **Sınamalar:** `medya test` (doğruluk sınamaları: vuruş, sahne, ağır çekim, Whisper, Demucs, denetim, kanca).
  Bir yeteneği değiştirdikten sonra sınamalar geçmeden "çalışıyor" deme.
- **Yeni araç / model:** `arac-radari` becerisi + `medya-gozcu`; periyodik tarama `medya-radar`. Benimsenen araç:
  `yetenekler.toml`'a sağlayıcı + `medya/komutlar/` uyarlayıcı + `testler/` doğruluk sınaması + beceri güncellemesi.
  Ücretli/bulut araçlar yalnız `etkin = false` sağlayıcı olarak yazılır; kullanıcı açıkça isterse açılır.
- **Dersler:** her projeden sonra `sistem/dersler.md`'ye kısa ders; tekrar eden ders beceriye taşınır.
- **Yeni makine / onarım:** `zsh sistem/kur.sh` (bağımlılıklar, Swift aracı, beceri ve ajan bağlantıları).
- **Disk** (taban 5 GB; 2026-10-07 kurulumlardan sonra ~3–7 GB boş — takas boyutuna göre oynar): modeller `modeller/`,
  Python önbelleği `.uv/`; temizlik `medya temizle --uygula`. Büyük kurulumdan önce boyutu söyle ve sor.
  **Takas:** FLUX.2 (~9 GB) / VoxCPM2 (~7 GB) bellek tepesi macOS takasını büyütür ve diskten yer alır (2026-10-07:
  6 GB takas, boş disk 1,4 GB'a düştü). Ağır ML'yi sırayla çalıştır; `gorsel-uret`/`seslendir` diskte 3/2,5 GB altında
  çalışmaz; yeniden başlatma takası boşaltır. Ağır sınamalar yalnız `medya test --agir`.

## Ortam gerçekleri (2026-10-08)
Apple M2, 16 GB RAM, macOS 27. Homebrew kilitli (Xcode lisansı kabul edilmemiş; `sudo xcodebuild -license accept`
kullanıcının kararı) → araçlar uv/npm/resmî ikili ile kurulur; Swift için `DEVELOPER_DIR=/Library/Developer/CommandLineTools`.
Python 3.12 (`.venv`, uv; her ortam yalnız `.uv/python`'daki uv Python'unu kullanır: `UV_MANAGED_PYTHON=1`), ağır
ses yığını `ortamlar/ses` (torch, Beat This!, Essentia, librosa, Demucs, mlx-whisper),
ffmpeg-static 6.0 (`arac/ffmpeg`), HyperFrames 0.8.140, Remotion 4.0.533 (kök `node_modules`), OTIO 0.18.1,
RIFE 20221029 (`arac/rife`), mflux 0.21.0 + FLUX.2 [klein] 4B Q4 (`.uv/tools/mflux`, Python 3.13.16, paketler
`sistem/kisitlar/`'a sabit), mlx-audio 0.5.8 + VoxCPM2 4-bit
(`.uv/tools/mlx-audio`), SpeechBrain ECAPA (ses doğrulama), Kdenlive 26.08.1 ve DaVinci Resolve 21.1.0 (`/Applications`). Satıcı becerileri
depoda tutulmaz, sabit commit'ten üretilir: `python3 sistem/claude/satici/satici.py kur` + `bagla --uygula`. Döngüde ffmpeg'e `-nostdin`; zsh'de değişken sözcüklere
bölünmez (bayrakları açık yaz); ffmpeg `psnr` süzgeci farklı zaman damgalı akışlarda kare kaydırır (kareleri
doğrudan çözüp karşılaştır).
