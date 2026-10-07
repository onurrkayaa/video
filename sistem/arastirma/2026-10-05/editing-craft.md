# Kurgu zanaatı — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Main findings (evidence dated 2026-10-04/05; several points were tested on this Mac):

1. Root cause of the audio slipping. ilk-montaj/kurgu.py placed every cut on a constant grid: first beat 0.511 s plus n × 60/76.005, extended across 352 beats. A soft, live-played song wanders in tempo, so the cuts drift off the beat.
   - The cure is three-part. Track every beat individually with Beat This! (MIT for code and weights). Store the whole edit as one frame-exact EDL computed from absolute times. Keep the music as one continuous WAV that is muxed once, never assembled from AAC segments.
   - Each AAC encode adds encoder delay (1024 samples in ffmpeg, 2112 per Apple TN2258) plus padding. Joining segments therefore accumulates drift.
   - Cuts should land 0-1 frame before the beat. ITU-R BT.1359-1 says sound arriving early is detectable at 45 ms, while late sound is only detectable at 125 ms.
   - Every claim is verified with numbers: windowed cross-correlation of the final audio against the master WAV, and scdet cut times compared with the beat list.

2. Craft order follows Murch's Rule of Six: emotion > story > rhythm > eye-trace. For montages, give rhythm more weight. Work in stages: selects → stringout → rough → fine → picture lock → color → sound.
   - Cut density follows the music's energy per bar. Cut on downbeats and phrase starts, and slip each shot so its action peak lands on a beat.
   - Use transitions only when motivated: one primary type plus 1-2 accents.
   - Soft songs use phrase pacing: 4-8 beats per shot, dissolves, slow motion at the peak.

3. Tools.
   - ffmpeg-static 6.0, already installed, has every filter needed: xfade custom expressions, vidstab, zscale/tonemap, lut3d, nlmeans/hqdn3d/atadenoise, scdet, signalstats, ebur128, sidechaincompress, axcorrelate, photosensitivity, libvmaf. It also has the macOS coreimage filter (GPU CIZoomBlur, CIMotionBlur, CIBloom, CINoiseReduction). Tested locally: animating parameters with sendcmd, eq eval=frame flashes, the xfade custom expression (its P variable runs 1 → 0), and a closed-form setpts speed ramp.
   - Apple frameworks through a small Swift CLI need no install. Swift 6.4 runs via `DEVELOPER_DIR=/Library/Developer/CommandLineTools`, because the Xcode license is not accepted. Probed here:
     - Supported: VTFrameProcessor frame-rate conversion (optical-flow slow motion and speed ramps; needs 64RGBAHalf buffers), VT motion blur and optical flow.
     - Limited: super-resolution works only at 4x.
     - Not supported: VTTemporalNoiseFilter.
     - Also available: Vision aesthetics scores, faces, saliency, foreground masks, and the SoundAnalysis classifier (303 classes, including laughter, giggling, speech and singing).
   - HyperFrames stays the motion-design layer: GSAP, 15 CPU-composited shader transitions, the motion-blur component, rate lanes, Studio preview. Two cautions:
     - For footage-heavy montages an EDL → ffmpeg path is faster and frame-exact. HyperFrames extracts video frames as JPG by default and keeps a persistent cache of about 0.9 GB in $TMPDIR.
     - Its built-in whip-pan clamps samples to the frame edge, which streaks real footage. Use mirrored tiling plus directional blur instead.

4. Verification without watching in real time. Pair contact sheets, 13-frame strips around each transition, and beat strips (waveform with beat and cut ticks) with metrics: Laplacian variance, ΔE2000, leave-one-out PSNR/SSIM for interpolated frames, LUFS/true peak, cross-correlation lag, crop-path jerk, and a flash count per WCAG 2.3.1.

5. Licensing traps for work output (non-commercial terms):
   - madmom models (CC BY-NC-SA).
   - Depth Anything V2 Base/Large/Giant and DA3 Large/Giant (CC-BY-NC-4.0).
   - sniklaus 3d-ken-burns (CC BY-NC-SA, needs CUDA).
   - Remotion requires a paid licence for companies with more than 3 employees.
   - video-use needs a paid ElevenLabs key.

## Seçimler

### Frame-accurate backbone for footage editing, compositing and measurement: cuts, xfade and luma wipes, setpts speed ramps, vid.stab, HDR tone-mapping, LUTs, denoise, grain, audio placement, ducking and loudness, plus every QC metric used in the cards.
- **Seçim:** FFmpeg: the installed ffmpeg-static 6.0 at /Users/onurkaya/Projects/video/arac/ffmpeg. Optional upgrade to Homebrew ffmpeg-full 9.0.2.
- Alternatifler: HyperFrames 0.8.124 (installed; Apache-2.0): best for graphics, product and explainer pieces, Studio preview, and GSAP keyframes; 15 built-in shader transitions composited on rendered frames (whip-pan, cinematic-zoom, light-leak, flash-through-white, cross-warp-morph...). MLT/melt (GPL): XML timelines the user can open in Shotcut or Kdenlive. MoviePy 2 (MIT): Python compositing, slower. gl-transitions (MIT npm, ~0.6 MB): GLSL transitions usable inside HyperFrames' WebGL.
- Neden: The installed build already has the filters the techniques need. Confirmed locally: xfade (46 presets plus custom expr), vidstabdetect/vidstabtransform, zscale+tonemap, lut3d, nlmeans/hqdn3d/atadenoise/bm3d/chromanr, dblur/gblur, tmix, minterpolate, scdet, signalstats, blurdetect, siti, vfrdet, mpdecimate, freezedetect, blackdetect, photosensitivity, ssim/psnr/libvmaf, ebur128, loudnorm, sidechaincompress, acrossfade, axcorrelate. It also has the macOS coreimage filter (GPU CIFilters: CIZoomBlur, CIMotionBlur, CIBloom, CIBokehBlur, CINoiseReduction, CIToneCurve, CIColorCube, CIVignetteEffect) and the encoders aac_at, h264/hevc/prores_videotoolbox, libx264 (tunes: film, grain...), libx265, libsvtav1. Behaviours tested on this Mac: sendcmd animates dblur and exposure; eq brightness with eval=frame makes a Gaussian flash; in xfade custom expressions P runs from 1 to 0, and a soft luma-wipe expression rendered correctly; a closed-form log speed ramp in setpts produced the predicted 115 frames. Edit points are integer frames, so the EDL math stays exact.
- Lisans: kod FFmpeg is LGPL/GPL. This static build is configured --enable-gpl --enable-version3 --enable-nonfree, so it is fine to run locally but not to redistribute. Homebrew ffmpeg and ffmpeg-full are GPL-3.0-or-later. · ağırlık n/a · ticari: yes
- Apple Silicon: Native arm64. VideoToolbox H.264/HEVC/ProRes encode, AudioToolbox AAC (aac_at), and the coreimage filter runs CIFilters on the GPU. Most other filters are CPU (NEON); nlmeans and bm3d are slow.
- Kurulum: Nothing to install; it is already present. Optional upgrade: Homebrew is currently blocked on this Mac ('You have not agreed to the Xcode license'). The user would have to run `sudo xcodebuild -license accept` or `sudo xcode-select -s /Library/Developer/CommandLineTools`, then `brew install ffmpeg-full`. That adds rubberband (pitch-preserving stretch), libplacebo (Dolby Vision/HDR tone-mapping, debanding), whisper.cpp, libass, frei0r. Note the plain `ffmpeg` formula 9.0.2 is slimmed and has no vidstab or zimg. A no-brew alternative is the signed and notarized static arm64 build 9.0.2 (2026-09-20) from ffmpeg.martin-riedl.de; whether it includes vid.stab is not confirmed.
- Disk: ~0 MB · bakım: Upstream FFmpeg 8.0 (2025-08-22) and 8.1 (2026-03-16); Homebrew stable is 9.0.2 (Oct 2026). The local static build is 6.0 (2023) but includes every filter used here. Missing locally: rubberband, libplacebo, the xfade transitions added in 7.0+, the -/filter_complex syntax.
- Ajan kullanımı: Write long graphs to a file and pass them with -filter_complex_script (6.x; 7.1+ uses -/filter_complex). Always pass -nostdin. Animate parameters per frame with sendcmd files ('t filter option value;') for filters marked C (dblur, gblur, exposure, eq, crop, rotate, colorbalance, curves), or with eval=frame expressions in t (eq, scale). Build xfade offsets from absolute frame numbers. Mux the master WAV once at the end. Use the QC filters (scdet, signalstats, blackdetect, freezedetect, mpdecimate, vfrdet, siti, ebur128, libvmaf, photosensitivity) to produce JSON or text the agent parses. Use HyperFrames (installed) for motion-design layers and render them as separate clips or alpha overlays that ffmpeg composites.
- Güven: high · kaynaklar: https://ffmpeg.org/ffmpeg-filters.html, https://ffmpeg.org/index.html#news, https://formulae.brew.sh/api/formula/ffmpeg.json, https://formulae.brew.sh/api/formula/ffmpeg-full.json, https://ffmpeg.martin-riedl.de/, https://developer.apple.com/library/archive/technotes/tn2258/_index.html, https://ffmpeg.org/pipermail/ffmpeg-trac/2023-May/066110.html, https://trac.ffmpeg.org/wiki/denoise, https://dev.to/masonwritescode/ffmpeg-hdr-to-sdr-tone-mapping-that-doesnt-look-washed-out-2026-24ie, https://instagit.com/browser-use/video-use/how-does-video-use-handle-hdr-hlg-pq-source-footage-from-devices-like-iphones/, https://github.com/browser-use/video-use, https://www.bannerbear.com/blog/how-to-do-a-ken-burns-style-effect-with-ffmpeg, https://www.premiumbeat.com/blog/create-whip-pan-using-built-effects-premiere-pro/, https://4kshooters.net/2015/08/21/liven-up-your-editing-by-creating-a-whip-pan-in-adobe-after-effects-or-premiere-pro, https://cloud.wikis.utexas.edu/wiki/spaces/rtf318/pages/80022510/Murch+s+Rule+of+Six, https://nofilmschool.com/editing-emotion-using-walter-murchs-rule-six-non-narrative-content, https://workflow.frame.io/guide/editing-stages, https://larryjordan.com/articles/fcpx-montage-to-music/, https://www.soundstripe.com/blogs/a-video-editors-guide-to-j-cuts-and-l-cuts, https://www.studiobinder.com/blog/what-is-a-match-on-action-cut/, https://borisfx.com/blog/how-to-do-slow-motion-in-davinci-resolve/, https://amateurphotographer.com/video/how-to/what-is-speed-ramping-and-how-do-i-do-it, https://noamkroll.com/the-best-order-of-operations-for-color-grading-why-it-makes-all-the-difference/, https://docs.kdenlive.org/en/tips_and_tricks/scopes/vectorscope_i_and_q_lines.html, https://pixop.com/blog/three-easy-ways-to-add-film-grain, https://krotos.studio/blog/film-sound-design, https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026, https://www.owc.com/blog/how-to-make-music-tracks-longer-or-shorter-with-adobe-remix, https://wistia.com/blog/understanding-audience-retention, https://flowingdata.com/2014/09/22/evolution-of-movies/, https://wacom.com/en-ca/discover/film-animation/common-video-editing-mistakes, https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation, https://api.flutter.dev/flutter/material/Easing/emphasizedDecelerate-constant.html, https://api.flutter.dev/flutter/material/Easing/standard-constant.html, https://api.flutter.dev/flutter/material/Easing/emphasizedAccelerate-constant.html, https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html, https://gsap.com/licensing/, https://registry.npmjs.org/gl-transitions/latest

