# Motor seçimi ve kurgu programına devir

## Kompozisyon motoru
- **HyperFrames 0.8.140:** varsayılan motor, Apache-2.0, iş için de serbest. Becerileri aynı etiketin commit'inden (`satici.py`); `~/.claude/skills`'e bağlanana dek eski v0.8.124 kopyaları etkin (durum: `satici.py dogrula`). Ayrıntısı hareket-tasarimi'nde.
- **Remotion 4.0.533:** yalnız lisans kapısı geçerse kullanılır. Kapı, BRIEF.md'deki "Lisans bağlamı" satırına bakar.

| Lisans bağlamı | Motor |
|---|---|
| kişisel; serbest (tek kişi, yalnız bitmiş dosya teslimi); iş, en çok 3 kişi | Remotion kullanılabilir |
| iş, şirket 4+ kişi; müşteri Remotion kodunu alıyor ya da çalıştırıyor | HyperFrames |
| boş ya da bilinmiyor | Sor. Yanıt yoksa HyperFrames. |

- **Remotion projesi açmak:** lisans bağlamını proje açılmadan sor; kapı geçerse `medya proje yeni "<ad>" --tur animasyon --motor remotion`. Proje varsayılan motorla açıldıysa ve kapı sonra geçtiyse: `cp -R /Users/onurkaya/Projects/video/sablonlar/remotion projeler/<p>/calisma/remotion` ve BRIEF.md'deki "Kompozisyon motoru" satırını `remotion` yap. medya-uretim bu satırı okumaz (HyperFrames kurar); Remotion işini medya-hareket ile doğrudan yürüt. Sonra `remotion-best-practices` becerisini kullan; dosyanın başındaki stüdyo kuralları önce gelir.
- **Ücretli lisans fiyatları:** yalnız raporda bilgi olarak yazılır. Creators 25 $/koltuk/ay, Automators en az 100 $/ay.
- **Remotion 5.x:** şartlarına göre yükleniciler ekip sayısına girer. Bu şartlar şu an yürürlükte değil. Lisans incelemesi yapmadan 5.x'e yükseltme.

## Ağır çekim
`medya yavaslat` kaynağa göre yöntem seçer:
- Kaynak gerçekten yüksek fps ise `dogal` kullanır.
- Değilse sırayla Apple ML'i, RIFE v4.6'yı ve minterpolate'i dener. Asılan ya da başarısız olan yöntem bir sonrakine düşer.

Ölçüm sonuçları (sistem/dersler.md):
- Hızlı harekette Apple ile RIFE yaklaşık aynı kalitede. İkisi de minterpolate'ten 1,5–2 dB daha iyi.
- Sakin çekimde yöntemler arasında fark yok.

HyperFrames'te `data-playback-rate` 1'in altına inerse kareler tekrarlanır. Bu yüzden ağır çekim önce `medya yavaslat` ile üretilir. Ayrıntısı kurgu-zanaati'nde.

## Kurgu programına devir (NLE)
- **Komut:** proje klasöründe `medya nle plan/kurgu.json --bicim otio|kdenlive|edl|hepsi`. Çıktı `cikti/nle/`: `kurgu.otio` (Resolve), `kurgu-kdenlive.otio` (Kdenlive), `kurgu.edl` (CMX 3600). `medya-uretim` bu adımı zaten yapar.
- **Ölçüldü (2026-10-08):** kare kodlu sınama medyası (`testler/nle_sinama.py`: karışık 30/60/24 fps, 12 karelik erime, çekim sesi, numaralı müzik tonları) programda çizildi, `testler/nle_olc.py` her kareyi ve sesi plana karşı ölçtü. Kdenlive'da kaydedilen proje XML'i de denetlendi (`nle_olc.py <proje> --kdenlive-xml <proje.kdenlive>`): çizim işaretleri göstermez.

