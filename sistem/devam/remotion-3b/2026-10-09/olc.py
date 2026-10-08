"""E3 ölçümü (2026-10-09): Remotion 4.0.533 + @remotion/three / @remotion/lottie şablon örnekleri.

1. gl seçeneklerinin her birinde sayfanın WebGL sürücüsü (şablonun ayarı 'angle', ayarsız varsayılan ve --gl=…).
2. Ornek3B (90 kare, 1080x1920) mp4 çizim süresi: çalışan her gl seçeneğinde.
3. Belirlenimcilik: 'angle' ile iki ayrı PNG dizisi kare kare; 'swangle' (CPU) ile fark.
4. Şablonda 3B/Lottie kayıtlıyken ve değilken 'Ornek' çizim süresi (paket yükü).
5. Lottie: 1 Remotion karesi = 1 Lottie karesi mi (fr 30 ve 60 aynı karede aynı görüntü mü).
6. Ağ kapalıyken (yalnız localhost açık, sandbox-exec) iki örnek çiziliyor mu.

Çalıştır: source ortam.sh && .venv/bin/python <bu dosya> <çıktı.json>   (stüdyo kökünden; ~1,5 dk)
Kopyalar testler/.gecici/e3-olcum/ altında (modüller stüdyo kökünden çözülsün diye ağaç içinde); sonunda silinir.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(os.environ["MEDYA"])
RM = KOK / "node_modules" / ".bin" / "remotion"
G = KOK / "testler" / ".gecici" / "e3-olcum"
SONUC: dict = {"tarih": time.strftime("%Y-%m-%d %H:%M"), "chrome": None}

OLCUM_INDEX = """import {registerRoot} from 'remotion';
import {OlcumKok} from './OlcumKok';

registerRoot(OlcumKok);
"""
OLCUM_KOK = """import {useEffect, useRef, useState} from 'react';
import {AbsoluteFill, Composition, continueRender, delayRender} from 'remotion';

// Sayfanın WebGL sürücü adını PNG'nin ilk satırına karakter kodu olarak yazar (console.log çizim günlüğünde görünmedi).
const GlBilgi: React.FC = () => {
	const tuval = useRef<HTMLCanvasElement>(null);
	const [bekle] = useState(() => delayRender('gl bilgisi'));
	useEffect(() => {
		const c = document.createElement('canvas');
		const gl = (c.getContext('webgl2') || c.getContext('webgl')) as WebGLRenderingContext | null;
		let metin = 'webgl-yok';
		if (gl) {
			const ext = gl.getExtension('WEBGL_debug_renderer_info');
			metin = `${gl.getParameter(gl.VERSION)} | ${ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)}`;
		}
		const ctx = tuval.current!.getContext('2d')!;
		const img = ctx.createImageData(512, 1);
		for (let i = 0; i < Math.min(metin.length, 511); i++) {
			const k = metin.charCodeAt(i) & 255;
			img.data.set([k, k, k, 255], i * 4);
		}
		ctx.putImageData(img, 0, 0);
		continueRender(bekle);
	}, [bekle]);
	return (
		<AbsoluteFill style={{background: 'black'}}>
			<canvas ref={tuval} width={512} height={2} style={{position: 'absolute', left: 0, top: 0}} />
		</AbsoluteFill>
	);
};

