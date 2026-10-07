# Kaynaklar, lisanslar, kurulum gerektirenler

Kaynak: `sistem/arastirma/2026-10-05/audio-production.md` (şüpheci düzeltmeler dahil), `eksiklik-elestirisi.md`; paket
bilgileri 2026-10-05'te PyPI'dan okundu, bağımlılık çözümlemesi `uv pip compile --only-binary :all:` ile sınandı
(kurulmadı). Kurulu olmayan her şey için: boyutu söyle, >2 GB ise onay al, kaydı `arac-radari` yapar.

## Lisans defteri
Her ses dosyası için `KARARLAR.md`'ye bir satır:
`- AAAA-AA-GG · ses: calisma/ses/<dosya> — kaynak <URL/kişi/araç>, lisans <ad>, ticari <evet|hayır|koşullu>, atıf <yok|metin>; <ölçüm>`
Üretilen seste yanına künye JSON'u: araç ve sürüm, model, istem/metin, ayarlar, tarih, lisans, `shasum -a 256` özeti.
`efekt.py --json` hepsini yazar (betik sürümü, argümanlar, tarih, sha256; ölçüldü: `shasum -a 256` ile aynı); öbür
araçlarda (müzik sentezi, TTS) özeti `shasum -a 256 <dosya>` ile ayrıca yaz.
- İş (ticari) için `ticari: evet` şart; NC asla. Kişisel işte NC kullanılacaksa açıkça söyle.
- Telifli şarkı kişisel hediyede olur, herkese açık paylaşımda risklidir: söyle. Instagram'ın uygulama içi müziği
  seçilirse kısma ve miks bizde yapılamaz.
- **Kural (CLAUDE.md):** telifsiz ses kodla üretilir ya da CC0'dan alınır. CC-BY (atıf gönderi açıklamasına; ekrana
  yazı yok), Pixabay İçerik Lisansı ve Sonniss EULA yalnız kullanıcı açıkça onaylarsa: onay `KARARLAR.md`'ye satırla.
- YouTube gerçekçi yapay içeriği (ana odaktaki müzik dahil) beyan ister; kişinin kendi klon sesiyle dış ses muaf
  (support.google.com/youtube/answer/14328491). Instagram/Meta ve öbür platformların YZ etiketi kuralını kullanıcıya
  hatırlat (araştırma: "gereken yerde yapay dış sesi etiketle"); kuralın ayrıntısı doğrulanmadı.

## Müzik — seçenekleri bu sırayla sun
| Seçenek | Lisans | Durum |
|---|---|---|
| Kullanıcının parçası | belge kullanıcıda; sor | hazır |
| Kodla: numpy/pedalboard sentezi | kendi üretimimiz | hazır; ses sentetik, kullanıcı dinleyip karar verir |
| CC-BY kütüphane (ör. incompetech, Kevin MacLeod: CC-BY 4.0, hesapsız) | atıf zorunlu → yalnız kullanıcı onayıyla | indirilebilir; bot koruması aşılmaz |
| Kodla: MIDI + SoundFont (tinysoundfont, pretty_midi, MIT) | GeneralUser GS müzik üretimine serbest | kurulu değil (~40 MB); TinySoundFont modülatör desteklemez → ses sönük |
| Magenta RealTime 2, `mrt2_small` (enstrümantal) | kod Apache-2.0, ağırlık CC-BY-4.0; Google çıktıda hak iddia etmez; eğitim "stock music" (satıcı beyanı) | kurulu değil, ~2,4 GB → sor |
| ACE-Step 1.5 (sözlü şarkı, BPM/ton) | MIT; satıcı ticari kullanıma izin verir | 8–9,5 GB → yalnız harici SSD, kullanıcı kararı |

Doğrulanmış bir CC0 müzik kütüphanesi yok (araştırmada bulunmadı); CC0 dendiğinde dosyanın lisans sayfasını göster.
Kodla üretilen müzikte vuruşlar aritmetiktir (n·60/BPM); kesimler yine `medya senkron` ile ölçülür.

