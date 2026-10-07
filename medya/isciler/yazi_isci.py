"""Konuşmayı yazıya dökme işçisi — ortamlar/ses Python'unda (mlx-whisper, Apple GPU).

  ortamlar/ses/bin/python medya/isciler/yazi_isci.py <wav> <cikti.json> [--dil tr] [--model ...] [--sarki]

Varsayılan model mlx-community/whisper-large-v3-turbo (MIT, ~1,6 GB, ilk kullanımda Hugging Face'ten iner;
hesap/anahtar gerekmez). condition_on_previous_text=False: şarkı ve uzun kayıtta tekrar döngüsü ve
uydurma metni (halüsinasyon) belirgin azaltır. Dil verilmezse model kendisi seçer; Türkçe için --dil tr ver.
--sarki: müzikte (vokal) kullanım için halüsinasyon sessizlik eşiği açılır.
"""
from __future__ import annotations

import json
import sys
import warnings

warnings.filterwarnings("ignore")


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("wav"); p.add_argument("cikti")
    p.add_argument("--dil", default=None)
    p.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    p.add_argument("--sarki", action="store_true")
    p.add_argument("--ipucu", default=None, help="bilinen sözcükler/söz (initial_prompt)")
    a = p.parse_args()
    import mlx_whisper
    secenek = dict(path_or_hf_repo=a.model, word_timestamps=True, condition_on_previous_text=False,
                   language=a.dil, verbose=None)
    if a.ipucu:
        secenek["initial_prompt"] = a.ipucu
    if a.sarki:
        secenek["hallucination_silence_threshold"] = 2.0
    r = mlx_whisper.transcribe(a.wav, **secenek)
    kelimeler = []
    for s in r.get("segments", []):
        for w in s.get("words", []) or []:
            kelimeler.append({"k": w["word"].strip(), "bas": round(float(w["start"]), 3), "son": round(float(w["end"]), 3),
                              "olasilik": round(float(w.get("probability", 0.0)), 3)})
    cikti = {"dil": r.get("language"), "metin": r.get("text", "").strip(), "model": a.model,
             "bolumler": [{"bas": round(float(s["start"]), 3), "son": round(float(s["end"]), 3), "metin": s["text"].strip(),
                           "sessizlik_olasiligi": round(float(s.get("no_speech_prob", 0.0)), 3)} for s in r.get("segments", [])],
             "kelimeler": kelimeler}
    with open(a.cikti, "w") as f:
        json.dump(cikti, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
