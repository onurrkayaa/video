---
name: ses-tasarimi
description: Use when a video or animation needs sound work - choosing or shortening music, stems, noisy dialog (wind, crowd, hum), sound effects or transition whooshes, ducking music under speech, J/L cuts, clicks at cuts, mixing, platform loudness, voiceover or TTS, or generated music, fitting a song to video length or lyric timing (müzik, fon müziği, şarkıyı kısalt, şarkıyı videoya uydur, şarkının sonu, sözler, gürültü, rüzgâr, efekt, dış ses, seslendirme, müziği kıs, ses seviyesi, LUFS, tık, miks).
---

# Ses tasarımı

**İlke: Claude duyamaz. Her ses kararı ölçümle kapanır; ölçülemeyene "doğrulanamadı" denir, kullanıcıya dinleyeceği
saniyeler verilir.** Ses saattir: ölçülen ana WAV çalınır; katmanlar PCM'de tek sürekli miks olur, AAC parçaları eklenmez.

## Ne zaman / ne zaman değil
- **Ne zaman:** videonun her ses işi.
- **Değil:** kesim, sıra, geçiş, en-boy → `kurgu-zanaati`; yazı/hareket → `hareket-tasarimi`; görsel → `gorsel-uretim`; teslim eşikleri → `teslim-denetimi`; araç kurma → `arac-radari`; yönlendirme → `medya-studyo`.

## Hızlı başvuru
`B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts`, `PY=$MEDYA/ortamlar/ses/bin/python`. Komutlar: [teknikler](references/teknikler.md).

| İş | Yap | Kapı |
|---|---|---|
| Klip sesi | WAV'a, `aresample=48000:async=1:first_pts=0` ile | — |
| Konuşma | `medya ses-temizle ham.wav --cikti temiz.wav --dogrula` | `$PY $B/temizlik_olc.py`, `$PY $B/cer.py --kapi temizlik` |
| Müzik | `medya muzik <wav> --cikti analiz/muzik.json` | güven |
| Kısaltma | `$PY $B/kisalt.py yap` → `medya muzik` → `kisalt.py olc` | ek ±10 ms, F ≥ 0,95, ±0,5 LU, kuyruk < −60 dBFS |
| Katman | `medya ayir [--iki]` | — |
| Kısma | `$PY $B/kisma.py [--kazanc dB]` | 3 sn pencerede konuşma − müzik ≥ 10 LU |
| Efekt | `$PY $B/efekt.py` ya da lisanslı hazır ses | olay ±1 kare |
| Dış ses | kullanıcının kaydı ya da TTS (kurulum ister) | `$PY $B/cer.py --kapi tts` |
| Tık | her sert ses kesimine 5–10 ms geçiş (`data-fade-in/out` ≥ 0.01); ek yeri yoksa `$PY $B/tik_onar.py` | `medya denetle` tık listesi boş |
| Ustalık | `medya ustala --hedef -14` (sosyal) / `-16` (web, konuşma) `--tepe -1.5` | `medya denetle --hedef …` |

## Kurallar
1. **Lisans defteri:** her ses dosyası `KARARLAR.md`'ye (kaynak, lisans, ticari mi, atıf). Belirsiz → kullanma; NC → iş için asla. Seçenekler, kaçınılacaklar: [kaynaklar](references/kaynaklar.md).
2. **Kurulum:** TTS ve müzik üreteci kurulu değil; boyutu söyle, >2 GB onaysız kurma.
3. **Ölçülmüş varsayılanlar:** `ses-temizle` 12 dB (sınırsızda anlaşılırlık düştü), `-D` içinde; `arac/deep-filter`'ı doğrudan çağırma.
4. **Yazı yok:** altyazı yalnız istenirse. **Vuruş iddiası** yalnız `medya muzik` güveni `yuksek` + `medya senkron` ile.
5. **Gizlilik:** mahrem kayıtta döküm metnini açmadan sor; "yalnız sayısal mod"da betik sayılarıyla çalış.
6. Tek mesajda yalnız sonucu değiştiren sorular: müzik kaynağı, iş mi kişisel mi, platform, dış ses metni/sesi.

## Uygulama
1. `medya ses-turu`, `medya ses-olay`: çekim sesi var mı, konuşma/kahkaha nerede.
2. `ses-temizle`'ye `--cikti x.mp4` verme (kare kaybı ölçüldü); WAV'la çalış; kırpmayı `astats` ile ölç (teknikler §2).
3. Müzik: kaynakları [kaynaklar](references/kaynaklar.md) sırasıyla sun. Kısaltma: güven `yuksek` → ölçü başında 20–80 ms ek; `orta`/`dusuk` → bölüm sınırı ya da vokal cümle başı, 0,5–1,5 sn erime, vuruş iddiası yok. Şarkının gerçek sonu = video sonu (ortadan kısalt).
4. Söz–doruk: `medya ayir --iki` → `yaziya-dok vocals.wav --sarki`; satırı kullanıcı seçer, doruk `plan/kurgu.json`'dan; `kisalt.py --esle` (teknikler §3).
5. Kısma: `kisma.py --bas <plan muzik.bas>`; kısılmış WAV ana WAV'ın yerine, aynı `data-start`/`data-media-start` ile.
6. Bitiş: görüntü düzeltmeleri → tık onarımı → `medya ustala` → `medya meta-temizle` (en son; ustala konumu taşır) → `medya denetle`.

## Doğrulama — "bitti" demeden
- `temizlik_olc.py` (hizalama ≤ 1 ms, duraklarda gürültü düştü, 1–4 kHz ±2 dB), `cer.py --kapi temizlik`, `kisma.py` geçti.
- Müzik eki: `kisalt.py olc` geçti, güven düşmedi; söz başı doruğa ±1 kare. Dış ses: CER ≤ %3, 10–18 karakter/sn, konuşmayla ±2 LU.
- Son dosya: `medya denetle` GEÇTİ ve `ses.tik` boş; `cer.py --kapi miks` geçti; kare sayısı kaynakla aynı.
- `denetle --muzik` yalnız güven `yuksek` + vuruş iddiasıyla (kısaltıldıysa `muzik-kisa.json`).
- `av` KALDI = çekim sesi görüntüden kaymış (kaynak başındaki eski araç hatası 2026-10-05'te düzeltildi): düzelt, sonra yeniden ölç.
- Doğrulanamaz: metalik yan ürün, müzik zevki, TTS doğallığı, efekt seviyesi → eşit düzeyli A/B + saniye listesi.

## Sık hatalar
- Türkçe TTS'te Chatterbox PyTorch (~5 GB): önce VoxCPM2 (mlx-audio); macOS `say` yalnız kişisel taslak.
- CER %5 kapısı ya da Türkçe normalleştirmesiz ölçüm ("9'da" = "dokuzda", İ/ı).
- Döküm farkını kapı yapmak; güveni karşılaştır.
- Kısma eşiği uydurmak; tıkı sınırlayıcıya ya da `adeclick`'e bırakmak (ölçüldü: olmuyor).

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/audio-production.md`, `music-sync.md`; eskidiyse `arac-radari`.
