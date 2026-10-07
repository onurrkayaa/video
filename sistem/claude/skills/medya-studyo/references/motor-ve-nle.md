# Motor seçimi ve kurgu programına devir

## Kompozisyon motoru
- **HyperFrames 0.8.124:** varsayılan motor, Apache-2.0, iş için de serbest. Ayrıntısı hareket-tasarimi'nde.
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
- **Komut:** proje klasöründe `medya nle plan/kurgu.json --bicim otio|edl|hepsi` çalıştır. Çıktı `cikti/nle/` altına yazılır. `medya-uretim` bu adımı zaten yapar.
- **.otio dosyası:** DaVinci Resolve 18.5+ ve Kdenlive 25.04+ kesimleri açar; erimeler Kdenlive 26.08+ ile gelir (25.04 notları: geçişler aktarılmaz).
- **.edl dosyası:** CMX 3600 biçimindedir.
- **Aktarılanlar:** kesimler, erimeler ve işaretler.
- **Aktarılmayanlar:** hız (ağır çekim önce `medya yavaslat` ile klibe gömülür), kadraj ve zoom, renk, ses düzeyi. Bunlar işaret olarak gelir ya da ara klibe gömülür.

**Ajan ücretsiz Resolve'u yönetemez.** Dış betik desteği yalnız Studio sürümünde var. Resolve 21.1 ücretsiz sürümden Python betiklerini de kaldırdı. Kullanıcı kurguyu programda kendi sürdürür.

**"Claude DaVinci'de kurgulasın" isteği:** bunun için ücretli DaVinci Resolve Studio gerekir (295 $). Resolve 21.1'deki yerleşik MCP, File > Setup AI Assistants menüsünden kurulur.
- Kayıt defterinde `resolve-studio-mcp` olarak `etkin = false` durur.
- Yalnız kullanıcı açıkça satın alır ve isterse açılır.
- Bu yolla kareler modele gider; gizlilik kuralı geçerli.

**Kdenlive ve ücretsiz Resolve:** kullanıcının kurduğu uygulamalardır (`yetenekler.toml`'da `tur = "uygulama"`, `etkin = false`). Kurulum satırları kayıt defterinde; kurmak kullanıcının kararıdır:
- Kdenlive: 620 MB.
- Ücretsiz Resolve: 2,5 GB; App Store hesabı ya da kayıt formu gerekir.
