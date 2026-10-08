# Araçlar: kurulu olanlar, isteğe bağlı kurulumlar, kaçınılacaklar

Ölçümler bu Mac'te (M2, 16 GB, macOS 27) 2026-10-05'te, Apple örnek görselleri (`/Library/User Pictures`, 512 px)
ve sentetik fikstürlerle yapıldı. Stüdyo kökünde, `source /Users/onurkaya/Projects/video/ortam.sh` sonrası:
`G=$MEDYA/sistem/claude/skills/gorsel-uretim/scripts`, `PY=$MEDYA/.venv/bin/python`.

## Kurulu (indirme yok)

| Araç | Ne için | Ölçülen davranış |
|---|---|---|
| `medya arkaplan-sil X [--kirp] [--maske] [--cikti Y.png]` | Apple Vision ön plan maskesi → RGBA PNG | EXIF yönünü uygular, P3'ü sRGB'ye çevirir, GPS yazmaz; 512 px'te 0,3 sn. Papağanda 1 parça 0 delik, kenarda eski zeminin rengi (hale; `kenar_arindir.py` %1 kirli alfayı 0'a indirdi); gitarda 5 parça 13 delik (desenli plaka delindi). Saç/ince kenarda BiRefNet'e karşı **ölçülmedi** |
| `medya analiz X --cikti Y.json` | estetik (-1..1), yüz + yakalama kalitesi, ilgi kutusu, etiketler | Kutular [x,y,g,y], 0..1, sol-üst köken. **Resimde EXIF yönünü uygulamaz** (yön 6'lı JPEG'de ölçüldü) → önce `disa_aktar.py --asil` |
| `medya meta-temizle X --cikti Y` | yeniden kodlamadan üst veri silme | ExifTool `-all=` + yön ve ICC geri yazılır; GPS/marka gitti, yön ve Display P3 kaldı (ölçüldü); pikseller birebir |
| `medya incele X` | künye | Resimde boyut (saklanan yönde), çekim tarihi, cihaz, GPS uyarısı |
| `medya kontak V` | **yalnız video** | Durağan görsel için `$G/kontak.py` |
| `sips` | HEIC ve RAW çözme (Apple), ICC dönüştürme (`-m`), küçültme (`-Z`) | `sips -g profile` ICC'siz dosyada da "sRGB IEC61966-2.1" der (ölçüldü): ICC'yi `olc.py` ya da `arac/exiftool -ICC_Profile:ProfileDescription` ile oku |
| Pillow 12.3 + numpy (`.venv`) | düzenleme, ICC (ImageCms), betikler | ImageMagick yok (Homebrew kilitli) |
| `arac/ffmpeg` 6.0 `lut3d` | `.cube` uygulama (fotoğraf ve video aynı) | `gorunum.py` kimlik LUT'u en çok 1 düzey fark (ölçüldü); girdinin ICC etiketini PNG çıktısına taşır (ölçüldü) → P3 kopyada LUT sRGB sanılır ama etiket P3 kalır: LUT'u yalnız `disa_aktar.py --asil` ile üretilmiş sRGB kopyaya uygula; teslimde yine `disa_aktar.py` |
| `tesseract` 5.5.3 (`eng`, `tur`; önceden kurulu Homebrew şişesi) | yazı denetimi | `tesseract X - -l tur+eng --psm 6` HyperFrames afişinde "İĞNE ŞIK IŞIL İSTANBUL"u birebir okudu |
| `hyperframes render D --format png-sequence --fps 1 -o K` | yazılı afiş tek kare | `data-duration="1" data-fps="1"` → 1 PNG, 0,7 sn; **ICC yok** → `disa_aktar.py` |

Apple ML komutları (`analiz`, `arkaplan-sil`) Neural Engine derleyicisi takılıysa hemen düşer ve çözümü yazar
(`sudo killall ANECompilerService` — kullanıcı çalıştırır). Bu sırada asılı kalıp beklemeyin: kullanıcıdan killall'ı isteyin. Beklenemiyorsa
elle maske, `disa_aktar.py --merkez x,y`, `kolaj.py --merkez x,y …` ile sürdürün ve raporda yazın. Yüzlü kolaj/kırpım
analizsiz (elle merkezle) teslim edilmez; edilecekse hücreleri kullanıcı kontrol eder (sayısal modda özellikle).

