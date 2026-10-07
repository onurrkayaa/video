# Teknikler: zanaat, komutlar, ölçüt

Değişkenler: `G=$MEDYA/sistem/claude/skills/gorsel-uretim/scripts`, `PY=$MEDYA/.venv/bin/python`,
`F=$MEDYA/arac/ffmpeg`. Ara dosyalar kayıpsız PNG; JPEG yalnız son teslimde (her JPEG yeniden kodlar, piksel
karşılaştırmasını bozar).

## 1. Giriş: çalışma kopyası
`$PY $G/disa_aktar.py kaynak/X.HEIC --asil --cikti calisma/gorsel/X.png` — HEIC/RAW sips ile çözülür, yön pikselde
pişirilir, P3 → sRGB, EXIF yazılmaz. `medya analiz` ve kırpma yalnız bu kopyada (analiz yönü uygulamaz).
Kronolojik sıra (kolaj, seri): `arac/exiftool -T -FileName -DateTimeOriginal -OffsetTimeOriginal kaynak/*`.
RAW: önce `sips` (Apple çözücü). Deterministik 16 bit geliştirme gerekirse rawpy (`ortamlar/gorsel`); yeni
JPEG-XL ProRAW'ı rawpy açamayabilir → sips.

## 2. Kapak / küçük resim seçimi
Videodan: `medya analiz video.mp4 --aralik 0.5 --cikti analiz/v.json` → en yüksek `estetik` + yüz yakalama
kalitesi; adayları `medya kontak video.mp4 --anlar t1,t2,…` ile gör, seç. Estetik puanı zayıf sinyal: tek başına
karar verme. Kapakta yazı yalnız istenirse.

## 3. Boyutlar ve güvenli alan
| Hedef | Boyut | `disa_aktar.py --hazir` | Durum |
|---|---|---|---|
| Instagram akış 4:5 (en güvenli) | 1080x1350 | `ig-dikey` | doğrulanmadı (araştırma) |
| Instagram kare | 1080x1080 | `ig-kare` | doğrulanmadı |
| Hikâye / Reels kapağı 9:16 | 1080x1920 | `ig-hikaye` | doğrulanmadı |
| YouTube kapak | 3840x2160 (yedek 1280x720 ≤ 2 MB) | `yt-kapak`, `yt-kapak-hd` | YouTube Yardım (araştırma) |
| Shorts kapak | 2160x3840 | `yt-shorts-kapak` | araştırma |
| LinkedIn / X / Pinterest | 1200x627 / 1600x900 / 1000x1500 | `--boyut GxY` | doğrulanmadı |

Profil ızgarası 3:4 önizler: karede önemli içerik ortada. 9:16 kırmızı bant (Meta Reels reklam rehberi,
`teslim-denetimi` ile aynı): üst %14, alt %35, yanlar %6 — yüz ve yazı dışarıda. Denetim:
`$PY $G/kontak.py X_hikaye.jpg --guvenli dikey --cikti analiz/guvenli.png` (bindirme teslime girmez).
Kare/hikâye aynı sahnenin iki kırpımı: `--analiz` ile yüz/ilgi merkezli `kapla`; özne sığmıyorsa `sigdir --pay
0.1 --zemin '#hex'` (bulanık uzatma istenmedikçe yok). Uyarı "büyütme ×…" → kaynak küçük: §6.

## 4. Renk görünümü (bir seri, tek görünüm)
1. Görünümü bir kez yaz: `$PY $G/gorunum.py --hazir sicak-sinematik --cikti plan/gorunum.cube`
   (sıcak ışıklar, hafif serin gölge, mat siyah, −%10 doygunluk; çıktı nötr griyi ve tekdüzeliği yazar).
