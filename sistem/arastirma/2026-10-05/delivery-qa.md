# Teslim ve kalite denetimi — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Everything for delivery and QC can run locally today with the workspace's bundled ffmpeg 6.0 (/Users/onurkaya/Projects/video/arac/ffmpeg). I checked it on this M2 on 2026-10-05. It has zscale and tonemap, libvmaf with the built-in vmaf_v0.6.1 and neg models and the phone transform, x264, x265, SVT-AV1, h264, hevc and prores_videotoolbox, aac_at, and these filters: scdet, freezedetect, blackdetect, silencedetect, ebur128 true-peak, astats, signalstats, vfrdet, mpdecimate, photosensitivity and aphasemeter. The bundled ffprobe 4.4.1 is old but works, including its lavfi movie source. The macOS built-ins avconvert and avmediainfo and the existing .venv (Python 3.12, PySceneDetect 0.7.1, numpy, OpenCV 5.0) cover the rest. Homebrew is currently unusable: every brew command fails because the Xcode license has not been accepted, and the user has to run sudo to fix that. Homebrew's slim ffmpeg 9.0.2 has no zimg, so it would be a step backwards for HDR work. Only ffmpeg-full 9.0.2 adds libplacebo and zimg.

Key findings:
1. HyperFrames' default HDR mode is 'auto'. Any HLG or PQ video or image in a project silently turns the whole MP4 into BT.2020 10-bit HEVC (Main10). Its --sdr path tone-maps with zscale npl=100 and hable.
2. I measured operators on a synthetic HLG grey ramp, where 75% HLG is reference white; numbers are 8-bit Y. hable puts reference white at Y 182 (darker midtones). mobius puts it at 218 and reinhard at 209. Apple avconvert's H.264 preset put it at 148. Retagging without a tone map clipped at 255. ITU-R BT.2408-7 maps SDR 100% to HLG 75% and keeps midtones when down-mapping, so mobius is the closest default. Pre-convert iPhone clips to SDR BT.709 CFR yourself and always render with --sdr. Let the user pick the look once from a side-by-side sheet.
3. avconvert's H.264 presets convert HLG to BT.709 SDR and its HEVC presets keep HLG, matching WWDC20. Its default metadata filter, even with PresetPassthrough (no re-encode), removed ISO6709 location, make, model and creation date.
4. Re-encode the HyperFrames master for each destination. The master uses -bf 0, carries provenance tags, and CRF 16 reached 74 Mb/s on grainy footage. Presets are exact; for example, vertical is 1080x1920 30p H.264 High@4.2, CRF 17 capped at 20 Mb/s, GOP 15, AAC 48 kHz, -14 LUFS / -1 dBTP or lower, faststart, metadata stripped.
5. A QC conformance check caught a real pitfall: scaling 16:9 straight to 1080x1920 silently produced SAR 256:81.
6. The earlier 'audio slipping' problem is now measurable:
   - A flash-plus-beep slate measured a planted +40 ms offset as exactly +40.0 ms.
   - FFT cross-correlation of the song inside the render gives offset and drift: 0.00 ms when correct, -2.25 to -9.25 ms with a 0.05% speed error.
   - Cut-versus-beat residuals are checked against ±1 frame.
   - astats Max_difference finds clicks at edit points: 334 when clean, 11,919 at a hard cut.
7. A WCAG 2.3.1 flash counter is validated: 5 Hz fails, 3 Hz passes, a single flash passes. Its script and the drift script are in the scratchpad; copy them into the workspace to keep them.
8. Encoder speed and quality, measured on hard synthetic 1080p grain:
   - At about 4 Mb/s, VMAF was x265 medium 49.8, x264 slow 47.0, VideoToolbox HEVC 44.9, VideoToolbox H.264 41.1.
   - At about 20 Mb/s, VideoToolbox -q:v 65 scored 63.2 and x264 CRF 18 scored 64.2.
   - VideoToolbox ran at 88-105 fps versus 20 fps for x264 slow.
   - Use VideoToolbox for high-bitrate, fast copies and x264/x265 when file size is capped.
9. Archive: the M2's ProRes engine does 4K HQ about 9x faster than prores_ks. But 1080p30 HQ is 99 GB/h and 4K30 HQ is 398 GB/h, so with about 18 GB free the archive should be: camera originals, the composition source, and a CRF 14-16 master. Use ProRes only for hand-off to another editor or on an external disk.

## Seçimler

### Transcode + automated QC engine usable right now (tone mapping, VMAF, VideoToolbox, ProRes, loudness, all detectors)
- **Seçim:** Bundled ffmpeg 6.0 (npm ffmpeg-static 5.3.0) + ffprobe 4.4.1 (@ffprobe-installer) at /Users/onurkaya/Projects/video/arac/
- Alternatifler: Homebrew ffmpeg-full 9.0.2 (next pick), after the Xcode license is fixed
- Neden: Checked on this M2 (2026-10-05). The build has --enable-libzimg (zscale), tonemap, --enable-libvmaf (vmaf_v0.6.1 / vmaf_v0.6.1neg built in; phone transform via model string), libx264/libx265/libsvtav1, h264/hevc/prores_videotoolbox, aac_at (Apple AudioToolbox AAC, max 320 kb/s stereo), scdet, freezedetect, blackdetect, silencedetect, ebur128 true-peak, loudnorm, astats, signalstats, idet, vfrdet, mpdecimate, ssim/psnr/msad, photosensitivity, aphasemeter, vidstab, xfade, minterpolate and lut3d. Every QC command in this report was run with it against synthetic files with planted defects. It lacks scale_vt (6.1+), libplacebo, xpsnr, colordetect (8.0), the Dolby Vision bitstream filters and APAC decoding. ffprobe 4.4.1 quirks: rotation is in side_data_list 'Display Matrix' or tags.rotate; keyframe times come from packet=pts_time,flags because frame=pts_time is empty in 4.4; 'movie=' lavfi works.
- Lisans: kod GPL-3.0-or-later build, also configured with --enable-nonfree: fine to use locally, do not redistribute the binary. Outputs are not GPL-encumbered. · ağırlık - · ticari: yes
- Apple Silicon: Native arm64. VideoToolbox hardware H.264/HEVC/ProRes encode and decode on the M2 media engine: ProRes HQ 4K, 90 frames in 0.71 s versus 6.58 s with prores_ks. -q:v constant quality works only on Apple Silicon (kVTCompressionPropertyKey_Quality = q/100, not for ProRes). Encode speed on 1080p: VideoToolbox H.264 88 fps, HEVC 105 fps, x264 slow 20 fps, x264 medium 29 fps, x265 medium 17 fps.
- Kurulum: Already installed: source /Users/onurkaya/Projects/video/ortam.sh (puts arac/ on PATH: arac/ffmpeg -> node_modules/ffmpeg-static/ffmpeg, arac/ffprobe -> @ffprobe-installer/darwin-arm64/ffprobe)
- Disk: ~0 MB · bakım: FFmpeg 6.0 dates from Feb 2023. Upstream is now 9.0 'Lei' (released 2026-08-04) and Homebrew ships 9.0.2. 6.0 is sufficient for everything here.
- Ajan kullanımı: Pure CLI. Parse stderr summary lines (black_start, lavfi.freezedetect.*, lavfi.scd.time, silence_*, ebur128 Summary I/LRA/Peak) or per-frame metadata=mode=print:file=- on stdout; ffprobe -of json for conformance. Always pass -nostdin inside loops.
- Güven: high · kaynaklar: https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog, https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavcodec/videotoolboxenc.c, https://github.com/eugeneware/ffmpeg-static, https://9to5linux.com/ffmpeg-9-0-lei-open-source-multimedia-framework-officially-released, local: /Users/onurkaya/Projects/video/node_modules/ffmpeg-static/ffmpeg -buildconf / -filters / -encoders (2026-10-05)

### HDR (iPhone HLG / Dolby Vision 8.4, 10-bit HEVC) to SDR BT.709 conversion with a controlled look
- **Seçim:** ffmpeg zscale -> linear -> tonemap=mobius:desat=0 -> BT.709 tv range, with explicit tags (bundled ffmpeg). Use hable only for a deliberately darker, filmic look.
- Alternatifler: - avconvert (Apple look; next pick)
- libplacebo (tonemapping=bt.2390 / bt.2446a / spline, gamut_mode=perceptual, apply_dolbyvision) via ffmpeg-full + molten-vk (unverified on macOS 27)
- scale_vt color_transfer=bt709 (VTPixelTransferSession; needs FFmpeg 6.1+)
- Neden: Measured on a synthetic HLG grey ramp. Inputs are HLG signal at 25 / 50 / 75 (reference white) / 90 / 100%; outputs are 8-bit Y:
- mobius: 99 / 175 / 218 / 231 / 235
- reinhard: 99 / 161 / 209 / 228 / 235
- hable: 72 / 123 / 182 / 217 / 235. This is exactly HyperFrames' built-in --sdr chain: zscale=t=linear:npl=100, tonemap=hable:desat=0.
- Apple avconvert: 63 / 100 / 148 / 194 / 234
- transfer retag with no tone map: 99 / 181 / 255 / 255 / 255 (clipped, illegal)

ITU-R BT.2408-7 maps SDR 100% to HLG 75% (203 cd/m2). Its display-light down-mapping keeps lowlights and midtones and compresses highlights into the top of the SDR range. That favours mobius or reinhard; hable gives 'darker midtones'. With no MaxCLL or mastering metadata, FFmpeg's tonemap assumes an HLG peak of 10 x 100 cd/m2 (ff_determine_signal_peak). iPhone DV 8.4 decodes as its HLG base layer (RPU ignored), which is the correct input here.

Speed on M2: 4K, 90 frames in 3.9 s; scaling to 1080 before linearizing takes 1.55 s. With -hwaccel videotoolbox decoding, autorotation still works.
- Lisans: kod FFmpeg GPL build; zimg WTFPL · ağırlık - · ticari: yes
- Apple Silicon: CPU float path (NEON). Hardware decode via -hwaccel videotoolbox. Not GPU tone mapping.
- Kurulum: none (bundled ffmpeg)
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: Fixed filter string per clip; verify tags with ffprobe and highlight clipping with signalstats (QC5).
- Güven: medium · kaynaklar: https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2408-7-2023-PDF-E.pdf, https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/colorspace.c, https://dev.to/masonwritescode/ffmpeg-hdr-to-sdr-tone-mapping-that-doesnt-look-washed-out-2026-24ie, https://libplacebo.org/options/, https://ffmpeg.org/pipermail/ffmpeg-devel/2023-July/312189.html, local: /Users/onurkaya/Projects/video/node_modules/hyperframes/dist/chunk-LVXNXV7G.js (hdrToSdrToneMapFilter)

### Apple-native HDR->SDR export and zero-re-encode privacy stripping (built in, no install)
- **Seçim:** avconvert (/usr/bin/avconvert, macOS built-in)
- Alternatifler: ffmpeg tone map (previous pick) for full control
- Neden: Checked locally:
- H.264 presets (PresetHighestQuality, Preset1920x1080...) turned an HLG HEVC Main10 file into H.264 High with bt709/bt709/bt709 tags.
- PresetHEVCHighestQuality kept HLG (bt2020/arib-std-b67), matching WWDC20 session 10010: 'HEVC and Apple ProRes presets preserve HDR... to convert from HDR to SDR use the H.264 presets'.
- The default metadata filter removed ISO6709 location, make, model and creationdate, including with PresetPassthrough (remux, no re-encode). --disableMetadataFilter keeps them.

Limits: preset-only, so no CRF, bitrate or fps control and VFR passes through; only one video and one audio track. On the synthetic ramp it put HLG reference white at Y=148, darker than BT.2408-style mapping. Real DV 8.4 clips may tone-map differently via the RPU (untested), so compare side by side. Speed: 4K, 90 frames in 3.0 s.
- Lisans: kod Apple proprietary (part of macOS) · ağırlık - · ticari: yes
- Apple Silicon: AVFoundation/VideoToolbox hardware
- Kurulum: built in; also /usr/bin/avmediainfo (edit lists, sample tables, metadata) and /usr/bin/avmetareadwrite
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: avconvert -s IN.MOV -p PresetHighestQuality -o OUT.mp4 --replace (SDR); avconvert -s IN.MOV -p PresetPassthrough -o OUT.mov --replace (metadata strip only)
- Güven: high · kaynaklar: https://developer.apple.com/videos/play/wwdc2020/10010/, local: man avconvert (macOS 27, Feb 2025 page); local tests 2026-10-05

