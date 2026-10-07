# Yönlendirme ayrıntıları

## İş akışları
Her yerden mutlak yolla çağrılır: `Workflow({scriptPath:'/Users/onurkaya/Projects/video/.claude/workflows/<ad>.js', args})`. `proje` stüdyo köküne göre yazılır.

| İş akışı | Ne zaman | args |
|---|---|---|
| `medya-uretim` | Videoyu, karma işi ya da HyperFrames animasyonunu baştan sona üretmek için (Remotion değil). BRIEF.md dolu olmalı. | `{proje, atla?:['analiz','plan','yapim-ses','yapim-gorsel','cizim'], yanitlar?}` |
| `medya-denetim` | Video, ses ya da görsel teslim edilmeden önce. | `{cikti, proje?, hedef?:'web'\|'sosyal'\|'youtube'\|'arsiv', brief?}` |
| `medya-radar` | Ayda bir ya da yeni bir araç duyulunca. | `{alanlar?, konu?}` |
| `medya-beceri-yaz` | Stüdyonun becerileri yazılırken. | `{beceriler:[{ad, yazildi?}]}` |

`medya-uretim` her aşamayı projedeki `DURUM.md`'ye işaretler. İş yarıda kalırsa:
- Aynı oturumdaysan `resumeFromRunId` kullan.
- Yeni oturumdaysan `[x]` işaretli aşamaları `atla`'ya koyup yeniden çalıştır.

**Duraklat:** çalışan iş akışlarını durdur (TaskStop) → arta kalan süreçleri kapat → bitmiş ajan çıktılarını ve iş akışı args'ını `sistem/devam/`'a kaydet → `sistem/DURUM.md`'yi "duraklatıldı" diye yaz. Kendiliğinden yeniden başlatma. **Devam et:** `sistem/DURUM.md`'deki sıradan sürdür. Ayrıntı CLAUDE.md "Uzun işler ve kullanım sınırı".

`medya-uretim` sona doğru `ustala`, `meta-temizle` ve `medya nle` adımlarını çalıştırır. Kapak ya da görsel adımı yoktur.

## Küçük işler
İş akışı gerekmez; ilgili ajanı ya da beceriyi doğrudan kullan. Örnekler:
- **Tek fotoğraf ya da kapak:** medya-gorsel ve gorsel-uretim.
- **Yalnız ses düzeyi ya da teslim:** teslim-denetimi.
- **Yalnız müzik kısaltma:** medya-ses ve ses-tasarimi.

Denetim kapısı küçük işte de geçerlidir.

## Ajanlar ya da beceriler bağlı değilse
Önce `ls ~/.claude/agents/medya-*` ve `ls ~/.claude/skills` ile bak.
- **Beceri yüklenemiyorsa:** `/Users/onurkaya/Projects/video/sistem/claude/skills/<ad>/SKILL.md` dosyasını Read ile oku.

Ajan listesi boşsa ajanlar alt ajan türü olarak kayıtlı değildir. Ne yapacağın işe göre değişir:
- **`medya-uretim` ile çalışıyorsan:** sorun yok. İş akışı rol dosyalarını kendi yolundan okur.
- **Tek ajan gerekiyorsa:** genel bir alt ajana "önce `/Users/onurkaya/Projects/video/sistem/claude/agents/<ad>.md` dosyasını oku" de.
- **Kalıcı çözüm:** `zsh /Users/onurkaya/Projects/video/sistem/kur.sh --bagla` beceri ve ajan bağlantılarını kurar. Bu komut `~/.claude` altına yazar, bu yüzden önce kullanıcıya söyle.

## Satıcı becerileri: önce stüdyo kuralları
HyperFrames kompozisyon motorudur. Becerileri sözdizimi başvurusu olarak kullanılır:
- Kullanılacaklar: `hyperframes-core`, `-cli`, `-animation`, `-keyframes`, `-registry`, `-audio`.
- Yönlendirme bu beceridedir, `hyperframes` yönlendiricisinde değil.

**Atlanacak satıcı adımları:**
- `npx hyperframes usage`. Kanca bunu engeller.
- Niyet mülakatı ve "pitch round". Brief, stüdyonun `BRIEF.md`'sidir. Satıcının `workflow`/`flow` alanlarını ekleme.
- `publish`, `feedback`, `cloud`, `lambda`, `cloudrun`, `auth`.
- Masaüstü uygulaması ve Framey tanıtımı.
- `hyperframes snapshot` daima `--describe false` ile çalışır.

**Kullanılmayacak satıcı becerileri:**
- `media-use`: HeyGen hesabı ister.
- `music-to-video`: sabit tempo ızgarası kurar; "sesler kaymış" hatası bundan çıktı.
- Altyazı becerileri (`embedded-captions`, `talking-head-recut`): yalnız kullanıcı yazı isterse.

**Başvuru olarak okunabilecekler:** `product-launch-video`, `pr-to-video`, `faceless-explainer`, `motion-graphics`, `general-video`. Bunlar yalnız stüdyo projesinin içinde, stüdyonun BRIEF.md'sinden sonra, medya-hareket ve hareket-tasarimi ile birlikte kullanılır.

**Remotion satıcı becerisi:** `remotion-best-practices` dosyasının başındaki stüdyo kuralları satıcı metninden önce gelir.

## Başka bir klasörden gelen istek
Örnek: "bu repodaki yeni özellik için tanıtım animasyonu".
0. Stüdyonun CLAUDE.md'si orada yüklenmez: önce `/Users/onurkaya/Projects/video/CLAUDE.md`'yi oku. Her Bash komutunu `source /Users/onurkaya/Projects/video/ortam.sh && …` ile başlat (kabuk durumu çağrılar arasında korunmaz; otomatik yükleme yalnız stüdyo klasöründe).
1. Projeyi stüdyoda aç: `medya proje yeni "<ad>" --tur animasyon`. Kullanıcının deposuna dosya yazma; depoyu yalnız oku (README, değişiklikler, ekran görüntüleri).
2. Yalnız gerçekten bilinmeyenleri sor:
   - Hangi özellik tanıtılıyor, kime ve nerede gösterilecek?
   - En-boy ve süre ne olacak?
   - Ekranda yazı olacak mı? Tanıtımda yazı olası olduğu için sor, varsayma.
   - Ekran kaydı ya da logo var mı?
   - Lisans bağlamı ne? (Motor seçimini belirler: [motor-ve-nle](motor-ve-nle.md).)
3. Yapım medya-hareket ve hareket-tasarimi ile yapılır: HyperFrames ise `medya-uretim` (animasyon planını sahne/zaman çizelgesi olarak yazar); Remotion ise medya-hareket doğrudan. Teslimden önce denetim kapısından (`medya-denetim`) geçer.
