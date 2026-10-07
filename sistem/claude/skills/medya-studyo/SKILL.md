---
name: medya-studyo
description: Use when the user asks for any media work - video edit, montage, reel, promo or product/feature animation, motion graphics, photo or cover image, music, voice or sound, personal or for work - even from another project folder, or says pause/continue on a media job (video, kurgu, montaj, tanıtım, animasyon, kapak, görsel, fotoğraf, müzik, ses, duraklat, devam et).
---

# Medya stüdyosu: giriş ve yönlendirme

Her medya işi `/Users/onurkaya/Projects/video` stüdyosunda, bir proje klasöründe, uzman ajan ve zanaat becerisiyle yürür. **Bu beceri yalnız yönlendirir.** Planı tek başına kurma, kendi betiğini yazma: o işin ajanı ve iş akışı zaten var.

**Ne zaman değil:** zanaat ayrıntısı (aşağıdaki beceriler), araç ekleme (arac-radari).

## Başlarken (komutlarda mutlak yol)
1. Stüdyo dışındaysan önce `/Users/onurkaya/Projects/video/CLAUDE.md`'yi oku. Kabuk durumu Bash çağrıları arasında korunmaz: her komutu `source /Users/onurkaya/Projects/video/ortam.sh && …` ile başlat.
2. `sistem/DURUM.md` "duraklatıldı" diyorsa bekleyen işi kullanıcıya söyle ve sor. İstek yarım kalmış bir projeye aitse `projeler/<p>/DURUM.md`'deki `[x]` aşamaları `atla`'ya girer. Yeni istekte yeni proje aç.
3. `du -ch <kaynaklar>` ve `df -h /` çalıştır. `--kaynak` tam kopya alır; sonrasında 5 GB'tan az yer kalacaksa sor.
4. Yalnız bilinmeyenleri tek mesajda, varsayılanıyla sor: amaç/izleyici, platform ve en-boy, süre, ekranda yazı (varsayılan YOK), müzik kaynağı ve lisansı, teslim tarihi, lisans bağlamı (motoru belirler), mahremiyet. Kapak istendiyse: kullanım yeri, en-boy, kapakta yazı (varsayılan yazısız, videodan seçilmiş kare). Kurulum ya da müzik üretme teklifi ilk mesaja girmez.
5. `medya proje yeni "<ad>" --tur video|animasyon|gorsel|ses|karma --kaynak <dosyalar>`; lisans kapısı geçtiyse `--motor remotion`. Başka klasörden gelen istekte de proje stüdyoda açılır. Yanıtları BRIEF.md'ye yaz.

## Kesin kurallar (tamamı CLAUDE.md'de)
- Yerel ve ücretsiz; telemetri kapalı; kişisel bilgi dışarı çıkmaz; lisansı belirsiz ya da NC medya işte yok.
- Asıllar salt okunur; silmeden, üzerine yazmadan önce sor. İstenmedikçe ekrana yazı yok.
- Read ile açılan her kare ya da temas sayfası modele gider: mahrem klipte önce sor, "yalnız sayısal mod" öner. Kamuya açık işte görüntüdeki kişilerin rızasını hatırlat; telifli şarkı yalnız kişisel paylaşımda.
- Ölçmeden iddia yok. "Vuruşta" için `medya muzik` güveni `yuksek` ve `medya senkron` geçmeli.

## Yönlendirme
| İstek | Ajan | Beceri |
|---|---|---|
| Kaynak analizi | medya-analist | — |
| Sıralama, geçiş, ağır çekim, kadraj, NLE devri | medya-kurgucu | kurgu-zanaati |
| Animasyon, hareketli grafik, kompozisyon ve çizim | medya-hareket | hareket-tasarimi |
| Müzik, ses, miks | medya-ses | ses-tasarimi |
| Fotoğraf, kapak, görsel | medya-gorsel | gorsel-uretim |
| Teslim, denetim | medya-denetci | teslim-denetimi |
| Yeni araç, ücretli servis | medya-gozcu | arac-radari |

İş akışları, duraklatma, satıcı becerileri, bağlı olmayan ajan/beceri, başka klasör: [yonlendirme](references/yonlendirme.md). Motor ve DaVinci/Kdenlive: [motor-ve-nle](references/motor-ve-nle.md).

## Boru hattı
Sıra: analiz → plan → yapım → çizim → denetim kapısı → rapor.
- **Video, karma ya da HyperFrames animasyonu:** `Workflow({scriptPath:'/Users/onurkaya/Projects/video/.claude/workflows/medya-uretim.js', args:{proje:'projeler/…'}})`.
- **Motor remotion ise:** aynı iş akışı; medya-hareket motoru BRIEF'teki 'Kompozisyon motoru' + 'Lisans bağlamı'ndan seçer (kapı geçmezse HyperFrames).
- Soru dönerse yanıtlarla `{proje, atla:['analiz'], yanitlar:'…'}`.
- İş akışı kapak/görsel üretmez: video bitince medya-gorsel + gorsel-uretim.
- Bir yeteneğe güvenmeden önce `medya test <yetenek>`.
- Apple ML "ANECompilerService" hatası verirse kullanıcıya `sudo killall ANECompilerService` öner; kendin çalıştırma.

## Doğrulama
- `medya-denetim.js` (`{cikti, proje, hedef, brief}`) ya da medya-denetci GEÇTİ demeden "bitti" yok; kapak ayrıca denetlenir.
- Türkçe rapor: dosya yolları ve boyutları, sayılarıyla ölçülenler, ölçülemeyenler ve izlenecek/dinlenecek saniyeler, lisans defteri. "Mükemmel" yok.
- Sonra `sistem/dersler.md`'ye kısa ders.

## Sık hatalar
- `sistem/DURUM.md`'deki stüdyo bakım listesini kullanıcının yeni işi sanmak.
- Başka klasörde ikinci Bash çağrısında `medya` bulunamıyor: `source` her komutta.
- İşte lisans kapısız Remotion; satıcı adımları (`usage`, `publish`, satıcı mülakatı).

Bilgi tarihi 2026-10-05; kanıt sistem/arastirma/2026-10-05/claude-code-ecosystem.md ve sistem/devam/ham/arastir-{remotion,davinci}.json; eskidiyse arac-radari.
