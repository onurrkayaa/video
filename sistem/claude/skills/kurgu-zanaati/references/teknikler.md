# Kurgu teknikleri — sayılar ve kararlar

Öncelik (Murch): duygu > hikâye > ritim > göz izi. Montajda ritmin payı artar. Sıra: seçki → stringout → kaba →
ince → görüntü kilidi → renk → ses. Stringout (sıralı kontak + tablo) kullanıcıya onaylatılır; değişiklik burada ucuz.

## Seçki
- Künye: `medya incele` → `etiketler.olusturma` (çekim zamanı), `video.kare_olcumu.gercek_fps`, HDR, VFR, dönme, GPS.
  Gerçek fps ≥ 85 ise özgün ağır çekim (doğal yavaşlatılır). Kap fps'i yüksek ama gerçek fps ~30 olabilir (yinelenen
  kare): kararı `gercek_fps` verir.
- `medya analiz … --sahneler` → `cekim_ozeti[]`: `en_iyi_an`, `en_iyi_puan`, `ilgi_merkezi` [x,y] (0–1, sol üst),
  `hareket`, `etiketler`. An penceresi 1,5–6 sn, eylemden 0,3–0,5 sn önce başlar.
- Göz kırpma karesinde, gülüşün ortasında kesme; gülüş olayından (`medya ses-olay`) 0,3 sn sonra kes.
- Yan yana neredeyse aynı iki kare yok (istenmemiş atlama kesimi); çekim boyu değişsin (geniş → orta → yakın).
- `medya ses-turu` önceden kurgulanmış videoda (müzik çekim sesine karışık mı); ham tek çekimde `ses-olay` kullan.

## Sıra ve yay
- Zaman damgası varsa gerçek kronoloji; 2 saatten (ya da gün) büyük boşluk = yeni bölüm. Bölüm içinde küçük takaslar serbest.
- Yay: açılış (geniş, sakin, kim/nerede) → gelişme (gündelik neşe) → doruk (şarkının en büyük bölümü: en yakın, en
  duygulu anlar, ağır çekim) → nefes (köprü/enerji düşüşü ≥ 6 LU: uzun tutuş, fotoğraf) → kapanış (açılışla kafiyeli
  görüntü, son notada tutulan en güçlü "biz" çekimi).
- Göz izi: gelen odak (yüz/ilgi merkezi) gidenin odağına köşegenin %15–20'si içinde → kesim görünmez. Hareket yönü
  kesimde korunur (soldan sağa sağa devam).

## Ritim (müzik güvenine bağlı)
| Bar enerjisi | Çekim başına |
|---|---|
| alt %30 | ≥ 8 vuruş (2 ölçü) |
| orta | 4 vuruş |
| üst %30 | 2 vuruş; zirvede en çok 4–8 kesimlik 1 vuruş patlaması, sonra uzun tutuş |
Yumuşak/akustik 60–80 BPM — yalnız `guven_seviye: yuksek` ise (davulsuz/yumuşak şarkı çoğu zaman yüksek çıkmaz;
değilse aşağıdaki `orta`/`dusuk` maddesi): çekim başına 4–8 vuruş, ölçü başında kes, cümle başlarında 0,5–1 vuruşluk erime, ağır çekim
nakaratta, en hızlı kurgu yalnız son nakaratta. 3–4'ten fazla eş aralık art arda yok.
- **Kaydır, oynatma:** kesim vuruşta kalır; kaynağın giriş noktası kaydırılır ki eylemin tepesi de vuruşa düşsün.
- `guven_seviye` `orta`/`dusuk`: vuruş ızgarası yok; bölüm sınırı ve söz cümlesi başı (`medya ayir … --iki` →
  `medya yaziya-dok <vokal> --sarki --dil <dil>`) + 0,5–1,5 sn erime (±100 ms hatayı gizler); `medya muzik`in ürettiği tık
  dinletisini (müzik sol, tık sağ) kullanıcıya dinlemesi için öner.

## Geçişler
Varsayılan düz kesim. Geçişin motivasyonu olmalı: hareket (savurma, itme), ışık (sızma, flaş), zaman/yer değişimi
(erime, dip), müzik olayı (vuruşta flaş/punch). Bir ana tür (%60+) + en çok 2 vurgu; videoda en çok 2 shader geçişi.
Süre: sakin 0,5–1,2 sn, orta 0,3–0,5, yüksek 0,15–0,3. Güven yüksekse geçişin ortası/tepesi vuruşta.
Sakin/romantik: dakikada ≤ 4–6 süslü geçiş; dönme (spin) yok.

