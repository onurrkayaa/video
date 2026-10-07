---
name: gorsel-uretim
description: Use when a task makes or edits still images - photos, product shots, posters, covers/thumbnails, collages, Instagram square/story exports, background removal, upscaling old photos, object removal, a color look on photos, HEIC/RAW, logo vectorizing, depth for parallax, or removing photo location data (görsel, fotoğraf, afiş, kapak, kolaj, arka plan sil, büyüt, renk görünümü, konum sil).
---

# Görsel üretim ve fotoğraf

Yerel, ticari güvenli, ölçülerek. **İlke:** önce var olan yetenek ve betik; gerçek pikseller korunur (ürün ve yüz
yeniden çizilmez); her iddia bir ölçüme ya da Read ile açılmış sayfaya dayanır. Proje: `medya proje yeni "<ad>" --tur gorsel --kaynak …`;
her biçim aynı ustadan (`disa_aktar.py`). Her kabukta:
`source /Users/onurkaya/Projects/video/ortam.sh; G=$MEDYA/sistem/claude/skills/gorsel-uretim/scripts; PY=$MEDYA/.venv/bin/python`

## Ne zaman / ne zaman değil
- **Ne zaman:** düzenleme, kesik, büyütme, nesne silme, görünüm, kolaj, afiş, kapak, sosyal boyut, vektör, derinlik.
- **Değil:** video kurgusu `kurgu-zanaati`; hareket, paralaks animasyonu `hareket-tasarimi`; ses `ses-tasarimi`;
  video teslimi `teslim-denetimi`; yeni araç `arac-radari`.

## Yalnız bunları sor
- **Gizlilik:** kişisel fotoğrafta kare açmadan sor; istemezse yalnız sayısal mod (`olc.py`, `medya analiz`; kullanıcı bakar).
- İş mi kişisel mi (lisans); yazı hangi görselde ve metni ne (uydurma); hedef boyutlar.
- Herkese açık mı → görüntüdeki kişilerin rızasını hatırlat. Konum silmede: tarih/kamera da gider, asıllar GPS'i tutar (§13).
- Üretim: `medya gorsel-uret "<istem>" --cikti x.png [--referans ürün.png]` (FLUX.2 klein, Apache-2.0; tohum sabit = aynı görsel). Afiş metnini kullanıcı verir.

## Hızlı başvuru
| İş | Yol | Kanıt |
|---|---|---|
| Çalışma kopyası (HEIC/RAW/P3, yön) | `$PY $G/disa_aktar.py X --asil --cikti calisma/gorsel/x.png` | `olc.py` |
| Arka plan sil | `medya arkaplan-sil` → `kenar_arindir.py` | `olc.py` alfa + `kontak.py --zemin hepsi` |
| Büyüt | Lanczos; gerekirse Real-ESRGAN (kurulum) | `olc.py --referans` ≥ 30 dB / 0,90 |
| Nesne sil | `lama_sil.py` (kurulum) | `olc.py --referans --maske` → 0 piksel |
| Renk görünümü | `gorunum.py` → `ffmpeg lut3d` | `olc.py` `lab_ort`, kırpık % |
| Kolaj | `kolaj.py --duzen` | uyarılar + sayfa |
| Sosyal boyut | `disa_aktar.py --hazir ig-kare/ig-dikey/ig-hikaye --analiz a.json` | `olc.py --teslim --boyut` |
| Kapak / en iyi kare | `medya analiz` + `medya kontak --anlar` | sayfa |
| Afiş (yazı istendiyse) | HyperFrames HTML → `render --format png-sequence --fps 1` | `tesseract -l tur+eng` |
| Konum sil | `medya meta-temizle` (yeniden kodlamaz) | `exiftool -location:all` boş |

Komutlar ve sınırlar: [teknikler](references/teknikler.md); kurulumlar, lisanslar, kaçınılacaklar: [araçlar](references/araclar.md).

## Kurallar
1. Yeni `medya`/Swift komutu, kayıt satırı yazma; eksik yetenek `arac-radari` ile.
2. Apple süper çözünürlüğü önerme (sınandı: bikübikten kötü PSNR, alfa 0).
3. Yalnız ticari güvenli: rembg'de model adı hep açık (`birefnet-general-lite`; varsayılan bria NC). CodeFormer,
   GFPGAN, UltraSharp, FLUX.1-dev/klein-9B, SD3.5, Depth Anything Base/Large, ücretli bulut yok. Kurulumda boyut +
   lisans söyle, onay al, `KARARLAR.md`'ye yaz (tek seferlik); kalıcısı `arac-radari`.
4. Model yazı çizmez; yazı HTML'de, `<html lang="tr">`. Yazı yalnız istenen görselde.
5. Asıllar `medya proje yeni --kaynak` ile salt okunur; betikler var olan çıktıyı ezmez (`--uzerine`; kullanıcı dosyasıysa sor).
6. `medya analiz` yönü uygulamaz → analiz ve kırpma yönü pişmiş kopyada. ANE takılıysa kullanıcı
   `sudo killall ANECompilerService` çalıştırsın; elle `--merkez` ile yüzlü kırpımı kullanıcı kontrol eder.
7. Ağır işler (BiRefNet, LaMa, üretici, HyperFrames) sırayla (16 GB).
8. Kolaj/seri: önce aynı `.cube`, sonra yerleşim; boşluk eşit; süs, yazı yok.

## Doğrulama (bitti demeden)
1. `$PY $G/olc.py cikti/*.jpg --teslim --en-cok-mb 8 --json analiz/olcum.json` → hepsi geçer (sRGB ICC, GPS/EXIF/XMP
   yok, 4:4:4); her biçim için `--boyut` ayrı.
2. Kesik: 1 parça, 0 delik, kirli alfa ≈ 0; büyütme: geri izdüşüm eşiği; nesne silme: maske dışı 0 piksel.
3. Görünüm: kırpık piksel artmamış; `lab_ort` raporlanır (sayısal modda ön düzeltme yok, §4).
4. Afiş: OCR beklenen metinle birebir; hikâyede `kontak.py --guvenli dikey`.
5. İzin varsa Read: `kontak.py` sayfaları (teslimler, kenar 3 zemin, %100 kırpıntı).
6. `medya-denetim` geçmeden "bitti" yok; `brief`: "DURAĞAN GÖRSEL: `medya denetle`/`kontak` kullanma (yanlış KALDI /
   çöker); ölçüm `gorsel-uretim/scripts/olc.py --teslim --boyut`, `kontak.py`, afişte tesseract".

**Ölçülemez (raporda yaz):** beğeni, marka uyumu, Instagram'ın yeniden sıkıştırması ve ölçülerinin güncelliği.

## Sık hatalar
- `sips -g profile` ICC yokken de sRGB der → `olc.py`.
- HyperFrames PNG'si ICC'siz → `disa_aktar.py`.
- Büyütme aslın tam katı değil ya da `--referans` IG kırpımından sonra.
- P3 kopyaya LUT (ffmpeg ICC'yi taşır) → önce `disa_aktar.py --asil`.
- Kesiği tek zeminde görmek (hale koyuda çıkar).

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/image-photo.md` (+ footage-analysis.md); eskidiyse `arac-radari`.
