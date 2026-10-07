"""Metinden konuşma işçisi — mlx-audio araç ortamında (.uv/tools/mlx-audio/bin/python), Apple GPU (MLX).

  .uv/tools/mlx-audio/bin/python medya/isciler/ses_uret_isci.py <is.json> <sonuc.json>

is.json: {"model": "<yerel model klasörü>", "klasor": "<çıktı klasörü>",
          "cumleler": [{"ad": "001", "metin": "…"}, …],
          "kimlik": {"wav": "…", "metin": "…"} | null,   # varsa her cümle bu sesten klonlanır
          "tarif": "…" | null,                            # kimlik yoksa: ses tarifi (VoxCPM2 voice design)
          "kip": "klon" | "devam"}                        # devam: kimliğin metniyle birlikte (prompt) klonlar
Model BİR KEZ yüklenir (komut satırı aracı her çağrıda yeniden yükler: cümle başına ~5 sn kayıp).
Her cümle <klasor>/<ad>.wav (model örnekleme hızında, mono float32) olarak yazılır.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def main() -> int:
    is_ = json.loads(Path(sys.argv[1]).read_text())
    import numpy as np
    from mlx_audio.audio_io import write as audio_write
    from mlx_audio.tts.utils import load_model
    from mlx_audio.utils import load_audio

    t0 = time.perf_counter()
    model = load_model(Path(is_["model"]))
    yukleme = time.perf_counter() - t0
    sr = int(model.sample_rate)
    kw: dict = {}
    k = is_.get("kimlik")
    if k:
        ref = load_audio(k["wav"], sample_rate=sr)
        kw["ref_audio"] = ref
        if is_.get("kip") == "devam" and k.get("metin"):
            kw.update(prompt_audio=ref, prompt_text=k["metin"])
    elif is_.get("tarif"):
        kw["instruct"] = is_["tarif"]
    klasor = Path(is_["klasor"])
    klasor.mkdir(parents=True, exist_ok=True)
    sonuc = []
    for c in is_["cumleler"]:
        t = time.perf_counter()
        parca = [np.asarray(r.audio, dtype=np.float32) for r in model.generate(text=c["metin"], **kw)]
        ses = np.concatenate(parca) if parca else np.zeros(0, np.float32)
        yol = klasor / f"{c['ad']}.wav"
        audio_write(str(yol), ses, sr, format="wav")
        sonuc.append({"ad": c["ad"], "wav": str(yol), "sure": round(len(ses) / sr, 3),
                      "uretim_sn": round(time.perf_counter() - t, 2)})
    Path(sys.argv[2]).write_text(json.dumps({"ornekleme": sr, "yukleme_sn": round(yukleme, 2), "cumleler": sonuc},
                                            ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