| `gecis.tur` | Ne zaman | Süre | HyperFrames | ffmpeg 6.0 |
|---|---|---|---|---|
| kesim | varsayılan; vuruşta / eylemde | 0 | — | — |
| erime | zaman/yer değişimi, sakin | 12–24 kare | gelen `.kat` opaklığı | `xfade=transition=fade` |
| j-kesim / l-kesim | konuşma, gülüş köprüsü | ses 6–24 kare önce/sonra | ayrı `<audio>` | — |
| eslesme | benzer biçim/hareket/renk | 0 | `match-cut`, `cut-the-curve` | — |
| savurma | gerçek hareketin devamı, enerjik | 8–12 kare | `whip-pan-cut` (yerleşik `whip-pan` shader'ı kenar pikselini uzatır: bak) | — |
| yakinlasma | yükselen müzik, vurgu | çıkış 6–8, giriş 8–12 kare | `cinematic-zoom`, `parallax-zoom` | `zoomin` (bulanıksız) |
| isik | bölüm değişimi, açılış/bitiş | 12–24 kare, tepe kesimde | `light-leak`, `organic-light-leak-overlay` | — |
| siyah-dip / beyaz-dip | zaman sıçraması; anı | 12–24 kare | siyah/beyaz katman opaklığı | `fadeblack` / `fadewhite` |
| flas | vuruş/vurgu (tanıtım) | 2–3 kare yükseliş, 4–8 sönüş | `flash-through-white`, `editorial-flash-overlay` | `eq=brightness='…':eval=frame` |
Sınır: herhangi 1 sn'de ≤ 3 flaş (WCAG 2.3.1). İndirilmiş ışık sızması/LUT paketi yok (lisans belirsiz): kodla üret.
Blok adları `hyperframes catalog --tag transition --json` ile doğrulandı (2026-10-05, 49 öğe).

## Kamera hareketi
- **Punch-in:** 1,00 → 1,08–1,12 (ince) / 1,15–1,25 (sert); anında ya da 2–4 karede `expo.out`; güven `yuksek` ise ölçü
  başında/vurguda, değilse eylem tepesinde ya da söz cümlesi başında (vuruş iddiası yok);
  yüz/ilgi merkezine çapalı; sakin işte ölçü başına ≤ 1, romantik nakaratta 2–3.
- **Ken Burns (fotoğraf):** 1,00 → 1,04–1,08 (≤ 1,12), 4–6 sn, kayma ≤ %3–5; doğrusal ya da `sine.inOut`; hareket
  görüntü gelirken başlamış olur; yüzde/gözde biter; yönler değişir. GSAP (alt piksel), `zoompan` değil.
- **2,5B paralaks (katman):** `medya arkaplan-sil foto.jpg --cikti calisma/klipler/foto-on.png`; arka = aynı fotoğraf
  1,00 → 1,03, ön = PNG 1,00 → 1,06 + %1–2 yanal, 4–6 sn `sine.inOut`. Ön/arka göreli kayma ≤ genişliğin %2–3'ü
  (fazlasında arkadaki öznenin kenarı görünür). Kenarları snapshot'ta büyütüp bak. Derinlik modeli kurulu değil;
  Depth Anything V2 Base/Large ve 3d-ken-burns ticari değil (NC).
- **Zoom sınırı:** etkin ölçek = cover ölçeği × punch × sabitleme zoom'u ≤ 1,15 (kaynak pikseli başına çıktı pikseli,
  kırpılan eksende; cover = max(Wç/Wk, Hç/Hk)). Aynı en-boy: 4K → 1080p punch ≤ 2,3; 1080p → 1080p ≤ 1,15. 16:9 4K →
  1080x1920: cover 1920/2160 = 0,89 → punch ≤ 1,29. 16:9 1080p → dikey: cover zaten 1,78 → punch yok, yumuşak
  görüneceğini kullanıcıya söyle. `plan_denetle` cover × `hareket.olcek`'i ⚠ ile bildirir (sabitleme zoom'unu bilmez).

## Hız
- **Ağır çekim:** `medya yavaslat <kaynak> --hiz H --bas A --sure S --cikti calisma/klipler/<ad>-yavas.mp4` — motor
  seçme (gerçek yüksek fps → doğal; değilse hazır kare ≤ 2000 px ise RIFE, üstünde Apple ML → diğeri → minterpolate;
  HDR'yi kendisi SDR'ye çevirir; çıktı sessiz). HyperFrames'e `.mp4` (H.264 CRF 12): HyperFrames ProRes'i her kipte 16 bit
  PNG kareye açar; `.mov` (ProRes 422 HQ) yalnız NLE devrine. ×2 çoğu çekimde güvenli; ×4 yalnız basit harekette (el,
  saç, su, kesişen insan "jöle" yapar: şeride bak). Dakikada 1–3, yalnız duygu doruklarında; en yavaş an ölçü başında.
  Planda `hiz` < 1, `klip` = bu dosya, `ses` ≠ kendi.