### Optional newer engine: libplacebo tone/gamut mapping, scale_vt, xpsnr, colordetect, whisper
- **Seçim:** Homebrew ffmpeg-full 9.0.2 (keg-only) + molten-vk 1.4.2
- Alternatifler: Keep the bundled 6.0 (enough for all QC)
- Neden: Homebrew 'ffmpeg' 9.0.2 depends only on dav1d, lame, libvmaf, libvpx, openssl@3, opus, sdl2-compat, svt-av1, x264, x265 and xz. It has no zimg, so no zscale, and no libass or freetype, so no drawtext. 'ffmpeg-full' 9.0.2 adds zimg, libplacebo, libvidstab, rubberband, whisper.cpp, libass, frei0r, jpeg-xl, tesseract and more. Bottles exist for arm64_golden_gate (this macOS 27). The libplacebo formula depends on vulkan-loader and shaderc but not MoltenVK, so the ffmpeg libplacebo filter also needs molten-vk. That combination is not verified on macOS 27. Disk use is an estimate only (0.6-1.2 GB with dependencies; low confidence).
- Lisans: kod FFmpeg GPL-3.0-or-later; libplacebo LGPL-2.1-or-later; MoltenVK Apache-2.0 · ağırlık - · ticari: yes
- Apple Silicon: arm64 bottles; libplacebo runs on the GPU via Vulkan on Metal (MoltenVK); scale_vt uses VTPixelTransferSession
- Kurulum: BLOCKED today: brew fails with 'You have not agreed to the Xcode license' (xcode-select points to /Applications/Xcode.app). The user runs: sudo xcodebuild -license accept (or sudo xcode-select -s /Library/Developer/CommandLineTools). Then: HOMEBREW_NO_ANALYTICS=1 brew install ffmpeg-full molten-vk. The binary is $(brew --prefix ffmpeg-full)/bin/ffmpeg and is not on PATH.
- Disk: ~1000 MB · bakım: FFmpeg 9.0 released 2026-08-04; formula 9.0.2 generated 2026-10-04
- Ajan kullanımı: Call by absolute path, e.g. ffmpeg -vf 'libplacebo=tonemapping=bt.2390:colorspace=bt709:color_primaries=bt709:color_trc=bt709:format=yuv420p'
- Güven: medium · kaynaklar: https://formulae.brew.sh/api/formula/ffmpeg.json, https://formulae.brew.sh/api/formula/ffmpeg-full.json, https://formulae.brew.sh/api/formula/libplacebo.json, https://formulae.brew.sh/api/formula/molten-vk.json, https://jbkempf.com/blog/2026/ffmpeg-9.0/

### Ingest inspection: Dolby Vision profile, HDR format, VFR mode, rotation, edit lists, extra tracks
- **Seçim:** pymediainfo 7.0.1 (MediaInfo library bundled in the wheel) + avmediainfo (built-in) + ffprobe JSON
- Alternatifler: brew install media-info (after the Xcode license fix)
- Neden: - MediaInfo (BSD-2) reports the HDR format string. For iPhone this includes the Dolby Vision profile '8.4' with BL+RPU and HLG compatibility (exact wording is medium confidence). It also reports 'Frame rate mode: Variable'.
- The pymediainfo 7.0.1 macOS universal2 wheel (2025-02-12) bundles libmediainfo, so Homebrew is not needed.
- avmediainfo shows per-track edit-list segments (measured: video media start 0.067 s for B-frame delay, audio 0.021 s for AAC priming), per-sample timing (--samples, useful for proving VFR) and asset/track metadata.
- The Homebrew media-info 26.05 CLI is the alternative once brew works.
- Lisans: kod pymediainfo MIT; MediaInfo BSD-2-Clause; avmediainfo Apple built-in · ağırlık - · ticari: yes
- Apple Silicon: native universal2 wheel; no acceleration needed
- Kurulum: /Users/onurkaya/Projects/video/arac/uv pip install --python /Users/onurkaya/Projects/video/.venv/bin/python pymediainfo
- Disk: ~15 MB · bakım: pymediainfo 7.0.1 (Feb 2025); MediaInfo 26.05 (Homebrew, 2026)
- Ajan kullanımı: from pymediainfo import MediaInfo; v=MediaInfo.parse(p).video_tracks[0]; read v.hdr_format, v.frame_rate_mode, v.rotation, or MediaInfo.parse(p, output='JSON'). Also: avmediainfo IN.MOV --brief / --metadata all.
- Güven: medium · kaynaklar: https://pypi.org/pypi/pymediainfo/json, https://formulae.brew.sh/api/formula/media-info.json, local: avmediainfo --help (macOS 27)

### Metadata / GPS verification and stripping for videos and photos
- **Seçim:** ExifTool 13.55
- Alternatifler: ffprobe format_tags/stream_tags + avmediainfo --metadata all (built in) for verification; ffmpeg -map_metadata -1 or avconvert for stripping
- Neden: Reads and writes QuickTime metadata groups:
- Keys:GPSCoordinates (com.apple.quicktime.location.ISO6709), ItemList '©xyz', UserData and XMP
- Make, Model, Software and CreationDate
- -ee extracts timed metadata (mebx tracks)

FAQ #32 gives the safe JPEG strip that keeps the ICC profile: -all= --icc_profile:all -tagsfromfile @ -colorspacetags (add -orientation if pixels are not rotated). It is pure Perl and macOS ships perl 5.34, so it runs without Homebrew.
- Lisans: kod Artistic-1.0-Perl OR GPL-1.0-or-later · ağırlık - · ticari: yes
- Apple Silicon: Perl; no acceleration needed
- Kurulum: brew install exiftool (after the Xcode fix), or without brew: download the current Image-ExifTool-<ver>.tar.gz (13.55 at time of writing) from https://exiftool.org, tar xzf, then run perl Image-ExifTool-13.55/exiftool -ver
- Disk: ~30 MB · bakım: 13.55 is current in Homebrew (Oct 2026); very actively maintained
- Ajan kullanımı: exiftool -a -G1 -s -ee out.mp4 | grep -i -E 'gps|location|make|model|software|serial|lens' -> must print nothing
- Güven: high · kaynaklar: https://formulae.brew.sh/api/formula/exiftool.json, https://exiftool.org/TagNames/QuickTime.html, https://exiftool.org/faq.html, https://exiftool.org/exiftool_pod.html

### Objective quality of each deliverable versus the master (VMAF / SSIM / PSNR)
- **Seçim:** libvmaf inside the bundled ffmpeg + ffmpeg-quality-metrics 3.12.2 (JSON wrapper)
- Alternatifler: ffmpeg ssim/psnr filters (built in)
- Neden: Verified:
- The default model (vmaf_v0.6.1) and the NEG model work.
- The phone model works via model=version=vmaf_v0.6.1\\:enable_transform=true (97.6 versus 85.3 default on the same pair). The deprecated phone_model=1 option is silently ignored in 6.0.
- The JSON log has pooled_metrics.vmaf.mean / min / harmonic_mean.

The Netflix FAQ says the default model assumes a 1080p HDTV viewed at 3H. Upsample a lower-resolution distorted file to the reference resolution and keep identical fps and frame alignment. VMAF is not valid for HDR-versus-SDR comparisons. ffmpeg-quality-metrics 3.12.2 (MIT, uploaded 2026-09-17, Python 3.10+) wraps VMAF, SSIM, PSNR, VIF and MSAD into JSON. Standalone libvmaf 3.2.1 (BSD-2-Clause-Patent) is optional.
- Lisans: kod libvmaf BSD-2-Clause-Patent; ffmpeg-quality-metrics MIT · ağırlık VMAF models: BSD-2-Clause-Patent (shipped with libvmaf) · ticari: yes
- Apple Silicon: CPU (NEON, n_threads=8): a 1080x1920 test pair runs in seconds
- Kurulum: Bundled already. Optional: /Users/onurkaya/Projects/video/arac/uv pip install --python /Users/onurkaya/Projects/video/.venv/bin/python ffmpeg-quality-metrics
- Disk: ~5 MB · bakım: ffmpeg-quality-metrics 3.12.2 (2026-09-17); libvmaf 3.2.1 (Homebrew)
- Ajan kullanımı: ffmpeg -i delivered.mp4 -i master.mp4 -lavfi '[0:v]setpts=PTS-STARTPTS[d];[1:v]setpts=PTS-STARTPTS[r];[d][r]libvmaf=model=version=vmaf_v0.6.1:n_threads=8:log_fmt=json:log_path=vmaf.json' -f null -   (the first input is the distorted file)
- Güven: high · kaynaklar: https://github.com/Netflix/vmaf/blob/master/resource/doc/faq.md, https://pypi.org/pypi/ffmpeg-quality-metrics/json, https://formulae.brew.sh/api/formula/libvmaf.json

### Cut map for flash-frame, jump-cut and EDL-conformance checks
- **Seçim:** PySceneDetect 0.7.1 (already in the .venv) + ffmpeg scdet
- Alternatifler: ffmpeg select='gt(scene,0.25)',showinfo (already in the workspace CLAUDE.md)
- Neden: Detector defaults: detect-adaptive 3.0 (fast cuts, rolling average), detect-content 27, detect-threshold 12 (fades / black), detect-hash 0.395 (perceptual hash, also finds repeated shots), detect-hist 0.05. The default --min-scene-len of 0.6 s hides flash frames, so use -m 1 for QC. ffmpeg scdet (t=10) reported a planted one-frame white insert as two cuts (2.500 s and 2.567 s). scdet ignores dissolves by design.
- Lisans: kod PySceneDetect BSD-3-Clause; OpenCV Apache-2.0 · ağırlık - · ticari: yes
- Apple Silicon: CPU; OpenCV build in the venv
- Kurulum: Already installed: /Users/onurkaya/Projects/video/.venv/bin/scenedetect (0.7.1, released 2026-07-22, Python 3.10-3.13)
- Disk: ~0 MB · bakım: 0.7.1 2026-07-22; 0.7 2026-05-03
- Ajan kullanımı: scenedetect -i out.mp4 -m 1 detect-adaptive list-scenes -n   (prints the scene list; -s stats.csv for per-frame metrics)
- Güven: high · kaynaklar: https://pypi.org/pypi/scenedetect/json, https://www.scenedetect.com/docs/latest/cli.html

### Loudness / true-peak normalization and good AAC encoding
- **Seçim:** ffmpeg ebur128 (measure) + two-pass loudnorm with linear=true + aac_at (AudioToolbox AAC); re-measure the ENCODED file
- Alternatifler: ffmpeg-normalize (MIT wrapper; PyPI reports 1.42.0, release date unclear)
- Neden: Verified:
- Pass 1 JSON, then pass 2 with linear=true, landed at I -13.84 LUFS, TP -1.78 dBTP, normalization_type 'linear'.
- After AAC encoding, true peak rose: aac_at 256k -1.7, native aac 256k -1.6, aac_at 128k -1.4. Target -1.5 dBTP before encoding at 192k or more and -2.0 at 128k or less, then confirm -1.0 dBTP or lower after encoding.
- The current gain + alimiter approach (betikler/ustala.sh, -16 LUFS target) undershot on transient-heavy material (-15.4 for a -14 target), so iterate measure -> adjust.
- aac_at silently caps stereo 48 kHz at 320 kb/s.

Targets: social / YouTube -14 LUFS (the HyperFrames media-use 'Publish loudness' recipe uses I=-14, TP=-1.5, LRA=11). YouTube's about -14 normalization is widely measured but not officially documented. Instagram and TikTok publish none.
- Lisans: kod FFmpeg GPL; aac_at uses Apple AudioToolbox (macOS) · ağırlık - · ticari: yes
- Apple Silicon: aac_at is Apple's encoder; CPU
- Kurulum: none (bundled ffmpeg)
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: Pass 1: -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - ; parse the JSON with Python (zsh does not word-split variables); pass 2: measured_I, measured_TP, measured_LRA, measured_thresh, offset, linear=true
- Güven: high · kaynaklar: https://pypi.org/pypi/ffmpeg-normalize/json, local: /Users/onurkaya/.claude/skills/media-use/references/operations.md (Publish loudness), local: /Users/onurkaya/Projects/video/betikler/ustala.sh

