# Kurguyu HyperFrames'te kurmak

Motor başvurusu: `hyperframes-core` (sözleşme), `hyperframes-keyframes` (punch-in, Ken Burns, kadraj yolu),
`hyperframes-registry` (geçiş blokları). Burada yalnız gerçek çekim kurgusuna özgü kurallar var.

## Klasör
```sh
K=calisma/kompozisyon; mkdir -p $K/medya
cp $MEDYA/varliklar/js/gsap.min.js $K/                    # ağdan betik yok
ln -s ../../../kaynak/IMG_0433.MOV $K/medya/IMG_0433.MOV   # medya kompozisyon klasörü İÇİNDEN görünmeli
ln -s ../../klipler/IMG_0420-yavas025.mp4 $K/medya/
ln -s ../../ses/muzik.wav $K/medya/
```
`src="../…"` lint hatasıdır ve çizim görüntüyü atlar; bağlantı (symlink) çalışır (sınandı).

## Yapı (sınandı: lint 0 hata, taslak çizildi)
```html
<html lang="tr"> … <script src="gsap.min.js"></script>
<style>
#root{position:relative;width:100%;height:100%;overflow:hidden;background:#000}
.kat{position:absolute;inset:0;overflow:hidden}          /* zamansız: z-index + opaklık (erime, dip) */
.ic{position:absolute;inset:0}                           /* zamansız: GSAP scale/x/y (punch, Ken Burns, kadraj) */
.ic video,.ic img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
</style>
<div id="root" data-composition-id="kurgu" data-start="0" data-width="1080" data-height="1920" data-duration="60">
  <div class="kat" id="k2" style="z-index:2"><div class="ic" id="i2">
    <video id="c2" class="clip" src="medya/IMG_0420-yavas025.mp4" muted playsinline
           data-start="4.266667" data-duration="3.2" data-media-start="0" data-track-index="1"></video></div></div>
  <div class="kat" id="k3" style="z-index:3"><div class="ic" id="i3">
    <video id="c3" class="clip" src="medya/IMG_0433.MOV" data-has-audio="true" playsinline
           data-start="6.866667" data-duration="4.133333" data-media-start="8" data-track-index="2"></video></div></div>
  <audio id="muzik" src="medya/muzik.wav" data-start="0" data-duration="60" data-media-start="0" data-track-index="10"></audio>
</div>
<script>
const tl = gsap.timeline({ paused: true });
tl.fromTo("#i2", {scale:1}, {scale:1.1, duration:3/30, ease:"expo.out"}, 128/30);   // punch, vuruşta
tl.fromTo("#k3", {opacity:0}, {opacity:1, duration:18/30, ease:"sine.inOut"}, 206/30); // erime: yalnız GELEN açılır
window.__timelines["kurgu"] = tl;
</script>
```
- Değerleri elle yazma; plandan üret (her zaman `k/fps`). Zamanlı öğenin atasında `data-start` olmaz (lint hatası);
  animasyon zamansız sarmalayıcıda, zamanlı `<video>`da değil.
- Eğri, çapa ve uçlar plandan ([plan şeması](plan-semasi.md) "Kadraj, hareket ve erime anlamı"): `ease` = `gecis.egri` /
  `hareket.egri` (yoksa `"none"`), `.ic` `transform-origin` = ilginin ekrandaki yeri, kenburns `fromTo` süresi
  (son kare − ilk kare)/fps. Böylece `medya ciz` aynı plandan aynı hareketi çizer (ölçüldü: Ken Burns ≤ 0,2 px).
- Erime: gelen `.kat` üstte, opaklık 0→1; giden kararmaz (parlaklık çukuru olmaz). Siyah/beyaz dip: siyah/beyaz katmanın
  opaklığı. Tek, duraklatılmış zaman çizelgesi; `Math.random`/`Date` yok.
