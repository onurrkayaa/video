"""E3 sınamalarının duyarlılığı: şablona tek tek bozuk değişiklik uygula, ilgili sınama KIRILMALI; sonra geri al.
Çalıştır: source ortam.sh && .venv/bin/python <bu dosya> <çıktı.json>   (stüdyo kökünden)"""
import json
import os
import subprocess
import sys
from pathlib import Path

KOK = Path(os.environ["MEDYA"])
S = KOK / "sablonlar" / "remotion"
UC, LO = "test_remotion_3b_ornegi_gpu_da_cizer", "test_remotion_lottie_ornegi_yerel_ve_olcusu_dogru"
MUTASYONLAR = [
    ("gl swangle (dize sınaması geçer, etkin ayar CPU)", "remotion.config.ts",
     "Config.setChromiumOpenGlRenderer('angle'); // WebGL",
     "Config.setChromiumOpenGlRenderer('angle'); Config.setChromiumOpenGlRenderer('swangle'); // WebGL", UC),
    ("gl satırı yok", "remotion.config.ts", "Config.setChromiumOpenGlRenderer('angle');", "", UC),
    ("ışıklar yok", "src/Ornek3B.tsx",
     """				<ambientLight intensity={0.35} />
				<directionalLight position={[4, 6, 5]} intensity={2.2} />
				<pointLight position={[-5, -3, 2]} intensity={30} color="#3fa7d6" />
""", "", UC),
    ("dönüş yok", "src/Ornek3B.tsx", "rotation={[donus * 0.5, donus, 0]}", "rotation={[0.5, 1, 0]}", UC),
    ("yay girişi yok (0. karede tam boy)", "src/Ornek3B.tsx", "scale={giris * 0.8}", "scale={0.8}", UC),
    ("Lottie kutusu 800 px", "src/OrnekLottie.tsx", "width: 900, height: 900", "width: 800, height: 800", LO),
    ("Lottie çizgi 28 → 25", "public/lottie/ornek.json", '"w":{"a":0,"k":28}', '"w":{"a":0,"k":25}', LO),
    ("trim path animasyonsuz", "public/lottie/ornek.json",
     '"e":{"a":1,"k":[{"t":0,"s":[0],"o":{"x":[0.6],"y":[0]},"i":{"x":[0.2],"y":[1]}},{"t":36,"s":[100]}]}',
     '"e":{"a":0,"k":100}', LO),
    ("uzak Lottie adresi", "src/OrnekLottie.tsx", "fetch(staticFile('lottie/ornek.json'))",
     "fetch('https://assets4.lottiefiles.com/x.json')", LO),
]


def main():
    sonuc = []
    for ad, dosya, eski, yeni, sinama in MUTASYONLAR:
        yol = S / dosya
        asil = yol.read_bytes()
        metin = asil.decode()
        assert metin.count(eski) == 1, (ad, "eşleşme yok")
        yol.write_text(metin.replace(eski, yeni))
        try:
            r = subprocess.run([str(KOK / ".venv/bin/python"), "-m", "pytest", "-q", "-x", str(KOK / "testler" /
                                "test_temel.py"), "-k", sinama], cwd=KOK, capture_output=True, text=True,
                               timeout=600, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        finally:
            yol.write_bytes(asil)
        hata = [s for s in r.stdout.splitlines() if s.startswith("E ")][:2]
        sonuc.append({"mutasyon": ad, "sinama": sinama, "kirildi": r.returncode != 0, "neden": hata})
        print(sonuc[-1], flush=True)
    durum = subprocess.run(["git", "status", "--porcelain", "sablonlar/remotion"], cwd=KOK, capture_output=True,
                           text=True).stdout
    Path(sys.argv[1]).write_text(json.dumps({"mutasyonlar": sonuc, "sablon_git_durumu_sonra": durum}, ensure_ascii=False,
                                            indent=1) + "\n")


if __name__ == "__main__":
    main()
