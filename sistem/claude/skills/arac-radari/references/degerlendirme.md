# Değerlendirme: kapılar, kanıt komutları, rapor

İçindekiler: 1 Başlangıç · 2 Kapı komutları · 3 Ölçüm · 4 Beceri/eklenti/MCP taraması · 5 Rapor

Kanıt kuralı: her iddiaya birincil kaynak (LICENSE dosyası, model kartı, PyPI/npm kaydı, kaynak kodu) ve getirme
tarihi (`date +%F`). Dış isteğe kişisel bilgi, kullanıcı medyası, e-posta girmez; bot koruması aşılmaz. Hız sınırına
takılırsan döngüyle yeniden deneme; kayıt JSON'unu ve ham dosyaları (raw) kullan. Komutlardan önce
`source /Users/onurkaya/Projects/video/ortam.sh`. §1, §2, §4 ve §5 salt okunurdur (gözcü de çalıştırır); §3 deneme
kurulumu ister, yalnız kullanıcı onayıyla.

## 1. Başlangıç
1. Araç adı/bağlantısı ve amacı belli değilse sor: "Hangi model (ad ya da bağlantı), ne için?" Tahminle aday
   dosyası hazırlama.
2. [bilinen-kararlar.md](bilinen-kararlar.md): satır varsa kararı ve "yeniden bak" tetiğini söyle; tetik
   gerçekleşmediyse burada dur.
3. Bu iş zaten bir yetenek mi? `medya yetenekler --saglayicilar`. Öyleyse soru "mevcut sağlayıcıdan iyi mi?" olur.
4. Karşılaştırma tabanı: `sistem/arastirma/` altındaki en yeni tarih; alan dosyasındaki "Şüpheci doğrulama /
   Düzeltmeler" bölümü seçimlerin önüne geçer.

## 2. Kapı komutları

### Erişim ve lisans (kapı 1–2)
Hugging Face modeli — lisans alanı, kapı, upstream, toplam boyut, dosya türleri:
```sh
curl -s "https://huggingface.co/api/models/<kurum>/<depo>?blobs=true" | python3 -c '
import json,sys; d=json.load(sys.stdin); c=d.get("cardData") or {}
print("lisans:", c.get("license"), [t for t in d.get("tags",[]) if t.startswith("license:")])
print("gated:", d.get("gated"), "| base_model:", c.get("base_model"), "| son:", d.get("lastModified"))
s=d.get("siblings",[]); print("toplam MB:", round(sum(x.get("size") or 0 for x in s)/1e6))
print(sorted({x["rfilename"].rsplit(".",1)[-1] for x in s}))'
```
- `gated` false değilse (`auto`, `manual`; ör. meta-llama/Llama-3.2-1B = manual, 2026-10-05) giriş ve onay
  gerekir → kapı 1 hayır.
- Lisans alanı boş olabilir: `mlx-community/whisper-large-v3-turbo` kartında lisans ve base_model yok (2026-10-05);
  upstream `openai/whisper-large-v3-turbo` = mit. Kayda "upstream MIT; yeniden yükleme, alan boş" yaz. Upstream de
  belirsizse araç girmez.
- Lisans metni (siblings içinde LICENSE* varsa): `curl -sL https://huggingface.co/<kurum>/<depo>/raw/main/<dosya> | grep -n -iE "commercial|revenue|territor|output|attribution|non-commercial"`
  — maddeyi satır numarasıyla rapora koy.
- PyPI: `curl -s https://pypi.org/pypi/<paket>/json | python3 -c 'import json,sys; d=json.load(sys.stdin); i=d["info"]; print(i["version"], i.get("license_expression") or i.get("license"), d["urls"][0]["upload_time"] if d["urls"] else "-"); print(i.get("requires_dist"))'`
- npm: `npm view <paket> version license time.modified`
- GitHub: `curl -sL https://raw.githubusercontent.com/<kurum>/<depo>/<dal>/LICENSE | head -20`

Kod ve ağırlık ayrı değerlendirilir: beat_this kod + ağırlık MIT; madmom kodu BSD, modelleri CC BY-NC-SA; MusicGen
ağırlığı CC-BY-NC-4.0. Eğitim verisinin telifli olması kullanımı etkilemez (beat_this README). `kosullu` örnekleri:
GSAP "Standard no-charge" (ticari video serbest, rakip görsel animasyon aracı yasak); Remotion (3 kişiden büyük
kurumda ücretli lisans). Koşulu kayda alıntıyla yaz; kullanıcı iş için de üretir.

### Bu Mac (kapı 3)
- Boş disk: `df -h /Users/onurkaya/Projects/video` (`du` değil: uv klon dosyalarını iki kez sayar).
- Bellek ve ısı: `sysctl vm.swapusage`, `memory_pressure -Q`, `pmset -g therm`. 2026-10-05'te takas 3 GB'ın 1,6'sı
  doluydu; makine fansız MacBook Air.
- Eşik: kurulumdan sonra ≥5 GB + 2 × beklenen çıktı; bir proje ayrıca 5–8 GB çalışma alanı ister.
- Aynı anda tek ağır model ya da çizim; uzun işte `caffeinate -i` ve şarj.
- Yalnız CUDA çekirdeği olan araç → hayır. Satıcının NVIDIA hız/bellek sayısı bu Mac için kanıt değildir.

