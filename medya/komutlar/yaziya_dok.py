"""medya yaziya-dok <ses|video> [--dil tr] [--srt] [--sarki] — konuşmayı kelime zamanlarıyla yazıya döker.

Sağlayıcı: mlx-whisper + whisper-large-v3-turbo (yerel, Apple GPU). Çıktı JSON: dil, metin, bölümler,
kelimeler (k, bas, son, olasilik). --srt ile alt yazı dosyası da yazılır. Şarkıda doğrudan kullanma: önce
`medya ayir` ile vokali ayır, sonra --sarki ile vokal kanalını dök (miks üzerinde uydurma metin artar).
Kelime zamanları şarkıda yaklaşıktır; kesimi bir kelime zamanına koyacaksan vokal başlangıcıyla doğrula.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ..ortak import KOK, MedyaHatasi, calistir, ffmpeg, json_oku, json_yaz

SES_PY = KOK / "ortamlar" / "ses" / "bin" / "python"
ISCI = KOK / "medya" / "isciler" / "yazi_isci.py"


def _zaman(t: float) -> str:
    ms = int(round(t * 1000))
    s, ms = divmod(ms, 1000); d, s = divmod(s, 60); sa, d = divmod(d, 60)
    return f"{sa:02d}:{d:02d}:{s:02d},{ms:03d}"


def srt_yaz(sonuc: dict, yol: Path, en_cok_kelime: int = 7, en_uzun: float = 3.5) -> Path:
    """Kelimelerden okunur alt yazı blokları: en çok N kelime / en uzun T sn; cümle sonunda böl."""
    bloklar, simdiki = [], []
    for w in sonuc["kelimeler"]:
        simdiki.append(w)
        sure = simdiki[-1]["son"] - simdiki[0]["bas"]
        if len(simdiki) >= en_cok_kelime or sure >= en_uzun or w["k"].endswith((".", "?", "!")):
            bloklar.append(simdiki); simdiki = []
    if simdiki:
        bloklar.append(simdiki)
    satirlar = []
    for i, b in enumerate(bloklar, 1):
        satirlar += [str(i), f"{_zaman(b[0]['bas'])} --> {_zaman(b[-1]['son'])}", " ".join(w["k"] for w in b), ""]
    yol.write_text("\n".join(satirlar), encoding="utf-8")
    return yol


def yaziya_dok(girdi: str, *, dil: str | None = None, sarki: bool = False, ipucu: str | None = None,
               model: str | None = None) -> dict:
    if not SES_PY.exists():
        raise MedyaHatasi("ses ortamı yok (ortamlar/ses). Kur: medya kur ses-ortami")
    with tempfile.TemporaryDirectory() as g:
        wav = Path(g) / "girdi.wav"
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi, "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                 hata_mesaji="ses çözülemedi")
        cikti = Path(g) / "c.json"
        komut = [str(SES_PY), str(ISCI), str(wav), str(cikti)]
        if dil:
            komut += ["--dil", dil]
        if sarki:
            komut += ["--sarki"]
        if ipucu:
            komut += ["--ipucu", ipucu]
        if model:
            komut += ["--model", model]
        r = subprocess.run(komut, capture_output=True, stdin=subprocess.DEVNULL, cwd=KOK)
        if r.returncode:
            raise MedyaHatasi("yazıya dökme başarısız:\n" + r.stderr.decode("utf-8", "replace")[-2000:])
        return json_oku(cikti)


def calistir_(args) -> int:
    sonuc = yaziya_dok(args.girdi, dil=args.dil, sarki=args.sarki, ipucu=args.ipucu, model=args.model)
    cikti = Path(args.cikti or str(Path(args.girdi).with_suffix("")) + "-yazi.json")
    json_yaz(cikti, sonuc)
    print(f"[{sonuc['dil']}] {sonuc['metin'][:300]}{'…' if len(sonuc['metin']) > 300 else ''}")
    dusuk = [w for w in sonuc["kelimeler"] if w["olasilik"] < 0.5]
    print(f"  {len(sonuc['kelimeler'])} kelime, {len(sonuc['bolumler'])} bölüm"
          + (f"; düşük güvenli {len(dusuk)} kelime: {', '.join(w['k'] for w in dusuk[:8])}" if dusuk else ""))
    print(f"→ {cikti}")
    if args.srt:
        print(f"→ {srt_yaz(sonuc, cikti.with_suffix('.srt'))}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="konuşmayı yazıya dök (kelime zamanlı)")
    p.add_argument("girdi")
    p.add_argument("--dil", help="ör. tr, en (verilmezse otomatik)")
    p.add_argument("--srt", action="store_true", help="alt yazı (.srt) da yaz")
    p.add_argument("--sarki", action="store_true", help="vokal/şarkı modu (önce medya ayir ile vokali ayır)")
    p.add_argument("--ipucu", help="bilinen özel adlar / söz metni")
    p.add_argument("--model", help="varsayılan mlx-community/whisper-large-v3-turbo")
    p.add_argument("--cikti")
    p.set_defaults(islev=calistir_)
