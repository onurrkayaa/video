# Denetim kapısı: eşikler, düzeltme planı, bağımsız denetim, rapor

Kanıt: `medya/komutlar/denetle.py` (kod), `delivery-qa.md` (QC1–QC11), `sistem/dersler.md`, bu becerinin fikstür
sınamaları (2026-10-05). Önce `source /Users/onurkaya/Projects/video/ortam.sh; P=$MEDYA/.venv/bin/python;
T=$MEDYA/sistem/claude/skills/teslim-denetimi/scripts/teslim.py`. Raporlar `cikti/denetim/` altına.

## `medya denetle` — neyi KALDIRIR, neyi yalnız yazar
| Satır | ✗ (çıkış 1) | yalnız bulgu (✓ satırında; oku) |
|---|---|---|
| teknik | HDR etiketi; `--boyut`/`--fps` (±0,01)/`--sure` (±0,1 sn) uyuşmazlığı; moov sonda (web/sosyal/youtube) | yuv420p değil; "renk etiketleri boş" (ffprobe `color_primaries`/`color_transfer` boş; 2026-10-05'te yanlış alarm hatası düzeltildi, sınama var) |
| siyah | baş/sondan 0,6 sn içeride siyah | baş/son kararması |
| donma | — | her donma (bilinçli duraklama olabilir) |
| flas | 1–2 karelik flaş (kare kare histogram; ffmpeg sahne puanı göremez) | — |
| ses | LUFS aralık dışı (web -17…-15, sosyal/youtube -15…-13, arsiv -24…-12); gerçek tepe > -1,0 dBTP; > 10 kırpık örnek; ses akışı yok | kesimde tık; içeride ≥ 1,5 sn sessizlik |
| senkron (`--muzik`) | karar `vurusta` değil (p90 ≤ 40 ms, en büyük ≤ 70 ms; güven düşükse `guvenilmez`) | — |
| av (`--plan`, `"ses": "kendi"` çekimler) | \|gecikme\| > 45 ms ya da ilinti < 0,5 | — |
| meta | GPS/konum etiketi | — |

Varsayılan `--hedef web`'dir: sosyal teslimi `--hedef`siz denetlemek -14 LUFS'u yanlışlıkla KALDIRIR. Bilerek sessiz teslimde
(GIF, döngü, yükleniyor) `--sessiz` ver: "ses akışı yok" kusur sayılmaz; raporda belirt. Temas sayfası (40 kare) JSON'un yanına yazılır.

## `teslim.py uygunluk` — `denetle`nin bakmadıkları
| Satır | kaldi | inceleme / ölçülemedi |
|---|---|---|
| akislar | 1 video + ≤ 1 ses dışında iz (mebx, APAC, veri) | ses yok |
| kodek, seviye, pix_fmt, boyut | ön ayardan farklı; H.264 seviyesi kare/fps'in gerektirdiğinden yüksek | — |
| sar, cfr, renk, donus, alan | SAR ≠ 1:1; r ≠ avg fps; bt709×3+tv değil (hdr: bt2020/arib-std-b67/bt2020nc); dönüş matrisi; geçmeli | — |
| ses_bicimi | AAC-LC stereo değil | 48 kHz değil |
| av_baslangic, av_sure | > 1 kare; > 50 ms | — |
| gop | — | ön ayardan uzun (dikey/youtube 0,5 sn, diğer 2 sn) |
| faststart, dosya_boyutu | moov mdat'tan sonra; `--mb` aşıldı (`kodla` bir kez kendisi yeniden dener; yine ✗ ise `--mb`'yi ~%5 düşür, yeni adla kodla) | — |
| ust_veri | izinli dışı etiket (konum, cihaz, tarih, yorum, `hyperframes_*`), bayt izi (ISO6709, com.apple.quicktime, hyperframes), exiftool kişisel satırı | — |
| cozme | çözme hatası satırı | — |
| luma (SDR) | — | beyaz kırpık kare > %2, ezik siyah > %5 (gece/bilinçli beyaz olabilir), aralık dışı (YMIN < 16 / YMAX > 235; 480 px'te) kare > %1 |
| `--usta`: ses_kaymasi | \|gecikme\| > 5 ms ya da pencereler arası yayılım > 2 ms | ilinti < 0,5 → ölçülemedi |
| `--usta`: kare_sayisi, kare_kaymasi | sayı farklı; kayma ≠ 0 kare | fps farklı / durağan görüntü |
| `--vmaf` (yalnız hizalı) | — | yükleme ve `kucuk` kopyası ort < 93 ya da en az < 85; WhatsApp telefon modeli ort < 80 |

Fikstürde doğrulandı: temiz kodlamalar geçti; 1 kare kaydırılmış kopyada ses -33,3 ms ve kare -1 yakalandı (hizasız
VMAF 57,9 olurdu → hesaplanmaz); `ustala` çıktısında konum + `hyperframes` yorum etiketi yakalandı; `meta-temizle`
çıktısı üst veriden geçti; `creation_time` ve `com.apple.quicktime.make` yakalandı. Eşikler sentetik ölçümle
kalibredir: `inceleme` = bak ve raporla, otomatik ✗ değil. VMAF HDR'ye karşı SDR'de geçersiz; ffmpeg 6.0'da
`phone_model=1` sessizce yok sayılır (betik `enable_transform` kullanır).

## Kesim anlarında temas sayfası
```
F=$($MEDYA/arac/ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of csv=p=0 cikti/X.mp4)   # ör. 30/1
A=$($P -c "import json,sys;from fractions import Fraction as Fr;d=json.load(open(sys.argv[1]));f=float(Fr(sys.argv[2]));print(','.join(f'{t-1/f:.3f},{t:.3f}' for t in d['denetimler']['kesimler']['anlar']))" cikti/denetim/X-denetim.json "$F")
medya kontak cikti/X.mp4 --anlar "$A" --cikti cikti/denetim/X-kesimler.png
```
Her kesim için önceki son kare + yeni ilk kare (`kontak` ekrandaki kareyi alır). Plan varsa kesimler `cikti_bas`.
Read ile açmak gizlilik onayı ister; yalnız sayısal modda açma, anları kullanıcıya izlemesi için yaz.
Bak: boş/siyah/yabancı kare, zıplama, kadraj dışı yüz, renk sıçraması, istenmeyen yazı, ağır çekim yırtılması.

## A/V senkron ve ses yüksekliği
- Duran: `uygunluk` av_baslangic/av_sure. Ustaya göre: `--usta` (aynı kurgu kanıtı). Çekim sesi: `denetle --plan`.
  Müzik: `medya senkron X --muzik analiz/muzik.json --plan plan/kurgu.json`.
- AAC ~21 ms ön dolgu taşır: senkron ölçümünde sesi daima ffmpeg ile çöz (düzenleme listesini uygular);
  `medya ustala` çıktısı 0,000 ms kayma ölçüldü.
- Ses yüksekliği KODLANMIŞ dosyada ölçülür. AAC gerçek tepeyi yükseltir (-1,78 → aac_at 256k -1,7, aac 256k -1,6,
  aac_at 128k -1,4 dBTP): ≥ 192k için `--tepe -1.5`, ≤ 128k için `--tepe -2.0`. Müzik ağırlıklı sosyal -14,
  konuşma ağırlıklı / web -16 LUFS.

## Düzeltme planı (bağımsız denetimin kusurlu fikstür planı; sırayla)
1. **Tek karelik flaş/siyah** → önceki karenin kopyası. Kök neden kompozisyondaysa orada düzelt, yeniden çiz.
   Bitmiş ustada (N = round(t × fps)):
   `ffmpeg -nostdin -i calisma/usta.mp4 -filter_complex "[0:v]split[a][b];[a][b]freezeframes=first=N:last=N:replace=N-1[v]" -map "[v]" -map 0:a:0 -c:v libx264 -preset slow -crf 14 -c:a copy calisma/usta-duz.mp4`
   (fikstürde: flaş ✓, kare sayısı 600 = 600). Kareyi SİLME: sonraki her kesim 1 kare kayar.
2. **Kesimdeki tık** → `ses-tasarimi` (`ustala`dan önce; sınırlayıcı tıkı yalnız ~4,7 dB bastırır).
3. `medya ustala` doğru `--hedef/--tepe` ile. 4. `kodla` ya da en son `medya meta-temizle` (`ustala` konum
   etiketini korur; `meta-temizle` siler ve moov'u başa alır). 5. `medya denetle --hedef …` + `uygunluk` yeniden.

## Bağımsız denetim
`Workflow({scriptPath: '/Users/onurkaya/Projects/video/.claude/workflows/medya-denetim.js', args: {cikti: 'projeler/…/cikti/X.mp4', proje: 'projeler/…', hedef: 'sosyal', brief: '1080x1920 30p SDR, yazı yok, -14 LUFS'}})`
— üç mercek (teknik-ses, görsel-brief, senkron-iddia) + karar; `hedef` ∈ web|sosyal|youtube|arsiv. KALDI → düzelt,
yeniden çalıştır (`medya-uretim` en çok 2 tur yapar). Her ayrı kurgu/en-boy için bir kez; aynı ustanın yeniden
kodlaması için `uygunluk --usta` (0 kare, ≤ 5 ms) aynı kurguyu ölçer. Yalnız sayısal modda `brief`e "YALNIZ SAYISAL
MOD: hiçbir kare/PNG Read ile açılmaz" yaz (görsel mercek temas sayfası açar). Denetçi (`medya-denetci`) salt okunurdur:
`kodla` çalıştırmaz; `denetle`, `uygunluk`, `guvenli`, `kontak` rapor dosyaları yazabilir.

## Ölçülemeyenler — nasıl yazılır
"Ölçülemedi: <ne> — <dk:sn> anlarını izle/dinle." Liste: hareketin akıcılığı (örnek kareler arası), sesin kulağa
gelişi ve miks dengesi, platformun yeniden sıkıştırması (kullanıcı kendine gönderip dosyayı geri verirse `incele` +
`uygunluk` ile ölçülür), HDR ekranda görünüm, QuickTime/iPhone'un bt709'u biraz açık göstermesi (düşük güven),
ışığa duyarlılık (WCAG 2.3.1 sayacı yok; `denetle` flaşı WCAG değildir), müzik hakları / Content ID, uygulama içi
güncel sınırlar. İzlenecek anlar: kesimler, geçişler, en parlak/HDR çekim, uyarılı anlar (donma, tık, sessizlik),
ilk ve son 2 sn. İnceleme taslağı gerekirse `medya zamankodu X` (köşede dk:sn.kare; teslim değil).

## Rapor şablonu (Türkçe)
```
Teslim dosyaları
| Dosya | MB | Boyut, fps | Süre | LUFS / dBTP | denetle | uygunluk |

Ölçülenler: <sayılarla: senkron p90/en büyük, VMAF, av ms, kırpık kare %>
Bakılanlar: <açılan PNG yolları> | "Yalnız sayısal mod: kare açılmadı"
Ölçülemeyenler ve izlemen gereken anlar: <madde: ne — dk:sn>
Kararlar: ton eşleme <mobius…>, ses hedefi <-14/-1.5>, varsayımlar; doğrulanmamış platform sınırları
Yükleme: WhatsApp kalite için Belge; AirDrop dosyayı değiştirmez
```