### Gizlilik (kapı 4)
- Telemetriyi aracın kaynağında ara (kurulu paket: site-packages / node_modules; kurulmamışsa depodaki ham dosya):
  `grep -rniE "posthog|telemetry|analytics|sentry|supabase|DO_NOT_TRACK|DISABLE_TELEMETRY" <dizin> | head`
- Kapatma değişkenini koddan al: mcp-for-blender DO_NOT_TRACK'i yok sayar (`BLENDER_MCP_DISABLE_TELEMETRY`);
  media-use PostHog'u yalnız ortam değişkenleri (`HYPERFRAMES_NO_TELEMETRY=1`, `DO_NOT_TRACK=1`, `CI`) kapatır,
  ayar dosyasındaki `telemetryEnabled:false`'u yok sayar.
  Değişkeni sağlayıcının `not` alanına ve uyarlayıcının ortamına yaz.
- Ağsız çalışma (benimseme denemesinde): `HF_HUB_OFFLINE=1 sandbox-exec -p '(version 1)(allow default)(deny network*)' <komut>`.
  Ağ denemesi "Operation not permitted" ile düşer (2026-10-05'te sınandı); iş tamamlanıyorsa araç çevrimdışıdır.
- Kişisel kareler/ses hiçbir "describe" ya da bulut API'sine gitmez (`hyperframes snapshot` daima `--describe false`).

### Bakım ve ajan uyumu (kapı 5)
Son sürüm tarihi (PyPI `upload_time`, npm `time.modified`, HF `lastModified`); başsız CLI ya da API. Yalnız
arayüzden çizen araç (ör. Motion Canvas) ajan için hayır.

## 3. Ölçüm (kapı 6; deneme kurulumu kullanıcı onayıyla)
- Eşikleri denemeden ÖNCE yaz; sonuç yalnız onlara göre.
- Girdi: `testler/veri/` fikstürleri (üretici `testler/uretec.py`, gerçek değerler `testler/veri/gercek.json`);
  eski ve yeni sağlayıcı aynı girdiyle.
- Süre ve bellek: `/usr/bin/time -l <komut>` → `real` ve `peak memory footprint`; öncesi/sonrası `sysctl vm.swapusage`.
- Kalite ölçütleri stüdyonun sınamalarından: kesim ±1 kare, vuruş ≤40 ms, Türkçe kelime isabeti ≥%90; görüntü
  karşılaştırması kareler doğrudan çözülerek (`testler/test_temel.py` `_kareler`, `_psnr`) — ffmpeg `psnr` süzgeci
  kare kaydırır; VMAF için `arac/ffmpeg` içindeki `libvmaf`.
- Kısa koşu fansız makinede iyimserdir: uzun koşuyu ayrıca ölç ya da "ölçülmedi" yaz.

## 4. Beceri / eklenti / MCP taraması (kurmadan önce ve her güncellemeden sonra)
1. Bütün dosyaları oku: SKILL.md, scripts/, hooks, `.mcp.json`.
2. İki tarama — ilki kabuk enjeksiyonu, ön onaylı araç ve oturum kancası; ikincisi hesap, dış istek ve
   sabitlenmemiş paket arar:
~~~sh
grep -rnE '(^|[[:space:]])!`|^```!|allowed-tools|^hooks:' <dizin>
grep -rnoE 'hyperframes (usage|feedback|auth|publish|cloud|lambda|cloudrun)|posthog|@latest|API_KEY' <dizin>
~~~
   2026-10-05: `~/.claude/skills/hyperframes*`, `media-use`, `music-to-video` üzerinde ilki boş döner; ikincisi
   `usage --json`, `feedback`, `cloud`, `@latest` satırlarını bulur. Her bulguyu kanca ve `medya-studyo` yönlendirmesi karşılıyor mu, bak.
3. Topluluk dizinlerinden (skillsmp, mcp.film, glama…) denetlenmemiş beceri kurma; resmî depo + sürüm ya da commit sabitle,
   `sistem/claude/satici/KAYNAKLAR.md`'ye yaz ([güncelleme](guncelleme-ve-disk.md) §3.7).

## 5. Rapor
- Yol: `sistem/radar/<YYYY-AA-GG>-<konu>.md` (`date +%F`).
- Bölümler: karar (benimse | izle | reddet); kapı tablosu (kapı | sonuç | kanıt URL | tarih); ölçümler (komut +
  sayı); önerilen `[[saglayici]]` ([benimseme](benimseme.md) §1 biçimi); uyarlayıcı ve sınama taslağı; riskler;
  yeniden bakma tetiği.
- Kullanıcıya Türkçe kısa tablo: araç | indirme | lisans/ticari | bu Mac'e sığar mı | karar. Sonra tek soru
  (ör. "X GB indirip ölçümlü deneyeyim mi?"). Kurulum kararı kullanıcınındır.
- Red kararını [bilinen-kararlar.md](bilinen-kararlar.md)'ye bir satır olarak ekle.