### Üretici (kurulu): `medya gorsel-uret` — FLUX.2 [klein] ve Z-Image-Turbo
Kayıt `yetenekler.toml` (`flux2-klein` birincil, `z-image-turbo` yedek); iki modelin ağırlığı da Apache-2.0, mflux
0.21.0 (MIT), stüdyonun Python 3.13.16'sı, ağsız çalışır. Model klasörleri sabit commit'te (yerel anlık görüntü yolu).
```zsh
medya gorsel-uret "<istem>" --cikti calisma/gorsel/k1.png --adet 3 --tohum 11          # varsayılan: flux2
medya gorsel-uret "<istem>" --cikti calisma/gorsel/afis.png --model z-image --tohum 11   # görselde İngilizce yazı
medya gorsel-uret "<istem>" --cikti calisma/gorsel/sahne.png --referans calisma/gorsel/urun.png   # düzenleme: hep flux2
```
| A/B 2026-10-08 (1024², aynı 3 istem × 2 tohum, `--low-ram`) | FLUX.2 [klein] 4B Q4 (`flux2`) | Z-Image-Turbo 6B Q4 (`z-image`) |
|---|---|---|
| model, adım | 4,62 GB (794cd15), 4 | 5,90 GB (f427e25), 9 |
| süre | 83–107 sn | 275–383 sn (3,3–3,7 kat) |
| bellek tepesi (`time -l` peak memory footprint) | 9,0–10,8 GB | 6,3 GB |
| İngilizce afiş yazısı | 0/2 afiş doğru ("SUM MER", "MUIC", "NIGHT"); OCR 6/12 kelime | 2/2 afiş harfi harfine doğru; OCR 10/12 kelime |
| istem etiketi (Vision) / estetik ort (Apple) | aynı / 0,61 | aynı / 0,65 |
| düzenleme (`--referans`) | var (~176 sn) | yok (Z-Image-Edit yayımlanmadı) |
- Seçim: konsept taraması ve düzenleme `flux2` (varsayılan); görselde İngilizce yazı ya da bellek darsa `--model
  z-image` (~3,5 kat süre). Fotogerçekçilik farkı ölçülmedi: görseller `sistem/devam/ham/gorsel-ab/`, kullanıcı bakar.
  Kural 4 değişmedi: teslim edilen yazı HTML'de; Türkçe harf modele çizdirilmez.