export const OlcumKok: React.FC = () => (
	<Composition id="GlBilgi" component={GlBilgi} durationInFrames={1} fps={30} width={512} height={2} />
);
"""


def kos(klasor: Path, *arg: str, zaman_asimi: int = 300, on: tuple[str, ...] = ()) -> dict:
    t0 = time.perf_counter()
    try:
        r = subprocess.run([*on, str(RM), *arg, "--log=error"], cwd=klasor, capture_output=True, text=True,
                           timeout=zaman_asimi)
        kod, hata = r.returncode, (r.stderr + r.stdout)[-600:]
    except subprocess.TimeoutExpired:
        kod, hata = "zaman_asimi", f"{zaman_asimi} sn"
    return {"kod": kod, "sure_sn": round(time.perf_counter() - t0, 2), **({"hata": hata} if kod != 0 else {})}


def gl_metni(png: Path) -> str:
    satir = np.asarray(Image.open(png).convert("RGB"))[0, :, 0]
    son = int(np.argmax(satir == 0)) if (satir == 0).any() else len(satir)
    return "".join(chr(int(k)) for k in satir[:son])


def png_dizisi(klasor: Path) -> list[np.ndarray]:
    return [np.asarray(Image.open(p).convert("RGB"), dtype=np.int16) for p in sorted(klasor.glob("*.png"))]


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(np.mean((a.astype(float) - b.astype(float)) ** 2))
    return round(10 * np.log10(255 ** 2 / mse), 2) if mse > 0 else float("inf")


def main() -> None:
    cikti = Path(sys.argv[1])
    shutil.rmtree(G, ignore_errors=True)
    G.mkdir(parents=True)
    yeni = G / "yeni"
    shutil.copytree(KOK / "sablonlar" / "remotion", yeni)
    (yeni / "src" / "olcum").mkdir()
    (yeni / "src" / "olcum" / "index.ts").write_text(OLCUM_INDEX)
    (yeni / "src" / "olcum" / "OlcumKok.tsx").write_text(OLCUM_KOK)
    varsayilan = G / "varsayilan"                         # gl satırı yok: Remotion 4.0.533 varsayılanı (null)
    shutil.copytree(yeni, varsayilan)
    ayar = (varsayilan / "remotion.config.ts").read_text()
    (varsayilan / "remotion.config.ts").write_text(re.sub(r"^Config\.setChromiumOpenGlRenderer.*$", "", ayar,
                                                          flags=re.M))
    eski = G / "eski"                                     # 3B/Lottie kayıtsız Kok.tsx (HEAD'deki)
    shutil.copytree(KOK / "sablonlar" / "remotion", eski)
    (eski / "src" / "Kok.tsx").write_text(subprocess.run(["git", "show", "HEAD:sablonlar/remotion/src/Kok.tsx"],
                                                         cwd=KOK, capture_output=True, text=True,
                                                         check=True).stdout)
    SONUC["chrome"] = sorted((Path.home() / ".cache/hyperframes/chrome/chrome-headless-shell").glob("mac_arm-*"))[-1].name

    # 1. gl seçenekleri → WebGL sürücüsü
    gl = {}
    secenekler = [("sablon (angle)", yeni, []), ("ayarsiz (null)", varsayilan, [])] + \
                 [(g, yeni, [f"--gl={g}"]) for g in ("swangle", "swiftshader", "egl", "vulkan", "angle-egl")]
    for ad, klasor, bayrak in secenekler:
        png = klasor / "out" / f"gl-{ad.split()[0]}.png"
        r = kos(klasor, "still", "src/olcum/index.ts", "GlBilgi", str(png.relative_to(klasor)), *bayrak,
                zaman_asimi=120)
        r["webgl"] = gl_metni(png) if r["kod"] == 0 and png.exists() else None
        gl[ad] = r
        print("gl", ad, r, flush=True)
    SONUC["gl"] = gl

    # 2. Ornek3B mp4 süresi (90 kare, 1080x1920, şablonun JPEG ara kareleri, eşzamanlılık 4)
    sure = {}
    for ad, klasor, bayrak in secenekler:
        if not (gl[ad]["kod"] == 0 and gl[ad]["webgl"] and "webgl-yok" not in gl[ad]["webgl"]):
            continue
        r = kos(klasor, "render", "src/index.ts", "Ornek3B", f"out/u-{ad.split()[0]}.mp4", *bayrak)
        sure[ad] = r
        print("3b mp4", ad, r, flush=True)
    SONUC["ornek3b_mp4_90_kare"] = sure

    # 3. belirlenimcilik ve gl farkı (PNG dizisi, kayıpsız)
    dizi = {}
    for ad, bayrak in (("angle-1", []), ("angle-2", []), ("swangle", ["--gl=swangle"])):
        d = yeni / "out" / f"seq-{ad}"
        r = kos(yeni, "render", "src/index.ts", "Ornek3B", str(d.relative_to(yeni)), "--sequence",
                "--image-format=png", *bayrak)
        dizi[ad] = r
        print("dizi", ad, r, flush=True)
    a1, a2, sw = (png_dizisi(yeni / "out" / f"seq-{a}") for a in ("angle-1", "angle-2", "swangle"))
    arka = a1[0][5, 5]                                     # köşe: CSS arka planı (tuval saydam)
    SONUC["belirlenimcilik"] = {
        "kare": [len(a1), len(a2), len(sw)],
        "angle_iki_kosu_ayni_kare": sum(int(np.array_equal(x, y)) for x, y in zip(a1, a2)),
        "angle_iki_kosu_en_buyuk_fark": int(max(np.abs(x - y).max() for x, y in zip(a1, a2))),
        "angle_swangle_psnr_en_dusuk": min(psnr(x, y) for x, y in zip(a1, sw)),
        "angle_swangle_psnr_ort": round(float(np.mean([psnr(x, y) for x, y in zip(a1, sw)])), 2),
        "angle_swangle_en_buyuk_fark": int(max(np.abs(x - y).max() for x, y in zip(a1, sw))),
        "nesne_orani_kare_0_45_89": [round(float(((a1[i][..., 0] - a1[i][..., 2]) > 30).mean()), 3)
                                     for i in (0, 45, 89)],                # kırmızı baskın (R − B > 30) = düğüm
        "kose_rgb": [int(v) for v in arka],
        "kare_45_std": round(float(a1[45].std()), 1),
        "kare_44_45_ort_fark": round(float(np.abs(a1[44] - a1[45]).mean()), 2),
    }
    SONUC["dizi_sure"] = dizi
    print("belirlenimcilik", SONUC["belirlenimcilik"], flush=True)

    # 4. paket yükü: 'Ornek' (yalnız 2B) çizimi, 3B/Lottie kayıtlıyken ve değilken (dönüşümlü, 3'er kez)
    yuk = {"eski": [], "yeni": []}
    for _ in range(3):
        for ad, klasor in (("eski", eski), ("yeni", yeni)):
            r = kos(klasor, "render", "src/index.ts", "Ornek", "out/o.mp4", "--scale=0.25")
            yuk[ad].append(r["sure_sn"] if r["kod"] == 0 else r)
    SONUC["ornek_2b_cizim_sn"] = yuk
    print("yuk", yuk, flush=True)

    # 5. Lottie: fr 60'lık kopya aynı Remotion karesinde aynı görüntü mü (kare eşlemesi fr'yi yok sayıyor mu)
    lj = yeni / "public" / "lottie" / "ornek.json"
    l30 = kos(yeni, "still", "src/index.ts", "OrnekLottie", "out/l30.png", "--frame=24")
    veri = json.loads(lj.read_text())
    veri["fr"] = 60
    lj.write_text(json.dumps(veri))
    l60 = kos(yeni, "still", "src/index.ts", "OrnekLottie", "out/l60.png", "--frame=24")
    lj.write_text(json.dumps({**veri, "fr": 30}))
    x30, x60 = (np.asarray(Image.open(yeni / "out" / f"l{f}.png").convert("RGB")) for f in (30, 60))
    SONUC["lottie_fr"] = {"fr30": l30, "fr60": l60, "ayni_goruntu": bool(np.array_equal(x30, x60))}
    lr = kos(yeni, "render", "src/index.ts", "OrnekLottie", "out/l.mp4")
    SONUC["lottie_mp4_60_kare"] = lr
    print("lottie", SONUC["lottie_fr"], lr, flush=True)

    # 6. ağ kapalı (localhost açık): Remotion çizim sunucusu localhost'ta; dışarı çıkış yasak
    profil = ('(version 1)(allow default)(deny network-outbound)'
              '(allow network-outbound (remote ip "localhost:*"))(allow network-outbound (remote unix-socket))')
    sb = ("sandbox-exec", "-p", profil)
    disari = subprocess.run([*sb, "curl", "-s", "-o", "/dev/null", "-m", "5", "-w", "%{http_code}",
                             "https://registry.npmjs.org/"], capture_output=True, text=True)
    SONUC["agsiz"] = {
        "curl_disari": {"kod": disari.returncode, "http": disari.stdout},
        "ornek3b_still": kos(yeni, "still", "src/index.ts", "Ornek3B", "out/a3.png", "--frame=45", on=sb),
        "lottie_still": kos(yeni, "still", "src/index.ts", "OrnekLottie", "out/al.png", "--frame=50", on=sb),
    }
    print("agsiz", SONUC["agsiz"], flush=True)

    cikti.write_text(json.dumps(SONUC, ensure_ascii=False, indent=1) + "\n")
    shutil.rmtree(G, ignore_errors=True)


if __name__ == "__main__":
    main()