Magenta RT 2 (onaydan sonra; `df -h /` ≥ 5 GB + çıktının iki katı kalmalı):
```
source /Users/onurkaya/Projects/video/ortam.sh; cd $MEDYA
export MAGENTA_HOME=$MEDYA/modeller/magenta        # varsayılan ~/Documents/Magenta (iCloud'a yüklenebilir)
arac/uv venv --python 3.12 ortamlar/muzik-uret
arac/uv pip install --python ortamlar/muzik-uret/bin/python --no-build 'magenta-rt[mlx]==2.0.3'
ortamlar/muzik-uret/bin/mrt models init && ortamlar/muzik-uret/bin/mrt models download mrt2_small
ortamlar/muzik-uret/bin/mrt mlx generate --model mrt2_small --prompt 'warm fingerpicked acoustic guitar, soft piano' --duration 60
```
Paket kaynağından okundu: `--model` varsayılanı `mrt2_base` (açıkça `mrt2_small` ver), tohum bayrağı yok, çıktı her
seferinde `$MAGENTA_HOME/magenta-rt-v2/outputs/output_audio_mlx_mrt2_small.wav` üzerine yazılır → hemen projeye taşı.
Çözümleme: 88 paket, yalnız tekerlek (jax 0.11.2, mlx 0.32.3); hız ve kalite bu Mac'te sınanmadı.

Üretilen müzik kabulü (araştırma): istenen tempo varsa `medya muzik` ±1 BPM; enstrümantalse `medya ayir --iki`
sonrası vocals katmanında `medya yaziya-dok` kelime bulmaz; süre tam; düzey `medya ustala --olc`; istemde sanatçı adı
yok; künye JSON'u. Üretim ile çizim aynı anda çalışmaz (16 GB bellek paylaşılır).

## Efektler
| Kaynak | Lisans | Nasıl |
|---|---|---|
| `scripts/efekt.py` (whoosh, riser, vurus, tik) | kendi üretimimiz | hazır; önce bu |
| Kenney ses paketleri (kenney.nl/assets/category:Audio) | CC0, hesapsız | LICENSE dosyasıyla `kaynak/`'a |
| `~/.claude/skills/media-use/audio/assets/sfx/*.mp3` (19: whoosh, whoosh-short, whoosh-cinematic, riser, impact-bass-1/2, click…) | Pixabay İçerik Lisansı: videoda ticari serbest, atıf gerekmez; CC0 değil, ham dosya ayrıca dağıtılmaz | yalnız kullanıcı onayıyla; yalnız dosyalar (media-use komutları değil) |
| Sonniss #GameAudioGDC | telifsiz, atıfsız; YZ eğitimi ve ham dağıtım yasak; CC0 değil | yalnız kullanıcı onayıyla; Cloudflare koruması: kullanıcı tarayıcıdan indirir, `medya proje yeni --kaynak` |
| MOSS-SoundEffect v2 (metinden efekt) | Apache-2.0 | 6,4 GB, ~12 GB tepe bellek → yalnız harici SSD |

Kullanma: Freesound (hesap), BBC SFX (ticari değil), Pixabay/YouTube Audio Library indirmesi (bot koruması/hesap),
OpenGameArt'ta CC0 olmayanlar.

## Dış ses (Türkçe)
1. **Kullanıcının kendi kaydı:** en doğal, lisans sorunu yok. Aynı yerde 10 sn oda sesi kaydettir. Sonra temizlik
   ([teknikler](teknikler.md) §2).
