# Benimseme: kayıt, kurulum, uyarlayıcı, sınama, geçiş

İçindekiler: 0 Önkoşul · 1 Kayıt · 2 Kurulum yeri · 3 Uyarlayıcı · 4 Sınama · 5 Geçiş · 6 Belgeleme · 7 Ücretli/bulut ve uygulama kaydı

## 0. Önkoşul
- Değerlendirme raporu `sistem/radar/` altında; kullanıcı bu kurulumu adı ve boyutuyla onayladı.
- Önce güncel durumu oku (`yetenekler.toml`, ilgili `medya/komutlar/*.py`, `git status`): stüdyo dosyaları başka
  oturumlarca değişebilir.
- Geri dönüş yolunu başlamadan yaz; değişecek dosyaların ilk hâlini sakla (depoda commit yoksa kopya al).
- İşi iş akışıyla yürütüyorsan bağımsız adımları ayrı küçük iş akışlarına böl: `resumeFromRunId` önek tabanlıdır;
  ilk değişen ya da bitmemiş ajan çağrısından sonraki her çağrı (bitmiş olsa bile) yeniden koşar (D 2026-10-05).

## 1. Kayıt (`yetenekler.toml`)
`medya/kayit.py` her `[[saglayici]]` tablosunu `Saglayici(**alanlar)`, her `[[yetenek]]` tablosunu
`Yetenek(**alanlar)` ile kurar. Bilinmeyen alan ya da eksik zorunlu alan TypeError verir (2026-10-05'te sınandı:
`surum` alanı → "unexpected keyword argument"; `aciklama`sız yetenek → "missing 1 required positional argument").
Sonuç: `medya yetenekler` ve `medya kur` durur; `medya sahneler` hatayı yutup uyarısız ffmpeg'e düşer (sessiz kalite
kaybı, aynı gün sınandı).

```toml
[[saglayici]]
ad = "<kisa-ad>"
tur = "python-arac"        # ikili | python-arac | python-paket | node | uygulama | bulut-ucretli
lisans = "kod <lisans> · ağırlık <lisans> (<kaynak>, <YYYY-AA-GG>)"
ticari = "evet"            # evet | hayir | kosullu | ?
kurulum = "<tek satır, sürümü sabit, tekrar çalıştırılabilir komut>"
kontrol = "<hızlı, 0 ile çıkan komut>"
boyut_mb = 900             # ortam + ilk kullanımda inen modeller
not = "<sürüm>; ölçüm: <süre, tepe bellek, tarih>; telemetri: <kapatma değişkeni>"

[[yetenek]]
ad = "<yetenek>"
alan = "<inceleme|ses|donusturme|denetim|uretim|gorsel|sistem>"
komut = "medya <komut>"
aciklama = "<ne yapar>"    # zorunlu
saglayici = "<yeni>"
yedek = ["<eski>"]
```
- `kurulum` kabukta çalışır (`shell=True`, stüdyo kökünde); `kontrol` kabuksuz çalışır (`shlex` ile bölünür, 60 sn
  sınırı): boru, `&&`, `$DEĞİŞKEN` kullanma. Yorumlayıcı ya da bağ denetliyorsan `ls -L` ya da onu çalıştıran
  komut: kopuk bağda `ls` 0 döner, `ls -L` 1 (ölçüldü 2026-10-08).
- `etkin` (varsayılan true) ve `onay` yalnız kapalı sağlayıcı içindir: `bulut-ucretli` ve `uygulama` (§7).
- Yeni alan gerçekten gerekiyorsa önce `Saglayici` sınıfına varsayılanlı alan ekle, sonra `medya test kayit`.
- Denetim: `medya yetenekler --saglayicilar` hatasız döner; `medya test kayit` geçer.

## 2. Kurulum yeri
| Tür | Yer | Kalıp |
|---|---|---|
| ağır Python (torch vb.) | `ortamlar/<alan>` | `arac/uv venv --python 3.12 ortamlar/<alan> && arac/uv pip install --python ortamlar/<alan>/bin/python '<paket>==<sürüm>'` |
| Python komut satırı aracı | `.uv/tools`, komut `arac/` (`UV_TOOL_DIR`, `UV_TOOL_BIN_DIR`) | `arac/uv tool install '<paket>==<sürüm>'` |
| hafif Python (`.venv`) | `pyproject.toml` extra | `arac/uv sync --extra <extra>` |
| node | `node_modules` | `npm install -D --save-exact <paket>@<sürüm>` |
| ikili | `arac/` | resmî sürüm + SHA-256 (kalıp: `sistem/kur.sh` içindeki uv kurulumu) |
| model | `modeller/` (`HF_HOME`, `TORCH_HOME`) | ilk kullanımda iner; `boyut_mb`'ye kat |