### Choosing the delivery encoder (quality per bit versus speed)
- **Seçim:** libx264 -preset slow (CRF or two-pass) for size-capped deliverables; h264/hevc_videotoolbox -q:v 60-70 for fast high-bitrate copies (uploads, AirDrop, previews); libx265 -tag:v hvc1 when HEVC size matters
- Alternatifler: SVT-AV1 (in bundled ffmpeg) for small archive copies
- Neden: Equal-bitrate VMAF on hard synthetic 1080p30 content (fractal zoom plus temporal grain):
- About 4 Mb/s: x265 medium 49.8, x264 slow 47.0, VideoToolbox HEVC 44.9, VideoToolbox H.264 41.1.
- About 20 Mb/s: VideoToolbox H.264 -q:v 65 (20.3 Mb/s) 63.2 versus x264 CRF 18 (21.6 Mb/s) 64.2.

The hardware gap closes at high bitrate and widens when bits are scarce, as with WhatsApp. Speeds: VideoToolbox H.264 88 fps and HEVC 105 fps versus x264 slow 20 fps. The VideoToolbox encoder passes color primaries, transfer and matrix tags but writes no HDR mastering or MaxCLL metadata.
- Lisans: kod x264/x265 GPL; VideoToolbox Apple · ağırlık - · ticari: yes
- Apple Silicon: VideoToolbox = M2 media engine; x264/x265 = CPU NEON
- Kurulum: none (bundled ffmpeg)
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: -c:v h264_videotoolbox -q:v 65 -profile:v high (Apple Silicon only); -c:v libx264 -preset slow -crf 17-20
- Güven: medium · kaynaklar: https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavcodec/videotoolboxenc.c, local measurements 2026-10-05 (synthetic content, indicative only)

### Archival / hand-off masters
- **Seçim:** ProRes 422 HQ (or LT) via prores_videotoolbox (M2 hardware), 10-bit 4:2:2 + PCM 24-bit in .mov, only for editor hand-off or an external disk. The real archive is originals + composition source + a CRF 14-16 master.
- Alternatifler: - libx265 -crf 14 -pix_fmt yuv420p10le -tag:v hvc1 (space-efficient 10-bit master)
- avconvert PresetAppleProRes422LPCM
- FFV1 lossless (too large for this disk)
- Neden: Apple ProRes White Paper (Apr 2022) target rates:
- 1920x1080 30p: Proxy 45 Mb/s (20 GB/h), LT 102 (46 GB/h), 422 147 (66 GB/h), HQ 220 (99 GB/h), 4444 330
- 3840x2160 30p: Proxy 182, LT 410 (185 GB/h), HQ 884 Mb/s (398 GB/h)

With about 18-21 GB free, that is roughly 11 min of 1080p30 HQ or about 2.7 min of 4K30 HQ. prores_videotoolbox works on this M2 (the hardware encoder is required by default), keeps HLG tags, outputs yuv422p10le, and is about 9x faster than prores_ks.
- Lisans: kod Apple ProRes encoder via VideoToolbox (macOS); prores_ks part of FFmpeg (LGPL/GPL build) · ağırlık - · ticari: yes
- Apple Silicon: M2 ProRes engine: 4K HQ at about 127 fps
- Kurulum: none (bundled ffmpeg)
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: ffmpeg -nostdin -i IN -c:v prores_videotoolbox -profile:v hq -c:a pcm_s24le master.mov; integrity: shasum -a 256 and ffmpeg -i master.mov -map 0:v -f framemd5 master.framemd5
- Güven: high · kaynaklar: https://www.apple.com/final-cut-pro/docs/Apple_ProRes.pdf

### Dolby Vision RPU inspection or removal (only if preserving or debugging DV)
- **Seçim:** dovi_tool 2.3.4 (optional)
- Alternatifler: 
- Neden: iPhone records DV profile 8.4 (HLG-compatible base layer + RPU). Re-encoding with ffmpeg drops the RPU and keeps HLG, which is fine for SDR or plain HLG deliverables, so this tool is only needed to inspect or keep DV. Bundled ffmpeg 6.0 has no Dolby Vision bitstream filters; FFmpeg 9.0 added a DV multi-layer bsf.
- Lisans: kod MIT · ağırlık - · ticari: yes
- Apple Silicon: native arm64 bottle (Rust)
- Kurulum: brew install dovi_tool (after the Xcode license fix) or the GitHub release binary
- Disk: ~10 MB · bakım: 2.3.4 in Homebrew (2026)
- Ajan kullanımı: dovi_tool info / extract-rpu / remove on a raw HEVC stream extracted with ffmpeg -c:v copy -bsf:v hevc_mp4toannexb -f hevc
- Güven: medium · kaynaklar: https://formulae.brew.sh/api/formula/dovi_tool.json, https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog

### Measurable photosensitivity check and audio drift / offset check (cannot listen or watch continuously)
- **Seçim:** Two validated helper scripts written during this research: flashcount.py (WCAG 2.3.1 flash counter) and xcorr_lag.py (song-in-render offset and drift via numpy FFT cross-correlation)
- Alternatifler: 
- Neden: flashcount.py results: 5 Hz full-frame strobe = 5 flashes/s FAIL; 3 Hz = 3 PASS; single white flash = 1 PASS. ffmpeg's photosensitivity filter flagged 10/90 frames of an ordinary moving test pattern, so use it only as a warning. xcorr_lag.py results: exact placement measured 0.00/0.00/0.00 ms; a 0.05% speed error measured -2.25/-5.25/-9.25 ms (drift 7 ms) -> FAIL. Both use only ffmpeg and numpy (present in system python3 and the .venv).
- Lisans: kod own code (no third-party code) · ağırlık - · ticari: yes
- Apple Silicon: CPU; seconds per file
- Kurulum: Copy from the session scratchpad into the workspace, e.g. cp /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/qc/{flashcount.py,xcorr_lag.py} /Users/onurkaya/Projects/video/betikler/
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: python3 flashcount.py ffmpeg out.mp4 ; python3 xcorr_lag.py ffmpeg song.wav out.mp4 <song_start_s> [max_lag_ms]
- Güven: medium · kaynaklar: https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html, https://en.wikipedia.org/wiki/Audio-to-video_synchronization, /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/qc/flashcount.py, /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/qc/xcorr_lag.py

## Kaçınılacaklar

- **Homebrew 'ffmpeg' (slim 9.0.2) for HDR or text work** — No zimg, so no zscale (the tone-map chain fails), and no libass/freetype, so no drawtext or subtitles. Its dependencies are only dav1d, lame, libvmaf, libvpx, openssl, opus, sdl2-compat, svt-av1, x264, x265 and xz. Use the bundled 6.0 or keg-only ffmpeg-full.
- **Retagging HLG as bt709, a transfer-only zscale conversion, or the 'colorspace' filter without tonemap** — Measured: HLG 75-100% became Y=255 (illegal, clipped highlights). Faces and skies wash out.
- **HyperFrames default HDR mode 'auto' (rendering without --sdr)** — A single HLG clip promotes the whole MP4 to BT.2020 HEVC Main10, which is risky on WhatsApp, Android and Windows. --sdr tone-maps with hable (reference white at about 76%, darker midtones), so pre-convert clips with an operator you chose.
- **-vsync** — Deprecated; use -fps_mode cfr|vfr|passthrough (FFmpeg 5.1+).
- **Naive slow motion (setpts on 30 fps sources) and 30<->25/24 fps conversions** — Duplicate frames (unique-frame ratio 0.50 measured) give visible stutter; cadence changes judder. Use true 60/120/240 fps footage or interpolation.
- **libvmaf phone_model=1 in ffmpeg 6.0** — Silently ignored (identical score to the default). Use model=version=vmaf_v0.6.1\\:enable_transform=true.
- **idet on HyperFrames or graphics renders; signalstats BRNG as a hard gate** — False positives: idet reported 27% TFF on a progressive test pattern; BRNG counts chroma and read 31.7% on legal saturated colours.
- **ffmpeg photosensitivity filter as pass/fail** — Over-sensitive: it flags ordinary moving high-contrast content. Use the WCAG counter and treat the filter as a warning.
- **H.264 High10 / 4:2:2 deliverables and the 'hev1' HEVC tag** — Many phone hardware decoders cannot play H.264 10-bit or 4:2:2, and Apple players require hvc1. Deliver 8-bit yuv420p H.264, or HEVC with -tag:v hvc1.
- **VideoToolbox for size-capped deliverables (WhatsApp size targets)** — 3-6 VMAF lower than x264 slow at an equal low bitrate (measured). Fine at 20 Mb/s or more.
- **-map 0 on iPhone MOVs, or -c copy concat of mixed phone clips** — -map 0 pulls mebx timed-metadata tracks and possibly undecodable spatial-audio tracks, and can leak metadata. Mixed timebases, VFR and edit lists in a copy concat drift A/V. Map streams explicitly and conform first.
- **-shortest in the audio mastering pass (betikler/ustala.sh) without a duration check** — Can silently trim the video tail when the audio is shorter. Check |dur_v - dur_a| afterwards.
- **Sending quality-critical videos as WhatsApp or iMessage media** — The apps re-encode them. Use WhatsApp 'Document' (up to 2 GB since May 2022) or AirDrop / iCloud link.
- **FFV1 / uncompressed / 4K ProRes HQ archives on the internal disk** — 4K30 ProRes HQ is about 6.6 GB/min against about 18-21 GB free.
- **PEAT, Netflix Photon, QCTools GUI** — Windows-only, IMF-only, or GUI-centric respectively; not agent-drivable here. ffmpeg plus the scripts cover the same checks.
- **OpenCV 5 Haar cascades for the safe-zone face check** — The .venv's opencv 5.0.0 has no CascadeClassifier or Haar XML files. Use FaceDetectorYN (YuNet ONNX model) or a manual contact sheet.
- **Online QC, compression or 'AI enhance' web services** — They violate the local-only and privacy rules for personal footage.
- **ffprobe-static npm package** — Wrong architecture on Apple Silicon (workspace CLAUDE.md); keep @ffprobe-installer/darwin-arm64.

## Teknikler

### T0 Ingest triage per phone clip (HDR/DV, VFR, true cadence, rotation, audio tracks)
source /Users/onurkaya/Projects/video/ortam.sh.
(1) ffprobe -v error -show_streams -show_format -of json IN.MOV > IN.probe.json. Read from it:
- HDR: color_transfer is arib-std-b67 (HLG) or smpte2084 (PQ).
- Dolby Vision: a side_data_list entry 'DOVI configuration record'; dv_profile 8 + dv_bl_signal_compatibility_id 4 = iPhone 8.4.
- Rotation: 'Display Matrix'.rotation, or tags.rotate in ffprobe 4.4.
- Audio: list every audio stream and pick the stereo AAC index.
(2) VFR: r_frame_rate != avg_frame_rate, or ffmpeg -nostdin -hide_banner -i IN.MOV -map 0:v:0 -vf vfrdet -an -f null - 2>&1 | grep 'VFR:' shows a ratio > 0.
(3) True cadence: ffmpeg -nostdin -hide_banner -i IN.MOV -map 0:v:0 -vf mpdecimate=hi=768:lo=320:frac=0.33,showinfo -an -f null - 2>&1 | grep -c 'showinfo.* n:' divided by duration. Many iPhone clips are 30 fps content in a 60 fps container.
(4) Optional cross-check: pymediainfo hdr_format / frame_rate_mode, and avmediainfo IN.MOV --brief.

**Doğrulama:** One JSON row per clip: {hdr, transfer, dv_profile, rotation, vfr_ratio, true_fps, audio_index}. Continue only when every field is known. Synthetic VFR test: r=30/1 versus avg=1800/67 and vfrdet VFR:0.235 were detected; after the fix, VFR:0.000.

