"""4K HEVC → 1080x1920 dikey karşılaştırma: aynı plan, ciz ve HyperFrames (kadraj = object-position formülü, Ken Burns =
.ic ölçeği, transform-origin = ilginin ekrandaki yeri, eğri plandan). Yalnız sayısal."""
import json, shutil, sys
from pathlib import Path
K = Path("/Users/onurkaya/Projects/video")
D = Path(sys.argv[1]); (D / "plan").mkdir(parents=True, exist_ok=True); (D / "kaynak").mkdir(exist_ok=True)
src = D / "kaynak" / "IMG_4021.MOV"
if not src.exists():
    src.symlink_to(K / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV")
shutil.copy(K / "projeler/2026-10-08-nle-sinama/kaynak/muzik.wav", D / "kaynak" / "muzik.wav")
kes = {"tur": "kesim", "sure_kare": 0}
C = [{"no": 1, "kaynak_bas": 1.0, "cikti_bas": 0, "cikti_son": 2.5, "gecis": kes, "kadraj": {"ilgi": [0.743, 0.32], "mod": "sabit"},
      "hareket": {"tur": "kenburns", "olcek": [1.0, 1.05]}},
     {"no": 2, "kaynak_bas": 6.0, "cikti_bas": 2.5, "cikti_son": 5.0, "gecis": kes, "kadraj": {"ilgi": [0.246, 0.9], "mod": "sabit"}},
     {"no": 3, "kaynak_bas": 10.0, "cikti_bas": 4.6, "cikti_son": 7.5, "gecis": {"tur": "erime", "sure_kare": 12},
      "kadraj": {"ilgi": [0.4655, 0.61], "mod": "sabit"}},
     {"no": 4, "kaynak_bas": 15.0, "cikti_bas": 7.5, "cikti_son": 10.0, "gecis": kes, "kadraj": {"ilgi": [0.08, 0.56], "mod": "sabit"},
      "hareket": {"tur": "kenburns", "olcek": [1.0, 1.08], "egri": "sine.inOut"}}]
for c in C:
    c.update(kaynak="kaynak/IMG_4021.MOV", hiz=1, ses="muzik", vurusa=False)
plan = {"ad": "dikey", "fps": 30, "boyut": [1080, 1920], "sure": 10.0, "muzik": {"dosya": "kaynak/muzik.wav", "bas": 0}, "cekimler": C}
(D / "plan" / "kurgu.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
Ws, Hs, Wc, Hc = 4096, 2160, 1080, 1920
k_ = max(Wc / Ws, Hc / Hs); ww, wh = Wc / k_, Hc / k_
def P(i, S, C_):
    o = S * k_
    return min(1.0, max(0.0, (i * o - C_ / 2) / (o - C_))) if o - C_ > 1e-9 else 0.5
k = D / "kompozisyon"; (k / "medya").mkdir(parents=True, exist_ok=True)
shutil.copy(K / "varliklar/js/gsap.min.js", k / "gsap.min.js")
for f in (src, D / "kaynak" / "muzik.wav"):
    (k / "medya" / f.name).unlink(missing_ok=True); (k / "medya" / f.name).symlink_to(f.resolve())
kat, tween = [], []
for c in C:
    ix, iy = c["kadraj"]["ilgi"]
    px, py = P(ix, Ws, Wc), P(iy, Hs, Hc)
    X0, Y0 = (Ws - ww) * px, (Hs - wh) * py
    ax, ay = (ix * Ws - X0) / ww, (iy * Hs - Y0) / wh
    bas, son = round(c["cikti_bas"] * 30), round(c["cikti_son"] * 30)
    kat.append(f'  <div class="kat" id="k{c["no"]}" style="z-index:{c["no"]}"><div class="ic" id="i{c["no"]}" '
               f'style="transform-origin:{100 * ax:.6f}% {100 * ay:.6f}%"' + (' data-layout-allow-overflow' if c.get("hareket") else '') + '>\n'
               f'    <video id="c{c["no"]}" class="clip" src="medya/IMG_4021.MOV" muted playsinline style="object-position:{100 * px:.6f}% {100 * py:.6f}%" '
               f'data-start="{bas / 30:.6f}" data-duration="{(son - bas) / 30:.6f}" data-media-start="{c["kaynak_bas"]:.6f}" data-track-index="{c["no"]}"></video></div></div>')
    h = c.get("hareket")
    if h:
        a, b = h["olcek"]
        tween.append(f'tl.fromTo("#i{c["no"]}", {{scale:{a}}}, {{scale:{b}, duration:{son - 1 - bas}/30, ease:"{h.get("egri", "none")}"}}, {bas}/30);')
tween.append('tl.fromTo("#k3", {opacity:0}, {opacity:1, duration:12/30, ease:"none"}, 138/30);')
html = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><script src="gsap.min.js"></script>
<style>
html,body{{margin:0;background:#000}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}}
.kat{{position:absolute;inset:0;overflow:hidden}}
.ic{{position:absolute;inset:0}}
.ic video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
</style></head><body>
<div id="root" data-composition-id="kurgu" data-start="0" data-width="1080" data-height="1920" data-duration="10">
{chr(10).join(kat)}
  <audio id="muzik" src="medya/muzik.wav" data-start="0" data-duration="10" data-media-start="0" data-track-index="10"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tween)}
window.__timelines["kurgu"] = tl;
</script>
</body></html>
"""
(k / "index.html").write_text(html)
print(html[html.find("<div id=\"root\""):html.find("</script>\n</body>")][-900:])