- `.venv` `uv.lock`'a tam eşitlenir: elle `pip install` bir sonraki `uv sync`'te silinir.
- Yorumlayıcı yalnız stüdyonun (`.uv/python`; `ortam.sh` → `UV_MANAGED_PYTHON=1`, kayıt komutunda da `--managed-python`
  yaz). mflux 2026-10-08'e dek python.org 3.13.1'e bağlıydı; `test_python_ortamlari_studyonun_yorumlayicisinda` tutar.
  Çok paketli ortamda `uv pip freeze` çıktısını `sistem/kisitlar/<paket>-<sürüm>.txt`'e koy, kurulumda `-c` ile ver
  (`.uv/`, `ortamlar/`, `arac/` git'e girmez). `uv tool install` kısıttaki `--hash`'i zorlamıyor (yanlış hash'le kurdu);
  yönetilen Python arşivini uv gömülü SHA-256'yla doğruluyor (bozuk arşivde "Hash mismatch").
- torch: `ortamlar/ses` 2.14.1 kullanır; aynı sürüm uv klonlarıyla diski paylaşır, farklı sürüm iki kez yer kaplar.
- İndirilen dosya: URL ve sürüm sabit; `shasum -a 256 <dosya>` yayımlanan değerle (HF: `?blobs=true` → `lfs.sha256`)
  eşleşir. safetensors / ONNX / CoreML / GGUF tercih; pickle (.pth, .ckpt, .bin) yalnız resmî kaynaktan. Üçüncü
  taraf yeniden yüklemede SHA-256 yalnız o yüklemeyi doğrular, aslına uygunluğu değil.
- İkili: `codesign -dv --verbose=2 <dosya>` ve `spctl -a -vv -t execute <dosya>` sonucunu kaydet (npm'den gelen
  ffmpeg-static bile "adhoc" imzalı ve "rejected"). Karantinayı (`xattr -d com.apple.quarantine`) kullanıcı onayı
  olmadan kaldırma.
- Homebrew kilitli (Xcode lisansı kabul edilmemiş; `sudo xcodebuild -license accept` kullanıcının kararı). Swift ve
  clang için `DEVELOPER_DIR=/Library/Developer/CommandLineTools`.
- Sonra `medya kur <ad>`: lisansı, ticari durumu ve boyutu gösterir; `etkin = false` sağlayıcıyı ve kurulumdan sonra
  5 GB'tan az boş bırakacak kurulumu reddeder (çıktı payını sen ekle).

## 3. Uyarlayıcı (`medya/komutlar/`)
- Var olan yetenek: aynı modülde `_<saglayici>_<is>()` yaz; `saglayici_sec("<yetenek>").ad` ile dallan; hata olursa
  `uyar(...)` ile yedeğe düş (kalıp: `medya/komutlar/sahneler.py`). Komut adı, bayraklar ve JSON çıktısı aynı kalır,
  böylece beceriler ve ajanlar değişmez. Çıktıya kullanılan sağlayıcının adını yaz.
- Ağır ortam: `medya/isciler/<ad>_isci.py` dosyasını `ortamlar/<alan>/bin/python` ile alt süreçte çalıştır, JSON
  dosyasıyla konuş (kalıp: `medya/komutlar/yaziya_dok.py` + `medya/isciler/yazi_isci.py`).
- Apple ML sağlayıcısı (Vision, SoundAnalysis, Core ML, VideoToolbox FRC): çağrıyı `medya/ortak.py`
  `apple_calistir(komut, zaman_asimi, hata_mesaji)` bekçisinden geçir (kalıp: `medya/komutlar/analiz.py`,
  `yavaslat.py`) ve Neural Engine kullanmayan bir yedek koy. `ANECompilerService` hata vermeden asılabilir
  (2026-10-05: 18 saat); çözüm kullanıcıda: `sudo killall ANECompilerService`.
- Yeni yetenek yalnız kullanıcı istediyse: yeni modülde `kaydet(alt, ad)` + `medya/cli.py` `KOMUTLAR` satırı.

## 4. Sınama (`testler/`)
- Bilinen-cevaplı fikstür: `testler/uretec.py` içine üretici ekle, gerçek değeri `gercek.json`'a yaz. Fikstürler
  yalnız `gercek.json` yoksa kendiliğinden üretilir; ekledikten sonra `.venv/bin/python testler/uretec.py`.
- Sağlayıcı kurulu değilse atla: `pytest.skip("<ad> kurulu değil")`.
- Eski ve yeni sağlayıcı aynı fikstürde koşar; yeni eşik eskisinden gevşek olamaz; geçmiş bir hatayı kilitleyen
  sınama silinmez.
- Bilinen cevabı olmayan üretken araçta: süre, kare sayısı, sabit kare hızı (`medya incele`), `medya denetle`
  (siyah/donma/flaş) ve `medya kontak` + Read. Kalite iddiası yok; kullanıcı izler.

## 5. Geçiş
`saglayici = "<yeni>"`, `yedek = ["<eski>"]` → `medya test <yetenek>` → tam `medya test` → `medya yetenekler
--saglayicilar` (✓). Eski sağlayıcı en az bir proje boyunca yedekte kalır; kaldırmak disk durumu ve kullanıcı
onayıyla. Geri dönüş: `saglayici`'yı eskiye al, `medya test`.

## 6. Belgeleme
- İlgili kardeş beceri (`kurgu-zanaati`, `hareket-tasarimi`, `ses-tasarimi`, `gorsel-uretim`, `teslim-denetimi`,
  `medya-studyo`): yetenek dilinde yeni sınırlar ve bayraklar.
- Bilgi tabanı: yeni tarihli dosya `sistem/arastirma/<YYYY-AA-GG>/<alan>.md`. Eski tarihli dosyalar kanıttır;
  düzeltme yeni tarihe yazılır. Becerinin son satırındaki bilgi tarihini güncelle.
- `sistem/dersler.md`: benimseme ya da red dersi (en üstte, tarihli).
- Üretken (AI) çıktı: projenin `KARARLAR.md`'sine "AI üretimi" satırı; gerçekçi AI içeriği platformda beyan ister
  (YouTube).

## 7. Ücretli / bulut ve uygulama kaydı (yalnız belgeleme)
```toml
[[saglayici]]
ad = "<hizmet>"
tur = "bulut-ucretli"
lisans = "ticari hizmet şartları (hesap + ücret/kredi), <YYYY-AA-GG>"
ticari = "?"
kurulum = ""
kontrol = ""
boyut_mb = 0
etkin = false
onay = "ücretli hesap; kişisel görüntü/ses <hizmet> sunucularına gider"
not = "yerel karşılık: <yetenek ya da beceri>"
```
- Yeteneğe bağlama, uyarlayıcı yazma, hesap açma, giriş yapma, anahtar isteme yok. `medya kur` kapalı sağlayıcıyı
  reddeder; `medya yetenekler --saglayicilar` onu "KAPALI" gösterir.
- "X'i ekle, onunla üretelim" isteği açık onay değildir. Önce göster: maliyet (tarihli fiyat sayfası), çıktının
  ticari kullanım ve sahiplik şartları, dışarı gidecek kişisel medya; sonra tek soru sor.
- Açılsa bile stüdyo onu sürmez (uyarlayıcı yok): kullanıcı kendi hesabında üretir, çıktıyı
  `medya proje yeni --kaynak` ile getirir; projenin `KARARLAR.md`'sine "AI üretimi: <hizmet>, <tarih>" satırı yazılır.
- Kullanıcı açıkça açtırırsa: hesabı ve anahtarı kullanıcı yönetir. `etkin = true` olunca `test_kayit_defteri_tutarli` bilerek kırılır — bunu söyle; sınamayı yalnız
  kullanıcı isterse değiştir.

**`tur = "uygulama"`:** kullanıcının kurduğu GUI programı; ajan onu süremez, yalnız dosya köprüsü verir
(`medya nle` → .otio/.edl). Örnekler `yetenekler.toml`'da: `kdenlive`, `resolve-ucretsiz`, ücretli
`resolve-studio-mcp`.
- `etkin = false`, `onay` = kullanıcı kararı (boyut; hesap/kayıt formu ya da ücret varsa onu da yaz).
- `kurulum` kullanıcıya verilecek tam yol (sürüm + SHA-256 ya da mağaza kimliği; telemetri/çökme raporu ayarı);
  `kontrol` = `ls '/Applications/<Uygulama>.app'`. Ücretliyse `kontrol = "false"`.
- `not`: köprüde ne aktarılır, ne kaybolur (ör. hız, kadraj, ses düzeyi) — ölçülmüş olarak.
- Yeteneğe sağlayıcı olarak bağlanmaz, uyarlayıcı yazılmaz; ajan kurmaz, açmaz.