- `data-playback-rate` yalnız `> 1` hızlandırmada; `< 1` kare tekrarlar (ölçüldü: 0,5x'te yinelenen kare %48).
- Fotoğraf: `<img id="c<no>">`. HEIC tarayıcıda ve ffmpeg 6.0'da açılmaz: `sips -s format jpeg x.heic --out calisma/klipler/x.jpg`.
- Kadraj (yatay → dikey, sabit mod): `object-position: P% 50%`, `P = clamp((x·Wö − Wç/2)/(Wö − Wç), 0, 1)·100`;
  `x` = `ilgi_merkezi[0]`, `Wö` = kaynağın çıktı yüksekliğine ölçeklenmiş genişliği, `Wç` = çıktı genişliği.
  Hareketli özne: `.ic`'te x anahtar kareleri (`hyperframes-keyframes`), yumuşatılmış ve kesimde sıfırlanır.
- Geçiş bloğu: `hyperframes catalog --tag transition --json` → `hyperframes add <ad>` → `hyperframes-registry` ile bağla.
  `catalog --on-device` (model indirir; boyutu söyleyip sormadan değil) ve `feedback --search-miss` (feedback engelli)
  kullanma. `add` yalnız `--dir/--json/--vars/--force/--clipboard` alır.

## Denetim ve çizim
```sh
hyperframes lint calisma/kompozisyon                                    # 0 hata
hyperframes check calisma/kompozisyon --at-transitions
hyperframes snapshot calisma/kompozisyon --describe false --at 4.27,6.9,7.2 --output analiz/snap   # → Read (izin varsa)
df -h .                                                                 # çizimden önce
hyperframes render calisma/kompozisyon --sdr -q draft --frames-cache-dir off -o calisma/taslak.mp4
# SON (gerçek çekim, ≤ 1080p kaynak): PNG ara kare (VMAF 95,0 → 96,6; ~2 kat süre); bit hızı hedefi teslim-denetimi'nden
caffeinate -i hyperframes render calisma/kompozisyon --sdr -q delivery --video-frame-format png --frames-cache-dir off --video-bitrate 12M -o calisma/usta.mp4
# 4K kaynakta PNG çöktü (5 işçi, takas 0,9 → 15,9 GB; 2026-10-08) → JPEG + tek işçi (35,8 sn, 0,37 GB) ya da klipleri önce
# teslim boyutuna indir; yazısız gerçek çekim kurgusunda zaten `medya ciz` (VMAF 96,2, disk 0,02 GB)
caffeinate -i hyperframes render calisma/kompozisyon --sdr -q delivery --workers 1 --frames-cache-dir off --video-bitrate 12M -o calisma/usta.mp4
```
- `-q delivery` yalnız USTA içindir (sonra `teslim-denetimi` → `teslim.py kodla` platforma kodlar). Doğrudan teslim
  çiziminde `-q standard`: delivery 1080x1920'de H.264 seviye 5.0 verir, dikey teslim kapısından KALIR (uçtan uca sınama).
- `--sdr` yalnız güvenlik ağıdır: HyperFrames'in hable zincirini uygular. HDR (HLG/PQ) kaynak kompozisyona girmez;
  önce `medya sdr` klibi (`plan_denetle` HDR aslı ✗ verir).
- `--frames-cache-dir` projeye taşınınca yer kazandırmaz (aynı disk) → `off`. Varsayılan CRF 16 uzun grenli videoda
  devasa (4:48 → 2,5 GB) → `--video-bitrate`. Ağır işleri sırayla çalıştır.
- B-roll üstünde röportaj sesi (J/L de böyle): b-roll çekimi planda `ses: sessiz`; konuşma ayrı
  `<audio id="s<no>" src="medya/<röportaj kaynağı>">` ile sürer (`data-start` = b-roll başı, `data-media-start` =
  röportajın o andaki kaynak saniyesi, ikisi de k/fps). Plan bu sesi bilmez: `plan_denetle` yalnız ızgara ve yolunu
  denetler, `medya nle` taşımaz → KARARLAR.md'ye yaz, Resolve'a devirde kullanıcıya söyle.
- Müzik tek, sürekli bir `<audio>`; ses parça parça kodlanıp birleştirilmez (AAC başlangıç gecikmesi birikir:
  segment başına ~24 ms ffmpeg, ~67 ms Apple).
- Kare dökmeyen yol: `medya ciz plan/kurgu.json` (kesim, erime, sabit kadraj, punch/Ken Burns, kendi sesi + müzik;
  motor seçimi SKILL.md). Elle `xfade`/`concat`/`zoompan` zinciri kurma: concat → xfade → concat erimeden sonra +1 kare
  kaydırdı, `zoompan` tam piksele yuvarlayıp titrer (p95 0,94 px; ölçüldü).