2. **VoxCPM2** (OpenBMB, mlx-audio): kod ve ağırlık Apache-2.0, Türkçe dahil 30 dil; `--instruct` ile tariften ses
   tasarlar (kimsenin sesi gerekmez). Satıcı ölçümü Türkçe WER %0,82. 4-bit 2,3 GB / 8-bit 3,2 GB → sor. Temel M2'de
   gerçek zamandan yavaş (tahmin; M4 Pro'da RTF ~1,76).
```
arac/uv venv --python 3.12 ortamlar/tts
arac/uv pip install --python ortamlar/tts/bin/python --no-build 'mlx-audio[tts]==0.5.7'
ortamlar/tts/bin/mlx_audio.tts.generate --model mlx-community/VoxCPM2-4bit --text "$(cat plan/dis-ses.txt)" --instruct 'Calm, warm male voice in his thirties' --output_path calisma/ses/dis-ses --file_prefix vo-1
```
   Çözümleme: 55 paket, torch yok. `sts`/`server` ekleri derleyici ister (webrtcvad): ekleme. Bayraklar paketten:
   `--instruct --ref_audio --ref_text --lang_code --output_path --file_prefix`; tohum bayrağı yok → her alımı sakla.
   Klon yalnız rızayla (kullanıcının kendi sesi): `--ref_audio ben.wav --ref_text '<tam döküm>'`; başkasını taklit
   VoxCPM2 koşullarına aykırı.
3. **Chatterbox Multilingual v3** (MIT, Türkçe var): aynı mlx-audio ile `--model mlx-community/chatterbox-multilingual-v3
   --lang_code tr --ref_audio <izinli kayıt>` (2,7 GB). PyTorch paketi (torch 2.6, numpy<2 sabitler) kullanılmaz.
4. **Kokoro** (`hyperframes tts`): Türkçe yok (dil listesi en-us, en-gb, es, fr-fr, hi, it, pt-br, ja, zh; yerelde okundu);
   yalnız İngilizce, `HYPERFRAMES_PYTHON` ile kokoro-onnx ortamı ister (kurulu değil).
5. **macOS `say -v Yelda`:** lisans "kişisel, ticari olmayan kullanım" → yalnız kişisel taslak ya da zamanlama yer
   tutucusu; yayımlanacak işte değil.

Her alımın kabulü: metni sayılar yazıyla, kısaltmasız onaylat → 2–3 alım →
```
medya yaziya-dok calisma/ses/dis-ses/vo-1.wav --dil tr --cikti analiz/vo-1-yazi.json
$PY $B/cer.py --metin plan/dis-ses.txt --yazi analiz/vo-1-yazi.json --kapi tts --json analiz/vo-1-cer.json
ffmpeg -nostdin -i calisma/ses/dis-ses/vo-1.wav -af silencedetect=n=-50dB:d=0.7 -f null - 2>&1 | grep silence_start
```
Kapı: CER ≤ %3, WER ≤ %8, eklenen/düşen kelime yok, 10–18 karakter/sn, içte 0,7 sn'den uzun sessizlik yok (araştırma);
ilk alımda sesi kullanıcı onaylar. Seçilen alım, ayarlar ve model künyeye.

## Kaçınılacaklar
- MusicGen (CC-BY-NC): media-use BGM'nin yedeği; hesap yoksa pip ile kurup kullanır → media-use ses komutları çalıştırılmaz.
- Stable Audio Open (kapılı, hesap; gelir sınırı), AudioLDM2, AudioGen, MMAudio, AudioX, TangoFlux (NC), ThinkSound (yalnız araştırma).
- XTTS-v2 (CPML, NC), F5-TTS, MMS-TTS, OmniVoice, Higgs TTS 3 (NC), Piper Türkçe sesleri (NC ya da Lessac tabanlı).
- Demucs `[quantized]`/mdx_q ve audio-separator (diffq: CC-BY-NC); topluluk BS-RoFormer ağırlıkları (lisans belirsiz: yalnız kişisel).
- Resemble Enhance, DeepFilterNet Python paketi (eski sabitlemeler): `medya ses-temizle` var.
- `hyperframes beats` ve her sabit BPM ızgarası ("sesler kaymış"); HeyGen/ElevenLabs/Gemini/Lyria bulut yolları.
- Sonniss'i betikle indirmek (bot koruması aşılmaz).

## Ağ, disk
- `ortam.sh` telemetriyi kapatır; model indikten sonra `HF_HUB_OFFLINE=1`. Modeller `modeller/`, ortamlar `ortamlar/<alan>`.
- Kurulum öncesi/sonrası `df -h /`; ≥ 5 GB boş kalsın. Temizlik raporu `medya temizle` (silme onayla).