### T1 HDR (HLG / DV 8.4) -> SDR BT.709 CFR mezzanine before HyperFrames
ffmpeg -nostdin -hwaccel videotoolbox -i IN.MOV -map 0:v:0 -map 0:a:0 -vf 'zscale=w=-2:h=1920:f=spline36,setsar=1,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv:d=error_diffusion,format=yuv420p,fps=30' -fps_mode cfr -c:v libx264 -preset slow -crf 14 -g 30 -bf 2 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -c:a aac_at -b:a 256k -ar 48000 -map_metadata -1 -movflags +faststart OUT_sdr.mp4

Notes:
- h=1920 is for portrait clips after autorotate; use h=1080 for landscape.
- Scaling before linearizing is about 2.5x faster.
- tonemap=hable gives a filmic, darker look; reinhard sits between hable and mobius.
- Apple-look alternative: avconvert -s IN.MOV -p PresetHighestQuality -o OUT.mp4, then conform fps with ffmpeg.

**Doğrulama:** - ffprobe shows color_primaries=bt709, color_transfer=bt709, color_space=bt709, color_range=tv, pix_fmt=yuv420p.
- QC5: frames with YHIGH >= 234 are 2% of frames or fewer.
- Mean YAVG is within ±10 code values of the reference rendition the user approved. Make a one-time side-by-side sheet of mobius / hable / avconvert on 3-4 real clips, then lock the operator.

### T2 VFR -> CFR conform and real slow motion
- Conform to the project rate, normally 30 (60 only if the true cadence is 60): -vf 'fps=30' -fps_mode cfr.
- HyperFrames resamples VFR sources itself (-fps_mode cfr -r fps), but direct ffmpeg montages (concat / xfade / acrossfade) need identical inputs: 'settb=AVTB,fps=30,format=yuv420p,setsar=1', same WxH, 48 kHz audio.
- Slow motion: 60 fps source 'setpts=2*PTS,fps=30'; 120 fps 'setpts=4*PTS,fps=30'; 240 fps 'setpts=8*PTS,fps=30'.
- 30 fps sources need interpolation (minterpolate mci, or a RIFE-class model), never plain setpts.

**Doğrulama:** - r_frame_rate == avg_frame_rate == 30/1.
- vfrdet prints 'VFR:0.000000'.
- Per slow-motion shot, mpdecimate kept/total is 0.95 or more. A naive 2x setpts measured 0.50 (stutter); real motion measured 1.00.

### T3 Rotation and 9:16 reframe with square pixels
- Rely on ffmpeg autorotate (default when re-encoding; verified with and without -hwaccel videotoolbox: 1920x1080 + rotation 90 became 720x1280).
- Landscape to vertical: 'crop=trunc(ih*9/16/2)*2:ih,zscale=w=1080:h=1920:f=spline36,setsar=1' (centre crop; animate crop x for reframing).
- End every scale with setsar=1.
- -c copy keeps the display matrix even with -map_metadata -1. In 6.0, clear it with -metadata:s:v:0 rotate=0, or bake it in by re-encoding.

**Doğrulama:** - ffprobe: width/height exactly per preset, sample_aspect_ratio=1:1, display_aspect_ratio=9:16.
- No 'Display Matrix' in side_data_list and no tags.rotate.
- Caught in testing: scaling 16:9 straight to 1080x1920 produced SAR 256:81.

### T4 HyperFrames render settings for delivery
Command: HYPERFRAMES_NO_TELEMETRY=1 npx hyperframes render <proj> --sdr --fps 30 --quality delivery --output renders/<name>_master.mp4

What the engine does (from its code):
- hdrMode 'auto' promotes to 'BT.2020 / HEVC Main10' whenever any HLG/PQ video or image is present. The log says '[Render] HDR auto-promotion triggered by ...'.
- Presets: draft = ultrafast CRF 28; standard = medium CRF 18; high/delivery = slow CRF 15; the 'looks' default = CRF 16.
- libx264 runs with -bf 0, aq-mode=3, deblock 1,1, bt709 VUI, AAC 192k at 48 kHz, +faststart, and writes renderer/version provenance tags (use_metadata_tags).

Treat this file as the master and always transcode per destination (T5).

**Doğrulama:** - The render log says '[Render] SDR forced by --sdr flag' (or 'No HDR sources detected').
- The master probes as h264, yuv420p, bt709 tags, 30/1.
- Run QC1-QC11 on every delivery file, not only on the master.

### T5 Destination export presets (2025-2026 targets)
Common tail for every preset: -map 0:v:0 -map 0:a:0 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -movflags +faststart

(a) Reels / TikTok / Shorts:
ffmpeg -nostdin -i master.mp4 -vf 'scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p' -c:v libx264 -preset slow -crf 17 -maxrate 20M -bufsize 40M -profile:v high -level:v 4.2 -g 15 -bf 2 -c:a aac_at -b:a 320k -ar 48000 -ac 2 <tail> out_vertical.mp4
Targets:
- Video: 9:16, 30 fps (60 only if the source is), H.264 + AAC 48 kHz.
- Audio: -14 LUFS, -1 dBTP or lower.
- Meta Reels ads: 1440x2560 recommended, 0-15 min, 4 GB or less, AAC stereo 128 kb/s or more.
- TikTok ads (Jun 2026): 540x960 or larger, 500 MB or less, 10 min or less, 516 kb/s or more.
- Shorts: up to 3 min (since 2024-10-15), max 1080p upload.

(b) YouTube 16:9: as (a) but scale=1920:1080 and -crf 16 -g 15 -bf 2 (closed GOP at half the frame rate), AAC-LC 48 kHz stereo 384 kb/s (-c:a aac -b:a 384k). For 4K use scale=3840:2160 -level:v 5.1 -maxrate 60M.
YouTube spec:
- Container and stream: MP4 with moov at the front, no edit lists, progressive, High profile, CABAC, 4:2:0.
- SDR bitrates: 1080p 8 Mb/s (24-30 fps) / 12 Mb/s (48-60 fps); 2160p 35-45 / 53-68 Mb/s.
- HDR bitrates: 1080p 10 / 15 Mb/s; 2160p 44-56 / 66-85 Mb/s.
Only if YouTube processing complains: -use_editlist 0, then re-run the A/V slate.

(c) WhatsApp (H.264 8-bit, never HEVC/HDR):
- Bitrate: VK = floor(TARGET_MB*8000*0.97/DUR - 128).
- Pass 1: ffmpeg -y -i master.mp4 -vf 'scale=720:1280:flags=lanczos,setsar=1,fps=30,format=yuv420p' -c:v libx264 -preset slow -profile:v high -level:v 4.0 -b:v ${VK}k -g 60 -pass 1 -passlogfile wa -an -f null /dev/null
- Pass 2: same -vf and codec with -b:v ${VK}k -maxrate $((VK*3/2))k -bufsize $((VK*2))k -g 60 -pass 2 -passlogfile wa -c:a aac_at -b:a 128k -ar 48000 <tail> out_whatsapp.mp4
- Send it as a Document (up to 2 GB) to avoid WhatsApp's recompression.

(d) iMessage / AirDrop: -c:v hevc_videotoolbox -q:v 65 -tag:v hvc1 -profile:v main (or libx265 -crf 20 -tag:v hvc1). AirDrop delivers the file unchanged.

(e) Optional Apple-only HDR copy: hyperframes render --hdr (HLG, BT.2020, HEVC Main10, hvc1).

**Doğrulama:** - QC1 per preset: exact WxH, 30/1, codec/profile/level, bt709 tags, SAR 1:1, AAC-LC 48 kHz 2 ch, moov before mdat, keyframe gap 0.5 s or less for (a)/(b).
- File size within the destination limit; WhatsApp file within ±3% of TARGET_MB.
- QC10 VMAF thresholds met.

### T6 Vertical safe-zone check
Platform UI-free areas on 1080x1920:
- Meta Reels ads guide: keep 14% top, 35% bottom and 6% on each side clear.
- TikTok in-feed template: 12.5% top, 34% bottom, about 11% per side, plus the right button column.
- Shorts: keep key content in the centre 4:5 (1080x1350).
- Conservative union: x 120-960, y 285-1248.
- Instagram's grid previews Reels as a 3:4 centre crop, so keep the cover subject within y 240-1680.

Review sheet: ffmpeg -nostdin -i out.mp4 -vf 'fps=1/2,drawbox=x=0:y=0:w=iw:h=ih*0.14:color=red@0.35:t=fill,drawbox=x=0:y=ih*0.65:w=iw:h=ih*0.35:color=red@0.35:t=fill,drawbox=x=0:y=0:w=iw*0.11:h=ih:color=red@0.25:t=fill,drawbox=x=iw*0.89:y=0:w=iw*0.11:h=ih:color=red@0.25:t=fill,scale=216:-2,tile=6x3' -frames:v 1 -update 1 safe_sheet.png, then open the PNG with Read.

Automatic option: cv2.FaceDetectorYN (YuNet ONNX from opencv_zoo, about 0.2 MB; licence not verified).

**Doğrulama:** - Faces and key action lie outside the red bands in every sampled frame.
- Automatic check: 95% or more of sampled face centres inside the safe box.
- A face in the bottom 35% for more than 1 s means reframe.

### QC1 Container and stream conformance
- Streams: ffprobe -v error -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,profile,level,pix_fmt,width,height,sample_aspect_ratio,display_aspect_ratio,r_frame_rate,avg_frame_rate,field_order,color_range,color_space,color_transfer,color_primaries,sample_rate,channels,start_time,duration,has_b_frames -of json out.mp4
- Keyframes: ffprobe -v error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=p=0 out.mp4 | awk -F, '$2 ~ /K/ {print $1}'
- Faststart: read the top-level MP4 boxes (4-byte size + 4-byte type, seek size-8) and require 'moov' before 'mdat'. Verified: h264_videotoolbox output without +faststart was ftyp,free,mdat,moov.
- Edit lists and sample timing: avmediainfo out.mp4.

**Doğrulama:** PASS when all of these hold:
- codec/profile/level match the preset; pix_fmt yuv420p; SAR 1:1.
- r_frame_rate == avg_frame_rate == target; field_order progressive or absent.
- SDR: bt709 x3 + tv range. HDR copy: bt2020 / arib-std-b67 / bt2020nc + yuv420p10le + hvc1.
- Audio: AAC LC, 48000 Hz, 2 channels.
- |start_time_v - start_time_a| is 1 frame or less; |duration_v - duration_a| is 50 ms or less (8 ms measured on a correct file; one AAC frame = 21.3 ms).
- Maximum keyframe gap 2 s or less (0.5 s for the YouTube spec).
- moov before mdat; no Display Matrix; size and duration within the destination limits.

### QC2 Decode integrity plus black / freeze / silence detectors
- Decode errors: ffmpeg -nostdin -v error -i out.mp4 -map 0 -f null - 2>&1 | wc -l
- Video pass: ffmpeg -nostdin -hide_banner -nostats -i out.mp4 -an -vf 'blackdetect=d=0.1:pix_th=0.10:pic_th=0.98,freezedetect=n=-60dB:d=0.5,scdet=t=10' -f null - 2>&1 | grep -E 'black_start|freeze_(start|duration|end)|lavfi.scd'
- Audio pass: ffmpeg -nostdin -hide_banner -nostats -i out.mp4 -vn -af 'silencedetect=n=-50dB:d=0.5,ebur128=peak=true:framelog=quiet,astats=measure_perchannel=none:measure_overall=Peak_level+Flat_factor+Peak_count+DC_offset' -f null - 2>&1
- Validated on a file with planted defects: black at 0-0.5 s, a 1-frame white flash at 2.5 s, a 1 s freeze at 4.03 s and 1 s of silence at 2 s were all reported at the right times. freezedetect also flags the black head, so de-duplicate overlapping events.

**Doğrulama:** PASS when:
- There are 0 decode-error lines.
- Black appears only where the EDL plans it (head fade 0.5 s or less, tail 1.5 s or less).
- No freeze of 0.5 s or more outside planned stills or holds.
- No silence of 0.5 s or more mid-programme (head 0.3 s or less, tail 1.5 s or less).
- idet is used only on legacy interlaced camera sources (PASS if TFF+BFF is under 5% of the multi-frame count); never on renders.

