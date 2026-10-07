# Claude Code ekosistemi — araştırma ve doğrulama (2026-10-05)

> Kaynak: 9 araştırmacı + 9 şüpheci doğrulayıcı ajan (web + yerel ölçüm). Kanıt tarihleri satırlarda. Bu dosya bilgi tabanıdır; karar ve kurallar becerilerde (sistem/claude/skills) ve yetenekler.toml'dadır.

## Özet

Evidence date: 2026-10-05. Sources are official docs (code.claude.com, platform.claude.com), the package registries, and a read-only inspection of this Mac.

The biggest gains come from wiring up what already exists, not from adding new tools.

(1) The hook is written but not connected. `~/.claude/hooks/medya-koruma.py` exists, but `~/.claude/settings.json` has no `hooks` key, so nothing is enforced today. The vendor HyperFrames skill text tells agents to run `npx hyperframes usage --json` at the start of a workflow and `npx hyperframes feedback` after renders, so the rules in CLAUDE.md are easily overridden. Only a PreToolUse hook that exits with code 2 is deterministic. I tested the hook by piping commands into it on stdin:
- It blocks the common forms.
- It does NOT block `sh -c "..."`, `bash -lc '...'`, or `node node_modules/hyperframes/bin/hyperframes.mjs usage`.
- It lets invalid input through (fail-open), and the docs say hook timeouts are fail-open too.

(2) Telemetry and update switches are missing from this session. The Bash environment here has neither HYPERFRAMES_NO_TELEMETRY nor DO_NOT_TRACK.
- The media-use skill's PostHog telemetry (`scripts/lib/telemetry.mjs`) opts out ONLY through those environment variables. It ignores `telemetryEnabled:false` in `~/.hyperframes/config.json`.
- The HyperFrames 0.8.124 CLI checks for updates and silently starts a background install of newer minor versions unless HYPERFRAMES_NO_UPDATE_CHECK=1 is set.
- `snapshot` calls Gemini by default whenever GEMINI_API_KEY is set.
- Fix: set these variables once in the settings.json `env` block, which reaches every subprocess.

(3) Add a QA subagent (`~/.claude/agents/medya-qa.md`). It has tools Read, Bash, Glob and Grep, plus `memory: user`. It must return a measured PASS or FAIL for:
- A/V offset and drift, measured by cross-correlation against a known-offset self-test.
- Cut-to-beat residuals, checked against a tracker-agreement test.
- Loudness (LUFS) and true peak.
- Black, frozen and blurry frames.
- Contact sheets no wider than 2000 px, with tiles of at least 200 px.

(4) Store lessons as skills that follow Anthropic's best practices:
- name: at most 64 characters, lowercase letters, digits and hyphens.
- description: at most 1,024 characters, third person, says what the skill does and when to use it, key use case first. Claude Code truncates description plus `when_to_use` at 1,536 characters.
- SKILL.md body under 500 lines; references one level deep; scripts are run, not read.
- After auto-compaction only the first 5,000 tokens of each skill are kept.

The failed montage ignored HyperFrames' own music-to-video rule: on calm music the beat grid is a metronome the tracker imposed, so pace by phrases and never hard-cut to the beat.

(5) MCP servers:
- Keep Playwright. Adding `--caps=devtools` enables browser video recording.
- For 3D, drive Blender through its CLI. mcp-for-blender 2.1.3 (MIT) is optional and needs `DISABLE_TELEMETRY=true`.
- Avoid ComfyUI (Comfy itself does not recommend local diffusion under 32 GB of memory; this Mac has 16 GB), ffmpeg MCP wrappers, the DaVinci Resolve MCP (needs the paid Studio edition), and Figma, Canva, Adobe and Runway (all need accounts).

(6) The terminal `claude` is version 2.1.259, while the VS Code extension runs 2.1.289. `claude plugin eval`, which measures how reliably a skill triggers, needs at least 2.1.269.

## Seçimler

### Deterministic enforcement of the media hard rules even when vendor skill text says otherwise: no HyperFrames cloud, lambda, cloudrun, auth, publish, usage or feedback; snapshot only with --describe false; telemetry stays off
- **Seçim:** A PreToolUse command hook on Bash that runs the already-written /Users/onurkaya/.claude/hooks/medya-koruma.py. It is currently NOT registered: ~/.claude/settings.json has no "hooks" key.
- Alternatifler: - permissions.deny rules such as Bash(npx hyperframes cloud *): a cheap first layer that still works if Python breaks, but the docs say Bash rules only match the literal form and are not a security boundary.
- The hookify plugin from the official marketplace, which uses markdown regex rules.
- The sandbox network allowlist as an OS-level backstop.
- Neden: The memory doc says CLAUDE.md and auto-memory are context, not enforced configuration, and recommends a PreToolUse hook to block an action regardless of what Claude decides.

Verified conflict in local files: ~/.claude/skills/hyperframes-cli/SKILL.md tells agents to run `npx hyperframes usage --json` at the start of a workflow (it reads the Claude Code or Codex login) and `npx hyperframes feedback` after renders (which posts to a public channel).

How the hook behaves per the docs: exit 2 blocks the call before permission rules are evaluated, and stderr is sent back to Claude. Hooks defined in settings also fire inside subagents.

Stdin tests on 2026-10-05:
- Blocks `npx hyperframes cloud`, env-prefixed `usage`, path-prefixed `feedback`, `npx --yes hyperframes@latest auth login`, and snapshot without --describe false.
- Lets through `sh -c "npx hyperframes cloud render"`, `bash -lc 'hyperframes publish'` and `node node_modules/hyperframes/bin/hyperframes.mjs usage`.
- Exits 0 on invalid input.

The docs also say exit codes other than 2, and hook timeouts, are non-blocking, so the hook fails open.
- Lisans: kod n/a (your own script; Claude Code feature) · ağırlık - · ticari: yes
- Apple Silicon: n/a: python3 standard library only, adds tens of milliseconds per Bash call
- Kurulum: 1. Merge into ~/.claude/settings.json (strict JSON, reloaded live):
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/medya-koruma.py","timeout":10,"statusMessage":"medya-koruma"}]}]}}
2. Confirm it is registered with /hooks.
3. Harden the script:
- recurse into the -c argument of sh, bash and zsh;
- treat `node .../hyperframes/bin/hyperframes.mjs` the same as `hyperframes`;
- add a final regex backstop over the raw command text for hyperframes followed by a forbidden subcommand;
- wrap main() in try/except and exit 2 whenever 'hyperframes' appears in the raw stdin, so it fails closed.
4. Optionally also block `events` and `upgrade`.
- Disk: ~0 MB · bakım: Hook schema checked against code.claude.com/docs/en/hooks on 2026-10-05. The running Claude Code (VS Code extension) is 2.1.289, which equals the npm latest.
- Ajan kullanımı: Runs automatically on every Bash call, including inside subagents. Claude receives the 'ENGELLENDİ (medya-koruma): ...' message on stderr and has to re-plan. To regression-test, pipe crafted {"tool_input":{"command":...}} JSON into the script and check for exit code 2.
- Güven: high · kaynaklar: https://code.claude.com/docs/en/hooks, https://code.claude.com/docs/en/permissions, https://code.claude.com/docs/en/memory, /Users/onurkaya/.claude/skills/hyperframes-cli/SKILL.md, /Users/onurkaya/.claude/hooks/medya-koruma.py

### Telemetry, update-check and vision-upload switches present in every Bash, hook and MCP subprocess, without depending on `source ortam.sh`
- **Seçim:** An `env` block in ~/.claude/settings.json (user scope)
- Alternatifler: A SessionStart hook that writes to CLAUDE_ENV_FILE (used for PATH, see the next pick), or `source ortam.sh` before every command, which is fragile.
- Neden: The env-vars doc says variables in the settings `env` block apply to the session and its subprocesses no matter how claude was launched.

Verified gaps on this machine:
- This session's Bash environment has neither HYPERFRAMES_NO_TELEMETRY nor DO_NOT_TRACK.
- media-use's PostHog telemetry (~/.claude/skills/media-use/scripts/lib/telemetry.mjs, posting to us.i.posthog.com) opts out ONLY through HYPERFRAMES_NO_TELEMETRY=1, DO_NOT_TRACK=1, CI or NODE_ENV=development. It ignores telemetryEnabled:false in ~/.hyperframes/config.json.
- HyperFrames CLI 0.8.124 (dist/autoUpdate-*.js) checks for updates and spawns a detached background install of newer minor or patch versions unless HYPERFRAMES_NO_UPDATE_CHECK=1 (or HYPERFRAMES_NO_AUTO_INSTALL=1) is set.
- `hyperframes init` checks skills against GitHub unless HYPERFRAMES_SKIP_SKILLS=1 is set.
- `snapshot --describe` runs Gemini vision by default when GEMINI_API_KEY is set.
- DISABLE_TELEMETRY and DO_NOT_TRACK are also honoured by the `npx skills` CLI and by mcp-for-blender.
- Lisans: kod n/a (Claude Code setting) · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: Add to ~/.claude/settings.json:
{"env":{"HYPERFRAMES_NO_TELEMETRY":"1","DO_NOT_TRACK":"1","HYPERFRAMES_NO_UPDATE_CHECK":"1","HYPERFRAMES_SKIP_SKILLS":"1","HF_HUB_DISABLE_TELEMETRY":"1","GRADIO_ANALYTICS_ENABLED":"False","HOMEBREW_NO_ANALYTICS":"1","DISABLE_TELEMETRY":"1"}}

Notes:
- DISABLE_TELEMETRY also turns off Claude Code's own telemetry; that is the user's choice. Any non-empty value, even 0, turns it on.
- Optional defence in depth: "GEMINI_API_KEY":"", "GOOGLE_API_KEY":"" and "OPENROUTER_API_KEY":"". An empty string counts as unset in Node; check with `npx hyperframes auth status`.
- Do NOT use CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC for this. It also disables auto-updates, feature flags (Remote Control) and claude.ai plugin and skill sync.
- Disk: ~0 MB · bakım: Variable names read from the HyperFrames 0.8.124 source on 2026-10-05.
- Ajan kullanımı: Applies automatically. Check with `echo $HYPERFRAMES_NO_UPDATE_CHECK $DO_NOT_TRACK` in a fresh Bash call; it should print `1 1`.
- Güven: high · kaynaklar: https://code.claude.com/docs/en/env-vars, https://code.claude.com/docs/en/settings, /Users/onurkaya/.claude/skills/media-use/scripts/lib/telemetry.mjs, /Users/onurkaya/Projects/video/node_modules/hyperframes/dist (autoUpdate-*.js, snapshot-*.js, telemetry-*.js)

