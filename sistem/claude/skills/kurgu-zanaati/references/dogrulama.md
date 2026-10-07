# Doğrulama — amatör izleri ve ölçümleri

Claude videoyu gerçek zamanlı izleyemez, sesi duyamaz. Her kalite cümlesi bir sayıya ya da Read ile açılmış bir PNG'ye
dayanır; gerisi "doğrulanamadı" + kullanıcının izleyeceği saniyeler. Kişisel klipte kare açmak izne bağlı (yalnız
sayısal modda PNG açılmaz). Proje kökünden, `source $MEDYA/ortam.sh` sonrası; `X` = çizim.

## Sıra
1. Çizimden önce: `$P $K/plan_denetle.py plan/kurgu.json` → GEÇTİ; `--html calisma/kompozisyon/index.html` → GEÇTİ.
2. `hyperframes lint` 0 hata, `hyperframes check … --at-transitions` hatasız, `snapshot --describe false` geçiş/punch tepelerinde.
3. Taslak çizim → aşağıdaki ölçümler → `medya zamankodu X --cikti calisma/X-tc.mp4` kullanıcıya (geri bildirim
   "dk:sn.kare → not"; teslim değil).
4. Son çizim + bitirme (görüntü düzeltmesi → ses onarımı → `medya ustala` → `medya meta-temizle` en son) →
   `medya denetle … --json cikti/denetim/X-denetim.json` → `$P $K/plan_denetle.py plan/kurgu.json --denetim cikti/denetim/X-denetim.json`.

## Ölçümler
| Amatör izi | Ölçüm (geçer) |
|---|---|
| Geç/kayan kesim | Güven `yuksek`: (a) `medya senkron X --muzik analiz/muzik.json --plan plan/kurgu.json` → `vurusta` (planlanan; tek başına çizimi kanıtlamaz); (b) `plan_denetle --denetim` → planlı sert kesimlerin hepsi çizimde ±1 karede; (c) plansız `medya senkron X --muzik analiz/muzik.json --json analiz/senkron-cizim.json` → `kesimler[]` (`t`, `sapma_ms`)'den yalnız planda `vurusa: true` kesimlere (±1 kare) denk gelenlerin `sapma_ms`'i p90 ≤ 40, en büyük ≤ 70. Plansız ölçüm erime/dip/flaş sınırlarını ve `vurusa: false` kesimleri de sayar: plansız karar `vurusta` şartı yalnız bütün kesimler `vurusa: true` ise. Güven yüksek değilse: "vuruş iddiası yok" yaz |
| Kesim planda değil / planlı kesim yok | `plan_denetle --denetim`: planlı sert kesimler ±1 karede bulundu; plansız kesim yok |
| Metronom ritim, her kesimde başka geçiş, aşırı ağır çekim, > 3 flaş/sn | `plan_denetle` uyarıları |
| Kesimde kötü kare (göz kapalı, boş an), benzer iki çekim yan yana | `medya kontak X --anlar <kesimler> --genislik 360 --cikti analiz/kesimler.png` → Read |
| Ağır çekim takılıyor (yinelenen kare) | `$P $K/yinelenen.py X --bas A --sure S` (A,S = yavaş aralık, geçiş dışında) → ≤ %3. `mpdecimate` varsayılanı yavaş harekette yanlış alarm verir |
| Ara kare "jöle" (el, saç, su) | En hızlı hareket anlarında `medya kontak calisma/klipler/<yavas> --anlar …` → Read |
| Dikeyde siyah kenar | `arac/ffmpeg -nostdin -i X -an -vf "cropdetect=limit=0.08:round=2:reset=1,metadata=print:key=lavfi.cropdetect.w:file=-" -f null - 2>/dev/null \| grep -o "w=[0-9]*" \| sort \| uniq -c` → yalnız çıktı genişliği |
| İstenmemiş siyah | `arac/ffmpeg -nostdin -i X -an -vf blackdetect=d=0.03:pix_th=0.08 -f null - 2>&1 \| grep black_start` → yalnız planlı dipler |
| Komşu çekimde pozlama/renk sıçraması | Her çekimin ortasında 1 sn: `arac/ffmpeg -nostdin -v error -ss T -t 1 -i X -an -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null -` (UAVG/VAVG aynı) → sahne içinde yakın; + kontak |
| Titrek seçki / sabitleme işe yaramadı | `titreme.py` önce/sonra (≥ %50 düşüş) |
| Zoomda yumuşama | `plan_denetle` ölçek ⚠ yok (cover × punch ≤ 1,15; sabitlemede × 1+Z/100, elle); punch tepesinde ve öncesinde snapshot → Read |
| İstenmeyen yazı | `plan_denetle --html` (ekran yazısı uyarısı); BRIEF'te istenmediyse kaldır |
| Yüz platform arayüzü altında | `teslim-denetimi` güvenli alan sayfası |
| Kesimde tık, ses düzeyi, müzik cümle ortasında bitiyor | `medya denetle` ses satırları; onarım `ses-tasarimi` |

## Tek karelik flaş/siyah kare
Silme (sonraki her kesim 1 kare kayar, senkron bozulur). Önce planda nedenini düzelt (boşluk, kısa klip, yanlış
`data-media-start`) ve yeniden çiz. Çizilmiş dosyada N. kare, N−1'in kopyası olur (kare sayısı korunur; sınandı):
```sh
arac/ffmpeg -nostdin -v error -i X -filter_complex "[0:v]split[a][b];[a][b]freezeframes=first=N:last=N:replace=N-1[v]" -map "[v]" -map 0:a -c:a copy -c:v libx264 -crf 12 calisma/X-onarim.mp4
```

## Raporda
Dosya yolları; ölçülenler sayılarla (senkron kararı ve ms ya da "güven yüksek değil, vuruş iddiası yok"; denetle
sonucu); açılan PNG'ler ya da "yalnız sayısal mod"; ölçülemeyenler: duygusal etki, akış hissi, ağır çekimin
doğallığı, sesin kulağa gelişi → izlenecek saniyeler (geçişler, ağır çekimler, açılış, bitiş). "Mükemmel" yok.
