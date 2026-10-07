"""medya zamankodu <video> [--cikti x.mp4] — gözden geçirme taslağı: köşeye dakika:saniye.kare yazılı küçük kopya.

Kullanıcı taslağı izleyip geri bildirimi "0:12.15 → şu geçiş sert" biçiminde verebilsin diye. Teslim dosyası
DEĞİLDİR (yazı içerir); adı -taslak-zk.mp4 olur. Görüntü 720 px'e küçültülür, ses aynen kalır.
"""
from __future__ import annotations

from pathlib import Path

from ..ortak import calistir, ffmpeg, oran, probe, video_akisi

YAZI = "/System/Library/Fonts/Supplemental/Arial.ttf"


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + "-taslak-zk.mp4"))
    v = video_akisi(probe(args.girdi)) or {}
    fps = oran(v.get("avg_frame_rate")) or 30.0
    w, h = int(v.get("width", 1280)), int(v.get("height", 720))
    olcek = "scale=720:-2" if w >= h else "scale=-2:720"
    metin = (f"drawtext=fontfile={YAZI}:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8:x=16:y=16:"
             f"text='%{{eif\\:floor(t/60)\\:d}}\\:%{{eif\\:mod(floor(t)\\,60)\\:d\\:2}}.%{{eif\\:mod(n\\,{round(fps)})\\:d\\:2}}'")
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", args.girdi, "-vf", f"{olcek},{metin}", "-c:v", "libx264",
              "-crf", "23", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
              "-movflags", "+faststart", cikti], hata_mesaji="zaman kodlu taslak üretilemedi")
    print(f"gözden geçirme taslağı (teslim değil) → {cikti}")
    print("  kullanıcıdan geri bildirimi 'dk:sn.kare → not' biçiminde iste")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="zaman kodlu gözden geçirme taslağı")
    p.add_argument("girdi")
    p.add_argument("--cikti")
    p.set_defaults(islev=calistir_)
