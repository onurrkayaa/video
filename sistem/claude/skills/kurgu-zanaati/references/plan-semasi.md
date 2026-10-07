# Kurgu planı sözleşmesi — `plan/kurgu.json`

Tek gerçek kaynak. `medya senkron --plan`, `medya denetle --plan`, `medya nle` ve `scripts/plan_denetle.py` bunu okur;
alan adlarını değiştirme, yeni alan uydurma (araçlar okumaz). Üst düzey yalnız `ad fps boyut sure muzik cekimler`;
`muzik` yalnız `dosya bas analiz`; çekimde `not`/`gerekce` yok (gerekçe `KARARLAR.md`'ye); bilinmeyen alan ⚠. Göreli yollar proje köküne göredir; `medya` komutlarını
proje kökünden çalıştır.

```json
{
  "ad": "tatil-montaj",
  "fps": 30,
  "boyut": [1080, 1920],
  "sure": 60.0,
  "muzik": {"dosya": "calisma/ses/muzik.wav", "bas": 0, "analiz": "analiz/muzik.json"},
  "cekimler": [
    {"no": 1, "kaynak": "kaynak/IMG_0412.MOV", "kaynak_bas": 3.2,
     "klip": "calisma/klipler/IMG_0412-sdr.mp4", "klip_bas": 3.2,
     "cikti_bas": 0, "cikti_son": 4.2667, "hiz": 1, "ses": "muzik", "vurusa": false,
     "gecis": {"tur": "siyah-dip", "sure_kare": 12},
     "kadraj": {"ilgi": [0.62, 0.41], "mod": "sabit"}, "hareket": {"tur": "kenburns", "olcek": [1.0, 1.06]}},
    {"no": 2, "kaynak": "kaynak/IMG_0420.MOV", "kaynak_bas": 1.5,
     "klip": "calisma/klipler/IMG_0420-yavas025.mov", "klip_bas": 0,
     "cikti_bas": 4.2667, "cikti_son": 7.4667, "hiz": 0.25, "ses": "sessiz", "vurusa": true,
     "gecis": {"tur": "kesim", "sure_kare": 0}, "hareket": {"tur": "punch", "olcek": [1.0, 1.1], "kare": 3}},
    {"no": 3, "kaynak": "kaynak/IMG_0433.MOV", "kaynak_bas": 8.0,
     "cikti_bas": 6.8667, "cikti_son": 11.0, "hiz": 1, "ses": "kendi", "vurusa": false,
     "gecis": {"tur": "erime", "sure_kare": 18}}
  ]
}
```

## Alanlar
| Alan | Anlam |
|---|---|
| `fps`, `boyut` | Çıktı kare hızı; `[genişlik, yükseklik]`, çift tamsayı |
| `sure` | Toplam süre (sn, k/fps); son çekimin `cikti_son`u ile aynı |
| `muzik.dosya` | Kompozisyonda çalan dosyanın AYNISI (analiz edilen) |
| `muzik.bas` | Müzik dosyasının t=0'a denk gelen saniyesi (video vuruşu = müzik vuruşu − bas). Önerilen 0 (aşağıya bak) |
| `muzik.analiz` | `medya muzik` JSON'u (bu dosyanın analizi) |
| `kaynak`, `kaynak_bas` | `kaynak/` altındaki salt okunur kopya ve oradaki giriş saniyesi |
| `klip`, `klip_bas` | `calisma/klipler/` altındaki ara dosya (sdr, cfr, yavaslat, rampa, sabitleme); yoksa kaynak kullanılır |
| `cikti_bas`, `cikti_son` | Çıktı saniyeleri, k/fps ızgarasında (4+ ondalık) |
| `hiz` | Asla göre hız. `< 1` ise ağır çekim `klip`'e pişirilmiş olmalı, klip 1x oynar. `> 1` hızlandırma `data-playback-rate` olabilir |
| `ses` | `kendi` (kameranın sesi; yalnız `hiz: 1`), `muzik`, `sessiz` |
| `vurusa` | Açıkça `true`/`false`. `true` = kesim vuruşa oturtuldu; `medya senkron` ölçer |
| `gecis` | Bu çekime GİRİŞ: `{tur, sure_kare}`; `tur`: kesim, erime, j-kesim, l-kesim, eslesme, savurma, yakinlasma, isik, siyah-dip, beyaz-dip, flas |
| `kadraj`, `hareket` | Kompozisyon parametreleri (serbest nesne). Öneri: `kadraj {ilgi:[x,y] 0–1 sol üst, mod: sabit|pan|takip|dolgu}`, `hareket {tur: punch|kenburns|paralaks, olcek:[a,b], kare}` |

## Kurallar
- **Erime örtüşmedir:** `cikti_bas = önceki cikti_son − sure_kare/fps`. Diğer bütün geçişlerde çekimler uç uca, boşluksuz.
- Erimeye `vurusa: true` verilmez (`senkron` örtüşmenin başını ölçer); erimenin ORTASI ölçü başına konur.
- Vuruşa kesim: `cikti_bas = floor(vuruş·fps)/fps` (görüntü 0–1 kare önce). Yalnız `guven_seviye: yuksek`.
- İlk çekim 0'da başlar; ilk çekime erime olmaz (siyahtan açılış = `siyah-dip`).
- 3 kareden kısa çekim olmaz (flaş kare).
- Kare ızgarası: her zaman `k/fps`, toplanmış yuvarlanmış sürelerden değil mutlak zamanlardan hesaplanır.

## `muzik.bas` (önerilen: 0)
`bas` = müzik dosyasında videonun 0. saniyesine denk gelen an: video vuruşu = müzik vuruşu − bas. `medya nle`,
`senkron` ve `denetle` aynı okur (senkron 2026-10-05'te düzeltildi; sınama `test_senkron_plan_sozlesmesi…`).
Yine de en temizi tek saat: şarkının kullanılan bölümünü ayrı WAV olarak kes, onu analiz et, `bas: 0`:
```sh
medya muzik kaynak/sarki.m4a --cikti analiz/muzik-tam.json --ana analiz/muzik-ana.wav   # bölümler, S seçimi
arac/ffmpeg -nostdin -v error -ss S -t L -i analiz/muzik-ana.wav -c:a pcm_s24le calisma/ses/muzik.wav
medya muzik calisma/ses/muzik.wav --cikti analiz/muzik.json                                # planın analizi
```
S bir ölçü başı ya da cümle başıdır; L kapanış sönümünü de kapsar (son ve kısaltma: `ses-tasarimi`).
`plan_denetle` `bas ≠ 0`'ı uyarı olarak gösterir (hata değil).

## Kompozisyon eşlemesi (plan_denetle `--html` bunu arar)
Her çekim için `id="c<no>"` zamanlı `<video>`/`<img>`: `data-start = cikti_bas`, `data-duration = cikti_son − cikti_bas`,
`data-media-start = klip_bas` (klip varsa) ya da `kaynak_bas`, `src` adı plandaki dosyayla aynı. `ses: kendi` →
`data-has-audio="true"` ve `muted` yok; diğerleri `muted`. Müzik: `id="muzik"` `<audio>`, `data-start="0"`,
`data-media-start = muzik.bas`. Ayrıntı: [kompozisyon](kompozisyon.md).

## Denetim
```sh
$P $K/plan_denetle.py plan/kurgu.json                                   # çizimden önce
$P $K/plan_denetle.py plan/kurgu.json --html calisma/kompozisyon/index.html
$P $K/plan_denetle.py plan/kurgu.json --denetim cikti/denetim/X-denetim.json   # medya denetle --json çıktısı
```
✗ = hata (çıkış 1; düzeltmeden çizme). ⚠ = bak; bilinçliyse `KARARLAR.md`'ye gerekçesiyle yaz. Denetler: şema,
ızgara, boşluk/örtüşme, kaynak `kaynak/` altında mı, klip süresi yetiyor mu, ağır çekim pişmiş mi, `kendi` sesi,
güven kapısı, floor kuralı, erime ortası, geçiş çeşitliliği/sıklığı, ağır çekim sıklığı, flaş sınırı, metronom
uzunluklar, HTML eşlemesi, ağdan betik, istenmeyen ekran yazısı, çizimde planlı/plansız kesim, flaş ve siyah,
HDR (HLG/PQ) ortamın klipsiz kullanımı (✗), etkin ölçek = cover × `hareket.olcek` > 1,15 (⚠; döndürme hesaba katılır).
Sınandı (2026-10-05, küçük fikstür): doğru plan GEÇTİ; bozuk planda 9 hatanın hepsi yakalandı; HyperFrames taslağı +
`medya denetle` raporu ile planlı siyah-dip/erime "flaş" bulguları beklenen olarak ayrıldı. HDR/ölçek/bilinmeyen alan
sınaması (2026-10-05): HLG asıl ✗, `medya sdr` klibi geçti; 4K yatay → 1080x1920 punch 1,25 geçti, 1,35 ⚠ (≤ 1,29);
1080p yatay → dikey ⚠ (cover 1,78); 90° döndürülmüş 1920x1080 → dikey geçti; üst düzey `cikti`, `muzik.kaynak_bas` ⚠.