2. Uygula (yalnız `disa_aktar.py --asil` ile üretilmiş sRGB kopyaya; ffmpeg girdinin ICC'sini taşır): `$F -nostdin -v error -i calisma/gorsel/1.png -vf "lut3d=file=plan/gorunum.cube:interp=tetrahedral" -frames:v 1 calisma/gorsel/1-g.png`.
   Aynı `.cube` videoda da çalışır (`kurgu-zanaati`): fotoğraf ve klip aynı görünür.
3. Birliği ölç: `$PY $G/olc.py calisma/gorsel/*-g.png` → `lab_ort` [L*, a*, b*]. Bir fotoğraf diğerlerinden belirgin
   ayrışıyorsa (ör. b* farkı > 6) o fotoğrafa ön düzeltme: `gorunum.py --sicaklik -0.03 --cikti calisma/3-duzelt.cube`,
   sonra `-vf "lut3d=file=calisma/3-duzelt.cube,lut3d=file=plan/gorunum.cube"`. Eşik sezgisel: `lab_ort` sahne içeriğini
   (mavi deniz, sıcak iç mekân) renk kaymasından ayıramaz; son söz kontak sayfası. **Yalnız sayısal modda ön düzeltme
   yapma:** `lab_ort` sayılarını raporla, hangi dosyalara bakılacağını kullanıcıya söyle, kararı o versin.
4. Ten: sıcaklığı 0.03–0.06 aralığında tut; yüzler turuncuya kaçarsa sıcaklığı düşür, doygunluğu artırma.
5. Kırpık piksel (`kirpik_*_%`) görünümden sonra artmamalı.
Kuralı: piksel başına renk LUT'a girer; gren, vinyet, keskinlik giremez (istenmedikçe ekleme).

## 5. Arka plan silme (ürün, kişi)
`medya arkaplan-sil calisma/gorsel/urun.png --maske --cikti calisma/gorsel/urun-kesik.png`
→ `$PY $G/kenar_arindir.py calisma/gorsel/urun-kesik.png --cikti calisma/gorsel/urun-temiz.png`
→ `$PY $G/olc.py calisma/gorsel/urun-temiz.png` (tek özne: `alfa_parca` 1, `alfa_delik` 0, `alfa_kirli_%` ≈ 0)
→ `$PY $G/kontak.py calisma/gorsel/urun-temiz.png --zemin hepsi --cikti analiz/kenar.png` ve kenar yakını:
`--kirp x,y,g,y`. Saç, kürk, cam, desenli yüzey, delik/parça varsa ikinci görüş BiRefNet ([araçlar](araclar.md)),
ikisini aynı ölçüm ve sayfayla karşılaştır. Ürün asla yapay zekâyla yeniden çizilmez: gerçek kesik sahneye konur.
Sahneye yerleştirme: ürünü zeminine oturtan yumuşak temas gölgesi, ışık yönü plaka ile aynı, ürün renkleri değişmez.

## 6. Büyütme (eski / düşük çözünürlüklü fotoğraf)
Hedef boyut aslın **tam katı** (2×: G*2 x Y*2) — `--boyut` en-boy tutmazsa kırpar, geri izdüşüm anlamsızlaşır
(`olc.py --referans` en-boy %0,5'ten farklıysa ölçmeden hata verir). Referans ölçümü IG kırpımından **önce**.
Taban Lanczos (`disa_aktar.py --boyut`); ayrıntı gerekiyorsa Real-ESRGAN x4 → teslim boyutuna Lanczos küçültme.
Ölç: `$PY $G/olc.py buyuk.png --referans calisma/gorsel/asil.png` (geri izdüşüm: küçültüp aslıyla): PSNR ≥ 30 dB,
SSIM ≥ 0,90; altıysa model içerik uyduruyor → Lanczos ya da 2× ile kal, kullanıcıya göster. Geri izdüşümde Lanczos
her zaman kazanır (sadakat ölçüsüdür, güzellik değil); ESRGAN'ın kazancı `netlik` artışı + yan yana sayfa:
`kontak.py asil.png lanczos.png esrgan.png --kirp …`. Ölçülen: 256→1024 PSNR 31,2 / SSIM 0,976 (geçti);
128 px kaynakta 28,8 dB (kaldı — çok küçük kaynak). Gerçek kişilerin yüzü en çok ~2×, yüz onarımı yok.

## 7. Nesne silme
Maske (beyaz = sil): `medya arkaplan-sil --maske` çıktısı ya da Pillow ile çizilmiş çokgen.
`ortamlar/gorsel/bin/python $G/lama_sil.py calisma/gorsel/X.png maske.png --model modeller/lama/lama_fp32.onnx --cikti calisma/gorsel/X-temiz.png`
→ `$PY $G/olc.py calisma/gorsel/X-temiz.png --referans calisma/gorsel/X.png --maske calisma/gorsel/X-temiz-bolge.png`:
`maske_disi_degisen_piksel` 0 olmalı. Dikiş için %100 kırpıntıya bak.

## 8. Kolaj
`$PY $G/kolaj.py 1-g.png 2-g.png 3-g.png --duzen 1,2 --dikey --boyut 1080x1350 --analiz 1.json 2.json - --cikti calisma/gorsel/kolaj.png`
- Önce aynı görünüm (§4), sonra kolaj. Sıra: çekim zamanı ya da görsel akış (bakış yönü içeri, en güçlü kare büyük hücrede).
- Boşluk tek ve eşit (varsayılan kısa kenarın %1,5'i), dış pay da aynı; zemin nötr. Yazı, çerçeve süsü, sticker yok.
- `medya analiz` yoksa (ANE takılı): `--analiz` yerine `--merkez 0.5,0.35 - 0.6,0.4` (görsel başına x,y ya da `-`);
  yüz kutusu uyarısı o zaman çalışmaz → hücreleri kullanıcı kontrol eder.
- Uyarılar: yüz hücre kenarında → düzeni ya da sırayı değiştir; ×büyütme → o fotoğrafı küçük hücreye koy.
- Teslim: `disa_aktar.py calisma/gorsel/kolaj.png --hazir ig-dikey --cikti cikti/kolaj_dikey.jpg`.

## 9. Yazılı görsel (afiş) — yalnız yazı istendiyse
Model yazı çizmez (Türkçe ğ ş ı İ güvenilmez). Zemin plakası (fotoğraf, kesik ürün ya da üretim) + HyperFrames
HTML tipografi: `<html lang="tr">`, yerel woff2 latin + latin-ext (`varliklar/yazitipleri/`, OFL), duraklatılmış tek
GSAP zaman çizelgesi, `data-duration="1" data-fps="1"`. Kompozisyon kuralları: `hareket-tasarimi`.
`hyperframes lint D` → `hyperframes render D --format png-sequence --fps 1 -o calisma/afis` (1 PNG) →
`disa_aktar.py calisma/afis/frame_000001.png --hazir ig-kare --cikti cikti/afis_kare.jpg`. Kare ve hikâye için
iki ayrı kompozisyon (yeniden yerleşim; kırpma değil). Metin denetimi: `tesseract cikti/afis_kare.jpg - -l tur+eng --psm 6`
beklenen metinle birebir. Metni uydurma: kullanıcıdan al; kanıtsız iddia ("en hızlı") yazma.

## 10. Üretim (konsept görselleri)
Üretici kurulu değil; yalnız harici SSD + onay ([araçlar](araclar.md)). Üretici yoksa: kullanıcının fotoğrafları,
kesik ürün + HTML/CSS zemin (gradyan, ışık), ya da lisansı açık (CC0) fotoğraf. Varsa:
- Konsept başına 3–4 tohum, sabit tohumla tekrarlanabilir; istem İngilizce, olumlu ("plain, unbranded surfaces"),
  kişisel bilgi ve marka adı yok. Işık yönü ve kamera yüksekliği ürün fotoğrafına eşlenir.
- Kare ve hikâye: 9:16 plaka üret, kareyi ondan kırp (iki biçimde aynı sahne).
- Aday seçimi: `kontak.py` sayfası + `medya analiz` estetik; `tesseract` sahte yazı/logo bulursa ele.
- KARARLAR.md: model, revizyon, istem, tohum, adım, boyut, süre. Paylaşımda "AI ile üretildi" notunu öner.

## 11. Vektör (logo, ikon)
`ortamlar/gorsel/bin/python -c "import vtracer, os; vtracer.convert_image_to_svg_py('logo.png','logo.svg',colormode='color',hierarchical='stacked',mode='spline',filter_speckle=4); os._exit(0)"`
→ `arac/resvg logo.svg logo-r.png -w <genişlik>` → `$PY $G/olc.py logo-r.png --referans logo.png`: SSIM ≥ 0,97
(fikstürde 0,99). Küçük kaynakta önce 2–4× büyüt.

## 12. Derinlik (2.5D paralaks)
`derinlik.py` (16 bit, yakın = açık) → ön plan kesiği (§5) + LaMa ile doldurulmuş arka plan (§7) → katmanlı
hareket `hareket-tasarimi`'nde (arka plan %1–4, ön plan %1–8 ölçek; özne açığa delik çıkarmamalı).

## 13. Gizlilik
Teslimde `disa_aktar.py` EXIF yazmaz; görsel yeniden kodlanmıyorsa `medya meta-temizle X --cikti Y` (yön ve ICC
kalır). Doğrula: `arac/exiftool -a -G1 -s -location:all Y` boş + `olc.py --teslim` geçer.
- İkisi de konumla birlikte **çekim tarihini ve kamera bilgisini** de siler (ölçüldü). Kullanıcı yalnız konum istediyse
  söyle; tarihi korumak isterse: `arac/exiftool -overwrite_original -tagsFromFile SRC -DateTimeOriginal -OffsetTimeOriginal OUT`
  (ölçüldü: tarih geri gelir, konum boş kalır; `olc.py --teslim` bu dosyada tarih yüzünden kalır — beklenen, raporla).
- Asılların (`kaynak/`, telefondaki) GPS'i tuttuğunu kullanıcıya söyle.