- **4K'dan dikey ağır çekim:** `--kirp x,y,gen,yük --olcek 1080x1920` (görünen yönde, çift sayılar; ara kareden önce,
  doğal yolda da). 16:9 4K'nın tam boy 9:16 penceresi 1216x2160, `x = clamp(ilgi_x·Wk − 608, 0, Wk − 1216)`, çifte
  yuvarla. Ölçüldü (2026-10-08, deneme kesiti; HyperFrames'in kare çıkarma ayarları borudan taklit edildi, gerçek çizim
  yapılmadı): 237 ağır çekim karesinin geçici alanı ProRes 4K 7,8 GB → ProRes 1080x1920 1,6 GB (kırp/ölçek) → `.mp4`
  1080x1920 0,60 GB (kodek; PNG son çizim) / 0,05 GB (taslak JPEG); RIFE 4K'ya göre 3,6 kat hızlı. Kalite: gerçek
  çekimde kırp-önce = ara-kare-önce (0,00 dB; yalnız küçük harekette ölçüldü); aşırı ince desen (kumaş, ekran, ızgara)
  ölçeklenince örtüşür (sentetik en kötü −4,1 dB) → böyle çekimde yalnız `--kirp`.
  - Punch/Ken Burns olan çekimde pay bırak: `--olcek` = 1080x1920 × en büyük `hareket.olcek` (çifte yuvarla) ya da yalnız
    `--kirp` (cover 0,89 kalır, punch ≤ 1,29). Payla uzun kenar 2000 px'i aşarsa yöntem yine Apple önce.
  - Kırpma klibe pişer: kadraj değişirse klip yeniden üretilir. O çekimde `kadraj.ilgi` klibe göredir:
    `ilgi_x' = (ilgi_x·Wk − x)/gen` (y için aynı).
  - PNG'li son çizimin diske sığması için 1x 4K çekimler de teslim boyutuna inmeli: denemede 237 karelik 1x 4K HEVC
    PNG'de 2,8 GB (ağır çekimden büyük); bugün bunun komutu yok (gelistirme.md).
- **Rampa:** yalnız gerçek fps ≥ çıktı fps/hız olan kaynakta (240 fps → 0,125x; 120 → 0,25x):
  `$P $K/rampa.py kaynak/X.MOV --bas A --sure S --hiz 0.25 --a 0.8 --b 1.0 --c 1.6 --d 1.8 --cikti calisma/klipler/X-rampa.mp4`
  (a–d kesit içi kaynak saniyesi: iniş 6–12 kare, tutuş 0,5–2 sn, çıkış 6–10 kare). Değilse hız kesmesi: 1x çekim →
  vuruşta kes → `yavaslat` klibi.
- Hızlandırma > 2x: hareket bulanıklığı gerekir (`hyperframes-animation` motion-blur).

## Kadraj 16:9 → 9:16
- Özne aralığı kırpma genişliğinin %15'inden azsa sabit kırpma (ortanca merkez); tekdüze hareket → doğrusal pan;
  takip → ~1 sn yumuşatma, hız ≤ 0,25 kırpma genişliği/sn, yalnız kesimde sıfırla. Yüzler yüksekliğin %15–65 bandında
  (Reels arayüzü üst/alt). Formül: [kompozisyon](kompozisyon.md).
- Bulanık dolgu yalnız gerekli içerik kırpmaya sığmıyorsa (zıt kenarlarda iki kişi); kullanıcıya söyle. İstenmeden değil.

