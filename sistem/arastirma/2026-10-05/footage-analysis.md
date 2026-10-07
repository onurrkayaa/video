# Çekim analizi — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Main finding: most of what this job needs is already built into macOS 27 on this M2. I checked it locally on 2026-10-05 by compiling small Swift test programs. They live in /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/probe/; frc_png.swift is a working PNG to Apple-interpolation to PNG tool you can build on. Results:
- Apple Vision on a warm 1080p frame: aesthetic score 13.8 ms, faces 16 ms, people 16 ms, face-capture quality 14.5 ms, lens smudge 14.7 ms, saliency 42 ms, scene labels 18 ms, image fingerprint (duplicates) 13 ms, foreground mask 25 ms.
- Apple SoundAnalysis: 303 sound classes, including laughter/giggling/belly_laugh, cheering, applause, speech, singing and music. It processed 60 s of audio in 0.36 s.
- Apple VideoToolbox frame-rate conversion (VTFrameRateConversion, slow-motion): supported, accepts sizes from 640x480 up to portrait 4K. 1080p takes about 42 ms per in-between frame, or about 54 ms per frame pair for 4x slow-mo. On a synthetic hold-out test it scored PSNR 29.6 dB, beating ffmpeg minterpolate at 28.7 dB.
- Apple motion blur and 4x super-resolution are supported. Super-resolution needs a one-time model download from Apple.
- Apple's temporal noise filter is NOT supported on this M2.
- Apple's SpeechTranscriber has no Turkish. DictationTranscriber does support Turkish.
Recommended additions, all small with permissive licenses:
- exiftool, for chronological order.
- PySceneDetect 0.7.1 with TransNetV2, for shot cuts.
- MediaPipe 1.0.1 face blendshapes, for smile and blink.
- SigLIP2-base (multilingual, so Turkish text queries work), for semantic search.
- whisper.cpp 1.9.4 with large-v3-turbo, DTW timing and VAD, for Turkish. hyperframes already falls back to this because Parakeet v3 has no Turkish.
- Depth Anything V2 Small as a Core ML model, for depth and parallax.
- ffmpeg vid.stab and denoise filters, already in arac/ffmpeg.
- Optional: Qwen3-VL-4B 4-bit through MLX for shot captions, and rife-ncnn-vulkan as a second slow-mo engine.
The core set adds about 3.5-4.5 GB; with the VLM about 7 GB. 22 GB is free now.
Blockers:
- Homebrew cannot run at all, even `brew info`, because the Xcode license has not been accepted. The user has to run `sudo xcodebuild -license accept`. Swift works only with DEVELOPER_DIR=/Library/Developer/CommandLineTools.
- uv is not installed.
Licenses: several popular choices are non-commercial and should not be used for work: pyiqa, DOVER, MobileCLIP, Depth Pro, FastVLM, Depth Anything Base/Large, MMS aligners, jina-clip-v2, RMBG-2.0. Ultralytics YOLO is AGPL.
Every step has a measurable check, such as PSNR/SSIM on held-out frames, word-onset agreement, shake RMS and how many frames keep the subject in the crop. This is because the assistant cannot listen to audio or watch video.

## Seçimler

### Runtime for the analysis: zero download, Neural Engine and GPU accelerated, scriptable by the agent (Vision, SoundAnalysis, VideoToolbox, Speech, AVFoundation, Core ML)
- **Seçim:** Own small Swift command-line tools, compiled with the installed Command Line Tools (Swift 6.4, MacOSX27.sdk): `DEVELOPER_DIR=/Library/Developer/CommandLineTools swiftc -O tool.swift -o $MEDYA/arac/tool`
- Alternatifler: PyObjC (MIT) from Python 3.14; the Rust objc2-video-toolbox bindings
- Neden: Checked 2026-10-05 on this M2 with macOS 27.0.1. Every Apple API recommended below compiled and ran through the Command Line Tools (DEVELOPER_DIR) override. Plain `swift` and every `brew` command fail, because xcode-select points at Xcode.app and its license was never accepted. What this gives: hardware HEVC/HDR decoding through AVAssetReader, on-device models with no downloads, JSON output, and no telemetry. It also avoids Python wheel problems. A compiled binary skips the 5-10 s just-in-time compile that `swift script.swift` pays on every run.
- Lisans: kod Apple OS frameworks, free to use on macOS; the tool code is your own · ağırlık Models ship inside macOS. VT super-resolution and Dictation language packs are downloaded from Apple on first use, with no account. · ticari: yes
- Apple Silicon: Native: Neural Engine, GPU and Media Engine decode
- Kurulum: Nothing to download. Add `export DEVELOPER_DIR=/Library/Developer/CommandLineTools` to ortam.sh. Optional one-time step by the user, needs the password: `sudo xcodebuild -license accept`, or `sudo xcode-select -s /Library/Developer/CommandLineTools`. This also unblocks Homebrew.
- Disk: ~0 MB · bakım: Ships with the OS. Vision aesthetics and smudge need macOS 15+, VTFrameProcessor 15.4+, VT super-resolution 26+. All verified on 27.0.1.
- Ajan kullanımı: Write one `footage-scan` tool. It takes a clip path and a sample rate, decodes frames with AVAssetReader at 2-4 fps, runs the Vision requests, writes one JSON line per sample, runs a SoundAnalysis pass on the audio track and dumps AVAsset metadata. Return a non-zero exit code on error. Python alternative: pyobjc-framework-Vision 12.2.2 (MIT, wheels for cp310-cp315) works for Vision and SoundAnalysis. Prefer Swift for VideoToolbox. Starting code: scratchpad/probe/bench2.swift and frc_png.swift.
- Güven: high · kaynaklar: https://developer.apple.com/documentation/videotoolbox/frame-processing, https://developer.apple.com/documentation/vision/calculateimageaestheticsscoresrequest, https://developer.apple.com/documentation/soundanalysis/classifying-sounds-in-an-audio-file, https://pypi.org/project/pyobjc-framework-Vision/

### Put clips in correct chronological order and read basic clip facts: capture time with timezone, GPS, device, frame rate, slow-motion intent, HDR, rotation
- **Seçim:** exiftool 13.55 (Homebrew), with the existing ffprobe 4.4 as a fallback that needs no install
- Alternatifler: macOS `mdls -name kMDItemContentCreationDate` (no timezone); AVFoundation metadata identifiers inside the Swift tool
- Neden: Phone clips store Keys:CreationDate as local time with its UTC offset. QuickTime CreateDate is UTC, and file times change on copy or AirDrop, so neither is reliable. Other useful keys: Keys:GPSCoordinates (ISO6709), Keys:Model, and Keys:FullFrameRatePlaybackIntent (iOS 18+, 0 means the clip is meant to play as slow motion). ffprobe shows the same keys as format tags (com.apple.quicktime.creationdate, com.apple.quicktime.location.ISO6709). It also shows r_frame_rate vs avg_frame_rate (variable frame rate, real 120/240 fps sources) and color_transfer=arib-std-b67 (HLG HDR). The last montage had no date order only because the input was a single pre-edited file. With the original clips, ordering is deterministic.
- Lisans: kod Artistic-1.0-Perl OR GPL-1.0-or-later · ağırlık n/a · ticari: yes
- Apple Silicon: Perl, so speed is not an issue; arm64 bottles exist for tahoe and golden_gate
- Kurulum: `brew install exiftool` once the Xcode license is accepted. Works now: `$MEDYA/arac/ffprobe -v error -show_entries format_tags:stream=codec_name,r_frame_rate,avg_frame_rate,color_transfer,color_primaries -of json clip.mov`
- Disk: ~30 MB · bakım: exiftool 13.55 is the current formula (checked 2026-10-05)
- Ajan kullanımı: Run `exiftool -j -n -G1 -api LargeFileSupport=1 -Keys:CreationDate -Keys:GPSCoordinates -Keys:Model -Keys:FullFrameRatePlaybackIntent -QuickTime:VideoFrameRate -QuickTime:Duration <dir> > meta.json`. Sort by CreationDate after parsing the offset. Start a new chapter on gaps over 2 h or GPS jumps over 1 km. Show the ordered table to the user before editing.
- Güven: high · kaynaklar: https://formulae.brew.sh/formula/exiftool, https://exiftool.org/forum/index.php?msg=90353

