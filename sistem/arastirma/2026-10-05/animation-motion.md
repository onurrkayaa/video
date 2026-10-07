# Animasyon ve hareketli grafik — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Evidence dates run from 2025-05 to 2026-10-05. Live checks were made with npm, PyPI, the Homebrew API, GitHub release pages and official docs. Read-only local checks were also run.

BOTTOM LINE: Keep HyperFrames as the hub. It is Apache-2.0, already installed (0.8.124), built for agents and has 21 skills. Use it for every 2D motion graphic, every transition or zoom, and as the renderer for SVG, GSAP, Lottie and Three.js. Add small specialists only where they are clearly better:
- Manim CE 0.21.0 with the [typst] extra (no LaTeX) for math and algorithm explainers.
- Blender 5.2.2 LTS, run headless, for real 3D (Cycles uses the M2's Metal GPU).
- VHS 0.12.1 or asciinema 3.2.1 + agg 1.9.0 for terminal videos.
- Playwright 1.63 page.screencast for scripted product-demo capture.
- gifski 1.34 for GIFs.

Remotion 4.0.532 is excellent, but it is free only for individuals and for companies with 3 or fewer employees. Motion Canvas, Revideo and Theatre.js are stale or only partly maintained. Rive needs an account, and its exports have been paid since 2025-10-20.

PREREQUISITE FOUND: every brew command currently fails with "You have not agreed to the Xcode license" (verified). The user must run `sudo xcodebuild -license accept` once. Until then, use prebuilt binaries (agg, vhs). Compiling works with DEVELOPER_DIR=/Library/Developer/CommandLineTools (verified clang).

DECISION TABLE (task -> tool):
- Kinetic type, title card, logo sting, lower third, callout -> HyperFrames + GSAP (motion-graphics skill, registry).
- Transitions, punch-in zoom, Ken Burns, camera moves, speed ramps on footage -> HyperFrames (hyperframes-keyframes skill + transitions catalog, motion-blur component). Use ffmpeg minterpolate to prepare slow motion.
- Product launch or promo video from a URL -> HyperFrames product-launch-video skill (capture --skip-vision).
- Web-app demo or walkthrough -> scripted Playwright screencast at 2x DPR -> HyperFrames adds zoom-to-click, cursor polish, device frame and music.
- macOS app demo -> screencapture -v -C -k -> HyperFrames.
- iOS app demo -> xcrun simctl io recordVideo (after the Xcode license is accepted) -> HyperFrames.
- App Store preview -> HyperFrames at 886x1920 / 30 fps -> ffmpeg H.264 High L4.0 11 Mbps + AAC 256k stereo -> ffprobe checks.
- Code walkthrough or PR/changelog video -> HyperFrames code-typing / code-diff / code-morph (Shiki Magic Move) blocks, or the pr-to-video skill.
- Terminal demo -> VHS for a scripted demo; asciinema + agg for a real session.
- Math, algorithm or data-structure explainer -> Manim CE + Typst, rendered with alpha and composed in HyperFrames.
- Topic explainer from text -> HyperFrames faceless-explainer skill.
- Chart or data animation -> HyperFrames data-chart blocks and the dataviz-countup blueprint.
- SVG logo draw-on, morph or path animation -> GSAP DrawSVG/MorphSVG/MotionPath (free since 3.13) in HyperFrames, with SVGO cleanup.
- Lottie for app UI -> dotLottie runtimes (themes and state machines; an account-free stand-in for Rive) or airbnb lottie-ios / lottie-android / lottie-react-native. Author with text-to-lottie or dotlottie-js, then validate and render via HyperFrames.
- Telegram or WhatsApp stickers (personal use) -> python-lottie for TGS, or HyperFrames png-sequence -> img2webp or VP9 WebM with alpha.
- UI-grade 3D (logo spin, particles, device) -> Three.js 0.186 in HyperFrames, with Poly Haven CC0 assets.
- Photoreal or stylized 3D, Geometry Nodes, Grease Pencil -> Blender -b -P script (Cycles Metal) -> PNG sequence -> ffmpeg or HyperFrames.
- README or PR animation -> attach an MP4 if possible (GitHub limit: 10 MB on free plans); otherwise gifski + gifsicle, or HyperFrames --format gif at 15 fps.
- Transparent overlay for other editors -> HyperFrames --format mov (ProRes 4444) or webm.
- Existing Remotion code -> remotion-to-hyperframes skill. Use Remotion itself only when licensed.

VERIFY EVERYTHING MEASURABLY: contact sheets read with the Read tool, onion-skin keyframe shots, framemd5 determinism checks, scene-cut versus beat-frame alignment (max 1 frame off), an A/V flash+click sync test, a VMAF quality gate, and ffprobe spec checks.

## Seçimler

### Default engine for all 2D motion graphics, animation and video composition: kinetic type, UI/product animation, transitions, zooms, explainers, PR and launch videos. It is also the renderer for SVG, GSAP, Lottie and Three.js content.
- **Seçim:** HyperFrames 0.8.124 (already installed; pin the exact version)
- Alternatifler: Remotion (React; license conditional). Manim for math. Blender for heavy 3D. The remotion-to-hyperframes skill ports Remotion code.
- Neden: Apache-2.0 and built for agents.
- Compositions are plain HTML + CSS with a single paused GSAP timeline. Adapters cover Lottie/dotLottie, Three.js, Anime.js, CSS keyframes, WAAPI and TypeGPU.
- Rendering is deterministic: it seeks each frame in headless Chrome 152, then FFmpeg encodes.
- Outputs: mp4, webm (alpha), mov (ProRes 4444 alpha), gif, png-sequence (RGBA) and hls. --resolution 4k raises device pixel ratio for crisp text. --video-frame-format png keeps UI recordings sharp.
- The 394-item registry includes transitions, a motion-blur component, cinematic-zoom, code-typing/diff/morph/highlight/scroll/3d-extrude, 24 terminal/editor window themes, charts and device showcases.
- Installed skills hold real motion-design knowledge: rules, 22 blueprints (cursor-ui-demo, camera-journey, zoom-out-workspace-reveal...), a transition catalog and motion-blur guidance.
- Agent QA commands: check (lint + runtime + layout), snapshot (contact sheets), keyframes --shot (onion skin), compare and timeline.
- 2026 comparisons report that agents do better writing HTML+GSAP than Remotion TSX. There is no company-size license limit.
- Lisans: kod Apache-2.0 (CLI and engine). GSAP used inside compositions is under the GSAP Standard 'no charge' license. · ağırlık n/a. Optional TTS uses Kokoro-82M (not part of this pick). · ticari: yes
- Apple Silicon: Native arm64 chrome-headless-shell 152. --browser-gpu probes the host GPU for WebGL and falls back to SwiftShader. Experimental fast capture is on by default on macOS with a hardware GPU (about 2x faster). --gpu uses VideoToolbox encoding. Each worker is a Chrome process of about 256 MB.
- Kurulum: Already installed. To pin: npm i -D hyperframes@0.8.124 (0.8.125 shipped on 2026-10-04). Every shell: source /Users/onurkaya/Projects/video/ortam.sh, which sets HYPERFRAMES_NO_TELEMETRY=1 and DO_NOT_TRACK=1. After any upgrade, run hyperframes skills to resync the skills.
- Disk: ~390 MB · bakım: Very active. The npm package was created 2026-03-23 and had 479 versions by 2026-10-04, several per day. About 56.7k GitHub stars. Pin the version and upgrade deliberately.
- Ajan kullanımı: 1. Write index.html: root data-composition-id / data-duration / data-fps; clips with class=clip and data-start/data-duration; window.__timelines[id] = gsap.timeline({paused:true}).
2. Add registry items: hyperframes add code-morph --dir <proj> --no-clipboard.
3. Check: hyperframes check <proj>.
4. Look: hyperframes snapshot <proj> --at 1,2.5,4 --describe false, then Read the contact sheet. hyperframes keyframes <proj> --selector '#logo' --shot k.png shows the motion path and easing.
5. Render: hyperframes render <proj> -o renders/x.mp4 [--format mov|webm|gif|png-sequence] [--video-bitrate 8M] [--resolution 4k].
6. Human review: hyperframes preview <proj> for timeline scrubbing.
7. Vendor gsap, lottie and three files locally instead of the CDN URLs used in skill examples.
- Güven: high · kaynaklar: https://github.com/heygen-com/hyperframes, https://registry.npmjs.org/hyperframes, https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/registry.json, https://arceapps.com/blog/hyperframes-vs-remotion-2026/, https://motionflare.ai/compare/hyperframes-vs-remotion

### React/TypeScript alternative: reuse real app UI components in videos, data-driven templates, a large ecosystem (@remotion/three, @remotion/lottie, transitions, captions)
- **Seçim:** Remotion 4.0.532, only when the license conditions are met
- Alternatifler: HyperFrames (Apache-2.0) covers the same ground without the license limit.
- Neden: The most mature code-to-video framework.
- Official agent skills: npx skills add remotion-dev/skills.
- Frame-exact rendering, ProRes 4444 alpha output, studio preview.
- The license is source-available, not OSI. It is free for individuals (commercial use included), for-profit organizations with up to 3 employees, non-profits and evaluation. Larger companies need a paid Company License; the pricing page lists Creators at about $25/seat/month and Automators at $0.01/render with a $100/month minimum.
- Telemetry: server-side rendering sends it only when licenseKey is set. Client-side rendering APIs always send it.
- Lisans: kod Remotion License (source-available) · ağırlık n/a · ticari: conditional
- Apple Silicon: Native darwin-arm64 compositor with bundled ffmpeg. Downloads its own Chrome Headless Shell.
- Kurulum: npx create-video@latest (about 278 MB node_modules, about 205 packages per a 2026 benchmark). Skills: DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 npx skills add remotion-dev/skills.
- Disk: ~400 MB · bakım: 4.0.532 published 2026-10-01; near-daily releases.
- Ajan kullanımı: - Render: npx remotion render src/index.ts MyComp out.mp4 --props=props.json
- Verify a frame: npx remotion still MyComp --frame=90 still.png, then Read it.
- Alpha output: --codec prores --prores-profile 4444
- Do not set licenseKey and do not use @remotion/web-renderer, which keeps it free of telemetry.
- Güven: high · kaynaklar: https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md, https://www.remotion.dev/docs/license/pricing, https://www.remotion.dev/docs/telemetry, https://www.remotion.dev/docs/ai/skills, https://registry.npmjs.org/remotion

### Technical and math explainers: algorithms, data structures, graphs, equations, geometric or coordinate animations
- **Seçim:** Manim Community 0.21.0 with the [typst] extra (Typst / MathTypst instead of LaTeX)
- Alternatifler: ManimGL (3b1b; MIT; needs LaTeX; less suited to agents).
- Neden: MIT. Gives precise programmatic vector animation (Transform / ReplacementTransform morphs, graphs, number lines).
- 0.21.0 (2026-08-10) adds Typst and MathTypst mobjects that compile to SVG with no TeX install. That avoids the multi-GB MacTeX.
- The same release makes the Cairo renderer 2.2x faster and adds parallel partial-movie encoding (max_inflight_encoders).
- Since 0.19 it encodes through PyAV, so no system ffmpeg is needed.
- -t gives alpha output (mov/webm) that can be layered into HyperFrames for camera moves and transitions.
- Breaking change in 0.21: Code mobject colors now come from Pygments styles.
- Lisans: kod MIT. The typst Python binding is Apache-2.0 (about 17 MB arm64 wheel). · ağırlık n/a · ticari: yes
- Apple Silicon: CPU Cairo renderer; no GPU needed. manimpango 0.7.0 ships macOS arm64 wheels for cp310 to cp315. pycairo 1.29.2 has no macOS wheel and compiles against brew cairo, which is already installed.
- Kurulum: Clean path:
1. The user runs once: sudo xcodebuild -license accept
2. brew install pkgconf (cairo and pango are already installed)
3. source /Users/onurkaya/Projects/video/ortam.sh; uv venv -p 3.12 /Users/onurkaya/Projects/video/.venv-manim
4. VIRTUAL_ENV=/Users/onurkaya/Projects/video/.venv-manim uv pip install 'manim[typst]'
5. Check with: manim checkhealth
No-sudo fallback (untested): uv pip install pkgconf into the same venv, then DEVELOPER_DIR=/Library/Developer/CommandLineTools PKG_CONFIG_PATH=/opt/homebrew/lib/pkgconfig uv pip install 'manim[typst]'.
Or, after accepting the license: brew install manim (formula 0.21.0; pulls in python@3.14 and deps).
- Disk: ~350 MB · bakım: 0.21.0 on 2026-08-10; 0.20.0/0.20.1 in Feb 2026; 0.19.1/0.19.2 in Dec 2025 / Jan 2026.
- Ajan kullanımı: - Draft: manim -ql scene.py Scene
- Inspect: manim -s -ql scene.py Scene writes the last frame as PNG; Read it.
- Final: manim -qh --fps 30 -r 1920,1080 scene.py Scene
- Overlay: manim -t --format mov for alpha.
- Verify: ffprobe nb_frames equals duration x fps, and pix_fmt has alpha.
- Güven: high · kaynaklar: https://pypi.org/pypi/manim/json, https://docs.manim.community/en/stable/changelog/0.21.0-changelog.html, https://docs.manim.community/en/stable/changelog/0.19.0-changelog.html, https://docs.manim.community/en/stable/installation/uv.html, https://docs.manim.community/en/stable/guides/configuration.html, https://pypi.org/pypi/manimpango/json, https://pypi.org/pypi/pycairo/json, https://pypi.org/pypi/pkgconf/json, https://formulae.brew.sh/api/formula/manim.json

### Lottie in app UI (web, iOS, Android, React Native, Flutter) and turning Lottie files into video, GIF or alpha overlays
- **Seçim:** dotLottie runtimes (@lottiefiles/dotlottie-web 0.80.0; dotlottie-rs/ThorVG-based iOS, Android, Flutter and RN players) plus airbnb lottie-web 5.13.0, lottie-ios, lottie-android and lottie-react-native 7.5.0. Video is rendered through HyperFrames' lottie adapter.
- Alternatifler: Rive runtime (MIT, @rive-app/canvas 2.44.0), but authoring needs the paid Rive editor.
- Neden: All MIT or Apache-2.0.
- dotLottie 2.0 adds themes/slots (color, scalar, gradient, text, image) and declarative state machines (click, hover, complete and custom events) written as JSON in a zipped .lottie file. That is an account-free replacement for Rive-style interactivity.
- ThorVG gives the same renderer on every platform (it also powers Canva iOS, Godot and LVGL).
- lottie-web is still the reference SVG renderer but moves slowly (5.13.0, May 2025).
- HyperFrames seeks lottie-web (goToAndStop) and dotLottie frame by frame and can export ProRes 4444 or WebM alpha.
- Lisans: kod MIT: dotlottie-web, dotlottie-rs, lottie-web, ThorVG. Apache-2.0: lottie-ios, lottie-android, lottie-react-native. · ağırlık n/a · ticari: yes
- Apple Silicon: dotlottie-web runs as WASM, with WebGL and WebGPU builds. Native iOS and Android libraries. No special acceleration needed.
- Kurulum: npm i @lottiefiles/dotlottie-web lottie-web, then copy the dist files into the project vendor/ folder rather than using a CDN. Apps: SPM lottie-ios or dotlottie-ios; Gradle com.airbnb.android:lottie or dotlottie-android; npm lottie-react-native.
- Disk: ~10 MB · bakım: dotlottie-web 0.80.0 on 2026-08-28 (active). lottie-web 5.13.0 on 2025-05-21 (slow). lottie-react-native 7.5.0.
- Ajan kullanımı: - In HyperFrames: autoplay:false, an explicit loop setting, and window.__hfLottie.push(anim).
- Check with hyperframes snapshot --at ... --describe false.
- Render with --format mov for an alpha deliverable.
- For apps: ship .lottie (smaller, themes and state machines) and test it in the target runtime.
- Güven: high · kaynaklar: https://registry.npmjs.org/@lottiefiles/dotlottie-web, https://registry.npmjs.org/lottie-web, https://github.com/LottieFiles/dotlottie-rs, https://dotlottie.io/spec/2.0, https://docs.lottiefiles.com/en/format/dotlottie/interactivity.md, https://github.com/airbnb/lottie-ios, https://registry.npmjs.org/lottie-react-native, https://github.com/thorvg/thorvg

### Authoring Lottie, dotLottie or TGS animations with no After Effects and no accounts (icons, loaders, onboarding, empty states, chat stickers)
- **Seçim:** text-to-lottie agent skill (diffusionstudio/lottie, MIT) plus @dotlottie/dotlottie-js 1.8.0 (MIT) for packaging themes and state machines. python-lottie 0.7.2 (AGPL-3.0+) as a standalone converter. Glaxnimate 0.6.0 (GPL-3, ARM dmg) if a human wants a GUI.
- Alternatifler: Hand-written Lottie JSON from a TypeScript generator; @lottiefiles/lottie-js object model.
- Neden: Bodymovin requires After Effects (paid). LottieFiles Creator, Jitter and Rive require accounts.
- text-to-lottie gives Claude Code a skill plus a local Vite hot-reload player (about 5.5k stars).
- dotlottie-js builds and edits .lottie bundles from code.
- python-lottie has the most complete code-to-Lottie object model. It imports SVG, TGS, dotLottie, GIF and MP4, exports GIF/WebP/MP4/WebM/HTML, and makes Telegram TGS stickers (512x512, at most 64 KB, 60 fps, at most 3 s).
- python-lottie is AGPL: fine as a local tool, since generated JSON is your output. Do not embed it in a closed product or service.
- Lisans: kod MIT: text-to-lottie, dotlottie-js. AGPL-3.0-or-later: python-lottie. GPL-3: Glaxnimate. · ağırlık n/a · ticari: conditional
- Apple Silicon: Pure JS or Python. Glaxnimate offers a native ARM dmg.
- Kurulum: DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 npx skills add diffusionstudio/lottie (or git clone it and copy the skill folder). npm i @dotlottie/dotlottie-js. uv pip install 'lottie[gif,video]' into the workspace venv.
- Disk: ~200 MB · bakım: python-lottie 0.7.2 on 2025-05-01 (slow). dotlottie-js 1.8.0 on 2026-08-10. text-to-lottie release cadence not verified.
- Ajan kullanımı: Generate the JSON, validate it against the lottie-spec JSON Schema (ajv), and check fr / ip / op / w / h. Render sample frames through both lottie-web and dotlottie-web in HyperFrames, compare them with SSIM, and check the byte budget.
- Güven: medium · kaynaklar: https://github.com/diffusionstudio/lottie, https://registry.npmjs.org/@dotlottie/dotlottie-js, https://pypi.org/pypi/lottie/json, https://gitlab.com/mattbas/python-lottie/-/raw/master/README.md, https://glaxnimate.org/download/, https://lottie.github.io/, https://core.telegram.org/stickers, https://www.mintlify.com/vercel-labs/skills/advanced/telemetry

### UI-grade 3D inside motion graphics: logo or product spins, 3D text, particles, camera flights, shader backgrounds, device mockups
- **Seçim:** Three.js 0.186.1 through HyperFrames' three adapter (React Three Fiber 9.8.1 only when using React or Remotion), with glTF-Transform 4.5.1, troika-three-text 0.52.5 and Poly Haven CC0 assets
- Alternatifler: Blender for photoreal work. @remotion/three if already on Remotion.
- Neden: Everything here is MIT.
- Frames are deterministic: render inside the hf-seek event using __hfThreeTime instead of requestAnimationFrame. Set root data-duration, because the three adapter cannot infer duration.
- The registry already has 3D blocks (code-3d-extrude, transitions-3d, ui-3d-reveal, device showcases).
- Far lighter than Blender for this kind of 3D.
- glTF-Transform compresses models (meshopt or draco). troika renders crisp SDF text from local fonts.
- The Poly Haven API is free for any purpose, including commercial. Assets are CC0. A 'Powered by Poly Haven' credit is needed only when exposing the live API in a UI, and a unique User-Agent is required.
- Lisans: kod MIT (three, @react-three/fiber, @gltf-transform/cli, troika-three-text). Assets CC0. · ağırlık n/a · ticari: yes
- Apple Silicon: WebGL or WebGPU through Chrome (Metal via ANGLE) when the --browser-gpu probe succeeds. Otherwise SwiftShader on the CPU, which is much slower; check the render log.
- Kurulum: npm i three@0.186.1 and copy build/three.module.js into project vendor/. Optimize models with npx -y @gltf-transform/cli@4.5.1 optimize in.glb out.glb --compress meshopt. Download HDRIs once from polyhaven.com and keep them in the project.
- Disk: ~40 MB · bakım: three 0.186.1 on 2026-09-24. R3F 9.8.1 (needs React 19). glTF-Transform 4.5.1 on 2026-09-28. troika 0.52.5 on 2026-07-24.
- Ajan kullanımı: - Build the scene synchronously and preload GLB/HDRI files before seeking.
- Check with hyperframes check, hyperframes keyframes <proj> --shot k.png --ghost (canvas onion skin), and snapshots at key times.
- Render with --browser-gpu.
- Güven: medium · kaynaklar: https://registry.npmjs.org/three, https://registry.npmjs.org/@react-three/fiber, https://registry.npmjs.org/@gltf-transform/cli, https://registry.npmjs.org/troika-three-text, https://polyhaven.com/our-api

### High-end 3D: photoreal product renders, stylized 3D animation, Geometry Nodes motion graphics, Grease Pencil 2D, physics and particles
- **Seçim:** Blender 5.2.2 LTS driven headless by Python scripts
- Alternatifler: Three.js in HyperFrames for lighter 3D.
- Neden: The app is GPL, but renders are yours to use commercially.
- Cycles renders on the M2 GPU via Metal; EEVEE uses the Metal backend.
- The 5.2 LTS line is supported until 2028.
- Agent-friendly flags (verified in creator_args.cc): --python-exit-code returns non-zero when a script fails; --offline-mode blocks online access; --factory-startup; and after --, --cycles-device METAL.
- Blender 5.0 API changes models often get wrong: the engine id is BLENDER_EEVEE (not BLENDER_EEVEE_NEXT); set image_settings.media_type before file_format; use scene.compositing_node_group instead of scene.node_tree; render passes were renamed.
- Lisans: kod GPL-2.0-or-later (application). The bpy wheel is GPL-3.0. · ağırlık n/a · ticari: yes
- Apple Silicon: Blender 5.x runs only on Apple Silicon (macOS 13+). Cycles uses the Metal GPU. EEVEE uses Metal; background (-b) EEVEE rendering on macOS should be confirmed with a 1-frame test.
- Kurulum: Download the 330 MB DMG from blender.org (5.2.2, released 2026-09-15) and copy it to /Applications; no account needed. After the Xcode license is accepted, brew install --cask blender also works. Optional Python module: uv venv -p 3.13 && uv pip install bpy==5.2.2 (245 MB wheel; Python 3.13 only).
- Disk: ~1300 MB · bakım: 5.2 LTS released July 2026; 5.2.2 on 2026-09-15; bpy 5.2.2 the same day.
- Ajan kullanımı: - Run: /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --offline-mode --python-exit-code 1 -P build_scene.py -- --out /abs/frames/
- In the script: prefs = bpy.context.preferences.addons['cycles'].preferences; set prefs.compute_device_type = 'METAL'; call prefs.get_devices(); enable the devices; set scene.cycles.device = 'GPU'.
- Render a PNG sequence with -a, then encode with ffmpeg.
- Verify by reading frames 1, middle and last and checking per-frame times in the log. -E help lists the available engines.
- Güven: high · kaynaklar: https://www.blender.org/download/, https://pypi.org/pypi/bpy/5.2.2/json, https://developer.blender.org/docs/release_notes/5.0/python_api/, https://raw.githubusercontent.com/blender/blender/main/source/creator/creator_args.cc, https://www.renderahouse.com/blog/blender-system-requirements

### Interactive agent control of a running Blender GUI (look-dev, scene inspection, viewport screenshots)
- **Seçim:** MCP for Blender 2.1.3 (PyPI mcp-for-blender, formerly blender-mcp); optional
- Alternatifler: Direct bpy scripts (preferred).
- Neden: MIT. Lets Claude Code inspect the scene, edit objects and materials, run Python and grab viewport screenshots. Its Poly Haven CC0 integration needs no key.
- Telemetry is ON by default (install ID, session ID, tool names, OS, versions). DISABLE_TELEMETRY=true is required by the user's rules.
- execute_blender_code runs arbitrary Python, so set BLENDER_MCP_SAFE_MODE=1.
- The Sketchfab, Poly Pizza, Hyper3D Rodin and Hunyuan3D tools need API keys or accounts; do not use them.
- Plain blender -b -P scripts stay better for reproducible renders.
- Lisans: kod MIT · ağırlık n/a · ticari: yes
- Apple Silicon: Same as Blender. The add-on talks over a local socket.
- Kurulum: claude mcp add blender -e DISABLE_TELEMETRY=true -e BLENDER_MCP_SAFE_MODE=1 -- uvx mcp-for-blender. Then run uvx mcp-for-blender install-addon, enable the add-on in Blender and connect.
- Disk: ~50 MB · bakım: 2.1.3 uploaded 2026-09-30; about 30k stars.
- Ajan kullanımı: Use it only for exploratory look-dev. Then move the final scene setup into a versioned .py script and render headless.
- Güven: medium · kaynaklar: https://github.com/ahujasid/blender-mcp, https://raw.githubusercontent.com/ahujasid/blender-mcp/main/README.md, https://pypi.org/pypi/mcp-for-blender/json

### Scripted terminal and CLI demo videos (README, docs, launch videos)
- **Seçim:** VHS 0.12.1 (charmbracelet)
- Alternatifler: asciinema + agg for real sessions. HyperFrames terminal-window blocks for fully synthetic shells.
- Neden: MIT. A declarative .tape file makes a terminal demo reproducible and easy to re-record.
- Commands include: Output demo.mp4 | demo.gif | demo.webm | frames/; Set FontSize, FontFamily, Width, Height, Padding, TypingSpeed, Theme, Framerate; Type; Sleep; Wait /regex/ (waits for real output instead of guessing sleeps); Hide/Show to skip setup; Screenshot; Require.
- The MP4 can go into HyperFrames for zooms and branding.
- Never run vhs publish; it uploads to vhs.charm.sh.
- Lisans: kod MIT (vhs, ttyd 1.7.7). Brew's ffmpeg 9.0.2 is GPL-3.0-or-later. · ağırlık n/a · ticari: yes
- Apple Silicon: Native arm64 (brew bottle, or the vhs_0.12.1_Darwin_arm64.tar.gz release asset). Drives headless Chrome via go-rod and should find the installed Google Chrome; otherwise it may download a Chromium.
- Kurulum: After sudo xcodebuild -license accept: HOMEBREW_NO_ANALYTICS=1 brew install vhs. Bottles: vhs 9.1 MB, ttyd 0.4 MB, ffmpeg 21 MB plus about 10 small codec libraries; roughly 150 MB installed (estimate). ttyd has no macOS release binary, so brew is the practical route.
- Disk: ~150 MB · bakım: 0.12.1 on 2026-09-24; 0.12.0 on 2026-09-09; 0.11.0 on 2026-03-10.
- Ajan kullanımı: Run vhs demo.tape. Check duration, size and fps with ffprobe. Extract frames at the Wait points and Read them to confirm the expected output text is on screen.
- Güven: high · kaynaklar: https://github.com/charmbracelet/vhs, https://github.com/charmbracelet/vhs/releases, https://formulae.brew.sh/api/formula/vhs.json, https://formulae.brew.sh/api/formula/ttyd.json, https://github.com/tsl0922/ttyd/releases

### Capture a real, unscripted terminal session and turn it into a GIF or video
- **Seçim:** asciinema 3.2.1 (Rust rewrite) + agg 1.9.0
- Alternatifler: VHS for scripted demos.
- Neden: Records locally to .cast (asciicast v3, optional zstd), a text timeline you can trim. --idle-time-limit cuts dead time.
- agg renders a GIF using the gifski library. Options: --theme, --font-family, --font-size, --speed, --fps-cap, --renderer swash|resvg, and --select for frame ranges (new in 1.9.0).
- Nothing is uploaded unless you run asciinema upload or auth (don't).
- Both are GPL, which is fine for standalone CLI use; outputs are yours.
- Lisans: kod asciinema GPL-3.0-only; agg GPL-3.0-or-later · ağırlık n/a · ticari: yes
- Apple Silicon: Native arm64. agg has a prebuilt agg-aarch64-apple-darwin release binary. Brew bottles: agg 7.2 MB, asciinema 3.9 MB.
- Kurulum: brew install asciinema agg (after the Xcode license is accepted). Without brew: download agg-aarch64-apple-darwin from the GitHub release into /Users/onurkaya/Projects/video/arac/ and chmod +x it.
- Disk: ~15 MB · bakım: agg 1.9.0 on 2025-05-29. asciinema 3.2.1 is the current brew formula (2026).
- Ajan kullanımı: 1. asciinema rec --idle-time-limit 1 -c 'npm test' demo.cast
2. agg --font-size 28 --theme monokai --speed 1.25 demo.cast demo.gif
3. ffmpeg -i demo.gif -movflags +faststart -pix_fmt yuv420p -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2' demo.mp4
4. Verify size and frame count with ffprobe.
- Güven: high · kaynaklar: https://github.com/asciinema/asciinema, https://github.com/asciinema/agg, https://github.com/asciinema/agg/releases/expanded_assets/v1.9.0, https://formulae.brew.sh/api/formula/agg.json, https://formulae.brew.sh/api/formula/asciinema.json

### Animated source code for developer videos: typing, diffs, refactor morphs, spotlighting a line, scrolling a file, PR explainers
- **Seçim:** HyperFrames registry code blocks (code-typing, code-diff, code-morph via Shiki Magic Move, code-highlight, code-scroll, code-3d-extrude, 24 code-snippet-* terminal/editor themes) plus the pr-to-video skill
- Alternatifler: VHS for real command output.
- Neden: Highlighting comes from baked Shiki tokens, the same quality as VS Code, driven by deterministic GSAP timelines. Because nothing is screen-recorded, code stays sharp at 4K, edits are trivial and re-renders are exact. pr-to-video builds a changelog or feature video from a real git diff and commits.
- Lisans: kod HyperFrames repo Apache-2.0; Shiki and shiki-magic-move MIT · ağırlık n/a · ticari: yes
- Apple Silicon: Same as HyperFrames
- Kurulum: hyperframes add code-morph --dir <proj> --no-clipboard (fetched from the GitHub raw registry).
- Disk: ~5 MB · bakım: Ships with HyperFrames (daily releases).
- Ajan kullanımı: Fill window.__TOKENS with the real snippet. Make sure data-duration covers the per-character speed. Snapshot mid-morph and at the end, and Read them to check legibility and line wrapping.
- Güven: medium · kaynaklar: https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/registry.json, https://github.com/heygen-com/hyperframes

### Automated product demo and walkthrough recordings of web apps, with visible cursor, chapters and Screen-Studio-style zooms
- **Seçim:** A Playwright 1.63.0 script using page.screencast (start/stop, showActions with a cursor, showChapter, showOverlay), followed by HyperFrames for zoom-to-action, cursor polish, device frame and music
- Alternatifler: puppeteer-core screencast (already installed); hyperframes capture <url> --skip-vision to rebuild a site as editable components.
- Neden: Apache-2.0.
- Since 1.59, page.screencast gives precise start/stop, built-in action annotations with an animated pointer cursor, chapter titles and HTML overlays. An onFrame callback hands out JPEG frames for your own high-quality encode.
- Plain recordVideo has no cursor by default and caps size (viewport scaled to fit 800x800; 800x450 with no viewport).
- A script is a reproducible demo you can re-record after every UI change.
- launch({channel:'chrome'}) reuses the installed Google Chrome and skips the bundled Chromium download.
- Zero-install fallback: puppeteer-core 25.12.0, already in node_modules, has page.screencast({path:'x.webm'|'x.mp4'|'x.gif', fps, quality as CRF, crop, scale}). It pipes PNG frames into ffmpeg (VP9, constant-fps grid).
- Lisans: kod Apache-2.0 (playwright, puppeteer-core) · ağırlık n/a · ticari: yes
- Apple Silicon: Native arm64 browsers.
- Kurulum: npm i -D playwright@1.63.0 in a demo folder. Then either use channel:'chrome' or run npx playwright install chromium (about 150-200 MB, estimate).
- Disk: ~20 MB · bakım: 1.63.0 on 2026-09-04; screencast API added in 1.59 (2026).
- Ajan kullanımı: 1. Create a context with viewport 1440x900 and deviceScaleFactor 2.
2. await page.screencast.start({path:'raw.webm', size:{width:2880,height:1800}}); await page.screencast.showActions({cursor:'pointer'}).
3. Log every action to actions.json as {t,x,y,w,h}, then stop the screencast.
4. Convert to constant frame rate with ffmpeg (fps=60).
5. Build a HyperFrames composition from actions.json: zooms (hyperframes-keyframes), the cursor-ui-demo blueprint, render with --video-frame-format png.
6. Verify with snapshots at each action time.
macOS native apps: screencapture -v -C -k -V20 -R0,0,1440,900 out.mov (needs Screen Recording permission). iOS Simulator: xcrun simctl io booted recordVideo --codec=h264 out.mp4 (needs the Xcode license; output is variable frame rate).
- Güven: medium · kaynaklar: https://playwright.dev/docs/api/class-screencast, https://playwright.dev/docs/api/class-browser, https://playwright.dev/docs/release-notes, https://playwright.dev/docs/videos, https://registry.npmjs.org/playwright, https://pptr.dev/api/puppeteer.screencastoptions

### GIF, animated WebP, APNG and AVIF exports for READMEs, PRs, docs and chat stickers
- **Seçim:** gifski 1.34.0 for GIF. ffmpeg-static 6.0 (palettegen/paletteuse, libwebp_anim, apng, avif via libaom/libsvtav1, all verified locally) plus img2webp/gif2webp from libwebp 1.6.0 (already installed) for WebP. gifsicle 1.96 for -O3 --lossy. HyperFrames --format gif for quick ones.
- Alternatifler: HyperFrames --format gif (best at 15 fps per its help); agg for terminal GIFs.
- Neden: gifski (libimagequant palettes, temporal dithering) gives the best GIF quality per byte. It is AGPL-3.0-only, but as a standalone CLI that license does not attach to your GIFs.
- ffmpeg's two-pass palette is the no-install fallback.
- Prefer MP4 where you can: GitHub accepts .mp4, .mov and .webm (10 MB on free plans, 100 MB on paid) and caps GIFs and images at 10 MB.
- WebP and APNG keep alpha for stickers. WhatsApp animated stickers: 512x512 WebP, at most 500 KB (third-party spec). Telegram video stickers: VP9 WebM, one side 512 px, at most 3 s, at most 30 fps, at most 256 KB, no audio.
- Lisans: kod gifski AGPL-3.0-only; gifsicle GPL-2.0-only; libwebp BSD-3-Clause; the ffmpeg-static build is GPL with --enable-nonfree (local use only; do not redistribute the binary) · ağırlık n/a · ticari: yes
- Apple Silicon: Native arm64 for all tools
- Kurulum: After the Xcode license is accepted: brew install gifski gifsicle (gifski bottle 0.6 MB; it depends on brew ffmpeg). Nothing else is needed for the ffmpeg and img2webp paths.
- Disk: ~30 MB · bakım: gifski 1.34.0 on 2026-07-13; gifsicle 1.96; libwebp 1.6.0.
- Ajan kullanımı: - gifski: ffmpeg -i in.mp4 -vf fps=15,scale=960:-1:flags=lanczos -f yuv4mpegpipe - | gifski --fps 15 --quality 90 -o out.gif -
- ffmpeg fallback: ...split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a (use bayer:bayer_scale=5 for flat UI)
- Optimize: gifsicle -O3 --lossy=30 out.gif -o out.min.gif
- WebP: img2webp -loop 0 -lossy -q 75 -d 33 f*.png -o s.webp
- APNG: ffmpeg -i f%04d.png -plays 0 -f apng s.png
- Verify byte size, frame count and delays, and loop-seam SSIM.
- Güven: high · kaynaklar: https://github.com/ImageOptim/gifski, https://github.com/ImageOptim/gifski/releases, https://formulae.brew.sh/api/formula/gifski.json, https://formulae.brew.sh/api/formula/gifsicle.json, https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files, https://core.telegram.org/stickers, https://docs.zavu.dev/guides/whatsapp/messages/sticker, https://creatomate.com/blog/how-to-make-a-gif-from-a-video-using-ffmpeg

### SVG animation: logo draw-on, icon morphs, motion along a path, line-art reveals, per-letter text, animated README or site banners
- **Seçim:** GSAP 3.15.0 plugins (DrawSVG, MorphSVG, MotionPath, SplitText, CustomEase, Flip, Inertia) inside HyperFrames, SVGO 4.1.0 to clean SVGs, and anime.js 4.5.0 (MIT) when the animation ships inside a product that needs an OSI license
- Alternatifler: anime.js v4 (an adapter exists in HyperFrames); CSS/WAAPI.
- Neden: The plugins are already in node_modules/gsap/dist (verified locally) and have been free since GSAP 3.13 (2025-04-30).
- The Standard 'no charge' license allows commercial use. It only forbids use inside tools that compete with Webflow's visual animation builder.
- HyperFrames seeks GSAP, CSS @keyframes, WAAPI and Anime.js deterministically.
- For web or README delivery with no JavaScript, emit SVG with CSS keyframes and check it the same way.
- Lisans: kod GSAP: Standard 'no charge' license (proprietary, free, not OSI). SVGO and anime.js: MIT. · ağırlık n/a · ticari: yes
- Apple Silicon: Browser-based; nothing to accelerate
- Kurulum: Already installed (node_modules/gsap 3.15.0; vendor/gsap.min.js). Clean SVGs with npx -y svgo@4.1.0 in.svg -o out.svg.
- Disk: ~10 MB · bakım: GSAP 3.15.0 on 2026-04-13; SVGO 4.1.0 on 2026-08-24; anime.js 4.5.0.
- Ajan kullanımı: Register plugins with gsap.registerPlugin, then tween drawSVG '0% 0%' to '0% 100%' or morphSVG to a target path. Audit motion with hyperframes keyframes <proj> --selector 'path#logo' --shot k.png --layout strip. Snapshot the frames.
- Güven: high · kaynaklar: https://registry.npmjs.org/gsap, https://webflow.com/blog/gsap-becomes-free, https://gsap.com/community/standard-license/, https://registry.npmjs.org/svgo, https://registry.npmjs.org/animejs

### App Store and Google Play preview videos and store graphics that pass validation the first time
- **Seçim:** A HyperFrames composition at store resolution, a final ffmpeg encode, and ffprobe conformance checks
- Alternatifler: ProRes 422 HQ (-c:v prores_ks -profile:v 3) when bandwidth does not matter.
- Neden: Apple App Store Connect spec (fetched 2026-10):
- Length 15-30 s, file at most 500 MB, at most 30 fps.
- H.264 Progressive High Profile, up to Level 4.0, target 10-12 Mbps (.mov, .m4v or .mp4), or ProRes 422 HQ (.mov, about 220 Mbps).
- Audio: stereo, 256 kbps AAC (or PCM for ProRes), 44.1 or 48 kHz, all tracks enabled.
- Up to 3 previews per localization; default poster frame at 5 s.
- Sizes: 886x1920 portrait / 1920x886 landscape (iPhone 6.9/6.5/6.3/6.1 inch), 1080x1920 (5.5 inch), 1200x1600 (iPad 13 and 11 inch), 1920x1080 (Mac and Apple TV, landscape only), 3840x2160 (Vision Pro).
Google Play:
- The preview is a YouTube URL: public or unlisted, embeddable, ads off, not age-restricted; only the first 30 s autoplay.
- Feature graphic 1024x500 JPEG or 24-bit PNG; icon 512x512 32-bit PNG at most 1024 KB.
- Lisans: kod n/a · ağırlık n/a · ticari: yes
- Apple Silicon: h264_videotoolbox is available, but use libx264 for exact profile/level control
- Kurulum: Nothing new
- Disk: ~0 MB · bakım: Spec pages current as of 2026-10.
- Ajan kullanımı: 1. Use data-width=886 data-height=1920 data-fps=30 and render a master.
2. Encode: ffmpeg -i master.mov -c:v libx264 -profile:v high -level:v 4.0 -b:v 11M -maxrate 12M -bufsize 24M -pix_fmt yuv420p -r 30 -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart preview.mp4
3. Assert with ffprobe JSON: size, fps, duration, profile, level, channels and bytes.
- Güven: high · kaynaklar: https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications, https://support.google.com/googleplay/android-developer/answer/9866151

## Kaçınılacaklar

- **Rive Editor (rive.app)** — Requires an account. Since 2025-10-20, exporting to apps or sites needs a paid plan (Cadet, $9/month billed annually). The MIT runtime (@rive-app/canvas 2.44.0) is fine for playing existing .riv files, but HyperFrames has no Rive adapter. Use dotLottie state machines instead.
- **Theatre.js** — The last public release is 0.7.2 (2024-05-19), and development moved to a private repo. @theatre/studio is AGPL-3.0-only. Use GSAP timelines + hyperframes preview instead.
- **Motion Canvas (and the Canvas Commons fork)** — No stable release since 3.17.2 (2024-12-14), and motioncanvas.io is offline. Rendering only starts from the editor's RENDER button (no headless CLI), which is poor for agents. Canvas Commons 0.4.0 (2026-09-24) is active but renders the same UI-only way.
- **Revideo** — Releases are sporadic (0.10.4 in Feb 2025, then 0.11.0 in Jul 2026), the repo moved to midrender/revideo with no GitHub releases, and the community is small. HyperFrames or Remotion cover the same needs.
- **Full MacTeX for Manim** — Multi-GB on an 18-21 GB disk. Manim 0.21's [typst] extra (about 17 MB) makes LaTeX unnecessary. If TeX is truly needed, use TinyTeX with the package list in Manim's docs.
- **TRELLIS.2 / Hunyuan3D image-to-3D and text-to-3D** — TRELLIS.2 on Mac peaks around 18 GB RAM (16 GB Macs swap), needs about 15 GB of weights, and depends on gated Hugging Face models (account). Hunyuan3D's license excludes the EU, UK and South Korea.
- **HyperFrames cloud / lambda / cloudrun / publish / auth / usage; snapshot without --describe false; capture without --skip-vision** — They need accounts or upload to HeyGen. snapshot sends frames to Gemini when GEMINI_API_KEY is set, and capture's vision captioning uses OPENROUTER, GEMINI or GOOGLE keys if present. Personal footage must never leave the machine.
- **vhs publish; asciinema upload / asciinema auth** — They upload recordings to third-party servers (vhs.charm.sh, asciinema.org).
- **MCP for Blender external generators (Sketchfab, Poly Pizza, Hyper3D Rodin, Hunyuan3D) and its default telemetry** — These need API keys or accounts, and the server sends usage telemetry unless DISABLE_TELEMETRY=true is set.
- **After Effects + Bodymovin, LottieFiles Creator, Jitter, SVGator, Spline, Screen Studio, Canva** — Paid and/or account-bound. Local tools above cover the same outputs.
- **Remotion at work without a license; @remotion/web-renderer** — For-profit employers with 4 or more employees need a paid Company License. Client-side rendering APIs always send telemetry.
- **Plain Playwright recordVideo for final marketing footage** — Default size fits within 800x800 (800x450 with no viewport set), output is WebM, and no cursor is shown unless showActions is used. Use page.screencast with an explicit size, or frame capture plus your own encode.
- **Homebrew thorvg formula as a Lottie-to-GIF tool** — The formula builds only the library (no -Dtools), so the lottie2gif and svg2png CLIs are not installed. Render Lottie through HyperFrames or python-lottie instead.
- **Home-made numpy beat tracking to time animation** — It already produced off-beat cuts that sounded like 'audio slipping'. Take beat times from the audio domain's vetted tracker and prove alignment with the measurable checks in techniques.

## Teknikler

### Privacy and telemetry preamble for every session
Run source /Users/onurkaya/Projects/video/ortam.sh (HYPERFRAMES_NO_TELEMETRY=1, DO_NOT_TRACK=1, HOMEBREW_NO_ANALYTICS=1, HF_HUB_DISABLE_TELEMETRY=1) and also export DISABLE_TELEMETRY=1. Never set GEMINI_API_KEY, OPENROUTER_API_KEY or GOOGLE_API_KEY. Always pass snapshot --describe false and capture --skip-vision. Vendor JS libraries into project vendor/ folders.

**Doğrulama:** env | grep -E 'GEMINI|OPENROUTER|GOOGLE_API' prints nothing. grep -nE 'https?://' <proj>/index.html shows no script or style sources.

### Determinism proof
Render the same composition twice, then run ffmpeg -i a.mp4 -map 0:v -f framemd5 a.md5 (and the same for b).

**Doğrulama:** diff a.md5 b.md5 is empty. Any difference points to non-seeked animation, Math.random, Date, requestAnimationFrame or network assets.

### Visual QA loop with the Read tool
Run hyperframes snapshot <proj> --at <key times and transition midpoints> --describe false. Run hyperframes keyframes <proj> --selector '#el' --shot k.png (add --ghost for canvas/WebGL) to see paths and easing spacing; use --zoom '#title' --zoom-scale 3 to check text edges. For the final MP4, use the workspace's timestamped tile contact-sheet filter.

**Doğrulama:** Read every sheet. Check for no clipping, no overlaps, readable text and correct z-order. Onion-skin spacing should show easing (bunched at the ends), not uniform linear steps.

### Cut, beat and accent alignment proof
Keep every cut or accent as an integer frame number, frame = round(t_beat x fps), using beat times from a vetted tracker (audio domain), and place GSAP labels at frame/fps. After rendering, list the real cuts: ffmpeg -i out.mp4 -an -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'.

**Doğrulama:** A script compares intended and detected cut times. Max |difference| must be at most 1 frame (33.3 ms at 30 fps), with no missing or extra cuts. Report the numbers; never claim it 'sounds right'.

### A/V sync pulse test (anti 'audio slipping')
Build a 3-second test composition: one full-white frame at t=1.000 s plus a 10 ms click in the audio at the same instant. Run it through the exact production pipeline (same fps, sources, encoder, loudness step). Measure the flash with ffmpeg -vf signalstats (jump in YAVG) and the click onset with astats or silencedetect (silence_end).

**Doğrulama:** |t_flash - t_click| is under 1 frame. Re-run after any pipeline change (new fps, variable-frame-rate source, new encoder or mastering step).

### Constant-frame-rate normalization of recordings
Before composing, convert screencasts, simulator or screen recordings and phone clips to constant frame rate: ffmpeg -i raw.webm -vf fps=60 -c:v libx264 -crf 12 -pix_fmt yuv420p rec60.mp4 (or ProRes). In HyperFrames, use --video-frame-format png for UI footage.

**Doğrulama:** ffprobe shows r_frame_rate equal to avg_frame_rate, and nb_frames is about duration x fps. mpdecimate shows no unexpected runs of duplicate frames.

### Screen-Studio-style product demo polish
1. Record at deviceScaleFactor 2 and log actions.json with {t,x,y,w,h}.
2. In HyperFrames, zoom by 1.5-2.2x centered on the action's bounding box: ease in with power3.inOut over 0.6-0.9 s, hold during the interaction, ease back out.
3. Move a synthetic cursor along a curved path with eased timing, add a click ripple, and blur only fast pans.
4. Never zoom past recorded pixel density (max zoom = recorded px / output px).
5. Use the cursor-ui-demo and zoom-out-workspace-reveal blueprints.

**Doğrulama:** Take snapshots at each action time with --zoom on the target region. Text must be crisp, and the cursor tip must sit within a few pixels of the logged coordinates.

### Motion-design craft rules (pro look, no text overlays required)
- Easing: power2/3.inOut for camera moves and zooms; expo.out for entrances; back.out(1.4-1.7) for pops; linear only for continuous spins.
- Add anticipation, overshoot and settle; stagger 0.03-0.08 s.
- Keep one easing family per piece.
- Motion blur only on moves of at least one element-width per frame (motion-blur component or engine option).
- Use 2.5D parallax with depth layers, match cuts and whip transitions from the hyperframes-animation transitions catalog.
- Use 60 fps for UI and cursor work, 24-30 fps for cinematic pieces.

**Doğrulama:** hyperframes keyframes <proj> --json lists tween durations and eases; check them against the rules. The onion-skin shot confirms the spacing.

### Delivery-encode quality gate
Keep a high-quality master (ProRes 4444 or CRF at most 12), then make the delivery encode with yuv420p, bt709 tags and +faststart. Score it: ffmpeg -i deliver.mp4 -i master.mov -lavfi '[0:v][1:v]libvmaf' -f null - (libvmaf is in ffmpeg-static).

**Doğrulama:** VMAF at least 95 (at least 97 for UI or text-heavy pieces). Check bitrate and file size against the target; in the workspace, 8 Mbps at 1080p was a good sharing default.

### Spec conformance asserts
A small script runs ffprobe -v error -show_streams -show_format -of json and checks the target spec. Examples: App Store 886x1920, at most 30 fps, 15-30 s, H.264 High at most L4.0, AAC stereo at 44.1 or 48 kHz, at most 500 MB. Telegram sticker: 512 px side, at most 3 s, at most 30 fps, at most 256 KB, no audio. GitHub: at most 10 MB on free plans.

**Doğrulama:** The script exits 0 and prints each check with PASS or FAIL.

### Lottie validation and cross-renderer check
Validate the JSON against the lottie-spec JSON Schema with ajv-cli, and check fr, ip, op, w and h. Render the same frames with lottie-web (SVG) and dotlottie-web (ThorVG) in HyperFrames and compare them with ffmpeg -lavfi ssim.

**Doğrulama:** Schema passes, SSIM is at least 0.98 on sampled frames, and size stays within budget (for example 100 KB or less for UI, 64 KB or less for TGS).

### Blender headless render recipe
Run Blender -b --factory-startup --offline-mode --python-exit-code 1 -P scene.py -- args. In the script, turn on Cycles Metal (prefs.compute_device_type = 'METAL', get_devices(), scene.cycles.device = 'GPU'), set fps and frame range, and output a PNG sequence with render.use_overwrite = False and use_placeholder = True so renders can resume. Render with -a, then encode with ffmpeg. Use BLENDER_EEVEE for EEVEE in 5.x.

**Doğrulama:** The command exits 0, the frame count matches the range, and frames 1, middle and last look right when Read. Log per-frame render times. Before a long EEVEE background run, test with -f 1.

### Manim to HyperFrames compositing
Render scenes at the composition's fps with manim -qh --fps 30 -t --format mov (alpha). Place them in HyperFrames as muted <video> clips, and add camera moves, transitions and music there.

**Doğrulama:** ffprobe shows an alpha pix_fmt (yuva or argb in ProRes 4444) and the right frame count. A snapshot over a colored background shows clean edges.

### GIF, WebP, APNG and sticker pipeline
- GIF: gifski (ffmpeg ... -f yuv4mpegpipe - | gifski --fps 15 --quality 90 -o out.gif -), or the ffmpeg two-pass palette (palettegen stats_mode=diff + paletteuse sierra2_4a; bayer for flat UI); then gifsicle -O3 --lossy=30.
- WebP: img2webp -loop 0 -lossy -q 75 -d 33 frames/*.png -o s.webp
- APNG: ffmpeg -i f%04d.png -plays 0 -f apng s.png
- Telegram WebM: libvpx-vp9 -pix_fmt yuva420p -an -t 3

**Doğrulama:** Check size against the limit, check frame count and delays with ffprobe, and make sure the loop seam is clean (SSIM of first vs last frame at least 0.98 for seamless loops).

### Code-first terminal demos
Write a VHS tape: Set Width 1920, Height 1080, FontSize 28-32, Padding, TypingSpeed 40ms. Hide setup commands, use Wait /regex/ instead of fixed Sleep, Output demo.mp4 and demo.gif. For highlighted code without a shell, use the HyperFrames code-* blocks.

**Doğrulama:** Extract frames at each Wait point (ffmpeg -ss) and Read them to confirm the expected text is visible. Duration stays within budget.


## Riskler

- Homebrew is unusable right now: every brew command (even brew info) fails with 'You have not agreed to the Xcode license' (verified 2026-10-05). The same block hits xcrun simctl. Only the user can fix it, by running `sudo xcodebuild -license accept` once (needs the admin password). DEVELOPER_DIR=/Library/Developer/CommandLineTools makes clang work (verified), but Homebrew ignores it.
- Disk is tight (21.7 GB free).
- The HyperFrames frame-extract cache in /var/folders is already 907 MB and grows silently; use hyperframes clean or --frames-cache-dir.
- 1080p RGBA PNG sequences cost roughly 2-4 MB per frame (several GB per minute at 30 fps); prefer ProRes 4444 MOV or chunked renders and delete intermediates.
- Blender needs about 1.2-1.3 GB installed (estimate) plus optional bpy (245 MB wheel, more unpacked).
- iOS simulator runtimes are multi-GB each; one is already installed.
- HyperFrames moves very fast (479 npm versions since 2026-03-23, several per day). The CLI, lint rules and skills can change under you. Pin the exact version, upgrade on purpose, and re-run hyperframes skills after upgrading.
- Model knowledge drift. Blender 5.0 changed BLENDER_EEVEE, media_type, compositing_node_group and pass names; Grease Pencil v3 changed in 4.3; Manim 0.21 changed the Code mobject; Playwright's screencast API is 1.59+; HyperFrames is newer than most training data. Write small test scripts, check versions, and introspect with --help, dir() and -E help before long renders.
- WebGL in headless Chrome may fall back to SwiftShader (software rendering) if the GPU probe fails. Three.js scenes then render very slowly. Watch the --browser-gpu result, and move heavy 3D to Blender.
- Telemetry defaults to watch: HyperFrames (HYPERFRAMES_NO_TELEMETRY=1), MCP for Blender (on by default), the Vercel 'skills' CLI used by npx skills add (DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1), Remotion client-side rendering (always on), and Homebrew analytics (HOMEBREW_NO_ANALYTICS=1).
- Image-leak paths to external AI: hyperframes snapshot and capture use Gemini or OpenRouter when keys exist, and the media-use skill can call Gemini or Lyria. Keep those keys unset and always pass --describe false and --skip-vision.
- License traps:
- GSAP is free but not OSI-licensed and forbids building a competitor to Webflow's visual animation builder.
- Remotion needs a company license above 3 employees.
- AGPL (gifski, python-lottie) matters only if you embed or serve them.
- The ffmpeg-static binary was built with --enable-nonfree; do not redistribute it.
- HyperFrames registry device blocks (vfx-iphone-device, ios26-liquid-glass; marked 'experimental') bundle iPhone/MacBook GLB models and iOS-style app icons with no license metadata. Do not use them in commercial marketing until their origin is confirmed, and watch Apple's trademark rules.
- Variable-frame-rate sources (screencasts, simctl recordVideo, screencapture, phone footage) drift against audio if composed without conversion. Always convert to constant frame rate (ffmpeg fps=N) and check that r_frame_rate equals avg_frame_rate. This is a common real cause of 'audio slipping'.
- macOS Screen Recording permission is needed for screencapture and ffmpeg avfoundation capture; only the user can grant it. Playwright channel:'chrome' follows the auto-updating Chrome, which can change pixels between re-recordings. Pin a bundled Chromium when byte-exact repeatability matters (costs about 150-200 MB).
- Skill examples load lottie, dotlottie and three from cdnjs, unpkg and jsdelivr. Network access during render hurts determinism and offline use. Vendor the libraries into each project and grep the compositions for http(s):// before rendering.
- Memory on 16 GB: each HyperFrames worker is a Chrome of about 256 MB. 4K renders with WebGL, Lottie or many videos can thrash, so lower --workers. Blender Cycles at 4K can take minutes per frame; use EEVEE or lower samples with denoising for animation.
- Young and less-proven pieces: text-to-lottie (release cadence unknown), dotLottie state machines, and Playwright screencast quality settings. Lottie features (expressions, effects, mattes) differ between lottie-web and ThorVG, so test in the target runtime.

## Açık sorular

- How many employees does the user's employer have? This decides whether Remotion is allowed for work. Will any animation code ship inside a product (GSAP clause, AGPL tools) or only as rendered media?
- Will the user run `sudo xcodebuild -license accept` once? It unblocks Homebrew (VHS, gifski, agg, pkgconf, Blender cask), local compiling and iOS Simulator recording.
- Which app platforms matter for Lottie/dotLottie and store previews: web, native iOS, Android, React Native or Flutter? Which store device sizes are needed?
- How deep should 3D go: UI-grade Three.js (about 40 MB) or Blender-grade photoreal/stylized work (about 1.3 GB plus render time)?
- Is an occasional GUI acceptable for manual touch-ups (HyperFrames Studio preview, Blender UI, Glaxnimate), or must everything stay CLI-only?
- Which delivery targets should get standard presets: Reels/TikTok 1080x1920, YouTube 16:9, LinkedIn, GitHub README, App Store?

## Şüpheci doğrulama

The findings are mostly accurate and well sourced. Versions, dates, licenses and Apple Silicon support for HyperFrames, Remotion, Manim 0.21.0, Blender 5.2.2 LTS, MCP for Blender, VHS, the Lottie runtimes, Three.js, GSAP, Playwright 1.59+ screencast, ffmpeg-static, and the App Store, Google Play, GitHub, Telegram and WhatsApp specs were all confirmed against primary sources and local checks on 2026-10-05.

The picks still stand. HyperFrames as the hub, Manim with Typst, Blender headless, VHS or asciinema+agg, Playwright or puppeteer, and gifski or the ffmpeg palette path are reasonable for a 16 GB M2 with about 18 GiB free.

Factual errors to fix:
- Free disk is 18 GiB, not 21.7 GB.
- gifski 1.34.0 is from 2025-07-13, and agg 1.9.0 is from 2026-05-29; both years are wrong in the findings.
- motioncanvas.io is online.
- Rive's free plan does export, with a splash screen.
- The typst wheel is 30.5 MB.
- The registry has 3 code-snippet blocks, not 24.
- python-lottie[gif] cannot install on macOS arm64, and python-lottie cannot import MP4.

Decision-relevant gaps:
- **Slow motion:** this was requested explicitly, but the findings rely on minterpolate (0.09x realtime at 1080p here). Apple VTFrameProcessor or RIFE should be added.
- **Beat detection:** HyperFrames' own `beats` command is a naive bpm-detective grid, the same failure class as the earlier 'audio slipping'. The proposed cut-alignment check also never validates the beat list itself.
- **Image quality:** HyperFrames uses JPEG intermediates by default (q95 capture, JPEG footage extraction). This should be measured with VMAF on footage pieces.
- **Verification method:** the framemd5 determinism test needs --no-browser-gpu or a tolerance, and scene-score cut detection misses dissolves.

Confidence: high for the version, license and spec checks; medium for the new slow-motion and parallax recommendations, which were not built or tested here.

### Kontroller

- [confirmed] HyperFrames is Apache-2.0 and very active. npm created 2026-03-23, 479 versions, 0.8.125 on 2026-10-04, ~56.7k GitHub stars. 0.8.124 is installed. — npm registry: latest 0.8.125 (2026-10-04), created 2026-03-23, 479 versions, license Apache-2.0. GitHub API: 56,728 stars, Apache-2.0, last pushed 2026-10-04. Local node_modules/hyperframes/package.json is 0.8.124, Apache-2.0. (https://registry.npmjs.org/hyperframes ; https://api.github.com/repos/heygen-com/hyperframes ; /Users/onurkaya/Projects/video/node_modules/hyperframes/package.json)
- [confirmed] HyperFrames takes about 390 MB on disk. — Workspace node_modules is 195 MB and ~/.cache/hyperframes/chrome is 193 MB (chrome-headless-shell mac_arm-152.0.7977.30), about 388 MB in total. (local du)
- [confirmed] Render outputs are mp4, webm, mov (ProRes 4444 alpha), gif, png-sequence and hls. --resolution 4k raises the device pixel ratio. Each worker is a Chrome of about 256 MB. Fast capture is on by default on macOS with a hardware GPU (about 2x). --browser-gpu falls back to SwiftShader. --gpu uses VideoToolbox. — Every item appears in the `hyperframes render --help` text (v0.8.124). The dist code calls h264_videotoolbox / hevc_videotoolbox and `prores_ks -profile:v 4444 -pix_fmt yuva444p10le`. Low-memory mode switches on automatically only at 8 GB RAM or less, so it stays off on this 16 GB Mac. (local CLI help; node_modules/hyperframes/dist)
- [confirmed] --video-frame-format png keeps UI recordings sharp. The findings imply the default path is fine for real footage. — The png option is confirmed, but the findings leave out what the default does. resolveFrameFormat (dist/chunk-CMH5CSTH.js) turns 'auto' into jpg for any opaque source. The render engine (dist/chunk-VFCR64GO.js, resolveCaptureImageFormat) captures composition frames as JPEG quality 95 (80 in draft) unless alpha or motion blur is needed. So an mp4 of phone footage goes through two lossy JPEG steps before x264 encodes it. (node_modules/hyperframes/dist/chunk-CMH5CSTH.js, chunk-VFCR64GO.js)
- [confirmed] snapshot sends frames to Gemini when a key is set, and capture's vision step uses OpenRouter, Gemini or Google keys. The fix is --describe false and --skip-vision. Telemetry is switched off with HYPERFRAMES_NO_TELEMETRY or DO_NOT_TRACK. — snapshot help says: 'Gemini vision frame analysis. Runs by default when GEMINI_API_KEY is set'. The code also accepts GOOGLE_API_KEY. In capture-*.js line 3472, vision runs when skipVision is off and an OPENROUTER, GEMINI or GOOGLE key (or Vertex credentials) is present. The dist reads HYPERFRAMES_NO_TELEMETRY and DO_NOT_TRACK. The media-use skill has its own telemetry, which honors the same two variables. (node_modules/hyperframes/dist/snapshot-F5ZSC5FM.js, capture-42GHDJSH.js, skills/media-use/scripts/lib/telemetry*)
- [confirmed] The registry has 394 items, including motion-blur, cinematic-zoom, code-typing/diff/morph/highlight/scroll/3d-extrude, transitions-3d, ui-3d-reveal and data-chart. There are 21 skills and 22 blueprints. — registry.json on main (fetched 2026-10-05) lists 394 items: 222 components, 164 blocks and 8 examples. Every named item is present. ~/.claude/skills has 21 HyperFrames skills, and hyperframes-animation/blueprints holds 22 files. (https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/registry.json ; ~/.claude/skills)
- [refuted] The registry has 24 code-snippet-* terminal/editor window themes. — The live registry index lists only 3: code-snippet-apple-terminal-pro, code-snippet-dark-2026 and code-snippet-dark-modern. The installed skill doc (hyperframes-registry/references/discovery.md) still says 'Code snippets (24)', so the doc no longer matches the registry. (registry.json; ~/.claude/skills/hyperframes-registry/references/discovery.md)
- [confirmed] The vfx-iphone-device and ios26-liquid-glass blocks are experimental and bundle device models and iOS-style icons with no license metadata. — It is worse than stated. Both registry-item.json files say stability 'experimental' and have no license field. vfx-iphone-device ships 'Real GLTF iPhone 15 Pro Max and MacBook Pro models'. ios26-liquid-glass ships third-party brand icons (instagram, slack, chatgpt, x, proton-mail). (https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/blocks/{vfx-iphone-device,ios26-liquid-glass}/registry-item.json)
- [confirmed] Speed ramps and slow motion on footage can be done in HyperFrames. — This covers retiming only. A constant data-playback-rate from 0.1 to 10 is render-safe, with pitch-preserved audio. A speed ramp is a 'rate' lane in data-automation. Nothing synthesizes new frames, so 0.5x on 30 fps footage repeats each frame (judder). (~/.claude/skills/hyperframes-core/references/creator-editing-recipes.md; hyperframes-keyframes/SKILL.md)
- [refuted] Use ffmpeg minterpolate to prepare slow motion. — It is not the best local option. Measured here: minterpolate (mci/aobmc) turning 1080p30 into 60 fps ran at about 5.7 fps output, 0.09x realtime (1 s of video took 10 s), on the CPU only. Better local paths: Apple VideoToolbox VTFrameProcessor with VTFrameRateConversionConfiguration (macOS 15.4+; VTFrameRateConversionParameters takes an interpolationPhase list, so any slow-down factor works) and VTMotionBlurConfiguration (macOS 15.4+), plus super-resolution and temporal noise filtering on macOS 26+. CommandLineTools swiftc 6.4 can compile a small CLI now. RIFE options: Practical-RIFE (MIT code and weights, pushed 2026-08) and rife-ncnn-vulkan (MIT, macOS zip, last release 2022-10-29). (local ffmpeg timing; https://developer.apple.com/tutorials/data/documentation/videotoolbox/vtframerateconversionconfiguration.json (and vtframeprocessor, vtmotionblurconfiguration, vtframerateconversionparameters); https://github.com/hzwer/Practical-RIFE ; https://api.github.com/repos/nihui/rife-ncnn-vulkan/releases)
- [confirmed] The bundled ffmpeg-static 6.0 has libvmaf, libaom, libsvtav1, libwebp_anim, apng, avif and ProRes. It was built with --enable-nonfree, so do not redistribute it. — The npm package is ffmpeg-static 5.3.0, which ships ffmpeg 6.0 for arm64. Its configure line includes --enable-gpl --enable-version3 --enable-nonfree --enable-libvmaf --enable-libaom --enable-libsvtav1 --enable-libwebp --enable-libzimg --enable-libvidstab. A libvmaf test ran and returned a score. The listed encoders and muxers (including avif) are present. There is no rubberband filter. (local ffmpeg -buildconf / -encoders / -muxers / libvmaf test)
- [confirmed] Every brew command fails until `sudo xcodebuild -license accept` is run. — `brew info vhs` fails with 'You have not agreed to the Xcode license'. `brew --version` still works (Homebrew 7.0.1). The active developer directory is Xcode 27.0. The CommandLineTools clang and swiftc 6.4 work when DEVELOPER_DIR=/Library/Developer/CommandLineTools is set. (local)
- [refuted] About 21.7 GB of disk is free. — df on 2026-10-05 shows 18 GiB available (about 19.3 GB). Other domains have already added ortamlar/ses (1.2 GB) and modeller/ (1.7 GB). The 907 MB HyperFrames extract cache in /var/folders is confirmed. (local df/du)
- [confirmed] Remotion is source-available. It is free for individuals, for-profit companies with up to 3 employees, non-profits and evaluation. The findings' pricing and telemetry rules are right, and 4.0.532 shipped on 2026-10-01. — The eligibility list in LICENSE.md matches. remotion.pro: Creators '$25/mo per seat'; Automators '$0.01 per render, $100/mo minimum'; Enterprise from $500/mo. The telemetry doc says server-side rendering sends telemetry 'only ... when the licenseKey option is set', while client-side rendering will 'always send a telemetry event for every render'. npm latest is 4.0.532 (2026-10-01). New finding: LICENSE.md says the license 'will slightly change' in Remotion 5.0 (PR #3750). (https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md ; https://www.remotion.pro/license ; https://www.remotion.dev/docs/telemetry ; https://registry.npmjs.org/remotion)
- [confirmed] Manim CE 0.21.0 (2026-08-10, MIT) has a [typst] extra. Typst and MathTypst need no TeX, the Cairo renderer is 2.2x faster, max_inflight_encoders exists, Code colors come from Pygments, and PyAV has replaced the ffmpeg CLI since 0.19. — PyPI: 0.21.0 uploaded 2026-08-10, MIT, requires Python 3.11 or newer, and the typst extra pulls typst>=0.14. The changelog states all four changes (the class was renamed MathTypst). The 0.19.0 changelog (2025-01-20) says PyAV 'removes the need to have ffmpeg available as a command line tool'. The dates of 0.19.1/0.19.2/0.20.x match. (https://pypi.org/pypi/manim/json ; https://docs.manim.community/en/stable/changelog/0.21.0-changelog.html ; .../0.19.0-changelog.html)
- [refuted] Manim installs with uv on Python 3.12, only pycairo has to compile, and the typst wheel is about 17 MB. — The main claim holds but the details are off. manimpango 0.7.0 (2026-10-01) has arm64 wheels for cp310 to cp315. pycairo 1.29.2 (uploaded 2026-10-04) ships only an sdist, so it needs a compiler and pkg-config. Brew cairo 1.18.4 and pango 1.58.2 are installed but pkg-config is missing. The PyPI pkgconf 3.0.7.post0 package has an arm64 wheel (MIT). av 19.0.1 requires Python 3.12 or newer. moderngl 5.12.0 has wheels only up to cp313. The typst 0.15.0 arm64 wheel is 30.5 MB, not about 17 MB. The brew manim 0.21.0 formula pulls in python@3.14 and brew ffmpeg. (https://pypi.org/pypi/{pycairo,manimpango,av,moderngl,typst,pkgconf}/json ; https://formulae.brew.sh/api/formula/manim.json ; https://docs.manim.community/en/stable/installation/uv.html)
- [confirmed] Blender 5.2.2 LTS (2026-09-15) runs on Apple Silicon only, needs macOS 13+, has a ~330 MB DMG, LTS support to 2028, and a bpy 5.2.2 wheel for Python 3.13 only (245 MB, GPL-3.0). — blender-5.2.2-macos-arm64.dmg is 346,286,611 bytes, last modified 2026-09-15; 5.2.0 came out 2026-07-14. The LTS page says 'Last updated to 5.2.2 on September 15, 2026', with a 2-year LTS window. The requirements page says 'Blender 5.0 and later require Apple Silicon running macOS 13 (Ventura)', with 8 GB RAM minimum and 32 GB recommended. The brew cask is 5.2.2. bpy 5.2.2 was uploaded 2026-09-15: cp313 only, 245.2 MB, GPL-3.0. The installed size of about 1.3 GB was not verified. (https://download.blender.org/release/Blender5.2/ ; https://www.blender.org/download/lts/ ; https://www.blender.org/download/requirements/ ; https://pypi.org/pypi/bpy/json)
- [confirmed] Blender 5.0 API changes: the engine id is BLENDER_EEVEE, media_type must be set before file_format, compositing_node_group replaces scene.node_tree, and render passes were renamed. — The release notes state all four changes in those words, for example "`scene.node_tree` was removed, use `scene.compositing_node_group` instead". (https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [confirmed] MCP for Blender 2.1.3 (PyPI mcp-for-blender, formerly blender-mcp) is MIT. It sends usage telemetry by default unless DISABLE_TELEMETRY=true, and BLENDER_MCP_SAFE_MODE=1 is available. — PyPI mcp-for-blender 2.1.3 was uploaded 2026-09-30, MIT. The repo moved to ahujasid/mcp-for-blender (29,980 stars). The README collects 'a minimal anonymous usage record' by default (install ID, session ID, tool name, OS, versions), and DISABLE_TELEMETRY=true turns it off. BLENDER_MCP_SAFE_MODE=1 checks scripts before they run. A paid 'Premium' tier generates models through their servers. (https://pypi.org/pypi/mcp-for-blender/json ; https://raw.githubusercontent.com/ahujasid/mcp-for-blender/main/README.md)
- [confirmed] VHS 0.12.1 (2026-09-24) is MIT with an arm64 build. It needs ttyd and ffmpeg; ttyd has no macOS binary; `vhs publish` uploads to vhs.charm.sh. — GitHub releases: v0.12.1 2026-09-24, v0.12.0 2026-09-09, v0.11.0 2026-03-10, each with vhs_*_Darwin_arm64.tar.gz. The README says it 'requires ttyd and ffmpeg ... on your PATH'. ttyd 1.7.7 (2024-03-30) ships Linux and win32 binaries only. The brew vhs formula is MIT and depends on ffmpeg and ttyd. The publish command posts to vhs.charm.sh. (https://api.github.com/repos/charmbracelet/vhs/releases ; https://api.github.com/repos/tsl0922/ttyd/releases ; https://formulae.brew.sh/api/formula/vhs.json)
- [refuted] asciinema 3.2.1 is GPL-3.0-only, and agg 1.9.0 (released 2025-05-29) is GPL-3.0-or-later with the swash/resvg renderers and --select. — The date is wrong: agg v1.9.0 came out 2026-05-29, not 2025. Everything else holds. agg switched to GPL-3.0 in 1.6.0 (2025-09-25) because it uses gifski, and asciicast v3 input has been supported since 1.6.0. swash became the default renderer in 1.8.0. asciinema 3.2.1 came out 2026-06-16 (brew lists GPL-3.0-only). Both projects publish prebuilt aarch64-apple-darwin binaries on GitHub, so neither needs brew. (https://api.github.com/repos/asciinema/agg/releases ; https://api.github.com/repos/asciinema/asciinema/releases ; https://formulae.brew.sh/api/formula/agg.json)
- [refuted] gifski 1.34.0 (released 2026-07-13) is AGPL-3.0-only and installs via brew. — The date is wrong: GitHub shows release 1.34.0 on 2025-07-13, and it is still the latest. Brew's license field is AGPL-3.0-only and the formula depends on brew ffmpeg. The GitHub release ships only a source tarball, with no macOS binary, so it needs brew (blocked until the Xcode license is accepted) or a cargo build. (https://api.github.com/repos/ImageOptim/gifski/releases ; https://formulae.brew.sh/api/formula/gifski.json)
- [confirmed] gifsicle 1.96 is GPL-2.0-only. libwebp 1.6.0 with img2webp is already installed. — Brew says gifsicle 1.96, GPL-2.0-only. /opt/homebrew/Cellar/webp/1.6.0 exists. img2webp reports encoder 1.6.0 and accepts -loop/-lossy/-q/-d. (https://formulae.brew.sh/api/formula/gifsicle.json ; local)
- [uncertain] Playwright 1.63.0 has page.screencast (added in 1.59) with showActions cursor, showChapter, showOverlay and onFrame. Recording at 2x DPR gives crisp frames. — The API is confirmed: npm playwright 1.63.0 on 2026-09-04 (Apache-2.0), Screencast class 'Added in: v1.59', showActions cursor 'pointer'|'none', JPEG frames in onFrame. The crisp-frames part is not shown. By default the size is 'page viewport scaled down to fit into 800×800', and 'the actual frame is scaled to preserve the page's aspect ratio'. The docs don't say whether deviceScaleFactor pixels are kept, so 2880x1800 at 2x is unproven. (https://playwright.dev/docs/api/class-screencast ; https://registry.npmjs.org/playwright)
- [confirmed] puppeteer-core 25.12.0 is already installed, and its page.screencast supports webm/gif/mp4, fps, quality as CRF, crop and scale. — lib/types.d.ts: VideoFormat = 'webm'|'gif'|'mp4'. Options include fps (default 30, 20 for GIF), quality as 'Constant Rate Factor between 0–63', crop, scale, speed and ffmpegPath. (/Users/onurkaya/Projects/video/node_modules/puppeteer-core/lib/types.d.ts)
- [confirmed] The Lottie runtimes are MIT or Apache and the versions are right: dotlottie-web 0.80.0 with WebGL/WebGPU builds, lottie-web 5.13.0 (May 2025), lottie-react-native 7.5.0. dotLottie 2.0 has themes and state machines. — dotlottie-web 0.80.0 (2026-08-28, MIT) exports ./webgl and ./webgpu (7.4 MB unpacked). lottie-web 5.13.0 is from 2025-05-21. lottie-react-native 7.5.0 (2026-08-22) is Apache-2.0. lottie-ios and lottie-android are Apache-2.0. dotlottie-rs, dotlottie-ios, dotlottie-android and ThorVG are MIT. The dotLottie 2.0 spec defines themeable slots and state machines with pointer and complete events. (npm registry; GitHub API; https://dotlottie.io/spec/2.0)
- [confirmed] text-to-lottie (MIT, ~5.5k stars) and dotlottie-js 1.8.0 (MIT) are no-account Lottie authoring tools. — diffusionstudio/lottie: 5,539 stars, MIT, v1.0.0 on 2026-06-15, last commit 2026-07-25, installed with `npx skills add diffusionstudio/lottie`. @dotlottie/dotlottie-js 1.8.0 is from 2026-08-10, MIT. The skills CLI honors DISABLE_TELEMETRY=1 and DO_NOT_TRACK=1, which also switch off its security-audit requests. (https://api.github.com/repos/diffusionstudio/lottie ; https://registry.npmjs.org/@dotlottie/dotlottie-js ; https://raw.githubusercontent.com/vercel-labs/skills/main/README.md)
- [refuted] python-lottie 0.7.2 (AGPL) installs with `uv pip install 'lottie[gif,video]'` and imports SVG, TGS, dotLottie, GIF and MP4. — The version and license are right: 0.7.2 uploaded 2025-05-01, AGPL. The install command fails on this Mac: the 'gif' extra requires the PyPI package glaxnimate 0.6.0.3, which ships only a manylinux x86_64 wheel and no sdist, so the resolve fails on macOS arm64. The README's format table also marks MP4 and WebM as export-only. (https://pypi.org/pypi/lottie/json ; https://pypi.org/pypi/glaxnimate/json ; https://gitlab.com/mattbas/python-lottie/-/raw/master/README.md)
- [confirmed] Glaxnimate 0.6.0 is GPL-3 and has an ARM dmg. — The KDE GitLab API reports license gpl-3.0 and activity on 2026-10-04. The download page links glaxnimate-0.6.0-arm64.dmg. (https://invent.kde.org/api/v4/projects/graphics%2Fglaxnimate?license=true ; https://glaxnimate.org/download/)
- [confirmed] The Three.js stack is MIT with these versions: three 0.186.1 (2026-09-24), R3F 9.8.1, glTF-Transform 4.5.1 (2026-09-28), troika 0.52.5 (2026-07-24). Poly Haven's API is free, its assets are CC0, and it requires a credit and a unique User-Agent. — npm metadata matches every version and date, all MIT. Poly Haven says the API 'is free to use, for any purpose'. A credit is needed only when the live API is used inside a product, and every request needs a 'unique User-Agent header'. The assets are CC0. (npm registry; https://polyhaven.com/our-api)
- [confirmed] GSAP 3.15.0 uses the Standard 'no charge' license, has been free since 3.13 (2025-04-30), and allows commercial use except in tools that compete with Webflow's visual builder. The bonus plugins are already installed locally. SVGO 4.1.0 and anime.js 4.5.0 are MIT. — npm: gsap 3.13.0 on 2025-04-30 and 3.15.0 on 2026-04-13, both under the 'Standard no charge' license. The license page allows commercial use and forbids use in visual no-code animation builders that compete with Webflow. node_modules/gsap/dist contains DrawSVGPlugin, MorphSVGPlugin, MotionPathPlugin, CustomEase, Flip and InertiaPlugin. svgo 4.1.0 (2026-08-24) and animejs 4.5.0 (2026-06-22) are MIT. (https://registry.npmjs.org/gsap ; https://gsap.com/community/standard-license/ ; local)
- [confirmed] App Store preview spec: 15–30 s, 500 MB max, 30 fps, H.264 High L4.0 at 10–12 Mbps or ProRes 422 HQ, 256 kbps stereo AAC, up to 3 previews, 5 s poster frame, 886x1920 for iPhone 6.9/6.5/6.3/6.1, among other sizes. — The Apple spec page matches every item, including the iPad 1200x1600, Mac and Apple TV 1920x1080, and Vision Pro 3840x2160 sizes. (https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications)
- [confirmed] Google Play specs, GitHub attachment limits (10 MB on free plans, 100 MB on paid), and Telegram TGS and video sticker limits. — Google Play: YouTube URL, public or unlisted, ads off, not age-restricted, embeddable; feature graphic 1024x500 JPEG or 24-bit PNG; icon 512x512 32-bit PNG, 1024 KB max. GitHub: 10 MB for images and GIFs, 10 MB for videos on free plans, 100 MB on paid. Telegram: TGS 512x512, 60 fps, 3 s max, 64 KB; video stickers VP9 WebM, one side exactly 512, 3 s max, 30 fps max, 256 KB, no audio. (https://support.google.com/googleplay/android-developer/answer/9866151 ; https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files ; https://core.telegram.org/stickers)
- [confirmed] WhatsApp animated stickers are 512x512 WebP, 500 KB max (cited from a third-party spec). — WhatsApp's own repo confirms it: exactly 512x512 WebP, 500 KB max for animated stickers, frames at least 8 ms, 10 s total max, and the first frame should show the complete sticker. (https://raw.githubusercontent.com/WhatsApp/stickers/main/Android/README.md)
- [refuted] Rive needs an account, and since 2025-10-20 exporting needs a paid plan (Cadet, $9/month billed annually). — The pricing page says the Free plan can export .riv files, but 'Free exports play a Rive splash screen. Upgrade to remove it.' Cadet is $9/seat/mo with a maximum of 3 seats. The 2025-10-20 date is not on the page. The account requirement still stands. @rive-app/canvas 2.44.0 (2026-09-30) is MIT. (https://rive.app/pricing ; https://registry.npmjs.org/@rive-app/canvas)
- [confirmed] Theatre.js last released 0.7.2 on 2024-05-19, @theatre/studio is AGPL-3.0-only, and development moved to a private repo. — npm: @theatre/core and @theatre/studio 0.7.2 on 2024-05-19; studio is AGPL-3.0-only. The GitHub repo was last pushed 2024-08-14. The private-repo move was not checked independently. (https://registry.npmjs.org/@theatre/studio ; https://api.github.com/repos/theatre-js/theatre)
- [refuted] Motion Canvas has had no stable release since 3.17.2 (2024-12-14) and motioncanvas.io is offline. Canvas Commons 0.4.0 came out 2026-09-24. — Partly wrong. On 2026-10-05 motioncanvas.io returns HTTP 200 and serves the Docusaurus docs, so it is not offline. The release part is right: npm latest is 3.17.2 (2024-12-14), with only 3.18.0-alpha.0 (2025-02-16) since; the repo was last pushed 2026-07-02. @canvas-commons/core 0.4.0 (2026-09-24, MIT) is confirmed. The claim that rendering works only through the editor was not verified. (curl https://motioncanvas.io ; https://registry.npmjs.org/@motion-canvas/core ; https://registry.npmjs.org/@canvas-commons/core)
- [confirmed] Revideo: 0.11.0 in Jul 2026, the repo moved to midrender/revideo, and it has no GitHub releases. — @revideo/core 0.11.0 is from 2026-07-10. redotvideo/revideo redirects to midrender/revideo (MIT, 4,081 stars), and its releases list is empty. (https://registry.npmjs.org/@revideo/core ; https://api.github.com/repos/midrender/revideo/releases)
- [confirmed] Avoid TRELLIS.2 (about 18 GB RAM peak on a Mac, gated models) and Hunyuan3D (its license excludes the EU, UK and South Korea). — The decision is right, but the stronger evidence is the official requirements. The TRELLIS.2 README says it is 'tested only on Linux' and needs 'an NVIDIA GPU with at least 24GB', so Macs are unsupported. The 18 GB Mac figure is unverified. The Hunyuan3D-2.1 LICENSE says it 'DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA' and adds a clause for services above 1M monthly active users. (https://raw.githubusercontent.com/microsoft/TRELLIS.2/main/README.md ; https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE)
- [confirmed] The Homebrew thorvg formula builds only the library, without the lottie2gif or svg2png tools. — thorvg.rb (1.1.2) builds with -Dengines=cpu -Dloaders=all -Dsavers=all -Dbindings=capi -Dtests=false. There is no -Dtools, so no CLIs are installed. (https://raw.githubusercontent.com/Homebrew/homebrew-core/main/Formula/t/thorvg.rb)
- [uncertain] 2026 comparisons report that agents do better writing HTML+GSAP than Remotion TSX. — The cited arceapps post (2026-07-14) relies on HeyGen's internal evaluations and a YouTuber anecdote. It gives no numbers or method, so it is weak evidence. (https://arceapps.com/blog/hyperframes-vs-remotion-2026/)
- [confirmed] The home-made numpy beat tracker should be avoided; beat times should come from a vetted tracker. — The findings miss a related problem: HyperFrames' own `hyperframes beats` is in the same class. dist/beat-analyzer.global.js bundles bpm-detective 2.0.5 plus RMS energy peaks on channel 0, then fits a constant-tempo grid to the first 10 onsets. The music-to-video skill's analyze-beatgrid.py uses librosa.beat.beat_track, and its SKILL.md says that on calm music 'the grid is a metronome the tracker imposed'. Beat This! is MIT for both code and weights, and beat_this 1.1.0 is already installed in ortamlar/ses. (node_modules/hyperframes/dist/beat-analyzer.global.js ; ~/.claude/skills/music-to-video/SKILL.md ; https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md)

### Düzeltmeler (seçimlerin önüne geçer)

- **Slow motion on real footage (the user explicitly asked for slow motion)**: Replace 'use ffmpeg minterpolate' with a tiered path. 1) Prefer high-frame-rate sources (iPhone 60/120/240 fps) and retime with data-playback-rate or a rate lane; no frames are invented. 2) For 24/30 fps sources, use Apple VideoToolbox VTFrameProcessor: VTFrameRateConversionConfiguration with an interpolationPhase list (macOS 15.4+), optionally VTMotionBlurConfiguration for whip pans or speed ramps. Drive it from a small Swift CLI compiled with /Library/Developer/CommandLineTools/usr/bin/swiftc (DEVELOPER_DIR set, so no Xcode license is needed). It is a built-in OS framework, so there is nothing to download and outputs can be used commercially. This CLI has not been built yet, so treat the plan as medium confidence. 3) Fallbacks: Practical-RIFE 4.25 (MIT code and weights; PyTorch MPS, untested on M2) or rife-ncnn-vulkan 20221029 (MIT, macOS zip about 437 MB, unmaintained since 2022). 4) Use minterpolate only as a last resort. To verify: mpdecimate shows no duplicate frames inside slowed segments, snapshots at mid-phase frames are Read and checked for warping or ghosting, and SSIM between consecutive frames has no spikes. — gerekçe: Measured on this M2, minterpolate ran at 0.09x realtime at 1080p, on the CPU only, and it is known for artifacts. HyperFrames' playback-rate only repeats frames.
- **Beat source for cuts (the cause of the earlier 'audio slipping')**: Add `hyperframes beats` to the avoid list: it is bpm-detective plus energy peaks forced onto a constant-tempo grid. Treat the music-to-video analyzer (librosa beat_track) as unreliable on soft or acoustic songs. Use Beat This! (MIT code and weights, already in ortamlar/ses) for beats and downbeats, and require a second tracker (librosa or essentia) to agree within ±70 ms on at least 90% of beats before hard-cutting on the grid. Otherwise cut on phrase boundaries and strong onsets. Keep the cut-versus-beat check, but add this validation step for the beat list itself. — gerekçe: The findings' alignment check only proves that cuts match the beat list. If the list is wrong, as in the earlier failure, the check passes anyway.
- **Image quality of footage montages rendered with HyperFrames**: Mention that the defaults use lossy intermediates. 'auto' extracts footage frames as JPEG, and opaque outputs are captured as JPEG quality 95 (80 in draft). For footage-heavy pieces, run a 5 s A/B test: the default mp4 against `--video-frame-format png --format mov` (a ProRes 4444 master, which is captured as PNG), with the delivery encode made by ffmpeg in both cases. Compare VMAF and PSNR. Use the lossless path only if the difference is measurable, because it costs a lot of disk (ProRes 4444 1080p is roughly 2+ GB per minute, an estimate). — gerekçe: Verified in the dist code (resolveFrameFormat, resolveCaptureImageFormat).
- **Determinism proof (framemd5 equality)**: Run the double render with `--no-browser-gpu` (SwiftShader) and `--experimental-fast-capture=false`, or compare with a tolerance (PSNR ≥ 50 dB or SSIM ≥ 0.999) when hardware-GPU capture is used. — gerekçe: HyperFrames' own help calls SwiftShader the deterministic mode. The default on this Mac is a hardware GPU with drawElementImage fast capture.
- **Cut/accent timing verification**: Take the intended cuts from `hyperframes timeline --json` (clip starts) and check the rendered hard cuts with ffmpeg scdet or select=scene. Check dissolves, whips and match cuts by snapshotting their midpoints, not by scene scores. — gerekçe: Scene-change scores miss gradual transitions and fire twice on flashes or whip pans.
- **Disk budget figure**: Use 18 GiB free as of 2026-10-05, not 21.7 GB. Treat Blender (about 1.3 GB installed, unverified) as optional. Move or clean the 907 MB extract cache with `hyperframes clean` or --frames-cache-dir. — gerekçe: Measured with df. Other domains' installs already used about 3 GB.
- **python-lottie install command**: Use `uv pip install lottie` or `lottie[video]` and never `lottie[gif]` on macOS. Render GIF and WebP through HyperFrames, ffmpeg or img2webp instead. Also correct the text: MP4 and WebM are export-only, so python-lottie cannot import them. — gerekçe: The gif extra depends on PyPI glaxnimate 0.6.0.3, which has only a manylinux x86_64 wheel and no sdist, so the resolve fails.
- **GIF tooling dates and install route**: gifski 1.34.0 is from 2025-07-13, not 2026. It has no prebuilt macOS binary, so it needs brew after the license is accepted, or a cargo build. Until then the ffmpeg palettegen/paletteuse fallback works today. — gerekçe: GitHub releases API.
- **Terminal demo capture without brew**: agg 1.9.0 is from 2026-05-29, not 2025. Download the agg and asciinema 3.2.1 aarch64-apple-darwin binaries from GitHub releases into arac/, so no brew is needed. VHS still needs brew for ttyd. Add `asciinema stream` and `asciinema session` to the avoid list, since both connect to a server. — gerekçe: GitHub releases and the release notes.
- **Rive avoid reason**: Reword it as: Rive needs an account. The Free plan exports carry a Rive splash screen, and Cadet ($9/seat/mo, up to 3 seats) removes it. The 2025-10-20 change date is unverified. — gerekçe: rive.app/pricing.
- **Motion Canvas avoid reason**: Drop 'motioncanvas.io is offline'. Keep the stale-release reason: 3.17.2 from 2024-12-14 is the last stable release, with only a 3.18.0-alpha.0 since. — gerekçe: The site returned HTTP 200 on 2026-10-05.
- **Code-block inventory and device mockups**: Say that 3 code-snippet-* blocks exist, not 24, and check `hyperframes catalog` before promising a theme. Mark vfx-iphone-device and ios26-liquid-glass as not for commercial work: they contain Apple device models and third-party brand icons (Instagram, Slack, ChatGPT, X, Proton Mail) with no license field. Prefer device-frame-stage, browser-device-stage or CC0 or self-made models. Note that shiki-magic-move is deprecated in favor of @shikijs/magic-move. — gerekçe: registry.json and registry-item.json; npm deprecation notice.
- **Manim environment pinning**: Use Python 3.12 for the venv, not 3.11 or 3.14: av 19 requires Python 3.12 or newer, and moderngl has no cp314 wheel. Expect the typst wheel to be about 30.5 MB. Prefer the uv venv to brew manim, which pulls in python@3.14 and brew ffmpeg 9.0.2 with its codec libraries. — gerekçe: PyPI and Homebrew metadata.
- **3D and AI generation avoid list**: Restate the TRELLIS.2 reason with its official requirements: Linux only, an NVIDIA GPU with at least 24 GB, CUDA 12.4. Add local AI image-to-video and text-to-video to the avoid list for this machine. Wan2.2-TI2V-5B (Apache-2.0) is a 34.2 GB repo, which is more than the free disk. Lightricks/LTX-Video uses a custom ('other') license. — gerekçe: TRELLIS.2 README and the Hugging Face API.
- **Playwright demo capture**: Always pass an explicit screencast size. The default fits within 800×800, and the output is WebM built from JPEG frames. Check the real pixel density with ffprobe and Read a zoomed frame before relying on 2x. For the sharpest UI, consider native Retina `screencapture -v -C -k` (flags verified locally) or rebuilding the UI in HyperFrames. — gerekçe: The Playwright docs do not say whether deviceScaleFactor pixels are kept.
- **Homebrew wording**: Say that brew info and brew install fail, while brew --version still works. — gerekçe: Verified locally.

### Eksik bulunanlar

- ML frame interpolation and optical-flow motion blur for real footage. Apple VTFrameProcessor provides frame-rate conversion and motion blur on macOS 15.4+, and super-resolution, temporal noise filtering and low-latency interpolation on macOS 26+. Practical-RIFE and rife-ncnn-vulkan are fallbacks. The findings offer only minterpolate, although the user asked for slow motion.
- Monocular depth for 2.5D photo parallax (the '3D Ken Burns' look on still photos). Depth-Anything-V2-Small, Video-Depth-Anything-Small, DA3-SMALL and DA3-BASE are Apache-2.0, so commercial use is fine. Depth-Anything-V2 Base/Large and DA3-LARGE are CC-BY-NC-4.0. Apple Depth Pro is 'apple-amlr', research use only. Combine the depth map with HyperFrames layers or Three.js displacement.
- Subject cut-outs for layered parallax: the built-in `hyperframes remove-background` (local ONNX with a CoreML provider; the binary references u2net_human_seg, isnet-general-use and birefnet-portrait). Which model is the default, and its license, was not verified; confirm both before commercial use.
- Flag that `hyperframes beats` and the music-to-video beat grid are unreliable on soft songs. Name Beat This! (MIT, already installed) as the beat and downbeat source, and add a phrase-based pacing rule for calm music.
- A policy for lossless masters and intermediates (PNG, ProRes 4444 or JPEG capture) with disk math, given 18 GiB free and HyperFrames' JPEG intermediates.
- iPhone HDR (HLG or Dolby Vision) and variable-frame-rate footage in HyperFrames (--hdr / --sdr; zscale and tonemap are available in ffmpeg-static). Cross-check with the video-editing domain.
- Optional hand-off to a human editing app for fine-tuning (for example OpenTimelineIO into Kdenlive or DaVinci Resolve). Not researched here.
- An optional GUI keyframer for hands-on tweaks: Glaxnimate 0.6.0 (GPL-3.0, arm64 dmg). Friction (GPL-3.0) is active, but its latest 1.0.0-rc.3 (2025-12-31) has no macOS build; the last arm64 dmg was rc.2 (2025-08-06).
- Remotion's license changes in 5.0 (LICENSE.md, PR #3750). Re-check it before any work adoption.
- Real-time 3D cinematics as an alternative to Blender, such as Godot's Movie Maker mode (MIT). Not evaluated.