### Workspace PATH (arac/, .venv/bin, node_modules/.bin) and the uv and Hugging Face cache locations loaded automatically in every session
- **Seçim:** A project SessionStart hook that appends the exports from ortam.sh to $CLAUDE_ENV_FILE, using the pattern documented in the hooks reference
- Alternatifler: Wrapper scripts that source ortam.sh themselves.
- Neden: PATH can't be prepended through the `env` block, because env values don't expand $PATH. The hooks doc says CLAUDE_ENV_FILE persists `export` lines for all later Bash commands in the session. It also documents a diff pattern for this: take `export -p` before and after running setup commands and append the difference. Project hooks run only after the workspace-trust dialog has been accepted.
- Lisans: kod n/a · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: 1. /Users/onurkaya/Projects/video/.claude/settings.json:
{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"bash $CLAUDE_PROJECT_DIR/.claude/hooks/ortam-yukle.sh"}]}]}}
With no matcher it fires on startup, resume, clear and compact.
2. Contents of ortam-yukle.sh:
[ -n "$CLAUDE_ENV_FILE" ] || exit 0
B=$(export -p|sort)
source "$CLAUDE_PROJECT_DIR/ortam.sh"
A=$(export -p|sort)
comm -13 <(echo "$B") <(echo "$A") >> "$CLAUDE_ENV_FILE"
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: Applies transparently. To verify, run `which ffmpeg` (should resolve to .../arac/ffmpeg) and `echo $UV_CACHE_DIR $HF_HOME` (should show workspace paths) in a fresh session.
- Güven: medium · kaynaklar: https://code.claude.com/docs/en/hooks

### An independent, measurement-only reviewer before any claim that a video, animation or audio file is done. The assistant can't listen, and the main thread is biased by its own plan.
- **Seçim:** A user-level custom subagent at ~/.claude/agents/medya-qa.md
- Alternatifler: A `type: "agent"` Stop hook (experimental per the docs), or the skill-creator grader agent.
- Neden: The sub-agents doc lists these frontmatter fields: name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills (preloads the full skill content), mcpServers, hooks, memory, background, effort, isolation, color, initialPrompt.

Why this setup works:
- `memory: user` gives the agent ~/.claude/agent-memory/medya-qa/, and the first 200 lines or 25 KB of its MEMORY.md are injected at every start. Recurring defects are learned across projects.
- Read returns images as visual content, so the subagent can inspect contact sheets and spectrograms.
- Session hooks also apply inside subagents, so the rule hook still holds.
- Claude delegates automatically based on the description, or you can name it with @agent-medya-qa.
- A fresh context avoids the main thread's confirmation bias.
- Lisans: kod n/a · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: ~/.claude/agents/medya-qa.md

Frontmatter:
---
name: medya-qa
description: Independent measured QA for any rendered media (MP4/MOV/GIF/PNG/WAV). Use proactively after every render or export and before telling the user a video, animation or audio is finished.
tools: Read, Bash, Glob, Grep
model: inherit
effort: high
memory: user
color: orange
---

Body checklist:
1. ffprobe streams, durations, start_time, fps and rotation.
2. ebur128 integrated loudness and true peak.
3. A/V offset and drift against the source audio.
4. Cut-to-beat residuals and the tracker-agreement test.
5. blackdetect, freezedetect, blurdetect and signalstats exposure jumps.
6. Contact sheets and transition strips, then Read them.
7. Output a PASS/FAIL table with numbers and file paths. Never say something sounds good. Append recurring defects to MEMORY.md.
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: 'Use the medya-qa subagent on <render.mp4> with source audio <song>' or @agent-medya-qa. Manage it with /agents.
- Güven: high · kaynaklar: https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/tools-reference

