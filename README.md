# Medya Stüdyosu

Bu Mac'te, Claude Code ile **yerel ve ücretsiz** video, animasyon, görsel ve ses üretimi. Ücretli hizmet, hesap
ya da bulut yok; kişisel görüntüler bilgisayardan çıkmaz.

## Nasıl kullanılır
Claude Code'u açıp (bu klasörde ya da herhangi bir yerde) isteğini yazman yeterli. Örnekler:

- "İndirilenler'deki şu videolarla müziğe oturan 45 saniyelik dikey bir montaj yap."
- "Ürünümüzün yeni özelliği için 30 saniyelik bir tanıtım animasyonu hazırla; ekran görüntüleri şu klasörde."
- "Bu konuşmanın sesini temizle, altına telifsiz müzik koy, Instagram'a uygun ses düzeyine getir."
- "Şu fotoğrafın arka planını sil, kare ve hikâye boyutlarında dışa aktar."
- "Bu videoyu Reels, YouTube ve WhatsApp için hazırla ve teslimden önce denetle."
- "Yeni çıkan şu modeli sisteme ekleyelim mi?" — araştırır, kanıtla önerir; onayın olmadan kurmaz.
- "Bu kurguyu DaVinci'de kendim de düzelteyim." — kurgunun `.otio` dosyasını verir; ücretsiz Resolve ya da Kdenlive açar.
- "Duraklat" / "devam et" — uzun işi durdurur, kaldığı yeri `sistem/DURUM.md`'ye yazar; sonra oradan sürdürür.
- "Bu metni sakin bir erkek sesiyle Türkçe seslendir." — yerel dış ses (VoxCPM2); aynı projede hep aynı ses.
  Kendi sesinle istersen 10 sn'lik temiz bir kayıt ver.
- "Ürün fotoğrafımı mermer bir masaya koy" / "şu konseptte üç görsel üret" — yerel görsel üretimi (FLUX.2 klein;
  görselde İngilizce yazı gerekiyorsa daha yavaş Z-Image-Turbo: tek afiş istemi × 2 tohumluk denemede yazıyı 2/2
  doğru yazdı, FLUX.2 0/2).
- "Ne önerirsin?" / "Yeni çıkanları araştır, sistemi güncelleyelim." — baş ajan (yönetici) inceler, önerileri
  maliyetiyle sunar; onaylarsan uygular ve sınar.

Her iş `projeler/YYYY-AA-GG-ad/` altında kendi klasöründe yürür; asıl dosyaların salt okunur kopyalanır.
Teslimden önce bağımsız bir denetçi ölçüm yapar; rapor neyin ölçüldüğünü ve neyi senin izleyip dinlemen
gerektiğini söyler.

## Daha iyi sonuç için çekerken
- Ağır çekim yapılacak anları telefonun **Ağır Çekim** modunda (120/240 fps) çek; sonradan üretilen ara kare iyi
  ama gerçek yüksek fps her zaman daha temizdir.
- Her çekimi en az 5 saniye sabit tut; bir de 10 saniyelik "ortam sesi" kaydı al (kesimleri yumuşatmak için).
- Dosyaları WhatsApp ile değil **AirDrop/kablo** ile aktar (WhatsApp görüntüyü ve sesi sıkıştırır, tarihleri siler).
- HDR ayarını çekimler arasında değiştirme; iş için ekran kaydında ayrı bir deneme hesabı ve Odak modu kullan.
- Mahrem görüntülerde: araçlar yereldir ama Claude'un baktığı kareler modele gider; istersen "yalnız sayısal mod" iste.

## Neler var
- `medya` komutu: inceleme, sahne/çekim analizi (Apple Vision), müzik vuruşu + güven, Türkçe yazıya dökme
  (Whisper), ses katmanlarına ayırma, ağır çekim (Apple ML ara kare), HDR→SDR, ses ustalığı, kalite denetimi.
- Gerçek çekim kurgusu: `medya ciz` planı (kesim, erime, kadraj, punch/Ken Burns, çekim sesi + müzik) HyperFrames'siz,
  kare dökmeden doğrudan ffmpeg ile çizer; kare-kesin ölçüldü. 4K çekimden 10 sn'lik dikey kurguda disk tepesi 0,02 GB
  (HyperFrames'in PNG kipi aynı planda 3,5 GB kare açıp takası 15,9 GB'a çıkararak çöktü); 5 dk'lık 112 çekimli 4K
  planda bellek tepesi 1,9 GB, takas büyümedi. Yazı, hareketli grafik ve süslü geçiş gerekirse kompozisyon motoru devreye girer.
