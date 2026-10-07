"""medya ayir <ses|video> [--iki] [--model htdemucs|htdemucs_ft] — sesi katmanlara ayırır (Demucs v4, MIT).

Dört katman: vocals (vokal/konuşma), drums (davul), bass, other (diğer). --iki: yalnız vokal / vokalsiz.
Kullanım: şarkıda vokal girişlerini bulmak (yazıya dökmeden önce), vuruş analizini vokalsiz kanalda sınamak,
müziği konuşmanın altında kısmak, çekim sesindeki müziği ayıklamak. Ayrılmış katmanlar ZAMANLAMA ve
düzenleme içindir; ağırlıkların eğitim verisi tam açık değildir — ticari teslimde ayrılmış katmanı tek başına
"yeni ses" olarak satma. İlk kullanımda model (~80 MB) Hugging Face'ten iner.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ..ortak import KOK, MedyaHatasi, calistir, ffmpeg

SES_PY = KOK / "ortamlar" / "ses" / "bin" / "python"


def calistir_(args) -> int:
    if not SES_PY.exists():
        raise MedyaHatasi("ses ortamı yok (ortamlar/ses). Kur: medya kur ses-ortami")
    girdi = Path(args.girdi)
    hedef = Path(args.cikti or girdi.with_name(girdi.stem + "-katmanlar"))
    hedef.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as g:
        wav = Path(g) / f"{girdi.stem}.wav"
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", str(girdi), "-vn", "-ac", "2", "-ar", "44100", str(wav)],
                 hata_mesaji="ses çözülemedi")
        komut = [str(SES_PY), "-m", "demucs", "-n", args.model, "-o", g, "--filename", "{stem}.{ext}"]
        if args.iki:
            komut += ["--two-stems", "vocals"]
        komut += [str(wav)]
        r = subprocess.run(komut, capture_output=True, stdin=subprocess.DEVNULL, cwd=KOK)
        if r.returncode:
            raise MedyaHatasi("demucs başarısız:\n" + r.stderr.decode("utf-8", "replace")[-1500:])
        uretilen = list(Path(g, args.model).glob("*.wav"))
        if not uretilen:
            raise MedyaHatasi("demucs çıktı üretmedi")
        for f in uretilen:
            f.replace(hedef / f.name)
    print(f"{len(uretilen)} katman ({', '.join(sorted(f.stem for f in hedef.glob('*.wav')))}) → {hedef}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="ses katmanlarına ayırma (Demucs)")
    p.add_argument("girdi")
    p.add_argument("--iki", action="store_true", help="yalnız vokal / vokalsiz (daha hızlı)")
    p.add_argument("--model", default="htdemucs", choices=["htdemucs", "htdemucs_ft"], help="htdemucs_ft: daha iyi, 4 kat yavaş")
    p.add_argument("--cikti", help="katman klasörü (varsayılan <ad>-katmanlar/)")
    p.set_defaults(islev=calistir_)