### QC3 Cut map: flash frames, unplanned cuts, jump cuts, stutter
- Cut list: scdet times, or /Users/onurkaya/Projects/video/.venv/bin/scenedetect -i out.mp4 -m 1 detect-adaptive list-scenes -n
- Flash frame: two cuts fewer than 3 frames apart. Verified: a 1-frame insert produced cuts at 2.500 and 2.567 s.
- Jump-cut probe at each cut T: ffmpeg -nostdin -ss <T-1/fps> -i out.mp4 -ss <T> -i out.mp4 -lavfi '[0:v]trim=end_frame=1,scale=320:-2,format=gray[a];[1:v]trim=end_frame=1,scale=320:-2,format=gray[b];[a][b]ssim' -f null - 2>&1 | grep -o 'All:[0-9.]*'. Unrelated shots measured 0.37.
- Stutter: mpdecimate kept/total per shot (as in T2).
- Repeated footage: scenedetect detect-hash.

**Doğrulama:** - PASS: every planned hard cut is found within ±1 frame of its EDL time.
- WARN: any cut not in the EDL.
- FAIL: a shot shorter than 3 frames (100 ms at 30 fps), unless it is an intended strobe.
- WARN for review: SSIM 0.6 or more across a cut that uses the same source on both sides (jump cut).
- Unique-frame ratio 0.95 or more on motion shots.

### QC4 Photosensitivity (WCAG 2.3.1)
- Run python3 /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/qc/flashcount.py ffmpeg out.mp4
- The script converts per-frame YAVG to relative luminance, counts opposing changes of 0.10 or more where the darker state is below 0.80, and reports the worst 1-second window.
- Secondary warning: ffmpeg -v verbose -i out.mp4 -an -vf photosensitivity=bypass=1 -f null - 2>&1 | grep -c EXCEEDED

**Doğrulama:** - PASS: 3 or fewer flashes in any 1-second window.
- Validated: 5 Hz strobe FAIL; 3 Hz PASS; single white flash PASS.
- The full-frame average over-estimates flashing area, so the check is conservative.

### QC5 Luma range and clipping (especially after tone mapping)
ffmpeg -nostdin -i out.mp4 -an -vf 'signalstats,metadata=mode=print:file=-' -f null - 2>/dev/null | awk -F= '/YHIGH=/{n++; if($2>=234)hi++} /YLOW=/{if($2<=17)lo++} /YMIN=/{if($2<16)oor++} /YMAX=/{if($2>235)oor++} END{print n, hi, lo, oor}'

YHIGH and YLOW are the 90th and 10th percentiles, so they mean 10% or more of the frame is clipped white or crushed black.

**Doğrulama:** PASS (SDR, tv range):
- Clipped-white frames are 2% of frames or fewer, excluding intended white flashes or dips.
- Frames with out-of-range values (YMIN < 16 or YMAX > 235) are 1% or fewer.
- Crushed-black frames are 5% or fewer; night scenes go to review.
- Mean YAVG is within ±10 of the approved tone-map reference.

### QC6 Loudness, true peak and audio health (measured on the encoded file)
- Measure: ffmpeg -nostdin -hide_banner -nostats -i out.mp4 -vn -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | sed -n '/Summary/,$p'
- Fix, pass 1: loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json
- Fix, pass 2: the same with measured_I / measured_TP / measured_LRA / measured_thresh / offset and linear=true. Parse the JSON in Python.
- Encode with aac_at at 192-320 kb/s.
- Mono compatibility: -af 'aphasemeter=video=0,ametadata=mode=print:key=lavfi.aphasemeter.phase:file=-'

**Doğrulama:** PASS when:
- I is within ±1 LU of the target: -14 for social / YouTube; -14 to -16 for messaging (ustala.sh currently uses -16).
- True peak is -1.0 dBTP or lower after AAC encoding (measured overshoot +0.1 to +0.4 dB).
- LRA is 11 LU or less for music montages.
- loudnorm reported 'linear'.
- astats Flat_factor = 0 and Peak count is small (a clipped test signal gave 38 and 64000).
- |DC offset| is 0.005 or less.
- Mean phase is 0.2 or more (in-phase 1.00, inverted -1.00 measured).

### QC7 Clicks at audio edit points
- For each audio edit time T from the EDL, measure m(T): ffmpeg -nostdin -hide_banner -nostats -i out.mp4 -vn -af 'atrim=start=<T-0.01>:duration=0.02,astats=measure_perchannel=none:measure_overall=Max_difference+RMS_difference' -f null - 2>&1 | grep -E 'Max difference|RMS difference'
- Measure the same at T-60 ms and T+40 ms as neighbours.
- Prevent clicks with 5-10 ms fades or crossfades at every audio cut (afade / acrossfade d=0.01-0.02; HyperFrames data-fade-in/out).

**Doğrulama:** - PASS: m(T) is no more than 3x the larger neighbour at every edit.
- Measured: clean window 334 versus a hard phase-jump cut 11,919 (about 36x).
- Max/RMS difference ratio: 1.4 clean versus 26 at the click.

### QC8 A/V sync: static, pipeline slate, and song offset/drift
(1) Static: start_time and duration checks from QC1.
(2) Slate, once per toolchain change:
- Render a composition with a 1-frame white flash at t=1.000 s and a 1 kHz beep starting at t=1.000 s, encoded exactly like the deliverables.
- Flash time: first frame with YAVG > 128, from -vf 'signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=-'.
- Beep time: first silence_end from -af silencedetect=n=-30dB:d=0.005.
- Validated: a planted +40 ms offset measured +40.0 ms.
(3) Song placement and drift: python3 /private/tmp/claude-501/-Users-onurkaya-Projects-video/751b0520-a2bb-4907-b2a0-5609716dbd05/scratchpad/qc/xcorr_lag.py ffmpeg song.wav out.mp4 <song_start_s>. It uses 8 kHz mono FFT cross-correlation with a ±500 ms search at 10%, 50% and 90% of the song.

**Doğrulama:** - PASS: |slate offset| is 1 frame (33 ms) or less. This is stricter than EBU R37 (+40 / -60 ms end-to-end) and ITU-R BT.1359 detectability (45 ms audio lead / 125 ms lag).
- Song lag is within ±5 ms at every checkpoint, and max minus min is 2 ms or less (validated: a 0.05% speed error gave a 7 ms spread and failed).
- Durations pass QC1.

### QC9 Cut-on-beat verification (measures the earlier 'audio slipping' failure)
- Take hard-cut times from QC3 and the beat grid from a validated tracker.
- Cross-check two independent trackers; if their median disagreement exceeds 30 ms, mark the grid unreliable and confirm downbeats manually instead of guessing.
- Residual r_i = cut_i - nearest beat.
- Also compute a numpy spectral-flux onset envelope and check that cuts land within ±30 ms of onset peaks.

**Doğrulama:** - PASS: 90% or more of intended on-beat cuts are within ±1 frame (±33 ms). At 30 fps a cut can only sit on a frame boundary, so ±16.7 ms is the floor.
- Median |r| is 20 ms or less, and mean r is within ±10 ms (no systematic lag).
- Give the user the residual numbers, not 'sounds right'.

### QC10 Objective quality versus the master (VMAF)
- Command: ffmpeg -nostdin -i delivered.mp4 -i master.mp4 -lavfi '[0:v]setpts=PTS-STARTPTS,scale=1080:1920:flags=bicubic[d];[1:v]setpts=PTS-STARTPTS[r];[d][r]libvmaf=model=version=vmaf_v0.6.1:n_threads=8:log_fmt=json:log_path=vmaf.json' -f null -
- Read pooled_metrics.vmaf.mean and min from vmaf.json.
- Phone-viewing model: replace the model with model=version=vmaf_v0.6.1\\:enable_transform=true (keep the two backslashes inside the single quotes).
- Optional: ffmpeg-quality-metrics delivered.mp4 master.mp4 -m vmaf ssim psnr.

**Doğrulama:** Only compare at the same resolution, fps and frame count; never HDR against SDR. Heuristic thresholds:
- Upload copies: mean 93 or more and min 85 or more.
- WhatsApp / size-capped copies: phone-model mean 80 or more.
- SSIM All 0.98 or more as a secondary check.

### QC11 Privacy: metadata and GPS strip plus verification
- Strip: ffmpeg ... -map 0:v:0 -map 0:a:0 -map_metadata -1 -map_metadata:s -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact. Verified to remove ISO6709 location, make, model, creation date, the 'Lavf' encoder tag and HyperFrames provenance. Colour tags and rotation side data survive.
- No re-encode: avconvert -s IN.mov -p PresetPassthrough -o OUT.mov.
- Photos: exiftool -all= --icc_profile:all -tagsfromfile @ -colorspacetags -orientation -overwrite_original photo.jpg
- iPhone share sheet: Options -> Location off.

**Doğrulama:** PASS when all of these print nothing:
- ffprobe -v error -show_entries format_tags:stream_tags -of compact out.mp4 | grep -i -E 'location|ISO6709|xyz|make|model|software|creat|com.apple|encoder|hyperframes'
- exiftool -a -G1 -s -ee out.mp4 | grep -i -E 'gps|location|make|model|software|serial|lens'
- avmediainfo out.mp4 --metadata all has no 'Asset Metadata' block
- grep -c -a ISO6709 out.mp4 returns 0
Remaining handler_name and vendor_id tags are harmless.

### T7 Archival master and integrity
Archive contents:
- Untouched camera originals.
- The composition source: HTML, JS, assets, kurgu scripts, EDL, beat grid.
- Tool versions: ffmpeg -version and the hyperframes version.
- One CRF 14-16 SDR master.

ProRes only for hand-off or on an external disk:
- ffmpeg -nostdin -i IN -c:v prores_videotoolbox -profile:v hq -c:a pcm_s24le master.mov
- Software fallback: -c:v prores_ks -profile:v 3 -vendor apl0 -pix_fmt yuv422p10le
- 10-bit compact alternative: libx265 -crf 14 -pix_fmt yuv420p10le -tag:v hvc1

Integrity:
- shasum -a 256 master.mov > master.sha256
- ffmpeg -i master.mov -map 0:v -f framemd5 master.framemd5

**Doğrulama:** - ffprobe shows profile HQ (or LT), yuv422p10le, and colour tags equal to the source.
- A later framemd5 is identical.
- At least 5 GB stays free after writing.
- Size budget: 1080p30 HQ = 99 GB/h; 4K30 HQ = 398 GB/h.


## Riskler

