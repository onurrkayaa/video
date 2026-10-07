# Hareket ilkeleri (sayılarla)

Kaynaklar:
- `animation-motion.md` → "Motion-design craft rules" ve "Screen-Studio-style product demo polish".
- Satıcı kuralları: `hyperframes-animation/adapters/gsap-easing-and-stagger.md`, `rules/spring-pop-entrance.md`, `rules/cursor-click-ripple.md`.

Her değer `hyperframes keyframes kompozisyon --json` çıktısındaki süre ve ease ile denetlenir.

## Süreler (saniye → kare)
| Hareket | Süre | 60 fps | 30 fps | Ease |
|---|---|---|---|---|
| Sıkı küçük UI girişi (çip, rozet) | 0,37–0,51 sn | 22–31 | 11–15 | `expo.out` / `power3.out` |
| Standart giriş | 0,51–0,74 sn | 31–44 | 15–22 | `expo.out` |
| Ağır kahraman inişi | 0,74–1,03 sn | 44–62 | 22–31 | `expo.out` |
| Pop (yay) | 0,4–0,7 sn | 24–42 | 12–21 | `back.out(1.4–1.7)` |
| Kademeleme (stagger) | 0,03–0,08 sn | 2–5 | 1–2 | — (grubun toplamı ≤ 0,5 sn) |
| Kamera / punch-in | 0,6–0,9 sn | 36–54 | 18–27 | `power3.inOut` |
| İmleç yolu | 0,4–1,0 sn | 24–60 | 12–30 | `power2.inOut`, kavisli yol |
| Tık basması (yarım, yoyo ×2) | 0,06–0,12 sn | 4–7 | 2–4 | — |
| Tık dalgası | 0,5–1,0 sn | 30–60 | 15–30 | çıkış ease'i |
| Sürekli dönüş | periyot | — | — | `none` (lineer) |

- **Kahraman öğe:** ilk 0,5 sn içinde görünür olmalı.
- **Tık zamanı:** tık, imleç durduktan 0–0,3 sn sonra gelir. Sıfır bekleme otomatik pilot gibi, 0,3 sn'den uzunu tereddüt gibi okunur.
- **Ease ailesi:** parça boyunca tek ease ailesi kullanılır. Lineer yalnız sürekli dönüşte kabul edilir; soğan kabuğunda eşit aralıklı adımlar hata sayılır.
- **Hareket bulanıklığı:** yalnız kare başına en az bir öğe genişliği kadar yer değiştiren harekette kullanılır (`motion-blur` bileşeni ya da `rules/motion-blur-streak.md`).
- **Ritim:** önce hazırlık (anticipation), sonra aşma ve oturma (overshoot, settle).
- **Derinlik:** 2,5B paralaks katmanları, eşleşen kesimler ve whip geçişleri için satıcı geçiş kataloğu kullanılır (`hyperframes-animation/transitions`).

## Ekran görüntüsünden ürün tanıtımı
- **Odak:** her sahnede tek bir odak vardır; kamera ve öğe aynı anda yarışmaz.
- **Okuma payı:** kamera hareketinden sonra izleyiciye okuma süresi bırakılır. Süreyi taslakta kullanıcı onaylar (`medya zamankodu` ile gözden geçirme kopyası).
- **Punch-in:**
  - Eylemin sınır kutusuna yapılır, oran 1,5–2,2x, ease `power3.inOut` (0,6–0,9 sn).
  - Etkileşim boyunca tutulur, sonra geri açılır.
  - **Sınır:** yakınlık ≤ kaynak px / ekrandaki px; aşan oran bulanık yazı demektir.
- **Kamera nesnesi:** kamera hareketi zamanlı klibe değil, bir `.kamera` sarmalayıcısına verilir.
- **İmleç:** sentetik imleç kavisli yoldan gider; tık dalgası eklenir. Bulanıklık yalnız hızlı kaydırmalarda.
- **Blueprint'ler:** `cursor-ui-demo`, `device-surface-showcase`, `zoom-out-workspace-reveal`; logo kapanışı `logo-assemble-lockup`.
- **Kaçınılacaklar:**
  - Tam ekran beyaz ya da siyah flaş kare.
  - Videonun ortasında siyaha düşen geçiş.
  - Aynı anda iki odak hareketi.
