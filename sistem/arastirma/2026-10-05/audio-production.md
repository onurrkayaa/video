# Ses üretimi — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Root cause found in local code: the 'audio slipping' failure is structural, not bad luck. ilk-montaj/kurgu.py cut to a fixed 76.005 BPM grid. A 0.05 BPM error drifts by about 0.18 s over 352 beats, and live acoustic songs have no constant tempo. The HyperFrames 'beats' command would not have helped: it combines RMS peaks with bpm-detective's integer-rounded BPM, then regularizeBeats() builds a constant grid (node_modules/hyperframes/dist/beat-analyzer.global.js). The music-to-video analyzer uses librosa.beat.beat_track, which has the same constant-tempo bias.

Fix (measurement-first workflow):
- Beat This! (beat_this 1.1.0, 2026-04-14, MIT code and weights) gives per-beat and downbeat times. Running its 3 seeds and comparing them gives a measurable confidence.
- Mix all audio into one continuous 48 kHz master and encode AAC once.
- Audit sync after every render: windowed cross-correlation must show a constant lag, plus cut-vs-beat offsets per frame.

Recommended brew-free stack (Homebrew is currently blocked: 'You have not agreed to the Xcode license'):
- Runtime: uv with Python 3.12.
- Already installed: ffmpeg for loudnorm two-pass, ebur128, sidechaincompress, acrossfade, axcorrelate.
- Effects: pedalboard 0.9.25 (GPLv3, outputs unrestricted).
- Time-stretch: Rubber Band 4.0.0 prebuilt CLI.
- Stems: Demucs 4.1.0 (2026-07-11, MIT code and weights).
- Speech enhancement: DeepFilterNet3 Rust binary (28 MB, MIT/Apache).
- TTS and checking: mlx-audio 0.5.7 (MLX, no torch). Turkish TTS with VoxCPM2 (Apache-2.0, vendor-reported Turkish WER 0.82%, voice design without a reference clip). Whisper large-v3-turbo through mlx-whisper acts as the agent's 'ears' (CER gates).
- English drafts: Kokoro.
- Music:
  - Instrumental beds: Magenta RealTime 2 small (Apache-2.0 code, CC-BY-4.0 weights, trained on licensed stock music, MLX).
  - Full songs with BPM/key control: ACE-Step 1.5 (MIT, vendor says licensed/royalty-free/synthetic data; heavy, 5.3-10 GB).
  - Deterministic, exact-beat music: MIDI plus tinysoundfont and an MIT/free SoundFont.
- SFX: Kenney CC0 packs, Sonniss GDC bundles (no account, royalty-free, no attribution), procedural numpy/pedalboard synthesis. Optional heavy text-to-SFX: MOSS-SoundEffect v2 MLX 4-bit (Apache-2.0, 6.4 GB).

Non-commercial or account-gated traps:
- MusicGen, the HyperFrames offline BGM fallback, is CC-BY-NC.
- Stable Audio Open is HF-gated.
- MMAudio, AudioLDM2, AudioX and TangoFlux are non-commercial.
- ThinkSound is research-only despite its Apache tag.
- XTTS-v2, F5-TTS, OmniVoice, Higgs TTS 3 and MMS-TTS are non-commercial.
- Piper's Turkish voices are NC or based on Lessac.
- macOS 'say' voices are licensed for personal, non-commercial use only.
- Demucs's diffq quantized models are CC-BY-NC.

Disk budget: the core stack is about 5.5 GB. Heavy generators should be installed on demand.

## Seçimler