- Homebrew is unusable right now: every brew command fails with 'You have not agreed to the Xcode license' (xcode-select points to /Applications/Xcode.app). It needs the user's sudo ('sudo xcodebuild -license accept' or switching to the Command Line Tools). Until then use the bundled ffmpeg, arac/uv 0.12.23 for Python tools (pymediainfo, ffmpeg-quality-metrics), and ExifTool from the tarball with system perl 5.34.
- Disk: about 18-21 GB free. ProRes 4K30 HQ is about 6.6 GB/min. HyperFrames CRF 16 renders of grainy footage hit 74 Mb/s (2.5 GB for 4:48). Check projected sizes before writing and delete intermediates.
- Tone mapping is a creative choice, not a measurement: operators put HLG reference white anywhere from Y 148 (Apple avconvert, synthetic ramp) to 218 (mobius). Apple's RPU-aware conversion of real DV 8.4 clips was not tested, so the user should approve the look once from a side-by-side contact sheet.
- Platform limits change fast and the official TikTok, Instagram and WhatsApp help pages could not be fetched (JavaScript-rendered). Organic numbers (Reels up to 20 min with full reach to about 3 min; TikTok 10 min in-app / 60 min web, about 288 MB iOS / 72 MB Android / 4 GB web; Shorts up to 3 min, max 1080p) come from postfa.st (updated 2026-09-25) and Google help. Official specs that were fetched: Meta Reels ads guide, TikTok ads spec (June 2026), YouTube upload spec.
- Instagram and TikTok loudness normalization is undocumented. YouTube's about -14 LUFS is community-measured. A -14 LUFS / -1 dBTP or lower target is a safe compromise, not a guarantee.
- ffprobe 4.4.1 is old: field names differ (pkt_pts_time, side_data_list, tags.rotate) and parsing written for it may break on ffprobe 7+ (stream_side_data section). Pin and test parsers.
- Bundled ffmpeg 6.0 cannot decode Apple APAC spatial audio. iPhone 16/17 spatial recordings may carry an APAC track (not verified on the user's clips), so always map the AAC stereo track explicitly. It also lacks scale_vt, libplacebo and the Dolby Vision bitstream filters.
- The bundled ffmpeg was built with --enable-nonfree: fine to use, not to redistribute.
- Several thresholds are heuristics calibrated on synthetic tests: VMAF of 93 or more, jump-cut SSIM 0.6, click ratio 3x, 2% clipped frames, flash counting from full-frame averages. Treat FAIL as 'review' and tune on the user's real footage.
- Beat-grid accuracy is upstream (the audio domain). QC9 can prove cuts are off-beat but cannot fix a wrong grid, and the assistant cannot listen, so report residual numbers rather than 'sounds right'.
- Low confidence: macOS and iOS players may show bt709-tagged (1-1-1) renders slightly lighter than Chrome did (QuickTime gamma handling). Check on the target iPhone before declaring a colour match.
- Messaging apps recompress unpredictably. WhatsApp in-chat size, HD and Status-length limits are unverified for 2026.
- The two helper scripts live in a session-scoped scratchpad. Copy them into the workspace or they disappear.

## Açık sorular

- Which destinations does the user actually use most: Instagram Reels, TikTok, YouTube Shorts / YouTube, WhatsApp, iMessage / AirDrop? Should every render automatically produce all the matching variants?
- HDR policy: SDR-only deliverables (recommended), or also an HLG HDR copy for iPhone-to-iPhone viewing (AirDrop / iMessage)?
- Tone-mapping look: the user should pick once from a side-by-side contact sheet of 3-4 of their own clips (mobius / hable / Apple avconvert). Measurements cannot decide taste.
- May the user run 'sudo xcodebuild -license accept' to unblock Homebrew (exiftool, media-info, ffmpeg-full, dovi_tool), or should everything stay brew-free (uv + ExifTool tarball)?
- Archive policy: is an external drive available for ProRes masters, or is 'originals + composition source + CRF 14-16 master' the archive?
- Loudness target for personal messaging deliverables: -14 LUFS (like social) or keep the current -16 LUFS in betikler/ustala.sh?
- Do the user's iPhone clips contain an APAC spatial-audio track (iPhone 16/17)? Probe one clip with ffprobe; bundled ffmpeg 6.0 cannot decode it.
- Current in-app limits on the user's devices (WhatsApp media / HD / Status length, TikTok upload size, iMessage compression) could not be read from the official help pages. Confirm them before tight deliveries.

## Şüpheci doğrulama

Most of the report holds up. I re-checked the decision-relevant facts on this M2 on 2026-10-05 and against primary sources, and they matched:
- **Bundled ffmpeg:** 6.0 has zscale, libvmaf, VideoToolbox and aac_at; ffprobe 4.4.1 reads Dolby Vision records.
- **Homebrew:** blocked by the Xcode license, and a DEVELOPER_DIR override does not help. Formula facts and licences check out: ffmpeg 9.0.2 slim vs ffmpeg-full keg-only; exiftool 13.55, dovi_tool 2.3.4, media-info 26.05, libvmaf 3.2.1.
- **Measurements I reproduced:**
  - tone-map values (hable 182 / reinhard 209 / mobius 218, Apple avconvert 148);
  - libvmaf behaviour (phone_model ignored, enable_transform works);
  - HyperFrames encoder and HDR internals.
- **Sources that check out:** the YouTube and Meta Reels ads specs, the ProRes data rates, BT.2408-7 §5.2 and WWDC20 10010.

What needs fixing:
1. **The WCAG flash counter is not conservative.** Run on the same logic, a full-contrast 5 Hz flash covering 30% of the frame passes with 0 transitions, and red flashes are never checked.
2. **The two helper scripts are already gone.** They were deleted from the scratchpad, and their install target betikler/ no longer exists.
3. **The workspace has moved on and partly contradicts the report:**
   - `medya sdr` defaults to hable, the darkest operator measured;
   - `meta-temizle` uses `-map 0 -c copy`, which the report itself warns against.
4. **Free disk is about 14-16 GiB,** not 18-21 GB.
5. **APAC is not fixed by any newer FFmpeg,** up to 9.0.
6. **Clearing the rotation matrix on stream copies would make portrait clips play sideways.**
7. **ffmpeg-normalize is maintained** (2026-09-02); its release date is not unclear.
8. **VideoToolbox speeds were limited by the synthetic source.** It does about 190-200 fps at 1080p here.

Better options the report missed:
- **Newer FFmpeg without sudo:** a notarized FFmpeg 9.0.2 static arm64 build (martin-riedl.de; VideoToolbox, zimg and libvmaf included).
- **HDR-to-SDR:** jellyfin-ffmpeg 8.1.3's Metal tone mapping, as another candidate for the look sheet.
- **Safe-zone checks:** the workspace's built-in Apple Vision tool instead of YuNet. YuNet is MIT (now verified) and remains the fallback.

The main pick is still right: bundled ffmpeg 6.0 plus avconvert and avmediainfo for delivery and QC today, with a version-pinned FFmpeg 9.x as a second binary later.

### Kontroller

- [confirmed] The bundled ffmpeg is 6.0 arm64 with zscale (zimg), tonemap, libvmaf, x264, x265, SVT-AV1, h264/hevc/prores_videotoolbox, aac_at and the listed QC filters. It lacks scale_vt, libplacebo, xpsnr, colordetect and the Dolby Vision bitstream filters. — Checked locally on 2026-10-05.
- `arac/ffmpeg -version` reports 6.0, configured with --enable-gpl --enable-version3 --enable-nonfree --enable-libzimg --enable-libvmaf --enable-libass --enable-libfreetype.
- Filters present: zscale, tonemap, libvmaf, scdet, freezedetect, blackdetect, silencedetect, ebur128, loudnorm, astats, signalstats, vfrdet, mpdecimate, photosensitivity, aphasemeter, vidstab, xfade, minterpolate, lut3d, nlmeans, cropdetect, blurdetect, blockdetect, siti.
- Filters absent: xpsnr, scale_vt, libplacebo, colordetect.
- Bitstream filters: only hevc_metadata and hevc_mp4toannexb, no dovi.
- Note: ffmpeg-static 5.3.0's package.json says binary-release-tag b6.1.1, yet the darwin-arm64 binary reports 6.0. (local: /Users/onurkaya/Projects/video/arac/ffmpeg -version/-buildconf/-filters/-encoders/-bsfs; node_modules/ffmpeg-static/package.json)
- [confirmed] ffprobe is 4.4.1 (@ffprobe-installer) and can identify iPhone Dolby Vision (DOVI configuration record, dv_profile, dv_bl_signal_compatibility_id). In 4.4, frame=pts_time is empty. — - Reports 'ffprobe version n4.4.1'; @ffprobe-installer/darwin-arm64 is 5.0.1.
- The binary contains the strings 'DOVI configuration record', 'dv_profile', 'dv_bl_signal_compatibility_id' and 'Display Matrix'.
- `-show_entries frame=pts_time,pkt_pts_time,best_effort_timestamp_time` printed only two values, so pts_time is not available in 4.4. (local: arac/ffprobe -version, byte scan of the binary, lavfi test)
- [confirmed] Homebrew is unusable until the Xcode license is accepted with sudo. — - `brew info exiftool` and `brew config` fail with 'You have not agreed to the Xcode license. Please resolve this by running: sudo xcodebuild -license accept'. `brew --version` (Homebrew 7.0.1) still works, so 'every brew command fails' is slightly overstated.
- Setting DEVELOPER_DIR=/Library/Developer/CommandLineTools does NOT get around it: brew filters its environment.
- /Library/Developer/CommandLineTools exists, so `sudo xcode-select -s /Library/Developer/CommandLineTools` is a valid fix, but it still needs sudo.
- Other Xcode shims fail the same way: /usr/bin/python3 and /usr/bin/strings.
- /usr/bin/perl 5.34.1 works. python3 on PATH is the python.org 3.14 build with numpy 2.5.3 and works. (local commands 2026-10-05)
- [confirmed] Homebrew 'ffmpeg' 9.0.2 depends only on dav1d, lame, libvmaf, libvpx, openssl@3, opus, sdl2-compat, svt-av1, x264, x265 and xz. It has no zimg and no libass/freetype. — formulae.brew.sh JSON (generated 2026-10-04): stable 9.0.2, GPL-3.0-or-later, exactly those runtime dependencies, keg_only false. Bottles exist for arm64_golden_gate, arm64_tahoe and arm64_sequoia. (https://formulae.brew.sh/api/formula/ffmpeg.json)
- [uncertain] ffmpeg-full 9.0.2 is keg-only and adds zimg, libplacebo, whisper.cpp, libass, rubberband, libvidstab, frei0r, jpeg-xl and tesseract. Its libplacebo filter is usable on macOS only with molten-vk. — Formula facts are confirmed: keg_only true; all of those dependencies are listed; arm64_golden_gate bottles exist; --enable-libplacebo and --enable-libzimg are passed.

Usability is not confirmed:
- The formula does NOT pass --enable-vulkan. FFmpeg master's configure autodetects vulkan and sets libplacebo_filter_deps="libplacebo", so the filter is probably built.
- libplacebo 7.360.1 depends on little-cms2, shaderc and vulkan-loader, and not on molten-vk.
- Whether the Vulkan loader finds the MoltenVK ICD on macOS 27 is untested. (https://formulae.brew.sh/api/formula/ffmpeg-full.json ; https://raw.githubusercontent.com/Homebrew/homebrew-core/main/Formula/f/ffmpeg-full.rb ; https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/configure ; https://formulae.brew.sh/api/formula/libplacebo.json ; https://formulae.brew.sh/api/formula/molten-vk.json (1.4.2, Apache-2.0))
- [confirmed] FFmpeg 9.0 'Lei' was released 2026-08-04 and 9.0.2 is current. 9.0 added a Dolby Vision multi-layer bitstream filter, scale_vt arrived in 6.1 and colordetect in 8.0. — - jbkempf blog dated 2026-08-04 announces 9.0 'Lei'.
- ffmpeg.org/download lists 9.0.2 'Lei' (2026-09-18).
- Changelog lines: 9.0 'Bitstream filter to split Dolby Vision multi-layer HEVC'; 6.1 'scale_vt filter for videotoolbox'; 8.0 'Colordetect filter'.
- The 6.1 vf_scale_vt.c source already has color_matrix, color_primaries and color_transfer options (VTPixelTransferSession). (https://jbkempf.com/blog/2026/ffmpeg-9.0/ ; https://ffmpeg.org/download.html ; https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog ; https://raw.githubusercontent.com/FFmpeg/FFmpeg/release/6.1/libavfilter/vf_scale_vt.c)
- [refuted] APAC decoding is one of 6.0's gaps, implying a newer FFmpeg would fix it. — - No changelog entry from 6.1 to 9.0 mentions an Apple APAC / Positional Audio decoder.
- The 'apac' decoder in 6.0 is 'Marian's A-pac audio', which is unrelated.
- So upgrading FFmpeg does not help. Map the stereo AAC track, or decode APAC through AVFoundation (avconvert or Swift).
- Medium confidence: this rests on a changelog scan, not a test file. (https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/Changelog ; local: arac/ffmpeg -decoders)
- [confirmed] Tone-map operator numbers for HLG 75% (reference white), as 8-bit Y: hable 182, mobius 218, reinhard 209. HyperFrames --sdr uses zscale=t=linear:npl=100,tonemap=hable:desat=0. — - Re-ran a lavfi grey frame (10-bit code 721 = 75% HLG, BT.2020/arib-std-b67) through the bundled ffmpeg: YAVG hable 182, mobius 218, reinhard 209.
- Analytic check: 75% HLG -> 203 nits; on output, zimg applies the BT.1886 inverse EOTF (gamma 1/2.4). That predicts 181.5 for hable and 218.2 for mobius.
- The HyperFrames code returns `${setTags}zscale=t=linear:npl=100,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv`. (local test 2026-10-05; node_modules/hyperframes/dist/chunk-LVXNXV7G.js)
- [confirmed] avconvert H.264 presets convert HLG to BT.709 SDR (reference white Y about 148) and HEVC presets keep HLG. Its default metadata filter strips location, recording date and device info. This matches WWDC20 10010. — - Re-ran a synthetic HLG HEVC Main10 file through `avconvert -p PresetHighestQuality`: output h264, yuv420p, bt709/bt709/bt709, YAVG 148 (mobius on the same file: 218).
- The man page (macOS February 2025) says --disableMetadataFilter keeps 'location of the video, time when the video was recorded, video capture device information', which are otherwise removed.
- PresetPassthrough exists.
- WWDC20 transcript: HEVC and ProRes presets preserve HDR; use H.264 presets to convert to SDR. AVFoundation export supports HLG and HDR10, not Dolby Vision.
- Missed by the researcher: avconvert also has --multiPass. (local avconvert test + man avconvert; https://developer.apple.com/videos/play/wwdc2020/10010/)
- [confirmed] With no metadata, FFmpeg tonemap assumes an HLG peak of 10 x 100 cd/m2 (ff_determine_signal_peak). — Source: `if (!peak) peak = in->color_trc == AVCOL_TRC_SMPTE2084 ? 100.0f : 10.0f;` with the comment 'otherwise assume HLG with reference display peak 1000'. (https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavfilter/colorspace.c)
- [confirmed] VideoToolbox -q:v works only on Apple Silicon, with quality = q/100. — In videotoolboxenc.c, vtenc_qscale_enabled() returns !TARGET_OS_IPHONE && TARGET_CPU_ARM64. The quality value is global_quality / (FF_QP2LAMBDA*100) and is written to kVTCompressionPropertyKey_Quality. (https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/libavcodec/videotoolboxenc.c)
- [uncertain] VideoToolbox encodes 1080p at 88-105 fps versus 20 fps for x264 slow. — - On this M2 with a cheap testsrc2 source, 600 frames took 3.01 s with h264_videotoolbox -q:v 65 (about 200 fps) and 3.23 s with hevc_videotoolbox (about 186 fps).
- x264 slow did 150 frames in 1.88 s (about 80 fps) on that easy content.
- The researcher's figures were probably limited by the CPU-heavy synthetic source (fractal plus grain). The ranking holds; the absolute speeds depend on the source. (local timing 2026-10-05)
- [confirmed] libvmaf in 6.0: phone_model=1 is silently ignored, model=version=vmaf_v0.6.1\\:enable_transform=true works, and the NEG model is built in. — - On a synthetic distorted/reference pair: default 59.53, phone_model=1 59.53 (identical), enable_transform 79.48, vmaf_v0.6.1neg 58.42.
- `-h filter=libvmaf` marks phone_model as deprecated: "use model='enable_transform=true'". (local test 2026-10-05)
- [confirmed] VMAF FAQ: the default model assumes a 1080p HDTV viewed at 3H; upsample lower-resolution files before comparing. — The FAQ text quotes a 1080p HDTV in a living-room environment at three times screen height, and says to upsample (e.g. 480p) to 1080p rather than compare native-resolution scores. (https://github.com/Netflix/vmaf/blob/master/resource/doc/faq.md)
- [confirmed] ProRes target data rates: 1080p30 HQ 220 Mb/s (99 GB/h); 4K (3840) 30p Proxy 182 / LT 410 / HQ 884 Mb/s (398 GB/h). — Apple ProRes White Paper (April 2022), p.20:
- 1920x1080 60i/30p: Proxy 45 (20 GB/h), LT 102 (46), 422 147 (66), HQ 220 (99), 4444 330.
- QFHD 3840x2160 30p: Proxy 182, LT 410 (185), 422 589, HQ 884 (398). (https://www.apple.com/final-cut-pro/docs/Apple_ProRes.pdf)
- [confirmed] YouTube upload spec values, and Shorts up to 3 min since 2024-10-15. — - Google help page: moov at front; 'No Edit Lists (or the video might not get processed correctly)'; progressive; High profile; 2 consecutive B-frames; closed GOP of half the frame rate; CABAC; 4:2:0.
- Audio: AAC-LC (or Opus) 48 kHz, stereo 384 kbps.
- SDR bitrates: 1080p 8/12 Mb/s; 2160p 35-45/53-68 Mb/s. HDR: 1080p 10/15 Mb/s; 2160p 44-56/66-85 Mb/s.
- Shorts: up to 3 min for uploads after 2024-10-15.
- The 'max 1080p upload' for Shorts was NOT found on that page. (https://support.google.com/youtube/answer/1722171 ; https://support.google.com/youtube/answer/15424877)
- [confirmed] Meta Reels ads: 1440x2560 recommended, 0-15 min, 4 GB or less, AAC 128 kb/s or more. Keep 14% top, 35% bottom and 6% sides clear. — The Meta ads guide (served in Turkish) lists 1440x2560, 9:16, max 4 GB, 0 to 15 minutes, H.264, square pixels, fixed frame rate, progressive, stereo AAC at 128 kbps or more. Safe zone: at least 14% top, 35% bottom and 6% sides. (https://www.facebook.com/business/ads-guide/update/video/instagram-reels)
- [refuted] The WCAG 2.3.1 counter (flashcount.py) is validated, and full-frame averaging makes it conservative. — - I re-ran the script's exact logic on synthetic 1080x1920 clips with a full-contrast 5 Hz flash:
  - flash covering 30% of the frame: transitions=0, PASS (false negative)
  - flash covering 50% or 100%: 5 flashes/s, FAIL
- Cause: it averages gamma-encoded Y' (YAVG) and only then applies ^2.4, so partial-area flashes are diluted. Black/white flashes are detected only when they cover about 38% of the frame or more.
- WCAG's area threshold is 25% of any 10-degree field (a 341x256 px rectangle at 1024x768), so a 30%-of-frame flash clearly counts.
- It also has no red-flash test, which WCAG requires (R/(R+G+B) >= 0.8, chromaticity change > 0.2). (https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html ; local re-test 2026-10-05)
- [refuted] The two helper scripts live in the scratchpad and can be installed with `cp .../scratchpad/qc/{flashcount.py,xcorr_lag.py} .../betikler/`. — - Both files were present at about 01:00. By about 01:16 on 2026-10-05 the scratchpad had been emptied (only claude-config-reference.md remains), so the scripts are gone.
- /Users/onurkaya/Projects/video/betikler/ does not exist either; the workspace was reorganised into medya/komutlar/*.py.
- I read both scripts before they were deleted. Corrections below summarise their logic and the fixes needed. (local ls 2026-10-05)
- [refuted] The workspace state the findings rely on: betikler/ustala.sh with a -16 LUFS gain + alimiter, used together with this report's advice. — - The current workspace has medya/komutlar/ustala.py (default --hedef -16, alimiter loop), denetle.py, senkron.py, incele.py and donustur.py.
- donustur.py `medya sdr` defaults to tonemap=hable. The report measured hable as the darkest operator.
- `medya meta-temizle` runs `-map 0 ... -c copy`, which the report's own 'avoid' list warns against (mebx timed-metadata tracks and APAC get copied).
- There is no betikler/ directory. (local: /Users/onurkaya/Projects/video/medya/komutlar/{ustala,donustur,denetle}.py, yetenekler.toml)
- [refuted] About 18-21 GB of free disk. — `df -h /System/Volumes/Data` showed 15, then 14, then 16 GiB available between about 00:59 and 01:18 on 2026-10-05, changing as parallel jobs wrote and cleaned up. Measured usage: ortamlar/ses 1.2G, .uv 1.5G, modeller 1.8G, .venv 170M, node_modules 195M. Plan for about 14 GiB. (local df/du 2026-10-05)
- [confirmed] Package facts: pymediainfo 7.0.1 (Feb 2025, MIT, universal2 wheel with libmediainfo bundled), ffmpeg-quality-metrics 3.12.2 (2026-09-17, MIT), PySceneDetect 0.7.1 (2026-07-22, BSD-3, Python 3.10-3.13) and its detector defaults. — - pymediainfo 7.0.1: macosx_10_10_universal2 wheel, 6.98 MB, uploaded 2025-02-12; requires Python >=3.9. No newer release, so maintenance is slow.
- ffmpeg-quality-metrics 3.12.2: wheel uploaded 2026-09-17T18:14:49; requires Python >=3.10.
- PySceneDetect 0.7.1: uploaded 2026-07-22. Local `--help` defaults: min-scene-len 0.6s, detect-content 27, detect-threshold 12, detect-hash 0.395, detect-hist 0.05. (https://pypi.org/pypi/pymediainfo/json ; https://pypi.org/pypi/ffmpeg-quality-metrics/3.12.2/json ; https://pypi.org/pypi/scenedetect/json ; local scenedetect --help)
- [refuted] ffmpeg-normalize 1.42.0 has an unclear release date. — The 1.42.0 wheel and sdist were uploaded 2026-09-02 (MIT, Python >=3.10), so the project is actively maintained. (https://pypi.org/pypi/ffmpeg-normalize/1.42.0/json)
- [confirmed] ExifTool 13.55 (Artistic-1.0-Perl OR GPL-1.0-or-later); FAQ #32 safe strip; runs on system perl. Also dovi_tool 2.3.4 (MIT), media-info 26.05 (BSD-2) and libvmaf 3.2.1 (BSD-2-Clause-Patent). — - Homebrew JSON (2026-10-04): exiftool 13.55 with exactly that licence; source tarball Image-ExifTool-13.55.tar.gz.
- FAQ #32 'How do I safely delete all metadata from a file?' gives `exiftool -all= --icc_profile:all -tagsfromfile @ -colorspacetags`.
- /usr/bin/perl 5.34.1 runs without the Xcode license.
- dovi_tool 2.3.4 (MIT), media-info 26.05 (BSD-2-Clause) and libvmaf 3.2.1 (BSD-2-Clause-Patent) all have arm64_golden_gate bottles. (https://formulae.brew.sh/api/formula/exiftool.json ; https://exiftool.org/faq.html ; https://formulae.brew.sh/api/formula/dovi_tool.json ; https://formulae.brew.sh/api/formula/media-info.json ; https://formulae.brew.sh/api/formula/libvmaf.json)
- [confirmed] The .venv's OpenCV 5.0 has no CascadeClassifier, so use YuNet, whose licence was not verified. — - cv2 5.0.0: CascadeClassifier=False, FaceDetectorYN=True.
- YuNet licence: opencv_zoo says 'All files in this directory are licensed under MIT License'. A newer face_detection_yunet_2026may.onnx (dynamic input) is the default.
- New risk: the .venv has BOTH opencv-python and opencv-python-headless 5.0.0.93, a combination OpenCV packaging advises against. (local .venv; https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- [confirmed] aac_at silently caps stereo 48 kHz at 320 kb/s. — The cap is real but not silent. A request for -b:a 384k logs '[aac_at] Bitrate 384000 not allowed; changing to 320000', while the output stream header still shows 384 kb/s. Measure the actual bitrate with ffprobe. (local test 2026-10-05)
- [refuted] T3: with -c copy, clear the display matrix with -metadata:s:v:0 rotate=0 (6.0). — - Stream copy does not rotate the pixels, so on a portrait iPhone clip clearing or zeroing the matrix makes the copy play sideways.
- Only re-encoding with autorotate (the default) bakes the rotation in and drops the matrix.
- ffmpeg 6.0 also has the proper `-display_rotation` and `-display_hflip` options (shown in `-h long`), so the deprecated rotate tag is not needed. (local: arac/ffmpeg -h long)
- [confirmed] HyperFrames internals: hdrMode auto/--sdr/--hdr; quality presets draft ultrafast 28, standard medium 18, high/delivery slow 15, looks CRF 16; libx264 -bf 0, aq-mode=3, deblock 1,1, bt709 VUI; provenance tags; VFR resampled with -fps_mode cfr -r. — - render-4PBKSNC3.js: QUALITY_ALIASES {looks: standard crf 16, delivery: high}; hdrMode: args.sdr ? 'force-sdr' : args.hdr ? 'force-hdr' : 'auto'.
- chunk-CMH5CSTH.js: ENCODER_PRESETS; `if (codec === "h264" ...) args.push("-bf","0")`; aq-mode=3:aq-strength=0.8:deblock=1,1; renderProvenanceArgs with +use_metadata_tags; resampleVfrToCfr pushes '-fps_mode cfr -r'.
- Log strings confirmed: '[Render] SDR forced by --sdr flag', 'HDR auto-promotion triggered by'. (local: node_modules/hyperframes/dist (0.8.124, Apache-2.0))
- [confirmed] ITU-R BT.2408-7: HLG 75% is reference white (203 cd/m2), and display-light down-mapping keeps lowlights and midtones while compressing highlights. — Report BT.2408-7 (09/2023), §5.2: display-light methods attempt to preserve 'the lowlights and midtones'; down-mapping follows 'a complementary tone-curve ... over the lower and middle signal ranges, with compressed highlights filling the upper SDR signal range'. The 75% HLG marker is the reference level. (https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2408-7-2023-PDF-E.pdf (copy the researcher downloaded))
- [uncertain] QCTools is GUI-centric and not agent-drivable. — MediaArea offers QCTools 1.4.1 with a separate qcli command-line download for macOS, so a CLI does exist. It is x86_64-only (Rosetta), so leaving it out is still reasonable. (https://mediaarea.net/QCTools/Download/Mac_OS)
- [uncertain] Many iPhone clips are 30 fps content in a 60 fps container, which mpdecimate reveals. — Not verified. iPhone Auto-FPS in low light usually lowers the capture rate and produces variable timestamps (VFR, which vfrdet catches) rather than duplicate frames. Duplicates are more typical of screen recordings and re-encodes. Low confidence either way; test on the user's real clips. (reasoning only; no primary source fetched)
- [uncertain] Platform numbers taken from secondary sources: Reels up to 20 min, TikTok safe zone 12.5%/34%/11%, Shorts centre 4:5, Instagram 3:4 grid crop, TikTok in-app size limits. — These could not be re-verified because the web-search budget was exhausted. Only the Meta Reels ads safe zone and the YouTube specs were confirmed from primary pages. (n/a)

### Düzeltmeler (seçimlerin önüne geçer)

- **Photosensitivity (WCAG 2.3.1) check**: Rewrite the flash counter and integrate it into `medya denetle`:
- Linearise before averaging: decode a downscaled RGB proxy (e.g. scale=96:-2), convert to relative luminance per pixel (sRGB/BT.709 linear, Y=0.2126R+0.7152G+0.0722B).
- Count general flashes per tile or sliding window. Use a window of about 10% of the frame for phone viewing, which is conservative versus WCAG's 25% of a 10-degree field.
- Add the red-flash rule (R/(R+G+B) >= 0.8 and chromaticity change > 0.2).
- FAIL if any window has more than 3 flashes in 1 s.
- Keep the ffmpeg photosensitivity filter as a warning only.
- Regression tests: 5 Hz at 30% / 50% / 100% area must all FAIL; 3 Hz must PASS.
- Optional cross-check: EA IRIS (BSD-3-Clause, CLI, CSV/JSON output). Heavy to build: CMake + vcpkg + OpenCV, low activity (7 commits). — gerekçe: Re-test: the current logic PASSES a full-contrast 5 Hz flash covering 30% of the frame (0 transitions). Its 'conservative' claim is false, and red flashes are not checked.
- **QC helper scripts (flashcount.py, xcorr_lag.py)**: Do not cp them from the scratchpad: they were deleted around 01:16 on 2026-10-05, and betikler/ no longer exists. Re-implement both inside medya/komutlar (denetle.py / senkron.py).

xcorr_lag logic: 8 kHz mono, FFT cross-correlation of 3 s windows at 10/50/90% of the song, ±500 ms search; PASS when |lag| <= 5 ms and spread <= 2 ms.

Add:
- a --song-in offset (the montage may start mid-song);
- checkpoints only inside the overlap that is not fading (renders are often shorter than the song);
- GCC-PHAT weighting, so a periodic beat cannot make it lock onto a neighbouring beat;
- a confidence value (peak-to-second-peak ratio). — gerekçe: The scripts are gone. Also, the drift check assumes the song starts at 0 and runs to 90% of its length inside the render; real montages violate both.
- **Transcode/QC engine upgrade path**: Keep the bundled ffmpeg 6.0 as the default QC engine; it is verified. The upgrade route is a second, version-pinned binary (e.g. arac/ffmpeg9), checked with -buildconf. Options, in order:
1. Martin Riedl's static FFmpeg 9.0.2 macOS arm64 build: no Homebrew and no sudo. It is a signed zip with SHA256; its codec list includes h264/hevc/prores_videotoolbox and aac_at, and it bundles zimg, libvmaf, libass/freetype, x264, x265 and SVT-AV1.
2. Homebrew ffmpeg-full 9.0.2, only after `sudo xcode-select -s /Library/Developer/CommandLineTools` (or accepting the license), and only for libplacebo. — gerekçe: The report says newer FFmpeg is blocked until sudo. A notarized arm64 9.0.2 static build exists (release 2026-09-20). It is third-party: verify the SHA256 and the configure line; the licence is GPL through its components.
- **HDR (HLG/DV 8.4) to SDR look selection**: Keep the side-by-side contact sheet, with the default set to mobius until the user chooses.

Add as candidates:
- Apple avconvert H.264 preset (darker: reference white Y 148, re-verified);
- scale_vt with color_transfer=bt709 (FFmpeg 6.1+, Apple VTPixelTransferSession);
- jellyfin-ffmpeg 8.1.3-1 portable macarm64 (31.4 MB, GPL, 2026-09-27): Metal-based tone mapping with tuning and DV P5 support, without MoltenVK.

Also change the workspace's `medya sdr` default from hable to the chosen operator. — gerekçe: Re-measured: hable 182, reinhard 209, mobius 218, avconvert 148. The workspace currently defaults to the darkest ffmpeg operator, the opposite of the report's own recommendation.
- **Metadata/GPS stripping (current workspace command)**: In donustur.py `meta-temizle`, replace `-map 0 ... -c copy` with `-map 0:v:0 -map 0:a:0` (the AAC index from incele), or keep `-map 0` plus `-map -0:d -map -0:t`. Then verify with `exiftool -a -G1 -s -ee` and `ffprobe -show_entries format_tags:stream_tags`. — gerekçe: -map 0 copies iPhone mebx timed-metadata tracks and extra (APAC) audio tracks, as the report's own 'avoid' list says.
- **Rotation handling (T3)**: Delete the advice to clear the display matrix on -c copy outputs. Instead:
- Deliverables are always re-encoded with autorotate, then QC1 confirms no Display Matrix.
- Stream copies keep their matrix.
- If an override is truly needed, ffmpeg 6.0 has `-display_rotation` (input option). — gerekçe: Zeroing the matrix on a stream copy makes portrait phone clips play sideways.
- **APAC spatial audio**: State that no FFmpeg release up to 9.0 decodes Apple APAC; the 6.0 'apac' decoder is Marian's A-pac, which is unrelated. Always map the stereo AAC track. If a clip has only APAC, decode it through AVFoundation (avconvert preset or a Swift AVAssetReader command in arac/medya-apple). — gerekçe: The report implies newer FFmpeg would fix this; the changelog through 9.0 shows no such decoder.
- **Disk budget**: Use about 14 GiB free, as measured during this check (14-16 GiB, fluctuating), not 18-21 GB.
- That is roughly 9 min of 1080p30 ProRes HQ or 2 min of 4K30 HQ.
- Enforce a size projection before any render or transcode and keep 5 GB free.
- Clean scratch renders; the scratchpad alone held 2.4 GB before it was wiped. — gerekçe: Measured with df/du during verification.
- **Automatic safe-zone check (T6)**: Use the built-in Apple Vision path the workspace already has: `arac/medya-apple analiz <video> out.json` gives faces, humans and saliency boxes, top-left origin, normalised. Use YuNet only as a cross-platform fallback (now verified MIT; prefer face_detection_yunet_2026may.onnx). — gerekçe: No model download is needed, it is accelerated on this Mac, and it is already compiled with the Command Line Tools.
- **Loudness tooling**: ffmpeg-normalize 1.42.0 (MIT, uploaded 2026-09-02) is maintained. It can replace hand-parsing loudnorm JSON, run through arac/uv tool and pointed at arac/ffmpeg via FFMPEG_PATH.

Whichever tool is used:
- measure the ENCODED file;
- target TP -1.5 dBTP before AAC encoding;
- check `normalization_type: linear`;
- note aac_at logs a bitrate clamp (requests above 320k become 320k) while the header still shows the requested rate. — gerekçe: Corrects the 'release date unclear' note and the 'silent' clamp.
- **Encoder speed guidance**: Restate the VideoToolbox speeds as at least 190-200 fps for 1080p on this M2 when the source is cheap; the 88-105 fps figure was limited by the synthetic source. Keep the quality ranking: x264/x265 win at low bitrates, VideoToolbox is close at 20 Mb/s or more. — gerekçe: Local timing: 600 frames in 3.0 s (H.264 VT) and 3.2 s (HEVC VT).
- **avconvert description**: Add the --multiPass option ('higher quality multi-pass encode') and --disableSpatialConversion to the description. Also note that only one video and one audio track survive, and which audio track it picks from APAC+AAC iPhone files is untested. — gerekçe: Read from the man page (macOS February 2025) and --help.

### Eksik bulunanlar

- A playback-compatibility gate using Apple's own decoders (the same stack iOS uses). ffmpeg decodes almost anything, so it is a weak compatibility test. Options: a decode pass via AVAssetReader in arac/medya-apple, `avmediainfo out.mp4 --brief`, and `qlmanage -t` thumbnail generation.
- QC filters already in bundled ffmpeg 6.0 but unused:
- cropdetect: unintended black bars after 16:9 to 9:16 reframes;
- blurdetect: soft or out-of-focus phone shots;
- blockdetect: compression blocking in size-capped WhatsApp copies;
- siti: ITU-T P.910 complexity, used to pick bitrates.
- Target-quality encoding for size-capped deliverables: ab-av1 0.11.7 (MIT, Homebrew bottle for arm64_golden_gate, after the Xcode fix). It runs crf-search to a minimum VMAF or XPSNR under a max encoded size, and works with libx264/libx265/SVT-AV1.
- Per-shot A/V sync for shots that keep their own camera audio (laughter, speech). Cross-correlate each shot's audio in the render against its source clip; this catches VFR-conform or trim slips. The workspace denetle has an 'av' check, but the report's QC8 covers only the slate and the song.
- Work deliverables are missing from the presets:
- alpha video: ProRes 4444 via prores_videotoolbox; HEVC with alpha via hevc_videotoolbox -alpha_quality or avconvert PresetHEVC1920x1080WithAlpha; VP9 yuva420p WebM for browsers;
- GIF / animated WebP / APNG for docs and Slack via ffmpeg palettegen/paletteuse (gifski is AGPL-3.0, so flag it);
- LinkedIn, X, Slack and GitHub-README size/length presets;
- cover and thumbnail export (YouTube 1280x720 under 2 MB; Reels cover inside the 3:4 grid crop).
- Photo delivery caveat: `exiftool -all=` removes Apple MakerNotes, which Apple's legacy HDR gain-map rendering appears to rely on (low-medium confidence; Apple's 'Applying Apple HDR effect to your photos' page could not be read). Decide per photo whether to keep HDR (strip GPS/serials selectively) or flatten to SDR (sips/ffmpeg) before a full strip.
- iPhone Slo-mo originals: the user's slow-motion ramp is stored as metadata that ffmpeg ignores. Detect 120/240 fps clips at ingest and decide the ramp in the edit (low confidence on the exact storage).
- Environment gotchas to record in CLAUDE.md:
- Until the Xcode license is accepted, /usr/bin/python3, /usr/bin/strings and other xcrun shims fail. Scripts and hooks must use .venv/bin/python or the python.org python3 (which has numpy).
- The .venv has both opencv-python and opencv-python-headless 5.0.0.93 installed; keep only one.
- HDR copy for iPhone recipients needs its own QC row: hvc1 tag, yuv420p10le, bt2020/arib-std-b67/bt2020nc, and a check that the iPhone shows the HDR badge. VideoToolbox writes no MaxCLL or mastering metadata (HLG does not need it).