### Find shot cuts in multi-shot files, screen recordings and already-edited montages, including dissolves and fades
- **Seçim:** PySceneDetect 0.7.1 (`detect-adaptive`) as a fast first pass, plus TransNetV2 through transnetv2-pytorch 1.0.5 (weights included) for gradual transitions. ffmpeg `scdet` as the zero-install fallback.
- Alternatifler: ffmpeg `-vf scdet=threshold=10` (built in); AutoShot (CVPRW'23, about 1% better F1, no pip package, weights license unclear)
- Neden: PySceneDetect 0.7 (May 2026) reworked timestamps for variable-frame-rate video, which iPhone clips usually are. It can export cut lists as CSV, EDL, OTIO and FCPXML. TransNetV2 is still the standard learned cut detector (NVIDIA NeMo Curator used it in 2026). It catches dissolves and fades that colour-difference detectors miss; paper F1 is about 0.96 on BBC and 0.94 on RAI. Its weights are MIT and come in a 32.7 MB wheel. The package docs report numerical inconsistencies on MPS, so run it on CPU.
- Lisans: kod BSD-3-Clause (scenedetect); MIT (transnetv2-pytorch, upstream soCzech/TransNetV2) · ağırlık MIT, converted from the official TF SavedModel · ticari: yes
- Apple Silicon: CPU only. TransNetV2 works on 48x27 frames, so video decoding is the bottleneck. Estimate (not measured): 5-15x realtime at 1080p.
- Kurulum: In the workspace venv (uv, Python 3.12 recommended; torch 2.14.1 also ships cp314 arm64 wheels): `uv pip install --python $MEDYA/.venv 'scenedetect[pyav]' transnetv2-pytorch`. The torch wheel is 127 MB. If MediaPipe (which uses opencv-contrib-python) is in the same venv, install scenedetect with `--no-deps` plus click, platformdirs and tqdm.
- Disk: ~600 MB · bakım: scenedetect 0.7.1, 2026-07-22; transnetv2-pytorch 1.0.5, 2025-06-01
- Ajan kullanımı: CLI: `scenedetect -i in.mp4 -o out detect-adaptive list-scenes save-images -n 3 save-otio`. Python: TransNetV2 `predict_video` returns a cut probability per frame; threshold at 0.5. Merge the two sets of cuts that fall within ±3 frames. Write cuts.json in seconds, using timestamps (PTS), not frame indices.
- Güven: high · kaynaklar: https://pypi.org/project/scenedetect/, https://github.com/Breakthrough/PySceneDetect/releases, https://www.scenedetect.com/docs/0.7/cli.html, https://pypi.org/project/transnetv2-pytorch/, https://arxiv.org/abs/2008.04838, https://docs.nvidia.com/nemo/curator/latest/nemo-curator/nemo_curator/models/transnetv2

### Technical quality per frame and per shot: blur/sharpness, exposure, noise, black or frozen frames, motion energy, lens smudge
- **Seçim:** ffmpeg 6.0 filters already in arac/ffmpeg (blurdetect, signalstats, siti, freezedetect, blackdetect, mestimate), plus OpenCV 5.0 (Laplacian variance, Immerkaer noise sigma, shake), plus Apple Vision DetectLensSmudgeRequest
- Alternatifler: pyiqa (non-commercial, see avoid); Apple aesthetics score (next pick) for an overall quality signal
- Neden: All of these are local and return numbers per frame. I confirmed every filter is in the local build. Vision's lens-smudge request (macOS 15+) took 14.7 ms per 1080p frame on this M2 and targets the most common phone defect. These replace pyiqa and DOVER, which are non-commercial.
- Lisans: kod ffmpeg is used locally as a tool; the arac build is --enable-gpl --enable-nonfree, so never redistribute that binary. OpenCV: Apache-2.0. · ağırlık n/a; smudge model built into macOS · ticari: yes
- Apple Silicon: ffmpeg and OpenCV on CPU (NEON); Vision on Neural Engine
- Kurulum: Nothing for ffmpeg. `uv pip install opencv-python` (48 MB abi3 wheel, works on Python 3.14 too) or use the opencv-contrib-python that MediaPipe installs.
- Disk: ~150 MB · bakım: opencv-python 5.0.0.93, 2026-07-02
- Ajan kullanımı: Run `ffmpeg -i c.mov -vf "fps=4,scale=640:-2,blurdetect=block_width=32:block_height=32,signalstats,siti,metadata=print:file=q.txt" -f null -`. Parse lavfi.blur, YAVG/YLOW/YHIGH and SI/TI. Run separate passes with `freezedetect=n=0.003:d=1` and `blackdetect=d=0.2`. Convert each metric to a z-score within the footage set instead of using absolute thresholds.
- Güven: high · kaynaklar: https://ffmpeg.org/ffmpeg-filters.html, https://developer.apple.com/documentation/vision

### Aesthetic 'keeper' score, scene tags, near-duplicate detection and best-frame choice
- **Seçim:** Apple Vision: CalculateImageAestheticsScoresRequest (overallScore from -1 to 1, isUtility flag), ClassifyImageRequest (about 1.3k labels), GenerateImageFeaturePrintRequest (768-d fingerprint), DetectFaceCaptureQualityRequest
- Alternatifler: LAION improved-aesthetic-predictor (Apache-2.0 code, AVA-trained, needs ViT-L/14)
- Neden: No download. Measured warm per 1080p frame on this M2: aesthetics 13.8 ms, labels 18 ms, fingerprint 13.2 ms, face quality 14.5 ms. Apple's score already accounts for blur, exposure, colour balance, composition and subject. isUtility flags screenshots and documents. Face capture quality ranks frames of the same person, which is ideal for picking the best frame or take. Alternatives cost more: the LAION aesthetic predictor needs a 1.7 GB CLIP-L, and aesthetic-predictor-v2-5 is AGPL with a large SigLIP backbone.
- Lisans: kod Apple OS API · ağırlık Built into macOS · ticari: yes
- Apple Silicon: Neural Engine
- Kurulum: none
- Disk: ~0 MB · bakım: Aesthetics API is macOS 15+ (revision1 on 27.0.1)
- Ajan kullanımı: Inside footage-scan, sample at 2 fps and store per-shot median and max aesthetic. Best frame = argmax(aesthetic + faceQuality). Treat clips as duplicates when fingerprint distance is below a threshold; calibrate it on 10 known pairs first, roughly 0.3-0.5. Use the labels for grouping, such as beach/food/night/indoor.
- Güven: high · kaynaklar: https://developer.apple.com/documentation/vision/calculateimageaestheticsscoresrequest, https://createwithswift.com/scoring-the-aesthetics-of-an-image-with-the-vision-framework, https://github.com/christophschuhmann/improved-aesthetic-predictor

### Face and person detection, tracking and saliency to choose auto-reframe and punch-in targets
- **Seçim:** Apple Vision DetectFaceRectanglesRequest, DetectHumanRectanglesRequest (upperBodyOnly=false), GenerateAttentionBasedSaliencyImageRequest / ObjectnessBased, and TrackObjectRequest. Smooth the result with a One-Euro filter and turn it into GSAP keyframes.
- Alternatifler: YuNet 2026may ONNX (MIT, needs OpenCV 5); SAM 2.1 tiny (Apache-2.0, 156 MB PyTorch, or Apple Core ML build 80 MB, image-only) for masks of any subject; BiRefNet_lite (MIT, 178 MB) for clean mattes
- Neden: Built in, runs on the Neural Engine, no AGPL. Measured per warm 1080p frame: faces 16.4 ms, people 16.4 ms, saliency about 42 ms. That means analysing at 5-10 fps is faster than realtime. For specific objects such as a dog, cake or ring, use RF-DETR Nano (Apache-2.0, 30.5M parameters, ONNX 29-108 MB) through onnxruntime 1.30, which has cp314 wheels and the CoreML execution provider.
- Lisans: kod Apple OS API; RF-DETR Apache-2.0 for Nano to Large (XL and 2XL are PML-1.0, avoid); supervision MIT · ağırlık Built in; RF-DETR Nano/S/M/L Apache-2.0 · ticari: yes
- Apple Silicon: Neural Engine (Vision); onnxruntime CoreML or CPU execution provider
- Kurulum: none for Vision. Optional: `uv pip install onnxruntime supervision` plus onnx-community/rfdetr_nano-ONNX (int8, 29 MB).
- Disk: ~0 MB · bakım: supervision 0.30.7 and rfdetr 1.11.2 both released 2026-10-04; onnxruntime 1.30.0, 2026-09-10
- Ajan kullanımı: Run detection at 6 fps and track in between. Produce per-frame subject boxes, smooth them with One-Euro (min_cutoff about 0.5 Hz, beta about 0.01), limit pan speed and add ease. Emit {t,x,y,scale} keyframes for the hyperframes-keyframes skill. To find the main person across clips, cluster SFace embeddings (opencv_zoo, Apache-2.0) locally.
- Güven: high · kaynaklar: https://developer.apple.com/documentation/vision, https://github.com/roboflow/rf-detr, https://huggingface.co/onnx-community/rfdetr_nano-ONNX, https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet, https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface, https://huggingface.co/apple/coreml-sam2.1-tiny

### Smile, eyes-open and expression scores, to pick the best moments and avoid cutting on a blink
- **Seçim:** MediaPipe 1.0.1 Face Landmarker (Tasks API) blendshapes: mouthSmileLeft/Right, eyeBlinkLeft/Right, jawOpen, browInnerUp
- Alternatifler: CIDetector smile/blink (zero install, coarse); Apple Vision face landmarks plus geometry
- Neden: Code and models are Apache-2.0 (model cards for BlazeFace, FaceMesh-V2 and Blendshape V2). It returns 52 blendshape scores per face. The wheel is py3-none macOS arm64 (33.7 MB), so it works on any Python 3, including 3.14. The model file face_landmarker.task is 3.76 MB. Note that `mp.solutions` was removed in 0.10.31+; use `mediapipe.tasks.python.vision.FaceLandmarker` in VIDEO mode. Quick fallback built into macOS: CIDetector with CIDetectorSmile and CIDetectorEyeBlink (checked: available).
- Lisans: kod Apache-2.0 · ağırlık Apache-2.0 (Google model cards) · ticari: yes
- Apple Silicon: CPU (XNNPACK). Estimate (not measured): 5-15 ms per face.
- Kurulum: `uv pip install mediapipe` (also pulls opencv-contrib-python 154 MB and matplotlib). Get the model with `curl -L -o $MEDYA/modeller/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`
- Disk: ~350 MB · bakım: 1.0.0 released 2026-07-28, 1.0.1 on 2026-08-14 (active)
- Ajan kullanımı: Run on face crops from the Vision boxes at 6-10 fps. smile = mean(mouthSmileL, mouthSmileR); blink if eyeBlink > 0.5. Mark blink frames as forbidden cut points and use smile peaks as highlight candidates. For subtle emotions, describe them with a VLM or with Claude looking at the frames, not with emotion classifiers trained on AffectNet.
- Güven: high · kaynaklar: https://pypi.org/project/mediapipe/, https://github.com/google-ai-edge/mediapipe/releases, https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker, https://github.com/google-ai-edge/mediapipe/issues/6192

### Search frames by text, including Turkish queries, and cluster shots by meaning
- **Seçim:** SigLIP 2 base (google/siglip2-base-patch16-224, or the open_clip form `hf-hub:timm/ViT-B-16-SigLIP2`) on PyTorch MPS through open_clip-torch 3.3.0
- Alternatifler: OpenCLIP ViT-B-32 laion2B-s34B-b79K (MIT, 605 MB, English-only, faster); third-party Core ML conversions of SigLIP2; mlx-embeddings 0.1.0 (code is GPL-3.0)
- Neden: The weights are Apache-2.0. The text side is multilingual (the paper's title is 'Multilingual Vision-Language Encoders'), so a query like 'sahilde gün batımı' works without translating. The fp32 file is 1.5 GB (about 0.75 GB as fp16). open_clip is MIT, and torch 2.14.1 has macOS arm64 wheels for cp312 and cp314. MobileCLIP is smaller but research-only (apple-amlr).
- Lisans: kod MIT (open_clip); Apache-2.0 (transformers) · ağırlık Apache-2.0 · ticari: yes
- Apple Silicon: PyTorch MPS, fp16. Estimate (not measured): 30-80 images/s at batch 32 on M2.
- Kurulum: `uv pip install open_clip_torch torch torchvision`. The first load downloads to HF_HOME=$MEDYA/modeller/hf (already set in ortam.sh).
- Disk: ~1600 MB · bakım: open-clip-torch 3.3.0, 2026-02-27; SigLIP2 weights, 2025-02
- Ajan kullanımı: Embed the 1-2 fps samples of each shot and L2-normalise. Store as $MEDYA/analiz/emb.npy plus an index.json. Query: cosine similarity to the text embedding, keep the top 20, and Claude checks the contact sheet. Also cluster with k-means or HDBSCAN to build chapters.
- Güven: medium · kaynaklar: https://huggingface.co/google/siglip2-base-patch16-224, https://huggingface.co/timm/ViT-B-16-SigLIP2, https://pypi.org/project/open-clip-torch/, https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K

### Plain-language description of each shot (who, what, where, mood) to plan order and story
- **Seçim:** First choice: Claude looks at ffmpeg contact sheets itself (no install). For hundreds of clips, or offline: Qwen3-VL-4B-Instruct 4-bit MLX (mlx-community) through mlx-vlm 0.7.4.
- Alternatifler: moondream2 (Apache-2.0, 3.9 GB fp16, updated 2026-09); SmolVLM2 (Apache-2.0); Qwen3-VL-2B-4bit when disk is tight
- Neden: Claude can read PNG contact sheets with the Read tool, and its judgment is better than a small local model. A 4x3 grid costs about one image's worth of tokens. Qwen3-VL (Oct 2025, Apache-2.0) at 4-bit is 3.1 GB; the 2B version at 4-bit is 1.8 GB. Either fits in 16 GB RAM, and it describes in Turkish or English. mlx-vlm is MIT and actively maintained.
- Lisans: kod MIT (mlx-vlm) · ağırlık Apache-2.0 (Qwen3-VL 2B/4B/8B) · ticari: yes
- Apple Silicon: MLX on Metal. Estimate (not measured): 3-8 s per image caption on M2.
- Kurulum: Contact sheet: `ffmpeg -i clip.mov -vf "fps=1/2,scale=384:-2,tile=4x3:padding=4" -frames:v 1 sheet.png`. VLM: `uv pip install mlx-vlm`, then `python -m mlx_vlm.generate --model mlx-community/Qwen3-VL-4B-Instruct-4bit --image frame.jpg --prompt '...JSON...'`
- Disk: ~3200 MB · bakım: mlx-vlm 0.7.4, 2026-09-28; Qwen3-VL MLX weights, 2025-10
- Ajan kullanımı: Caption one representative frame per shot (best aesthetic) into JSON {people, action, place, time_of_day, mood}. Never send frames to cloud models.
- Güven: medium · kaynaklar: https://huggingface.co/mlx-community/Qwen3-VL-4B-Instruct-4bit, https://huggingface.co/mlx-community/Qwen3-VL-2B-Instruct-4bit, https://pypi.org/project/mlx-vlm/, https://huggingface.co/vikhyatk/moondream2

### Detect audio events: laughter, cheering, applause, speech, singing, music, crying
- **Seçim:** Apple SoundAnalysis built-in classifier (SNClassifySoundRequest with classifierIdentifier .version1)
- Alternatifler: YAMNet (521 AudioSet classes, Apache-2.0) through MediaPipe AudioClassifier with yamnet.tflite (4.1 MB, no TensorFlow needed). For free-text audio queries: LAION larger_clap_general (Apache-2.0, 776 MB) or MS-CLAP 2023 (MS-PL, 690 MB). PANNs CNN14 (code MIT, weights CC-BY-4.0, Core ML and MLX ports exist).
- Neden: Checked on this Mac: 303 classes, including laughter, giggling, belly_laugh, chuckle_chortle, snicker, baby_laughter, applause, cheering, crowd, speech, shout, whispering, singing, music, clapping, crying_sobbing, sigh, fireworks, sea_waves and silence. The window length can be set from 0.5 to 15 s. It analysed 60 s of audio in 0.36 s (about 170x realtime) with no download.
- Lisans: kod Apple OS API · ağırlık Built into macOS · ticari: yes
- Apple Silicon: Neural Engine / CPU
- Kurulum: none
- Disk: ~0 MB · bakım: OS framework (version1 classifier, macOS 12+)
- Ajan kullanımı: Use SNAudioFileAnalyzer on the extracted 16 kHz mono WAV with windowDuration 1.0 s and overlapFactor 0.5. Write JSON [{t, label, conf}], then merge consecutive windows with conf > 0.5 into events. Use speech regions to decide what to transcribe. Treat laughter and cheering as highlight markers.
- Güven: high · kaynaklar: https://developer.apple.com/documentation/soundanalysis/snclassifieridentifier, https://swiftjectivec.com/Sound-Analysis-Framework-Built-In-Model/, https://developers.google.com/edge/mediapipe/solutions/audio/audio_classifier, https://huggingface.co/laion/larger_clap_general, https://huggingface.co/microsoft/msclap

### Speech transcription with word timestamps, Turkish and English
- **Seçim:** whisper.cpp 1.9.4 (`brew install whisper.cpp`, Metal) with ggml-large-v3-turbo (1.6 GB; q8_0 874 MB or q5_0 574 MB), DTW token timestamps and Silero VAD. This is what `npx hyperframes transcribe clip.mov --language tr --model large-v3-turbo` runs.
- Alternatifler: mlx-whisper 0.4.3 (MIT; about 2x faster than whisper.cpp on turbo in a Jan-2026 benchmark; `mlx_whisper.transcribe(f, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', word_timestamps=True, language='tr')`). Apple DictationTranscriber: tr-TR is supported on this Mac, with .audioTimeRange timing, but the language pack downloads from Apple and quality is unverified. Qwen3-ASR-1.7B: Apache-2.0 and recognises Turkish, but its ForcedAligner has no Turkish timestamps. WhisperX with mpoyraz/wav2vec2-xls-r-300m-cv7-turkish (CC-BY-4.0) for forced alignment: CPU-only, needs Python below 3.14.
- Neden: hyperframes already calls whisper-cli with `--output-json-full --dtw <model> --suppress-nst`. It falls back to whisper for Turkish because Parakeet-TDT v3 covers only 25 European languages, and Turkish is not one of them. For reference, Whisper large-v3 has about 2.4% character error rate on FLEURS Turkish (BuzzASR card). VAD (ggml-silero-v6.2.0.bin, 0.89 MB, MIT) stops Whisper from inventing words over music or silence. hyperframes does not pass --vad, so call whisper-cli directly for clips with music. Code and weights are MIT.
- Lisans: kod MIT · ağırlık MIT (OpenAI Whisper; ggml conversions) · ticari: yes
- Apple Silicon: Metal through ggml (Core ML encoder optional when building from source). Estimate (not measured): 5-15x realtime on M2.
- Kurulum: After the Xcode license fix: `brew install whisper.cpp` (the formula was renamed from whisper-cpp). Models: `curl -L -o $MEDYA/modeller/ggml-large-v3-turbo-q8_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q8_0.bin`, plus ggml-silero-v6.2.0.bin from huggingface.co/ggml-org/whisper-vad.
- Disk: ~900 MB · bakım: whisper.cpp 1.9.4 (brew, Oct 2026); large-v3-turbo, 2024-10
- Ajan kullanımı: `whisper-cli -m ggml-large-v3-turbo-q8_0.bin -l tr -ojf --dtw large.v3.turbo -sow --vad -vm ggml-silero-v6.2.0.bin -of out audio16k.wav`. Merge tokens into words (as hyperframes does). Check timing with the word-timing technique below.
- Güven: high · kaynaklar: https://formulae.brew.sh/formula/whisper.cpp, https://huggingface.co/ggerganov/whisper.cpp, https://github.com/ggml-org/whisper.cpp/blob/master/examples/cli/README.md, https://huggingface.co/ggml-org/whisper-vad, https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3, https://huggingface.co/BuzzASR/turkish, https://notes.billmill.org/dev_blog/2026/01/updated_my_mlx_whisper_vs._whisper.cpp_benchmark.html, https://huggingface.co/Qwen/Qwen3-ASR-1.7B

### Depth from a single image, plus a subject mask, for 2.5D parallax and depth-aware zooms
- **Seçim:** Depth Anything V2 Small, Apple's Core ML build (apple/coreml-depth-anything-v2-small, F16 file 49.8 MB), run from Swift with VNCoreMLRequest, plus Vision GenerateForegroundInstanceMaskRequest for the subject
- Alternatifler: Video-Depth-Anything-Small (Apache-2.0, 116 MB, PyTorch, not tested on Mac); DA3-SMALL/BASE (Apache-2.0, 137/542 MB, Nov 2025, the install expects xformers, not tested on Mac); DA3MONO-LARGE (Apache-2.0)
- Neden: Only the Small size is Apache-2.0. Apple's model card gives 32.8 ms per frame on M1 Max and 24.6 ms on M3 Max (Neural Engine, 518x392). The foreground mask took 24.9 ms on this M2. No Python needed. The depth map and mask then drive a Three.js displacement or layered parallax in hyperframes.
- Lisans: kod Apache-2.0 · ağırlık Apache-2.0 (Small only) · ticari: yes
- Apple Silicon: Core ML on the Neural Engine
- Kurulum: `curl` the DepthAnythingV2SmallF16.mlpackage files from huggingface.co/apple/coreml-depth-anything-v2-small into $MEDYA/modeller and compile once with `xcrun coremlcompiler compile` (with the DEVELOPER_DIR override), or load them through MLModel.compileModel in Swift.
- Disk: ~50 MB · bakım: Core ML export 2024-06; model stable
- Ajan kullanımı: Swift tool: image or frame in, 16-bit depth PNG plus mask PNG out. For moving shots, prefer Video-Depth-Anything-Small for frames that stay consistent over time. Fill the background revealed by parallax with LaMa (Apache-2.0 ONNX, 208 MB) or OpenCV inpaint.
- Güven: high · kaynaklar: https://huggingface.co/apple/coreml-depth-anything-v2-small, https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf, https://github.com/DepthAnything/Video-Depth-Anything, https://github.com/ByteDance-Seed/Depth-Anything-3, https://huggingface.co/Carve/LaMa-ONNX

### Frame interpolation (optical flow) for slow motion and speed ramps
- **Seçim:** Apple VideoToolbox VTFrameRateConversion (VTFrameProcessor, macOS 15.4+), in a Swift tool of about 150 lines. Use native high-frame-rate footage first whenever it exists.
- Alternatifler: rife-ncnn-vulkan (MIT): nihui 20221029 macOS zip, 436 MB, models up to v4.6, MoltenVK bundled; TNTwise fork 20250112, 830 MB, adds v4.25 and v4.26. Estimate: 5-10 frames/s at 1080p on M2, based on SVP's note that M1 does 576p at 48 fps in realtime. rife-mlx: MIT, 23 MB, June 2026, very new, 554 ms per 1080p frame on M5 Max, too slow. ffmpeg minterpolate only for small motion.
- Neden: Checked on this M2: supported, and it accepts every size from 640x480 to portrait 4K. In quality mode, 1080p takes about 42 ms per frame pair for one in-between frame and about 54 ms for three (4x slow-mo). 4K takes about 141 and 181 ms. The first run spends about 10 s loading the model; after that it is cached (0.3 s). Held-out-frame test on synthetic 1080p (testsrc2, frame 5 rebuilt from frames 4 and 6): PSNR 29.6 dB and luma SSIM 0.974, vs 28.7 dB / 0.972 for ffmpeg minterpolate (mci, aobmc) and 24.6 dB / 0.953 for frame blending. No download and no licence question. It needs 64RGBAHalf ('RGhA') buffers, converted through CoreImage or VTPixelTransferSession. VTMotionBlur is also supported, which helps whip transitions.
- Lisans: kod Apple OS API · ağırlık Built into macOS · ticari: yes
- Apple Silicon: Neural Engine / GPU
- Kurulum: none. Starting point: scratchpad/probe/frc_png.swift (works: PNG pair in, interpolated PNG out). Extend it to AVAssetReader → AVAssetWriter.
- Disk: ~0 MB · bakım: OS API; WWDC25 session 300
- Ajan kullanımı: Tool: `slowmo in.mov out.mov --factor 4 --range 3.2-5.0`. Convert to constant frame rate first. Keep audio separate, since slow-mo audio is replaced by music. Check with the held-out-frame test before using it on a hero shot.
- Güven: medium · kaynaklar: https://developer.apple.com/documentation/videotoolbox/vtframerateconversionconfiguration, https://developer.apple.com/videos/play/wwdc2025/300/, https://github.com/nihui/rife-ncnn-vulkan/releases, https://github.com/TNTwise/rife-ncnn-vulkan, https://www.svp-team.com/wiki/RIFE_AI_interpolation, https://huggingface.co/mlx-community/RIFE-4.25, https://github.com/hzwer/Practical-RIFE

### Stabilization with a measured shake score
- **Seçim:** ffmpeg vid.stab in two passes (vidstabdetect, then vidstabtransform), already in arac/ffmpeg
- Alternatifler: Gyroflow CLI (with gyro logs); ffmpeg deshake (one pass, lower quality)
- Neden: Already present (libvidstab, GPL-2.0). It smooths the camera path over the whole clip, where deshake only removes jitter and leaves drift. tripod=1 gives a locked-off look. The transform data also yields a numeric shake score. Gyroflow 1.6.3 (GPL-3.0, 88.6 MB universal DMG, has a CLI) is better only when gyro logs exist, and the stock iPhone Camera does not record them; it needs an app such as Sensor Logger or GyroCam. Stabilization does not fix rolling-shutter wobble, and iPhone footage is already stabilized in-camera, so gate it on the shake score.
- Lisans: kod GPL-2.0-or-later (libvidstab), used as a tool; outputs are unaffected · ağırlık n/a · ticari: yes
- Apple Silicon: CPU. Estimate (not measured): 30-60 fps at 1080p.
- Kurulum: none
- Disk: ~0 MB · bakım: libvidstab 1.1.2 (stable)
- Ajan kullanımı: Pass 1: `-vf vidstabdetect=shakiness=6:accuracy=15:result=t.trf -f null -`. Pass 2: `-vf vidstabtransform=input=t.trf:smoothing=20:optzoom=1:zoomspeed=0.25:interpol=bicubic,unsharp=5:5:0.6`. Never put filters that change frame rate before pass 1 unless pass 2 has them too.
- Güven: high · kaynaklar: https://github.com/georgmartius/vid.stab, https://docs.gyroflow.xyz/app/advanced-usage/command-line-cli, https://github.com/gyroflow/gyroflow/releases

### Upscale old or low-resolution clips and photos
- **Seçim:** Apple VTSuperResolutionScaler (macOS 26+, separate video and image models). On this M2 it is supported only at scale 4 and needs a one-time model download from Apple (status was DownloadRequired). Fallback: Real-ESRGAN-ncnn-vulkan v0.2.5.0 macOS (51.8 MB).
- Alternatifler: realcugan-ncnn-vulkan (MIT, anime); Upscayl (AGPL app; some bundled community models are non-commercial)
- Neden: The Apple scaler is built in and runs on the Neural Engine and GPU. Real-ESRGAN code and models are BSD-3/MIT: realesrgan-x4plus for photos, realesr-animevideov3 for fast video and anime. realesrgan-x4plus makes faces look waxy. iPhone 4K rarely needs upscaling, so use this only for old or low-resolution clips.
- Lisans: kod Apple OS API; Real-ESRGAN BSD-3-Clause / ncnn-vulkan MIT · ağırlık Apple: built in, downloaded on demand. Real-ESRGAN models: BSD-3. · ticari: yes
- Apple Silicon: Apple Neural Engine/GPU; Real-ESRGAN through MoltenVK. Estimate (not measured): 1-3 s per 1080p frame at 4x.
- Kurulum: Apple: call `downloadConfigurationModel` only after the user agrees. Real-ESRGAN: download realesrgan-ncnn-vulkan-20220424-macos.zip from github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0 into $MEDYA/arac, then remove the quarantine flag with `xattr -dr com.apple.quarantine`.
- Disk: ~52 MB · bakım: Real-ESRGAN ncnn release 2022-04 (stable, not updated); Apple API macOS 26
- Ajan kullanımı: `realesrgan-ncnn-vulkan -i in_dir -o out_dir -n realesr-animevideov3 -s 2 -f png` on extracted frames, then re-encode. Compare face crops before and after.
- Güven: medium · kaynaklar: https://developer.apple.com/documentation/videotoolbox/vtsuperresolutionscalerconfiguration, https://github.com/xinntao/Real-ESRGAN/releases, https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan

### Denoise low-light phone footage
- **Seçim:** ffmpeg hqdn3d or atadenoise (fast, temporal) and nlmeans or bm3d (slow, higher quality), from the existing arac/ffmpeg
- Alternatifler: VapourSynth 80 with vapoursynth-bm3d/mvtools (brew; LGPL/MIT/GPL) when Homebrew works again
- Neden: Apple's VTTemporalNoiseFilter reports isSupported=false on this M2 (checked), so it is ruled out. The ffmpeg filters are present. Use a mild temporal setting, e.g. `hqdn3d=1.5:1.5:6:6` or `atadenoise`, then light sharpening with `cas=0.3`. Measure noise sigma before and after so you don't smear texture.
- Lisans: kod ffmpeg (GPL build, local use) · ağırlık n/a · ticari: yes
- Apple Silicon: CPU (nlmeans and bm3d are slow; use them only on short hero shots)
- Kurulum: none
- Disk: ~0 MB · bakım: n/a
- Ajan kullanımı: Denoise only shots whose Immerkaer sigma is above the 75th percentile of the footage set. Re-measure sigma and blurdetect afterwards, and reject the result if blur rises by more than 10%.
- Güven: medium · kaynaklar: https://ffmpeg.org/ffmpeg-filters.html, https://developer.apple.com/documentation/videotoolbox/vttemporalnoisefilterconfiguration

## Kaçınılacaklar

- **Ultralytics YOLO (v8/11/26) and YOLO-face derivatives** — AGPL-3.0 for both code and weights (PyPI 8.4.173). Commercial or closed use needs an Ultralytics Enterprise licence. Apple Vision or RF-DETR (Apache-2.0) cover the same needs.
- **pyiqa (IQA-PyTorch) and the metrics it bundles** — PolyForm-Noncommercial-1.0.0 plus NTU S-Lab licence (0.1.16, July 2026), so it cannot be used for work. Use ffmpeg metrics plus the Apple aesthetics score instead.
- **DOVER / FAST-VQA video quality models** — Ship an S-Lab licence (non-commercial). CUDA-centric and inactive since 2023.
- **MobileCLIP / MobileCLIP2, FastVLM, Apple Depth Pro, Apple DFN CLIP weights** — apple-amlr licence: 'Research Purposes' only, which excludes commercial use and product development. Use SigLIP2 or OpenCLIP LAION (MIT/Apache) and Depth Anything V2 Small instead.
- **Depth Anything V2 Base/Large/Giant, Video-Depth-Anything Base/Large, DA3 Large/Giant/Nested** — CC-BY-NC-4.0. Only the Small sizes (plus DA3-BASE, DA3METRIC-LARGE and DA3MONO-LARGE) are Apache-2.0.
- **aesthetic-predictor-v2-5 / LAION improved-aesthetic-predictor** — v2.5 is AGPL-3.0 and needs a large SigLIP backbone. LAION's needs a 1.7 GB CLIP ViT-L/14 and was trained on AVA, which has restrictive terms. Apple's built-in aesthetics score takes 13.8 ms with no download.
- **HSEmotion, FER/ViT emotion models, DeepFace emotion, InsightFace models, CodeFormer, GFPGAN** — Weights trained on AffectNet/FER2013 are research-only datasets despite 'Apache' code. InsightFace models are non-commercial, CodeFormer is S-Lab NC, and GFPGAN uses NVIDIA StyleGAN2 ops (NC). Use MediaPipe blendshapes or a VLM for expression.
- **MMS models / ctc-forced-aligner default model / torchaudio MMS_FA, SeamlessM4T** — CC-BY-NC-4.0 (checked: facebook/mms-300m, MahmoudAshraf/mms-300m-1130-forced-aligner). For Turkish alignment, use the CC-BY-4.0 mpoyraz wav2vec2 model or Whisper DTW.
- **jina-clip-v2, RMBG-2.0, moondream3-preview, Qwen2.5-VL-3B** — Non-commercial or restricted licences (CC-BY-NC-4.0 / 'other' / Qwen research licence).
- **Parakeet-TDT v3 (parakeet-mlx, sherpa) for Turkish** — Turkish is not among its 25 languages. hyperframes auto mode already falls back to whisper for tr. Never force `--engine parakeet --language tr`.
- **Apple SpeechTranscriber for Turkish** — Checked: tr is not in its 45 supported locales on macOS 27.0.1. Use whisper.cpp, or DictationTranscriber (which does list tr-TR) as an experiment.
- **TensorFlow-based tools on Python 3.14 (YAMNet via TF, FILM)** — TF 2.21 wheels stop at cp313. FILM is slow and has no Metal path. Use SoundAnalysis or MediaPipe YAMNet TFLite, and VT or RIFE for interpolation.
- **Practical-RIFE PyTorch and rife-mlx as the main slow-mo engine** — Practical-RIFE's README requires python<=3.11 and says nothing about MPS. rife-mlx (June 2026, 3 stars) takes 554 ms per 1080p frame even on M5 Max. Apple VT or rife-ncnn-vulkan are faster.
- **ffmpeg minterpolate for hero slow-mo shots** — Block-matching artifacts on occlusions, hands and hair, and it runs single-threaded. Use it only as a fallback for small motion; Apple VT already beat it on the held-out-frame test.
- **Gyroflow on stock iPhone Camera clips; ffmpeg deshake** — Gyroflow needs gyro data, which the stock app does not record. deshake removes jitter but leaves drift. Use two-pass vid.stab.
- **Apple VTTemporalNoiseFilter on this Mac** — isSupported=false on this M2 (checked).
- **Home-made numpy beat or onset trackers, and any audio sync step without a numeric check** — This caused the 'sesler kaymış' (audio slipped) failure. Every cut or sync must be checked by measured offsets, because the assistant cannot listen.
- **hyperframes snapshot with a Gemini key, and hyperframes cloud/lambda/cloudrun/publish/auth** — These send frames or projects off the machine, and personal footage must stay local.

## Teknikler

### One analysis file per clip before any editing
For each clip, the Swift footage-scan tool and one Python script write $MEDYA/analiz/<clip>.json. Fields: metadata (date with offset, GPS, fps, HDR, slow-mo intent); cuts; per-shot medians and maxima of aesthetic, sharpness, exposure, noise sigma, shake RMS and smudge; faces with smile/blink timelines; saliency boxes; scene labels; SoundAnalysis events; transcript words; and the index of its SigLIP2 embedding. Also write a 4x3 contact sheet PNG per shot. The editor reasons only from these files plus the contact sheets it views.

**Doğrulama:** Check every JSON file against a schema. Check that the shot durations add up to the clip duration within 1 frame. Pick 3 random shots and compare their contact sheets with the JSON labels.

### Chronological story order
Sort by Keys:CreationDate, interpreting its offset. Split into chapters on time gaps over 2 h or GPS jumps over 1 km. Inside a chapter keep time order, but allow small swaps when the 'energy' curve needs them: motion TI plus laughter and cheering events. Open with a calm, high-aesthetic establishing shot and close on the strongest smile or laughter moment.

**Doğrulama:** Print an ordered table (time, place, first frame thumbnail) and get the user's OK before cutting. Confirm dates only increase within chapters, and list clips with missing or duplicate dates.

### Shot scoring and selection
score = z(aesthetic) + z(sharpness) + 0.5·z(faceQuality) + smile and laughter bonuses − penalties (smudge > 0.5, black or frozen frames, shake RMS above the 80th percentile, isUtility). Pick the top shots per chapter. Drop near-duplicates using fingerprint or SigLIP2 cosine similarity above 0.92, keeping the higher score.

**Doğrulama:** Show Claude the selected and the rejected contact sheets side by side, and log why each was chosen. Results must stay the same across reruns.

### Cut points inside a shot
Each shot gets an in and out point. A calm cut goes at a local minimum of TI (motion); an action cut goes at a motion peak. Never cut on a blink frame (eyeBlink > 0.5) or in the middle of a laugh; extend 0.3 s past the end of the laughter event. Romantic pacing: minimum hold 1.5-2.5 s. Then snap the cut to the beat grid from the audio research.

**Doğrulama:** Extract the frames at each in and out point and check eyes are open and the subject is inside the frame. Report max |cut − nearest beat| and require it to be ≤ 1 frame (33 ms at 30 fps).

### Auto-reframe and punch-in keyframes
Vision face and person boxes at 6 fps, filled in with TrackObjectRequest; fall back to the attention-saliency box when nobody is found. Smooth with One-Euro, limit pan speed to 4% of width per second and zoom speed to 3% per second, then ease in and out. Emit hyperframes-keyframes {t,x,y,scale}. For 9:16, keep the face center in the upper third.

**Doğrulama:** Report: frames whose subject box lies fully inside the crop (target ≥ 98%), max crop velocity, and jerk (sum of squared second differences, compared before and after smoothing). Render a contact sheet of crops at 1 fps.

### Slow-motion decision tree and held-out-frame test
If r_frame_rate is 100 fps or more, or FullFrameRatePlaybackIntent is 0, slow down with setpts on the real frames (no synthesis). Otherwise use VT frame-rate conversion, then rife-ncnn-vulkan v4.25 as the second option. Convert to constant frame rate before interpolating. Slow down only 1-3 s around the moment of action.

**Doğrulama:** Take a 60 fps (or native) section, drop every other frame, rebuild the dropped frames and compare with the originals: ffmpeg psnr, plus ssim on format=gray. On synthetic 1080p, VT scored 29.6 dB / 0.974 vs minterpolate 28.7 / 0.972. Pick the engine with higher mean PSNR on the user's own footage, then view the 5 worst frames.

### Matching transitions by motion direction
Estimate the global motion (dx, dy, rotation, scale) of the last and first 0.5 s of each shot from vid.stab global_motions or OpenCV estimateAffinePartial2D, and classify it as pan left/right, tilt, push in/out or static. Pair shots that move the same way for whip or match cuts. Add Apple VTMotionBlur (supported here) or a GSAP blur only on the whip frames.

**Doğrulama:** Print the motion vector at each boundary. Require the direction cosine to be above 0.7 for every whip pair and less than 20% speed mismatch.

### Measured stabilization
Compute the camera path from feature tracking at 360p. Shake RMS = the RMS of (path − its Savitzky-Golay-smoothed path) in pixels per frame, divided by frame width. Stabilize only above a threshold, e.g. 0.004, using two-pass vid.stab with optzoom.

**Doğrulama:** Recompute shake RMS on the output: require at least 50% reduction, crop/zoom no more than 10%, and no new wobble (check the 2 worst frames visually).

### Turkish word-timing check (no listening needed)
Transcribe the speech regions with whisper.cpp large-v3-turbo using --dtw and VAD, and independently with mlx-whisper word_timestamps. Align the two word lists by text.

**Doğrulama:** Report median and 95th-percentile onset difference between the engines (target: median under 80 ms, 95th percentile under 200 ms). Every word onset should be within 120 ms of an RMS-energy rise. Render a waveform PNG with word boxes (showwavespic plus an overlay) and look at it.

### Normalize HDR and frame rate before analysis and editing
Detect HLG/PQ from color_transfer and Dolby Vision side data. Either tone-map everything once (zscale=t=linear,tonemap=hable,zscale=p=bt709:t=bt709:m=bt709) or keep the whole pipeline HDR. Convert VFR to constant frame rate with audio resampling.

**Doğrulama:** Run ffprobe on the normalized clips: one colour space and one fps for all. Compare audio vs video duration (at most 1 frame apart) and start_time of 0. Compare thumbnails of an HDR and an SDR clip side by side.


## Riskler

- Homebrew is blocked right now: every `brew` command, even `brew info`, fails with 'You have not agreed to the Xcode license', because xcode-select points at Xcode.app. Before any brew install (whisper.cpp, exiftool, uv), the user must run `sudo xcodebuild -license accept` once (needs the password), or `sudo xcode-select -s /Library/Developer/CommandLineTools`. Until then, Swift works only with DEVELOPER_DIR=/Library/Developer/CommandLineTools.
- uv is not installed (checked 2026-10-05), although ortam.sh expects it. Options: `brew install uv` after the licence fix, the official installer from astral.sh, or `python3 -m pip install --user uv`.
- python.org Python 3.14 here has no CA bundle for urllib (SSL CERTIFICATE_VERIFY_FAILED when I tried it). requests and huggingface_hub use certifi and are fine. For other HTTPS calls, use curl, or run 'Install Certificates.command' from /Applications/Python 3.14.
- Python version: torch 2.14.1, mlx 0.32.3, onnxruntime 1.30, opencv 5.0 (abi3), mediapipe 1.0.1 (py3-none) and numba 0.68 all ship cp314 arm64 wheels. TensorFlow (max cp313), coremltools 9.0 (max cp313) and whisperX (<3.14) do not, so a uv-managed 3.12 venv is the safe default.
- OpenCV conflict: mediapipe pulls in opencv-contrib-python while scenedetect pulls in opencv-python. Both provide cv2 and overwrite each other in one venv. Keep one provider and install scenedetect with --no-deps.
- The VT frame-rate conversion quality was measured only on synthetic content (testsrc2). Real footage with occlusions, hair and hands must pass the held-out-frame test and a look at the worst frames before use on hero shots.
- Apple assets downloaded on demand (the VT super-resolution model, the Turkish Dictation language pack) come from Apple servers. No account is needed, but ask the user first; their sizes are unknown.
- Variable frame rate: iPhone clips are usually VFR. Cutting by frame index, or mixing VFR clips in a constant-frame-rate render, makes audio and video drift. Convert to constant frame rate (`-fps_mode cfr -r 30`, `aresample=async=1`) and compare audio vs video stream duration and start_time; flag a gap over 1 frame. This might also have contributed to the earlier audio slipping. That is unverified, because the source file was deleted.
- HDR: iPhone records HLG/Dolby Vision (color_transfer=arib-std-b67). Analysis and grading on mixed HDR/SDR footage without one consistent tone-map (zscale→tonemap→bt709) gives a washed-out or clipped look, and it skews the exposure metrics.
- Datasets behind some 'permissive' weights (AVA, AffectNet, FER2013, AudioSet from YouTube) can carry research-only terms. For work deliverables, prefer the Apple built-ins and Google/Meta Apache-2.0 models with clean model cards.
- Whisper invents words over music and silence. Gate transcription with VAD or SoundAnalysis 'speech' regions. DTW word timestamps can be 100-300 ms off; refine cut points to the nearest energy dip.
- Apple Vision scores (aesthetics, face quality) are relative signals, not calibrated scores. Normalize them within each footage set, and confirm the top and bottom picks visually on contact sheets.
- rife-ncnn-vulkan has not been updated upstream since 2022. The macOS builds are unsigned (remove the quarantine flag), and an M1 issue reports 'decode image failed' on the first frames (use -j 1:2:2 and PNG input).
- The arac/ffmpeg static build has --enable-nonfree. It is fine to use locally but must never be redistributed. The local ffmpeg filter SSIM on rgb24 input gave misleading 'All' values (0.81 for identical frames); measure SSIM on luma (format=gray).
- Disk: 22 GB free now. The core set is about 3.5-4.5 GB, plus Qwen3-VL-4B at 3.1 GB, RIFE at 0.4-0.8 GB and CLAP at 0.8 GB. Keep all models under $MEDYA/modeller (HF_HOME is already set) so cleanup is easy.

## Açık sorular

- Which cameras will the footage come from: stock iPhone Camera, Android, GoPro or DJI? This decides which metadata keys exist, the HDR handling, and whether Gyroflow is worth it.
- Will the user run `sudo xcodebuild -license accept` once? Homebrew stays unusable until then (whisper.cpp, exiftool, uv).
- May macOS download Apple's on-demand assets: the VT super-resolution model and the Turkish Dictation language pack? Both come from Apple servers, no account.
- Is local face-identity clustering (SFace embeddings, never leaving the Mac) acceptable, so the editor can prefer shots of the partner automatically?
- Is it OK to spend about 3 GB of disk on the optional local VLM (Qwen3-VL-4B 4-bit)? The alternative is Claude viewing contact sheets, which costs more tokens per run.
- Does the user want an OTIO or FCPXML handoff (PySceneDetect save-otio, or a generated timeline) to make manual tweaks in DaVinci Resolve or Final Cut alongside the hyperframes render?

## Şüpheci doğrulama

Most of the findings hold up. I checked licences, versions and dates against the PyPI, Hugging Face and Homebrew APIs and GitHub, and the Apple API availability against the local macOS 27 SDK. I also compiled and ran my own Swift probes on this M2. They confirm that Vision, SoundAnalysis (303 classes), VT frame-rate conversion and motion blur work through the Command Line Tools with no download, that VT temporal noise filtering is unsupported, and that VT super-resolution supports only 4x.

The decision-relevant problems are below.

1. **The Turkish word-timing recipe is broken in whisper.cpp 1.9.4.** The default flash attention silently disables DTW. Issue #4046 (open) shows that `-ojf` with `--vad` leaves token times on the VAD-compressed timeline. Either one would cause the same 'audio slipping' failure. hyperframes transcribe reads t0/t1 offsets rather than t_dtw, and it routes Turkish to Whisper only when --language is passed.
2. **The cited probe tools do not exist.** bench2.swift and frc_png.swift are not in scratchpad/probe or anywhere else on disk.
3. **The quality advantage of VT interpolation was not reproduced.** In my held-out test minterpolate won on testsrc2 by about 2.4 dB and they tied on a zooming fractal. VT is about 10x faster.
4. **uv is installed.** It sits at arac/uv 0.12.23, with a uv-locked Python 3.12 venv. The OpenCV double-provider conflict the findings warn about already exists in that venv.
5. **The VLM pick is outdated.** Qwen3.5-4B is newer (Feb 2026), the same size, Apache-2.0, and supported by mlx-vlm 0.7.4.
6. **Smaller errors:**
   - coremlcompiler is not part of the Command Line Tools.
   - Lens smudge is macOS 26 and Swift-only.
   - The VT super-resolution video model is already Ready.
   - The 'SSIM 0.81' claim does not reproduce.
   - A few dates and sizes are wrong.

The Homebrew/Xcode-licence blocker is real and cannot be bypassed with DEVELOPER_DIR. Brew-free paths exist: exiftool on the system Perl, and mlx-whisper through uv. Confidence: high for the whisper.cpp and local findings (source code, an open issue, and runs on this Mac); medium for the pick recommendations.

My working probe and test files are in /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/fc/: frcpairs.swift, vb2.swift, vtprobe.swift, probe2.swift, probe3.swift, and the t1/ and t2/ test frames. I made no changes to project files.

### Kontroller

- [refuted] The Swift probe programs exist in scratchpad/probe/ (bench2.swift, frc_png.swift) and frc_png.swift is a working PNG to VT-interpolation to PNG tool to build on — Checked 2026-10-05. scratchpad/probe/ does not exist. find over /private/tmp and /private/var/folders, plus mdfind, found no frc_png* or bench2*. The only Swift file left from the researcher is scratchpad/sacheck.swift (the SoundAnalysis label probe). I built working replacements: scratchpad/fc/frcpairs.swift (VT frame-rate conversion, PNG pairs to PNG), vb2.swift (Vision timing), vtprobe.swift and probe3.swift (capability and model-status probes). (local: /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/)
- [confirmed] Homebrew cannot run at all, even brew info, because the Xcode license was not accepted. Swift works only with DEVELOPER_DIR=/Library/Developer/CommandLineTools — `brew info exiftool` fails with 'You have not agreed to the Xcode license' (Homebrew 7.0.1). Plain `swiftc --version` fails the same way. With the DEVELOPER_DIR override it reports Swift 6.4, target arm64-apple-macosx27.0. Exporting DEVELOPER_DIR does NOT unblock brew: the brew wrapper runs `env -i` with a filtered environment, then `/usr/bin/xcrun --find clang`. I tested this. (local: /opt/homebrew/bin/brew line 344; /opt/homebrew/Library/Homebrew/brew.sh lines 403-431)
- [refuted] uv is not installed (checked 2026-10-05) — uv 0.12.23 (built 2026-10-03) sits at $MEDYA/arac/uv, installed 2026-10-04 23:43. ortam.sh puts arac/ on PATH. A uv-managed CPython 3.12.15 venv already exists at $MEDYA/.venv, locked by uv.lock (requires-python ==3.12.*). It already contains scenedetect 0.7.1, opencv 5.0.0.93 and numpy 2.5.3. (local: /Users/onurkaya/Projects/video/arac/uv, ortam.sh, pyproject.toml, uv.lock)
- [confirmed] About 22 GB of disk is free — `df -h` shows 21 GiB available (about 22.5 GB) on /System/Volumes/Data. The brief says ~18 GB, so budget against the lower figure; renders will eat into it. (local df -h, 2026-10-05)
- [confirmed] exiftool 13.55 is the current Homebrew formula (Artistic-1.0-Perl OR GPL-1.0-or-later) with arm64 bottles for golden_gate and tahoe — The formula API gives stable 13.55, that licence, and bottles including arm64_golden_gate and arm64_tahoe. (https://formulae.brew.sh/api/formula/exiftool.json)
- [confirmed] whisper.cpp 1.9.4 is the brew formula (renamed from whisper-cpp), released Oct 2026 — Formula 'whisper.cpp' is 1.9.4 with oldnames ['whisper-cpp'], MIT, and depends on ggml, llama.cpp and sdl2-compat. One correction: the v1.9.4 GitHub release is dated 2026-09-10/11, not October. (https://formulae.brew.sh/api/formula/whisper.cpp.json; https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.4)
- [refuted] `whisper-cli -m ggml-large-v3-turbo-q8_0.bin -l tr -ojf --dtw large.v3.turbo -sow --vad -vm ggml-silero-v6.2.0.bin` gives DTW word timestamps on the original timeline — (1) In v1.9.4, examples/cli/cli.cpp sets `bool flash_attn = true` by default. src/whisper.cpp (whisper_init_with_params_no_state) then logs 'dtw_token_timestamps is not supported with flash_attn - disabling'. DTW is therefore silently off unless -nfa is passed. (2) Issue #4046 (open, Sept 2026): with --vad, the -ojf token timestamps stay on the VAD-compressed timeline while segment times are mapped back. The reporter measured drift of up to about 2 minutes on a 70-minute file, and t_dtw is affected too. The v1.9.4 cli still reads raw whisper_full_get_token_data. The fix, PR #4068, is still open. This is the same class of failure as the earlier audio slipping. (https://raw.githubusercontent.com/ggml-org/whisper.cpp/v1.9.4/src/whisper.cpp; .../v1.9.4/examples/cli/cli.cpp; https://github.com/ggml-org/whisper.cpp/issues/4046)
- [refuted] `npx hyperframes transcribe clip.mov --language tr --model large-v3-turbo` runs whisper-cli with --output-json-full --dtw --suppress-nst, and hyperframes auto mode falls back to whisper for Turkish — The flags are right: chunk-AOJIC4Z6.js passes them with no -nfa and no --vad, and ignores stdio. But the implication of DTW timing is wrong. DTW is disabled by the flash-attention default, and normalize-O76AC4HE.js builds words from token.offsets (t0/t1) and never reads t_dtw. The fallback to whisper needs an explicit --language: parakeetSpeaks() returns true when no language is given, so Parakeet would be chosen if installed. media-use's transcribe.mjs runs parakeet-mlx regardless of language. The default model is small.en. A quantized model name such as large-v3-turbo-q8_0 becomes the DTW preset 'large.v3.turbo.q8_0', which whisper-cli rejects. Parakeet is not installed today. (local: node_modules/hyperframes/dist/chunk-AOJIC4Z6.js, normalize-O76AC4HE.js, transcribe-3BUOOE6P.js, chunk-IQ3OUQ5Z.js, chunk-OAF4XJOW.js, skills/media-use/scripts/transcribe.mjs)
- [confirmed] Parakeet-TDT v3 has no Turkish; Qwen3-ASR recognises Turkish but Qwen3-ForcedAligner has no Turkish timestamps — Parakeet v3's HF language list has 25 languages and no tr (CC-BY-4.0). Qwen3-ASR-1.7B and 0.6B (Apache-2.0, 2026-01-28) list Turkish (tr). Qwen3-ForcedAligner-0.6B covers 11 languages: zh, en, yue, fr, de, it, ja, ko, pt, ru, es. (https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3; https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
- [confirmed] Whisper large-v3 has about 2.4% CER on FLEURS Turkish (BuzzASR card) — The card lists large-v3 zero-shot CER as 2.42 on FLEURS. BuzzASR/turkish itself (MIT, a whisper-large-v3 fine-tune, created 2026-09-08, 3.09 GB) reports 2.0 CER on FLEURS and 4.67 on Common Voice 25, against 5.15 for large-v3. (https://huggingface.co/BuzzASR/turkish)
- [confirmed] mlx-whisper is about 2x faster than whisper.cpp on turbo (Jan 2026 benchmark) and supports word_timestamps — Benchmark dated 2026-01-09: 13.1 s vs 26.7 s, hardware not stated. PyPI docs show transcribe(word_timestamps=True). Latest release is 0.4.3 from 2025-08-29, and it requires torch and numba. (https://notes.billmill.org/dev_blog/2026/01/updated_my_mlx_whisper_vs._whisper.cpp_benchmark.html; https://pypi.org/pypi/mlx-whisper/json)
- [confirmed] VTFrameRateConversion works on this M2 with 64RGBAHalf buffers, at about 42 ms per 1080p in-between frame, and needs no download — My probe reports isSupported=true and a source pixel format of 1380411457 ('RGhA'). frcpairs.swift, compiled with the CLT override, ran 6 pairs at 1080p in quality mode: median 45-51 ms per pair, first pair 0.16-0.18 s, startSession 0.25-0.34 s (model cached). The availability annotation is macos(15.4). (local: scratchpad/fc/frcpairs.swift, vtprobe.swift; SDK VTFrameProcessor_FrameRateConversion.h)
- [refuted] VT frame interpolation beats ffmpeg minterpolate on a held-out synthetic test (29.6 vs 28.7 dB PSNR) — Not reproduced. In my held-out test (even frames in, odd frames rebuilt, 1080p, Y-channel PSNR/SSIM), testsrc2 scored VT 29.8-31.3 dB (SSIM 0.946-0.960) against minterpolate (mci/aobmc/bidir/vsbmc) 32.5-33.9 dB (0.969-0.974). On a zooming mandelbrot the two tied: VT 31.3-31.8 dB vs MI 31.3-31.9 dB, with VT SSIM slightly higher (0.972-0.975 vs 0.969-0.972). Frame blending scored 26.8-28.3 dB. A pipeline round-trip sanity check gave inf dB. VT is about 10x faster: minterpolate took 4.1 s for 11 output frames, single-threaded. (local: scratchpad/fc/t1, t2, frcpairs.swift; arac/ffmpeg 6.0)
- [confirmed] VTMotionBlur is supported; VTTemporalNoiseFilter is not supported on this M2; VT super-resolution supports only scale 4 — Probe output: MotionBlur true, TemporalNoise false, SuperRes true with scale factors [4], OpticalFlow true. (local: scratchpad/fc/vtprobe.swift)
- [refuted] VT super-resolution needs a one-time model download (status DownloadRequired) — Only partly true. configurationModelStatus is 2 (Ready) for inputType .video at 960x540 and 1920x1080 at 4x. It is 0 (DownloadRequired) only for inputType .image. (local: scratchpad/fc/probe3.swift; SDK VTFrameProcessor_SuperResolutionScaler.h)
- [refuted] Vision lens smudge needs macOS 15+; PyObjC (pyobjc-framework-Vision 12.2.2) works for the Vision requests — The SDK swiftinterface marks DetectLensSmudgeRequest @available(macOS 26.0). VTTemporalNoiseFilter and VTSuperResolutionScaler are also macOS 26. Lens smudge has no VN* Objective-C header, so it is Swift-only and PyObjC cannot call it. Aesthetics, face quality and the foreground mask do have ObjC headers (VNCalculateImageAestheticsScoresRequest.h and the others). pyobjc-framework-Vision 12.2.2 (2026-08-11, MIT, cp310-cp315) is confirmed. (local SDK: Vision.swiftmodule/arm64e-apple-macos.swiftinterface line ~3099; Vision.framework/Headers)
- [confirmed] Apple Vision on a warm 1080p frame: aesthetics 13.8 ms, faces 16 ms, fingerprint 13 ms, smudge 14.7 ms, and so on, with no download — All requests ran through the CLT-compiled Swift with no download. My warm medians, using one handler so the image decode is cached: aesthetics 3.9 ms, faces 5.9, humans 5.8, featureprint 2.9 (768-d), attention saliency 3.4, foreground mask 16.4, lens smudge 4.0, face capture quality 3.1, classify 7.4 (1303 labels). The researcher's numbers are therefore conservative. On a fractal the aesthetics score was 0.81, which shows the scores are relative only. (local: scratchpad/fc/vb2.swift)
- [confirmed] SoundAnalysis built-in classifier has 303 classes including laughter, giggling, belly_laugh, cheering, applause, speech, singing, music and crying — Probe: 303 classes, and every listed label is present. (local: scratchpad/fc/vtprobe.swift)
- [confirmed] PySceneDetect 0.7.1 (2026-07-22, BSD-3) reworked VFR timestamps and exports OTIO/FCPXML/EDL — PyPI dates are 0.7 on 2026-05-03 and 0.7.1 on 2026-07-22. The release notes describe PTS-backed timestamps for VFR. The installed CLI offers save-otio, save-fcp, save-edl and save-qp. There is no TransNet detector, and opencv-python is a hard dependency. (https://pypi.org/pypi/scenedetect/json; https://github.com/Breakthrough/PySceneDetect/releases; local .venv/bin/scenedetect --help)
- [confirmed] transnetv2-pytorch 1.0.5 (2025-06-01) is MIT, a 32.7 MB wheel with weights included, and its docs warn about MPS inconsistency — PyPI confirms all of this. It also requires ffmpeg-python, pandas and torch. predict_video and detect_scenes exist, and the description warns of 'numerical inconsistency' on MPS. (https://pypi.org/pypi/transnetv2-pytorch/json)
- [confirmed] MediaPipe 1.0.1 (2026-08-14) is a py3-none macOS arm64 wheel (33.7 MB), Apache-2.0 code and models; mp.solutions was removed in 0.10.31+; face_landmarker.task is 3.76 MB — PyPI confirms the wheel, the licence, and the opencv-contrib-python, matplotlib and sounddevice dependencies. Issue #6192 confirms mp.solutions is missing in 0.10.31. HTTP HEAD gives 3,758,596 bytes for the model. The Blendshape V2 model card says 'Apache License, Version 2.0'. The card also warns of selfie-oriented limits: faces turned more than 80°, under 50% visible, or too small. The opencv-contrib arm64 wheel is 55.7 MB, not 154 MB. (https://pypi.org/pypi/mediapipe/json; https://github.com/google-ai-edge/mediapipe/issues/6192; Model Card Blendshape V2 PDF)
- [confirmed] OpenCV conflict: two cv2 providers in one venv overwrite each other — The conflict already exists. $MEDYA/.venv has both opencv_python-5.0.0.93 and opencv_python_headless-5.0.0.93 dist-info: scenedetect requires opencv-python, and the pyproject 'analiz' extra adds the headless build. mlx-vlm 0.7.4 also pulls in opencv-python, and mediapipe pulls opencv-contrib-python. (local: .venv/lib/python3.12/site-packages; pyproject.toml; PyPI requires_dist)
- [confirmed] SigLIP2-base is Apache-2.0 and multilingual, 1.5 GB fp32; open_clip 3.3.0 (2026-02-27) is MIT — google/siglip2-base-patch16-224: apache-2.0, model.safetensors 1500.8 MB, paper title 'SigLIP 2: Multilingual Vision-Language Encoders'. timm/ViT-B-16-SigLIP2 holds both a .bin and a .safetensors copy (3.0 GB together), so fetch only the safetensors. open-clip-torch 3.3.0 was uploaded 2026-02-27 under MIT. (https://huggingface.co/api/models/google/siglip2-base-patch16-224; https://pypi.org/pypi/open-clip-torch/json)
- [refuted] Qwen3-VL-4B 4-bit MLX (3.1 GB, Apache-2.0) through mlx-vlm 0.7.4 is the best small local VLM — The sizes and licences are right (3.11 GB, and 1.80 GB for 2B), but the pick is outdated. Qwen3.5-4B came out 2026-02-27 (Apache-2.0, natively multimodal, 201 languages, video input). Its card says it 'outperforms Qwen3-VL models across ... visual understanding benchmarks'. mlx-community/Qwen3.5-4B-4bit is 3.06 GB and Qwen3.5-2B-4bit is 1.75 GB. The mlx-vlm 0.7.4 wheel ships qwen3_5 support. Thinking mode is on by default and should be disabled. Gemma 4 E4B is Apache-2.0 but 5.2 GB as MLX 4-bit. Qwen3.6 exists only at 27B and 35B-A3B, too large for this Mac. (https://huggingface.co/Qwen/Qwen3.5-4B; HF API mlx-community/Qwen3.5-4B-4bit; mlx_vlm-0.7.4 wheel contents)
- [confirmed] Package versions and wheels: torch 2.14.1, mlx 0.32.3, onnxruntime 1.30.0, opencv 5.0.0.93 (abi3), numba 0.68 have cp314 arm64; TF 2.21 and coremltools 9.0 stop at cp313 — PyPI: torch 2.14.1 (2026-09-30, 127 MB wheels, cp310-314); mlx 0.32.3 (2026-09-29); onnxruntime 1.30.0 (2026-09-10, cp311-314); opencv-python 5.0.0.93 (2026-07-02); numba 0.68.0 (2026-09-30); tensorflow 2.21.0 (2026-03-06, max cp313); coremltools 9.0 (2025-11-10, max cp313). (https://pypi.org/pypi/<pkg>/json)
- [confirmed] rfdetr 1.11.2 and supervision 0.30.7 released 2026-10-04; RF-DETR N/S/M/L are Apache-2.0 and XL/2XL are PML-1.0; rfdetr_nano ONNX int8 is 29 MB — PyPI dates confirmed. The README licence table matches (Nano 30.5M params). The onnx-community repo has model_int8.onnx at 28.8 MB and fp32 at 108.1 MB. (https://raw.githubusercontent.com/roboflow/rf-detr/develop/README.md; HF API)
- [refuted] Depth Anything V2 Small Core ML (F16, 49.8 MB, Apache-2.0) can be compiled once with `xcrun coremlcompiler compile` using the DEVELOPER_DIR override — The model facts hold: apache-2.0, F16 weights 49.4 MB, and the card gives 32.8 ms on M1 Max and 24.58 ms on M3 Max at 518x396. The compile step does not: `DEVELOPER_DIR=/Library/Developer/CommandLineTools xcrun --find coremlcompiler` returns 'unable to find utility'. coremlcompiler ships only with Xcode.app, whose licence is unaccepted. (https://huggingface.co/apple/coreml-depth-anything-v2-small; local xcrun)
- [confirmed] Depth model licence split: only the Small sizes plus DA3-BASE, DA3METRIC-LARGE and DA3MONO-LARGE are Apache-2.0 — Apache-2.0: DA3-SMALL (137 MB), DA3-BASE (542 MB), DA3METRIC-LARGE, DA3MONO-LARGE, Video-Depth-Anything-Small (116 MB). CC-BY-NC-4.0: DA3-LARGE, DA3NESTED, VDA-Base, VDA-Large, DA-V2-Base. Caveat: mlx-community/Video-Depth-Anything-Small-MLX is tagged cc-by-nc-4.0 even though the upstream Small is Apache. (HF API model metadata)
- [confirmed] Interpolation and stabilization assets: rife-ncnn-vulkan nihui 20221029 macOS 436 MB; TNTwise 20250112 830 MB; Practical-RIFE python<=3.11; rife-mlx (RIFE-4.25) MIT 23 MB; Real-ESRGAN ncnn macOS 51.8 MB; Gyroflow 1.6.3 DMG 88.6 MB — Asset sizes by HTTP HEAD: 436.5 MB, 830.6 MB, 51.8 MB, 88.6 MB. The Practical-RIFE README says 'python <= 3.11'. mlx-community/RIFE-4.25 is MIT, 22.7 MB, created 2026-06-06. Gyroflow v1.6.3 assets are dated 2025-09-04 and there has been no release since. (GitHub releases expanded_assets; https://raw.githubusercontent.com/hzwer/Practical-RIFE/main/README.md)
- [confirmed] Avoid-list licences: pyiqa, DOVER, Ultralytics, apple-amlr models, aesthetic-predictor-v2-5, MMS aligners, jina-clip-v2, RMBG-2.0, Qwen2.5-VL-3B; LAION aesthetic is Apache-2.0 — pyiqa 0.1.16 (2026-07-08): PolyForm-Noncommercial-1.0.0. DOVER: S-Lab License 1.0, non-commercial. ultralytics 8.4.173: AGPL-3.0. MobileCLIP2-S0, FastVLM-0.5B, DepthPro: apple-amlr. aesthetic-predictor-v2-5: AGPL-3.0. mms-300m and the MahmoudAshraf aligner: cc-by-nc-4.0. jina-clip-v2: cc-by-nc-4.0. RMBG-2.0: bria-rmbg-2.0 licence and gated. Qwen2.5-VL-3B: qwen-research. improved-aesthetic-predictor LICENSE: Apache 2.0. mpoyraz Turkish wav2vec2: cc-by-4.0. (PyPI JSON; HF API; GitHub LICENSE files)
- [confirmed] Keys:FullFrameRatePlaybackIntent: 0 means the clip is meant to play as slow motion (iOS 18+) — The AVFoundation header says the value means full frame rate (1) or slow-motion rate (0), macOS 15 / iOS 18. It also notes that QuickTime Player and Photos play clips at 85 fps or higher in slow motion by default when the key is absent. (local SDK AVFoundation.framework/Headers/AVMetadataIdentifiers.h lines 155-159)
- [refuted] The local arac/ffmpeg filter SSIM on rgb24 gave 0.81 for identical frames — Identical testsrc2 rgb24 inputs give SSIM All 1.000000 and PSNR inf. Gray input also gives 1.0. Measuring on luma is still good practice. (local arac/ffmpeg 6.0)
- [confirmed] arac/ffmpeg 6.0 has vidstab, blurdetect, siti, freezedetect, blackdetect, mestimate, scdet, minterpolate, nlmeans, bm3d, hqdn3d, atadenoise, cas, zscale, tonemap; it is a GPL + nonfree build — All of these filters are present, plus libvmaf, xfade and lut3d. Configure line: --enable-gpl --enable-version3 --enable-nonfree. ffprobe is n4.4.1. Neither ffmpeg 6.0 nor ffprobe 4.4 can open HEIC ('moov atom not found'), whereas sips reads it. (local arac/ffmpeg -version / -filters)
- [uncertain] SpeechTranscriber has no Turkish while DictationTranscriber lists tr-TR on macOS 27.0.1 — Not re-run. Querying supportedLocales may contact Apple's asset catalog, and the probe code the researcher cited is missing. It does not matter for the pick, which is not Apple Speech. (n/a)
- [confirmed] hyperframes snapshot sends frames to Gemini when a key is set — snapshot runs '--describe' by default when GEMINI_API_KEY or GOOGLE_API_KEY is set. capture also uses OpenRouter, Gemini or Vertex keys if present. So the GOOGLE_API_KEY and OPENROUTER_API_KEY triggers need blocking too. (local: node_modules/hyperframes/dist/snapshot-F5ZSC5FM.js:675,780; capture-42GHDJSH.js:1024,3472)

### Düzeltmeler (seçimlerin önüne geçer)

- **Turkish and English transcription with word timestamps**: Use whisper-cli with DTW and no VAD: `whisper-cli -m ggml-large-v3-turbo-q8_0.bin -l tr -nfa --dtw large.v3.turbo -ojf -of out audio16k.wav`, then read each token's `t_dtw` (centiseconds), not `offsets`. Do not pass --vad when token times are needed, until PR #4068 is released. Instead gate speech externally: take SoundAnalysis 'speech' regions, cut WAV segments, transcribe each one, and add its start offset. Gate on two checks: stderr must show 'dtw = 1', and a test with 30 s of silence prepended must shift every token by 30.00±0.05 s. Alternatively make mlx-whisper (brew-free, word_timestamps=True, about 2x faster) the primary engine, with whisper.cpp as the cross-check. — gerekçe: In v1.9.4 the default flash attention silently disables DTW, and --vad leaves -ojf token times on the compressed timeline (issue #4046, still open). Both drift silently, which is the same failure as the audio slipping.
- **Transcription through hyperframes, for captions and cut timing**: Always pass `--language tr --model large-v3-turbo`, or use `--engine whisper`. Never pass a quantized model name, because the derived DTW preset is invalid. Treat hyperframes word times as legacy t0/t1 estimates and require the energy-onset check before cutting on them. If parakeet-mlx is ever installed, do not use media-use's transcribe.mjs for Turkish. — gerekçe: Without --language, hyperframes picks Parakeet when it is installed. Its default model is small.en. It reads offsets rather than t_dtw, and DTW is off anyway.
- **Python environment for analysis tools**: Update the risks: uv 0.12.23 is installed at $MEDYA/arac/uv. Install heavy stacks (torch, mediapipe, mlx-vlm, mlx-whisper) as isolated `arac/uv tool install` environments or separate venvs, as yetenekler.toml already specifies. Do not use `uv pip install --python $MEDYA/.venv`. — gerekçe: The project .venv is managed by uv.lock. `uv sync` (the documented install command) is exact by default and would remove packages installed ad hoc.
- **OpenCV in the project venv**: Fix it now. Remove `opencv-python-headless` from the pyproject 'analiz' extra, since scenedetect hard-requires opencv-python, or override one provider away. Keep mediapipe (opencv-contrib-python) and mlx-vlm (opencv-python) in their own environments. — gerekçe: Both opencv_python and opencv_python_headless 5.0.0.93 are already installed into one cv2 package. Removing either one breaks cv2.
- **Local VLM for shot captions**: Replace Qwen3-VL-4B-Instruct-4bit with mlx-community/Qwen3.5-4B-4bit (3.06 GB), or Qwen3.5-2B-4bit (1.75 GB) when disk is tight. Run it through mlx-vlm 0.7.4 with thinking disabled. Keep Claude reading contact sheets as the first choice. — gerekçe: It is the same size and licence but a newer generation (Feb 2026), its card says it beats Qwen3-VL on visual understanding, it supports 201 languages, and mlx-vlm already ships qwen3_5.
- **Slow-motion engine choice**: Keep VT frame-rate conversion as the fast default, but stop calling it better than minterpolate. Choose the engine per clip with the held-out-frame test, comparing VT, minterpolate (mci/aobmc/bidir/vsbmc) and rife-ncnn-vulkan. Use scratchpad/fc/frcpairs.swift as the starting tool, since frc_png.swift does not exist. — gerekçe: My 6-pair 1080p test did not reproduce the claimed gain: minterpolate won on testsrc2 by about 2.4 dB and they tied on a zooming fractal. VT is about 10x faster. Real footage with occlusions is still untested.
- **Core ML depth model setup**: Compile the .mlpackage at runtime with `MLModel.compileModel(at:)` inside the Swift tool, or use `xcrun coremlcompiler` only after `sudo xcodebuild -license accept`. — gerekçe: coremlcompiler is not part of the Command Line Tools.
- **Upscaling**: Note that the VT super-resolution video model is already Ready on this Mac. Only the image-input model needs Apple's on-demand download, and that still needs the user's consent. — gerekçe: The probe returned configurationModelStatus 2 for video and 0 for image.
- **Lens-smudge and Vision via Python**: Mark DetectLensSmudgeRequest as macOS 26+ and Swift-only. Keep all Vision calls in the Swift footage-scan tool; PyObjC is only a partial fallback. In Swift tools, compile with `-swift-version 5` for simple scripts, and never pass a Swift String to a %s format, which crashes. — gerekçe: The SDK annotation is macOS 26.0 and there is no VN* ObjC header. I hit both Swift pitfalls while building the probes.
- **Chronological metadata while Homebrew is blocked**: Run the official Image-ExifTool 13.55 tarball with the system /usr/bin/perl 5.34.1 until the Xcode licence is accepted. Exporting DEVELOPER_DIR does not unblock brew. — gerekçe: brew filters its environment and fails on the licence check. Perl is already present.
- **Slow-motion intent detection**: In the decision tree, treat the clip as slow motion when the source is 85 fps or more and FullFrameRatePlaybackIntent is absent, or when the key equals 0. Use 85 fps, not 100. — gerekçe: Apple's header says Photos and QuickTime play clips at 85 fps or higher in slow motion by default.
- **Smile and blink scores**: Run MediaPipe on upscaled face crops of at least 256 px, and only for near-frontal faces. For small or turned faces, fall back to CIDetector or Vision landmarks. Report the share of frames where blendshapes were valid. — gerekçe: The Blendshape V2 model card says it is selfie-oriented and degrades for faces turned more than 80°, under 50% visible, or distant.
- **Licence hygiene for converted weights**: Check the licence of the exact repository downloaded, not only the upstream model, and record both in yetenekler.toml. — gerekçe: mlx-community/Video-Depth-Anything-Small-MLX is tagged CC-BY-NC-4.0 although the upstream Small is Apache-2.0, and mlx-community/gemma-4-E4B-it-4bit is tagged 'gemma' although upstream is Apache-2.0.
- **Disk budget for Whisper models**: Use a single copy of large-v3-turbo. hyperframes downloads the full 1.62 GB ggml-large-v3-turbo.bin into ~/.cache/hyperframes/whisper/models, outside $MEDYA/modeller. Either symlink one location to the other or let a single tool own the model. — gerekçe: Downloading q8_0 into modeller as well wastes about 0.9-1.6 GB of only ~21 GB free.
- **Minor factual fixes**: whisper.cpp 1.9.4 was released 2026-09-10/11. Gyroflow 1.6.3 was released 2025-09-04. The opencv-contrib arm64 wheel is 55.7 MB. Drop the 'SSIM 0.81 on identical rgb24' risk. Add GOOGLE_API_KEY and OPENROUTER_API_KEY to the hyperframes leak triggers. — gerekçe: Verified against GitHub, PyPI and the local code.

### Eksik bulunanlar

- Importing from the Apple Photos library: originals, Live Photos, slo-mo ramps, favorites and Photos' own person and score data. Options are Photos' 'Export Unmodified Originals', a PhotoKit Swift exporter, or osxphotos 0.77.2 (MIT, 2026-09-27; tested only to macOS 15.7, partial on 26.x, untested on 27; needs Full Disk Access).
- HEIC and Live Photo stills: arac/ffmpeg 6.0 and ffprobe 4.4 cannot open HEIC. Use the built-in sips, CoreImage or Vision ImageRequestHandler.
- Built-in motion estimation for whip and match cuts: VTOpticalFlow (verified supported on this M2) and Vision TrackOpticalFlowRequest, both zero-install, before reaching for OpenCV.
- Vision DetectHumanBodyPoseRequest (2D and 3D) to find action peaks (jumps, spins, hugs) as cut points.
- Vision RecognizeTextRequest OCR, which covers 33 languages including Turkish (verified locally): for screen recordings and product demos, to choose zoom targets and avoid cropping on-screen text.
- VMAF (libvmaf is already in arac/ffmpeg) as a perceptual check for interpolation, upscaling and encodes, alongside PSNR/SSIM.
- Speaker diarization for interviews and demos: sherpa-onnx 1.13.8 (Apache-2.0, arm64 wheels cp310-314, models from its GitHub releases). Avoid pyannote's Hugging Face models, which are gated and need an account.
- Brew-free ASR paths: mlx-whisper through uv; pywhispercpp 1.5.1 (MIT, arm64 wheels cp310-315, Metal and DTW support unverified); or the PyPI cmake 4.4.4 package plus DEVELOPER_DIR so hyperframes can build whisper.cpp from source.
- Qwen3-VL-Embedding-2B (Apache-2.0, Jan 2026; MLX 8-bit 2.66 GB or mxfp4 1.74 GB; supported by mlx-vlm 0.7.4) as a Turkish-strong alternative to SigLIP2 for image and video search. Also add MetaCLIP 2 (CC-BY-NC-4.0) to the avoid list.
- Turkish-specialized ASR: BuzzASR/turkish (MIT, Sept 2026, 2.0% FLEURS CER vs 2.42 for large-v3, 3.1 GB). It needs conversion to ggml or MLX, and its DTW alignment heads after fine-tuning are unverified.
- An Apache-2.0 Turkish CTC aligner option: facebook/omniASR-CTC-300M (1.3 GB, fairseq2, needs libsndfile). The macOS install path is unverified.
- Avoid-list additions: SAM 3 and SAM 3.1 (Hugging Face gated with manual approval, so an account is required; custom licence). Treat mlx-community conversions as separately licensed.
- A standing regression test against audio slipping: prepend 30 s of silence and check the token-time shift; require every token to fall inside its segment; require t_dtw ≠ -1; compare video and audio stream start_time and duration after conversion to constant frame rate.
- CinematicVideoIntent metadata (macOS 26) and the Cinematic-mode depth and focus tracks, for depth-aware reframing of iPhone Cinematic clips (minor).