- Aynı model + istem + tohum = piksel piksel aynı görsel (iki model; `medya test gorsel --agir`). Varsayılan adım
  sayıları damıtıldıkları sayı (`--adim` verilmezse flux2 4, z-image 9). Olumsuz istem yok (klein'da bayrak yok,
  yönlendirmesiz Z-Image `--negative-prompt`'u yok sayar) → istemi olumlu yaz.
- Sürekli üretimde ısıl kısılma (fansız M2): 44 dk'lık A/B'de süre ilk koşudan sonuncuya %28,6 (flux2) ve %39,5 (z-image) uzadı.
- mflux'ı doğrudan çağırma: `--model` verilmezse upstream depo iner (FLUX.2 23,7 GB, Z-Image ~33 GB); `medya
  gorsel-uret` sabit sürümlü yerel kopyayı kullanır, yanına istem/tohum/sağlayıcı/lisans kaydı (`.json`) yazar.
- Ortam paketleri kısıt dosyasına sabit (2026-10-08): taşımadan önce/sonra aynı tohum piksel piksel aynı çıktı.
  `uv tool upgrade` yapma; paket değişecekse kısıt dosyasını yenile ve `medya test gorsel --agir` koş (aynı tohum
  başka görsel verebilir).

## İsteğe bağlı kurulumlar: önce boyut ve lisansı söyle, onay al

Hepsi 2026-10-05'te geçici bir klasöre kurulup bu Mac'te çalıştırıldı; stüdyoya kurulmadı.
Bir iş için **tek seferlik** kullanım: kullanıcı onayıyla aşağıdaki yollara (`arac/`, `ortamlar/gorsel`, `modeller/`)
kurulabilir; ne kurulduğu, boyutu ve lisansı projenin `KARARLAR.md`'sine yazılır. Kalıcı benimseme (kayıt satırı,
`medya kur`, sınama) yalnız `arac-radari` becerisiyle.

### Görsel Python ortamı `ortamlar/gorsel` (372 MB, ölçüldü)
```zsh
arac/uv venv --python 3.12 ortamlar/gorsel && arac/uv pip install --python ortamlar/gorsel/bin/python 'rembg[cpu]==2.0.85' 'onnxruntime==1.30.0' 'rawpy==0.27.1' 'vtracer==0.6.15'
ortamlar/gorsel/bin/python -c 'import rembg, onnxruntime, rawpy, vtracer'      # kontrol
```
Lisans: rembg MIT, onnxruntime MIT, rawpy MIT (LibRaw LGPL-2.1/CDDL), vtracer MIT. `rembg[cli]` kurma (gradio
analitiği). onnxruntime 1.30 kapanışta ara sıra `libc++abi … recursive_mutex lock failed` ile çöker (çıktılar
yazılmıştı): betikler `os._exit` ile çıkar; satır içi kodda da en sona `os._exit(0)`.

### rembg + BiRefNet-general-lite (model 224 MB, MIT): zor kenar ve ürün için ikinci görüş
```zsh
REMBG_HOME=$MEDYA/modeller/rembg ortamlar/gorsel/bin/python -c "
import os, sys
from rembg import new_session, remove
from PIL import Image
s = new_session('birefnet-general-lite', providers=['CPUExecutionProvider'])
remove(Image.open('calisma/gorsel/urun.png'), session=s).save('calisma/gorsel/urun-birefnet.png')
sys.stdout.flush(); os._exit(0)"
$PY $G/kenar_arindir.py calisma/gorsel/urun-birefnet.png --cikti calisma/gorsel/urun-birefnet-temiz.png
```
- Model adını **her zaman** ver: `new_session()` varsayılanı `bria-rmbg` (RMBG-2.0, CC BY-NC): iş için yasak, sessizce ~1 GB indirir.
- `post_process_mask=True` kullanma: alfa ikiliye döner, kenar testere olur. Ham çıktıda kirli alfa var → `kenar_arindir.py`.
- Ölçüm (model içeride 1024²): oturum 16 sn, görsel başına 23–40 sn, tepe RSS 4,6 GB → tek başına çalıştır.
  `CoreMLExecutionProvider` 10 dakikada oturum açamadı: kullanma.
- Gitarda plakayı korudu (1 parça) ama alt kenardan parça kesti: iki yolu `olc.py` + 3 zeminde karşılaştır.

### Real-ESRGAN ncnn (58 MB; kod MIT, `realesrgan-x4plus` ağırlığı BSD-3)
```zsh
curl -fL -o /tmp/re.zip https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip && [ "$(shasum -a 256 /tmp/re.zip | cut -d' ' -f1)" = e0ad05580abfeb25f8d8fb55aaf7bedf552c375b5b4d9bd3c8d59764d2cc333a ] && mkdir -p arac/realesrgan && unzip -q /tmp/re.zip realesrgan-ncnn-vulkan 'models/realesrgan-x4plus.*' -d arac/realesrgan && chmod +x arac/realesrgan/realesrgan-ncnn-vulkan && rm /tmp/re.zip
test -x arac/realesrgan/realesrgan-ncnn-vulkan                                   # kontrol (-h 255 ile çıkar)
arac/realesrgan/realesrgan-ncnn-vulkan -i girdi.png -o cikti-x4.png -n realesrgan-x4plus -s 4 -t 256 -f png -m arac/realesrgan/models
```
- SHA-256 ilk indirmede kaydedildi (yayında sağlama yok). Evrensel ikili: mimariyi `file` ile bak (`lipo` Xcode
  lisansı yüzünden hata verir). Girdi yalnız jpg/png/webp. `-n` şart: varsayılan model anime.
- 512²→2048² 8 sn, tepe bellek 2,1 GB. Araştırmanın önerdiği yeni koşucu upscayl-bin (AGPL, tek başına CLI) ve
  sıkıştırma hasarı için Helaman modelleri (CC-BY-4.0: atıf gerekir) burada **denenmedi**.

### LaMa ONNX (208 MB, Apache-2.0): nesne silme
```zsh
mkdir -p modeller/lama && curl -fL -o modeller/lama/lama_fp32.onnx https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx && [ "$(shasum -a 256 modeller/lama/lama_fp32.onnx | cut -d' ' -f1)" = 1faef5301d78db7dda502fe59966957ec4b79dd64e16f03ed96913c7a4eb68d6 ]
ortamlar/gorsel/bin/python $G/lama_sil.py GIRDI.png MASKE.png --model modeller/lama/lama_fp32.onnx --cikti SONUC.png
```
512 px'te 3–10 sn (CPU). Bilinen cevaplı fikstürde maske içi PSNR 35,5 dB; bölge dışı 0 piksel değişti (yeniden
ölçüldü). IOPaint kullanma (2025-08-13'te arşivlendi).

### Depth Anything V2 Small (ONNX fp16 49,6 MB, Apache-2.0): 2.5D paralaks
```zsh
mkdir -p modeller/derinlik && curl -fL -o modeller/derinlik/da2s_fp16.onnx https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model_fp16.onnx && [ "$(shasum -a 256 modeller/derinlik/da2s_fp16.onnx | cut -d' ' -f1)" = 2df6223f206b5164e21f664ace61dabeb9bb6a49b8b5a3e00510b4807d0f5b04 ]
ortamlar/gorsel/bin/python $G/derinlik.py GIRDI.png --model modeller/derinlik/da2s_fp16.onnx --cikti analiz/ad-derinlik.png
```
0,8–1,3 sn. Yalnız **Small** Apache-2.0 (Base/Large CC-BY-NC). Core ML sürümü `coremlcompiler` ister (yalnız Xcode).

### Vektör: vtracer (`ortamlar/gorsel`) + resvg 0.48.1 (4,6 MB, MPL-2.0)
```zsh
curl -fL -o /tmp/resvg.zip https://github.com/linebender/resvg/releases/download/v0.48.1/resvg-macos-aarch64.zip && [ "$(shasum -a 256 /tmp/resvg.zip | cut -d' ' -f1)" = 06440eb5aa14a28cbfc7e40ae39e1ffa71adc051b89fbaa913b4f1d9b905d09f ] && unzip -q -o /tmp/resvg.zip resvg -d arac && rm /tmp/resvg.zip
arac/resvg --version                                                              # kontrol
```

## Kaçınılacaklar (lisans ve kural tuzakları)
| Ne | Neden |
|---|---|
| rembg varsayılanı `bria-rmbg` (BRIA RMBG-2.0) | CC BY-NC; ticari için ücretli anlaşma |
| CodeFormer, GFPGAN (NC parçalar) | ticari değil; ayrıca gerçek kişinin yüzünü değiştirir — yüz onarımı varsayılan kapalı |
| Upscayl'in UltraSharp, Remacri (UltraMix) modelleri | CC-BY-NC-SA |
| FLUX.1 [dev]/Krea/Kontext, FLUX.2 [klein] 9B / [dev] | FLUX non-commercial lisansı; kişisel işte yasal ama 9,5 GB+ burada pratik değil |
| Stable Diffusion 3.5 | HF kapılı, iletişim bilgisi formu (hesap) |
| Qwen-Image / Edit | Apache-2.0 ama Q4 23–29 GB: disk ve RAM'e sığmaz |
| SAM 3 | kapılı; ad, doğum tarihi ister. Gerekirse SAM 2.1 (Apache-2.0) |
| Depth Pro, Depth Anything V2 Base/Large | araştırma / CC-BY-NC |
| Apple VTSuperResolution | **bu stüdyoda sınandı, reddedildi**: yalnız 4×, gölgeleri koyulaştırdı, PSNR bikübikten kötü, alfa 0 yazdı |
| `hyperframes media-use resolve` (görsel/LUT) | HeyGen kataloğu ve bulut; kanca engeller |
| rembg `withoutbg` arka ucu, `rembg[cli]` | bulut API / gradio analitiği |
| İndirilen "ücretsiz LUT paketleri", Apple Log LUT | lisans belirsiz ya da hesap ister → LUT'u `gorunum.py` ile kendin üret |
| Higgsfield, Midjourney, Runway… (ücretli bulut) | kullanıcı kuralı. Kullanıcı açıkça isterse yalnız `etkin = false` bir `bulut-ucretli` sağlayıcı kaydı (`arac-radari` → benimseme §7); maliyet ve dışarı gidecek dosyalar önce yazılır |
