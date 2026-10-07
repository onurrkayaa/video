# Medya Stüdyosu

Bu klasör, Onur'un bu Mac'teki **yerel medya üretim stüdyosudur**: video kurgusu, animasyon ve hareketli grafik,
görsel/fotoğraf, ses — hem kişisel işler hem iş için. Her şey yerelde ve ücretsiz çalışır; araçlar değişebilir,
sistem değişmez: işler **yetenek** adıyla çağrılır (`medya <komut>`), arkasındaki araç kayıt defterinden seçilir.

## Kesin kurallar (kullanıcının)
- Ücretli hizmet, hesap açma, kredi, bulut çizim yok. HyperFrames'in `cloud`, `lambda`, `cloudrun`, `auth`,
  `publish`, `usage`, `feedback` komutları, `heygen` CLI'si ve `hyperframes media-use resolve` (HeyGen kataloğu)
  kullanılmaz — `medya-koruma` kancası bunları engeller; engellenince yolunu değiştir, kancayı aşmaya çalışma.
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

## Mimari (üç katman)
| Katman | Nerede | Ne yapar |
|---|---|---|
| Yetenek | `medya/` (CLI), `yetenekler.toml` (kayıt), `medya/isciler/` (ağır ortam işçileri), `arac/medya-apple` (Swift: VideoToolbox, Vision, SoundAnalysis), `arac/rife` (ağır çekim yedeği) | Araçtan bağımsız komutlar; sağlayıcı değişince komut aynı kalır; asılan/başarısız sağlayıcı yedeğine düşer |
| Motor | HyperFrames (HTML+GSAP, varsayılan) · Remotion 4.0.533 (React/TSX, **lisans kapısıyla**) · ffmpeg | Kompozisyon ve çizim |
| Bilgi | Beceriler `sistem/claude/skills/` (→ `~/.claude/skills/` bağlantı; satıcı becerileri sabit commit'le, `sistem/claude/satici/KAYNAKLAR.md`), bilgi tabanı `sistem/arastirma/<tarih>/`, dersler `sistem/dersler.md` | Zanaat, karar kuralları, araç seçimleri ve gerekçeleri |
| Ajan | Ajanlar `sistem/claude/agents/` (→ `~/.claude/agents/`), iş akışları `.claude/workflows/`, kanca `sistem/claude/hooks/medya-koruma.py` | Uzman roller, uçtan uca boru hattı, kuralların zorlanması |

**Ajanlar:** `medya-analist` (kaynak analizi → `analiz/OZET.md`), `medya-kurgucu` (`plan/kurgu.json`,
`KARARLAR.md`, ara klipler, NLE devri), `medya-hareket` (motor seçimi, kompozisyon, animasyon, çizim), `medya-ses`
(müzik, katman, efekt, miks, ustalık), `medya-gorsel` (görseller), `medya-denetci` (salt okunur, şüpheci denetim),
`medya-gozcu` (yeni araç araştırması; kurmaz).
**İş akışları:** `medya-uretim` (analiz → plan → yapım → çizim → 3 mercekli denetim → düzeltme → rapor),
`medya-denetim` (bağımsız denetim), `medya-radar` (teknoloji radarı), `medya-beceri-yaz` (beceri yaz/incele/düzelt;
tanımlar `sistem/devam/beceri-tanimlari.json`). Stüdyo dışından:
`Workflow({scriptPath: '/Users/onurkaya/Projects/video/.claude/workflows/<ad>.js', args: {...}})`.
**Beceriler:** `medya-studyo` (giriş/yönlendirme), `kurgu-zanaati`, `hareket-tasarimi`, `ses-tasarimi`,
`gorsel-uretim`, `teslim-denetimi`, `arac-radari`. Motor becerileri **başvurudur**, yönlendirme `medya-studyo`'dadır:
HyperFrames'inkiler (`hyperframes-core`, `-cli`, `-keyframes`, `-registry`…; usage/feedback/görüşme adımları uygulanmaz)
ve `remotion-best-practices` (başındaki stüdyo kuralları önce gelir).

## Motorlar ve lisans kapısı
- **HyperFrames** her iş için serbest (Apache-2.0) — varsayılan.
- **Remotion** yalnız `BRIEF.md` → Lisans bağlamı kişisel, yalnız dosya teslim edilen tek kişilik serbest iş ya da en
  çok 3 kişilik şirket/ekipse. Şirket 4+ kişi, müşteri kodu alacak ya da bilinmiyorsa → HyperFrames (boşsa sor).
  Lisans anahtarı ASLA (ücretsiz anahtar da kullanım olayı gönderir); Studio kendiliğinden açılmaz; Google Fonts,
  uzak varlık, web-renderer, Lambda yok (kanca engeller). 5.x'e lisans incelemesiz geçilmez. Son çizimde
  `--image-format=png --color-space=bt709`.
- İki motor da ara kare üretmez: ağır çekim önce `medya yavaslat` (gerçek yüksek fps → ≤2000 px'te RIFE, 4K'da Apple →
  diğeri → minterpolate; gerçek kamerada RIFE en iyi ölçüldü).
- **DaVinci Resolve:** ücretsiz sürüm ajan tarafından yönetilemez (dış betik yalnız Studio'da; 21.1'de Python da
  kaldırıldı). Ücretsiz yol: `medya nle` → `.otio` → kullanıcı Resolve ya da Kdenlive'da açar. "Claude Resolve'da
  kurguluyor" yolu Studio'nun yerleşik MCP'sidir (295 $) — ücretsiz kural gereği kapalı, yalnız kullanıcı açıkça
  isterse (`yetenekler.toml` → `resolve-studio-mcp`).

## Bir işe başlarken
1. Ortam: bu klasörde oturum başında otomatik yüklenir; değilse `source /Users/onurkaya/Projects/video/ortam.sh`.
2. `medya proje yeni "<ad>" --tur video|animasyon|gorsel|ses|karma --kaynak <dosyalar>` →
   `projeler/YYYY-AA-GG-ad/{BRIEF.md, KARARLAR.md, kaynak/, analiz/, plan/, calisma/, cikti/}`.
3. `BRIEF.md`'yi doldur; yalnız gerçekten bilinmeyen ve sonucu değiştiren şeyleri sor (amaç/izleyici,
   platform ve en-boy, süre, yazı olacak mı, müzik kaynağı).
