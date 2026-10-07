# Hazırlık: HDR→SDR, VFR, döndürme, HyperFrames son çizimi

Kanıt: `delivery-qa.md` (T0–T4, Kaçınılacaklar, Düzeltmeler), `video-framework.md` (render, disk), `sistem/dersler.md`.
Komutlardan önce `source /Users/onurkaya/Projects/video/ortam.sh`.

## Kaynak triyajı
`medya incele kaynak/* --json analiz/incele.json` → HDR (HLG/PQ/Dolby Vision), VFR, döndürme, 10 bit, GPS, ses
akışları. iPhone Dolby Vision 8.4 HLG tabanı olarak çözülür (RPU yok sayılır); SDR teslim için doğru girdi budur.
Birden çok ses akışı varsa dikkat: ffmpeg Apple APAC uzamsal sesi çözemez (9.0'a kadarki değişiklik günlüğünde yok;
orta güven); AAC stereo izini seç, yalnız APAC varsa AVFoundation (avconvert) ile çöz. `medya sdr` ve `medya cfr` bütün ses akışlarını alır (`-map 0:a?`); kodlarken `-map 0:a:0` ilk izi alır.

## HDR → SDR görünüm kararı (bir kez, sonra kilitli)
Ton eşleme bir zevk kararıdır, ölçüm değil. Sentetik HLG rampasında referans beyaz (8 bit Y): mobius 218, reinhard
209, hable 182 (HyperFrames `--sdr` = hable), Apple avconvert 148; ton eşlemesiz yeniden etiketleme 255'te kırpar.
ITU-R BT.2408 orta tonları korumayı ister → **varsayılan mobius** (`medya sdr` varsayılanı). Karar beklenmez: mobius
ile sürdür, A/B dosyalarını ve izlenecek anları raporda sun; kullanıcı başka yöntem seçerse yeniden çevir ve kodla.

3–4 temsilci klipte (gökyüzü/en parlak, cilt, doygun ışık, gece) 5 sn'lik A/B:
```
ffmpeg -nostdin -ss T -t 5 -i kaynak/X.MOV -map 0:v:0 -c copy calisma/ab/X-5sn.mov   # akış kopyası; HLG etiketi kalır
medya sdr calisma/ab/X-5sn.mov --yontem mobius --cikti calisma/ab/X-mobius.mp4
medya sdr calisma/ab/X-5sn.mov --yontem hable --cikti calisma/ab/X-hable.mp4
avconvert -s calisma/ab/X-5sn.mov -p PresetHighestQuality -o calisma/ab/X-apple.mp4   # isteğe bağlı Apple görünümü
medya kontak calisma/ab/X-mobius.mp4 --anlar 1,2.5,4 --cikti calisma/ab/X-mobius.png      # her aday için
```
Kullanıcı dosyaları izler ya da sayfalara bakar (gizlilik onayıyla); seçim (yoksa "mobius, varsayılan") `KARARLAR.md`'ye. Her HDR klip
(HyperFrames kompozisyonu da bu dosyaları kullanır; `--sdr` yalnız emniyettir ve hable eşler):
`medya sdr kaynak/X.MOV --yontem <seçilen> --cikti calisma/sdr/X.mp4` (libx264 CRF 16, bt709 etiketli).
- **HDR kaynağın temas sayfasına bakıp renk yargısı verme:** `medya kontak` yalnız ölçekler, ton eşlemez.
- avconvert: yalnız ön ayar (CRF/fps yok, VFR geçer, tek ses izi); karşılaştırma adayıdır, varsayılan değil.
- Bitmiş HDR usta da aynı yoldan: `medya sdr usta-hdr.mov --yontem <seçilen> --cikti calisma/usta.mp4`.
- Doğrulama: `medya incele <çıktı>` HDR uyarısı vermez (bt709); teslimde `uygunluk` luma satırı beyaz kırpık kare
  ≤ %2, ezik siyah ≤ %5 (gece sahnesi → bak), aralık dışı (YMIN < 16 / YMAX > 235) kare ≤ %1 (mobius rampada YMAX 239
verdi → bu satır mobius'un bilinen kusurunu yakalar); YAVG onaylanan A/B örneğinin ±10'u içinde.

## VFR → CFR, döndürme
- `medya incele` VFR uyarısı → `medya cfr X --fps 30` (gerçek kadans 60 ise 60). Doğrulama: `r_frame_rate` =
  `avg_frame_rate`. HyperFrames VFR kaynağı kendisi örnekler (r ile avg %10'dan fazla ayrılırsa); doğrudan ffmpeg
  montajı ise aynı fps/boyut/48 kHz ister.
- Döndürme: yeniden kodlama dönüşü kareye işler (ffmpeg otomatik). Akış kopyasında dönüş matrisini SIFIRLAMA:
  dikey klip yan oynar. Teslimde matris kalmamalı (`uygunluk` → donus).

## HyperFrames son çizimi (usta)
```
caffeinate -i hyperframes render calisma/kompozisyon --sdr --quality delivery --video-frame-format png \
  --frames-cache-dir off -o calisma/usta.mp4
```
- `--sdr` şart: varsayılan `auto` tek bir HLG/PQ kaynakta bütün MP4'ü BT.2020 HEVC Main10 yapar. Günlükte
  "[Render] SDR forced by --sdr flag" (ya da "No HDR sources detected") görülmeli. `--sdr` hable ile eşler; görünüm
  kararını kaynakları önceden `medya sdr` ile çevirerek ver.
- `--quality delivery` = CRF 15 slow (usta); taslak `--quality draft`. Varsayılan `looks` CRF 16'dır.
- `--video-frame-format png` gerçek çekimli **son** çizimde: VMAF 96,6 (JPEG ara kare 95,0; ffmpeg doğrudan 96,8),
  ~2 kat süre. Taslakta varsayılan yeter.
- **Disk tahmini önce:** 1080x1920 PNG ara kare ölçüldü (sentetik) 0,6 MB (az gren) – 4,0 MB (yoğun gren); JPEG 0,14–1,2 MB.
  Çekim saniyesi × fps × 4 MB × (G×Y)/(1080×1920) (4K ≈ 16 MB/kare: 60 sn 4K30 ≈ 29 GB), `df -h` boşluğu − 5 GB'a
  sığmalı (piksel ölçeklemesi tahmindir; 4K PNG ölçülmedi); `--frames-cache-dir off` kareleri çizim sonunda siler.
  Sığmıyorsa JPEG ile çiz ya da bölüm bölüm çiz (her bölüm sonra silinir) ve raporda yaz. Usta boyutu: CRF 16 grenli çekimde 74 Mb/s ölçüldü (4:48 → 2,5 GB);
  sığmazsa `--video-bitrate 20M` (dikey ön ayar tavanı).
- Fansız M2, 16 GB: çizim sırasında başka ağır iş (ML, kodlama) yok; her işçi ayrı Chrome (~256 MB).
- CLAUDE.md'deki yasaklı alt komutlar kullanılmaz (kanca engeller); `snapshot` daima `--describe false`.
- Usta denetimi: `medya incele calisma/usta.mp4` (h264, yuv420p, bt709, CFR). HyperFrames ustası `-bf 0` ve kaynak
  etiketleri taşır → teslim her zaman `kodla` (ya da en son `meta-temizle`) ile.
- ffmpeg ile kurgulanmış usta (HyperFrames'siz): SDR, CFR, bt709 etiketli, CRF 14–16.