- **Yazı yok:** anlatımı arayüzün kendi yazıları, punch-in ve imleç taşır. Özellik adı, slogan ya da URL yalnız istenirse eklenir; o durumda `<html lang="tr">` ve `toLocaleUpperCase('tr-TR')` kullanılır.

## Algoritma anlatımı (ör. Dijkstra)
- **Durum renkleri:** her durum için sabit bir renk kodu seçilir (ziyaret edilmemiş, sınırda, ziyaret edilmiş, en kısa yol) ve baştan sona değişmez.
- **Adım ritmi:** adım başına tek değişiklik yapılır. Kenar gevşetmesi `DrawSVG` ile çizilir; seçilen düğüm pop alır.
- **Etiketler yazıdır:** düğüm harfleri ve mesafe sayıları da ekranda yazıdır, kullanıcıya sorulur. Önerilen: harfler ve sayılar olsun, açıklama cümlesi olmasın.
- **Doğruluk:** her adımın durumu algoritmanın gerçek çalıştırmasından (küçük bir betikten) üretilir. Elle yazılan durum tablosu kullanılmaz.
- **Kapanış 3B logo:** sürekli dönüş lineerdir. Son dönüş `power3.out` ile ön yüze oturur, ardından durgun tutulur. 3B için Three.js; çizimde `--browser-gpu` ve `keyframes --ghost`.

## Döngüler (yükleniyor, çıkartma, README)
- **Periyot:** süre tam N periyottur. Kareler 0 … T − 1/fps arasıdır; T anındaki kare 0. kareyle aynıdır ve dosyaya yazılmaz.
- **Dikiş denetimi:**
  - HyperFrames'te: `snapshot --at 0,T --no-end` ile alınan iki kare piksel piksel aynı olmalı (PIL `ImageChops.difference(...).getbbox()` → `None`).
  - Dosyada: `scripts/dongu.py` çalıştırılır.
- **Web yükleniyor animasyonu:**
  - Tek SVG + CSS `@keyframes`; yalnız `transform` ve `opacity` canlandırılır.
  - Renk `currentColor` ile verilir.
  - `@media (prefers-reduced-motion: reduce)` altında durur ya da yumuşar.
  - `role="status"` ve `aria-label` eklenir. Bu ekran okuyucu içindir, görünür yazı değildir.
  - Önizleme için yalnız CSS'li bir HyperFrames kompozisyonu kurulur: `data-no-timeline`, arka plan `#root`'ta. Seçenekler `hyperframes compare` ile yan yana gösterilir.
- **Native yükleniyor animasyonu:** Lottie/dotLottie ([araçlar](araclar.md)). Video ya da GIF yalnız istenirse verilir.

## Terminal demosu
- **Yazı boyutu:** 1920 genişlikte 28–32 px.
- **Yazma hızı:** karakter başına ~40 ms. Beklemeler gerçek çıktıya göre ayarlanır; tahmini `sleep` kullanılmaz.
- **Boşta süre:** en çok 1 sn (`--idle-time-limit 1`).
- **Kapanış:** son ekran tutulur; GIF 20 fps. Döngü değilse `dongu.py --tek-sefer` ile denetlenir.
- **Arka plan:** zemin `#root`'ta tam dikdörtgen olur. GIF'te saydamlık 1 bittir; beyaz ve koyu README zeminlerinde hale bırakır.

## Müzikle zamanlama
- **Vuruş kaynağı:** vuruşlar yalnız `medya muzik` çıktısından alınır; kare numarası round(t × fps) olarak hesaplanır.
- **Güven kapısı:** güven `yuksek` değilse vurgular bölüm ve cümle sınırlarına konur.
- **Ölçüm:** sonuç `medya senkron` ile ölçülmeden "vuruşa oturdu" denmez. Ses işinin kendisi `ses-tasarimi`ne aittir.