### Beat and downbeat times for cutting picture to music (replaces constant-BPM grids: the cause of the 'slipping' cuts)
- **Seçim:** Beat This! (CPJKU beat_this 1.1.0). Checkpoints final0/final1/final2 (seed ensemble); small0 for speed
- Alternatifler: librosa 1.0 beat_track/PLP (ISC), only as a second opinion. madmom/allin1/BeatNet: avoid (NC models, stale). Essentia: AGPL with NC models.
- Neden: ISMIR-2024 SOTA tracker. Outputs per-beat and downbeat timestamps using plain peak-picking, with no madmom DBN, so there is no constant-tempo assumption and no CC BY-NC-SA madmom models. Three independently trained seeds give a measurable agreement/confidence signal, which the assistant needs because it cannot listen. Local code shows why the alternatives failed. The HyperFrames 'beats' command does RMS peaks, takes bpm-detective's Math.round() BPM, then regularizeBeats() builds a constant grid: a 0.3 BPM error means about 1.1 s drift over 290 s. music-to-video's analyze-beatgrid.py uses librosa.beat.beat_track (Ellis DP, near-constant tempo); the skill itself warns it is a 'metronome' on calm music. ilk-montaj/kurgu.py used a fixed 76.005 BPM grid.
- Lisans: kod MIT · ağırlık MIT. The README notes some training audio is copyrighted; outputs are only timestamps. · ticari: yes
- Apple Silicon: PyTorch CPU. The CLI uses CUDA or CPU (--gpu=-1 forces CPU); MPS is not documented. Expected seconds to under a minute per song on M2 CPU (estimate, not measured).
- Kurulum: uv tool install --python 3.12 beat-this   (pulls torch>=2 + torchaudio; checkpoints of about 78 MB each auto-download from JKU's cloud on first use). Feed WAV made with the project's ffmpeg: arac/ffmpeg -i song.m4a -ac 2 -ar 44100 song.wav
- Disk: ~700 MB · bakım: PyPI 1.0 (2026-04-13) then 1.1.0 (2026-04-14). Paper code maintained by JKU.
- Ajan kullanımı: Run once per seed: beat_this song.wav -o song.final0.beats --model final0 --gpu=-1, then the same with final1 and final2. Python alternative: from beat_this.inference import File2Beats; beats, downbeats = File2Beats(checkpoint_path='final0', device='cpu', dbn=False)('song.wav'). Then build consensus beats, score the seeds against each other with mir_eval, and write <project>/beats/<audio>.json in HyperFrames format {version:1, audio, beats:[{time,strength}]} so Studio shows them. Never run 'hyperframes beats' for live or acoustic music.
- Güven: high · kaynaklar: https://github.com/CPJKU/beat_this, https://pypi.org/pypi/beat-this/json, https://github.com/CPJKU/madmom/blob/main/LICENSE, local: /Users/onurkaya/Projects/video/node_modules/hyperframes/dist/beat-analyzer.global.js, local: /Users/onurkaya/.claude/skills/music-to-video/scripts/analyze-beatgrid.py, local: /Users/onurkaya/Projects/video/ilk-montaj/kurgu.py

### Stem separation: vocals/drums/bass/other, instrumental beds, removing music under dialogue
- **Seçim:** Demucs v4.1.0 (officially maintained adefossez fork). htdemucs (fast) or htdemucs_ft (best). Optional: python-audio-separator 0.47.0 + Kim Mel-Band RoFormer for top vocal isolation
- Alternatifler: audio-separator with BS-RoFormer viperx 12.97 SDR (weights license unknown, personal use only). UVR GUI (not agent-friendly).
- Neden: The only top-tier separator with unambiguous MIT terms for both code and pretrained models. Scores about 9.0 dB SDR on MUSDB-HQ. Supports 4 stems or --two-stems=vocals. Version 4.1.0 (2026-07-11) modernized packaging, dropped the torchaudio dependency and hosts models on Hugging Face. For maximum vocal quality, KimberleyJSN/melbandroformer has an MIT card (913 MB) and runs through audio-separator, whose wrapper is MIT and uses MPS/CoreML. Most UVR/viperx BS-RoFormer weights have unknown licenses, so use them only for personal projects.
- Lisans: kod MIT · ağırlık MIT (htdemucs, htdemucs_ft, mdx*). Do NOT use the [quantized] extra or the mdx_q/mdx_extra_q models: they need diffq, which is CC-BY-NC-4.0. · ticari: yes
- Apple Silicon: PyTorch CPU: about 1.5x track length for htdemucs per the README; htdemucs_ft is about 4x slower. -d mps is undocumented, so try it but fall back to -d cpu. audio-separator uses MPS/CoreML automatically.
- Kurulum: uv tool install --python 3.12 demucs   (no [quantized]). Optional: uv tool install --python 3.12 'audio-separator[cpu]' and pass --model_file_dir ~/Models/audio-separator, because the default is /tmp/audio-separator-models
- Disk: ~850 MB · bakım: The facebookresearch repo was archived 2025-01-01. The fork released 4.1.0 on 2026-07-11; its maintainer says 'not actively working on Demucs … slow replies'.
- Ajan kullanımı: demucs -n htdemucs_ft --two-stems=vocals -d cpu --segment 8 -o stems song.wav  writes stems/htdemucs_ft/song/{vocals,no_vocals}.wav at 44.1 kHz. Check: residual of (sum of stems - mix) must be at least 30 dB down, and Whisper run on the instrumental should return no words.
- Güven: high · kaynaklar: https://github.com/facebookresearch/demucs, https://github.com/adefossez/demucs, https://pypi.org/pypi/demucs/json, https://github.com/nomadkaraoke/python-audio-separator, https://pypi.org/pypi/audio-separator/json, https://huggingface.co/KimberleyJSN/melbandroformer, https://pypi.org/pypi/diffq/json

### Speech/dialogue denoise and enhancement (phone clips with wind, crowd or room noise; voiceover cleanup)
- **Seçim:** DeepFilterNet3 through the standalone Rust 'deep-filter' 0.5.6 binary (aarch64-apple-darwin) with models/DeepFilterNet3_onnx.tar.gz
- Alternatifler: MossFormer2 SE 48K (mlx-audio, Apache-2.0). ffmpeg afftdn/anlmdn. ffmpeg arnndn with GregorR rnnoise-models (declared non-copyrightable). Resemble Enhance: avoid.
- Neden: Full-band 48 kHz neural noise suppression with dual MIT/Apache-2.0 terms for both code and weights. It is one 27.9 MB binary plus an 8.0 MB model: no Python, no torch, no brew. The Python package is pinned to numpy<2 and breaks with newer torchaudio, so it is avoided. If DFN3 artifacts show up, use MossFormer2_SE_48K (Apache-2.0, int8 90 MB) through mlx-audio as the higher-quality second option. For steady hiss, ffmpeg's afftdn/anlmdn are already available.
- Lisans: kod MIT OR Apache-2.0 · ağırlık MIT OR Apache-2.0 (DFN3). MossFormer2 SE: Apache-2.0. · ticari: yes
- Apple Silicon: Native arm64 Rust/tract on CPU (NEON). Expected faster than real time. The MLX port mlx-community/DeepFilterNet-mlx (MIT, 26 MB) also runs through mlx-audio.
- Kurulum: curl -L -o /Users/onurkaya/Projects/video/arac/deep-filter https://github.com/Rikorose/DeepFilterNet/releases/download/v0.5.6/deep-filter-0.5.6-aarch64-apple-darwin && chmod +x .../arac/deep-filter ; curl -L -o .../arac/DeepFilterNet3_onnx.tar.gz https://github.com/Rikorose/DeepFilterNet/raw/main/models/DeepFilterNet3_onnx.tar.gz   (curl adds no quarantine flag)
- Disk: ~36 MB · bakım: Last release v0.5.6 (2023-08-31): stable but dormant. The MLX port is from 2026-03.
- Ajan kullanımı: arac/ffmpeg -i clip.mov -vn -ac 1 -ar 48000 -c:a pcm_s16le v.wav && arac/deep-filter -D -m arac/DeepFilterNet3_onnx.tar.gz -o out v.wav  (-D compensates for STFT/lookahead delay, which is essential for sync). Blend about 85% processed with 15% dry using ffmpeg amix weights to avoid an 'underwater' sound. Check: noise floor in the pauses drops; the 1-4 kHz speech band changes by no more than ±2 dB; Whisper WER is not worse than before.
- Güven: high · kaynaklar: https://github.com/Rikorose/DeepFilterNet, https://api.github.com/repos/Rikorose/DeepFilterNet/releases/tags/v0.5.6, https://pypi.org/pypi/deepfilternet/json, https://huggingface.co/starkdmi/MossFormer2_SE_48K_MLX, https://huggingface.co/mlx-community/DeepFilterNet-mlx, https://github.com/GregorR/rnnoise-models

### Loudness measurement and delivery mastering
- **Seçim:** ffmpeg (bundled 6.0): ebur128 + two-pass loudnorm (linear=true) + alimiter. pyloudnorm 0.2.0 for checking stems in Python
- Alternatifler: matchering 2.0.6 (GPLv3, reference-track mastering for music; unchanged since 2022). pedalboard Limiter.
- Neden: Already installed and deterministic. Reports I, LRA and true peak, and does not re-encode video. betikler/ustala.sh already does measure, then gain, then alimiter. Two-pass linear mode keeps the dynamics. Known gotcha: dynamic mode, or a failed linear fallback, upsamples to 192 kHz, so always append aresample=48000 and check normalization_type in the JSON. pyloudnorm (MIT, 2026-01-04) implements BS.1770 integrated loudness for stems before mixing; it has no true peak, so use ebur128=peak=true for that.
- Lisans: kod ffmpeg: GPL. This static build has --enable-gpl --enable-nonfree, which is fine to use locally but not redistributable. pyloudnorm: MIT. · ağırlık - · ticari: yes
- Apple Silicon: Native arm64
- Kurulum: Nothing extra for ffmpeg (arac/ffmpeg). uv pip install pyloudnorm soundfile
- Disk: ~2 MB · bakım: ffmpeg-static 6.0 (2023); stable
- Ajan kullanımı: Pass 1: ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null -  Pass 2: loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=..:measured_TP=..:measured_LRA=..:measured_thresh=..:offset=..:linear=true:print_format=json,aresample=48000. Final check: ffmpeg -i out -af ebur128=peak=true -f null -
- Güven: high · kaynaklar: https://ffmpeg.org/ffmpeg-filters.html, https://lists.ffmpeg.org/pipermail/ffmpeg-cvslog/2017-August/108680.html, https://github.com/em-synth/ffmpeg-normalize, https://pypi.org/pypi/pyloudnorm/json, https://github.com/sergree/matchering, local: /Users/onurkaya/Projects/video/betikler/ustala.sh

### Mixing and effects (EQ, compression, de-ess, reverb, limiting) on stems, SFX and voiceover
- **Seçim:** Placement-level mix inside HyperFrames (data-fx-chain, data-automation, data-fade-in/out, overlapping clips) plus offline processing with Spotify pedalboard 0.9.25
- Alternatifler: ffmpeg acompressor/equalizer/deesser/afir (convolution reverb). SoX is unavailable while brew is blocked.
- Neden: hyperframes-audio runs the same Web Audio graph in preview and in render, so what Studio plays is what gets written. pedalboard adds JUCE-grade Compressor, Limiter, NoiseGate, filters, Reverb, Convolution, PitchShift and time_stretch. It can host macOS AU and VST3 plugins and stream files with O(1) memory. Wheels exist for cp310-cp315, so it even runs on the system Python 3.14. The GPL applies to distributing the software, not to audio you render.
- Lisans: kod pedalboard: GPLv3 (it bundles JUCE, VST3 SDK and Rubber Band) · ağırlık - · ticari: yes
- Apple Silicon: Native arm64
- Kurulum: uv pip install pedalboard   (into the shared 3.12 script venv)
- Disk: ~15 MB · bakım: 0.9.25 released 2026-09-09
- Ajan kullanımı: from pedalboard import Pedalboard, HighpassFilter, Compressor, Limiter, Reverb; from pedalboard.io import AudioFile. Read the file, apply board(audio, sr), write WAV. pedalboard has no sidechain input, so ducking uses gain envelopes (next pick). In HTML, use data-fx-chain JSON per hyperframes-audio/references/fx-registry.md.
- Güven: high · kaynaklar: https://github.com/spotify/pedalboard, https://pypi.org/pypi/pedalboard/json, local: /Users/onurkaya/.claude/skills/hyperframes-audio/SKILL.md

### Ducking/sidechain: music bed under voiceover or natural sound bites (laughter, speech in clips)
- **Seçim:** Envelope ducking: Silero-VAD or RMS-derived gain automation computed in numpy, written to HyperFrames data-automation or done with hyperframes-audio scripts/carve.mjs. Offline fallback: ffmpeg sidechaincompress
- Alternatifler: hyperframes-audio carve presets; pedalboard Compressor (no sidechain)
- Neden: Gives deterministic, measurable ducks with explicit depth, attack, release and pre-roll, unlike opaque compressor behaviour. The carve does frequency-selective dips so speech stays intelligible without killing the bed. sidechaincompress is already in the bundled ffmpeg. HyperFrames' own narration guidance puts music at about -31 LUFS under voice.
- Lisans: kod ffmpeg GPL; Silero VAD MIT (bundled in mlx-audio); numpy BSD · ağırlık - · ticari: yes
- Apple Silicon: Native
- Kurulum: Nothing extra (ffmpeg present; Silero VAD comes with mlx-audio)
- Disk: ~5 MB · bakım: n/a
- Ajan kullanımı: arac/ffmpeg -i bed.wav -i vo.wav -filter_complex "[0:a][1:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=450[d];[d][1:a]amix=inputs=2:normalize=0" mix.wav. Envelope alternative: -12 dB depth, 120 ms pre-roll, 80 ms attack, 450 ms release.
- Güven: high · kaynaklar: local: arac/ffmpeg -h filter=sidechaincompress, local: /Users/onurkaya/.claude/skills/hyperframes-audio/SKILL.md, local: /Users/onurkaya/.claude/skills/media-use/audio/references/tts.md, https://github.com/Blaizzy/mlx-audio

### Click-free audio cuts, micro-crossfades and musical splices
- **Seçim:** ffmpeg afade/acrossfade with equal-power curves (qsin/hsin) plus HyperFrames data-fade-in/out. Splice music only at beat_this downbeats. Mix everything into ONE continuous 48 kHz float WAV and encode AAC once
- Alternatifler: pedalboard/numpy custom fades
- Neden: Cutting mid-waveform causes clicks; 5-10 ms fades remove them. Equal-power curves keep loudness steady through 20-80 ms music crossfades. One continuous PCM master avoids AAC encoder priming/padding (tens of ms per segment) piling up when segments are concatenated, which is one plausible 'slip' mechanism. acrossfade supports 19 curve types, including qsin/hsin/esin.
- Lisans: kod ffmpeg GPL · ağırlık - · ticari: yes
- Apple Silicon: Native
- Kurulum: None
- Disk: ~0 MB · bakım: n/a
- Ajan kullanımı: acrossfade=d=0.04:c1=qsin:c2=qsin ; afade=t=in:d=0.008 ; afade=t=out:st=<t-0.008>:d=0.008 ; HTML data-fade-in="0.01". Then run the click detector and the duration-equality checks in the techniques list.
- Güven: high · kaynaklar: local: arac/ffmpeg -h filter=acrossfade, https://ffmpeg.org/ffmpeg-filters.html

### Time-stretch and pitch-shift (ambience under slow motion, small tempo nudges, key changes)
- **Seçim:** Rubber Band 4.0.0 CLI (official prebuilt macOS GPL binary, R3 'fine' engine), or pedalboard.time_stretch (same engine) in Python
- Alternatifler: python-stretch/Signalsmith (MIT). pedalboard.time_stretch (GPLv3). ffmpeg atempo (speech only, 0.5-2 per instance). HyperFrames data-playback-rate (constant rate, pitch preserved).
- Neden: The best open-source stretch quality: R3 for music, formant preservation for voice. Used as a standalone tool, its GPL terms do not reach the output audio. The download is 1.5 MB and needs no brew. Signalsmith Stretch (MIT, python-stretch wheels up to cp312) is the permissive option if code must ship inside work software. Rule: do not stretch the music bed more than ±3%; edit at bar boundaries instead.
- Lisans: kod GPL-2.0-or-later (commercial licence purchasable from Particular Programs) · ağırlık - · ticari: yes
- Apple Silicon: Native macOS executable (architecture of the prebuilt not inspected); CPU
- Kurulum: curl -LO https://breakfastquay.com/files/releases/rubberband-4.0.0-gpl-executable-macos.tar.bz2 && tar xjf rubberband-4.0.0-gpl-executable-macos.tar.bz2 && copy the binary into /Users/onurkaya/Projects/video/arac/ . Check with 'arac/rubberband --version'; if it is killed by signal 9, ad-hoc sign it: codesign -s - -f arac/rubberband
- Disk: ~5 MB · bakım: 4.0.0 released 2024-10-25
- Ajan kullanımı: rubberband -3 -t 2.0 amb.wav amb_slow.wav  (makes it 2x longer for 0.5x slow motion). rubberband -3 -p 2 -F voice.wav up2.wav  (+2 semitones, formant-preserving). -T sets a tempo ratio. Check: output samples == round(input × ratio); beat_this tempo ratio matches.
- Güven: medium · kaynaklar: https://breakfastquay.com/rubberband/, https://github.com/Signalsmith-Audio/signalsmith-stretch, https://pypi.org/pypi/python-stretch/json, https://github.com/spotify/pedalboard

### Instrumental background music generation: commercial-safe and small enough for M2/16 GB
- **Seçim:** Google Magenta RealTime 2, model mrt2_small (230M), through magenta-rt[mlx] 2.0.3
- Alternatifler: ACE-Step 1.5 (full songs, BPM/key control, heavy). MIDI+SoundFont (deterministic). incompetech/Kevin MacLeod (CC-BY 4.0, attribution required, no account).
- Neden: Code is Apache-2.0 and weights are CC-BY-4.0. Google says it trained on about 71k hours of stock music and 'claims no rights in outputs you generate'. It runs in real time on any Apple Silicon Mac (the small model is listed as real-time even on M1 Air). It can be steered with text, audio examples and MIDI, outputs 48 kHz stereo, and is mostly instrumental, which suits beds. There is no BPM parameter: measure tempo afterwards with beat_this, or steer with MIDI onsets.
- Lisans: kod Apache-2.0 · ağırlık CC-BY-4.0. Attribution is due only when redistributing the model; outputs are unrestricted by Google. · ticari: yes
- Apple Silicon: MLX native (exported .mlxfn plus a C++ engine). JAX CPU is also installed.
- Kurulum: uv venv --python 3.12 ~/.venvs/mrt && uv pip install --python ~/.venvs/mrt 'magenta-rt[mlx]' && mrt models init && mrt models download (non-interactive model-argument form not verified; check --help). Files are stored in ~/Documents/Magenta/magenta-rt-v2: about 1.38 GB of resources plus 0.46 GB for mrt2_small.
- Disk: ~2400 MB · bakım: Model released 2026-05/06; magenta-rt 2.0.3 released 2026-07-30
- Ajan kullanımı: mrt mlx generate --prompt 'warm fingerpicked acoustic guitar, soft piano, intimate' --duration 60 --model=mrt2_small  (check 'mrt mlx generate --help' for output path and --bits). The Python API (magenta_rt) handles prompt morphs and longer renders. Then apply the generated-music gate (techniques).
- Güven: medium · kaynaklar: https://huggingface.co/google/magenta-realtime-2, https://github.com/magenta/magenta-realtime, https://raw.githubusercontent.com/magenta/magenta-realtime/main/docs/models.md, https://raw.githubusercontent.com/magenta/magenta-realtime/main/docs/installation.md, https://pypi.org/pypi/magenta-rt/json

### Full songs (vocals and lyrics), with duration, BPM, key and time-signature control
- **Seçim:** ACE-Step 1.5: the 2B turbo DiT with the 0.6B LM, or with the LM off. Route A: official repo with MLX/MPS backend (exact bpm/keyscale/timesignature API). Route B: mlx-community/ACE-Step1.5-MLX-4bit (5.3 GB)
- Alternatifler: Magenta RT 2 small (instrumental, 2.4 GB). MiniMax Music 3 (community license, ≥9.2 GB at 4-bit). HeartMuLa-3B (Apache-2.0 but 15.7 GB). YuE2 (CC-BY-NC).
- Neden: Code and weights are MIT. The HF card says outputs can be used commercially and that training used licensed, royalty-free/public-domain and synthetic MIDI-rendered data; this is the vendor's claim. It controls duration (10 s to 10 min), bpm, keyscale, timesignature, seed and instrumental, and lyrics in 50+ languages (Turkish not explicitly verified). Reported quality is between Suno v4.5 and v5. A July 2026 report on an M1 Max 64 GB generated two 100 s songs in 58 s; a base M2 will be several times slower (estimate).
- Lisans: kod MIT · ağırlık MIT · ticari: yes
- Apple Silicon: MLX (the macOS scripts set ACESTEP_LM_BACKEND=mlx) or PyTorch MPS. Needs about 4.7 GB of weights for the 2B DiT; 16 GB is OK if nothing else heavy is running.
- Kurulum: git clone https://github.com/ace-step/ACE-Step-1.5 && cd ACE-Step-1.5 && uv sync   (Python 3.11-3.12). Use CHECK_UPDATE=false and --download-source huggingface, and download only acestep-v15-turbo (4.8 GB), acestep-5Hz-lm-0.6B (1.4 GB), Qwen3-Embedding-0.6B (1.2 GB) and vae (0.34 GB). The default bundle with the 1.7B LM is 10.1 GB.
- Disk: ~7000 MB · bakım: v1.5 released 2026-01/02; XL released 2026-04-02; active
- Ajan kullanımı: Python: from acestep.inference import GenerationParams, GenerationConfig, generate_music; params = GenerationParams(caption='acoustic folk ballad, warm guitar', lyrics='[Instrumental]', bpm=76, keyscale='D major', timesignature='4', duration=120, seed=7). Alternatively: python cli.py --config job.toml. Always force local execution: a 2026-07 user report found the bundled CLI sending requests to cloud endpoints until api_url/api_mode were set explicitly. Then apply the generated-music gate.
- Güven: medium · kaynaklar: https://github.com/ace-step/ACE-Step-1.5, https://huggingface.co/ACE-Step/Ace-Step1.5, https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/main/docs/en/INFERENCE.md, https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/main/docs/en/INSTALL.md, https://huggingface.co/mlx-community/ACE-Step1.5-MLX-4bit, https://dev.to/bigkijimon/100-free-fully-local-ai-music-generation-on-an-m1-mac-ace-step-15-two-100-second-vocal-songs-3h1b

### Deterministic, license-clean music with an exact beat grid (work explainers, jingles, loops, stingers)
- **Seçim:** Code-composed MIDI (pretty_midi or mido, MIT) rendered offline with tinysoundfont 0.3.7 (MIT) and the GeneralUser GS v2 or MuseScore_General (MIT) SoundFont, then polished with pedalboard
- Alternatifler: FluidSynth (needs brew, currently blocked); Magenta RT 2 MIDI steering
- Neden: Every beat time is known exactly (n·60/BPM), so cuts cannot slip. There is zero AI-provenance risk, the footprint is tiny and results are reproducible. TinySoundFont renders SF2/SF3 to buffers without an audio device. GeneralUser GS explicitly allows commercial music creation, with an author caveat about sample provenance for software products; MuseScore_General and FluidR3 are MIT.
- Lisans: kod MIT (tinysoundfont, pretty_midi, mido) · ağırlık SoundFonts: MuseScore_General MIT; GeneralUser GS permissive for music made with it · ticari: yes
- Apple Silicon: CPU; trivial cost
- Kurulum: uv pip install tinysoundfont pretty_midi  (tinysoundfont has arm64 wheels for cp38-cp312). Download GeneralUser-GS.sf2 (about 31 MB) from the github.com/mrbumpy409/GeneralUser-GS repo
- Disk: ~40 MB · bakım: tinysoundfont 2025-06-03; pretty_midi 2026-07-28
- Ajan kullanımı: Write the MIDI at a fixed BPM, then synth = tinysoundfont.Synth(); synth.sfload('GeneralUser-GS.sf2'); render to a numpy buffer, write WAV, and add pedalboard reverb/compression. Beat list = exact arithmetic.
- Güven: medium · kaynaklar: https://pypi.org/project/tinysoundfont/, https://pypi.org/pypi/pretty_midi/json, https://github.com/mrbumpy409/GeneralUser-GS, https://scancode-licensedb.aboutcode.org/generaluser-gs-2.0.yml, https://src.fedoraproject.org/rpms/mscore/blob/f36/f/MuseScore_General_License.md

### Ready-made SFX library (UI clicks, whooshes, impacts, ambiences) with clean licenses and no account
- **Seçim:** Kenney audio packs (CC0) plus Sonniss #GameAudioGDC bundles (royalty-free, no attribution), plus OpenGameArt filtered to CC0. Keep a local license ledger
- Alternatifler: Procedural synthesis (next pick). Avoid: Freesound (needs an account), BBC SFX (RemArc, non-commercial), Pixabay scraping (bot protection).
- Neden: Kenney: CC0, direct download with no account and an optional donation ('Continue without donating'). Packs are tiny (Interface Sounds is 100 OGG files in 834.5 KB) and include UI Audio, Impact, Sci-fi, Digital and RPG sets. Sonniss: direct ZIPs from downloads.sonniss.com with no login, 'royalty free and commercially usable', no attribution, unlimited projects. Its restrictions: no reselling raw files and no AI/ML training. Bundles are multi-GB (GDC 2026 is about 7.5 GB), so download individual parts. OpenGameArt licenses vary per asset. The 21 SFX bundled in media-use are under the Pixabay Content License: fine inside videos, not CC0, and not to be redistributed standalone.
- Lisans: kod CC0 (Kenney); Sonniss royalty-free EULA; per-asset on OGA · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: curl each pack's ZIP into /Users/onurkaya/Projects/video/kutuphane/sfx/<source>/ with its LICENSE file and a manifest.json (source URL, license, date)
- Disk: ~50 MB · bakım: Sonniss releases a bundle yearly (2015-2026); Kenney is ongoing
- Ajan kullanımı: Index files with ffprobe and ebur128 (duration, peak, LUFS, tags from the filename) into a manifest. Pick by tag and normalize per category (e.g. UI -24 LUFS short-term). A script must refuse any file without an allowed license entry.
- Güven: high · kaynaklar: https://kenney.nl/assets/category:Audio, https://kenney.nl/assets/interface-sounds, https://sonniss.com/gameaudiogdc, https://rekkerd.org/sonniss-releases-gdc-2026-game-audio-bundle/, https://opengameart.org/content/faq, local: /Users/onurkaya/.claude/skills/media-use/audio/assets/sfx/CREDITS.md

### Procedural/synth SFX by code (whoosh, riser, impact, UI blips) placed sample-accurately on frame events
- **Seçim:** numpy/scipy synthesis with seeded RNG plus pedalboard effects. ffmpeg aevalsrc/anoisesrc for quick tones and noise. ZzFX (MIT) for retro UI blips
- Alternatifler: pyfxr (BSD sfxr port, 2022); Kenney packs
- Neden: Exact timing (a riser can end on the cut frame), zero license risk, fully reproducible. The project already generates SFX with numpy (oto/tanitim-video/ses/v2/efekt.py). pedalboard adds the reverb, filters and saturation that make synthetic sounds less 'beepy'.
- Lisans: kod numpy/scipy BSD; pedalboard GPLv3 (outputs free); ZzFX MIT · ağırlık - · ticari: yes
- Apple Silicon: Native
- Kurulum: uv pip install numpy scipy soundfile pedalboard
- Disk: ~120 MB · bakım: n/a
- Ajan kullanımı: Recipes:
- Whoosh: pink noise × Hann envelope through a band-pass sweeping 300 Hz to 4 kHz, plus a stereo pan sweep.
- Riser: exponential sine sweep plus a noise swell and reverb, peaking 1 frame before the cut.
- Impact: 45-60 Hz sine with a pitch drop, a 5 ms noise transient and a short room reverb.
- UI click: 2-5 ms band-limited burst.
Then check LUFS/peak and a spectrogram PNG.
- Güven: high · kaynaklar: https://github.com/spotify/pedalboard, https://ffmpeg.org/ffmpeg-filters.html, https://www.npmjs.com/package/zzfx

### Text-to-SFX generation when libraries lack a sound (optional, heavy)
- **Seçim:** MOSS-SoundEffect v2.0 (OpenMOSS), MLX 4-bit port mlx-community/MOSS-SoundEffect-v2.0-4bit via the moss-sfx-mlx pipeline
- Alternatifler: Stable Audio Open Small (gated, needs an account). AudioLDM2/MMAudio/AudioX/TangoFlux (non-commercial). ThinkSound (research only). Dasheng-AudioGen (Apache-2.0 but 8.7 GB and CUDA-tested).
- Neden: The only permissively licensed (Apache-2.0 on the HF card and in the GitHub LICENSE), ungated, Mac-native text-to-SFX model found. Output is 48 kHz, up to 30 s, covering foley, ambience, creature and action sounds. It is heavy: 6.4 GB on disk (Qwen3-1.7B text encoder in bf16 about 4 GB, DAC-VAE 1.5 GB, int4 DiT 0.83 GB) and 12.2 GB peak RAM for 30 s on an M5 Max. On M2/16 GB keep clips to 5-10 s and close Chrome renders. The MLX package is third-party, so its maturity is unknown.
- Lisans: kod Apache-2.0 · ağırlık Apache-2.0 (training data not described) · ticari: yes
- Apple Silicon: MLX native
- Kurulum: Not on PyPI when checked; install from GitHub: uv pip install git+https://github.com/xocialize/moss-soundeffect-mlx (repo linked from the HF card). Weights auto-download from HF.
- Disk: ~6700 MB · bakım: Model released 2026-05-26; MLX port 2026-06-12
- Ajan kullanımı: from moss_sfx_mlx.pipeline_mlx import MossSoundEffectPipeline; pipe = MossSoundEffectPipeline.from_pretrained('mlx-community/MOSS-SoundEffect-v2.0-4bit'); audio = pipe(prompt='a heavy wooden door creaks open slowly', seconds=5, num_inference_steps=100, cfg_scale=4.0, seed=0). Check with LAION-CLAP text-audio similarity, transient position and LUFS.
- Güven: low · kaynaklar: https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0, https://huggingface.co/mlx-community/MOSS-SoundEffect-v2.0-4bit, https://raw.githubusercontent.com/OpenMOSS/MOSS-TTS/main/LICENSE, https://github.com/OpenMOSS/MOSS-TTS

### Turkish TTS / voiceover usable for work (commercial) and personal projects
- **Seçim:** VoxCPM2 (OpenBMB, 2B) through mlx-audio 0.5.7: mlx-community/VoxCPM2-8bit (3.2 GB) or -4bit (2.3 GB)
- Alternatifler: - Chatterbox Multilingual v3 (MIT, includes tr; MLX mlx-community/chatterbox-multilingual-v3 is 2.7 GB with --lang_code tr --ref_audio; the PyTorch package pins torch 2.6/numpy<2 and embeds a Perth watermark).
- MOSS-TTS-Nano-100M (Apache-2.0 repo, includes tr, 285 MB, cloning only; its model README calls the license provisional).
- Kokoro has no Turkish.
- Neden: Code and weights are Apache-2.0, explicitly 'free for commercial use'. Supports 30 languages including Turkish with no language tag. Voice Design creates a voice from a text description, so no reference voice and no voice-rights issue. It can also clone (e.g. the user's own voice) with style control, and outputs 48 kHz. Vendor-reported Turkish results (2026): WER 0.82% on Minimax-MLS (ElevenLabs 0.70, FishAudio S2 0.87), the highest speaker similarity among the systems compared, and 1.65% WER on its internal benchmark. MLX-native, no torch.
- Lisans: kod Apache-2.0 · ağırlık Apache-2.0 · ticari: yes
- Apple Silicon: MLX native; generation speed on base M2 not verified
- Kurulum: uv tool install --python 3.12 --prerelease=allow 'mlx-audio[tts,stt,sts]'   (deps: mlx, transformers>=5.14, numpy, scipy; no torch). Weights download from HF on first use.
- Disk: ~3000 MB · bakım: VoxCPM2 released 2026-04 (HF updated 2026-08-18); mlx-audio 0.5.7 released 2026-09-28 (very active)
- Ajan kullanımı: Voice design: mlx_audio.tts.generate --model mlx-community/VoxCPM2-8bit --text 'Merhaba, bugün size ürünümüzü tanıtacağım.' --instruct 'A calm, warm male voice in his thirties' --output_path vo/
Cloning: add --ref_audio me.wav --ref_text '<exact transcript>'.
Python: from mlx_audio.tts.utils import load; next(load('mlx-community/VoxCPM2-8bit').generate(text=..., instruct=...)).
Gate every take with Whisper CER (techniques).
- Güven: medium · kaynaklar: https://huggingface.co/openbmb/VoxCPM2, https://github.com/OpenBMB/VoxCPM, https://raw.githubusercontent.com/OpenBMB/VoxCPM/main/LICENSE, https://huggingface.co/mlx-community/VoxCPM2-8bit, https://raw.githubusercontent.com/Blaizzy/mlx-audio/main/mlx_audio/tts/models/voxcpm2/README.md, https://github.com/Blaizzy/mlx-audio, https://pypi.org/pypi/mlx-audio/json, https://huggingface.co/mlx-community/chatterbox-multilingual-v3, https://github.com/resemble-ai/chatterbox, https://pypi.org/pypi/chatterbox-tts/json, https://huggingface.co/OpenMOSS-Team/MOSS-TTS-Nano-100M

### English TTS (fast drafts, product-demo narration)
- **Seçim:** Kokoro-82M through 'hyperframes tts' (kokoro-onnx), with HYPERFRAMES_PYTHON pointing to a uv Python 3.12 venv. Alternatively Kokoro in mlx-audio
- Alternatifler: VoxCPM2 (English, voice design); Chatterbox-Turbo (English, MIT, 350M)
- Neden: Apache-2.0 weights, about 330 MB, fast, 54 voices, and already wired into the HyperFrames CLI. The system Python 3.14 cannot install kokoro-onnx (requires <3.14), and HyperFrames honours the HYPERFRAMES_PYTHON override. Languages are EN, JA, ZH, FR, ES, IT, PT and HI: no Turkish.
- Lisans: kod Kokoro Apache-2.0; kokoro-onnx wrapper permissive (PyPI license field empty, verify) · ağırlık Apache-2.0 · ticari: yes
- Apple Silicon: ONNX Runtime CPU (or MLX through mlx-audio)
- Kurulum: uv venv --python 3.12 /Users/onurkaya/Projects/video/.venv-tts && uv pip install --python /Users/onurkaya/Projects/video/.venv-tts kokoro-onnx soundfile
- Disk: ~450 MB · bakım: kokoro-onnx 0.6.1 released 2026-08-19
- Ajan kullanımı: HYPERFRAMES_PYTHON=/Users/onurkaya/Projects/video/.venv-tts/bin/python HYPERFRAMES_NO_TELEMETRY=1 npx hyperframes tts 'Welcome to the demo' -o narration.wav
- Güven: high · kaynaklar: https://huggingface.co/hexgrad/Kokoro-82M, https://pypi.org/pypi/kokoro-onnx/json, local: /Users/onurkaya/.claude/skills/media-use/audio/references/requirements.md, local: /Users/onurkaya/.claude/skills/media-use/audio/scripts/lib/python.mjs

### Speech-to-text as the agent's 'ears' (TTS intelligibility gates, Turkish/English word timings, lyric checks)
- **Seçim:** Whisper large-v3-turbo on MLX through mlx-whisper 0.4.3 (mlx-community/whisper-large-v3-turbo-8bit, 864 MB); mlx-audio STT as an alternative
- Alternatifler: whisper.cpp ggml-large-v3-turbo-q5_0 (574 MB) via pywhispercpp wheels (MIT); mlx-audio Whisper / Qwen3-ASR
- Neden: Whisper's MIT weights are strong on Turkish, give word timestamps and run MLX-native. 'hyperframes transcribe' needs whisper.cpp from Homebrew (blocked) or a cmake source build. Needed for CER/WER acceptance gates and for checking vocal leakage in instrumentals.
- Lisans: kod MIT (mlx-whisper, Whisper) · ağırlık MIT · ticari: yes
- Apple Silicon: MLX (Metal)
- Kurulum: uv pip install --python /Users/onurkaya/Projects/video/.venv mlx-whisper jiwer
- Disk: ~900 MB · bakım: mlx-whisper 2025-08-29; MLX Whisper weights updated 2025-12
- Ajan kullanımı: import mlx_whisper; r = mlx_whisper.transcribe('vo.wav', path_or_hf_repo='mlx-community/whisper-large-v3-turbo-8bit', language='tr', word_timestamps=True); then use jiwer.cer/wer against the script after Turkish-aware normalization.
- Güven: high · kaynaklar: https://pypi.org/pypi/mlx-whisper/json, https://huggingface.co/mlx-community/whisper-large-v3-turbo-8bit, https://huggingface.co/ggerganov/whisper.cpp, https://pypi.org/pypi/jiwer/json

### Objective audio QA, so the agent can 'listen' through numbers and images
- **Seçim:** ffmpeg astats, ebur128, silencedetect, axcorrelate, showspectrumpic and showwavespic, plus mir_eval 0.8.2 (beat F-measure) and jiwer 4.0 (WER/CER). Optional: audiobox-aesthetics (CC-BY-4.0) and LAION-CLAP (Apache-2.0)
- Alternatifler: pystoi/pesq (need a clean reference)
- Neden: Covers loudness, true peak, clipping, DC offset, gaps, sync lag, beat alignment, intelligibility and prompt adherence. Spectrogram and waveform PNGs can be opened with the image reader. hyperframes-audio/references/diagnosis.md mandates comparison-based diagnosis, never absolute spectra of a single voice. audiobox-aesthetics gives production-quality and enjoyment proxy scores for ranking generated variants.
- Lisans: kod ffmpeg GPL; mir_eval MIT; jiwer Apache-2.0; audiobox-aesthetics CC-BY-4.0; laion-clap CC0 code · ağırlık audiobox-aesthetics CC-BY-4.0 (831 MB); laion/clap-htsat-unfused Apache-2.0 (618 MB) · ticari: yes
- Apple Silicon: CPU / torch CPU for the optional models
- Kurulum: uv pip install mir_eval jiwer  (optional: audiobox_aesthetics laion-clap)
- Disk: ~50 MB · bakım: mir_eval 2025-02; jiwer 2025-06; audiobox-aesthetics 2025-05
- Ajan kullanımı: See the techniques list for exact thresholds.
- Güven: high · kaynaklar: https://pypi.org/pypi/mir_eval/json, https://pypi.org/pypi/jiwer/json, https://huggingface.co/facebook/audiobox-aesthetics, https://huggingface.co/laion/clap-htsat-unfused, local: /Users/onurkaya/.claude/skills/hyperframes-audio/references/diagnosis.md, https://www.forasoft.com/learn/audio-for-video/articles-audio/lip-sync-itu-r-bt-1359-tolerance-windows

### Python runtime and isolation for all of the above
- **Seçim:** uv 0.12.x (standalone installer) with uv-managed CPython 3.12. One 'uv tool install' per CLI, plus one shared script venv
- Alternatifler: python.org 3.12 installer plus venv
- Neden: System Python 3.14.7 is too new or too fragmented for this stack:
- numpy 2.5, scipy 1.18, librosa 1.0 and jax 0.11 need Python ≥3.12.
- kokoro-onnx needs <3.14.
- soxr's arm64 wheels skip cp313.
- chatterbox-tts pins torch 2.6 and numpy<2 below 3.13.
- torchaudio stopped at 2.11 while torch is at 2.14.1, but audio-separator wants torch ≥2.13.
So use 3.12 with per-tool isolation. uv clones packages from its cache on APFS, so duplicate torch copies cost little disk. Homebrew-only paths are out until the Xcode licence is accepted.
- Lisans: kod MIT OR Apache-2.0 · ağırlık - · ticari: yes
- Apple Silicon: Native
- Kurulum: curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh   (or python3 -m pip install --user uv), then uv python install 3.12, then uv venv --python 3.12 /Users/onurkaya/Projects/video/.venv
- Disk: ~150 MB · bakım: uv 0.12.23 released 2026-10-03
- Ajan kullanımı: uv tool install --python 3.12 beat-this ; uv tool install --python 3.12 demucs ; uv pip install --python .venv numpy scipy soundfile soxr pyloudnorm pedalboard librosa mir_eval jiwer tinysoundfont pretty_midi mlx-whisper
- Güven: high · kaynaklar: https://pypi.org/pypi/uv/json, https://pypi.org/pypi/numpy/json, https://pypi.org/pypi/torchaudio/json, https://pypi.org/pypi/torch/json, https://pypi.org/pypi/soxr/json, https://pypi.org/pypi/jax/json

## Kaçınılacaklar

- **MusicGen (facebook/musicgen-*), which is HyperFrames media-use's offline BGM fallback** — Weights are CC-BY-NC-4.0, so no work or commercial use. It also only generates about 30 s seeds and then crossfade-loops them.
- **Stable Audio Open 1.0 / Stable Audio Open Small** — HF repos are gated (gated=auto: login and accepting terms), which violates the no-account rule. The Stability AI Community License also has a $1M revenue cap.
- **AudioLDM2, AudioGen, MMAudio, AudioX / AudioX-Turbo** — Non-commercial weights: AudioLDM2 is CC-BY-NC-SA-4.0; AudioGen, MMAudio and AudioX are CC-BY-NC-4.0. AudioX-Turbo is also 23 GB.
- **TangoFlux; ThinkSound / PrismAudio** — TangoFlux checkpoints are 'non-commercial research use only' and also fall under the Stable Audio Open license. ThinkSound's README says 'research and educational purposes only. Commercial use is NOT permitted', despite the Apache-2.0 tag on HF.
- **HunyuanVideo-Foley, SAM-Audio** — Tencent Hunyuan community license and Meta SAM license (manually gated). Both are far beyond 16 GB RAM / 18 GB disk (SAM-Audio is 12-15 GB).
- **YuE / YuE2, SongGeneration, HeartMuLa-3B, MiniMax Music 3, Dasheng-AudioGen** — Infeasible or encumbered: YuE 7B needs about 24 GB VRAM-class hardware; YuE2-3B is CC-BY-NC-4.0; SongGeneration's license is unknown (11 GB); HeartMuLa is Apache-2.0 but 15.7 GB; MiniMax Music 3 has a community license and is ≥9.2 GB even at 4-bit; Dasheng-AudioGen is 8.7 GB and CUDA-tested.
- **XTTS-v2 (Coqui)** — Coqui Public Model License is non-commercial. Coqui is defunct, so no commercial licence can be bought.
- **F5-TTS, OmniVoice, Higgs TTS 3 (higgs-audio-v3), Meta MMS-TTS (tur)** — Non-commercial weights: F5 and MMS are CC-BY-NC; OmniVoice is CC-BY-NC because of Emilia data, despite Apache code; Higgs TTS 3 has a research/non-commercial license and is 9.3 GB.
- **Piper Turkish voices (tr_TR-dfki, fahrettin, fettah) for work** — dfki's dataset is CC BY-NC-SA 4.0. fahrettin/fettah use CC0 data but are fine-tuned from the Lessac base, whose Blizzard dataset is non-commercial, so they are ambiguous. Only dfki is in the official piper-voices repo. Piper's engine is now GPL-3.0 (piper1-gpl). Personal use only.
- **macOS 'say' system voices (e.g. Turkish Yelda)** — The macOS SLA allows System Voices only 'for your personal, non-commercial use'; publishing in a commercial context is prohibited.
- **KugelAudio-0-open** — MIT and supports Turkish, but 18.7 GB (7B): impossible with 18 GB free.
- **'hyperframes beats', and home-made numpy or librosa constant-grid beat trackers on acoustic/live music** — It combines RMS peak picking, bpm-detective's integer-rounded BPM and regularizeBeats(), which emits a constant grid. Any BPM error or real tempo drift accumulates, e.g. 0.05 BPM is about 0.18 s after 352 beats. This is the mechanism behind 'audio slipping'.
- **madmom, allin1, BeatNet, Essentia (for beat tracking)** — madmom models are CC BY-NC-SA 4.0 and its PyPI release is an sdist only, from 2018. allin1 (2023) depends on madmom and NATTEN. BeatNet is stale (2023). Essentia is AGPL-3.0 and its TF models are non-commercial.
- **Demucs [quantized] extra (mdx_q, mdx_extra_q)** — Requires diffq, licensed CC-BY-NC-4.0. Use htdemucs/htdemucs_ft instead.
- **Community BS-RoFormer/UVR weights (e.g. model_bs_roformer_ep_317_sdr_12.9755) for work** — Weight license unknown/unspecified. Fine to test on personal projects; for commercial work use Demucs or the MIT Kim Mel-Band RoFormer.
- **Resemble Enhance; the DeepFilterNet Python package** — Resemble Enhance (2023) pins torch 2.1.1, deepspeed 0.12.4 and gradio 4.8, with no macOS-friendly path. The DeepFilterNet Python package pins numpy<2 and breaks with newer torchaudio. Use the Rust deep-filter binary or the MLX ports instead.
- **Freesound, BBC Sound Effects, Pixabay/YouTube Audio Library downloads** — Freesound needs an account to download. BBC SFX are under the RemArc licence (personal, educational or research use only), so not for work. Pixabay is behind bot protection and YouTube needs a Google account. Already-bundled Pixabay SFX in media-use are fine.
- **media-use cloud routes (HeyGen TTS/BGM/SFX, ElevenLabs, Gemini TTS, Lyria)** — They need accounts or API keys and send text/audio to external services, violating the user's rules.
- **ACE-Step start scripts or CLI run as-is** — CHECK_UPDATE defaults to true, the download source may auto-select (e.g. ModelScope), and a 2026-07 report found the bundled CLI defaulting to cloud endpoints. Drive the Python API with explicit local settings and offline environment variables.

## Teknikler

### Per-beat cut grid (never a constant BPM)
1. Convert the song to WAV and run beat_this with final0, final1 and final2 on CPU.
2. Build consensus beats (beats matched within ±35 ms across seeds, median time) and downbeats.
3. Compute inter-beat intervals (IBI) and local tempo per 8 bars.
4. If seeds disagree, or the IBI coefficient of variation in a section is above about 4-6%, mark the section rubato and cut on phrase starts or strong onsets with 6-12-frame dissolves instead of hard cuts.
5. Snap each planned cut to the nearest consensus beat or downbeat, then to the nearest frame (at most 16.7 ms at 30 fps).
6. Write <project>/beats/<audio>.json in HyperFrames format so Studio displays it.

**Doğrulama:** - mir_eval.beat.f_measure between seeds ≥0.9 (report and switch to phrase cuts if <0.8).
- Median |beat - nearest onset-strength peak| ≤25 ms.
- Residual of a linear fit (beat time vs index): if it exceeds 50 ms anywhere, a constant grid is provably invalid for this song.
- After render, detect cuts (select='gt(scene,0.3)',showinfo) and require p95 |cut - beat| ≤1 frame and max ≤2 frames.
- Give the user a 3×10 s click-track preview (clicks at beats, -12 dB) for a 30-second ear check.

### Render-level A/V sync audit (catch 'slipping' numerically)
After every render, extract the MP4 audio (48 kHz mono) and compute windowed cross-correlation against the source music WAV, and against each kept clip's original audio. Use about 10 windows of 3 s spread over the timeline (numpy FFT xcorr, or ffmpeg axcorrelate). Also run ffprobe for start_time and duration of the audio and video streams of every source clip and of the output.

**Doğrulama:** - The lag is constant across windows (max - min ≤5 ms) and the absolute lag is ≤10 ms. Monotonic growth means drift (sample-rate mislabel, VFR handling, or concatenated AAC); a constant offset means a start_time or edit-list mismatch.
- |audio_duration - video_duration| < 1/fps.
- Keep far inside ITU-R BT.1359 detectability (audio early >45 ms or late >125 ms is noticeable).

### Normalize phone clips before editing
Run ffprobe on each source: compare r_frame_rate with avg_frame_rate (they differ for VFR), and check stream start_time and sample_rate. Convert to CFR with the fps=30 filter (timestamp-based; never -r as an input option or setpts=N/..). When clip sound is kept, convert it with aresample=48000:async=1:first_pts=0. For slow motion, either mute the clip audio (bed only) or stretch it by exactly the same factor with Rubber Band; never leave normal-speed audio under slowed picture.

**Doğrulama:** For each clip: |audio_dur - video_dur| < 1 frame; both start_times are 0; stretched audio has exactly samples_in × factor samples (±1); a cross-correlation check against the source shows lag ≤10 ms.

### One continuous audio master, encoded once
Render or mix bed, clip sounds, SFX and voiceover into a single 48 kHz float WAV (HyperFrames render, or offline numpy/ffmpeg amix with normalize=0). Encode AAC once at 192-256 kb/s and mux with -c:v copy. Never concat-demux AAC segments: each join adds encoder priming/padding.

**Doğrulama:** - Output audio duration equals video duration within 1 frame.
- silencedetect (noise=-60dB:d=0.05) finds no unintended gaps in music-only regions.
- The sync audit lag is constant.

### Click-free edits and musical splices
- Put a 5-10 ms afade (or HyperFrames data-fade-in/out ≥0.01) on every hard audio cut.
- For music edits, use equal-power acrossfade (c1=qsin:c2=qsin, 20-80 ms) at downbeats, starting 10-20 ms before the incoming transient.
- Prefer 4- or 8-bar phrase boundaries, and use the Demucs drums stem to place transients exactly.

**Doğrulama:** - Click detector within ±5 ms of each edit: max |x[n]-x[n-1]| ≤3× the clip's 99th-percentile derivative, and >4 kHz band energy no more than +6 dB above the ±50 ms neighbours.
- Momentary loudness step ≤1 LU.
- IBI across the splice within ±2% of the local median.
- Chroma cosine similarity across the splice ≥0.8.
- The spectrogram PNG shows no vertical broadband line.

### Music-structure-driven edit map (craft, not captions)
Segment the song using downbeats, onset density (librosa onset_strength), RMS energy and phrase boundaries. Map visual tempo to musical density: slow motion and long holds on sustained, low-onset passages; faster cutting on high-density passages; transitions such as whip, zoom punch-in or dissolve on phrase boundaries; a 1-2 beat 'breath' (bed duck or drop) before key reveals. Lead natural sound bites 4-12 frames before their picture (J-cut) or let them trail (L-cut). Risers and whooshes end exactly on the cut frame.

**Doğrulama:** The plan JSON records, for every cut or transition, its musical anchor (downbeat, phrase or onset) and the measured offset. Cut rate per section should correlate positively with onset density. Every SFX hit should sit within ±1 frame of its picture event.

### Ducking under voiceover and natural sound
Detect speech or laughter regions with Silero VAD or an RMS gate. Automate bed gain -8 to -15 dB with about 120 ms pre-roll, 80 ms attack and 450 ms release, using HyperFrames data-automation or carve.mjs. Offline fallback: ffmpeg sidechaincompress.

**Doğrulama:** - Render stems separately: in speech regions, short-term LUFS(VO or bite) minus LUFS(bed) ≥10 LU (HyperFrames narration guide: bed about -31 LUFS under voiceover).
- Bed level outside the ducks is unchanged (±0.5 LU).
- Whisper WER on the final mix is within 2 points of the voiceover-only stem.

### Delivery loudness, two-pass linear
Run loudnorm pass 1 with print_format=json, then pass 2 with the measured_I/TP/LRA/thresh and offset values, linear=true, followed by aresample=48000. Alternatively keep betikler/ustala.sh (measure, gain, alimiter). Targets: music-led social -14 LUFS integrated; speech-led -16 LUFS; true peak ≤-1.0 dBTP (-1.5 before AAC for headroom).

**Doğrulama:** - The loudnorm JSON reports normalization_type 'linear' (if 'dynamic', the output was upsampled to 192 kHz and its dynamics changed).
- ebur128 I is within ±0.5 LU of target and true peak is at or under target.
- ffprobe shows sample_rate 48000.
- astats Peak_level is below -1 dBFS with Flat_factor about 0 (no clipping).

### TTS acceptance gate (Turkish-aware)
1. Generate 2-3 takes per sentence with fixed seeds.
2. Trim leading/trailing silence and normalize to -16 LUFS.
3. Transcribe with Whisper large-v3-turbo (language='tr', word timestamps).
4. Normalize text Turkish-aware: map İ→i and I→ı before lowercasing (Python's lower() turns İ into i plus a combining dot), strip punctuation, spell numbers consistently.
5. Score with jiwer CER/WER and keep the best take. Get one user approval of the voice before batch production.

**Doğrulama:** - CER ≤3% (WER ≤8%), with no inserted or dropped words.
- 10-18 chars/s.
- No internal silence >0.7 s (silencedetect).
- LUFS and true peak on target.
- The chosen take's seed and settings are logged.

### Generated-music acceptance and provenance ledger
For ACE-Step, pass bpm, keyscale, timesignature, duration and seed; for Magenta RT 2, log prompt, model and seed. Render 2-4 variants and measure them. Store a JSON ledger next to each WAV: model, version, weight file hashes, prompt, seed, date and license.

**Doğrulama:** - beat_this tempo within ±1 BPM of the request, and IBI CV <2% (generated music should be steady).
- Chroma key estimate matches the request.
- Instrumental tracks: the Demucs vocals stem is ≥30 dB below the mix, or Whisper returns no words.
- Duration is exact; LUFS and true peak are on target.
- Optional: rank variants by audiobox-aesthetics (production quality, enjoyment).
- No artist names appear in prompts.

### Offline and telemetry guard for local AI tools
Export HF_HUB_DISABLE_TELEMETRY=1, DO_NOT_TRACK=1, GRADIO_ANALYTICS_ENABLED=False and HYPERFRAMES_NO_TELEMETRY=1. After the first model download, set HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1. For ACE-Step set CHECK_UPDATE=false and --download-source huggingface, and use the Python API rather than the CLI or cloud defaults. Never put personal text in prompts sent anywhere.

**Doğrulama:** During a generation run, 'lsof -nP -iTCP -a -p <pid>' (or 'nettop -p <pid> -l 1') shows no remote connections. A rerun with Wi-Fi off gives identical output.

### Disk budget and cache hygiene
Run 'df -h /' before every download over 1 GB and keep ≥5 GB free for renders. Use one HF cache (~/.cache/huggingface/hub) and remove a model's folder when the project is done. Install heavy generators only when a task needs them, and uninstall them with 'uv tool uninstall'. Watch ~/Documents/Magenta and the ACE-Step checkpoints directory.

**Doğrulama:** Log 'du -sh ~/.cache/huggingface ~/Documents/Magenta <ace-step>/checkpoints ~/.local/share/uv' before and after each task; free space never drops below 5 GB.

### Visual stand-ins for listening
Render showspectrumpic=s=1600x600:legend=1 and showwavespic PNGs of stems and the final mix. Plot the onset-strength curve with beat, cut and duck markers (matplotlib). Open the images with the image reader to look for clicks (vertical lines), gaps, clipping (flat tops), missing highs and duck depth.

**Doğrulama:** Every visual finding must agree with the numeric checks. Report disagreements as uncertainty and do not guess.

### Fit the music bed by editing, not stretching
Shorten or lengthen at bar or phrase boundaries using the splice technique. Stretch only within ±3%, with Rubber Band R3 (-3 -T ratio). End on the song's real cadence or a final downbeat with a 1-3 s fade.

**Doğrulama:** - The new beat_this tempo equals original × factor (±0.3%).
- The last cut sits on the final downbeat (±1 frame).
- The tail decays below -60 dBFS before the file ends.

### Comparison-based diagnosis (never absolute)
Follow /Users/onurkaya/.claude/skills/hyperframes-audio/references/diagnosis.md: compare against the clean original, the pauses, the file's own spectral tilt and the file over time. When neither an original nor usable pauses exist, report 'under-determined' and do not invent a metric.

**Doğrulama:** Every claimed defect is backed by a before/after or within-file comparison number.


## Riskler

- Homebrew is unusable right now: 'brew info' fails with 'You have not agreed to the Xcode license' (xcode-select points at Xcode.app). Brew-only tools (rubberband, sox, fluidsynth, whisper-cpp, espeak-ng) stay unavailable until the user runs 'sudo xcodebuild -license accept' or 'sudo xcode-select -s /Library/Developer/CommandLineTools'. The recommended stack avoids brew entirely.
- Disk: df shows 19 GiB free.
- Core stack: about 5.5 GB.
- Heavy options, each on its own: ACE-Step 5.3-10 GB, MOSS-SFX 6.4 GB, Magenta RT 2 small 2.4 GB, Chatterbox v3 2.7 GB, VoxCPM2 2.3-3.2 GB.
- Renders: one 4:48 CRF-16 render was 2.5 GB.
Not everything can coexist. Install generators on demand, delete caches afterwards, and check 'df -h /' before every download over 1 GB.
- 16 GB unified memory is shared between MLX models and HyperFrames' headless Chrome render. MOSS-SFX peaked at 12.2 GB for 30 s on an M5 Max. Never run generation and rendering at the same time.
- Licenses and training-data claims for ACE-Step, VoxCPM2, MOSS and Magenta RT 2 are vendor-declared and cannot be independently audited, and generative output can resemble existing songs. Keep a provenance ledger, never prompt with artist names, and prefer MIDI/SoundFont or CC0 for high-stakes commercial deliverables.
- Even a SOTA tracker can fail on rubato or soft acoustic songs. Require agreement across beat_this seeds, a human 30-second click-track check, and a phrase-based fallback with dissolves instead of hard cuts.
- Rule conflict: the music-to-video skill says its analyze-beatgrid.py (librosa beat_track) is the ONLY beat analyzer and must not be re-measured. For calm or acoustic tracks this contradicts the recommended beat_this workflow, so the orchestrator must decide whether to override.
- Privacy and network leaks:
- The ACE-Step CLI was reported (2026-07) to call cloud endpoints by default.
- ACE-Step start scripts run update checks.
- Gradio UIs (ACE-Step, chatterbox, voxcpm) send analytics unless GRADIO_ANALYTICS_ENABLED=False.
- HF downloads contact huggingface.co.
After the first download, set HF_HUB_OFFLINE=1, HF_HUB_DISABLE_TELEMETRY=1 and DO_NOT_TRACK=1, and check with lsof or nettop that no remote connections are made.
- Dependency drift:
- torchaudio's last release is 2.11.0 (2026-03-23) while torch is at 2.14.1, so tools that need torchaudio (beat-this) may pin older torch.
- audio-separator on Apple Silicon requires torch ≥2.13, so keep them in separate 'uv tool' envs.
- librosa 1.0, numpy 2.5 and jax need Python ≥3.12.
- The system Python (python.org 3.14) lacks CA certificates for urllib: SSL CERTIFICATE_VERIFY_FAILED was observed. Scripts using urllib will fail; use curl, requests/certifi, or a uv-managed Python.
- GPL tools (pedalboard, Rubber Band, matchering, Piper) are fine for producing media, but embedding them in distributed work software triggers GPL obligations. The bundled ffmpeg-static build is GPL+nonfree and must not be redistributed.
- AI voice ethics: the Chatterbox PyTorch package embeds an imperceptible Perth watermark, and the VoxCPM2 terms forbid impersonation. Clone only voices with consent (e.g. the user's own), never the partner's without permission, and label AI narration in work content where required.
- Third-party MLX conversions (mlx-community ports, moss-sfx-mlx, ACE-Step MLX) can lag behind upstream or differ in quality. Every output must pass the numeric gates.
- Unsigned downloaded binaries (deep-filter, rubberband) can be blocked if fetched with a browser (quarantine). Fetch with curl, and ad-hoc sign with 'codesign -s - -f' if macOS kills them.
- Magenta RT 2 stores models in ~/Documents/Magenta. If iCloud 'Desktop & Documents' sync is on, GBs of weights would upload to iCloud and use cloud quota.
- Sonniss EULA: no AI/ML training on the sounds and no redistribution of raw files. OpenGameArt licenses differ per asset (CC-BY/GPL require attribution or copyleft), so only CC0 should go into the library without a ledger review.
- Turkish TTS quality claims are vendor benchmarks. Real Turkish prosody and name/number pronunciation must be checked with Whisper CER and one user listening pass before batch production.

## Açık sorular

- Which platforms are the deliverables for: Instagram Reels, TikTok, YouTube or WhatsApp for personal; web, LinkedIn or product pages for work? This sets loudness (-14 vs -16 LUFS), codec and aspect.
- Disk approval: is it OK to install the about 5.5 GB core stack, and heavy generators (ACE-Step 5-10 GB, MOSS-SFX 6.4 GB, Magenta 2.4 GB) only on demand? Can the 2.5 GB draft renders/ilk-montaj-v1.mp4 be deleted?
- Will the user accept the Xcode licence (sudo) to unlock Homebrew (rubberband, sox, whisper-cpp, fluidsynth), or should the brew-free stack stay?
- Turkish voice: a designed synthetic voice (VoxCPM2 instruct), or cloning the user's own voice? Cloning needs 10-30 s of clean speech and explicit consent.
- Is visible attribution acceptable in work videos? That unlocks CC-BY music (incompetech/Kevin MacLeod) and courtesy credit for CC-BY model weights.
- For the past montage, which did 'sesler kaymış' (audio slipped) mean: cuts off the beat, clip sounds out of lip-sync, or the music drifting against the picture? Timestamps of the worst moments would let the sync audit confirm the cause.
- Should the orchestrator override the music-to-video skill's 'only analyze-beatgrid.py' rule for calm or acoustic songs and use beat_this instead?
- Is the Magenta RT model path configurable away from ~/Documents (iCloud sync)? This was not verified.
- Unverified details to test on first use: Magenta RT 'mrt' output-path and model-argument flags; whether Chatterbox MLX has a default voice when no ref_audio is given; real generation speed of VoxCPM2 and ACE-Step on a base M2; whether ACE-Step's MLX-4bit route exposes bpm/keyscale.
- Session note: the claude.ai Google Drive connector is not authorized in this non-interactive session. Authorize it in claude.ai connector settings if it is ever needed; this research did not need it.

## Şüpheci doğrulama

The researcher's licensing and maintenance claims mostly hold. I checked them on 2026-10-05 against PyPI JSON, the Hugging Face API and cards, GitHub source, and local code. The diagnosis of the old failure is also right: HyperFrames 'beats' builds a constant grid from an integer BPM, and the music-to-video analyzer relies on librosa's global-tempo beat tracking. The 76.005 BPM figure in ilk-montaj/kurgu.py cannot be re-checked because that folder is gone.

I ran a few local measurements:
- Beat This! takes about 2 s per seed on the M2 and also runs on MPS through the Python API. On a synthetic drifting-tempo track, the seeds agree at F=0.995, while a constant grid was off by up to 0.65 s.
- Demucs 4.1.0 runs on MPS 2.5-5x faster than CPU, with identical results when --shifts is 0.

Several install and usage instructions would fail on this Mac:
1. beat-this alone cannot read audio. torchaudio 2.11 needs TorchCodec plus system FFmpeg libraries, and soundfile is not a dependency, so it needs '--with soundfile'.
2. 'mlx-audio[...,sts]' and audio-separator cannot install. There is no working compiler while the Xcode license is unaccepted (clang itself refuses to run), and audio-separator also hard-requires diffq, which is non-commercial.
3. The chosen mlx-whisper repo, whisper-large-v3-turbo-8bit, is in the wrong weight format for mlx-whisper.
4. Sonniss sits behind a Cloudflare challenge, so the agent cannot script downloads. The user has to download in a browser.
5. laion-clap conflicts with numpy 2.

Other corrections: ACE-Step's disk need is underestimated (about 9-10 GB, not 7 GB). The ACE-Step 'cloud endpoint' claim is not supported by the current code. TinySoundFont lacks modulators, so GeneralUser GS will sound degraded. MAGENTA_HOME and 'mrt models download NAME' resolve two of the open questions.

The picks themselves are still the best permissive options I could find. I found no better commercially clean alternatives:
- Turkish TTS: VoxCPM2, confirmed Apache-2.0 with strong vendor Turkish results.
- Beats: Beat This!
- Stems: Demucs.
- Music: Magenta RT 2 and ACE-Step.
- Speech enhancement: DeepFilterNet3 or MossFormer2.

Free disk is shrinking while parallel agents install (19 GiB down to 16 GiB). Accepting the Xcode license or switching xcode-select is the main prerequisite to unlock, and that needs the user to run one sudo command. Web search budget was exhausted mid-task, so newer 2026 alternatives could only be checked through the PyPI/HF APIs and the mlx-audio catalog. I have medium confidence that nothing better was missed.

### Kontroller

- [confirmed] Beat This! (beat_this 1.1.0, 2026-04-14) is MIT for code and weights. final0/1/2 are three seeds, each about 78 MB. — PyPI lists 1.0 (2026-04-13) and 1.1.0 (2026-04-14), license MIT, py3-none-any. The README says: 'The code and the published model weights are released under the MIT license.' final0-2 are trained on all data except GTZAN, each with a different seed. The local copies in modeller/torch/hub (downloaded by a parallel agent) are 81,058,141 bytes each. (https://pypi.org/pypi/beat-this/json ; https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md)
- [confirmed] beat_this runs in seconds on the M2 CPU. MPS is undocumented. A constant grid fails when the tempo drifts. — Measured 2026-10-05 in /Users/onurkaya/Projects/video/ortamlar/ses (torch 2.14.1) on a synthetic 90 s track that drifts 72→80→72 BPM. Each of final0/1/2 took about 2.0 s on CPU including model load. F-measure against the true beats: 1.000, 0.986 and 0.972. Agreement between seeds: F=0.995. The Python API with device='mps' works (1.4 s) and gives identical beat times. The CLI only picks cuda or cpu (cli.py lines 127-131), so MPS is reachable only through the API. The best constant-BPM fit to the same beats was up to 0.653 s off. (local benchmark; ortamlar/ses/lib/python3.12/site-packages/beat_this/cli.py)
- [refuted] 'uv tool install --python 3.12 beat-this' gives a working CLI. — beat_this load_audio tries torchaudio.load, then soundfile, then madmom. torchaudio 2.11.0 (2026-03-23) is the last release and declares no dependencies; its load() needs TorchCodec ('ImportError: If torchcodec is not available'). The torchcodec 0.17.0 macOS wheel does not bundle libavcodec, so it also needs FFmpeg shared libraries, which would come from brew (blocked). soundfile is not anywhere in beat-this's dependency tree (numpy, torch, torchaudio, einops, rotary-embedding-torch→einops/torch, soxr→numpy). It only worked in ortamlar/ses because soundfile 0.14.0 arrived with other packages. (ortamlar/ses/.../beat_this/preprocessing.py; torchaudio/_torchcodec.py; https://pypi.org/pypi/torchcodec/json)
- [refuted] torchaudio stopped at 2.11 while torch is at 2.14.1, so tools that need torchaudio may pin an older torch. — torchaudio 2.11.0 has no requires_dist. uv installed torch 2.14.1 and torchaudio 2.11.0 together. Tested: MelSpectrogram runs and beat_this imports. The real breakage is audio file I/O (TorchCodec), not torch version pinning. (https://pypi.org/pypi/torchaudio/json ; ortamlar/ses-kurulum.log; local import test)
- [confirmed] 'hyperframes beats' takes RMS peaks, uses bpm-detective's integer BPM, and regularizeBeats() turns that into a constant grid. — In beat-analyzer.global.js, bpm-detective@2.0.5 does theoreticalTempo = Math.round(...). When the onset BPM and the bpm-detective BPM differ by less than 5%, it calls octaveAlignBpm(detectiveBpm). Between 5% and 10% it uses Math.round(avg). Either way regularizeBeats emits t += 60/bpm from the best offset. Above 10% disagreement it returns the raw RMS peaks. Output is beats/<audio>.json {version:1,audio,beats:[{time,strength}]}. The drift arithmetic holds: 352×(60/76.005−60/76.055)=0.183 s, and 0.3 BPM over 290 s ≈ 1.1 s. (/Users/onurkaya/Projects/video/node_modules/hyperframes/dist/beat-analyzer.global.js ; dist/beats-GAROPWZX.js)
- [confirmed] music-to-video analyze-beatgrid.py uses librosa beat_track (near-constant tempo). The skill says it is the ONLY analyzer. — Line 70 calls librosa.beat.beat_track(...). In librosa 1.0.0 the defaults are bpm=None (a global tempo via aggregate=np.median) and tightness=100. SKILL.md lines 22 and 62 say 'the only beat analyzer … on calm music the grid is a metronome the tracker imposed'. (/Users/onurkaya/.claude/skills/music-to-video/scripts/analyze-beatgrid.py ; SKILL.md)
- [uncertain] ilk-montaj/kurgu.py cut to a fixed 76.005 BPM grid. — ilk-montaj/, renders/, betikler/ and kaynak/ no longer exist under /Users/onurkaya/Projects/video, and mdfind finds no kurgu.py. CLAUDE.md still says kurgu.py held the 'vuruş ızgarası' (beat grid). The 76.005 figure cannot be re-checked. (local filesystem 2026-10-05)
- [confirmed] Homebrew is blocked by the unaccepted Xcode license. — 'brew info rubberband' (Homebrew 7.0.1) prints 'Error: You have not agreed to the Xcode license'. The problem is wider than brew: 'clang --version' and 'xcrun --find clang' fail with the same license error, so there is no working C compiler for building packages from source. /Library/Developer/CommandLineTools is installed, so pointing xcode-select at it is a possible user-side fix. (local commands 2026-10-05)
- [confirmed] Demucs 4.1.0 (2026-07-11) is MIT, dropped torchaudio, hosts models on Hugging Face, and its maintainer is slow to reply. — PyPI shows 4.1.0 (2026-07-11), MIT. requires_dist has sphn, lameenc, huggingface-hub and safetensors; torchaudio appears only in the train extra. The README says '11/07/2026: Released Demucs v4.1.0 … models hosted on Hugging Face' and 'I'm not actively working on Demucs anymore'. Weights live at adefossez/HTDemucs (84 MB) and HTDemucs-ft (4×84 MB). Those HF repos have no license tag; the MIT license comes from the repo README. (https://pypi.org/pypi/demucs/json ; https://raw.githubusercontent.com/adefossez/demucs/main/README.md ; HF API)
- [confirmed] Demucs '-d mps' is undocumented, so plan to fall back to CPU (about 1.5x track length). — The raw README never mentions MPS. A WebFetch summary claimed it did; grep of the raw file shows it does not. Measured on this M2 with demucs 4.1.0: a 93.6 s file took 60.9 s on CPU and 12.9 s on MPS; a 30 s excerpt took 11.8 s on CPU and 4.8 s on MPS. With --shifts 0, CPU and MPS stems match at 63-102 dB SNR, so they are numerically equivalent. With the default --shifts 1, each run applies a random time shift and the stems differ (1-33 dB SNR), so output is non-deterministic. (local benchmark 2026-10-05 in scratchpad (HF_HOME redirected, deleted afterwards))
- [uncertain] Stem check: the residual of (sum of stems − mix) must be at least 30 dB down. — On a clean synthetic mix, htdemucs at default shifts gave a residual of −29.2 dB, which would fail this gate. The threshold has not been validated. (local measurement)
- [refuted] audio-separator 0.47.0 is an MIT wrapper you can add with 'uv tool install --python 3.12 audio-separator[cpu]'. — 0.47.0 (2026-08-27) has a mandatory dependency 'diffq>=0.2; sys_platform != "win32"'. diffq 0.2.4 is CC-BY-NC-4.0 and ships macOS arm64 wheels only for cp38-cp310. A wheel-only resolve for py3.12 falls back to audio-separator 0.14.5. A source build needs a C compiler, which is blocked. It also pins samplerate==0.1.0 (2017) and needs torch>=2.13 on arm64. (https://pypi.org/pypi/audio-separator/json ; https://pypi.org/pypi/diffq/json ; uv pip compile --only-binary test)
- [confirmed] Kim Mel-Band RoFormer weights are MIT, 913 MB. — HF API: license mit; MelBandRoformer.ckpt is 913.1 MB. (https://huggingface.co/api/models/KimberleyJSN/melbandroformer)
- [confirmed] DeepFilterNet3 Rust binary 0.5.6 exists for aarch64-apple-darwin; -D compensates delay; MIT/Apache; model is 8 MB; the Python package pins numpy<2. — The release asset deep-filter-0.5.6-aarch64-apple-darwin is 26.6 MiB. In enhance_wav.rs@v0.5.6: -m/--model; -D/--compensate-delay (off by default); -a/--atten-lim-db (default 100, 'mixing the enhanced signal with the noisy signal'); --pf; -o (default 'out'). DeepFilterNet3_onnx.tar.gz is 7,983,136 bytes. publish.yml builds deep-filter with FEATURES …default-model, so the model is embedded. deepfilternet 0.5.6 requires numpy<2.0. (https://github.com/Rikorose/DeepFilterNet/releases/expanded_assets/v0.5.6 ; raw enhance_wav.rs and publish.yml at v0.5.6)
- [confirmed] MossFormer2_SE_48K MLX is Apache-2.0 (int8 is 90 MB). DeepFilterNet-mlx is MIT, 26 MB. — HF API: apache-2.0, model_int8.safetensors is 90.1 MB. DeepFilterNet-mlx: mit, about 26 MB, created 2026-03-10. Both show 0 downloads, so adoption is low. (HF API)
- [confirmed] pedalboard 0.9.25 (2026-09-09) is GPLv3 with wheels for cp310-cp315. — PyPI arm64 wheels exist for cp310, cp311, cp312, cp313, cp314, cp314t, cp315 and cp315t. (https://pypi.org/pypi/pedalboard/json)
- [confirmed] Rubber Band 4.0.0 has a prebuilt macOS GPL CLI (1.5 MB). Its architecture was not inspected; it may need an ad-hoc codesign. — The download exists and is still the latest: 'v4.0 released 25 Oct 2024'. I downloaded it to the scratchpad (1,500,014 bytes) and deleted it afterwards. 'rubberband' and 'rubberband-r3' are Mach-O universal binaries (x86_64+arm64), signed 'Developer ID Application: Particular Programs Ltd (73F996B92S)' with hardened runtime, so ad-hoc signing is unnecessary. R3 is selected with -3 or by calling rubberband-r3. The bundled ffmpeg has no rubberband filter. (https://breakfastquay.com/rubberband/ ; local file/lipo/codesign)
- [confirmed] loudnorm dynamic mode upsamples to 192 kHz; two-pass linear keeps the sample rate. — Tested with the bundled ffmpeg 6.0. A single pass gave a 192000 Hz output stream with normalization_type 'dynamic'. Pass 2 with the measured_* values and linear=true gave 48000 Hz. Linear mode silently falls back to dynamic when constraints fail, including when measured_LRA is 0. The bundled build also has ebur128, sidechaincompress, acrossfade, axcorrelate, afftdn, anlmdn, arnndn, adeclick, adeclip, dialoguenhance and amix normalize. It lacks rubberband and libsoxr, and is built with --enable-gpl --enable-nonfree. (local ffmpeg tests)
- [confirmed] pyloudnorm 0.2.0 (2026-01-04) is MIT; matchering 2.0.6 is GPLv3 and unchanged since 2022; python-stretch is MIT with wheels up to cp312. — PyPI dates and licenses match. python-stretch 0.3.1 (2025-02-14) ships a cp312-abi3 wheel, which also covers Python 3.13 and 3.14. (PyPI JSON)
- [confirmed] Magenta RealTime 2: Apache-2.0 code, CC-BY-4.0 weights, Google claims no rights in outputs, small model runs real-time on any Apple Silicon, about 1.38 GB of resources plus 0.46 GB for the small model. — The HF card shows the license terms and 'Google claims no rights in outputs you generate'. It says 'trained on ~71k hours of stock music from multiple sources, mostly instrumental'; it says 'stock', not explicitly 'licensed'. docs/models.md: 'mrt2_small (230M) — runs real-time on any Apple Silicon Mac, including Air models'. The HF repo has resources/ = 1.38 GB and mrt2_small.mlxfn = 455.7 MB. magenta-rt 2.0.3 (2026-07-30) has an 'mlx' extra; its mandatory deps include recurrentgemma[jax], google-cloud-storage and ai-edge-litert. (https://huggingface.co/google/magenta-realtime-2 ; docs/installation.md ; docs/models.md ; PyPI)
- [refuted] Open question: Magenta RT always stores models in ~/Documents and model download is interactive. — magenta_rt/paths.py reads os.environ.get('MAGENTA_HOME', ~/Documents/Magenta). The CLI is 'mrt models download [NAME]', with NAME optional, so 'mrt models download mrt2_small' runs non-interactively. Sources are the GCS bucket magenta-rt-public or HF google/magenta-realtime-2. 'mrt mlx generate' accepts --prompt --model --duration --bits --temperature --top-k --cfg-musiccoca --cfg-notes; there is no output-path flag. ~/Documents currently shows no iCloud sync markers. (magenta_rt-2.0.3 wheel source (read in memory))
- [confirmed] ACE-Step 1.5: MIT, vendor claims of licensed/royalty-free/synthetic training data, bpm/keyscale/timesignature control, Python 3.11-3.12, MLX on macOS, XL released 2026-04-02. — The HF card says license mit, 'Licensed Data … Royalty-Free / No-Copyright … Synthetic Data', and 'You can strictly use the generated music for commercial purposes'. pyproject.toml has requires-python >=3.11,<3.13; macOS deps are torch>=2.9.1, mlx and mlx-lm; gradio==6.2.0, modelscope and torchcodec (on arm64) are core deps. In GenerationParams, bpm is an int between 30 and 300. The acestep-v15-xl-* repos were created 2026-04-02. (https://huggingface.co/ACE-Step/Ace-Step1.5 ; raw pyproject.toml, INSTALL.md, acestep/inference.py ; HF API author=ACE-Step)
- [refuted] ACE-Step disk is about 7000 MB. — Weights alone for the recommended route are 7.69 GB: turbo 4.79 + LM-0.6B 1.37 + Qwen3-Embedding 1.19 + VAE 0.34. The uv env adds torch, torchvision, torchaudio, torchcodec, gradio, transformers, mlx-lm and modelscope, estimated at 1.5-2.5 GB, for about 9-10 GB total. The mlx-community ACE-Step1.5-MLX-4bit repo is 5.29 GB but has no license tag, a 2.38 GB fp32 embedding, no LM, and 124 downloads. (HF API blobs=true)
- [uncertain] A 2026-07 report says the ACE-Step CLI calls cloud endpoints until api_url/api_mode are set. — The current main cli.py contains no api_url, api_mode or endpoint URLs. It loads .env, or .env.example as a fallback (defaults: LM 1.7B, LM backend vllm, download source auto), and it clears proxy variables. The report may concern another client. (https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/main/cli.py ; .env.example)
- [confirmed] MOSS-SoundEffect v2 MLX 4-bit: Apache-2.0, 6.4 GB, 12.2 GB peak RAM, not on PyPI. — HF API: apache-2.0, 6.40 GB, created 2026-06-12, 0 downloads. The card says '30 s latent: 45 s wall clock, 12.2 GB peak memory' on M5 Max. The card says 'pip install moss-sfx-mlx', but PyPI returns 404, so install from GitHub. (HF API and card; https://pypi.org/pypi/moss-sfx-mlx/json (404))
- [confirmed] VoxCPM2 is Apache-2.0, covers Turkish, and has the vendor-reported WER figures; MLX 8-bit is 3.2 GB and 4-bit is 2.3 GB. — HF card: apache-2.0, 30 languages including tr, created 2026-04-03, modified 2026-08-18. Minimax-MLS Turkish WER from the GitHub README: Minimax 1.52, ElevenLabs 0.699, FishAudio S2 0.870, VoxCPM2 0.817. Turkish speaker similarity 87.1, the best in the table. Internal Turkish WER 1.65%. MLX sizes are 3.23 and 2.30 GB. Speed: the README reports RTF ~1.76 on an Apple M4 Pro (llama.cpp Q8), so a base M2 is likely slower than real time. That is an estimate. (https://huggingface.co/openbmb/VoxCPM2 ; https://raw.githubusercontent.com/OpenBMB/VoxCPM/main/README.md)
- [refuted] Install with 'uv tool install --python 3.12 --prerelease=allow mlx-audio[tts,stt,sts]'. — In mlx-audio 0.5.7 (2026-09-28) the sts extra requires webrtcvad>=2.0.10, which is sdist-only (a 2017 C extension) and needs a compiler. A wheel-only resolve of [tts,stt,sts] fails; [tts,stt] resolves. transformers>=5.14 is met by the stable 5.18.0 (2026-09-30), so --prerelease=allow is unnecessary. The CLI flags --instruct, --ref_audio, --ref_text, --lang_code and --output_path do exist. (https://pypi.org/pypi/mlx-audio/json ; https://pypi.org/pypi/webrtcvad/json ; raw mlx_audio/tts/generate.py ; uv pip compile test)
- [confirmed] Chatterbox Multilingual v3 is MIT and includes Turkish (MLX 2.7 GB). The PyTorch package pins torch 2.6 and numpy<2. MOSS-TTS-Nano's license is provisional. Kokoro has no Turkish. — HF: chatterbox-multilingual-v3 is mit, includes tr, 2.71 GB. chatterbox-tts 0.1.7 requires torch==2.6.0 (py<3.14), numpy<2 (py<3.13) and gradio==6.8.0. The MOSS-TTS-Nano card says 'treat the repository as not yet licensed for redistribution' until its LICENSE file is published. The mlx-audio README lists Kokoro as EN/JA/ZH/FR/ES/IT/PT/HI. (HF API/cards; PyPI; https://raw.githubusercontent.com/Blaizzy/mlx-audio/main/README.md)
- [confirmed] kokoro-onnx 0.6.1 needs Python <3.14; HYPERFRAMES_PYTHON overrides the interpreter; the wrapper is permissively licensed. — requires_python is <3.14,>=3.10. python.mjs line 47 reads env.HYPERFRAMES_PYTHON. However, kokoro-onnx depends on phonemizer>=3.4 and espeakng-loader, both GPL-3.0 (the espeak-ng stack). That is fine for rendered audio but matters if it is embedded in distributed software. (https://pypi.org/pypi/kokoro-onnx/json ; ~/.claude/skills/media-use/audio/scripts/lib/python.mjs)
- [refuted] mlx-whisper 0.4.3 works with mlx-community/whisper-large-v3-turbo-8bit (864 MB). — mlx_whisper/load_models.py loads only weights.safetensors or weights.npz. The -8bit repo contains model.safetensors, config.json and multilingual.tiktoken, built with mlx-audio-plus for mlx_audio.stt, so mx.load would fail. Repos that are compatible: mlx-community/whisper-large-v3-turbo (weights.safetensors, 1.61 GB, updated 2026-04-12) and -q4 (weights.npz, 464 MB). (ortamlar/ses/.../mlx_whisper/load_models.py ; HF API)
- [confirmed] 'hyperframes transcribe' needs whisper.cpp from brew or a cmake build. — chunk-OAF4XJOW.js looks for whisper-cli in env, then system, then a built binary. The auto-build runs git clone plus 'cmake -B build' and fails with 'Ensure cmake and a C compiler are installed'. On macOS its install hint is 'brew install whisper-cpp'. (/Users/onurkaya/Projects/video/node_modules/hyperframes/dist/chunk-OAF4XJOW.js)
- [refuted] QA stack: mir_eval 0.8.2 MIT, jiwer 4.0 Apache, audiobox-aesthetics CC-BY-4.0, laion-clap can be installed into the shared 3.12 venv. — The licenses are correct. audiobox-aesthetics needs only about 415 MB; the 831 MB repo holds checkpoint.pt and model.safetensors duplicates. But laion-clap 1.1.7 pins numpy<2 and pulls in wandb, webdataset and wget. With numpy>=2, uv falls back to laion-clap 1.1.5 (2024), and whether that runs on numpy 2.5 is unknown. (PyPI JSON; uv pip compile test)
- [confirmed] uv 0.12.23 (2026-10-03). numpy 2.5, scipy 1.18, librosa 1.0 and jax 0.11 need Python ≥3.12. soxr has no cp313 wheel. The system Python fails SSL verification. — PyPI requires_python is >=3.12 for numpy 2.5.3, scipy 1.18.1, librosa 1.0.0 and jax 0.11.2. soxr 1.1.0 arm64 wheels are cp39-cp312 and cp314. arac/uv reports 0.12.23 (2026-10-03) and is already installed. System python3 3.14.7 with urllib fails with CERTIFICATE_VERIFY_FAILED. (PyPI JSON; local commands)
- [confirmed] Kenney audio packs are CC0 with no account. Sonniss is royalty-free with no attribution, no AI training and no raw redistribution. The GDC 2026 bundle is about 7.5 GB. — Kenney's page shows 'License Creative Commons CC0' and 'Continue without donating'. Sonniss terms, via WebFetch: royalty-free, commercial use, 'No attribution is required', 'Use for AI/ML training is strictly prohibited'. rekkerd.org (2026-03-16): 'giving away 7.47GB+'. (https://kenney.nl/assets/interface-sounds ; https://sonniss.com/gameaudiogdc ; https://rekkerd.org/sonniss-releases-gdc-2026-game-audio-bundle/)
- [refuted] The agent can curl Sonniss ZIPs from downloads.sonniss.com without logging in. — On 2026-10-04 at 21:48 GMT both sonniss.com/gameaudiogdc and downloads.sonniss.com returned HTTP 403 with 'cf-mitigated: challenge' (a Cloudflare bot challenge). A scripted fetch would mean getting past bot protection, which the hard rules forbid. (curl -I response headers)
- [confirmed] media-use bundles 21 SFX under the Pixabay Content License. MusicGen, the offline BGM fallback, is CC-BY-NC. — There are 19 MP3s; the 21 entries include CREDITS.md and manifest.json. facebook/musicgen-small is cc-by-nc-4.0. The fallback is worse than described: bgm.mjs auto-runs 'python -m pip install -q transformers soundfile torch numpy' and generates with musicgen-small whenever no HeyGen or Lyria credential is configured. (~/.claude/skills/media-use/audio/assets/sfx ; audio/scripts/lib/bgm.mjs ; HF API)
- [confirmed] The non-commercial, gated and oversized avoid list is accurate: Stable Audio Open, MMAudio, AudioLDM2, AudioGen, AudioX, TangoFlux, ThinkSound, XTTS, F5, MMS-TTS, OmniVoice, Higgs TTS 3, SAM-Audio, KugelAudio. — Stable Audio Open (1.0 and Small) is gated=auto under the Stability community license. MMAudio, AudioX, AudioGen, F5-TTS and mms-tts-tur are cc-by-nc-4.0; AudioLDM2 is cc-by-nc-sa-4.0. The TangoFlux card says 'non-commercial research use only'. ThinkSound's GitHub README says 'Commercial use is NOT permitted'. XTTS uses the coqui-public-model-license. OmniVoice's card says the 'pre-trained model is licensed under the CC-BY-NC'. Higgs TTS 3 is research/non-commercial at 9.32 GB. SAM-Audio is gated=manual at 14.86 GB. KugelAudio is MIT at 18.69 GB. (HF API and model cards 2026-10-05)
- [confirmed] Piper's official repo has only the dfki Turkish voice. macOS 'say' voices are licensed for personal, non-commercial use only. — rhasspy/piper-voices has only tr/tr_TR/dfki/medium under tr/. The local /Library/Documentation/License.lpdf says System Voices are for 'your personal, non-commercial use'; Personal Voice is the same. (HF API; local macOS license)
- [confirmed] GeneralUser GS is permissive for music, and tinysoundfont 0.3.7 (MIT, cp38-cp312) renders it. — License v2.0: 'use … without restriction for your own music creation, private or commercial', with a caveat for commercial software. But the GeneralUser README says it 'makes heavy use of SoundFont synthesis and modulator features … dependent on having a standards-compliant synth', and TinySoundFont's tsf.h lists as NOT YET IMPLEMENTED 'Support for modulators', chorus/reverb sends and a better low-pass filter. FluidSynth v2.6.1 ships no macOS binary (Windows and iOS only), so it needs brew. (https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/documentation/LICENSE.txt ; tsf.h ; FluidSynth release assets)
- [confirmed] hyperframes-audio renders the same Web Audio graph in preview and render, supports data-fx-chain, data-automation and carve.mjs, beds sit at about −31 LUFS under narration, and data-playback-rate preserves pitch. — SKILL.md lines 25-41 also state 'HyperFrames does not provide automatic waveform sync or drift correction'. media-use tts.md line 21 gives the −31 LUFS figure. (~/.claude/skills/hyperframes-audio/SKILL.md ; media-use/audio/references/tts.md)
- [uncertain] About 18-19 GB of disk is free and the core stack is about 5.5 GB. — df showed 19 GiB free at the start and 16 GiB about 30 minutes later while parallel agents installed. The workspace is now 4.9 GB: modeller 1.7 GB, .uv 1.5 GB, ortamlar 1.2 GB. ~/.cache/huggingface holds 458 MB outside the workspace. The measured shared env (beat-this, demucs, mlx-whisper, pedalboard, librosa, essentia, torch 2.14.1) is 1.2 GB plus a 1.4 GB uv cache shared through APFS clones. (df/du 2026-10-05)

### Düzeltmeler (seçimlerin önüne geçer)

- **Beat/downbeat tracking**: Install with 'uv tool install --python 3.12 beat-this --with soundfile', or keep it in the shared env, which already has soundfile. Drive it from Python with File2Beats(..., device='mps'), falling back to 'cpu'; the CLI never uses MPS. Feed it WAV files. — gerekçe: torchaudio 2.11 load() needs TorchCodec plus system FFmpeg dylibs, which are absent. soundfile is not a declared dependency of beat-this, so a bare install cannot read audio. MPS was verified to give identical beat times.
- **Stem separation**: Use 'demucs -n htdemucs_ft -d mps --shifts 0 …' by default and keep '-d cpu' as the fallback. Replace the '≥30 dB residual' gate with either ≤−25 dB or a comparison against a CPU run. Remove 'dropped torchaudio' from the risk text, since that is now an advantage. — gerekçe: Measured on this M2: MPS is about 2.5-5x faster than CPU and numerically equivalent at --shifts 0 (63-102 dB SNR). The default --shifts 1 is random and not reproducible. The residual on a clean mix was −29.2 dB.
- **Best-quality vocal isolation (optional)**: Drop audio-separator from the work and commercial stack. If Kim Mel-Band RoFormer (MIT) is wanted, run it through ZFTurbo's Music-Source-Separation-Training inference code (MIT) in its own env, or treat audio-separator as personal-only in a Python 3.10 env, where diffq wheels exist. — gerekçe: audio-separator 0.47.0 hard-requires diffq, which is CC-BY-NC-4.0 and has no cp311/cp312 macOS wheels. Building it needs a C compiler, which the Xcode license currently blocks.
- **Speech denoise**: Run 'deep-filter -D -a 15 -o out v.wav'. The release binary embeds the default model, so -m is optional. Use --atten-lim-db (12-20 dB) instead of an ffmpeg amix dry/wet blend. — gerekçe: The CLI has a built-in attenuation limit that mixes enhanced and noisy audio internally. -D is off by default, and the model is compiled in through the 'default-model' feature.
- **Time-stretch**: Call 'rubberband-r3' (or 'rubberband -3') straight from the extracted universal binary. Remove the ad-hoc 'codesign -s - -f' step. — gerekçe: The binary is universal (arm64 + x86_64) and Developer-ID-signed with hardened runtime. Re-signing it would strip a valid signature.
- **Instrumental music (Magenta RT 2)**: Export MAGENTA_HOME=/Users/onurkaya/Projects/video/modeller/magenta, then run 'mrt models init' and 'mrt models download mrt2_small', which is non-interactive. Budget about 1.84 GB for weights plus jax/flax/recurrentgemma/ai-edge-litert/google-cloud-storage deps. Do not describe the training data as 'licensed'; the card only says 'stock music'. — gerekçe: paths.py honours MAGENTA_HOME and the download command takes a NAME argument. This answers two of the open questions.
- **Full-song generation (ACE-Step 1.5)**: Raise disk_mb to about 9500, or about 8000 with the LM off. Also set ACESTEP_CHECKPOINTS_DIR inside the workspace, ACESTEP_DOWNLOAD_SOURCE=huggingface and CHECK_UPDATE=false, and ACESTEP_LM_BACKEND=mlx. Mark the 'cloud endpoints' claim as unverified. Note that the MLX-4bit repo has no license tag. — gerekçe: Weights alone are 7.69 GB, and the env adds torch, gradio 6.2, modelscope, mlx-lm and torchcodec. Current cli.py has no remote endpoints.
- **Turkish TTS (VoxCPM2 via mlx-audio)**: Use 'uv tool install --python 3.12 mlx-audio[tts,stt]' without the sts extra and without --prerelease=allow. Add sts only after the compiler issue is fixed. Expect generation slower than real time on a base M2 and budget minutes per minute of narration; use the 4-bit model if memory is tight. — gerekçe: The sts extra pulls webrtcvad, which is sdist-only C and needs clang (blocked). transformers 5.18.0 is a stable release. VoxCPM's own README reports RTF ~1.76 on an M4 Pro.
- **Speech-to-text gate (mlx-whisper)**: Use path_or_hf_repo='mlx-community/whisper-large-v3-turbo' (fp16, 1.61 GB), or '-q4' (464 MB) if disk is tight. Alternatively use mlx_audio.stt with the mlx-audio-plus repos. Update disk_mb to about 1650. — gerekçe: mlx_whisper loads only weights.safetensors or weights.npz. The -8bit repo has model.safetensors, so it would fail.
- **Objective QA (CLAP prompt adherence)**: Use transformers' ClapModel/ClapProcessor with laion/clap-htsat-unfused (Apache-2.0) in the shared venv instead of the laion-clap package, or put laion-clap in its own numpy<2 env. — gerekçe: laion-clap 1.1.7 pins numpy<2. With numpy 2.5, uv silently downgrades to 1.1.5, which is untested on numpy 2.
- **SFX library (Sonniss)**: The user downloads the chosen Sonniss parts in a browser into kutuphane/sfx/sonniss/, and the agent only indexes them and writes the license ledger. Keep curl for Kenney. — gerekçe: Both sonniss.com and downloads.sonniss.com answer curl with a Cloudflare challenge (HTTP 403, cf-mitigated: challenge). Scripting past it breaks the 'no bypassing bot protection' rule.
- **Deterministic MIDI + SoundFont music**: State that TinySoundFont does not implement modulators or chorus/reverb sends, so GeneralUser GS will sound flatter than intended. Prefer FluidSynth (LGPL-2.1, 'brew install fluid-synth') once brew works, or audition several SoundFonts. Add reverb and chorus in pedalboard. — gerekçe: tsf.h lists 'NOT YET IMPLEMENTED … Support for modulators', and the GeneralUser README says it depends on a standards-compliant synth.
- **Risks: toolchain**: Add a risk: there is no working C compiler (xcrun/clang refuse to run until the Xcode license is accepted), so any sdist with C code fails (webrtcvad, diffq on py≥3.11, madmom). Fix, by the user with sudo: 'sudo xcodebuild -license accept', or 'sudo xcode-select -s /Library/Developer/CommandLineTools' (CLT is installed). — gerekçe: Verified locally. This blocks more than brew.
- **Risks: dependency drift**: Replace 'torchaudio pins older torch' with 'torchaudio ≥2.9 audio I/O needs TorchCodec plus system FFmpeg shared libraries; use soundfile or ffmpeg-static for I/O'. — gerekçe: torch 2.14.1 and torchaudio 2.11.0 coexist and work; only file loading breaks.
- **English TTS (Kokoro)**: Add to license_code: kokoro-onnx pulls the GPL-3.0 phonemizer and espeak-ng (via espeakng-loader). That is fine for rendered audio but not for embedding in shipped work software. — gerekçe: These are in the PyPI requires_dist.
- **BGM safety in HyperFrames**: Add an 'avoid' rule: do not call media-use BGM resolve or generate without credentials for any deliverable. It auto-runs 'python -m pip install transformers torch …' and generates with CC-BY-NC MusicGen. Route BGM to Magenta RT 2, ACE-Step or MIDI instead. — gerekçe: bgm.mjs auto-installs on demand and falls back to MusicGen.
- **Minor factual fixes**: media-use has 19 bundled SFX MP3s, not 21. The python-stretch wheel is cp312-abi3, so it also covers 3.13 and 3.14. Silero VAD is not bundled with mlx-audio; it downloads mlx-community/silero-vad, whose port has no license tag (upstream is MIT). — gerekçe: Checked against local files, PyPI and the HF API.

### Eksik bulunanlar

- Prerequisite decision for the user: accept the Xcode license, or switch xcode-select to the CommandLineTools that are already installed. That one sudo step unlocks the C compiler (sdist builds such as webrtcvad and diffq) and Homebrew (sox, fluid-synth, whisper-cpp, espeak-ng, and the FFmpeg shared libraries TorchCodec needs).
- Dereverberation and speech restoration for phone dialogue are not covered (DeepFilterNet only denoises). Candidates: nara_wpe 0.0.11 (MIT, numpy-only WPE) and sarulab-speech/sidon-v0.1 (MIT, about 1 GB CPU TorchScript, restores to 48 kHz). Neither has been tested on Mac. Avoid mlx-community/DialogueSidon (CC-BY-NC-4.0) even though mlx-audio lists it.
- Phone-audio repair without new installs: the bundled ffmpeg 6.0 already has adeclick, adeclip, dialoguenhance and speechnorm. Add them to the cleanup chain and pair each with a before/after numeric check.
- Determinism and reproducibility rules: Demucs is random by default (--shifts 1), so use --shifts 0 for gated runs. Record seeds for VoxCPM2, ACE-Step and Magenta. Hash output files in the provenance ledger.
- Disk governance across parallel agents: free space fell from 19 GiB to 16 GiB during this check, and ~/.cache/huggingface (458 MB) sits outside the workspace even though ortam.sh sets HF_HOME. Enforce HF_HOME, TORCH_HOME, MAGENTA_HOME, ACESTEP_CHECKPOINTS_DIR and UV_CACHE_DIR in every command, and run a df gate before each download over 1 GB.
- Song-structure and section detection (intro, verse, chorus, bridge) to drive the craft-focused edit map. librosa 1.0 segmentation is already installed. allin1 is stale and depends on madmom, so avoid it.
- Guardrails against auto-installers and telemetry inside skills: media-use bgm.mjs pip-installs MusicGen on demand, and the ACE-Step and VoxCPM PyTorch packages pull in gradio, so GRADIO_ANALYTICS_ENABLED=False is needed. Consider a PreToolUse hook that blocks 'pip install' outside approved envs.
- A one-time listening calibration with the user, a 30 s click-track or A/B per new pipeline, because thresholds such as F≥0.9, the residual gate and the ducking LU targets have not been validated on the user's real soft acoustic material.
- Turkish forced alignment: avoid MMS-based CTC aligners (MMS weights are CC-BY-NC). Whether Qwen3-ForcedAligner in mlx-audio supports Turkish is unverified. Until then, rely on Whisper word timestamps.
- A fallback for vocal isolation that does not need audio-separator or diffq, such as Mel-RoFormer through MIT inference code, with its install verified on Python 3.12 arm64.