- İki kompozisyon motoru: **HyperFrames** (HTML + GSAP; her iş için serbest, varsayılan) ve **Remotion** (React;
  kişisel işlerde, yalnız dosya teslim ettiğin serbest işlerde ve en çok 3 kişilik şirket işlerinde ücretsiz —
  daha büyük şirkette ücretli lisans gerektiği için orada HyperFrames kullanılır). Remotion'da 3B sahne (Three.js) ve
  Lottie animasyonu da var; 3B Mac'in GPU'sunda çizilir (90 karelik dikey 3B sahne 3,9 sn, ölçüldü).
- Yerel üretim: görsel (FLUX.2 [klein] 4B ve Z-Image-Turbo, ikisi de Apache-2.0; aynı istem ve tohumlarla A/B'de
  Z-Image İngilizce afiş yazısını 2/2 doğru yazdı, FLUX.2 0/2; Z-Image 3,3–3,7 kat yavaş) ve Türkçe dış ses (VoxCPM2
  8-bit, Apache-2.0; 40 Türkçe cümlede CER %0,74) — hesap, bulut yok.
- Elle ince ayar: DaVinci Resolve (ücretsiz, App Store) ve Kdenlive kurulu; ikisine devir kare kodlu sınamayla ölçüldü.
- Ağır çekim: telefonun yüksek fps çekiminde ara kare üretmeden; değilse RIFE (1080p'ye kadar; gerçek kamerada en iyi
  ölçülen) ya da Apple ML (4K) → ffmpeg (biri takılırsa sıradakine geçer). 4K çekimden dikey (9:16) ağır çekim doğrudan
  teslim boyutunda üretilir (gerektiğinde RIFE ile). Çizimin geçici alanı HyperFrames'in çıkarma ayarlarıyla borudan
  ölçüldü: ProRes 4K 7,8 GB → `.mp4` 1080x1920 0,6 GB.
- Kurgu programına devir: `medya nle` (.otio: DaVinci Resolve; -kdenlive.otio: Kdenlive; .edl). "Claude DaVinci'yi yönetsin"
  yalnız ücretli Resolve Studio'nun MCP'siyle olur (295 $) — istemedikçe kapalı.
- Baş ajan (yönetici: öneriler, aylık inceleme, güncelleme) ve uzman ajanlar (analist, kurgucu, hareket, ses, görsel,
  denetçi, gözcü); iş akışları (üretim, denetim, radar, yönetim, güncelleme).
- Koruma kancası: ücretli/bulut komutlarını, sormadan büyük model indiren satıcı adımlarını (ör. altyazı akışlarının kendi
  Whisper'ı) ve sabit sürümü bozan yükseltmeleri engeller. Alt yazı istersen döküm stüdyonun kurulu Türkçe Whisper'ıyla yapılır.
- Ayrıntı: `CLAUDE.md` (sistemin kuralları ve mimarisi), `sistem/dersler.md`, `sistem/arastirma/`.

## Bakım
- `medya test` — bütün yeteneklerin doğruluk sınamaları.
- `python3 sistem/claude/satici/satici.py dogrula` — satıcı becerileri (HyperFrames, Remotion) sabit commit'le aynı mı ve
  Claude'da devrede mi; değilse ne yapılacağını yazar (`bagla` önce planı gösterir, `--uygula` eski kopyaları yedekleyip bağlar;
  geri almak: `bagla --geri <arşiv> --uygula`).
- `zsh sistem/kur.sh` — yeni bilgisayarda ya da bozulunca yeniden kurulum.
- Stüdyonun Python ortamları (görsel üretimi, ses analizi, dış ses) kendi Python'unu kullanır (`.uv/python`);
  bilgisayardaki Python'un güncellenmesi onları etkilemez. Kancalar ve `kur.sh`'nin ilk adımı ise PATH'teki `python3`'ü
  (çoğunlukla sistemdekini) çağırır: onu kaldırma.
- `sistem/DURUM.md` — yarım kalan iş ve devam sırası; `sistem/gelistirme.md` — sıradaki geliştirmeler.
- Disk dolarsa (büyük modeller belleği takasa taşırır): Mac'i yeniden başlatmak takas dosyalarını boşaltır;
  `medya temizle --uygula` önbellekleri siler.
- Apple'ın görüntü analizi/ağır çekimi "Neural Engine takılı" hatası verirse: Terminal'de
  `sudo killall ANECompilerService` (ya da Mac'i yeniden başlat).
- `medya yetenekler --saglayicilar` — hangi iş hangi araçla yapılıyor, lisansları, boyutları.