### On-device ML video operations without downloads: optical-flow slow motion and arbitrary eased speed ramps, synthetic motion blur, face/human/saliency analysis for reframing and selects, aesthetics and face-quality scoring, foreground masks for parallax and match cuts, laugh/speech detection for J-cuts and ducking, and a CoreML depth model.
- **Seçim:** Apple system frameworks driven by a small Swift CLI the agent writes once (e.g. arac/apple-fx). Frameworks: VideoToolbox VTFrameProcessor, Vision, SoundAnalysis, CoreImage, CoreML, AVFoundation.
- Alternatifler: rife-ncnn-vulkan (MIT; 437 MB macOS zip; last release 2022-10-29; MoltenVK). Practical-RIFE (MIT; PyTorch MPS). ffmpeg minterpolate (fallback, warps). pyobjc-framework-Vision 12.2.2 (MIT, cp314 universal2 wheels) for calling Vision from Python. MediaPipe face detection (Apache-2.0). Depth Anything 3 Base (Apache-2.0) via PyTorch.
- Neden: Zero download, no licence risk, and accelerated on Apple Silicon. Probed on this M2 / macOS 27 on 2026-10-05:
- Supported: VTFrameRateConversion (1080x1920 config OK, pixel format 64RGBAHalf 'RGhA'), VTMotionBlur, VTOpticalFlow, VTLowLatencyFrameInterpolation.
- Super-resolution: supported at 4x only.
- Not supported: VTTemporalNoiseFilter.
- Vision CalculateImageAestheticsScoresRequest: revision1 available.
- SoundAnalysis built-in classifier: 303 classes, including laughter, giggling, speech, singing, cheering, applause and crying_sobbing.
Frame-rate conversion accepts arbitrary interpolationPhase values, so one 'retime' subcommand covers optical-flow slow motion and any eased speed ramp; RIFE would need a 437 MB download, last updated 2022. Vision provides attention saliency (64-68 px heat map), face rectangles, face capture quality, human rectangles, object tracking and VNGenerateForegroundInstanceMaskRequest (macOS 14+). That is enough for AutoFlip-style reframing and for scoring selects.
- Lisans: kod Apple SDK system frameworks; the Swift tool's code belongs to the user. · ağırlık System models are Apple's and on-device; outputs belong to the user. Optional Depth Anything V2 Small CoreML is Apache-2.0. Do not use Base/Large/Giant, which are CC-BY-NC-4.0. · ticari: yes
- Apple Silicon: Native. VTFrameProcessor is Apple-Silicon-only (macOS 15.4+ for frame-rate conversion and motion blur; 26+ for the temporal noise filter, which this M2 reports as unsupported). Vision, SoundAnalysis and CoreML use the ANE/GPU.
- Kurulum: No install. Swift 6.4 ships with Command Line Tools; because the Xcode license is not accepted, set DEVELOPER_DIR. Example: `DEVELOPER_DIR=/Library/Developer/CommandLineTools swiftc -O -module-cache-path /tmp/mc -o arac/apple-fx apple-fx.swift`. Verified that `swift file.swift` runs this way. Optional depth model: huggingface.co/apple/coreml-depth-anything-v2-small, float16 49.8 MB, 518x396 input, about 25-33 ms per image on M-series Max chips. Compile it at runtime with MLModel.compileModel(at:); public download, no account.
- Disk: ~60 MB · bakım: WWDC25 session 300 introduced VTFrameProcessor for macOS 15.4+ (TNF macOS 26+). Vision aesthetics macOS 15+. Foreground instance mask macOS 14+. SoundAnalysis version1 macOS 12+. Ships with the OS (current macOS 27).
- Ajan kullanımı: Suggested subcommands, each emitting JSON or frames:
- analyze: at 2-10 fps, faces with capture quality, humans, saliency centroid, aesthetics overallScore/isUtility, and SoundAnalysis labels with timestamps.
- retime: input is a list of fractional source-frame positions per output frame. Integer positions are copied; fractional ones use VTFrameRateConversionParameters with interpolationPhase = frac, submissionMode .sequential, qualityPrioritization .quality.
- slomo: an N-times shortcut over retime.
- mblur: VTMotionBlurParameters, strength 1-100, calibrated against a test clip.
- mask: foreground instance mask PNG.
- depth: 16-bit PNG.
- xfx: animated CIMotionBlur or CIZoomBlur transitions, per-frame parameters.
I/O: read with AVAssetReader; convert 420v to 64RGBAHalf with VTPixelTransferSession or CIContext; write with AVAssetWriter (HEVC 10-bit or ProRes 422 for short intermediates). Benchmark a 5 s clip first. Quality and throughput have not been measured end to end.
- Güven: medium · kaynaklar: https://developer.apple.com/videos/play/wwdc2025/300, https://developer.apple.com/documentation/videotoolbox/frame-processing.md, https://developer.apple.com/documentation/videotoolbox/vtframerateconversionconfiguration.md, https://developer.apple.com/documentation/videotoolbox/vttemporalnoisefilterconfiguration.md, https://developer.apple.com/documentation/vision/cropping-images-using-saliency.md, https://developer.apple.com/documentation/vision/calculateimageaestheticsscoresrequest.md, https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest.md, https://developer.apple.com/documentation/soundanalysis/snclassifieridentifier/version1.md, https://huggingface.co/apple/coreml-depth-anything-v2-small, https://github.com/DepthAnything/Depth-Anything-V2, https://huggingface.co/depth-anything/DA3-BASE/blob/main/README.md, https://research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/, https://pypi.org/pypi/pyobjc-framework-Vision/json, https://api.github.com/repos/nihui/rife-ncnn-vulkan/releases/latest, https://github.com/apple/ml-depth-pro, https://github.com/sniklaus/3d-ken-burns

