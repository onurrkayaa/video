"""HyperFrames ↔ medya ciz karşılaştırması için fikstür, plan ve kompozisyon (yalnız sayısal; kare açılmaz).
Gerçek çekim: deneme kaynağının (4096x2160 HEVC 60 fps) 1920x1080 kesiti, ölçeklenmeden (iki motor da ölçek yapmasın:
fark yalnız boru hattının kaybı olsun), x264 CRF 6 60 fps. Plan 10 sn 1920x1080 30 fps: 3 kesim + 12 karelik erime."""
import json, shutil, subprocess, sys
from pathlib import Path
K = Path("/Users/onurkaya/Projects/video")
D = Path(sys.argv[1]); (D / "plan").mkdir(parents=True, exist_ok=True); (D / "kaynak").mkdir(exist_ok=True)
FF = str(K / "arac/ffmpeg")
fik = D / "kaynak" / "gercek1080.mp4"
if not fik.exists():
    subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(K / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"),
                    "-t", "22", "-vf", "crop=1920:1080:1088:540", "-c:v", "libx264", "-crf", "6", "-preset", "medium", "-g", "60",
                    "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-color_range", "tv", "-an", str(fik)], check=True)
muzik = D / "kaynak" / "muzik.wav"
shutil.copy(K / "projeler/2026-10-08-nle-sinama/kaynak/muzik.wav", muzik)
kes = {"tur": "kesim", "sure_kare": 0}
C = [{"no": 1, "kaynak": "kaynak/gercek1080.mp4", "kaynak_bas": 1.0, "cikti_bas": 0, "cikti_son": 2.5, "gecis": kes},
     {"no": 2, "kaynak": "kaynak/gercek1080.mp4", "kaynak_bas": 8.0, "cikti_bas": 2.5, "cikti_son": 5.0, "gecis": kes},
     {"no": 3, "kaynak": "kaynak/gercek1080.mp4", "kaynak_bas": 14.0, "cikti_bas": 4.6, "cikti_son": 7.5,
      "gecis": {"tur": "erime", "sure_kare": 12}},
     {"no": 4, "kaynak": "kaynak/gercek1080.mp4", "kaynak_bas": 18.0, "cikti_bas": 7.5, "cikti_son": 10.0, "gecis": kes}]
for c in C:
    c.update(hiz=1, ses="muzik", vurusa=False)
plan = {"ad": "karsilastirma", "fps": 30, "boyut": [1920, 1080], "sure": 10.0,
        "muzik": {"dosya": "kaynak/muzik.wav", "bas": 0}, "cekimler": C}
(D / "plan" / "kurgu.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
# HyperFrames kompozisyonu (kurgu-zanaati kompozisyon.md yapısı; erime eğrisi plandaki gibi doğrusal: ease "none")
k = D / "kompozisyon"; (k / "medya").mkdir(parents=True, exist_ok=True)
shutil.copy(K / "varliklar/js/gsap.min.js", k / "gsap.min.js")
for f in (fik, muzik):
    (k / "medya" / f.name).unlink(missing_ok=True); (k / "medya" / f.name).symlink_to(f)
kat = []
for c in C:
    d = round((c["cikti_son"] - c["cikti_bas"]) * 30) / 30
    kat.append(f'  <div class="kat" id="k{c["no"]}" style="z-index:{c["no"]}"><div class="ic" id="i{c["no"]}">\n'
               f'    <video id="c{c["no"]}" class="clip" src="medya/gercek1080.mp4" muted playsinline data-start="{c["cikti_bas"]:.6f}" '
               f'data-duration="{d:.6f}" data-media-start="{c["kaynak_bas"]:.6f}" data-track-index="{c["no"]}"></video></div></div>')
html = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><script src="gsap.min.js"></script>
<style>
html,body{{margin:0;background:#000}}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden;background:#000}}
.kat{{position:absolute;inset:0;overflow:hidden}}
.ic{{position:absolute;inset:0}}
.ic video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
</style></head><body>
<div id="root" data-composition-id="kurgu" data-start="0" data-width="1920" data-height="1080" data-duration="10">
{chr(10).join(kat)}
  <audio id="muzik" src="medya/muzik.wav" data-start="0" data-duration="10" data-media-start="0" data-track-index="10"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#k3", {{opacity:0}}, {{opacity:1, duration:12/30, ease:"none"}}, 138/30);
window.__timelines["kurgu"] = tl;
</script>
</body></html>
"""
(k / "index.html").write_text(html)
print(D)