### Turn hard-won craft and lessons (ordering, transitions, punch-ins, slow-mo, beat versus phrase pacing, sync checks) into reusable knowledge that triggers on the next request
- **Seçim:** Own media skills authored to Anthropic's best practices. Put them in ~/.claude/skills/<name>/, or keep the sources in the git-versioned workspace and symlink them in. Once stable, package them as a skills-dir plugin with `claude plugin init medya --with skills`.
- Alternatifler: Path-scoped rules in .claude/rules/*.md with `paths:` frontmatter for HTML composition conventions; CLAUDE.md kept under about 200 lines for always-on facts.
- Neden: Where skills live (docs, 2026-10-05):
- Personal: ~/.claude/skills, loaded for all local projects but not in cloud or Cowork sessions.
- Project: .claude/skills; its hooks and allowed-tools wait for workspace trust.
- Precedence: enterprise > personal > project. Plugin skills are namespaced as /plugin:skill. Symlinked folders are supported and loaded once.

Frontmatter rules:
- name: at most 64 characters, lowercase letters, digits and hyphens, no 'anthropic' or 'claude'.
- description: third person, says what and when, key use case first, at most 1,024 characters (API spec). Claude Code truncates description plus when_to_use at 1,536 characters.
- when_to_use: extra trigger phrases.
- allowed-tools: pre-approves tools for that turn only, e.g. Bash(${CLAUDE_SKILL_DIR}/scripts/*).
- disable-model-invocation:true: manual-only skills such as a final high-quality render.
- user-invocable:false: background knowledge only.
- paths: glob-scoped activation.
- context: fork plus agent: run in an isolated subagent.
- model and effort: per-skill overrides.
- hooks: registered for the rest of the session.
- !`cmd`: dynamic context that runs before Claude sees the skill.

Structure rules:
- SKILL.md under 500 lines.
- References one level deep; a table of contents in files over 100 lines.
- Scripts are executed, not read.
- Plan, validate, then execute, with verbose validators.
- No time-sensitive text.
- After auto-compaction each re-attached skill keeps only its first 5,000 tokens (25,000 shared, newest first), and the file isn't re-read. Put hard rules at the top of SKILL.md and in hooks.

Why a skills-dir plugin: it loads every session as medya@skills-dir and can also carry agents/, hooks/hooks.json and .mcp.json. Personal-scope plugins have no trust restrictions. `claude plugin eval` requires a plugin or skills-dir plugin.
- Lisans: kod n/a (Agent Skills open standard, agentskills.io) · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: 1. Example layout: ~/.claude/skills/medya-kurgu/
- SKILL.md
- references/kurgu-zanaati.md
- references/ses-senkron.md
- references/ffmpeg-tarifler.md
- scripts/contact_sheet.sh
- scripts/spectrogram.sh
- scripts/av_offset.py
- scripts/cut_beat_check.py
2. Validate with `claude plugin validate ~/.claude/skills` (v2.1.233+).
3. Packaging, when stable: `claude plugin init medya --with skills` creates ~/.claude/skills/medya/.claude-plugin/plugin.json.
- Disk: ~1 MB · bakım: 
- Ajan kullanımı: Claude selects skills from the name and description; the user can also type /medya-kurgu. Scripts are referenced as ${CLAUDE_SKILL_DIR}/scripts/x.
- Güven: high · kaynaklar: https://code.claude.com/docs/en/skills, https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, https://code.claude.com/docs/en/plugins/create, https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/memory

### Measure whether a skill actually triggers and improves output, instead of guessing
- **Seçim:** skill-creator (already synced from claude.ai as anthropic-skills:skill-creator; also available as skill-creator@claude-plugins-official), plus `claude plugin validate` and `claude plugin eval`
- Alternatifler: Manual A/B runs.
- Neden: skill-creator:
- Runs with-skill and baseline subagent runs.
- Grades assertions (grading.json, benchmark.json) and supports a blind A/B comparison.
- Has a description-optimization loop: about 20 realistic queries split 60/40 into train and held-out test, 3 runs per query, up to 5 iterations, picking best_description by the held-out score.

`claude plugin eval`:
- Runs isolated non-interactive sessions with and without the plugin.
- Supports graders including `type: tool_used` with `tool: Skill` and an input_match regex.
- Needs Claude Code ≥2.1.269 and a plugin or skills-dir plugin.

The terminal `claude` on PATH here is 2.1.259 (npm global). The VS Code extension binary is 2.1.289, the same as the npm latest. Every eval run uses plan quota.
- Lisans: kod skill-creator: Anthropic (LICENSE.txt in the skill); CLI: Claude Code · ağırlık - · ticari: yes
- Apple Silicon: n/a
- Kurulum: 1. Run `claude update` (or `npm i -g @anthropic-ai/claude-code@latest`) so the terminal CLI matches 2.1.289.
2. Then `claude plugin eval medya@skills-dir --ablation none` while iterating, or ask Claude to 'evaluate my medya-kurgu skill with skill-creator'.
- Disk: ~0 MB · bakım: Plugin eval requires v2.1.269+ (docs, 2026-10-05).
- Ajan kullanımı: Write eval queries in Turkish phrasing like the user's real requests, and include no personal information.
- Güven: high · kaynaklar: https://code.claude.com/docs/en/plugin-evals, https://code.claude.com/docs/en/skills, https://registry.npmjs.org/@anthropic-ai/claude-code/latest

### Main local engine for motion graphics, explainers, product videos and montages of real footage
- **Seçim:** The installed HyperFrames 0.8.124 and its 21 user-level skills: hyperframes (router), general-video, music-to-video, hyperframes-keyframes, hyperframes-audio, media-use, motion-graphics, product-launch-video and others
- Alternatifler: Remotion (licence-conditional); raw ffmpeg filtergraphs for simple cuts.
- Neden: Licence and status: Apache-2.0 per package.json, so commercial use is fine. It is also listed in the official marketplace as hyperframes@claude-plugins-official.

Craft rules it already contains that the failed montage ignored (verified locally):
- music-to-video/SKILL.md makes analyze-beatgrid.py (librosa) the only beat analyzer. It states that bpm and beats are reliable only for genuinely rhythmic music.
- references/montage.md says calm tracks get `phrase_flow` pacing: Ken Burns or slow crossfades, never per-onset hard cuts.

Other useful pieces:
- hyperframes-keyframes covers punch-in/out, Ken Burns, whip and match handoffs.
- `check --snapshots`, `snapshot --zoom` and `timeline --json` give machine-checkable QA.
- `--quality draft` speeds up iteration.

media-use local engines:
- Kokoro-82M TTS: Apache-2.0, about 311 MB; Turkish text needs espeak-ng.
- whisper.cpp transcription: models from 75 MB to 3.1 GB.
- u2net_human_seg background removal: about 168 MB.
- The offline background-music fallback, MusicGen-small (about 300 MB plus torch), has non-commercial weights.
- The HeyGen, ElevenLabs and Lyria providers need keys or accounts.
- Lisans: kod Apache-2.0 · ağırlık Kokoro Apache-2.0; MusicGen CC-BY-NC-4.0 (NON-COMMERCIAL); Whisper MIT; u2net per upstream (not re-verified here) · ticari: conditional
- Apple Silicon: Headless Chrome rendering plus FFmpeg (VideoToolbox encoders available); the ML engines run on CPU
- Kurulum: Already installed in /Users/onurkaya/Projects/video (npm) with skills in ~/.claude/skills. Keep either this standalone copy or the marketplace plugin, not both. Run `hyperframes skills update` only deliberately.
- Disk: ~0 MB · bakım: 0.8.124, update-checked 2026-10-04
- Ajan kullanımı: Route new video requests through /hyperframes. For music-driven montages use /music-to-video and respect its `pacing` per frame.
- Güven: high · kaynaklar: /Users/onurkaya/.claude/skills/music-to-video/SKILL.md, /Users/onurkaya/.claude/skills/music-to-video/references/montage.md, /Users/onurkaya/.claude/skills/media-use/audio/references/requirements.md, /Users/onurkaya/Projects/video/node_modules/hyperframes/package.json

### Generative art, posters and stills, GIF stickers and design themes for personal and work assets
- **Seçim:** anthropics/skills (marketplace `anthropic-agent-skills`), used selectively: algorithmic-art, canvas-design, slack-gif-creator, theme-factory
- Alternatifler: HyperFrames motion-graphics for animated output.
- Neden: Vendor-official and Apache-2.0. Only docx, pdf, pptx and xlsx in that repo are source-available.
- algorithmic-art: p5.js with seeded randomness and a parameter-explorer HTML. It loads p5.js from a CDN, so vendor it locally to follow the no-remote-scripts rule.
- canvas-design: PNG/PDF posters with bundled canvas-fonts.
- slack-gif-creator: Pillow/imageio GIF builder with validators: 128×128 emoji or 480×480 message size, 10–30 fps, 48–128 colours.
- theme-factory: palette and font themes.
The example-skills plugin installs 12 skills, including duplicates of frontend-design and skill-creator, which you already have.
- Lisans: kod Apache-2.0 · ağırlık - · ticari: yes
- Apple Silicon: Pure Python and JS on CPU
- Kurulum: Either:
- `/plugin marketplace add anthropics/skills`, then `/plugin install example-skills@anthropic-agent-skills`; or
- copy only the 4 folders, each with its LICENSE.txt, into ~/.claude/skills (no duplicates, but no auto-update).
- Disk: ~20 MB · bakım: Repo active: about 180k stars; marketplace.json read 2026-10-05
- Ajan kullanımı: These trigger by description. GIF output must be checked by extracting frames, because Claude vision only sees the first frame of an animated GIF.
- Güven: medium · kaynaklar: https://github.com/anthropics/skills, https://raw.githubusercontent.com/anthropics/skills/main/.claude-plugin/marketplace.json, https://raw.githubusercontent.com/anthropics/skills/main/skills/slack-gif-creator/SKILL.md, https://raw.githubusercontent.com/anthropics/skills/main/skills/canvas-design/SKILL.md, https://raw.githubusercontent.com/anthropics/skills/main/skills/algorithmic-art/SKILL.md

### Remotion knowledge, only for work repos that already use Remotion
- **Seçim:** remotion-dev/skills, 12 skills: remotion-best-practices, -create, -markup, -studio, -render, -captions, -maps, -saas, -interactivity, -docs, -upgrade, -multimedia
- Alternatifler: HyperFrames plus /remotion-to-hyperframes
- Neden: These are official and maintained by Remotion. However, Remotion's own licence is free only for individuals, for-profit companies with up to 3 employees, non-profits, or evaluation; larger employers need a paid Company Licence. HyperFrames (Apache-2.0) covers the same niche locally and already ships remotion-to-hyperframes for ports.
- Lisans: kod Remotion License (source-available, free-tier conditions); the skills repo licence was not shown on its page · ağırlık - · ticari: conditional
- Apple Silicon: Node and Chrome rendering on arm64
- Kurulum: `DO_NOT_TRACK=1 npx skills add remotion-dev/skills -a claude-code` installs at project scope; add -g for ~/.claude/skills. The vercel-labs `skills` CLI (MIT) sends anonymous telemetry unless DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1 is set.
- Disk: ~5 MB · bakım: 
- Ajan kullanımı: /remotion-best-practices as the entry point
- Güven: medium · kaynaklar: https://www.remotion.dev/docs/ai/skills, https://github.com/remotion-dev/skills, https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md, https://github.com/vercel-labs/skills

### Browser screenshots and screen-recorded UI footage for work product demos
- **Seçim:** Playwright MCP, already enabled through playwright@claude-plugins-official. With --caps=devtools it gains browser_start_video and browser_stop_video, which record .webm with fps and cursor-animation options.
- Alternatifler: `hyperframes capture <url>` (website to editable composition) together with the product-launch-video skill; chrome-devtools-mcp is not needed for media.
- Neden: Apache-2.0; @playwright/mcp 0.0.83 is the npm latest on 2026-10-05. It runs locally and returns images inline for Claude to inspect. The plugin's .mcp.json runs an unpinned `npx @playwright/mcp@latest` (supply-chain drift) without the devtools capability, so video recording isn't available today.
- Lisans: kod Apache-2.0 · ağırlık - · ticari: yes
- Apple Silicon: Native Chromium arm64
- Kurulum: Only if recording is needed:
1. `claude mcp add --scope user pw-kayit -- npx -y @playwright/mcp@0.0.83 --caps=devtools --headless --isolated --viewport-size 1920x1080 --output-dir <workspace>/projeler/<proje>/kayit`
2. Disable the plugin copy in /plugin to avoid duplicate tools.
3. A browser downloads on first run (roughly 150–250 MB, estimate).
- Disk: ~250 MB · bakım: Microsoft, frequent releases
- Ajan kullanımı: Use mcp__...__browser_start_video and browser_stop_video, then ffmpeg to transcode the webm and trim it for HyperFrames.
- Güven: medium · kaynaklar: https://github.com/microsoft/playwright-mcp, https://raw.githubusercontent.com/microsoft/playwright-mcp/main/README.md, https://registry.npmjs.org/@playwright/mcp/latest, /Users/onurkaya/.claude/plugins/cache/claude-plugins-official/playwright/d182ca456ca0/.mcp.json

### 3D work: product renders, logo turntables, simple scenes
- **Seçim:** Blender 5.2.2 LTS driven headless from the CLI with bpy scripts; mcp-for-blender 2.1.3 optional for interactive look-development
- Alternatifler: Three.js inside HyperFrames (runtime adapter) for light 3D in motion graphics
- Neden: Blender is GPL; rendered outputs belong to the user. The deterministic agent path needs no MCP: `/Applications/Blender.app/Contents/MacOS/Blender -b scene.blend -P build.py -- --out ...` renders PNG, EXR or MP4.

mcp-for-blender:
- Renamed from blender-mcp; MIT; PyPI 2.1.3 released 2026-09-30.
- Adds get_scene_info, get_object_info, get_viewport_screenshot and execute_blender_code through an addon socket on localhost:9876, which lets the agent see the viewport.
- Sends a minimal anonymous usage record by default; DISABLE_TELEMETRY=true turns it off.
- execute_blender_code runs arbitrary Python, so save first.
- Its Hyper3D, Hunyuan3D, Tripo, Sketchfab and Poly Pizza features need keys or accounts; don't use them. Poly Haven assets are CC0.
- Lisans: kod Blender GPL; mcp-for-blender MIT · ağırlık - · ticari: yes
- Apple Silicon: Native arm64; Cycles and EEVEE on Metal; requires macOS 13+
- Kurulum: 1. Download the DMG from blender.org (330 MB). Installed size is about 1–1.5 GB (estimate), which is significant against about 19 GB free. The Homebrew cask route is blocked until the Xcode licence is accepted.
2. MCP: `claude mcp add --scope user -e DISABLE_TELEMETRY=true blender -- uvx mcp-for-blender==2.1.3`, then enable the addon inside Blender.
- Disk: ~1300 MB · bakım: Blender 5.2.2 LTS released 2026-09-15; mcp-for-blender releases weekly in Sept 2026
- Ajan kullanımı: Prefer CLI scripts for reproducible renders. Use the MCP viewport screenshot only for look-development loops.
- Güven: medium · kaynaklar: https://www.blender.org/download/, https://github.com/ahujasid/mcp-for-blender, https://pypi.org/pypi/mcp-for-blender/json, https://pypi.org/pypi/blender-mcp/json, https://github.com/ahujasid/blender-mcp

### 'Hearing' the music: a trustworthy beat and downbeat grid with a measurable confidence test. The failed montage used a home-made numpy tracker whose phase jumped between −390 and +300 ms.
- **Seçim:** beat_this 1.1.0 (CPJKU, ISMIR 2024) CLI in the workspace uv venv (Python 3.12.15), cross-checked against HyperFrames' analyze-beatgrid.py (librosa)
- Alternatifler: librosa only (via HyperFrames); madmom and allin1 (licence or weights caveats)
- Neden: A modern beat and downbeat tracker that doesn't need a DBN. Code is MIT, and per the README the checkpoints are MIT too: about 78 MB for the full model, about 8 MB for small. PyPI beat-this 1.1.0 (2026-04-14) requires torch>=2, torchaudio, einops, rotary-embedding-torch and soxr.

Running two independent trackers gives an agreement score (mir_eval F-measure within ±70 ms). That is the agent's measurable substitute for listening.

Do NOT pass --dbn: it requires madmom, whose pretrained models are CC BY-NC-SA.
- Lisans: kod MIT · ağırlık MIT per the README; confirm the checkpoint licence before commercial use · ticari: yes
- Apple Silicon: CPU is fast enough for whole songs; MPS isn't documented; `--gpu=-1` forces CPU
- Kurulum: `uv pip install beat-this` into /Users/onurkaya/Projects/video/.venv. torch adds roughly 300–800 MB (estimate); measure with `du -sh .venv` before and after.
- Disk: ~700 MB · bakım: 1.1.0 released 2026-04-14
- Ajan kullanımı: `beat_this song.wav -o song.beats` produces a TSV of beats and downbeats. Compare it with the beats_sec output from `python3 ~/.claude/skills/music-to-video/scripts/analyze-beatgrid.py song.wav -o audiomap.json`.
- Güven: medium · kaynaklar: https://github.com/CPJKU/beat_this, https://pypi.org/pypi/beat-this/json, /Users/onurkaya/.claude/projects/-Users-onurkaya-Projects-video/memory/geri-bildirim-ses-senkron.md

### 'Seeing' and measuring renders without a human. Claude cannot hear audio or watch video: Read shows still images only, and an animated GIF shows only its first frame.
- **Seçim:** Analysis filters in the local ffmpeg-static 6.0, plus Read on the generated images
- Alternatifler: `hyperframes check --snapshots` / `snapshot --describe false` for composition-level frames
- Neden: Filters verified present on 2026-10-05 in /Users/onurkaya/Projects/video/arac/ffmpeg: tile, drawtext, showspectrumpic, showwavespic, ebur128, astats, silencedetect, aphasemeter, scdet, blackdetect, freezedetect, blurdetect, signalstats, mpdecimate, cropdetect, idet, ssim, psnr, libvmaf, vmafmotion, siti, axcorrelate. rubberband is missing.

Vision limits that shape the image sizes:
- Opus 5.5 is in the high-resolution tier (models 4.7 and later): at most 2576 px on the long edge and 4,784 visual tokens, where one token is a 28×28 px patch.
- Once a request holds more than 20 images, each image must be at most 2000 px.
- Accuracy drops for images under 200 px.
- Claude Code re-encodes images still larger than 500 KB as lower-quality JPEG.
- Lisans: kod GPL build configured with --enable-nonfree (fine for local use; don't redistribute the binary) · ağırlık - · ticari: yes
- Apple Silicon: arm64 binary; h264 and hevc VideoToolbox encoders
- Kurulum: Already present. PySceneDetect 0.7.1, OpenCV and numpy are already in the workspace .venv.
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: See the techniques section: contact sheets, spectrograms, loudness, A/V offset, cut-to-beat checks and visual detectors.
- Güven: high · kaynaklar: /Users/onurkaya/Projects/video/arac/ffmpeg (ffmpeg -h filter=<name>), https://platform.claude.com/docs/en/build-with-claude/vision, https://code.claude.com/docs/en/tools-reference

### An OS-level backstop: protect originals in ~/Downloads, ~/Movies and ~/Pictures from `ffmpeg -y` or rm, and block traffic to cloud and telemetry hosts however a command is spelled
- **Seçim:** The Claude Code Bash sandbox (macOS Seatbelt, @anthropic-ai/sandbox-runtime)
- Alternatifler: chmod a-w on source copies (already a workspace rule), the hook, and deny rules
- Neden: Per the docs:
- Writes are limited to the working directory, temp and any allowWrite entries.
- Network goes through a local proxy that checks an allowlist, which starts empty.
- `allowUnsandboxedCommands:false` removes the dangerouslyDisableSandbox retry.
- On macOS, `network.allowLocalBinding:true` lets sandboxed commands use localhost servers.
- Hooks, MCP servers and Claude's own Read, Edit and WebFetch tools run outside the sandbox.
- `sandbox.filesystem.disabled:true` (v2.1.216+) keeps only the network layer.

Compatibility with HyperFrames' headless Chrome is untested.
- Lisans: kod Claude Code feature (sandbox-runtime is open source) · ağırlık - · ticari: yes
- Apple Silicon: Supported on macOS
- Kurulum: 1. Try it for one session first:
claude --settings '{"sandbox":{"enabled":true,"allowUnsandboxedCommands":false,"network":{"allowLocalBinding":true,"allowedDomains":["registry.npmjs.org","pypi.org","files.pythonhosted.org","github.com","*.githubusercontent.com","huggingface.co","*.huggingface.co","*.hf.co"]}}}'
2. Render a 5-second test.
3. If Chrome fails, add a narrow excludedCommands entry such as "hyperframes render *". Those commands then run unsandboxed.
- Disk: ~0 MB · bakım: 
- Ajan kullanımı: Transparent. When the sandbox blocks a host, Claude Code names it in the command result.
- Güven: low · kaynaklar: https://code.claude.com/docs/en/sandboxing, https://code.claude.com/docs/en/permissions

## Kaçınılacaklar

- **ComfyUI with Comfy-Org/comfy-mcp (official local MCP, about v0.10)** — Licensed AGPL-3.0-or-later or commercial. Comfy's own README says local diffusion isn't recommended under 32 GB of unified memory, and this Mac has 16 GB. Models are several GB each against about 19 GB free. Partner nodes and partner_generate spend Comfy credits and need an account.
- **ffmpeg MCP wrappers (e.g. misbahsy/video-audio-mcp, MIT, about 87 stars)** — Thin wrappers around the ffmpeg CLI that expose a subset of it (trim, concat, overlay and so on). Claude already writes full filtergraphs through Bash, so a wrapper adds tool-definition context, a supply-chain surface (Smithery install) and less expressive control.
- **DaVinci Resolve MCP (samuelgursky/davinci-resolve-mcp 4.8.27, MIT)** — Blackmagic restricts external scripting to the paid Resolve Studio; the free edition works only through an in-app Workspace ▸ Scripts bridge. The Resolve download requires a registration form, the install is several GB, and it needs PYTHON3HOME set via launchctl.
- **Figma MCP, canva, adobe-for-creativity, runway-api, cloudinary and superdesign plugins (all in the official marketplace)** — All require accounts or paid credits. Figma's Starter, View and Collab seats are limited to 6 MCP tool calls per month; a Dev or Full seat is needed. This violates the no-account, no-credit rule unless an employer seat already exists for work.
- **HyperFrames cloud, lambda, cloudrun, auth, publish, usage, feedback and events commands; `snapshot --describe` with Gemini; media-use's HeyGen, ElevenLabs and Lyria providers** — Each is paid or hosted, needs an account, or sends data off the machine. feedback posts to a public channel, usage reads your Claude Code or Codex login, and --describe uploads frames to Google.
- **MusicGen (media-use's offline background-music fallback, facebook/musicgen-small)** — Its weights are CC-BY-NC-4.0, so it can't be used for work or other commercial outputs. It also pulls in torch and transformers (about 1 GB or more).
- **madmom pretrained models, and `beat_this --dbn`** — madmom's models are CC BY-NC-SA (non-commercial), and --dbn depends on them.
- **Home-made numpy beat trackers** — Measured failure in this workspace: a 76 BPM grid whose phase moved between −390 and +300 ms per 10-second window on a soft acoustic song. HyperFrames' music-to-video forbids re-measuring beats with other tools and prescribes phrase pacing for calm music.
- **hyperframes@claude-plugins-official installed on top of the standalone ~/.claude/skills copy** — Both copies would load (/hyperframes:... plus the plain names), which splits triggering and doubles the context cost. Use one distribution.
- **Unvetted skills from community directories and MCP listings (skillsmp, claudeskills.info, vibeindex, mcp.film, lobehub, glama)** — These sites list skills without vetting them. A skill can run !`cmd` when invoked, pre-approve tools through allowed-tools, and register hooks that last the whole session; plugins run with your user privileges.
- **CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC as a 'telemetry off' switch** — It also disables auto-updates, feature-flag fetching (Remote Control and similar), plugin auto-update and claude.ai plugin and skill sync. Even a value of '0' turns it on. Use DISABLE_TELEMETRY and DISABLE_ERROR_REPORTING instead.
- **Relying on CLAUDE.md or auto-memory alone for hard rules** — The docs say these are context, not enforced configuration, so vendor skill text can override them. Use hooks, permission rules or the sandbox for anything that must hold.
- **Publishing personal footage through Artifact assets or any external 'describe' service** — That uploads it to claude.ai or a third party. Keep personal media local and share file paths instead.

## Teknikler

### Wire up enforcement and env at user scope
1. Edit ~/.claude/settings.json (strict JSON, reloaded live) and add the `env` block and the PreToolUse hook from picks 1 and 2.
2. Keep the existing model, effortLevel, modelSettings and enabledPlugins keys.
3. Optionally add "$schema": "https://json.schemastore.org/claude-code-settings.json" for editor validation.
4. Lists such as permissions.allow merge across scopes; for keys, the higher-precedence file wins.

**Doğrulama:** - /status lists 'User settings'.
- /hooks shows the Bash PreToolUse hook.
- A fresh `echo $HYPERFRAMES_NO_UPDATE_CHECK $DO_NOT_TRACK` prints `1 1`.
- Asking Claude to run `npx hyperframes usage --json` is blocked with the medya-koruma message.

### Harden medya-koruma.py: fail closed and catch wrappers
1. In main(), wrap everything in try/except. If anything fails and the raw stdin contains 'hyperframes', print the reason to stderr and exit 2.
2. For tokens sh, bash or zsh followed by -c or -lc, re-run the check on the next argument.
3. Treat argv[0]=='node' followed by a path ending in hyperframes/bin/hyperframes.mjs as a hyperframes invocation.
4. Add a last raw-text regex backstop over the whole command for `hyperframes[.mjs][@version] <cloud|lambda|cloudrun|auth|publish|usage|feedback|events>`.
5. Keep runtime well under the 10-second timeout, because timeouts are fail-open.

**Doğrulama:** - Pipe JSON stdin cases into python3 ~/.claude/hooks/medya-koruma.py: `sh -c "npx hyperframes cloud render"`, `bash -lc 'hyperframes publish'`, `node node_modules/hyperframes/bin/hyperframes.mjs usage`, and a malformed payload containing 'hyperframes'. All must exit 2 (today they exit 0).
- `hyperframes render p --output x.mp4` must still exit 0.

### Auto-load the workspace environment in every session
1. Add the project SessionStart hook to /Users/onurkaya/Projects/video/.claude/settings.json.
2. It runs .claude/hooks/ortam-yukle.sh, which uses the documented `export -p` before/after diff to append ortam.sh's exports to $CLAUDE_ENV_FILE.
3. Project hooks need workspace trust to be accepted.

**Doğrulama:** In a new session in the workspace, `which ffmpeg` resolves to .../arac/ffmpeg and `echo $UV_CACHE_DIR $HF_HOME` shows workspace paths, without sourcing anything by hand.

### Independent QA subagent with persistent memory
1. Create ~/.claude/agents/medya-qa.md with this frontmatter:
---
name: medya-qa
description: Independent measured QA for any rendered media; use proactively after every render or export and before claiming a video, animation or audio is finished
tools: Read, Bash, Glob, Grep
model: inherit
effort: high
memory: user
---
2. In the body, list the checks from the following techniques with their numeric thresholds and require a PASS/FAIL table with file paths.
3. Tell it to append recurring defects to its MEMORY.md (the first 200 lines or 25 KB are auto-loaded).

**Doğrulama:** - /agents lists medya-qa.
- On a known-bad render (inject a 120 ms audio delay and a 0.5 s black gap) it must FAIL with the measured values.
- ~/.claude/agent-memory/medya-qa/MEMORY.md appears.

### Contact sheets and transition filmstrips sized for Claude vision
1. Write filters to a file and pass them with -filter_script:v; drawtext escaping breaks on the command line, as the workspace CLAUDE.md already notes.
2. Sheet filter: fps=1/2,scale=240:-2,drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%{pts\:hms}':x=4:y=4:fontsize=14:fontcolor=white:box=1:boxcolor=black@0.6,tile=8x5:padding=4:margin=4. Output JPEG with -q:v 3.
3. Per cut at time T: select='between(t,T-0.5,T+0.5)',scale=320:-2,tile=6x5, which covers every frame of the transition.
4. Composition-level views: `hyperframes check --snapshots`, `hyperframes snapshot <proj> --at t1,t2 --describe false`, and `--zoom "#selector"` for 3× crops.
5. Check rotation with ffprobe side_data (displaymatrix) for phone clips.

**Doğrulama:** - ffprobe each sheet: width ≤2000 px, so it stays valid after more than 20 images in a conversation.
- Each tile is at least 200 px; file size under 500 KB, which avoids Claude Code's lossy re-encode.
- Then Read the sheet.

### Spectrogram and waveform pictures with beat and cut markers
1. Spectrogram: ffmpeg -nostdin -i a.wav -lavfi showspectrumpic=s=1800x400:legend=1:fscale=log:stop=8000 spec.png
2. Waveform: ffmpeg -nostdin -i a.wav -lavfi showwavespic=s=1800x160:split_channels=1 wave.png
3. Optionally plot the beats (beat_this) and cut times as vertical lines with matplotlib to get one alignment picture to Read.

**Doğrulama:** Use these only for orientation. Pass or fail must come from the numeric checks (loudness, A/V offset, cut-to-beat).

### Loudness and audio health numbers
1. Loudness: `ffmpeg -nostdin -i out.mp4 -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary` gives integrated LUFS, LRA and true peak.
2. `astats` gives peak, RMS and flat factor, which reveals clipping.
3. `silencedetect=n=-45dB:d=0.4` finds unintended gaps.
4. `aphasemeter` checks stereo phase.
5. Targets for music-only montages: −14 to −16 LUFS-I and true peak ≤ −1 dBTP. The workspace's betikler/ustala.sh targets −16 LUFS and −1.5 dBTP.

**Doğrulama:** Values fall inside the thresholds and are re-measured after mastering. Never describe audio by ear.

### A/V offset and drift check by cross-correlation
1. Decode the source music and the render's audio to mono 16 kHz f32 with ffmpeg.
2. In numpy or scipy, take 8-second windows with 50% hop and run FFT cross-correlation (scipy.signal.correlate with method='fft') on onset-strength envelopes, searching ±500 ms of lag.
3. Offset is the median lag; drift is the slope of a linear fit of lag against time.
4. Also check ffprobe stream start_time and duration for each stream.
5. PASS when |offset| ≤ 20 ms, end-to-end drift ≤ 1 frame (33 ms at 30 fps), and |audio_dur − video_dur| ≤ 1 frame.

**Doğrulama:** Self-test:
- A copy made with -af adelay=120:all=1 must report about +120 ms.
- A copy made with atempo=1.001 must report about 60 ms per minute of drift.
The earlier montage measured −3 ms, which shows the song itself hadn't slipped.

### Cut-to-beat alignment with a tracker-trust test
1. Cuts: take absStart from `npx hyperframes timeline --json`, or detect them on the render with PySceneDetect (already in .venv) or ffmpeg scdet.
2. Beats: run beat_this without --dbn, and HyperFrames analyze-beatgrid.py.
3. Trust test: mir_eval.beat.f_measure between the two trackers is at least 0.8 (±70 ms), and the per-10-second-window residual standard deviation is at most 40 ms.
4. If the test fails, mark the grid unreliable, switch to phrase_flow pacing (cuts on phrase, downbeat or energy changes, with Ken Burns or crossfades), and tell the user.
5. On beat_cut sections, report the median and 95th-percentile distance from each cut to the nearest beat. The target is a 95th percentile of at most 40 ms (about one frame).

**Doğrulama:** - Mix a synthetic 120 BPM click track under a song: the trackers must give F≈1.0 on the clicks and 0±10 ms residual.
- Shift one cut by 100 ms: the checker must flag it.

### Visual defect detectors
1. blackdetect=d=0.08:pix_th=0.10
2. freezedetect=n=-60dB:d=0.4
3. blurdetect (lavfi.blur metadata)
4. signalstats YAVG per frame: flag shot-to-shot jumps above about 25 (8-bit) as exposure mismatches.
5. mpdecimate unique-frame counts on slow-motion segments, to catch stutter after minterpolate.
6. cropdetect for unexpected black bars, and idet for interlacing.
7. Use ssim, psnr or libvmaf against a reference when a sequence is rebuilt.
8. Print metadata to a file and parse it with Python.

**Doğrulama:** Inject a 0.5 s black gap, a 1 s frozen segment and a duplicated-frame slow-motion clip into a test video; each detector must fire on the right timestamps.

### Long renders without timeouts
1. Start `hyperframes render ... --quality draft` with Bash run_in_background:true while iterating, and use --quality looks or delivery only after approval.
2. Follow progress with the Monitor tool. Watches end after 5 minutes by default and at most 30 minutes, so re-arm as needed.
3. Local interactive sessions have no background time limit.
4. Foreground commands move to the background automatically at their timeout (default 2 minutes, maximum 10 minutes unless BASH_MAX_TIMEOUT_MS is raised).

**Doğrulama:** `test -s out.mp4` passes, and the ffprobe duration equals the root data-duration.

### Turkish trigger phrases plus measured triggering
1. Keep each skill's description in English, third person, with the key use first.
2. Add `when_to_use:` with the Turkish phrases the user actually types, e.g. 'montaj yap, kurgu, sırala, geçiş, ağır çekim, yakınlaştır, vuruşa göre kes, animasyon, ürün tanıtım videosu, ses dengesi'.
3. Keep description plus when_to_use within 1,536 characters.

**Doğrulama:** Run skill-creator's description-optimization loop with 8–10 Turkish should-trigger queries and 8–10 near-miss negatives (no personal information), 3 runs each. Or, with CLI 2.1.269+, `claude plugin eval` with a `type: tool_used`, `tool: Skill` grader.

### Context hygiene for 21 user-level HyperFrames skills
1. Measure with /context.
2. Collapse rarely used skills, e.g. in ~/.claude/settings.json:
{"skillOverrides":{"pr-to-video":"name-only","slideshow":"name-only","remotion-to-hyperframes":"name-only","figma":"name-only","talking-head-recut":"name-only","embedded-captions":"name-only","faceless-explainer":"name-only"}}
Alternatively use the /skills menu: Space cycles the state and it writes to .claude/settings.local.json.
3. Keep the hyperframes router and the workflows you actually use set to 'on'.
4. skillOverrides doesn't affect plugin skills.

**Doğrulama:** /context shows fewer skill-listing tokens, and trigger evals for the kept skills are unchanged.

### Optional Stop-hook QA gate
Add a project Stop hook script:
1. If stop_hook_active is true, exit 0 (loop guard).
2. Otherwise find renders newer than their `<name>.qa.json` (written by medya-qa).
3. For each one, print {"decision":"block","reason":"QA eksik: <file>; medya-qa çalıştır"}.

**Doğrulama:** - A render without QA prevents the turn from ending once.
- With the QA json present, the turn stops normally.
- There is no infinite loop.

### Version the workspace configuration with git
1. Run `git init` in /Users/onurkaya/Projects/video.
2. Track CLAUDE.md, .claude/, ortam.sh, betikler/, sablonlar/ and the skill sources.
3. Ignore node_modules/, .venv/, .uv/, modeller/, renders and outputs, and *.mp4, *.mov, *.wav.
4. Commit after every skill, hook or settings change. The docs say forked-skill edits fall outside session checkpoints and should be reverted with git, and /rewind doesn't undo Bash side effects.

**Doğrulama:** `git status` is clean after setup, and a deliberately broken skill edit can be reverted with git.

### Vet third-party skills, plugins and MCP servers before installing
1. Read every file: SKILL.md, scripts, hooks/hooks.json, .mcp.json.
2. Flag:
- !`cmd` or ```! blocks, which execute on invocation before Claude sees the skill;
- allowed-tools grants;
- frontmatter hooks, which persist for the session;
- network or telemetry calls;
- unpinned `npx pkg@latest`.
3. Prefer vendor-official repos (anthropics, heygen-com, remotion-dev, microsoft) and pin a commit or version.
4. Run `claude plugin validate <dir>`.
5. Optionally set "disableSkillShellExecution": true. No installed HyperFrames skill uses ! injection, allowed-tools or hooks (verified).

**Doğrulama:** `grep -rnE '(^|[[:space:]])!`|^```!|allowed-tools|^hooks:' <dir>` returns only expected hits, and validation passes.


## Riskler

- The hook fails open. Exit codes other than 2, hook timeouts, and the current script's invalid-input path all let the command run. Its text matching can also be bypassed with sh -c, bash -lc, node .../bin/hyperframes.mjs or a script file (all verified by stdin tests). Make it fail closed, and consider the sandbox as an OS-level backstop.
- Version mismatch: the terminal `claude` (npm global) is 2.1.259, while the VS Code extension runs 2.1.289. `claude plugin eval` (2.1.269+), `--plugin-dir` plugin folders (2.1.265+) and `omitClaudeMd` (2.1.271+) are unavailable from the terminal until it is updated.
- Privacy: every image Claude reads (contact sheets of personal footage, for example) is sent to Anthropic as part of the conversation. Keep sheets small and only as many as needed, and check the claude.ai privacy and training settings.
- Vision limits: once a request holds more than 20 images, each must be at most 2000 px. Animated GIFs show only their first frame. Tiles under 200 px lose accuracy. Images over 2576 px on the long edge are downscaled, and images still over 500 KB are re-encoded lossily by Claude Code.
- Compaction: after auto-compaction only the first 5,000 tokens of each invoked skill are re-attached, within a 25,000-token shared budget filled newest first. HyperFrames sessions invoke many skills, so older ones can disappear. Keep hard rules in hooks and CLAUDE.md, and put critical skill rules at the top of SKILL.md.
- The superpowers plugin injects SessionStart context requiring skill use and brainstorming before any creative work, while /hyperframes calls itself the mandatory entry point. This can mean a double intake. Plugin skills can't be hidden with skillOverrides; they can only be managed or disabled via /plugin.
- The project CLAUDE.md (110 lines) still points to ilk-montaj/, renders/, deneme/, kaynak/, fonts/ and vendor/, but the workspace now has projeler/, sablonlar/, testler/, varliklar/ and modeller/. Stale or contradictory instructions reduce how reliably Claude follows them.
- Homebrew is effectively blocked because the Xcode licence hasn't been accepted (per the auto-memory note). Any brew-based install will fail until the user runs `sudo xcodebuild -license accept`. Prefer uv, npm or official binaries in arac/.
- Disk: about 19 GiB free. Blender takes about 1.3 GB installed, torch several hundred MB, Whisper models up to 3.1 GB, the HyperFrames frame cache about 0.9 GB (in /var/folders), and ComfyUI models many GB.
- Playwright plugin supply-chain drift: it runs `npx @playwright/mcp@latest` unpinned on every start.
- The sandbox may break headless-Chrome renders or the HyperFrames preview; this is untested and needs a 5-second test render first.
- Per-turn context cost: the 21 user-level HyperFrames skill descriptions total about 10.6K characters (about 2.6K tokens) and are listed on every turn in every project.
- Licensing traps: Remotion needs a Company Licence above 3 employees; MusicGen and madmom weights are non-commercial; the ffmpeg-static build uses --enable-nonfree, so the binary can't be redistributed (outputs are fine).
- The HyperFrames CLI can silently update itself in the background (minor and patch versions) until HYPERFRAMES_NO_UPDATE_CHECK=1 is set, so a render could change between runs.

## Açık sorular

- Should the 21 HyperFrames skills stay at user level, which is usable from any directory but costs about 2.6K tokens per turn everywhere? Or should rarely used ones be collapsed with skillOverrides, or moved to the project's .claude/skills?
- Should Claude Code's own telemetry and error reporting also be disabled (DISABLE_TELEMETRY / DISABLE_ERROR_REPORTING), or only third-party tool telemetry?
- Is the user willing to try the Bash sandbox, which is strong protection for originals and network but may need tuning for headless-Chrome renders?
- For work use: does the employer have more than 3 employees (Remotion licence), and does it provide a Figma Dev or Full seat (Figma MCP)?
- Does the user consent to frames from personal footage being sent to Anthropic for visual QA, and what are their claude.ai privacy and training settings?
- Will the user accept the Xcode licence (`sudo xcodebuild -license accept`) to unblock Homebrew, or should everything keep installing through uv, npm and official binaries?
- Should the custom media setup be packaged as a personal skills-dir plugin (medya@skills-dir), which enables `claude plugin eval` and bundles hooks and agents, or stay as loose ~/.claude files?
- Should the terminal CLI be updated now (2.1.259 to 2.1.289) so that `claude plugin eval` and the other newer features documented here work outside VS Code?

## Şüpheci doğrulama

The Claude Code documentation facts in this domain are accurate, but the description of this machine is out of date, so the plan needs corrections before anyone acts on it.

Accurate, checked against official docs: skill limits and compaction budgets, hook semantics, subagent memory, plugin eval version, skills-dir plugins, the skill-creator loop, vision limits, Monitor and background limits, and the sandbox basics. Licences and versions also check out:
- beat_this MIT (code and weights) and madmom CC BY-NC-SA;
- Blender 5.2.2 LTS;
- Playwright MCP 0.0.83;
- Remotion's 3-employee rule;
- anthropics/skills Apache-2.0;
- MusicGen CC-BY-NC;
- U-2-Net Apache-2.0.

Out of date for this machine as of 2026-10-05 00:45:
- The hook is already registered, from sistem/claude/hooks rather than ~/.claude/hooks.
- The telemetry and update env block is already set.
- The current hook already blocks sh -c, bash -lc and node .mjs.
- beat_this is already installed in ortamlar/ses and used in a three-tracker committee.
- The workspace already has a `medya` CLI (denetle, kontak, senkron, ustala, muzik) that implements most of the proposed QA techniques.

Factual errors:
- mcp-for-blender does not honour DO_NOT_TRACK.
- ComfyUI is GPL-3.0; the AGPL licence and the 32 GB advice both belong to comfy-mcp.
- Kokoro has no Turkish voice.
- HyperFrames auto-install never applies to this project-local install.
- The workspace-trust statement is too strong.
- The Figma call limits are imprecise.
- betikler/ustala.sh does not exist.
- git is blocked by the Xcode licence; it works with DEVELOPER_DIR pointed at Command Line Tools.

New risks found:
- Hook bypasses through timeout, nice, /usr/bin/env, xargs, variable indirection, quote-splitting and python subprocess.
- The hook passes `--describe 0` and `--describe no`, which the CLI does not treat as opt-out.
- The hook fails open on malformed input.
- The Monitor tool is probably not covered by a Bash-only matcher.
- The sandbox prompts for unknown hosts rather than blocking them unless strictAllowlist is set.
- uvx is not on PATH for MCP servers.
- torchaudio audio loading now requires TorchCodec.

Recommended direction: harden the hook and add deny rules, rather than registering the hook again. Build the QA subagent and new skills as thin wrappers over the existing `medya` CLI, and use dynamic workflows plus Apple-native Vision and SoundAnalysis for the user's goal of professional editing craft.

Confidence is high for the local and documentation checks, and medium for the Figma numbers. The best current alternatives for slow motion and real-footage editing remain unverified because the web-search budget was exhausted.

### Kontroller

- [refuted] ~/.claude/settings.json has no `hooks` key, so the medya-koruma hook is not connected, and the script lives at ~/.claude/hooks/medya-koruma.py. — Checked at 2026-10-05 00:45 local. ~/.claude/settings.json now registers hooks.PreToolUse with matcher "Bash". It points to /Users/onurkaya/Projects/video/sistem/claude/hooks/medya-koruma.py with a 10 s timeout. The directory ~/.claude/hooks does not exist. The state before the change is in ~/.claude/backups/settings.json.medya-oncesi-20261005, which has neither hooks nor env. The finding describes a state that no longer exists. (local read of ~/.claude/settings.json and the backup)
- [refuted] The hook lets `sh -c "npx hyperframes cloud render"`, `bash -lc 'hyperframes publish'` and `node node_modules/hyperframes/bin/hyperframes.mjs usage` through. — I piped stdin JSON into the current script (modified 00:44) on 2026-10-05. All three forms exit 2. These also exit 2: eval, $(…), `npm exec hyperframes -- usage`, `pnpm dlx`, env-prefixed `usage`, path-prefixed `feedback`, `npx --yes hyperframes@latest auth login`, `telemetry enable`, and snapshot without --describe. `render` and `snapshot --describe false` exit 0. (/Users/onurkaya/Projects/video/sistem/claude/hooks/medya-koruma.py + scratchpad hooktest.py)
- [confirmed] The hook can still be bypassed and fails open. — New bypasses found; each exits 0:
- `/usr/bin/env npx hyperframes usage`
- `timeout 60 npx hyperframes usage`
- `nice …` and `caffeinate -i …`
- `echo usage | xargs npx hyperframes`
- `H=hyperframes; npx $H usage`
- `npx hyper""frames usage`
- `python3 -c` with subprocess

Other gaps:
- The `events` and `upgrade` subcommands are not blocked.
- Malformed JSON and empty stdin exit 0.
- The hook accepts `--describe 0` and `--describe no`, but the CLI only opts out on the exact string "false" (snapshot-F5ZSC5FM.js:720). `0` or `no` would be sent to Gemini as a custom question if a key were set.
- python3 on a missing script exits 2, so a wrong hook path in settings would block every Bash call. (stdin tests 2026-10-05; node_modules/hyperframes/dist/snapshot-F5ZSC5FM.js)
- [confirmed] Exit 2 blocks the call before permission rules are evaluated. Other exit codes and timeouts are non-blocking. Settings hooks also fire inside subagents. — Permissions doc: "A hook that exits with code 2 stops the tool call before permission rules are evaluated". Hooks doc: a timed-out command hook "doesn't block the tool call", and any other exit code "doesn't block on its own". The default command-hook timeout is 600 s. Hooks from settings run inside subagents. (https://code.claude.com/docs/en/hooks ; https://code.claude.com/docs/en/permissions)
- [uncertain] A PreToolUse hook with matcher "Bash" gates every shell command the agent runs. — Not tested live, but the docs strongly suggest a gap:
- The Monitor tool runs shell commands: the sandbox applies to "Bash, PowerShell, and Monitor commands", and its input field is `command`.
- Hook matchers use tool names, and the docs say to match `Bash|PowerShell` because Bash alone is not enough.
- PreToolUse fires for every tool except EndConversation.

So Monitor-launched commands are likely invisible to a Bash-only matcher. Bash deny rules do apply to Monitor. (https://code.claude.com/docs/en/tools-reference ; https://code.claude.com/docs/en/sandboxing)
- [refuted] This session's Bash environment lacks HYPERFRAMES_NO_TELEMETRY and DO_NOT_TRACK. — The settings env block now sets HYPERFRAMES_NO_TELEMETRY, HYPERFRAMES_NO_UPDATE_CHECK, HYPERFRAMES_NO_AUTO_INSTALL, DO_NOT_TRACK and HF_HUB_DISABLE_TELEMETRY, all to 1. All five are present in this session's Bash.

Still not in the env block: HYPERFRAMES_SKIP_SKILLS, DISABLE_TELEMETRY, GRADIO_ANALYTICS_ENABLED and HOMEBREW_NO_ANALYTICS. The last two are only in ortam.sh. (env in this session; ~/.claude/settings.json)
- [confirmed] media-use's PostHog telemetry opts out only through environment variables and ignores telemetryEnabled:false. — optedOut() checks only:
- HYPERFRAMES_NO_TELEMETRY==="1"
- DO_NOT_TRACK==="1"
- CI
- NODE_ENV=development

~/.hyperframes/config.json is used only for the notice and identity. Events are posted to us.i.posthog.com/batch. (/Users/onurkaya/.claude/skills/media-use/scripts/lib/telemetry.mjs)
- [refuted] HyperFrames 0.8.124 silently background-installs newer minor or patch versions unless HYPERFRAMES_NO_UPDATE_CHECK=1, so a render could change between runs. — detectInstaller() returns an installer only for global npm (/lib/node_modules/hyperframes/), bun -g, pnpm -g and Homebrew installs. npx-ephemeral and every other layout get kind "skip".

This workspace's copy is project-local (node_modules) with no global install, so it is never auto-upgraded. Only the registry check runs, and it is now disabled. The npm latest is 0.8.125 (2026-10-04T21:08Z); 0.8.124 is installed. (node_modules/hyperframes/dist/chunk-HQWCFX5E.js, autoUpdate-LM6YIFM4.js; registry.npmjs.org/hyperframes)
- [confirmed] `snapshot --describe` runs Gemini vision by default whenever GEMINI_API_KEY is set. — `describe` defaults to "true". The key is read from GEMINI_API_KEY or GOOGLE_API_KEY. Only `--describe false` opts out. Neither key is set in this session. (node_modules/hyperframes/dist/snapshot-F5ZSC5FM.js:673-786)
- [confirmed] Vendor skills tell agents to run `npx hyperframes usage --json` at the start and `feedback` after renders. Feedback goes to a public channel, and `usage` reads the Claude Code login. — The instructions are in:
- hyperframes/SKILL.md:21
- general-video/SKILL.md:15
- hyperframes-cli/SKILL.md:137-143 and :185

usage-EC3KFUIJ.js reads the keychain item 'Claude Code-credentials' or ~/.claude/.credentials.json and calls api.anthropic.com/api/oauth/usage.

Nuance: the skill says to send feedback "unless telemetry is disabled". `feedback` itself prints "Telemetry is disabled. Feedback not sent." under the env opt-outs, and `events` also honours DO_NOT_TRACK. So the env block already blocks those two; `usage` is not gated. (~/.claude/skills/*/SKILL.md; dist/usage-EC3KFUIJ.js, feedback-BXKESP4T.js, events-IF4ANAI4.js)
- [confirmed] A SessionStart hook can persist PATH and cache variables through CLAUDE_ENV_FILE, using the documented `export -p` diff pattern. — The hooks doc shows the exact ENV_BEFORE/ENV_AFTER plus `comm -13` script. CLAUDE_ENV_FILE is available to SessionStart, Setup, CwdChanged and FileChanged hooks. (https://code.claude.com/docs/en/hooks)
- [refuted] Project hooks run only after the workspace-trust dialog is accepted. — The permissions doc table 'What runs before you trust a folder' shows hooks in settings files and the env block as 'Used' in two cases: when only a parent folder is trusted, and in `claude -p` or SDK runs.

Trust does gate:
- frontmatter hooks in project subagents
- project @skills-dir plugins
- permissions.allow rules (https://code.claude.com/docs/en/permissions)
- [confirmed] Subagent frontmatter: `memory: user` maps to ~/.claude/agent-memory/<name>/ and injects the first 200 lines or 25 KB of MEMORY.md. The fields effort, color, isolation and initialPrompt exist, and @agent-<name> invokes a subagent. — Confirmed in the sub-agents doc, with these additions:
- Memory automatically enables the Read, Write and Edit tools.
- Memory has no effect if auto memory is off.
- `omitClaudeMd` requires v2.1.271.
- `orange` is a valid colour. (https://code.claude.com/docs/en/sub-agents)
- [uncertain] medya-qa should have tools: Read, Bash, Glob, Grep. — tools-reference: on macOS, Claude Code leaves Glob and Grep out of the default tool set and restores them only through --tools or --allowedTools. The entries may not resolve. That is harmless but redundant, because Write and Edit come from `memory` anyway. (https://code.claude.com/docs/en/tools-reference)
- [confirmed] Skill limits:
- description plus when_to_use is truncated at 1,536 characters;
- after compaction, the first 5,000 tokens of each skill are kept, within a shared 25,000-token budget filled newest first;
- name: at most 64 characters, lowercase letters, digits and hyphens, without 'anthropic' or 'claude';
- description: at most 1,024 characters, third person;
- SKILL.md body under 500 lines;
- references one level deep. — Every figure matches the skills doc and the platform best-practices page. Both also confirm skillOverrides (on, name-only, user-invocable-only, off; not applied to plugin skills), disableSkillShellExecution, personal skills not loading in cloud or Cowork, the precedence enterprise > personal > project, and symlink support. (https://code.claude.com/docs/en/skills ; https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [confirmed] `claude plugin eval` needs v2.1.269 or later. The terminal CLI is 2.1.259 and the VS Code extension is 2.1.289, which equals the npm latest. — `claude --version` prints 2.1.259. The extension is anthropic.claude-code-2.1.289. `npm view` shows 2.1.289.

The evals doc confirms:
- v2.1.269+ is required;
- `name@skills-dir` targets work;
- `--ablation none` is supported;
- the `tool_used` grader takes `input_match`;
- runs count against plan usage. (local; https://code.claude.com/docs/en/plugin-evals)
- [confirmed] `claude plugin init <name> --with skills` scaffolds ~/.claude/skills/<name>/, which loads as <name>@skills-dir. Validation without a manifest needs v2.1.233. Personal-scope plugins have no trust restrictions. — Confirmed by the CLI reference and the loading reference, with one nuance: whether a skills-dir plugin is enabled follows the manifest's `defaultEnabled`, unless a settings file overrides it. (https://code.claude.com/docs/en/plugins/cli-reference ; https://code.claude.com/docs/en/plugins/loading)
- [confirmed] skill-creator's description optimization uses about 20 queries, a 60/40 train/test split, 3 runs per query and up to 5 iterations, and picks best_description by the held-out score. — run_loop.py defaults: --max-iterations 5, --runs-per-query 3, --holdout 0.4. SKILL.md says to create 20 eval queries. (~/.claude/skills/synced/.../skill-creator/scripts/run_loop.py)
- [confirmed] Vision limits:
- Claude 4.7+ models are high-resolution: at most 2576 px and 4,784 visual tokens, with 28×28 px patches;
- above 20 images, each image must be at most 2000 px;
- accuracy drops under 200 px;
- an animated GIF shows only its first frame;
- Claude Code re-encodes images over 500 KB as JPEG. — All confirmed. One nuance: the many-image rule says neither dimension may exceed 2000 px, so height counts as well as width. The 500 KB JPEG re-encode applies from Claude Code v2.1.196 and keeps the pixel dimensions. (https://platform.claude.com/docs/en/build-with-claude/vision ; https://code.claude.com/docs/en/tools-reference)
- [confirmed] Monitor watches last 5 minutes by default and at most 30 minutes. Local interactive sessions have no time limit for background commands. Foreground commands move to the background when they hit their timeout. — All three confirmed by the tools reference. (https://code.claude.com/docs/en/tools-reference)
- [confirmed] Sandbox:
- the network allowlist starts empty;
- allowUnsandboxedCommands:false removes the unsandboxed retry;
- filesystem.disabled requires v2.1.216+;
- hooks, MCP servers and file tools run outside the sandbox. — All four confirmed, with three corrections:
- A new host triggers an approval prompt, and in auto mode a classifier reviews the hosts each command names. Hosts are denied outright only with network.strictAllowlist:true.
- Passing allowUnsandboxedCommands:false through --settings makes the sandbox admin-required, so excludedCommands in repository settings are ignored.
- Monitor commands are sandboxed too. (https://code.claude.com/docs/en/sandboxing)
- [confirmed] Playwright MCP 0.0.83 (Apache-2.0): `--caps=devtools` adds browser_start_video and browser_stop_video with fps and cursor options. The plugin runs an unpinned @latest. — npm latest is 0.0.83, published 2026-09-28. The README describes devtools caps with the video tools (fps defaults to 25). The plugin's .mcp.json runs `npx @playwright/mcp@latest`. (registry.npmjs.org/@playwright/mcp; raw README; ~/.claude/plugins/cache/claude-plugins-official/playwright/*/.mcp.json)
- [confirmed] Blender 5.2.2 LTS (2026-09-15): 330 MB DMG, needs macOS 13+. The Homebrew route is blocked until the Xcode licence is accepted. — blender.org confirms the version, date, size and minimum macOS. `brew info --cask blender` fails with "You have not agreed to the Xcode license", and still fails with DEVELOPER_DIR set to Command Line Tools. /usr/bin/git exits 69 for the same reason. (https://www.blender.org/download/ ; local)
- [confirmed] mcp-for-blender 2.1.3 is MIT, released 2026-09-30, and renamed from blender-mcp. — PyPI: uploaded 2026-09-30, license MIT, requires Python 3.10+. blender-mcp 2.0.0 is now a stub that depends on mcp-for-blender. The README confirms port 9876 and that Poly Haven needs no key. (https://pypi.org/pypi/mcp-for-blender/json ; https://github.com/ahujasid/mcp-for-blender)
- [refuted] DO_NOT_TRACK (as well as DISABLE_TELEMETRY) is honoured by mcp-for-blender. — The telemetry module checks only DISABLE_TELEMETRY, BLENDER_MCP_DISABLE_TELEMETRY and MCP_DISABLE_TELEMETRY, with values true/1/yes/on. DO_NOT_TRACK is ignored, and events go to Supabase. The user's env block sets only DO_NOT_TRACK. The npx skills CLI does honour DO_NOT_TRACK. (https://raw.githubusercontent.com/ahujasid/mcp-for-blender/main/src/blender_mcp/telemetry.py)
- [confirmed] beat_this 1.1.0 (2026-04-14): code and weights are MIT; the full model is about 78 MB and the small one about 8 MB; --dbn needs madmom, whose models are CC BY-NC-SA. — PyPI 1.1.0 was uploaded 2026-04-14 with licence MIT. The README says "The code and the published model weights are released under the MIT license" and warns that some training data is copyrighted. It lists about 78 MB for final* and about 8.1 MB for small*. madmom's code is BSD; its models are CC BY-NC-SA 4.0. (https://pypi.org/pypi/beat-this/json ; https://github.com/CPJKU/beat_this ; https://github.com/CPJKU/madmom)
- [refuted] Install beat_this with `uv pip install beat-this` into the workspace .venv; torch adds roughly 300–800 MB. — This is already done, elsewhere. The isolated env /Users/onurkaya/Projects/video/ortamlar/ses (Python 3.12.15, 1.2 GB) contains beat-this 1.1.0, torch 2.14.1, torchaudio 2.11.0, librosa 1.0.0, mir_eval 0.8.2, essentia and demucs 4.1.0.

medya/isciler/muzik_isci.py already runs a three-tracker committee (Beat This final0-2, Essentia, librosa) and scores agreement with mir_eval F ±70 ms and information gain. Installing into .venv would contradict the pyproject design, which keeps heavy tools in isolated envs.

Runtime test: torchaudio.load raises "TorchCodec is required". beat_this then falls back to soundfile, which beat-this does not declare as a dependency; it works here only because librosa pulls it in. The torch cp312 arm64 wheel is a 127 MB download. (local inspection and offline test)
- [refuted] ComfyUI is 'AGPL-3.0-or-later or commercial', and Comfy's README says local diffusion isn't recommended under 32 GB. — Wrong attribution. ComfyUI itself is GPL-3.0, and its README says it can run big models on 4 GB VRAM plus 8 GB RAM. Both the AGPL-3.0-or-later OR Commercial licence and the advice "On Apple Silicon, under 32 GB unified memory… go partner/cloud" come from the Comfy-Org/comfy-mcp README. Avoiding ComfyUI is still justified by disk space (17 GiB free) and speed. (https://github.com/comfyanonymous/ComfyUI ; LICENSE; https://github.com/Comfy-Org/comfy-mcp)
- [confirmed] DaVinci Resolve MCP 4.8.27 (MIT): external scripting is Studio-only, the free edition works through a Workspace ▸ Scripts bridge, and PYTHON3HOME must be set with launchctl. — Confirmed, and the constraint is tighter than stated: the README says Resolve 21.1 moved Python scripting to Studio only, so the bridge works only on 21.0.x and earlier. The repo has 3.3k stars and was last pushed 2026-10-03. (https://github.com/samuelgursky/davinci-resolve-mcp)
- [uncertain] Figma's Starter, View and Collab seats are limited to 6 MCP tool calls per month. — Figma's developer rate-limits page (as summarized) lists:
- View/Collab seats: up to 6 per month on Professional, Organization and Enterprise, but up to 20 per month on Starter;
- Dev/Full seats: 200–600 per day.

An account is required either way, so the 'avoid' verdict stands. (https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/)
- [confirmed] Remotion is free only for individuals, for-profit companies with up to 3 employees, non-profits and evaluation. remotion-dev/skills has 12 skills. — The LICENSE.md wording matches. The 12 skill names match, the repo has no detected licence, about 4.8k stars, and was last pushed 2026-10-01. (https://raw.githubusercontent.com/remotion-dev/remotion/main/LICENSE.md ; GitHub API)
- [confirmed] anthropics/skills:
- the four example skills are Apache-2.0, and the repo has about 180k stars;
- example-skills contains 12 skills, including frontend-design and skill-creator;
- algorithmic-art loads p5.js from a CDN;
- the slack-gif-creator limits are as stated. — The repo has 179,646 stars and was last pushed 2026-10-03. Each of the four skills ships an Apache 2.0 LICENSE.txt. algorithmic-art loads cdnjs p5.js 1.7.0. slack-gif-creator: 128×128 or 480×480, 10–30 fps, 48–128 colours. (raw marketplace.json, SKILL.md and LICENSE.txt files; GitHub API)
- [confirmed] The vercel-labs skills CLI is MIT and honours DISABLE_TELEMETRY=1 or DO_NOT_TRACK=1. — The README states both opt-outs, the MIT licence, and that -g installs to ~/.claude/skills. (https://github.com/vercel-labs/skills)
- [refuted] Kokoro-82M is Apache-2.0 and about 311 MB; Turkish text only needs espeak-ng. — The Apache-2.0 licence is right, but VOICES.md lists nine languages: US English, UK English, Japanese, Mandarin, Spanish, French, Hindi, Italian and Brazilian Portuguese. There is no Turkish voice. espeak-ng only phonemizes the text, so Turkish output would be heavily accented. (https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- [confirmed] MusicGen-small weights are CC-BY-NC-4.0; u2net is 'per upstream, not re-verified'. — The MusicGen model card states CC-BY-NC 4.0, which rules out commercial use. The U-2-Net repo is Apache-2.0. (https://huggingface.co/facebook/musicgen-small ; GitHub API xuebinqin/U-2-Net)
- [confirmed] ffmpeg-static 6.0 has the listed analysis filters, lacks rubberband, and is built with --enable-nonfree. — The buildconf includes gpl, version3, nonfree, libvmaf, libx265, libsvtav1, libzimg and libvidstab. Every listed filter is present; rubberband is missing. (/Users/onurkaya/Projects/video/arac/ffmpeg -buildconf / -h filter=)
- [confirmed] There are 21 user-level HyperFrames skills, with about 10.6K characters of descriptions. — 21 SKILL.md files, totalling 10,619 characters of description plus when_to_use. (~/.claude/skills)
- [confirmed] The project CLAUDE.md (110 lines) points to directories that no longer exist. — It references ilk-montaj/, renders/, deneme/, kaynak/, fonts/ and vendor/; none of them exist. (/Users/onurkaya/Projects/video/CLAUDE.md)
- [refuted] The workspace's betikler/ustala.sh targets −16 LUFS and −1.5 dBTP. — There is no betikler/ directory. The equivalent is `medya ustala` (medya/komutlar/ustala.py, defaults --hedef -16 --tepe -1.5).

The workspace `medya` CLI already provides:
- `denetle`: technical checks, black, freeze, 1–2 frame flashes, LUFS, true peak, clicks, cut-to-beat, A/V and GPS, written to JSON plus a contact sheet; exit 0 means pass;
- `kontak`: contact sheets;
- `senkron`: cut-to-beat, p90 ≤40 ms and max ≤70 ms;
- `muzik`: music analysis. (/Users/onurkaya/Projects/video/medya/komutlar/*.py)
- [confirmed] CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC also disables auto-updates, feature flags and plugin sync. DISABLE_TELEMETRY turns on with any non-empty value, including 0. — The env-vars doc lists both as presence-only variables. The loading doc says synced plugins don't load when that variable is set. (https://code.claude.com/docs/en/env-vars ; https://code.claude.com/docs/en/plugins/loading)
- [refuted] About 19 GiB of disk is free. — `df -h /` shows 17 GiB available at check time. The ortamlar/ses env already uses 1.2 GB. (local df)
- [confirmed] misbahsy/video-audio-mcp is MIT with about 87 stars. — MIT, 87 stars, last pushed 2025-05-24. That is over 16 months without a push, which is a further reason to avoid it. (GitHub API)

### Düzeltmeler (seçimlerin önüne geçer)

- **Hard enforcement of the HyperFrames rules (pick 1)**: Do NOT add the suggested `python3 ~/.claude/hooks/medya-koruma.py` entry. That path does not exist, and python3 exits 2 on a missing script, which would block every Bash call. The hook is already registered with an absolute path into sistem/claude/hooks.

Harden it instead:
(a) Change the matcher to "Bash|Monitor".
(b) Strip these wrappers and their option arguments: timeout, nice, stdbuf, noglob, caffeinate. Match path-prefixed wrappers by basename, e.g. /usr/bin/env.
(c) Block xargs/hyperframes pipelines that have no explicit subcommand.
(d) Block `$VAR` command words when the raw text contains hyperframes.
(e) Add a raw-text regex backstop that runs after removing quotes, which catches hyper""frames.
(f) Add `events` and `upgrade` to the blocked subcommands.
(g) Exit 2 when stdin can't be parsed and contains 'hyperframes'.
(h) Accept only `--describe false` or `--describe=false`, not 0 or no.

Also add permissions.deny rules such as Bash(npx hyperframes usage*) and Bash(hyperframes usage*), and the same for cloud|lambda|cloudrun|auth|publish|feedback. — gerekçe: Measured stdin tests show these exact gaps.

The permissions doc says Claude Code strips timeout, time, nice, nohup, stdbuf, command, builtin, noglob, bare xargs and leading variable assignments before matching deny rules. Bash deny rules also apply to Monitor.

So the two layers cover each other's gaps: the hook catches sh -c and node .mjs; deny rules catch the wrapper forms.
- **Telemetry and update switches (pick 2)**: Mark this as already done; the env block exists and is live in Bash.

Optional additions:
- HYPERFRAMES_SKIP_SKILLS=1.
- BLENDER_MCP_DISABLE_TELEMETRY=1, which avoids switching off Claude Code's own telemetry. Alternatively pass -e DISABLE_TELEMETRY=true on the Blender MCP server only.
- DISABLE_TELEMETRY only if the user also wants Claude Code telemetry off. — gerekçe: mcp-for-blender ignores DO_NOT_TRACK; I verified this in its telemetry.py.
- **Risk of HyperFrames self-updating**: Reword the risk: the project-local node_modules copy is never auto-installed (detectInstaller → 'skip'); only a registry check ran, and it is now disabled. To make this deterministic, pin "hyperframes": "0.8.124" exactly in package.json and upgrade deliberately. 0.8.125 was published 2026-10-04. — gerekçe: Verified in dist/chunk-HQWCFX5E.js.
- **Measured QA subagent (pick 4)**: Make medya-qa a thin wrapper over the existing CLI:
- `medya denetle <video> [--plan] [--muzik] --hedef …`, whose exit code is PASS/FAIL and which writes JSON plus a contact sheet;
- `medya kontak`;
- `medya senkron`.

The agent then Reads the PNGs. Use tools: Read, Bash; on macOS, Glob and Grep are not default tools, and memory adds Write and Edit automatically. Replace the betikler/ustala.sh reference with `medya ustala`. — gerekçe: The checks, thresholds and contact-sheet generation already exist in the workspace's medya/komutlar/*.py. Re-implementing them duplicates code and risks thresholds that diverge.
- **Beat and downbeat grid ('hearing' the music)**: Replace 'uv pip install beat-this into .venv' with: use `medya muzik`, which runs muzik_isci.py in ortamlar/ses.

Keep soundfile in that env and always feed it WAV. Since torchaudio 2.9, loading needs TorchCodec, and beat_this silently depends on soundfile as its fallback.

Use tracker agreement only as a post-hoc QA signal, not inside music-to-video planning, because that skill forbids re-measuring beats with another tool. Flag that Essentia is AGPL-3.0: fine for local use, but not permissive. — gerekçe: beat_this is already installed and wired into a committee. A runtime test showed torchaudio.load failing with ImportError.
- **OS-level sandbox backstop**: Add "network": {"strictAllowlist": true, …}.

Put any excludedCommands in the same --settings JSON or in user settings. Passing allowUnsandboxedCommands:false through --settings makes the sandbox admin-required, and repository excludedCommands are then ignored.

Note that `cd … &&`, redirects and $(…) keep a command sandboxed even when it matches an excluded pattern. — gerekçe: Without strictAllowlist, unknown hosts are prompted (or classifier-reviewed in auto mode) rather than blocked. Per the sandboxing doc.
- **Blender MCP install command**: Use: `claude mcp add --scope user -e BLENDER_MCP_DISABLE_TELEMETRY=1 -e UV_CACHE_DIR=/Users/onurkaya/Projects/video/.uv/cache -e UV_PYTHON_INSTALL_DIR=/Users/onurkaya/Projects/video/.uv/python blender -- /Users/onurkaya/Projects/video/arac/uvx mcp-for-blender==2.1.3` — gerekçe: uv and uvx are not on the default PATH; they exist only in the workspace arac/. Without the workspace cache variables, uv would cache outside the workspace.
- **Statement about workspace trust in pick 3**: Correct it to: project settings hooks and the env block load in -p/SDK runs and when a parent folder is trusted; interactive sessions show the trust dialog first. — gerekçe: Per the permissions doc table 'What runs before you trust a folder'.
- **ComfyUI entry in the avoid list**: State the licences separately: ComfyUI is GPL-3.0; comfy-mcp is AGPL-3.0-or-later OR commercial. Attribute the under-32 GB advice to the comfy-mcp README. The reason to avoid is disk (17 GiB free) and speed, not impossibility. — gerekçe: Both READMEs and the LICENSE file were fetched 2026-10-05.
- **Figma entry in the avoid list**: Replace 'Starter/View/Collab = 6 per month' with: View/Collab seats get up to 6 calls per month on paid plans (Starter is listed differently); Dev/Full seats get 200–600 per day; an account is always required. — gerekçe: Per Figma's developer rate-limits page.
- **Turkish voice (media-use TTS)**: Do not present Kokoro as a Turkish option. For local Turkish TTS, evaluate:
- Chatterbox multilingual: MIT weights, Turkish supported, every output carries a Perth watermark; chatterbox-tts 0.1.7, 2026-03-26.
- Piper: piper-tts 1.8.0, 2026-09-04, GPL-3.0-or-later; check each Turkish voice's licence. — gerekçe: Kokoro's VOICES.md has no Turkish voice. The Chatterbox card and PyPI were checked.
- **Contact-sheet sizing for vision**: Check that both width and height are at most 2000 px, not only width. — gerekçe: The vision doc says 'neither dimension exceeds 2000 px' for requests with more than 20 images.
- **Versioning the workspace configuration with git**: /usr/bin/git currently exits 69 because the Xcode licence hasn't been accepted. Either use `DEVELOPER_DIR=/Library/Developer/CommandLineTools git …` (git 2.54.0 works that way), or have the user accept the licence. Homebrew stays blocked either way. — gerekçe: Tested locally.
- **DaVinci Resolve entry in the avoid list**: Add that Resolve 21.1 moved Python scripting to Studio only, so the free-edition bridge works only on 21.0.x and earlier. — gerekçe: Per the davinci-resolve-mcp README.

### Eksik bulunanlar

- The findings ignore the existing workspace system:
- the `medya` CLI: incele, kontak, sahneler, ses-turu, ustala, senkron, denetle, sdr, cfr, meta-temizle, muzik;
- the yetenekler.toml capability registry, designed so providers can be swapped;
- the isolated ortamlar/ses env.
New skills and agents should call `medya <command>` rather than raw tools.
- Hook coverage of the Monitor tool (matcher "Bash|Monitor"), and permissions.deny rules as a complementary layer that is aware of wrappers.
- Claude Code dynamic workflows (code.claude.com/docs/en/workflows) for repeatable pipelines: per-clip analysis in parallel, then planning, render, and cross-checked QA. The workspace already has empty .claude/workflows and sistem/claude/workflows directories.
- Apple-native analysis through a Swift CLI, with no downloads (the workspace already has the arac/medya-apple binary):
- Vision VNCalculateImageAestheticsScoresRequest (macOS 15+) to rank the best shots;
- VNGenerateAttentionBasedSaliencyImageRequest (macOS 10.15+) for punch-in and Ken Burns targets;
- SoundAnalysis SNClassifySoundRequest for laughter, speech and music moments;
- SpeechAnalyzer (macOS 26+) for on-device transcription.
Compiling needs swiftc via DEVELOPER_DIR=CLT or acceptance of the Xcode licence.
- A Turkish TTS option. Kokoro has none, and MusicGen is non-commercial. Candidates are Chatterbox multilingual (MIT, watermarked) and Piper (GPL-3.0, per-voice licences).
- Mods risk: an installed mod that handles tool.check can approve a call that a PreToolUse hook blocked, unless the hook is in managed settings. Avoid installing mods that auto-approve Bash.
- Since torchaudio 2.9, loading audio requires TorchCodec, which affects any torch audio tool. Keep soundfile installed, or install torchcodec plus FFmpeg libraries, and feed WAV.
- Essentia (in ortamlar/ses) is AGPL-3.0 and should be listed in yetenekler.toml with a 'conditional' licence note. Essentia's pretrained TF models are often CC BY-NC-SA; they are not used here.
- A slow-motion frame-interpolation tool (RIFE-class) and a real-footage editing engine beyond HyperFrames and ffmpeg (e.g., MLT/melt, OpenTimelineIO) were not covered. The web-search budget was exhausted, so I could not verify current options.
- Pinning the HyperFrames version in package.json, and pinning the Playwright MCP version (the plugin runs @latest).
- Updating the stale project CLAUDE.md (110 lines, six missing directories) so that it documents the medya CLI, ortamlar/ses and the sistem/claude sources.
