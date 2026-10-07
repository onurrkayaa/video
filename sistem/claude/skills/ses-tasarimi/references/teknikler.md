# Teknikler — komutlar ve tarifler

Önce `source /Users/onurkaya/Projects/video/ortam.sh` (PATH'te `ffmpeg`/`ffprobe` = `arac/` kopyaları), proje kökünden
çalış (`projeler/<ad>/`). `B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts`, `PY=$MEDYA/ortamlar/ses/bin/python`.
Ölçümler 2026-10-05'te `testler/veri` fikstürleriyle bu Mac'te alındı. zsh: değişkenden hemen sonra `:` gelirse `${X}:`
yaz (`$X:s` değiştirici sanılır, "no previous substitution" hatası alındı). Döngüde ffmpeg'e `-nostdin`.

## 1. Klip sesini videonun saatinde çıkar
```
ffmpeg -nostdin -v error -i kaynak/v.mp4 -map 0:a:0 -af aresample=48000:async=1:first_pts=0 -ac 1 -c:a pcm_s24le calisma/ses/konusma-ham.wav
```
Ses akışı görüntüden geç başlıyorsa düz çıkarım sesi öne alır: 120 ms'lik başlangıç farkında düz çıkarım 0 ms verdi,
`first_pts=0` başa 120 ms ekleyip hizaladı (ölçüldü). `yaziya-dok`, `ses-olay`, `ses-temizle`, `kisma.py` bu WAV'la
çalışsın: bütün zamanlar videonun saatinde olur. Konuşma için mono yeter (`ses-temizle` zaten mono verir).

## 2. Konuşma temizliği
```
medya yaziya-dok calisma/ses/konusma-ham.wav --dil tr --cikti analiz/konusma-ham-yazi.json
medya ses-temizle calisma/ses/konusma-ham.wav --cikti calisma/ses/konusma.wav --dogrula
$PY $B/temizlik_olc.py --once calisma/ses/konusma-ham.wav --sonra calisma/ses/konusma.wav --yazi analiz/konusma-ham-yazi.json --json analiz/temizlik.json
medya yaziya-dok calisma/ses/konusma.wav --dil tr --cikti analiz/konusma-yazi.json
$PY $B/cer.py --metin analiz/konusma-ham-yazi.json --yazi analiz/konusma-yazi.json --kapi temizlik
```
- `--siddet 12` varsayılan (SI-SDR 1,8 → 10,1 dB; Whisper 12/15 → 13/15; sınırsızda 10/15). Kapı kalırsa `--siddet 8`.
  Fikstürde kahverengi gürültüyle sınırsız bastırma Whisper ortalama olasılığını 0,951 → 0,847 düşürdü, 12 dB düşürmedi.
- Gürültü anlaşılırlığı bozmuyorsa (pembe gürültü fikstüründe dökümler ve güven değişmedi) temizlik bir tercih: A/B dinlet.
- Çıktı mono 48 kHz, hizalama 0,0 ms, sonda ~30 ms kısa (DeepFilterNet `-D`); videoya koyarken doldur (bölüm 8).
  `--cikti x.mp4` sesi videoya ekler; kare sayısı korunur (`apad` + `-t`; 2026-10-05'te düzeltildi, sınama var).
- **Kırpma/rüzgâr tanısı (temizlikten önce):** kanal başına
  `ffmpeg -nostdin -i calisma/ses/ham-stereo.wav -af astats=measure_perchannel=Peak_level+Peak_count+Flat_factor:measure_overall=none -f null - 2>&1 | grep -E "Peak|Flat"`.
  Fikstür: kırpılmış sinüs tepe 0,0 dB, Flat factor 34,5, Peak count 95 400; temiz sinüs Flat 0, 908. İki kanal varsa
  kırpması az, rüzgâr bandı (< 200 Hz, §12 tayf A/B) zayıf olanı seç (`-af pan=mono|c0=c1`). Kırpma geri dönüşsüzdür
  (`adeclip` yalnız yumuşatır): kullanıcıya hangi saniyelerde olduğunu söyle.
- Kurulumsuz ffmpeg süzgeçleri (`highpass`, `adeclip`, `dialoguenhance`, `speechnorm`, `deesser`) yalnız önce/sonra
  `temizlik_olc.py` ile. `adeclick` kullanma: fikstürde tıkı gidermedi, dosyanın her yerini değiştirdi (ölçüldü).
- Yankı giderme yok: ses-temizle yalnız gürültü bastırır (araştırma: eksik).

## 3. Müzik
**Ana WAV ve analiz** (göreli yol da olur: 2026-10-05'te işçi yolu mutlağa çevrilecek biçimde düzeltildi):
```
medya muzik "$PWD/kaynak/sarki.m4a" --cikti "$PWD/analiz/muzik.json"
```
→ `analiz/muzik-ana.wav` (48 kHz/24 bit, saat budur), `muzik.json` (`vuruslar`, `olcu_baslari`, `bolumler`,
`guven_seviye`), görseller (Read), güven yüksek değilse `muzik-tik.wav` (sol müzik, sağ tık): kullanıcıya 1 dk dinlet.
MP3/AAC'yi ikinci kez çözme (kod çözücü/dolgu farkı 20–40 ms kaydırır, araştırma).

**Kısaltma/uzatma: `kisalt.py`** (çoklu ek; tek ek de aynı). Parçalar kaynak zamanında tutulanlardır; her ek önceki
parçanın sonunda biter, sonraki parçanın başı çıktıda tam ek anına oturur (ölçüldü: 0,0 ms; araştırmadaki `atrim=T2`
biçimi 30 ms erken getirdi, yeniden analiz tempoyu 100 → 200 BPM'e kaydırdı).
```
$PY $B/kisalt.py yap --ana analiz/muzik-ana.wav --parcalar 0-7.7 12.5-17.3 19.7-24 --gecis 0.03 --sonum 1 --esle 13.0 --cikti calisma/ses/muzik-ana.wav --harita analiz/kisalt.json
medya muzik "$PWD/calisma/ses/muzik-ana.wav" --cikti "$PWD/analiz/muzik-kisa.json" --ana "$PWD/calisma/ses/muzik-ana.wav"
$PY $B/kisalt.py olc --harita analiz/kisalt.json --ozgun analiz/muzik.json --kisa analiz/muzik-kisa.json --fps 30 --sure <video sn> --json analiz/kisalt-olc.json
```
Fikstür (24 sn, iki ek): ek aralıkları 600/600 ms, F 0,964, düzey −0,06 LU, son 50 ms sessiz, süre tam.
- **Ek yeri, güven `yuksek`:** ölçü başında, aynı tür bölümler arasında (`bolumler`), `--gecis 0.02–0.08`. Kapılar
  (`olc`): ek başına vuruş aralığı ±10 ms, F ≥ 0,95, ±0,5 LU, `--fps` ile ek en yakın ölçü başına ±1 kare.
- **Güven `orta`/`dusuk`:** ek yalnız `bolumler` sınırında ya da vokal cümle başında, `--gecis 0.5`–`1.5` (eşit güç;
  ±100 ms hatayı örter). Vuruş iddiası yok; vuruş/F kapıları anlamsız, yalnız düzey, kuyruk, süre. Ek yerinin §12
  tayf A/B'si + kullanıcıya dinleyeceği saniyeler (`ekler_cikti_sn`).
- **Bitiş (araştırma):** varsayılan şarkının gerçek sonu (outro, son kadans) = video sonu. Geriye doğru zamanla:
  son parça şarkının sonunda biter, kısaltma ortadan yapılır; gerçek son sığmıyorsa son ölçü başında 1–3 sn
  `--sonum`. Kapı: son 50 ms < −60 dBFS (`olc` ölçer), son ölçü başı ±1 kare, süre `--sure` ±1 kare.
- **Başlangıcı kaydırma:** ilk parça 0'dan başlamak zorunda değil (`--parcalar 31.2-…`); ya da ana WAV'ı olduğu gibi
  bırakıp kompozisyonda `data-media-start` ver (plan `muzik.bas` = müzik dosyasında videonun 0. sn'sine denk gelen an, ≥ 0;
  müzik videodan SONRA başlayacaksa ana WAV'ın başına sessizlik ekle — tek saat, `bas: 0`; negatif `bas` nle/senkron'da desteklenmez).
- **Söz–doruk hizası** (ör. "en duygusal söz videonun doruğunda"):
  1. `medya ayir kaynak/sarki.m4a --iki --cikti calisma/ses/katmanlar` → `medya yaziya-dok calisma/ses/katmanlar/vocals.wav --dil tr --sarki [--ipucu "<söz metni>"] --cikti analiz/soz.json`.
  2. Vokal katmanının sessiz olduğu yerdeki kelime halüsinasyondur (araştırma): `ffmpeg -nostdin -i calisma/ses/katmanlar/vocals.wav -af silencedetect=n=-40dB:d=0.3 -f null - 2>&1 | grep silence_`
     aralıklarına düşen kelimeleri at (−40 dB mühendislik eşiği).
  3. "En duygusal yer" ölçülemez: 2–4 aday satırı zamanlarıyla sun (son nakarat, en yüksek vokal enerjili cümle), kullanıcı seçer.
  4. Doruk anı `plan/kurgu.json`'dan (kurgu-zanaati); görüntü doruğunu müziğe kaydırmak da seçenektir — kurgucuya öner.
  5. Üç çapa: söz başı L → doruk C, şarkının sonu → video sonu V, başlangıç. Doruktan önce C sn, sonra V − C sn
     kalacak şekilde iki yanda ayrı ekler; `--esle L` çıktıda C'yi vermeli (±1 kare). Her eki `olc` ayrı ölçer.
  6. Kısaltılmış dosyada yeniden `yaziya-dok --sarki` (vocals'ı yeniden ayır): söz başı C'ye ±1 kare.
- Germe en çok ±%3 (araştırma); Rubber Band kurulu değil, `pedalboard.time_stretch` `ortamlar/ses`'te var.

## 4. Katmanlar
`medya ayir <dosya> [--iki] [--model htdemucs_ft] --cikti calisma/ses/katmanlar` → vocals/drums/bass/other ya da
vocals/no_vocals (9 sn'lik klip 8 sn sürdü). Kullanım: vokal girişleri, konuşma altındaki müziği ayıklama, vokalsiz
katmanda vuruş sınaması. Katman zamanlama/düzenleme içindir; tek başına "yeni ses" diye satılmaz. Demucs varsayılan
`--shifts` rastgele kaydırır (araştırma: iki çalıştırma farklı): bir kez üret, dosyayı sakla.

## 5. Kısma (ducking)
```
$PY $B/kisma.py --yatak calisma/ses/muzik-ana.wav --konusma calisma/ses/konusma.wav --araliklar analiz/konusma-yazi.json --bas 0 --cikti calisma/ses/muzik-kisik.wav --json analiz/kisma.json --png analiz/kisma.png
```
- `--konusma`: çıktı zamanında konuşma + dış ses katmanı, miks seviyesinde; `--araliklar` birden çok JSON alır (konuşma,
  dış ses, `medya ses-olay` kahkahası). Montajda katmanı almak için kompozisyonu müzik öğesi `data-volume="0"` ile taslak
  çiz, sesini bölüm 1'deki gibi çıkar.
- Zarf (araştırma): −12 dB, 120 ms önce, 80 ms iniş, 450 ms çıkış; arası 0,57 sn'den kısa konuşmalarda inik kalır.
  Kapı kalırsa betiğin önerisini uygula (−15'e kadar; ötesinde `--derinlik -15 --kazanc <dB>`: yatağı genel indirir,
  fikstür: −0,7 LU → `--kazanc -9` ile 11,3 LU). Fikstür: −12'de 9,5 LU → `--derinlik -14` 11,5 LU.
- `--bas` = plan `muzik.bas`. Çıktı ana WAV'la aynı uzunlukta: kompozisyonda yalnız `src` değişir, `data-start`/
  `data-media-start` aynı kalır (vuruşlar ve `plan_denetle.py` müzik kayması denetimi geçerli). 2 sn kaydırmalı sınamada
  kısma konuşma aralıklarına tam oturdu (−12,0 dB, aralarda 0,0 dB).
- Studio'da elle düzenlenecekse `--hf calisma/ses/kisma-hf.json --medya-bas <data-media-start>` → müzik öğesinin
  `data-automation`'ı. Ölçülen şey WAV'dır; şerit rampaları 7 noktayla yaklaşır.
- Kullanma: `sidechaincompress` (ileri bakış yok, derinlik opak; araştırma zarfı bu yüzden seçti); hyperframes-audio
  `carve.mjs` (`@hyperframes/core` kurulu değil).
- Mono konuşma ffmpeg/HyperFrames stereo miksine kanal başına −3 dB girer, ses yüksekliği aynı kalır (ölçüldü).

## 6. Mikro geçişler, J/L
- Her sert ses kesimine 5–10 ms: `afade=t=in:d=0.008`, `afade=t=out:st=<son−0.008>:d=0.008`; HyperFrames
  `data-fade-in`/`data-fade-out` (sn, ≥ 0.01). Müzik eki: 20–80 ms `acrossfade=…:c1=qsin:c2=qsin` (eşit güç).
- J/L: çekim sesi görüntüden 4–12 kare önce başlar (J) ya da sonra biter (L) (araştırma). HyperFrames'te ses ayrı
  `<audio>` (aynı kaynak saati), video `muted`: hyperframes-core `references/creator-editing-recipes.md`. Plandaki
  `j-kesim`/`l-kesim` kurgu-zanaati'nindir; ses ek yerlerine yine 10 ms geçiş.

## 7. Efektler
```
$PY $B/efekt.py --tur whoosh --fps 30 --tohum 2 --cikti calisma/ses/efektler/whoosh-2.wav --json calisma/ses/efektler/whoosh-2.json
```
- Türler: `whoosh` (geçiş), `riser` (kesimde biter, tepe 1 kare önce), `vurus`, `tik`. Her geçişe ayrı `--tohum` (aynı ses
  tekrar etmesin); aynı tohum aynı baytı verir (ölçüldü). Künye JSON'u lisans defterine.
- Yerleştirme: `data-start` = olay anı − `tepe_sn`; olay kare ızgarasındaysa sonuç da ızgarada. ffmpeg'de
  `adelay=<ms>:all=1`. Kapı: olay ±1 kare (araştırma).
- Hazır sesler ve lisansları: [kaynaklar](kaynaklar.md). Seviye yaratıcı karardır: efekt anındaki kelimeler `cer.py
  --kapi miks`te değişmemeli; son seviyeyi kullanıcı dinleyerek onaylar.

## 8. Miks ve videoya koyma
Kompozisyon varsa HyperFrames miksler (katmanları medya-hareket bağlar). Yoksa (normalize=0: katmanlar birim kazançla
toplanır):
```
ffmpeg -nostdin -v error -i calisma/ses/konusma.wav -i calisma/ses/muzik-kisik.wav -i calisma/ses/efektler/whoosh-2.wav -filter_complex "[2:a]adelay=8533:all=1[w];[0:a][1:a][w]amix=inputs=3:duration=longest:dropout_transition=0:normalize=0,aresample=48000[m]" -map "[m]" -ac 2 -c:a pcm_f32le calisma/ses/miks.wav
ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 kaynak/v.mp4
ffmpeg -nostdin -v error -i kaynak/v.mp4 -i calisma/ses/miks.wav -map 0:v:0 -map 1:a:0 -c:v copy -af apad -c:a pcm_s24le -t <video süresi> calisma/ara.mov
```
Dış ses ile konuşma aynı videodaysa miks seviyesindeki katmanların entegre düzeyi ±2 LU (mühendislik eşiği, araştırma
değil): `ffmpeg -nostdin -i <katman>.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1`; farkı `volume=<dB>`.
`-shortest` kullanma (ses kısaysa videoyu keser); `apad` + `-t` ile 553 kare korundu. Miks tepesi kırpılmamalı.
AAC parçaları uç uca eklenmez (her ekte kodlayıcı dolgusu birikir, araştırma). HyperFrames çizimi sesi AAC yazar ve
`ustala` yeniden kodlar (iki kuşak); kompozisyonsuz işte bu PCM yolu tek kodlamadır.

## 9. Ses düzeyi hedefleri
| Teslim | `medya ustala` | `medya denetle --hedef` |
|---|---|---|
| Instagram, TikTok, Reels, Shorts | `--hedef -14 --tepe -1.5` | `sosyal` (−15…−13 LUFS, ≤ −1 dBTP) |
| YouTube | `--hedef -14 --tepe -1.5` | `youtube` |
| Web, iş, mesajlaşma, konuşma ağırlıklı | `--hedef -16 --tepe -1.5` (varsayılan) | `web` (−17…−15) |

Instagram ve TikTok ses yüksekliği yayımlamaz; YouTube'un ~−14'ü topluluk ölçümü (araştırma). AAC tepeyi 0,1–0,4 dB
yükseltir; kodlamadan önce −1,5 (araştırma). `ustala` sınırlayıcısı gecikmesiz (0,000 ms), görüntüyü kopyalar, girdinin
üzerine yazmaz. LRA ve diğer eşikler: `teslim-denetimi`.

## 10. Tık onarımı
`medya denetle` `ses.tik` listesi verir (kesim anında yalıtık sıçrama; hi-hat tetiklemez) ama GEÇTİ'yi bozmaz.
- Ek yerindeyse sesi mikro geçişle yeniden üret. Ek yeri yoksa PCM'de, ustalıktan önce:
```
$PY $B/tik_onar.py --girdi calisma/ses/miks.wav --anlar 8.9 --cikti calisma/ses/miks-onarili.wav --json analiz/tik.json
```
  Fikstür: 0,5 ms +0,9 darbe → 25 örnek aradeğerlendi, gerçek tepe +0,9 → −3,1 dBTP, kalan örnekler bit bit aynı;
  davul vuruşunda "bulunamadı", basamakta "reddedildi".
- Sınırlayıcıya bırakma: tıkı ~4,7 dB bastırır, duyulur kalır, kazanç çöker (denetim dersi). AAC'den sonra onarılmaz:
  0,5 ms'lik tık kodlamadan sonra 892 örneğe yayıldı (ölçüldü).

## 11. Bitiş sırası
```
medya ustala calisma/ara.mov --hedef -14 --tepe -1.5 --cikti calisma/final-usta.mp4
medya meta-temizle calisma/final-usta.mp4 --cikti cikti/<ad>.mp4
medya denetle cikti/<ad>.mp4 --hedef sosyal [--plan plan/kurgu.json] [--muzik analiz/muzik.json]
medya yaziya-dok cikti/<ad>.mp4 --dil tr --cikti analiz/final-yazi.json
$PY $B/cer.py --metin analiz/konusma-yazi.json --yazi analiz/final-yazi.json --kapi miks
```
`meta-temizle` en son: `ustala`'nın yeniden sarması konum etiketlerini taşır. Fikstür: −14,0 LUFS / −2,1 dBTP, 553 kare,
`denetle` GEÇTİ, `miks` kapısı geçti (güven 0,980 → 0,991).
- `--muzik`: yalnız güven `yuksek` ve vuruşa kesim iddiası varken; kısaltıldıysa `analiz/muzik-kisa.json`. Yoksa verme
  (`senkron` `guvenilmez`/`kayik`/`kesim-yok` → `denetle` KALDI) ve raporda "vuruş iddiası yok" de.
- `av`: `kaynak_bas` < 0,5 sn çekimdeki sahte gecikme (500 − 1000·kaynak_bas ms) 2026-10-05'te düzeltildi (sınama
  `test_inceleme_bulgulari_cli_hatalari`); artık KALDI gerçek kaymadır. Yine de ölçülemeyen çekimi raporda yaz ve
  kullanıcıya o çekimin saniyelerini
  dinlet. Plan `kaynak`'ı asıl dosya kalsın: temizlenmiş + müzikli çıktıyla ilinti 0,95–0,97 ölçüldü.

## 12. Dinlemenin yerine geçenler
- Önce/sonra tayfı (önce üstte; Read ile bak). Mutlak tayf yorumlanmaz, karşılaştırılır (hyperframes-audio `references/diagnosis.md`):
```
ffmpeg -nostdin -v error -i once.wav -i sonra.wav -filter_complex "[0:a]showspectrumpic=s=900x260:legend=0:fscale=log:stop=12000[a];[1:a]showspectrumpic=s=900x260:legend=0:fscale=log:stop=12000[b];[a][b]vstack" -frames:v 1 analiz/tayf-ab.png
```
- `kisma.png`, `medya muzik` görselleri, betiklerin JSON'ları. Görsel bulgu sayıyla çelişirse "belirsiz" yaz.
- Kullanıcıya eşit düzeyli A/B (aynı 6–10 sn):
```
ffmpeg -nostdin -v error -ss 9 -t 6 -i calisma/ses/konusma-ham.wav calisma/ab-once.wav
medya ustala calisma/ab-once.wav --hedef -20 --tepe -2 --cikti cikti/dinleme/ab-once.wav
```
  Raporda dosya yolları ve dinlenecek saniyeler: en gürültülü yerler, kısma geçişleri, efekt anları, `cer.py`'nin
  değişen kelime anları.