### A reliable per-beat and downbeat grid to cut on, replacing the constant-BPM grid that drifted, and phrase/bar structure for pacing.
- **Seçim:** Beat This! (CPJKU), PyPI package beat-this 1.1.0
- Alternatifler: librosa beat_track (ISC): dynamic programming assuming near-constant tempo; fine for steady pop/EDM, imposes a metronome on calm music. madmom (BSD code, but pretrained models are CC BY-NC-SA: non-commercial). essentia (AGPL; NC models). allin1 structure analyzer (last release 2023-10; heavy demucs/natten/madmom deps). hyperframes beats (bpm-detective: one global BPM).
- Neden: Published at ISMIR 2024. It beats the prior state of the art in F1 without DBN post-processing and outputs individual beat and downbeat timestamps, so tempo drift in live or acoustic recordings is followed rather than averaged away. Training data includes solo-instrument recordings, time-signature changes and classical music with high tempo variation, which is closer to soft acoustic songs than EDM-tuned trackers. The authors note it can still fail on hard, under-represented genres, hence the gates in the beat-grid card. Code and weights are both MIT. Checkpoints: small0 about 8 MB, final0 about 78 MB, downloaded on first use from cloud.cp.jku.at with no account. CPU is enough for a 5-minute song on an M2.
- Lisans: kod MIT · ağırlık MIT (README: 'The code and the published model weights are released under the MIT license') · ticari: yes
- Apple Silicon: CPU is the default. torch 2.14.1 (2026-09-30) has macOS arm64 wheels for cp310-cp314 (about 127 MB). device='mps' should work through torch but is untested here.
- Kurulum: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -m venv ~/.venvs/beat && ~/.venvs/beat/bin/pip install beat-this`. This pulls numpy, torch, torchaudio (latest 2.11.0, a 0.7 MB wheel that may pull torch back to 2.11.x), einops, rotary-embedding-torch and soxr. Feed it WAV files extracted with the local ffmpeg. uv is not installed; system python3 3.14 also has torch wheels, but 3.13 is safer.
- Disk: ~700 MB · bakım: PyPI 1.0 on 2026-04-13 and 1.1.0 on 2026-04-14. Paper: ISMIR 2024 (arXiv 2407.21658).
- Ajan kullanımı: CLI: `~/.venvs/beat/bin/beat_this master.wav -o master.beats --gpu=-1` writes a Sonic-Visualiser-compatible TSV through save_beat_tsv; check the first lines for the column meaning. Python: `from beat_this.inference import File2Beats; beats, downbeats = File2Beats(checkpoint_path='final0', device='cpu', dbn=False)('master.wav')` returns seconds. Always run it on the exact WAV that gets muxed. Run small0 as an agreement check. Save beats.json next to the EDL and convert to frames once with floor(t*fps).
- Güven: high · kaynaklar: https://github.com/CPJKU/beat_this, https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md, https://raw.githubusercontent.com/CPJKU/beat_this/main/beat_this/inference.py, https://pypi.org/pypi/beat-this/json, https://arxiv.org/abs/2407.21658, https://pypi.org/pypi/torch/2.14.1/json, https://pypi.org/pypi/torchaudio/2.11.0/json, https://en.wikipedia.org/wiki/Audio-to-video_synchronization, https://www.forasoft.com/learn/audio-for-video/articles-audio/lip-sync-itu-r-bt-1359-tolerance-windows, https://birchtree.me/blog/your-eyes-ears-and-brain-dont-agree/

## Kaçınılacaklar

- **Constant-BPM beat grids (first_beat + n·60/BPM), as in ilk-montaj/kurgu.py** — Live and acoustic songs drift in tempo, so a fixed grid stretched over hundreds of beats moves cuts off the beat. This was the root cause of the user's 'audio slipping' complaint. Use tracked per-beat timestamps and gate them.
- **hyperframes beats (bundled bpm-detective analyzer)** — It finds one global BPM by peak counting and does not track tempo. Unsuitable as a cut grid except for steady electronic music.
- **librosa beat_track or the music-to-video analyze-beatgrid.py grid as the only grid on soft or acoustic songs** — Its dynamic programming assumes near-constant tempo, so on calm music it imposes a metronome; the skill says so itself. Keep its energy and onset fields; take beats from Beat This!.
- **madmom pretrained models; essentia models** — madmom models are CC BY-NC-SA (non-commercial). Essentia code is AGPL and many of its models are non-commercial. A trap for work output.
- **Concat demuxer on separately encoded AAC segments, or rendering audio in chunks** — Encoder delay and padding (1024-2112 priming samples plus up to 1023 padding per encode, Apple TN2258) accumulate into audible drift. Mux one continuous master and use the concat filter on PCM if needed.
- **ffmpeg minterpolate as the main slow-motion engine** — Block-based motion compensation warps hands, hair and occlusions and is slow on CPU. VTFrameProcessor frame-rate conversion (verified supported here) or RIFE are better; keep minterpolate as a fallback for ≤1.5× on simple motion.
- **zoompan for slow Ken Burns without a pre-upscale** — Positions are rounded to whole pixels, which makes visible jitter. Use GSAP/CoreImage sub-pixel transforms, or scale=8000:-1 before zoompan.
- **HyperFrames built-in 'whip-pan' shader on real footage without inspection** — Its source (chunk-3GXQPCJC.js) clamps samples to the frame edge with offsets up to 1.5 frame widths, producing edge-pixel streaks, and only blurs over about 8%. Build whips with mirrored tiling plus directional blur.
- **Depth Anything V2 Base/Large/Giant; Depth Anything 3 any-view Large/Giant** — CC-BY-NC-4.0, so non-commercial. Use V2 Small (Apache-2.0; CoreML 50 MB) or DA3-Base / DA3-Metric-Large (Apache-2.0).
- **sniklaus/3d-ken-burns** — CC BY-NC-SA 4.0 and requires CUDA/CuPy, which won't run on this Mac.
- **browser-use/video-use as a dependency** — Needs an ElevenLabs API key, i.e. a paid account, which violates the no-accounts rule. Borrow its ideas only: 30 ms fades at every cut, HDR auto-tonemap, self-evaluation at cut boundaries.
- **Downloaded LUT, light-leak, film-burn and overlay packs with unclear licences** — Licence risk for work use. Generate looks and overlays procedurally (buildCube params, GLSL or numpy fbm) or use the bundled Pixabay SFX.
- **Sonniss GDC game-audio bundles** — The licence is fine (royalty-free, commercial use, no attribution), but the bundles are tens of GB, beyond the disk budget. Synthesize SFX procedurally or use the bundled Pixabay set.
- **rife-ncnn-vulkan as the default interpolator** — A 437 MB download, last released 2022-10-29, running through MoltenVK. Native VTFrameProcessor covers the same need with zero download; keep RIFE as a fallback.
- **Remotion for work at companies with more than 3 employees** — Its licence requires a paid company licence beyond individuals and companies of up to 3 employees, which conflicts with the no-paid-services rule. HyperFrames (Apache-2.0) is already installed.
- **allin1 music-structure analyzer** — Last release October 2023, with heavy and brittle dependencies (demucs, natten, madmom) and the madmom licence caveats. Derive sections from novelty plus Beat This! downbeats instead.
- **Scraping trac.ffmpeg.org wiki pages or other bot-protected pages (Anubis, 403s)** — Bypassing bot protection is forbidden by the user's rules. Use local `ffmpeg -h filter=X`, the ffmpeg.org documentation, and test commands on synthetic lavfi inputs.
- **Text overlays by default in personal montages** — Explicit user feedback: they wanted editing craft, not added text.

## Teknikler

### Sync-safe timeline architecture (prevents 'audio slipping')
When: every project. Causes of drift seen in practice:
(1) A constant-BPM grid extrapolated over hundreds of beats on a live-played song. kurgu.py used 76.005 BPM from 0.511 s for 352 beats, so every bit of tempo wander accumulates.
(2) Audio encoded per segment and joined with the concat demuxer. Each AAC encode adds encoder delay (1024 samples in ffmpeg's encoder, 2112 per Apple TN2258) plus up to 1023 padding samples, so N segments drift by roughly N × 20-70 ms.
(3) VFR phone clips treated as CFR.
(4) Speed-changed video with unchanged diegetic audio.
Implementation:
- One EDL JSON is the single source of truth. Every time is an integer output frame computed from absolute times (beat seconds, source in-points), never by summing rounded durations. HyperFrames data-start = frame/fps.
- Conform sources first. Detect VFR with `-vf vfrdet`, real content fps by counting unique frames (mpdecimate), rotation (displaymatrix), and HDR (color_transfer arib-std-b67 = iPhone HLG). Make CFR mezzanines with `-vf fps=30` and put audio in PCM WAV (48 kHz, or keep the song's native rate) with `-c:a pcm_s24le`.
- Build the picture video-only. Place the music once as one continuous WAV: in HyperFrames a single `<audio data-timeline-role=music>` at 0; in ffmpeg, mapped in the final mux.
- Place diegetic, SFX and room-tone stems at absolute offsets (`adelay=<ms>:all=1`, mixed with `amix=normalize=0`).
- Encode AAC once at the very end: `-c:a aac_at -b:a 256k -movflags +faststart`. If audio must be concatenated, use the concat filter on decoded PCM.
- Slowed diegetic audio is either muted or stretched by the same factor with atempo (0.5-2 per instance; chain instances for more).

**Doğrulama:** 1) Windowed cross-correlation of the final audio against the master WAV. Decode both to mono 16 kHz float32 through ffmpeg pipes; use 3 s windows every 10 s with a ±250 ms search. The lag must stay constant at 0 ± 1 ms over the whole file; any slope means drift.
2) ffprobe: audio start_time ≤ 1 ms; audio and video durations differ by ≤ 1 frame; r_frame_rate == avg_frame_rate == 30/1.
3) For each diegetic clip, cross-correlate its output span against the source span: |lag| ≤ 1 frame.
4) `ffmpeg -i out.mp4 -an -vf vfrdet -f null -` must report VFR:0.

### Trustworthy beat/downbeat grid with reliability gates
Run Beat This! final0 on the master WAV to get beats[] and downbeats[] (per-beat, so tempo drift is followed). Bars come from downbeats; phrases are 4/8 bars starting at downbeats where spectral/chroma novelty is high.
Gates before any hard cut uses the grid:
(a) Agreement with an independent tracker (Beat This! small0, or librosa beat_track) has F-measure ≥ 0.85 at ±70 ms tolerance.
(b) Inter-beat-interval coefficient of variation within a section ≤ ~6%. Higher means rubato: don't hard-cut every beat.
(c) ≥ 70% of beats sit within ±50 ms of an onset-strength peak.
(d) Never replace the list with first_beat + n·60/BPM.
If the gates fail, pace by phrase: cut only on downbeats confirmed by strong onsets, use 0.5-1-beat dissolves and long holds. Or ask the user to tap along on a tiny offline HTML page (spacebar timestamps, two passes) and snap each tap to the nearest onset peak within ±60 ms.
Do not use `hyperframes beats` (bpm-detective, one global BPM) or the music-to-video librosa grid on acoustic or calm songs. That skill itself says its grid is a metronome on calm music. Its energy, onset and silence fields remain usable.

**Doğrulama:** Print the gate metrics. Render a 'beat strip' PNG for 20 s windows at the start, middle and end (waveform via showwavespic or numpy, onset envelope, beat and downbeat ticks) and inspect it with Read. Downbeat spacing should be consistent (4 beats in 4/4, 3 in 3/4). Report the residual between tracked beats and a constant-BPM fit: it shows the drift a fixed grid would have caused.

### Cutting on the beat: frame quantization, early bias, slip-to-action
Cut frame = floor(beat_time × fps), so the picture changes 0-33 ms before the beat. On very percussive hits, optionally go one more frame early (editors' rule: 'one or two frames before the beat'). Never cut late: under ITU-R BT.1359-1, sound leading picture is detectable at +45 ms, while picture leading sound is only detectable at -125 ms. A late cut reads as 'out of sync' sooner.
Which beats:
- Downbeats and phrase starts for scene changes.
- One cut per bar at medium energy.
- Every 2 beats only in peaks.
- Hero shots held 2-4 bars.
Slip, don't shift: keep the cut on the beat and move the source in-point so the shot's action peak also lands on a beat (±1 frame). Action peaks are a laugh, hug contact, jump landing or head turn; find them as motion-energy peaks from frame differences or siti TI, or as transients in the clip's own audio. If a natural action cut and the beat disagree by more than 2 frames, slip the shot rather than move the cut.

**Doğrulama:** After rendering: `ffmpeg -i out.mp4 -an -vf 'scdet=t=10:s=1,metadata=print:file=cuts.txt' -f null -` (keys lavfi.scd.time and lavfi.scd.score confirmed locally). Every EDL hard cut must be detected at exactly its frame. The offset to the nearest beat must lie within [-2, 0] frames for all cuts; list any positive (late) offsets. For slipped shots, the action peak must be ≤ 1 frame from its beat. Dissolves don't trigger scdet; check those against the EDL.

### Pipeline sync calibration test
Before cutting real footage, and whenever the toolchain changes, render a 30-60 s test through exactly the same path (HyperFrames render or the ffmpeg graph plus mux). The picture is black with one full-white frame at every planned cut frame and every beat frame (ffmpeg drawbox/geq enabled from a frame list, or one-frame HyperFrames clips); the audio is the real master. This catches renderer audio offsets, uncompensated AAC priming, fps rounding and segment joins before a 12-minute render is wasted.

**Doğrulama:** Find the white frames (signalstats YAVG > 200), convert them to times, and compare with the beats tracked on the master: offset ≤ 1 frame with no trend over time. Cross-correlate the output audio with the master: constant 0 ± 1 ms. Keep the test project as a regression check.

### Selects → stringout → rough → fine cut, run as a data pipeline
The professional order is review/select → assembly or stringout → rough cut → fine cut → picture lock → color → sound (Frame.io). Run it as data:
1) Ingest. ffprobe each file (fps r/avg, duration, rotation side data, color_transfer, creation_time / com.apple.quicktime.creationdate). `mdls -name kMDItemContentCreationDate` also covers photos. Keep all metadata local; GPS is personal data. Prefer original clips over an already-edited montage.
2) Split shots inside clips with scdet (t ≈ 10-15).
3) Score each shot at 2-5 fps:
   - sharpness (Laplacian variance or blurdetect)
   - exposure and clipping (signalstats)
   - motion and shake (siti TI, vidstabdetect transforms)
   - faces, plus VNDetectFaceCaptureQualityRequest
   - Vision aesthetics (overallScore, isUtility)
   - attention-saliency centroid
   - dominant Lab colors
   - diegetic events from the SoundAnalysis classifier (laughter, giggling, speech, singing)
4) Moments: per shot, pick 1-3 windows of 1.5-6 s that maximize aesthetics + face quality + action/laugh peak − shake − blur. Start each window 0.3-0.5 s before the action.
5) Stringout: every moment in chronological or thematic order, shown as a contact sheet for the AI and the user to approve. Changes are cheap here and expensive after a render.
6) Rough cut: fit moments to music sections and beat lengths.
7) Fine cut: frame trims, slip-to-beat, motivated transitions, ramps and slow motion on peaks, J/L cuts, punch-ins. Then lock picture before color and sound.
Priorities (Murch's Rule of Six): emotion 51% > story 23% > rhythm 10% > eye-trace 7% > 2D screen plane 5% > 3D space 4%. For montages, raise rhythm (≈19% per No Film School) and drop spatial continuity.

**Doğrulama:** Produce selects.json with per-moment scores and a contact-sheet PNG, and review both. Gates:
- No moment below the p20 sharpness of the shot set unless it is tagged as an emotional key.
- No adjacent pair with SSIM or perceptual-hash similarity > 0.8 (unintended jump cut).
- Face-area ratio changes ≥ 1.5× on at least 50% of adjacent pairs (shot-size variety).
- EDL length equals the planned music length to the frame.

### Ordering and story arc for a romantic montage
If timestamps exist, order by real chronology (season, hair and clothes confirm it). Otherwise cluster moments into scenes by date gaps (over 6-12 h), location, light and dominant color, then order scenes along an emotional arc:
- setup: calm, wide or establishing, 'who and where'
- build: everyday joy, medium shots, moderate pace
- peak, on the song's biggest section: the closest, most emotional moments, with slow motion
- breath, on the breakdown or bridge: quiet intimacy, photos with slow Ken Burns or parallax
- finale: callbacks to the opening, and the strongest 'us' shot held on the last note
Within a scene: move wide → medium → close, alternate shot sizes, never put near-duplicates side by side, and keep light and color consistent. Use transitions mainly at scene boundaries and hard cuts on beats inside scenes. Bookend: open and close on rhyming images (same place or pose, different time) so the ending is a match cut. Before rendering, show the proposed order as a storyboard image plus a list for approval, and ask for must-include and never-include moments.

**Doğrulama:** Kendall τ between EDL order and creation dates ≥ 0.8, unless the user approved a thematic order. Low ΔE2000 between shot medians within each scene. The top-k aesthetics and laughter moments fall in the top-energy music sections. The user's approval is recorded before the final render.

### Pacing to music sections and energy
Measure per-bar energy from short-term loudness (`ebur128=metadata=1`, lavfi.r128.S) or RMS, plus onsets. Find section boundaries from chroma/MFCC novelty or self-similarity and snap them to Beat This! downbeats.
Map energy to shot length:
- bottom 30% of bars: ≥ 8 beats (2 bars)
- middle: 4 beats
- top 30%: 2 beats
- top transients: 1-beat bursts of at most 4-8 cuts, then a long hold
Never more than 3-4 identical intervals in a row (e.g. 4-4-2-2-8). Phrases come in 4, 8, 12 or 16 bars; vary between 2-, 4-, 8- and 16-bar holds (Larry Jordan / CapCut guidance).
Soft or acoustic songs at 60-80 BPM:
- 4-8 beats per shot
- cuts on downbeats
- 0.5-1-beat dissolves at phrase starts
- slow motion in the chorus
- the fastest cutting only in the last chorus
An energy drop of 6 LU or more is a 'breath': longest holds, photos.
Reference: feature-film average shot length has fallen to roughly 2.5-4 s (Cutting/Salt). Music montages run shorter, but romantic pieces should breathe.

**Doğrulama:** Spearman ρ between per-bar cut count and per-bar energy ≥ 0.5. Density changes within ±1 beat of section boundaries. No single shot length (in beats) covers more than 60% of shots. Hero moments start on phrase downbeats.

### Cut on action, eye-trace and screen direction
Match on action: end the outgoing shot mid-movement and start the incoming shot a few frames into the same or continuing movement; the motion hides the cut (StudioBinder). In montages, cut at motion peaks such as a turn, spin or throw rather than on dead frames.
Eye-trace (Murch): put the incoming focal point (face or saliency centroid) near where the viewer is already looking. Within ≤ 15-20% of the frame diagonal the cut is nearly invisible; bigger jumps only as deliberate accents on strong beats.
Screen direction: keep motion direction consistent across a cut (left-to-right stays left-to-right) unless a reversal is the point. A whip pan must continue the existing motion.
In intimate shots, cut on a blink or a look.

**Doğrulama:** For each cut, measure the centroid distance between A's last frame and B's first frame from Vision saliency or faces. Compare the dominant motion vectors at A's end and B's start (phase correlation of consecutive grayscale frames): cosine ≥ 0 for at least 80% of cuts. Review the 13-frame strips of the outliers.

### J/L cuts and sound bridges
A J-cut starts the incoming shot's sound before its picture: a laugh or voice 6-24 frames early, up to 1-2 s for dialogue, to build anticipation. An L-cut lets the outgoing sound continue over the next picture, such as a spoken line carrying over a new shot. Keep split edits short, a few frames to a few seconds (Soundstripe).
Store picture and audio edit points separately in the EDL.
- HyperFrames: a separate `<audio>` element (WAV extracted from the clip) with its own data-start and data-media-start, plus a data-automation volume lane.
- ffmpeg: atrim/asetpts plus adelay for placement; `acrossfade=d=0.02:c1=qsin:c2=qsin`, or 10-30 ms afade in/out, at every audio boundary.
Duck the music 6-12 dB under the diegetic moment, with 150-300 ms ramps starting about 150 ms early.

**Doğrulama:** EDL audit: audio in/out differs from picture in/out where intended. Click check: the max absolute sample step in a 2 ms window around each edit stays under about 3× the local baseline. Cross-correlating diegetic audio against its source gives sync within ±1 frame. Duck depth is measured from music-stem short-term LUFS during versus before the moment.

### Match cuts (graphic, action, color, sound)
Search for candidate pairs instead of hoping for them:
- graphic: similar silhouette or position (foreground mask or saliency map IoU ≥ 0.5 after at most 10% scale and 5% shift)
- action: same motion direction and speed
- color/brightness: dominant hue/brightness within ΔE ~10
- sound: one sound or word bridging both shots
Nudge the incoming shot by ≤ 10% scale or position so the shapes overlap at the cut frame. Put the match on a downbeat or musical change.
Romantic uses: bookend open and close; time jumps (same pose, different season); a spin into a spin.

**Doğrulama:** Mask IoU at the cut frame ≥ 0.5; centroid distance ≤ 5% of the frame diagonal; review the 13-frame strip with Read.

### Transition grammar: motivated and sparing
Default to hard cuts. A transition needs a motive:
- camera or subject motion: whip, push, spin
- light: leak, burn, flash
- time or place change: dissolve, dip
- a music event: a hit gets a flash or punch; a riser gets a zoom-through
Use one primary transition for 60-70% of transitions plus 1-2 accents; never a different transition on every cut (HyperFrames transitions overview). Durations by energy:
- calm: 0.5-1.2 s
- medium: 0.3-0.5 s
- high: 0.15-0.3 s
The transition's midpoint or peak lands on the beat, and the whoosh peaks there too. Calm romantic: dissolves of 12-24 frames plus light leaks at chapter changes. Promos: whip, zoom and flash on hits. PremiumBeat warns whips become gimmicky if overused.

**Doğrulama:** Count transitions by type: the primary is at least 60%. Midpoint to beat ≤ 1 frame. Romantic pieces stay under about 4-6 transitions per minute outside deliberate sequences. Review a strip for each transition.

### Whip pan transition
8-12 frames total, e.g. 10 = 5 before plus 5 after the cut (After Effects / Premiere tutorials).
- Outgoing shot: translate X from 0 to 0.5-1.0 frame widths with power2.in or expo.in, so velocity peaks at the cut.
- Edges: tile mirrored copies (equivalent to Motion Tile's mirror edges) so no black or streaked edges appear.
- Blur: directional blur along the motion, ramping from 0 to about 6-12% of frame width at the cut. Options: ffmpeg dblur with radius via sendcmd, CoreImage CIMotionBlur, or in HTML an SVG feGaussianBlur with stdDeviation 'R 0'.
- Incoming shot: the mirror image, starting at -offset with maximum blur and easing to 0 with expo.out.
The direction should continue real motion in A or B. Add a whoosh peaking on the cut, panned the same way.
ffmpeg sketch (ran without errors locally): `split=3[a][b][c];[a]hflip[l];[c]hflip[r];[l][b][r]hstack=inputs=3,crop=w=W:h=H:x='W+0.8*W*pow(clip((t-T0)/0.167,0,1),2)':y=0,sendcmd=f=blur.cmd,dblur=angle=0:radius=1`, plus the reverse for B.
Caution: HyperFrames' built-in 'whip-pan' shader clamps samples to the frame edge and only blurs over about 8% of width, which streaks real footage. Inspect it before use.

**Doğrulama:** The per-frame Laplacian-variance curve dips symmetrically to its minimum at the cut. Horizontal displacement (phase correlation) is monotonic and peaks at the cut. No black edge pixels (blackdetect on 20 px side strips). Review the 13-frame strip.

### Zoom-through / punch transition
- Outgoing shot: scale 1.0 → 1.3-1.6 over 6-8 frames (power3.in or expo.in) with radial zoom blur ramping up to about 20-40 (CIZoomBlur inputAmount; range -200..200, default 20, verified locally), centered on the subject or a bright point.
- Cut at the peak.
- Incoming shot: 1.3-1.6 → 1.0 over 8-12 frames (expo.out) with blur falling to 0, or 0.7 → 1.0 for a zoom-out feel.
- Optional 1-2-frame +1 EV flash at the cut.
- Center both zooms on matching subjects (eye-trace).
Implementation: HyperFrames (GSAP scale on the inner wrapper, plus the built-in cinematic-zoom shader or a custom GLSL zoom blur), or Swift/CoreImage with a per-frame inputAmount. ffmpeg's coreimage filter only takes static parameters (tested), so a ramp needs one instance per short segment.
Resolution guard: scale × output width ≤ source width × 1.15.

**Doğrulama:** Laplacian-variance minimum at the cut; the scale curve matches the EDL; no upscaling beyond the guard; review the strip.

### Spin transition
- Outgoing shot: rotate 0 → 90-180° in 5-7 frames (power3.in).
- Incoming shot: -90/-180 → 0° in 7-10 frames (power3.out).
A rotated frame exposes its corners. Full cover needs scale ≥ |cos θ| + (long/short)·|sin θ|, about 2.0 at 45° for 16:9. Beyond small angles, use mirrored tiling or a blurred extension instead of extreme scaling.
Motion blur by temporal supersampling: render at 8× fps and average 4 sub-frames (180° shutter), or use HyperFrames' data-hf-motion-blur.
Only for energetic promos and music hits; never in calm romantic sequences.

**Doğrulama:** No black or transparent corners (blackdetect or cropdetect on corner patches). Rotation angle is monotonic in the strip. Check how often spins appear.

### Luma / ink wipes
A grayscale map drives the transition: each pixel switches from A to B when the map value falls below progress, with soft edge S = 0.05-0.15.
ffmpeg (tested; in xfade custom expressions P runs 1 → 0): `xfade=transition=custom:duration=0.5:offset=O:expr='st(1,clip((X/W-((1-P)*1.1-0.1))/0.1,0,1));A*ld(1)+B*(1-ld(1))'`.
Organic or ink look: a seeded fbm-noise PNG as the map, thresholded over time with `geq=lum='255*clip((lum(X,Y)/255-(T-T0)/D*(1+S)+S)/S,0,1)'`, then `maskedmerge`.
Timing: 12-20 frames for calm pieces, 8-12 for medium, sine.inOut on progress; the direction follows motion or reading direction.
HyperFrames: an animated CSS mask-image or clip-path, or a custom shader.

**Doğrulama:** The per-frame mean-luma progress curve is monotonic and S-shaped. The 10-90% edge band width in pixels matches S. Review the strip.

### Light leaks and film burns
Light adds, so blend with screen or add, never normal alpha. Use warm hues (amber ~#ff9a3d, peach, magenta) on plates larger than the frame, drifting slowly with 2-3 blobs at different speeds.
- Leak: 12-24 frames, opacity peaking at 0.6-0.9 exactly on the cut, which hides the cut under peak brightness.
- Film burn: 8-16 frames; a high-contrast burn grows from one edge with a hot core and covers at least 70% of the frame at the cut.
Generate them procedurally (HyperFrames light-leak shader or the CSS recipe in transitions/css-light.md, or numpy/GLSL fbm) rather than downloading overlay packs with unclear licences. Use them at openings, chapter changes and endings, not on every cut.

**Doğrulama:** The peak frame equals the cut frame. Faces don't clip: pixels at 255 outside the leak core ≤ 2% (signalstats YMAX plus a histogram). Count leaks per minute.

### Flash, dip to black/white, photosensitivity guard
- Flash: an exposure ramp, not a white overlay. Push +1.5 to +3 EV over the 2-3 frames into the cut, optionally hold one near-white frame, then decay over 4-8 frames on the incoming shot (expo.out). Tested locally: `eq=brightness='0.6*exp(-pow((t-T)/0.05,2))':eval=frame`, or `exposure` driven by sendcmd.
- Dip to black: 12-24 frames total (0.4-0.8 s) for time jumps and chapter changes. The music keeps playing.
- Dip to white: for dreamy or memory transitions.
- Limit: at most 3 flashes in any 1 s (WCAG 2.3.1; a 'general flash' is an opposing relative-luminance change of 10% or more).

**Doğrulama:** The per-frame YAVG curve shows the expected bell. Flash count per sliding 1 s window ≤ 3. `blackdetect=d=0.03:pix_th=0.08` finds only intended dips. Optionally run the photosensitivity filter and confirm it alters no frames (PSNR against the input stays very high).

### Speed ramps
Define playback rate s(t) with eased transitions:
- ramp down from 100% to 20-35% over 6-12 frames (sine.inOut or power2.inOut)
- hold 0.5-2 s on the emotional peak
- ramp back over 6-10 frames to 100-150% (a 'whoosh out')
Time it so the slowest moment lands on a downbeat or hit and the ramp-out ends at the next cut. Source position S(t) = ∫ s dt, integrated per output frame.
Slow segments need dense frames: real 60/120/240 fps footage (check unique frames; iPhone slo-mo originals are 120/240 fps) or a 4× optical-flow intermediate.
Three implementations:
(a) Swift 'retime' on VTFrameRateConversion: integer positions are copied, fractional ones become interpolationPhase = frac.
(b) ffmpeg closed form on a 120 fps intermediate. With rate linear in source time T, output time over the ramp is t = A + ln(1 + k(T−A))/k with k = (r−1)/(B−A); then t_B + (T−B)/r during the hold, the mirrored log term on the ramp up, and finally plain offset. Apply as `setpts='(piecewise expression)/TB',fps=30`. Tested: output length matched theory to the frame (115 frames).
(c) A HyperFrames data-automation rate lane on the high-fps intermediate, with points sampled every 2-3 frames from the ease.
Mute diegetic audio in the slow part, add a swell or reverse whoosh, and leave the music untouched. Below about 50 fps the slow part judders (Amateur Photographer).

**Doğrulama:** Plot S(t): monotonic and C1-continuous. mpdecimate finds 0 duplicate frames in the slow section. Ramp start and end frames match the EDL. The slowest frame is within ±1 frame of its target beat.

### Optical-flow slow motion
Prefer real high-fps sources. Detect the true rate by counting unique frames with mpdecimate, because many phone files are 60 fps containers holding 30 fps content.
Otherwise interpolate with VTFrameProcessor frame-rate conversion (macOS 15.4+; supported on this M2): 64RGBAHalf buffers, interpolationPhase [0.25, 0.5, 0.75] for 4×, qualityPrioritization .quality.
Limits: 2× is safe on most shots; 4× only on simple motion. Occlusions (hands, hair, crossing people, water) produce 'jelly' warping (Boris FX), so pick another shot or stay at 2× or less.
Fallbacks: rife-ncnn-vulkan (MIT, 437 MB, last release 2022) or ffmpeg minterpolate (mi_mode=mci:mc_mode=aobmc; artifact-prone and slow).
Use slow motion only on emotional peaks (hug, kiss, spin, snow throw), about 1-3 per minute.

**Doğrulama:** Leave-one-out test per shot: drop every second real frame, resynthesize it with phase 0.5, and compare with the real frame using the ffmpeg ssim/psnr filters or libvmaf. Heuristic gates: SSIM ≥ 0.90 and PSNR ≥ 30 dB allow 2×; ≥ 0.93 and ≥ 33 dB allow 4×. Inspect 13-frame strips at the highest-TI frames for warping.

### Punch-ins, zoom bounces and hit shake on downbeats
Punch-in: a scale step on a downbeat or hit.
- Size: subtle 1.00 → 1.08-1.12, hard 1.15-1.25.
- Timing: instant (a cut-zoom) or over 2-4 frames with expo.out.
- Then hold until the next phrase, or bounce back 1.06 → 1.0 over 8-12 frames (sine.inOut).
Anchor on the face or saliency centroid, not the frame center.
Big hits in promos can add camera shake: 4-12 px of seeded noise decaying over 6-8 frames, with 1-2 frames of motion blur.
Resolution guard: zoom ≤ (source/output) × 1.15. A 4K source into 1080p allows 2×; 1080 into 1080 allows ≤ 1.15×.
HyperFrames: GSAP on the inner wrapper (sub-pixel). ffmpeg: `scale=w='...':h=-2:eval=frame,crop=...` steps by whole pixels, which is fine for fast punches but not for slow zooms.

**Doğrulama:** The scale schedule per beat matches the EDL. Laplacian variance at maximum zoom is ≥ 0.6 of the unzoomed value. The subject centroid stays within the central 30% after the punch. Calm pieces have at most 1 punch per bar.

### Ken Burns for photos
A slow push or pan:
- scale 1.00 → 1.04-1.08 over 4-6 s (about 1.12 at most)
- pan ≤ 3-5% of the frame
- linear or a very gentle sine.inOut
The motion must already be running when the photo appears, so start it during the incoming dissolve. End on the subject's face or eyes; the longer the hold, the slower the zoom. Alternate in/out and left/right across consecutive photos. A landscape photo in a 9:16 frame should pan horizontally across the image rather than suffer a heavy crop or blurred fill.
Keep motion sub-pixel smooth with GSAP/CSS transforms in HyperFrames or a CoreImage Lanczos affine. ffmpeg zoompan rounds to whole pixels and jitters: upscale first (`scale=8000:-1,zoompan=...`, the Bannerbear trick) or avoid it.

**Doğrulama:** Frame-to-frame displacement from phase correlation is smooth (second-difference RMS < 0.1 px). The crop window stays inside the image, so no blank edges. Maximum upscale respects the source resolution. Directions vary across the sequence.

### 2.5D parallax from depth maps
Depth: Depth Anything V2 Small (Apache-2.0; CoreML fp16 49.8 MB) or DA3-Base (Apache-2.0). Not V2 Base/Large/Giant or DA3 any-view Large/Giant (CC-BY-NC-4.0), and not 3d-ken-burns (CC BY-NC-SA, needs CUDA).
Clean the subject edge with VNGenerateForegroundInstanceMaskRequest. Dilate foreground depth by 3-6 px, then blur σ 1-2 px to prevent tearing. For larger moves, split into a foreground layer and an inpainted background (OpenCV inpaint Telea on the mask dilated about 2% of width).
Render in HyperFrames with Three.js vendored locally (MIT): a plane mesh of about 256×448 segments displaced by depth, or a fragment-shader UV offset = (depth − focus) × camera offset.
Camera: dolly in 3-6% plus 1-2% lateral over 4-6 s, sine.inOut. Keep maximum foreground displacement ≤ 2-3% of frame width; an optional 1-3 px depth-of-field blur on the background sells the depth.

**Doğrulama:** Render the first, middle and last frames. Stretch score: the share of pixels near depth edges whose displacement gradient exceeds 0.3 px/px must stay ≤ 1%. Derive the foreground displacement in px from the camera path. Inspect enlarged edge crops with Read.

### Smart reframing 16:9 → 9:16 (subject tracking vs blurred fill)
Analyze at 5-10 fps with Vision: faces, humans and the attention-saliency heat map. Build a per-frame target box from the primary faces weighted by size and centrality, eyes on the upper third, with lead room toward motion or gaze; keep faces roughly in the 15-65% height band because Reels/TikTok UI covers the top and bottom.
Per shot, pick an AutoFlip camera mode:
- stationary: subject range < 15% of crop width; use the median position
- panning: monotonic movement; use a linear fit
- tracking: a smooth low-degree polynomial or a ~1 s Savitzky-Golay filter
Add a 6-10% dead zone, limit speed to ≤ 0.25 crop widths per second, and reset only at shot cuts.
If the needed content is wider than the crop (two people at opposite edges), fall back to blurred fill: fit to width, with a background of the same frame scaled to cover, downscale-blurred and upscaled (`scale=iw/8:-1,boxblur=10:2,scale=1080:1920`), brightness -0.08 to -0.15, saturation 0.8. A split-screen stack is the alternative.
Apply the path through crop x/y in a sendcmd file (crop accepts commands) or as GSAP x on the inner wrapper.

**Doğrulama:** Run face detection again on the output crops. In ≥ 95% of sampled frames the face center sits inside the central 60% of width and 20-45% of height; the face box is fully inside the frame in ≥ 98%. Path jerk RMS stays low and velocity is exactly 0 in stationary shots. Review a contact sheet of the crops.

### Stabilization (only when measured)
Phones already apply OIS/EIS. Over-stabilized handheld footage looks floaty, and rolling-shutter wobble cannot be fixed. Stabilize only shots with high measured jitter, using vid.stab in two passes:
1. `vidstabdetect=shakiness=5:accuracy=15:stepsize=6:result=t.trf`
2. `vidstabtransform=input=t.trf:smoothing=15:optzoom=1:zoomspeed=0.25:interpol=bicubic,unsharp=5:5:0.8:3:3:0.4`
smoothing N averages over 2N+1 frames, so 15 is about 1 s at 30 fps; tripod=1 gives a locked-off look; ffmpeg's docs recommend the unsharp afterwards. Stabilize first, at full resolution, before reframing or punch-ins, and keep the implied zoom ≤ 1.1.

**Doğrulama:** Run vidstabdetect (or phase correlation) on the output. High-frequency jitter (RMS of the second difference of global translation) drops by ≥ 50%. Zoom ≤ 10%. No black borders (blackdetect or cropdetect on the edges).

### Night-footage denoise
Order: decode → HDR to SDR → denoise → exposure/grade lift → light sharpening → grain last. Never brighten before denoising.
Apple's motion-compensated VTTemporalNoiseFilter reports unsupported on this M2, so use ffmpeg:
- temporal: `hqdn3d=2:3:5:8` (fast) or `atadenoise=s=7` (temporal without motion compensation, so it can ghost on motion)
- chroma: `chromanr=thres=25`
- high-quality spatial: `nlmeans=s=2.5:p=7:r=15` (very slow) or the GPU CoreImage route `coreimage=filter=CINoiseReduction@inputNoiseLevel=0.02@inputSharpness=0.4`
The FFmpeg wiki ranks bm3d and nlmeans highest quality and hqdn3d and atadenoise fastest. Stop before skin turns plastic.

**Doğrulama:** Noise sigma (MAD of a high-pass) in flat dark patches drops 30-60%. SSIM against the original on textured patches stays ≥ 0.9. Temporal flicker (std of mean luma in a static region) decreases. Strips at high-motion frames show no ghosting.

### Color pipeline: normalize → match → look → finish
1) Normalize. Detect HDR (color_transfer arib-std-b67 = iPhone HLG; smpte2084 = PQ) and convert to SDR BT.709: `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`. A naive scale looks washed out, and iPhone HLG has a raised black point, so check the blacks. Black point at Y ≈ 16-20, whites ≤ 235. Rule of thumb for face luma: ~55-70% on lighter skin, ~40-55% on darker skin.
2) Balance and match each scene to a hero frame. Use a Reinhard mean/std transfer in Lab or Oklab at 50-80% strength, or MKL via the color-matcher CLI (GPL-3.0, local use), and bake per-shot 33³ .cube files. Keep skin hue near the vectorscope I-line (≈123° in BT.601 YCbCr, ±10-15°).
3) Look. One global LUT or curve set for all shots: `lut3d=file=look.cube:interp=tetrahedral`. A gentle S-curve, highlight roll-off, subtly warm highlights and cool shadows, saturation 0.9-1.05. Build it locally (HyperFrames media-use buildCube params, or numpy) rather than downloading LUT packs.
4) Finish. For romantic pieces, bloom/halation (CIBloom, small radius) and a subtle vignette. Grain goes last (Pixop: grade first, then 10-20% intensity): luma-only, about 1-1.5 px, 2-4% amplitude, from a mid-gray noise plate with a softlight blend. Encode with x264 `-tune grain` (tune verified locally).
Order of operations follows Noam Kroll: neutralize and match → exposure fixes → color fixes → look → final tweaks.

**Doğrulama:** Compute each shot's median L*a*b*. ΔE2000 between consecutive shots in a scene ≤ 3-5 unless intentional. Clipped pixels < 0.5%. Skin hue within ±15° of the I-line. Before/after hstack frames for AI review. Check the file-size or bitrate impact of grain.

### Shutter-angle motion blur for footage and graphics
180° rule: blur length ≈ 50% of the motion per frame.
- Graphics: render HyperFrames at 240 fps, then `tmix=frames=4,select='eq(mod(n,8),3)',setpts=N/30/TB` for true sub-frame accumulation at a 180° shutter, 30 fps. Or use the data-hf-motion-blur component with shutterAngle 180-360 for a natural look; its default 720 is a heavy two-frame smear. Apply it only to fast snaps (more than about one element width per frame), never to text the viewer must read mid-move.
- Sunny phone clips shot at very fast shutter look staccato. Use VTMotionBlur (strength 1-100, calibrated on a test clip), or 8× frame-rate conversion plus tmix as above.

**Doğrulama:** On a tracked moving edge, the ratio of edge spread to displacement ≈ 0.4-0.6. Static frames keep their Laplacian variance (they stay sharp).

### Sound design layer
Stems: music, diegetic, ambience/room tone, transition SFX, impacts, risers.
- Whoosh: length ≈ transition length +30-50%, peak on the cut frame, panned with the motion.
- Riser: ends exactly on the downbeat or drop; optionally 1-2 frames of silence just before ('suck-out').
- Impact: transient on the cut frame (±5 ms); in promos a sub-drop from 60 to 35 Hz decaying over 0.5-1.5 s.
- Reverse swell into slow-motion moments.
Levels: in romantic montages SFX sit 12-18 dB below music peaks; louder in promos.
Room tone: under any muted or cut diegetic section, keep ambience at -45 to -35 LUFS with 0.5-1 s fades so the mix never drops to digital silence by accident.
Sources: procedural synthesis (numpy pink noise through a moving band-pass with an envelope; sine sweeps), or the bundled Pixabay SFX in ~/.claude/skills/media-use/audio/assets/sfx (commercial use OK, no attribution needed).
Work order (Krotos): dialogue → ambience → foley → designed FX → music → master.

**Doğrulama:** Onset detection on the SFX stem puts each peak within ±1 frame of its cut. Stem short-term LUFS relative to music falls in the target range. Master true peak ≤ -1 dBTP.

### Music edit to length, and endings
Fit the song to the edit; never cut a song off mid-phrase with a short fade (the earlier render did this at 284.95 s). Remove or repeat whole 4/8-bar phrases in the middle, at downbeats where beat-synchronous chroma+MFCC similarity is high. This is the Adobe Remix principle: keep the intro and outro. Use a 20-60 ms equal-power crossfade, e.g. `acrossfade=d=0.04:c1=qsin:c2=qsin`.
Land the last shot on the final chord. If shortening, jump to the outro at a phrase boundary and fade only the reverb tail (1-3 s). Hold the last image 1-2 s, then fade to black over 12-24 frames after the last note.

**Doğrulama:** Run Beat This! on the edited song. Across each splice, inter-beat-interval change < 2%, with no missing or extra beat. Short-term loudness jump < 1.5 LU. The spectral-flux spike at the splice is no higher than the p95 of neighbouring beats.

### Mix: ducking, micro-crossfades, loudness
Ducking: music down 8-12 dB under diegetic laughs and lines and 15-20 dB under narration, with 100-200 ms pre-roll and 250-500 ms release.
- HyperFrames: a data-automation volume lane, or data-fx-carve on the music bed.
- ffmpeg: `[vo]asplit[sc][v];[music][sc]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[m];[m][v]amix=inputs=2:normalize=0`.
Micro-crossfades of 5-30 ms on every audio edit; video-use applies 30 ms fades at every cut.
Loudness:
- YouTube, Instagram and TikTok: -14 LUFS integrated, ≤ -1 dBTP (YouTube only turns loud audio down).
- Apple Music: -16 LUFS.
Measure with `ebur128=peak=true`, then correct with two-pass loudnorm or gain plus alimiter. Encode once with aac_at at 256 kbps.

**Doğrulama:** ebur128 summary (I, LRA, TP) within target. Duck depth measured on the stems. Click detector at every edit. Final cross-correlation drift check.

### Motion-design principles: easing, anticipation, overlap
Disney's 12 principles applied to video, with Material 3 easing values (Flutter API).
Easing:
- No linear motion, except constant drifts, Ken Burns and tickers.
- Entrances decelerate: power3.out or expo.out; M3 emphasizedDecelerate = cubic-bezier(0.05, 0.7, 0.1, 1).
- Exits accelerate: power2.in; M3 emphasizedAccelerate = (0.3, 0, 0.8, 0.15).
- On-screen moves: power2/3.inOut; M3 standard = (0.2, 0, 0, 1).
Durations at 30 fps:
- micro: 6-9 frames (200-300 ms)
- standard: 12-18 frames
- hero: 18-30 frames
Other principles:
- Anticipation: a 3-6-frame reverse move of 5-10% before big moves.
- Follow-through: 5-10% overshoot (back.out(1.2-1.6)) settling in 6-12 frames.
- Overlapping action: children offset 2-4 frames (stagger 0.06-0.12 s).
- Arcs for organic objects (MotionPath).
- Staging: one hero motion at a time.
- Holds of 0.5-1.5 s after reveals.
- Blur only fast snaps.
Animate only x/y/scale/rotation/opacity, on a single paused, seek-safe timeline. GSAP's standard licence permits commercial use, including former bonus plugins; it only bars tools that compete with Webflow.

**Doğrulama:** Sample element bounding boxes per frame (hyperframes-animation/scripts/animation-map-sampling.mjs; SKILL.md mentions animation-map.mjs, which is missing locally). Check the velocity profiles: zero velocity at the ends of eased moves, overshoot ≤ 10%, consistent stagger, no two hero elements peaking within 3 frames of each other, holds present. Snapshot strips at key poses.

### Product demo / explainer structure and UI motion
Structure:
- Hook in 0-3 s: show the outcome, not a logo.
- Problem in ≤ 5 s.
- Solution reveal.
- 2-3 features, one idea per scene, 4-8 s each.
- Proof, then CTA.
Length: ≤ 60-90 s for social, ≤ 2 min for landing pages; Wistia's data across 564k videos shows engagement dropping sharply after 2 minutes.
UI motion:
- Capture the UI at 2× resolution for zoom headroom.
- Zoom to the clicked element at 1.5-2.5× over 0.5-0.8 s (power3.inOut).
- Cursor moves on gentle arcs over 0.4-0.7 s, with a 0.2-0.3 s click ripple.
- Hold 1-2 s for reading.
- One primary transition (push or whip) and soft click/whoosh SFX.
- Music about 15-20 dB under the voice-over.
Reuse HyperFrames blueprints and rules: cursor-ui-demo, coordinate-target-zoom, camera-cursor-tracking, zoom-out-workspace-reveal.

**Doğrulama:** Scene count matches the script. Every hold is at least the reading time (≈3 words/s). Cursor paths have no velocity discontinuities. Zoom targets are centered within 5%. Run the loudness and ducking checks.

### How the AI 'watches': review artifacts
The assistant cannot watch in real time but can Read images. Generate:
- a contact sheet, one frame every 1-2 s with timestamps (existing CLAUDE.md recipe)
- a strip per transition: cut frame −6 to +6, `select='between(n,F-6,F+6)',scale=240:-1,tile=13x1`
- beat strips: waveform with beat, downbeat and cut ticks drawn in numpy
- crop-path plots: subject x against crop window over time
- speed-curve plots
- before/after grade pairs (hstack)
- per-stem loudness plots
Never claim audio sounds good: report measured numbers only, and ask the user to listen once on phone speakers and on headphones.

**Doğrulama:** Every QC statement in the report cites a measured number or a reviewed PNG path.

### Amateur-edit QC checklist (run before delivery)
Each sign has an automated check:
1. Late or drifting cuts versus the beat (scdet vs beats; cross-correlation).
2. Metronomic, unvaried cut intervals (shot-length histogram).
3. A transition on every cut, or a mix of many transition types (counts by type).
4. Jump cuts between near-identical framings (adjacent SSIM or pHash > 0.8).
5. The same shot size repeated (face-area ratio).
6. Shots held past their peak (motion energy below 20% of the peak for more than 1.5 s).
7. Shaky or blurry selects (jitter, Laplacian variance).
8. Color or exposure jumps between adjacent shots (ΔE, ΔL*).
9. Crushed blacks, clipped highlights or oversaturation (signalstats).
10. Black bars or sideways clips in vertical output (cropdetect, displaymatrix).
11. Every Ken Burns move the same, or jittery zoompan.
12. Slow motion that stutters (duplicate frames) or warps (leave-one-out score).
13. Clicks at edits, digital-silence holes, music truncated mid-phrase.
14. Music too quiet or loud; true peak above -1 dBTP.
15. Diegetic audio fighting the music; SFX too loud.
16. Stray 1-2-frame 'flash frames' at cuts (scdet pairs fewer than 3 frames apart).
17. Text overlays the user did not ask for (this user explicitly did not want them).
18. Faces under the platform UI zones.
19. Grain or bitrate mush (VMAF of share copy vs master; inspect frames).
20. A weak opening shot, a long logo intro, or no resolution at the end.
21. Overuse of slow motion or ramps (more than about 3 per minute).
22. Unintended black frames (blackdetect).
23. More than 3 flashes per second.

**Doğrulama:** A QC script prints pass/fail per item with numbers and writes strip PNGs for the failures. Delivery requires every item to pass or be explicitly waived.

### Delivery and export settings
Share copy:
- H.264 High, or HEVC with -tag:v hvc1 for Apple-to-Apple sharing.
- yuv420p with explicit BT.709 tags: `-colorspace bt709 -color_primaries bt709 -color_trc bt709`.
- CFR 30, GOP ≤ 2 s, `-movflags +faststart`.
- AAC-LC 48 kHz at 256 kbps with aac_at.
- 8-12 Mbps for 1080×1920; platforms re-encode anyway.
- x264 `-preset slow -tune film`, or `-tune grain` when there is grain.
Keep a high-quality archive (CRF 14-16) only if disk allows. ProRes at 1080×1920 is roughly 1 GB or more per minute, which matters with ~20 GB free. WhatsApp recompresses heavily; send via AirDrop or iCloud link for quality.

**Doğrulama:** ffprobe: codec, profile, pix_fmt, color tags, fps, duration, bitrate. `-f null -` decode test. VMAF of the share copy against the master ≥ 90 (libvmaf is in the local build). Loudness re-measured. Size within budget.


## Riskler

- Homebrew does not work right now: `brew info` fails with 'You have not agreed to the Xcode license'. Fixing it needs the user to run sudo (`sudo xcodebuild -license accept` or `sudo xcode-select -s /Library/Developer/CommandLineTools`). Swift works without this when DEVELOPER_DIR=/Library/Developer/CommandLineTools is set.
- Disk is tight (19-21 GB free). HyperFrames' persistent frame-extract cache in $TMPDIR is already ~907 MB. Switching HyperFrames' source-frame extraction from the default JPG to PNG (--video-frame-format png) for a 5-minute vertical montage would need tens of GB. ProRes intermediates at 1080x1920 run about 1 GB or more per minute. Use HEVC or H.264 intermediates at high bitrate, delete them after use, and check `df` before every render.
- VTFrameProcessor availability was probed but end-to-end quality and throughput on the M2 are untested. VTTemporalNoiseFilter is unsupported on this machine. Super-resolution only supports 4×. Frame-rate conversion needs 64RGBAHalf buffers, so expect pixel-format conversion and memory cost.
- Beat This! can still fail on rubato or under-represented material, as its authors note. The reliability gates and fallbacks (phrase pacing, user tap-along) are required, not optional. Installing it on Python 3.13 with the torchaudio 2.11 pin is untested and takes about 0.7 GB.
- The assistant cannot hear. Every audio judgement must be a measurement: cross-correlation lag, LUFS, true peak, click detection, onset alignment. The user should listen once on phone speakers and on headphones before sharing.
- Re-cutting an already-edited montage loses chronology and resolution (the earlier source was 720x1280, upscaled to 1080x1920). Its extracted audio may also contain diegetic sounds tied to the old picture order. Get the original clips and the original song file.
- The non-commercial licence traps listed under avoid are easy to pull in through transitive dependencies (madmom models, NC depth checkpoints). Pin exact model names in scripts.
- The music-to-video skill insists its librosa analyzer is the only beat source. For soft or acoustic songs, document in the project CLAUDE.md that Beat This! overrides it, or don't use that workflow for real-footage montages.
- iPhone HLG and Dolby Vision tone-mapping in ffmpeg (zscale/tonemap) can differ from how Photos renders the clip. iPhone HLG has a raised black point, so compare stills against an iPhone-exported SDR reference when possible. libplacebo is only available via ffmpeg-full.
- The local ffmpeg is 6.0. Newer syntax and features (-/filter_complex, xfade transitions added in 7.0+) are not available, so docs for 8.x/9.x may not match. Test every command on synthetic lavfi input first.
- Privacy: personal frames must never leave the machine. Keep `hyperframes snapshot --describe false`; do no cloud captioning or vision. Model downloads (Hugging Face, cloud.cp.jku.at) carry no user data; set HF_HUB_DISABLE_TELEMETRY=1 and DO_NOT_TRACK=1.

## Açık sorular

- Will future romantic montages start from the original phone clips and photos (with creation dates) and the original song file, rather than an already-edited montage? This decides whether ordering can be chronological and whether quality is preserved.
- Primary delivery channels (WhatsApp, iMessage/AirDrop, Instagram Reels/TikTok, YouTube, LinkedIn)? This sets aspect ratio, loudness target (-14 vs -16 LUFS), bitrate, and HDR vs SDR.
- May the assistant ask the user to fix Homebrew with sudo (Xcode license) and install ~0.7 GB of PyTorch for Beat This!? Optionally also ffmpeg-full (~0.5-1.5 GB, unverified estimate).
- Preferred look: 30 fps natural vs 24 fps 'cinematic'? Converting 30 fps phone footage to 24 needs optical flow or judders. Is light grain, bloom or halation welcome?
- Should every montage include an approval step (storyboard image plus shot list with beat lengths) before the long render? Recommended.
- For work videos: brand fonts, colors and logo assets with clear licences, and typical product types (web app UI, mobile app, hardware)? This decides between HyperFrames blueprints and footage pipelines.

## Şüpheci doğrulama

The findings are accurate and well grounded. Almost every local claim reproduced exactly on 2026-10-05: the ffmpeg 6.0 filters, encoders and build flags, xfade's P running 1 → 0, VTFrameProcessor support, the 303 SoundAnalysis classes, and the HyperFrames whip-pan clamping and beats metronome. The licence claims also check out (Beat This! MIT for code and weights; Depth Anything V2 Small and DA3-Base/Metric/Mono Apache-2.0 versus non-commercial for the rest; 3d-ken-burns; Remotion; GSAP).

The root cause of the user's 'audio slipping' complaint is confirmed with numbers. Concatenating AAC segments drifted 24 ms per segment with ffmpeg's encoder and 67 ms with Apple's. A constant-BPM fit of a rubato track missed by up to 564 ms, while Beat This! final0 scored F = 0.964 at ±70 ms in 5.7 s on CPU using 0.9 GB RAM.

All three picks stand: the installed FFmpeg, the Apple frameworks through a Swift CLI, and Beat This!. I found no better current MIT- or Apache-licensed beat tracker. VT frame-rate conversion now works end to end on this M2 at about 25 ms per 1080x1920 frame.

Required fixes:
- The Beat This! install recipe is broken. torchaudio 2.11's load() needs TorchCodec, and beat-this does not declare soundfile, its fallback. The recipe is also superseded: uv/Python 3.12 is already set up and beat-this already works in ortamlar/ses.
- -/opt arrived in FFmpeg 7.0, not 7.1, and the local 6.0 cannot read HEIC (verified).
- animation-map.mjs does exist.
- atempo accepts 0.5-100 per instance, and vid.stab's zoomspeed is ignored with optzoom=1.
- The Swift frame-rate-conversion code has API gotchas: use the completion-handler call, and use .random rather than .sequential for non-consecutive pairs.
- Narrow the essentia and video-use avoid entries.
- Homebrew upgrades need sudo; DEVELOPER_DIR does not help.

The main gaps are iPhone HEIC and Live Photo ingest, an editable-timeline handoff, upscaling of low-resolution sources, transcription-driven cuts, and integration with the workspace's existing `medya` capability layer.

Test artifacts are in the scratchpad (bt/run_bt.py, frc.swift, aac/); no workspace files were changed. Evidence is from local tests and the primary sources listed. The web-search budget ran out, so the ITU figures and some sizes were not re-fetched.

### Kontroller

- [confirmed] Beat This! code AND published weights are MIT; PyPI beat-this 1.0 (2026-04-13) and 1.1.0 (2026-04-14). — PyPI JSON shows 1.0 uploaded 2026-04-13T15:21 and 1.1.0 uploaded 2026-04-14T10:16, both MIT. requires_dist: numpy>=1.20, torch>=2, torchaudio, einops, rotary-embedding-torch, soxr. The README says: 'The code and the published model weights are released under the MIT license.' The CHANGELOG dates v1.0 to 2024-10-18 on GitHub, so 1.1.0 is the only release since then; it adds support for non-CUDA accelerators. (https://pypi.org/pypi/beat-this/json ; https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md ; https://raw.githubusercontent.com/CPJKU/beat_this/main/CHANGELOG.md)
- [refuted] A fresh venv plus `pip install beat-this` is enough to beat-track a WAV (the pick's install command). — beat_this/preprocessing.py load_audio() tries torchaudio.load, then soundfile, then madmom. In torchaudio 2.11.0, load() is load_with_torchcodec. In the workspace env it raised 'ImportError: TorchCodec is required for load_with_torchcodec' (tested 2026-10-05). soundfile is not in beat-this's requires_dist, so a clean env fails with 'Could not load audio', even for WAV. The existing env only works because librosa pulled in soundfile 0.14.0. (/Users/onurkaya/Projects/video/ortamlar/ses/lib/python3.12/site-packages/beat_this/preprocessing.py ; .../torchaudio/__init__.py)
- [refuted] torchaudio 2.11 may pull torch back to 2.11.x; uv is not installed; use the python3.13 framework and ~/.venvs/beat. — On PyPI, torchaudio 2.11.0 has requires_dist = null, so torch is not pinned. The workspace now has arac/uv (uv 0.12.23) and the env ortamlar/ses (CPython 3.12.15). That env holds beat-this 1.1.0, torch 2.14.1, torchaudio 2.11.0 and soundfile 0.14.0 (see ortamlar/ses-kurulum.log), and it runs. The final0, final1 and final2 checkpoints are already in modeller/torch/hub/checkpoints, 81,058,141 bytes each. Footprint: torch 542 MB installed, about 0.7 GB in total with dependencies and one checkpoint, so the 700 MB disk estimate holds. (https://pypi.org/pypi/torchaudio/json ; local ls/du)
- [confirmed] CPU is enough for a 5-minute song on an M2; Beat This! follows tempo drift; MPS is untested. — Local test on a synthetic 300 s soft pluck track with rubato (76 BPM wandering ±7, 12 ms attacks, pad underneath), final0 on CPU:
- Inference 5.7 s, max RSS 0.88 GB.
- F = 0.964 at ±70 ms; median |error| 11.5 ms, p95 55.5 ms.
- A constant-BPM fit of the same ground truth misses by up to 564 ms.

device='mps' through the Python API works but gives no speedup: identical output in 6.5 s. The CLI --gpu flag only selects CUDA, so the CLI always runs on CPU on a Mac.

Caveat: on this signal 338 of 367 beats were flagged as downbeats, so downbeat output can be badly wrong. (scratchpad test: /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/bt/run_bt.py)
- [confirmed] Joining separately AAC-encoded segments drifts by about N × 20-70 ms (priming of 1024 samples in ffmpeg, 2112 in Apple's encoder). — Test: a 10 s click track split into 10 × 1 s segments, each AAC-encoded, then joined with the concat demuxer (-c copy).
- Native aac: output 10.24 s; click offset grows 21 → 141 → 237 ms.
- aac_at: output 10.67 s; click offset grows 44 → 377 → 644 ms.
That is about 24 ms and 67 ms per segment. The root-cause diagnosis and the 'mux one continuous master once' rule hold. (scratchpad/aac test with the local ffmpeg 6.0)
- [confirmed] The local ffmpeg-static 6.0 has every listed filter and encoder; it is configured --enable-gpl --enable-version3 --enable-nonfree, so it is not redistributable. — -buildconf shows those flags plus libvidstab, libzimg, libvmaf, libsvtav1, libx265 and libass.
- Every listed filter is present, including xfade, vidstab*, zscale, tonemap, lut3d, nlmeans, bm3d, chromanr, dblur, tmix, minterpolate, scdet, signalstats, blurdetect, siti, vfrdet, mpdecimate, photosensitivity, libvmaf, ebur128, sidechaincompress, axcorrelate, coreimage and sendcmd. rubberband and libplacebo are absent.
- Encoders aac_at, h264/hevc/prores_videotoolbox, libx264, libx265 and libsvtav1 are present.
- xfade has 46 presets plus custom.
- dblur, eq, exposure, crop, rotate, curves and colorbalance carry the C (command) flag; coreimage does not.
- ffprobe is n4.4.1. (/Users/onurkaya/Projects/video/arac/ffmpeg -buildconf / -filters / -encoders)
- [confirmed] In xfade custom expressions, P runs from 1 to 0. — Using expr='P*255' between two gray inputs, the per-frame YAVG ran 255, 229, 204 … 25, 0 across a 1 s transition. The researcher's luma-wipe expression is therefore oriented correctly. (local ffmpeg test)
- [refuted] 6.x uses -filter_complex_script; -/filter_complex arrives in 7.1+. — The FFmpeg Changelog lists 'ffmpeg CLI options may now be used as -/opt <path>' under version 7.0. The same 7.0 entry adds 'Support for HEIF/AVIF still images'. The local 6.0 cannot open a HEIC made by sips ('moov atom not found … Invalid data found'). (https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog ; local sips/ffmpeg test)
- [confirmed] Homebrew ffmpeg 9.0.2 is slimmed (no vidstab or zimg); ffmpeg-full adds rubberband, libplacebo, whisper.cpp, libass and frei0r. — The ffmpeg formula's dependencies are dav1d, lame, libvmaf, libvpx, openssl@3, opus, sdl2-compat, svt-av1, x264, x265 and xz.
ffmpeg-full 9.0.2 has 45 runtime dependencies, including libvidstab, zimg, rubberband, libplacebo, whisper.cpp, libass, frei0r and tesseract. It is keg_only, with arm64 bottles for golden_gate, tahoe and sequoia.
Upstream 9.0.2 'Lei' is dated 2026-09-18, 8.1 is 2026-03-16 and 8.0 is 2025-08-22.
Note that libass is already in the local 6.0 build, so it is not a gain. (https://formulae.brew.sh/api/formula/ffmpeg.json ; https://formulae.brew.sh/api/formula/ffmpeg-full.json ; https://ffmpeg.org/download.html)
- [confirmed] Homebrew is blocked by the unaccepted Xcode licence and fixing it needs sudo; Swift works through DEVELOPER_DIR. — `brew info` returns 'You have not agreed to the Xcode license'. Setting DEVELOPER_DIR does NOT rescue brew (tested): bin/brew re-execs with `env -i` and a filtered environment, then brew.sh runs `/usr/bin/xcrun --find clang` against the xcode-select path, which is Xcode.app. `DEVELOPER_DIR=/Library/Developer/CommandLineTools swift --version` reports Swift 6.4, and swiftc compiled a test binary. (/opt/homebrew/bin/brew, /opt/homebrew/Library/Homebrew/brew.sh lines 403-431; local runs)
- [uncertain] The martin-riedl static arm64 9.0.2 build (2026-09-20) is signed and notarized; vid.stab inclusion is unconfirmed. — The site shows 9.0.2 created on 20 Sep 2026 and says 'macOS binaries are signed (zip and installer) and notarized (installer)', so the zip itself is not notarized. Its listed libraries include zimg and libass. vid.stab, rubberband, libplacebo and whisper are not listed, so the build probably has no vid.stab. (https://ffmpeg.martin-riedl.de/)
- [confirmed] VTFrameProcessor on this M2: frame-rate conversion (FRC), motion blur and optical flow are supported; the temporal noise filter is not; super-resolution is 4x only; FRC needs 64RGBAHalf. — Swift probe:
- isSupported is true for FRC, MotionBlur and OpticalFlow; false for TemporalNoiseFilter.
- SuperResolution is supported with scale factors [4].
- LowLatencyFrameInterpolation is supported and accepts 420v.
- LowLatencySuperResolution offers no scale factors at 1920x1080.
- FRC and MotionBlur supportedPixelFormats are ['RGhA'].
SDK headers: FRC is API_AVAILABLE(macos 15.4); the temporal noise filter and the low-latency processors are macOS 26. (Swift probe via DEVELOPER_DIR=/Library/Developer/CommandLineTools; VideoToolbox.framework/Headers/VTFrameProcessor_*.h)
- [confirmed] VTFrameRateConversion end-to-end quality and throughput are unmeasured; arbitrary interpolationPhase values are accepted. — Header: interpolationPhase is an array of floats from 0 to 1, one per destination frame.

Compiled test at 1080x1920 with phases [0.25, 0.5, 0.75]:
- First call 131 ms, then 64-80 ms per call, about 22-27 ms per interpolated frame.
- About 120 MB RSS.
- A synthetic disc moving 120 px gave interpolated centroids of 330.2, 360.2 and 389.9 (expected 330, 360, 390).

Gotchas:
- Swift's `process(parameters:)` resolves to the AsyncThrowingStream variant, which failed with VTFrameProcessorProcessingError -19740. The completion-handler variant worked.
- Re-submitting the same pair with .sequential produced extrapolated frames (432-460 px, past the next frame); .random was correct.

Quality on real occlusions (hands, hair, water) is still untested. (scratchpad/frc.swift)
- [confirmed] The Apple-framework pick needs zero download. — True for FRC, motion blur, optical flow, Vision and SoundAnalysis. The one exception is VTSuperResolutionScaler: its header says the processor 'may require ML models which the framework needs to download'. Apps check configurationModelStatus and call downloadConfigurationModel; failure is reported as VTFrameProcessorAssetDownloadFailed. (VTFrameProcessor_SuperResolutionScaler.h lines 47-82; VTFrameProcessorErrors.h)
- [confirmed] The SoundAnalysis built-in classifier has 303 classes, including laughter, giggling, speech, singing, cheering, applause and crying_sobbing; Vision aesthetics is at revision1; the foreground instance mask is available. — Swift probe: knownClassifications.count = 303 with all 7 labels present. CalculateImageAestheticsScoresRequest().revision = revision1. VNGenerateForegroundInstanceMaskRequest.supportedRevisions = [1]. (local Swift probe)
- [confirmed] Depth licences: V2 Small is Apache-2.0 and V2 Base/Large/Giant are CC-BY-NC-4.0; DA3 Large/Giant are non-commercial; DA3-Base and DA3-Metric-Large are Apache-2.0. Apple's CoreML V2 Small is 49.8 MB F16, 518x396, about 25-33 ms. — Depth Anything V2 README: 'Small … Apache-2.0. Base/Large/Giant … CC-BY-NC-4.0'.
DA3 README: GIANT and LARGE (including the -1.1 and NESTED variants) are CC BY-NC 4.0. BASE, SMALL, METRIC-LARGE and MONO-LARGE are Apache 2.0; released 2025-11-14.
HF card: Apache-2.0, F16 49.8 MB and F32 99.2 MB, input 518x396, 24.58 ms on M3 Max and 32.80 ms on M1 Max (Neural Engine). (https://github.com/DepthAnything/Depth-Anything-V2 ; https://github.com/ByteDance-Seed/Depth-Anything-3 ; https://huggingface.co/apple/coreml-depth-anything-v2-small)
- [confirmed] sniklaus 3d-ken-burns is CC BY-NC-SA and needs CUDA. — The README says it is 'licensed under … CC BY-NC-SA 4.0 and may only be used for non-commercial purposes', and that 'Several functions are implemented in CUDA using CuPy'. (https://github.com/sniklaus/3d-ken-burns)
- [confirmed] Remotion needs a company licence above 3 employees; GSAP is free commercially, including the former bonus plugins. — Remotion's LICENSE.md makes it free for individuals, for-profit organisations with up to 3 employees, non-profits and evaluation; anyone else needs a Company License.
GSAP's standard licence allows commercial use, and SplitText, MorphSVG and the other formerly paid plugins are free. It prohibits only no-code visual animation builders that compete with Webflow, and states 'AI-generated code is not a Prohibited Use'. (https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md ; https://gsap.com/standard-license/)
- [confirmed] video-use needs a paid ElevenLabs key. — The README makes an ElevenLabs API key mandatory for transcription; the code is MIT. More precisely the requirement is an account plus API key, not necessarily a paid one. It breaks the no-accounts rule either way. (https://github.com/browser-use/video-use)
- [confirmed] rife-ncnn-vulkan's last release is 2022-10-29 (437 MB macOS zip). — The releases page shows 20221029 as the latest of 10 releases. The asset size could not be verified because the GitHub API returned 403. (https://github.com/nihui/rife-ncnn-vulkan/releases)
- [confirmed] allin1's last release was October 2023, with heavy dependencies. — PyPI shows allin1 1.1.0 uploaded 2023-10-10 with a null licence field. requires_dist: demucs, huggingface-hub, hydra-core, librosa, matplotlib, natten (macOS), numpy, omegaconf. madmom is not in requires_dist and is installed separately. (https://pypi.org/pypi/allin1/json)
- [confirmed] HyperFrames' whip-pan clamps samples to the frame edge (offsets up to 1.5 widths) and blurs over about 8% of the width; there are 15 CPU shader transitions; HyperFrames is Apache-2.0. — chunk-3GXQPCJC.js: fromOff = p*1.5; fuv = Math.max(0, Math.min(1, ux + fromOff + p*0.08*f)). The TRANSITIONS registry has 15 entries: crossfade, flash-through-white, chromatic-split, sdf-iris, glitch, light-leak, cross-warp-morph, whip-pan, cinematic-zoom, gravitational-lens, ripple-waves, swirl-vortex, thermal-distortion, domain-warp, ridged-burn. package.json: 0.8.124, Apache-2.0. (/Users/onurkaya/Projects/video/node_modules/hyperframes/dist/chunk-3GXQPCJC.js)
- [confirmed] `hyperframes beats` (bpm-detective) produces one global BPM, i.e. a metronome grid. — beat-analyzer.global.js picks energy peaks, takes a median-IOI BPM and checks it against bpm-detective@2.0.5. When the two agree within 10%, regularizeBeats() emits offset + n·60/bpm over the whole track, a constant grid. Otherwise it returns the raw energy peaks. (/Users/onurkaya/Projects/video/node_modules/hyperframes/dist/beat-analyzer.global.js)
- [refuted] The animation-map.mjs that SKILL.md mentions is missing locally. — ~/.claude/skills/hyperframes-animation/scripts/animation-map.mjs exists (23,340 bytes, dated 2026-10-04 22:03), with its test file, next to animation-map-sampling.mjs. The researcher probably looked in node_modules/hyperframes/dist/skills, which only contains hyperframes, hyperframes-cli and media-use. (ls ~/.claude/skills/hyperframes-animation/scripts)
- [confirmed] data-hf-motion-blur defaults to a 720° shutter; there is about 0.9 GB of extract cache in $TMPDIR; frames are extracted as JPG by default. — references/motion-blur.md gives a shutterAngle default of 720 ('two frames'). $TMPDIR/hyperframes-extract-cache-501 is 907 MB. The render flag --video-frame-format defaults to 'auto' (jpg or png; alpha sources always use PNG). (~/.claude/skills/hyperframes-animation/references/motion-blur.md; render-4PBKSNC3.js)
- [confirmed] The music-to-video skill calls its librosa grid a metronome on calm music and insists it is the only analyzer. — SKILL.md line 22: 'analyze-beatgrid.py is the only beat analyzer — never re-measure beats with another tool… on calm music the grid is a metronome the tracker imposed'. (~/.claude/skills/music-to-video/SKILL.md)
- [confirmed] The bundled Pixabay SFX may be used commercially without attribution. — media-use/audio/assets/sfx holds 19 mp3 files (1.3 MB). Its CREDITS.md cites the Pixabay Content License ('free use for commercial and non-commercial purposes without attribution'). (~/.claude/skills/media-use/audio/assets/sfx/CREDITS.md)
- [confirmed] Murch's Rule of Six weights; No Film School raises rhythm to about 19% for non-narrative pieces. — The article lists 51/23/10/7/5/4 and says, for sizzle reels: 'take that combined 9% and add it to Rhythm… giving it 19%'. (https://nofilmschool.com/editing-emotion-using-walter-murchs-rule-six-non-narrative-content)
- [refuted] atempo works within 0.5-2 per instance; chain instances for more. — `-h filter=atempo` in the local 6.0 gives a tempo range of 0.5 to 100. atempo=4 runs as a single instance; 0.4 errors. Chaining is only needed below 0.5. (local ffmpeg 6.0)
- [refuted] vidstabtransform … optzoom=1:zoomspeed=0.25 controls the stabilization zoom. — The local help describes zoomspeed as 'for adative zoom', meaning it applies only with optzoom=2; with optzoom=1 it is ignored. smoothing already defaults to 15 in this build. (local `ffmpeg -h filter=vidstabtransform`)
- [uncertain] ITU-R BT.1359-1 detectability is +45 ms when sound is early and -125 ms when sound is late, which justifies cutting 0-1 frame early. — Not re-fetched in this session, because the web-search budget was exhausted. The values match the commonly cited BT.1359 figures. Applying lip-sync thresholds to cut-on-beat perception is an extrapolation; treat it as a heuristic, not a standard. (none fetched)
- [confirmed] torch 2.14.1 (2026-09-30) has macOS arm64 wheels for cp310-cp314 (about 127 MB); pyobjc-framework-Vision 12.2.2 is MIT; color-matcher is GPL-3.0. — torch: uploaded 2026-09-30; macosx_14_0_arm64 wheels for cp310-cp314 and cp314t, 127.2-127.7 MB.
pyobjc-framework-Vision 12.2.2: 2026-08-11, MIT, universal2 wheels for cp310-cp315.
color-matcher 0.6.0: 2025-03-30, GNU GPL v3.0. (https://pypi.org/pypi/torch/2.14.1/json ; https://pypi.org/pypi/pyobjc-framework-Vision/json ; https://pypi.org/pypi/color-matcher/json)

### Düzeltmeler (seçimlerin önüne geçer)

- **Beat/downbeat grid (Beat This!) installation**: Drop the `python3.13 -m venv ~/.venvs/beat && pip install beat-this` recipe.
- Use the existing workspace env: source ortam.sh, then run ortamlar/ses/bin/beat_this or File2Beats with TORCH_HOME=$MEDYA/modeller/torch. That env already has beat-this 1.1.0, torch 2.14.1, torchaudio 2.11.0 and soundfile, plus the final0/1/2 checkpoints.
- For any new env: `arac/uv pip install --python <env>/bin/python beat-this soundfile`, using uv-managed CPython 3.12.
- Or skip the file loader entirely: decode with ffmpeg to float32 mono and call beat_this.inference.Audio2Beats(signal, sr). — gerekçe: In torchaudio 2.9 and later, load() needs TorchCodec. beat-this then falls back to soundfile, which it does not declare as a dependency, so a clean install fails even on WAV (verified). The workspace convention is uv with Python 3.12 and caches inside the workspace, not ~/.venvs.
- **Beat-grid reliability gates**: For gate (a), check agreement between final0, final1 and final2 (already on disk, no download) plus an algorithmically independent tracker (librosa beat_track or plp), instead of downloading small0.
Add an explicit downbeat sanity gate: the share of beats flagged as downbeats should be close to 1/meter, and downbeat intervals should be 3-4 beats. If it fails, ignore the downbeats and derive bars from phrase and onset analysis.
Note that the CLI is CPU-only (--gpu means CUDA). On a 5-minute track, MPS gave no speedup over CPU's 5.7 s. — gerekçe: In a synthetic rubato test, beats were excellent (F = 0.964), but 338 of 367 beats were labelled downbeats.
- **FFmpeg syntax and capability notes**: State that -/filter_complex (and -/opt for any option) arrived in FFmpeg 7.0, not 7.1.
Add to 'missing locally': HEIC/HEIF and AVIF still-image decoding, also added in 7.0. Convert iPhone photos first with the built-in `sips -s format png in.heic --out out.png`, or read them with ImageIO/CoreImage in the Swift tool. — gerekçe: The FFmpeg Changelog puts both under 7.0. A local test shows 6.0 failing on HEIC.
- **Speed ramps and slowed diegetic audio**: Replace 'atempo 0.5-2 per instance' with 'atempo accepts 0.5-100 per instance; chain only below 0.5'. For large stretches of real audio, prefer muting, or rubberband if ffmpeg-full is adopted. — gerekçe: Help output and test from the local ffmpeg 6.0.
- **Stabilization card**: Either remove zoomspeed, or use `optzoom=2:zoomspeed=0.25` for adaptive zoom. To guarantee zoom ≤ 1.1, measure the implied zoom from the .trf or the output (cropdetect), or set optzoom=0 with an explicit zoom= value. — gerekçe: vidstabtransform's zoomspeed only applies when optzoom=2; with optzoom=1 it is ignored.
- **Swift 'retime'/'slomo' subcommand on VTFrameRateConversion**: - Call process(parameters:completionHandler:) wrapped in a continuation. Do not use the Swift `process(parameters:)` overload, which returns an AsyncThrowingStream and failed with -19740.
- Submit all fractional phases for one source pair in a single call.
- Use .sequential only for strictly consecutive pairs; use .random for anything else.
- Budget about 25 ms per interpolated 1080x1920 frame on the M2, plus 420v ↔ RGhA conversion.
- Treat super-resolution as needing an on-demand Apple model download (check configurationModelStatus). — gerekçe: Compiled test on this M2: the completion-handler path gave correct mid-frames (330.2/360.2/389.9 px against 330/360/390). Re-submitting the same pair in sequential mode extrapolated wrongly. The SDK headers document the super-resolution model download.
- **Optional FFmpeg upgrade path**: Spell out that:
- Both Homebrew fixes need sudo; DEVELOPER_DIR does not work, because brew clears the environment.
- ffmpeg-full is keg-only, so call /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg explicitly.
- libass is not a gain, since the local build already has it.
- The martin-riedl 9.0.2 zip is signed but only the installer is notarized, and vid.stab, rubberband and libplacebo are not listed. As a no-sudo side-by-side binary, keep the 6.0 build for vid.stab. — gerekçe: Checked the formula JSON, the vendor site, brew.sh and a local brew test.
- **HyperFrames verification tooling**: Delete 'animation-map.mjs is missing locally'. Use ~/.claude/skills/hyperframes-animation/scripts/animation-map.mjs, as SKILL.md documents. — gerekçe: The file exists (23,340 bytes, installed 2026-10-04).
- **Avoid list: essentia**: Narrow the entry. The trap is essentia's pretrained TF models, many of which are non-commercial. Running the AGPL code locally and unmodified does not restrict commercial use of the outputs. Flag that essentia 2.1b6.dev1389 is already installed in ortamlar/ses, and name which algorithms may be used for work output. — gerekçe: AGPL obligations attach to distributing the code or serving it over a network, not to media produced locally. The current wording overstates the risk, and the cross-domain install makes the distinction practical. Confidence is medium; this is a legal nuance.
- **Avoid list: video-use**: Reword the reason as 'requires an ElevenLabs account and API key (mandatory for transcription)' instead of 'paid key'. — gerekçe: The README makes the key mandatory. The accurate objection is the account requirement, which violates the no-accounts rule whatever the tier.

### Eksik bulunanlar

- Ingesting iPhone photos and media:
- HEIC/HEIF photos: the local ffmpeg 6.0 cannot decode them (verified); use the built-in `sips` or ImageIO.
- HDR gain-map photos.
- Live Photos' paired MOV clips, which are good 1.5-3 s micro-clips for montages.
- Metadata preservation: ask for originals via AirDrop or an export with all photo data, rather than WhatsApp copies, which recompress and (from general knowledge, not verified here) strip metadata, breaking chronological ordering.
- An editable-timeline export so the user can make final tweaks themselves. OpenTimelineIO 0.18.1 (Apache-2.0, released 2025-11-09, macOS arm64 wheels for cp39-cp313) could serve as the EDL format or an export target. Which NLEs import it (Kdenlive or Shotcut via MLT XML, Resolve via OTIO) was not verified.
- Upscaling low-resolution sources. The earlier source was 720x1280. On this M2, VTSuperResolutionScaler supports only 4x and may need an Apple model download. No pick or quality gate is defined, e.g. VT 4x then downscale with Lanczos, versus Real-ESRGAN (not verified).
- Word-level transcription for dialogue- or voice-over-driven cuts: product demos, J/L cuts on speech, trimming dead air. mlx-whisper 0.4.3 is already installed in ortamlar/ses but no card references it. auto-editor 29.3.1 (Unlicense, 2025-11-04) is an option for removing silence in screen-recording demos.
- Separating music from diegetic sound when phone clips have music or speech under them. demucs 4.1.0 is already installed in ortamlar/ses; its weights licence should be confirmed by the audio domain.
- Consistency with the existing workspace capability layer (the `medya` CLI and yetenekler.toml commands senkron, denetle, sdr, cfr, meta-temizle, sahneler).
- The cards define parallel scripts rather than extending these commands.
- The registry routes shot detection to PySceneDetect while the cards use ffmpeg scdet; pick one or document both thresholds.
- A real-footage benchmark of VTFrameRateConversion against minterpolate (leave-one-out SSIM/PSNR on hands, hair and water). Only a synthetic speed and accuracy test exists so far (about 25 ms per frame, ±0.3 px).
- Music-structure labels (verse/chorus) for pacing. I checked SongFormer (2025): its code is CC-BY-4.0, its weights licence is unspecified, it depends on MuQ/MusicFM and was tested on CUDA. It is not a fit, which leaves novelty analysis plus Beat This! downbeats (with the downbeat gate) as the practical approach.