| Program ← dosya | Sonuç |
|---|---|
| DaVinci Resolve 21.1 ← `kurgu.otio` | GEÇTİ: kesimler 0 kare, 12 karelik erime yerinde (ağırlık rampasından 11,85 kare, ortası kesimde), 60 fps kaynak kare-kesin, 24 fps ±1 kare (giriş noktası zaman çizelgesi ızgarasına aşağı yuvarlanıyor), müzik ve çekim sesi ≤ 2 ms (müzik `medya senkron` ses hizasıyla 0 ms). Klip işareti ve kılavuz ölçülmedi |
| Kdenlive 26.08.1 ← `kurgu-kdenlive.otio` | GEÇTİ, erime yerine kesim + işaret: proje standart "HD 720p 30 fps", bütün giriş noktaları doğru, ses ≤ 1,5 ms. XML'de klip işareti girişin iki katındaydı (giriş 21 → işaret 42, zaman çizelgesinde 0,7 sn geç): `nle` 2026-10-08'de düzeltildi, Kdenlive'da yeniden ölçülmedi |
| Kdenlive 26.08.1 ← `kurgu.otio` | KALDI: proje 60 fps, her izin son klibi ve erimeden sonraki klip 0'dan başladı (müzik 0,5 sn, çekim sesi 1 sn erken), erime düştü (src/otio/otioimport.cpp) |

- **Resolve'da:** File > Import > Timeline… → `kurgu.otio` → "Set timeline resolution" plan boyutu (OTIO çözünürlük taşımaz); kare hızı ve "Automatically set project settings" OTIO'dan doğru gelir → Ok. App Store sürümü kum havuzlu: `projeler/` Tercihler > System > Media Storage'a eklendi (2026-10-08), proje medyası doğrudan açılır. Medya başka bir klasördeyse o klasörü de ekle.
- **Kdenlive'da:** File > OpenTimelineIO Import… → `kurgu-kdenlive.otio` (çözünürlük ilk klipten gelir). Sonra her izin sonundaki 1 karelik "SON — sil" kliplerini sil. Kırmızı "erime N kare" işaretlerinde klibi seç → U ya da birleşime çift tıkla; süreyi N kare yap. `nle` kırmızı işaretleri klibin ilk karesine yazar (düzeltmeden sonra Kdenlive'da doğrulanmadı: işaret klibin başında değilse not yine o klibindir). Kdenlive işareti kutudaki klibe koyduğu için aynı medyadan kesilmiş öteki klipte de görünebilir.
- **Aktarılmayanlar:** hız (ağır çekim önce `medya yavaslat` ile klibe gömülür), kadraj ve zoom, renk, ses düzeyi. Bunlar işaret olarak gelir ya da ara klibe gömülür.
- **Zaman kodlu kamera medyası:** `-kdenlive.otio` başlangıç TC'sini Kdenlive'ın hesabıyla (zaman çizelgesi hızında) yazar. TC'li gerçek kamera medyası sınanmadı.

**Ajan ücretsiz Resolve'u API ile yönetemez.** Dış betik yalnız Studio'da var; Resolve 21.1 ücretsiz sürümden Python betiklerini de kaldırdı; konsol erişilebilirlikte görünmeyen özel arayüz. macOS erişilebilirlik izniyle (VS Code'a verildi, 2026-10-08) menüler, dosya pencereleri ve Qt pencereleri sürülebiliyor: içe aktarma, Export Timeline, Quick Export, Tercihler. Ölçüm böyle yapıldı; kırılgan ve ekranı/fareyi kullanır, yalnız sınamada ya da kullanıcı isterse. Kurguyu programda kullanıcı sürdürür.

**"Claude DaVinci'de kurgulasın" isteği:** bunun için ücretli DaVinci Resolve Studio gerekir (295 $). Resolve 21.1'deki yerleşik MCP, File > Setup AI Assistants menüsünden kurulur.
- Kayıt defterinde `resolve-studio-mcp` olarak `etkin = false` durur.
- Yalnız kullanıcı açıkça satın alır ve isterse açılır.
- Bu yolla kareler modele gider; gizlilik kuralı geçerli.

**Kdenlive ve ücretsiz Resolve:** kullanıcının uygulamalarıdır (`yetenekler.toml`'da `tur = "uygulama"`).
- **Kdenlive 26.08.1 KURULU** (2026-10-07, `/Applications/kdenlive.app`, KDE noterli, SHA doğrulandı).
- **DaVinci Resolve 21.1.0 KURULU** (2026-10-08, App Store, `/Applications/DaVinci Resolve.app`, 2,9 GB; daha güçlü renk/ses). Tercihlerde güncelleme, kullanım verisi ya da çökme raporu seçeneği yok (App Store sürümü; bütün sayfalar tarandı). Blackmagic Cloud ve İnternet hesaplarına giriş yapılmadı. Çalışırken yalnız *:49153 dinleme soketi görüldü, dış bağlantı yok.