## Sabitleme (yalnız ölçülünce)
```sh
$P $K/titreme.py kaynak/X.MOV --bas A --sure S          # ~0,004 üstü ve setin en titreği → aday
arac/ffmpeg -nostdin -v error -ss A -t S -i kaynak/X.MOV -vf vidstabdetect=shakiness=5:accuracy=15:result=calisma/X.trf -f null -
arac/ffmpeg -nostdin -v info -ss A -t S -i kaynak/X.MOV -vf vidstabtransform=input=calisma/X.trf:smoothing=15:optzoom=1,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -crf 14 calisma/klipler/X-sabit.mp4 2> calisma/X-sabit.log
grep 'Final zoom' calisma/X-sabit.log                     # Z yüzde → 1+Z/100
$P $K/titreme.py calisma/klipler/X-sabit.mp4            # ≥ %50 düşüş yoksa sabitlenmişi kullanma
```
İki geçişte aynı `-ss/-t`. Kadraj ve punch-in'den önce, tam çözünürlükte. `zoomspeed` `optzoom=1`'de etkisiz.
`optzoom=1` zoom'u sınırlamaz: `Final zoom: Z` (yalnız `-v info`'da yazılır) okunur, 1+Z/100 KARARLAR.md'ye.
1+Z/100 > 1,10 ya da kadraj/punch ile etkin ölçek > 1,15 ise `optzoom=0:zoom=<daha küçük Z>` (kenarda siyah
kalabilir: kontakla bak) ya da sabitlemeyi bırak. Ölçüldü (2026-10-05): sarsıntılı fikstürlerde Z = 15,5 ve 28,9.
Titreme ölçüsü özne hareketini de sayar: kararı kontak sayfasıyla birlikte ver; `--sure` ≥ 1,5 sn (kısa kesit ölçülemez).
Rolling-shutter yalpası düzelmez. HDR kaynakta önce `medya sdr`. Desensiz dokuda vid.stab işe yaramayabilir (ölçüldü).

## Gece çekimi
Sıra: SDR → gürültü azaltma → aydınlatma → hafif keskinlik → gren en son. Önce aydınlatma yok. Hızlı: `hqdn3d=2:3:5:8`,
renk gürültüsü `chromanr=thres=25`; kaliteli ama çok yavaş `nlmeans`. Ten plastikleşmeden dur; hareketli karede
hayalet var mı şeride bak. Apple zamansal gürültü süzgeci bu Mac'te desteklenmiyor.

## Renk
1. Normalleştir: HDR → `medya sdr` (varsayılan mobius; ölçümde beyaz Y: mobius 218, hable 182). Renk kararını HDR
   kaynağın temas sayfasından verme (`kontak` ton eşlemez).
2. Eşle: sahnedeki çekimleri bir kahraman kareye — `signalstats` YAVG/UAVG/VAVG ölç, küçük `eq`/`colortemperature`.
3. Tek global görünüm (yumuşak S eğrisi); LUT yalnız kullanıcı verirse (`lut3d`).
4. Gren en son, hafif. Ölçüm: [doğrulama](dogrulama.md).

## Röportaj / konuşmalı iş videosu
- `medya yaziya-dok X --dil tr --cikti analiz/yazi/<ad>.json` → kelime zamanlarıyla cümle seç; kesim kelime içinden
  ≥ 50 ms uzakta, duraklamada. Her ses sınırında 10–30 ms yumuşatma (tık). Konuşma köprüsü J/L kesim.
- `ses: kendi`, `hiz: 1`, `vurusa: false`. Atlama kesimini ara görüntü (b-roll) ya da gerçek kadraj farkıyla örtme
  (ani dijital zoom yalnız zoom sınırı izin verirse). Plan yalnız çekimin kendi sesini bilir: b-roll çekimi
  `ses: sessiz`, altta süren konuşma kompozisyonda ayrı `<audio id="s<no>">` ([kompozisyon](kompozisyon.md)); yeni
  plan alanı uydurma. Bu ses NLE'ye taşınmaz.
- Müzik altta, ducking, konuşma temizliği (`medya ses-temizle`) → `ses-tasarimi`. İsim/ünvan yazısı yalnız istenirse.
- Görüntüdeki müşterilerin rızası ve ticari lisanslı müzik kullanıcıya hatırlatılır.
- Kullanıcı Resolve'da sürdürecekse: `medya nle plan/kurgu.json --bicim hepsi` → `cikti/nle/<ad>.otio` (Resolve),
  `<ad>-kdenlive.otio` (Kdenlive) + `.edl`. Resolve'a erimeler taşınır (Kdenlive'a kesim + işaret; içe aktarım adımları
  medya-studyo → motor-ve-nle); kadraj/hareket/diğer geçişler/pişmemiş hız kırmızı işaret + klip notu
  olur. OTIO'da müzik tam seviyede (ducking/seviye taşınmaz), b-roll altı konuşma ve J/L taşması yok: ducking, ses
  temizliği, ustalık Resolve'da yeniden yapılır; HyperFrames çıktısı ayrı bir teslimdir. İçe aktarım kare kodlu sınamayla
  ölçüldü (2026-10-08): Resolve kare-kesin (24 fps kaynakta ±1 kare), Kdenlive -kdenlive.otio ile doğru. Klip notu
  işaretinin yeri Kdenlive'da ölçüldü (tek işaretli sınamada doğru karede: kaynak 21 → zaman çizelgesi 114), Resolve'da
  ölçülmedi: Resolve'da kullanıcıya "not o klibin" de, "o karede" deme. Medya yolları mutlak; dosyalar taşınırsa
  yeniden bağla.
