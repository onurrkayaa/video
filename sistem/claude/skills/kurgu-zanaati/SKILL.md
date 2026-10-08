---
name: kurgu-zanaati
description: Use when real footage or photos must be edited into a video (personal montage, gift or vacation edit, reel, interview or testimonial cut), or when shot order, pacing to music or speech, transitions, punch-ins, Ken Burns, slow motion, speed ramps, 16:9/9:16 reframing, stabilization, color matching or a DaVinci/Kdenlive handoff is needed (kurgu, montaj, sırala, geçiş, yakınlaştırma, ağır çekim, dikey yap, röportaj kurgusu, Resolve'a aktar).
---

# Kurgu zanaatı

Gerçek çekimden kurgu: seç → sırala → müziğe/konuşmaya oturt → geçiş ve hareket → ölç.
**İlke:** tek gerçek kaynak `plan/kurgu.json` ([plan şeması](references/plan-semasi.md)); her zaman k/fps ızgarasında;
her iddia ölçümle. İstenmedikçe ekrana yazı yok. Proje kökünde:
`source /Users/onurkaya/Projects/video/ortam.sh; P=$MEDYA/.venv/bin/python; K=$MEDYA/sistem/claude/skills/kurgu-zanaati/scripts`

## Ne zaman / değil
- **Ne zaman:** seçki, sıra, ritim, geçiş, punch-in, Ken Burns, paralaks, ağır çekim, kadraj, sabitleme, renk, NLE.
- **Değil:** miks, ducking, müzik kısaltma, ustalık → `ses-tasarimi`; sıfırdan animasyon/yazı → `hareket-tasarimi`; görsel üretimi → `gorsel-uretim`; teslim eşikleri → `teslim-denetimi`; yönlendirme → `medya-studyo`.

## Önce sor (yalnız sonucu değiştirenler)
Kişisel klipte kare açmadan gizlilik (yoksa yalnız sayısal mod); en-boy, süre, olmazsa olmaz anlar; herkese açıksa
telifli şarkı ve kişilerin rızası; iş videosunda ticari lisanslı müzik.

## Hızlı başvuru (çıktı yolunu hep ver)
| İş | Komut |
|---|---|
| Künye | `medya incele kaynak/* --json analiz/kunye.json` |
| Görmek | `medya kontak X --cikti analiz/kontak/<ad>.png` → Read (HDR soluk görünür) |
| Seçki | `medya sahneler X --json analiz/sahneler/<ad>.json`; `medya analiz X --sahneler … --cikti analiz/vision/<ad>.json` |
| Çekim sesi olayları | `medya ses-olay X --cikti …` (ilke 4 ham klipte: `ses: kendi`; `ses-turu` kurgulanmışta) |
| Konuşma | `medya yaziya-dok X --dil tr --cikti analiz/yazi/<ad>.json` |
| Alt yazı (yalnız istenirse) | aynı komuta `--srt`; HyperFrames'e indirmesiz `hyperframes transcribe analiz/yazi/<ad>.srt -d calisma/kompozisyon` (işaret düzeyi; kelime zamanı: medya-studyo "Alt yazı istenirse"). Satıcı altyazı akışını çalıştırma: sormadan indirir, kanca engeller |
| Müzik | `medya muzik … --cikti analiz/muzik.json` → `guven_seviye` |
| HDR / VFR | `medya sdr` / `medya cfr` `--cikti calisma/klipler/…` |
| Ağır çekim | `medya yavaslat X --hiz 0.5 --bas A --sure S [--kirp x,y,gen,yük --olcek 1080x1920] --cikti calisma/klipler/<ad>-yavas.mp4` (HyperFrames; yalnız NLE devrine `.mov` ProRes). Kırpma payı: [teknikler](references/teknikler.md) Hız |
| Rampa (gerçek yüksek fps) | `$P $K/rampa.py X --hiz 0.25 --a … --d … --cikti calisma/klipler/<ad>-rampa.mp4` |
| Titreme | `$P $K/titreme.py X` (önce/sonra) |
| Plan denetimi | `$P $K/plan_denetle.py plan/kurgu.json [--html …] [--denetim …]` |
| Çizim, gerçek çekim | `medya ciz plan/kurgu.json [--cikti cikti/<ad>.mp4] [--crf 16]` — kesim, erime, sabit kadraj, punch/Ken Burns, hazır klipler, `hiz > 1`, kendi sesi + müzik; kare dökmez. Kısma: `--yalniz-konusma calisma/ses/konusma.wav` → ses-tasarimi `kisma.py` → kısılmış WAV `muzik.dosya` |
| Geri bildirim taslağı | `medya zamankodu calisma/taslak.mp4 --cikti calisma/taslak-tc.mp4` |
| Resolve / Kdenlive | `medya nle plan/kurgu.json --bicim hepsi` → `cikti/nle/kurgu.otio` (Resolve) · `kurgu-kdenlive.otio` (Kdenlive) |

## Akış
1. `medya proje yeni "<ad>" --tur video --kaynak <dosyalar>`; BRIEF.
2. Künye, kontak, sahneler, analiz, ses-olay; müzik kesiti + analiz (önerilen `bas: 0`).
3. Seçki → stringout (sıralı kontak + tablo) → **kullanıcı onayı** → kaba → ince kurgu: [teknikler](references/teknikler.md).
4. Ara klipler `calisma/klipler/`e (sdr, cfr, yavaslat, rampa, sabit); asıllara dokunma.
5. `plan/kurgu.json` → `plan_denetle` GEÇTİ → motor: plan yalnız `medya ciz` kapsamındaysa `medya ciz` (taslak `--crf 28 --preset veryfast`), yazı/grafik/süslü geçiş/dip/J-L/fotoğraf varsa kompozisyon ([kompozisyon](references/kompozisyon.md)) → taslak → ölç → `zamankodu` taslağıyla notlar → son çizim (HyperFrames'te `--video-frame-format png`).
6. Bitirme: görüntü düzeltmesi → ses onarımı → `medya ustala` → `medya meta-temizle` EN SON → `medya denetle`.

## Kesin kurallar
- Vuruşa kesim/punch yalnız `guven_seviye: yuksek` (akustikte nadir); kare `floor(vuruş·fps)`. Değilse bölüm/cümle sınırı + erime, `vurusa: false`, iddia yok.
- Sabit BPM ızgarası, `hyperframes beats`: yasak.
- Ağır çekim yalnız `medya yavaslat` (`--yontem` verme; motoru o seçer); `data-playback-rate` < 1 yasak; yavaşta çekim sesi yok.
- Çoğu kesim düz; bir ana geçiş + ≤ 2 vurgu, hepsi motivasyonlu.
- Tek karelik flaş/siyah kare silinmez, önceki karenin kopyası olur.
- Sabitleme yalnız ölçülmüş titremede (+kontak); `Final zoom` KARARLAR'a.
- Etkin ölçek (cover × punch × sabitleme) ≤ 1,15: 4K yatay → dikey punch ≤ 1,29; 1080p yatay → dikey punch yok, söyle.
- HDR asıl kompozisyona girmez: `medya sdr` klibi (`--sdr` hable uygular).
- Gerçek çekim kurgusunda önce `medya ciz`: kare dökmez, kare-kesin (4K → 1080x1920 10 sn: disk tepesi 0,02 GB; aynı
  plan HyperFrames PNG kipinde 3,5 GB kare + takas 0,9 → 15,9 GB ile çöktü, 2026-10-08). Kapsam dışı öğeyi sessizce
  kesime çevirmez, hata verir → HyperFrames. İki motor aynı planı aynı geometriyle çizer ([plan şeması](references/plan-semasi.md)).

## Doğrulama (bitti demeden)
1. `plan_denetle` (+`--html`, çizimden sonra `--denetim`) GEÇTİ; `hyperframes lint` 0 hata.
2. Kesim anlarında `medya kontak X --anlar … --genislik 360` → Read (izin varsa).
3. Güven yüksekse `medya senkron X --muzik … --plan …` `vurusta`; plansızda yalnız `vurusa: true` kesimler eşikte.
4. Ağır çekim aralığında `$P $K/yinelenen.py X --bas A --sure S` ≤ %3.
5. `medya denetle` GEÇTİ (`--muzik` yalnız güven yüksekse; eşikler `teslim-denetimi`).
Ayrıntı: [doğrulama](references/dogrulama.md). **Ölçülemez:** duygusal etki, akış, ağır çekimin doğallığı, ses → izlenecek saniyeleri ver.

## Sık hatalar
- Kendi şeman (`cikti.genislik`, `ara`, `ses: yok`, negatif `bas`): araçlar okumaz.
- Özel kurgu/rampa üreteci; `medya.ortak` iç fonksiyonları; `round()` ile kesim karesi.
- Önbelleği projeye taşımak (`--frames-cache-dir off`); `meta-temizle`yi `ustala`dan önce; zamankodu taslağını teslim etmek.
- İstenmeden yazı, bulanık dolgu, her kesimde başka geçiş.

Bilgi tarihi 2026-10-05; kanıt: `sistem/arastirma/2026-10-05/editing-craft.md` (+ video-framework.md, music-sync.md, footage-analysis.md); eskidiyse `arac-radari`.
