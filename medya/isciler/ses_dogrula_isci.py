"""Dış ses doğrulama işçisi — ortamlar/ses Python'unda (mlx-whisper + SpeechBrain ECAPA).

  ortamlar/ses/bin/python medya/isciler/ses_dogrula_isci.py <is.json> <sonuc.json>

is.json: {"whisper": "<model yolu ya da repo>", "ecapa": "<yerel ECAPA klasörü>", "dil": "tr",
          "kimlik_wav": "…" | null, "cumleler": [{"ad": "001", "metin": "…", "wav": "…"}, …]}
Her cümle için: Whisper dökümü, Türkçe normalleştirilmiş CER/WER (medya.turkce) ve kimliğe konuşmacı benzerliği
(ECAPA gömme kosinüsü; aynı konuşmacı ~0,6–0,9, ayrı tarifle üretilmiş "başka" sesler ~0,2–0,4 ölçüldü).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))     # stüdyo kökü (medya.turkce)


def main() -> int:
    is_ = json.loads(Path(sys.argv[1]).read_text())
    import librosa
    import mlx_whisper
    import numpy as np
    import torch
    from medya.turkce import karsilastir

    gomucu = None
    if is_.get("kimlik_wav") and is_.get("ecapa"):
        from speechbrain.inference.speaker import EncoderClassifier
        e = is_["ecapa"]
        gomucu = EncoderClassifier.from_hparams(source=e, savedir=str(Path(sys.argv[2]).parent / "ecapa"),
                                                run_opts={"device": "cpu"}, overrides={"pretrained_path": e})

    def gom(wav: str):
        y, _ = librosa.load(wav, sr=16000)
        v = gomucu.encode_batch(torch.tensor(y)[None]).squeeze().numpy()
        return v / (np.linalg.norm(v) + 1e-9)

    ref = gom(is_["kimlik_wav"]) if gomucu is not None else None
    sonuc = []
    for c in is_["cumleler"]:
        r = mlx_whisper.transcribe(c["wav"], path_or_hf_repo=is_["whisper"], language=is_.get("dil"),
                                   condition_on_previous_text=False, word_timestamps=True, verbose=None)
        dokum = r.get("text", "").strip()
        k = karsilastir(c["metin"], dokum)
        kel = [w for s in r.get("segments", []) for w in (s.get("words") or [])]
        konusma = (float(kel[-1]["end"]) - float(kel[0]["start"])) if len(kel) > 1 else None
        x = {"ad": c["ad"], "dokum": dokum, "cer": k["cer"], "wer": k["wer"],
             "degisen": k["kelime_islemleri"]["degisen"], "dusen": k["kelime_islemleri"]["dusen"],
             "eklenen": k["kelime_islemleri"]["eklenen"],
             "karakter_sn": round(len(c["metin"]) / konusma, 2) if konusma else None}
        if ref is not None:
            x["benzerlik"] = round(float(ref @ gom(c["wav"])), 3)
        sonuc.append(x)
    Path(sys.argv[2]).write_text(json.dumps({"cumleler": sonuc}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