4. Analiz → plan → yapım → çizim → denetim → rapor. Büyük işte `medya-uretim` iş akışı; küçük işte ilgili ajan
   ya da beceri. Denetim (`medya-denetci` / `medya-denetim`) geçmeden "bitti" denmez.

## Komutlar (`medya --help`, ayrıntı `medya <komut> --help`)
| İnceleme | Dönüştürme | Ses | Denetim | Sistem |
|---|---|---|---|---|
| `incele` `kontak` `sahneler` `analiz` `ses-turu` `ses-olay` `muzik` `yaziya-dok` | `sdr` `cfr` `yavaslat` `meta-temizle` `ayir` `arkaplan-sil` | `ses-temizle` `ustala` | `senkron` `denetle` `zamankodu` | `proje` `yetenekler` `kur` `test` `temizle` |
Teslim/devir: `nle` (kurgu planı → .otio / .edl). Kompozisyon/çizim: `hyperframes lint|check|snapshot --describe false|render`;
Remotion: proje klasöründen `$MEDYA/node_modules/.bin/remotion still|render src/index.ts <Id> …`.
Apple ML komutları bekçiyle çalışır: Neural Engine derleyicisi (`ANECompilerService`) takılıysa beklemeden hata
verir; çözüm kullanıcıda (`sudo killall ANECompilerService` ya da yeniden başlatma).

## HyperFrames notları (ölçülmüş)
- Bütün zamanları kare ızgarasına oturt (k/fps); aksi hâlde görüntü sesten 1 kareye kadar geç kalır.
- `data-playback-rate` < 1 kareleri tekrarlar → ağır çekimi önce `medya yavaslat` ile üret.
- Varsayılan çizim kalitesi (CRF 16) uzun/grenli videoda devasa (4:48 → 2,5 GB); teslimde `--video-bitrate`.
- Gerçek çekimli **son** çizimde `--video-frame-format png`: varsayılan JPEG ara kareler VMAF 95,0; PNG 96,6 (ffmpeg doğrudan 96,8), en kötü kare 94,4 → 95,7; bedeli ~2 kat çizim süresi. Taslakta varsayılan yeter.
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

## Bakım ve gelişim
- **Sınamalar:** `medya test` (doğruluk sınamaları: vuruş, sahne, ağır çekim, Whisper, Demucs, denetim, kanca).
  Bir yeteneği değiştirdikten sonra sınamalar geçmeden "çalışıyor" deme.
- **Yeni araç / model:** `arac-radari` becerisi + `medya-gozcu`; periyodik tarama `medya-radar`. Benimsenen araç:
  `yetenekler.toml`'a sağlayıcı + `medya/komutlar/` uyarlayıcı + `testler/` doğruluk sınaması + beceri güncellemesi.
  Ücretli/bulut araçlar yalnız `etkin = false` sağlayıcı olarak yazılır; kullanıcı açıkça isterse açılır.
- **Dersler:** her projeden sonra `sistem/dersler.md`'ye kısa ders; tekrar eden ders beceriye taşınır.
- **Yeni makine / onarım:** `zsh sistem/kur.sh` (bağımlılıklar, Swift aracı, beceri ve ajan bağlantıları).
- **Disk** (~15 GB boş, sınır 5 GB): modeller `modeller/`, Python önbelleği `.uv/`; temizlik `hyperframes clean`,
  `arac/uv cache clean`. Büyük kurulumdan önce boyutu söyle ve sor.

## Ortam gerçekleri (2026-10-05)
Apple M2, 16 GB RAM, macOS 27. Homebrew kilitli (Xcode lisansı kabul edilmemiş; `sudo xcodebuild -license accept`
kullanıcının kararı) → araçlar uv/npm/resmî ikili ile kurulur; Swift için `DEVELOPER_DIR=/Library/Developer/CommandLineTools`.
Python 3.12 (`.venv`, uv), ağır ses yığını `ortamlar/ses` (torch, Beat This!, Essentia, librosa, Demucs, mlx-whisper),
ffmpeg-static 6.0 (`arac/ffmpeg`), HyperFrames 0.8.124, Remotion 4.0.533 (kök `node_modules`), OTIO 0.18.1,
RIFE 20221029 (`arac/rife`). Döngüde ffmpeg'e `-nostdin`; zsh'de değişken sözcüklere
bölünmez (bayrakları açık yaz); ffmpeg `psnr` süzgeci farklı zaman damgalı akışlarda kare kaydırır (kareleri
doğrudan çözüp karşılaştır).
