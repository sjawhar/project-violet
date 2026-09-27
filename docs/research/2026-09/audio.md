# Violet — AI-Assisted Audio Pipeline Research (Music, SFX, Voice)
Research date: 2026-09-26. Devbox: Pop!_OS 24.04, Ryzen AI 9 HX PRO 370, Radeon 890M iGPU (no CUDA), 89 GB RAM.

## 1. Ranked Recommendation

**Adopt a text/code-first, hybrid pipeline, not a single vendor.** Rank order:

1. **Engine-side adaptive audio: Godot 4.3+ native (`AudioStreamSynchronized` + `AudioStreamInteractive` + `AudioStreamPlaylist`)**, not FMOD/Wwise. `AudioStreamSynchronized` supports up to 32 simultaneously-triggered, independently-volumed loops — a direct match for "gain an instrument layer per unlocked color." `AudioStreamInteractive` gives beat/tempo-aligned clip transitions for per-color leitmotif switching. Both are scripted in GDScript/C# (plain text, jj-diffable) with zero license paperwork. FMOD/Wwise indie tiers are free at Violet's likely budget, but Wwise has **no native Linux authoring tool** (Windows VM/Wine bridge required) and both are GUI-authoring-centric — a poor fit for an agent swarm that wants to read/write plain text.
2. **Music content: hybrid symbolic + hosted-API.** Have agents author per-color motifs as **MIDI/ABC text** (fully diffable, versionable, free), render draft stems via **FluidSynth + soundfonts** or **Csound/SuperCollider NRT** (the latter doubles as literal frequency/drone synthesis — thematically apt for a "resonance" mechanic). Use **ElevenLabs Music API** (licensed-stems model, streaming, composition-plan control, commercial rights on all paid tiers) and/or **Google Lyria 3 (Vertex AI)** for finished/high-fidelity beds and transitions. Run **ACE-Step (MIT, local, free)** for cheap batch variation generation on CPU. A human composer pass is still recommended for the emotional/dynamic nuance 2026 benchmarks show LLM/diffusion music still lacks.
3. **SFX: layered — free procedural first, API for the rest.** sfxr/jsfxr-derived synthesis (MIT/Apache/CC0, code-controllable) for ability/UI sounds; **ElevenLabs Sound Effects API** ($0.12/min, commercial from $6/mo) for organic/complex one-offs; **Stable Audio Open** self-hosted (free under $1M revenue, clean CC0/CC-BY training provenance) for ambient textures.
4. **Mix/master: ffmpeg `loudnorm`** as the scriptable backbone (EBU R128, two-pass, zero license cost), **Reaper + ReaScript** for human-in-the-loop passes needing plugin chains (cheapest fully headless/CLI-capable DAW on Linux), **matchering** (Python, OSS) as an optional reference-matching pass.
5. **Voice: none by default.** Violet's tone (GRIS/Celeste/Journey-adjacent) supports a wordless or minimally-narrated design; skip synthetic VO to sidestep consent/disclosure complexity entirely. If narrative VO is later required, use **ElevenLabs Professional Voice Cloning** of a hired, consenting voice actor (not a stock "AI voice"), and file Steam's AI disclosure accordingly.

**Explicitly avoid as pipeline components:** Suno (no official public API as of Sept 2026; third-party wrappers violate ToS, and Suno suffered a 55M-user data breach disclosed July 2026); Udio (no general-developer API; post-UMG/Warner/Merlin/NMPA settlements are moving it to a **"walled garden"** that restricts exporting audio out of the platform — disqualifying for a shippable game asset pipeline); Meta MusicGen/AudioCraft (code is MIT, but **model weights are CC-BY-NC-4.0** — commercial use of generated output is not permitted).

## 2. Comparison Table

| Tool | Type | API/CLI | Commercial license | Local/AMD-viable | Cost | Verdict |
|---|---|---|---|---|---|---|
| Suno | Hosted music gen | No official API (3rd-party wrappers only) | Paid-plan only, rights attach on download (Sep 2026 ToS) | N/A | $8–30/mo web only | Avoid (no API, ToS/breach risk) |
| Udio | Hosted music gen | Enterprise API only (Pro/Ent. tiers) | "Walled garden" 2026 — limited export | N/A | Custom | Avoid (export-restricted) |
| ElevenLabs Music | Hosted music gen | Full REST API, streaming | Yes, all paid tiers (Enterprise for AAA/film) | N/A (cloud) | $0.15/min PAYG; $6–990/mo tiers | **Recommended** |
| Google Lyria 2/3 | Hosted music gen | Vertex AI / Gemini API | Yes + indemnification, SynthID watermark | N/A (cloud) | $0.04–0.08/song, $0.06/30s | **Recommended** (alt/backup) |
| Stable Audio 2.5 | Hosted music+SFX gen | REST API | Yes, paid tiers; licensed AudioSparx data | N/A (cloud) | $0.20/gen; $12/mo Pro | Recommended for game-audio prototyping |
| Stable Audio Open | Self-hosted weights | Python/HF | Free <$1M revenue (register); CC0/CC-BY data | Runs on CPU; ROCm preview on iGPU | Free | **Recommended** (offline SFX/ambient) |
| ACE-Step | Self-hosted weights | Python/CLI/Gradio | MIT (fully free, no cap) | CPU ~150s/song; ROCm preview | Free | **Recommended** (batch/offline) |
| YuE | Self-hosted weights | Python/CLI | Apache 2.0 code, CC-BY weights | CPU-capable, ROCm preview | Free | Viable alternative to ACE-Step |
| MusicGen/AudioCraft | Self-hosted weights | Python/CLI | Weights CC-BY-NC-4.0 (**no commercial output**) | CPU/GPU | Free | **Avoid** for shipped audio |
| ElevenLabs SFX | Hosted SFX gen | REST API | Yes, paid tiers | N/A (cloud) | $0.12/min PAYG | Recommended for organic SFX |
| sfxr/jsfxr/ChipTone | Procedural SFX | Ports have CLI/lib; ChipTone GUI-only | MIT / Apache-2.0 / CC0 | Runs anywhere, no ML | Free | **Recommended** (retro/UI SFX) |
| MIDI/ABC + LLM + FluidSynth | Symbolic composition | Fully text/CLI (`fluidsynth -ni`) | Free, no IP concerns (original notes) | Trivial CPU | Free | **Recommended core** |
| SuperCollider (NRT) / Csound | Code synthesis | `sclang`/`csound` headless, text scores | Free, GPL/LGPL | Trivial CPU | Free | **Recommended** for frequency/drone layers |
| Godot AudioStream* (4.3+) | Adaptive-audio engine | GDScript/C#, in-engine | Free, MIT engine | N/A | Free | **Recommended** over middleware |
| FMOD | Middleware | C/C++/Studio GUI | Free indie (<$600k budget & <$200k rev) else $2k+/title | Native Linux runtime+authoring | Free–$18k/title | Not needed (Godot covers use case) |
| Wwise | Middleware | WAAPI, Studio GUI | Free indie (<$250k budget) else $7k+/title | Linux runtime yes; **authoring no** (Wine/VM only) | Free–$50k/title | Not needed; Linux authoring gap |
| Reaper + ReaScript | DAW | True CLI/headless (`-renderproject`, custom `libSwell` build) | Proprietary, cheap indie license | Native Linux | $60 (indie)/$225 | **Recommended** DAW |
| Ardour + Lua | DAW | `luasession`/`ardourN-lua` CLI, headless build | GPL/OSS | Native Linux | Free/PWYW | Good OSS fallback |
| Bitwig | DAW | Controller API (JS/Java) + undocumented `--headless` flag | Proprietary | Native Linux | $99–399 | Weaker CLI story; skip |
| ffmpeg loudnorm | Mastering | Full CLI | Free | Native | Free | **Recommended core** |
| matchering | Mastering | Python/CLI (`matchering-cli`) | Free (GPL) | Native | Free | Optional reference pass |
| ElevenLabs TTS/Voice Clone | Voice | REST API | Yes, paid tiers; consent required for others' voices | N/A (cloud) | Shared credit pool from $6/mo | Only if VO is added later |

## 3. Evidence List

- Suno commercial license, ToS, stems: suno.com/l/stem-player; suno.com/blog/suno-updates-tos (Aug 2026); help.suno.com/en/articles/9601985 — **current**.
- Suno data breach: cybernews.com/security/data-breach-at-suno-affects-over-55-million-users (Jul 2026 disclosure) — **current**.
- Udio–UMG settlement: universalmusic.com/universal-music-group-and-udio-announce-udios-first-strategic-agreements... (Oct 29, 2025) — **current**; Sony litigation ongoing per tntmagazine.com (2026).
- ElevenLabs Music API pricing/rights: elevenlabs.io/eleven-music-api; elevenlabs.io/pricing/api — **current**.
- Google Lyria pricing/terms: docs.cloud.google.com/gemini-enterprise-agent-platform/models/lyria/lyria-3; mlq.ai (Lyria 3.5 release) — **current**.
- Stable Audio 2.5: stability.ai/news-updates/stability-ai-introduces-stable-audio-25... (Sept 2025) — **12 mo, borderline; verify pricing before commit**.
- Stable Audio Open license: huggingface.co/stabilityai/stable-audio-open-1.0/blob/main/LICENSE.md — dated but license text is authoritative/unchanged-style — **flag as check-before-use**.
- ACE-Step: github.com/ace-step/ACE-Step-1.5 (MIT); github.com/ace-step/ACE-Step/discussions/404 (CPU/ROCm benchmark) — **current**.
- YuE license: github.com/multimodal-art-projection/YuE (Apache-2.0 code / CC-BY weights) — dated Jan 2025 transition, **>12 mo, re-verify**.
- MusicGen/AudioCraft license: facebookresearch.github.io/audiocraft (CC-BY-NC-4.0 weights) — **>12 mo (2023 origin), license clause is static/authoritative**.
- ElevenLabs Sound Effects pricing: elevenlabs.io/pricing/api — **current**.
- sfxr/jsfxr/ChipTone licenses: drpetter.se/project_sfxr.html (MIT); github.com/mneubrand/jsfxr (Apache-2.0); itch.io/t/1138063 (ChipTone CC0 output) — **stable, low staleness risk**.
- ROCm/AMD 890M status: community.frame.work/t/amd-rocm-does-not-support-the-amd-ryzen-ai-300-series-gpus (ongoing thread through 2026); reddit.com/r/ROCm/.../tried_rocm_71_vs_vulkanradv (May 2026); amd.com/en/products/software/rocm/whats-new.html — **current, but note active flux — re-check before large local-inference investment**.
- LLM/ABC/MIDI composition quality: aclanthology.org/2026.acl-long.493.pdf (MSU-Bench, Jul 2026); emergentmind.com/topics/midi-llm — **current**.
- FluidSynth CLI: fluidsynth.org/wiki/UserManual — **stable reference, low staleness**.
- SuperCollider NRT/headless: doc.sccode.org/Guides/Non-Realtime-Synthesis.html — **stable reference**.
- Csound CLI: csound.com/docs/manual/CommandFlags.html — **stable reference**.
- Godot AudioStream* classes: docs.godotengine.org/en/4.4/classes/class_audiostreamsynchronized.html; blog.blips.fm/articles/the-new-music-features-in-godot-43-explained — **current, Godot 4.3+**.
- FMOD Linux/licensing: fmod.com/licensing; fmod.com/docs/2.03/api/platforms-linux.html — **current**.
- Wwise Linux/licensing: audiokinetic.com/qa/2696/linux-wwise-sdk (no native authoring on Linux); audiokinetic.com/en/wwise/overview — **current**.
- Reaper headless/CLI: github.com/ReaTeam/Doc/blob/master/REAPER-CLI.md; forum.cockos.com/showthread.php?t=263372 (libSwell NOGDK build) — **stable reference**.
- Ardour Lua: manual.ardour.org/lua-scripting — **stable reference**.
- Bitwig headless flag: bitwish.top/t/command-line-support/6813 (Feb 2025 community report, unofficial) — **>12 mo and unofficial, treat as unverified**.
- matchering/ffmpeg loudnorm: github.com/sergree/matchering; ffmpeg-micro.com/blog/ffmpeg-loudnorm-filter-ebu-r128 — **stable reference**.
- ElevenLabs voice cloning terms: elevenlabs.io/use-policy; elevenlabs.io/docs/eleven-creative/voices/voice-cloning/professional-voice-cloning — **current**.
- Steam AI disclosure policy rewrite: gamedeveloper.com/business/valve-tweaks-and-clarifies-ai-disclosure-rules-for-steam (Jan 17, 2026); pcgamer.com (same); Steam Music separate policy: steam-music.com/sync-agency/ai-policy-statement — **current**.

## 4. Linux + AMD-iGPU Compatibility

- **ROCm on Radeon 890M (gfx1150, Ryzen AI 300 series)** is in an active, unsettled state as of Sept 2026: "preview" PyTorch support began ROCm 6.4.4 (Oct 2025); ROCm 7.2 (announced CES Jan 2026) extended Ryzen AI 300/Max coverage; a May 2026 Reddit report still found ROCm 7.1 lacking "first-class kernel support" for gfx1150, sometimes losing to the Vulkan backend and needing `HSA_OVERRIDE_GFX_VERSION` workarounds with occasional GPU resets. **Practical guidance: don't build the pipeline's critical path on iGPU-accelerated local inference.** Treat any ROCm win as a bonus speed-up, not a dependency.
- **CPU inference is the reliable local fallback.** ACE-Step 1.5 generates a full song in ~150 s on CPU (vs. <60 s on a discrete 7900 XT via ROCm) — fine for overnight/batch agent runs, not for real-time iteration.
- **All hosted APIs (ElevenLabs, Lyria/Vertex AI, Stable Audio 2.5) are platform-agnostic** — no GPU needed locally at all; this is the path of least resistance for anything time-sensitive.
- **Native Linux tooling** exists for essentially everything else in the stack: FluidSynth, SuperCollider, Csound, ffmpeg, matchering, Reaper, Ardour, Bitwig, and Godot itself all run natively on Pop!_OS. **Wwise is the one notable gap** — its authoring GUI has no native Linux build (Windows VM/Wine bridge required), reinforcing the recommendation to skip it.

## 5. Agent-Operability (CLI/API/MCP/Text/Headless)

| Component | Headless/CLI | Text format | Notes |
|---|---|---|---|
| ElevenLabs Music/SFX/Voice | REST API (curl-friendly) | JSON in/audio out | Best-in-class for agent scripting; streaming supported |
| Google Lyria | Vertex AI/Gemini REST API | JSON | Same tier of operability |
| Stable Audio 2.5 / Open | REST API or local Python | JSON / Python | Open weights also scriptable offline |
| ACE-Step / YuE | Python CLI, Gradio (optional) | Python args | Fully scriptable without any GUI |
| FluidSynth | `fluidsynth -ni -F out.wav sf2 in.mid` | MIDI (binary but tiny, diffable-ish) | Ideal for agent-authored music: LLM writes MIDI/ABC text, one command renders |
| SuperCollider | `sclang script.scd` (NRT via OSC score) | SuperCollider code (text) | Literal frequency synthesis — fits "resonance" theme |
| Csound | `csound flags orc sco` or `.csd` | Plain text orchestra/score | Extremely agent-friendly, decades-stable CLI |
| Godot AudioStream* | In-engine GDScript/C# | Text (.gd/.cs, .tscn) | No external tool needed; diffable in jj |
| Reaper | `reaper -renderproject x.rpp`; ReaScript (Lua/Python/EEL) passed as CLI arg | Lua/Python scripts, .rpp (text-ish) | True headless build possible on Linux only |
| Ardour | `luasession`, `ardourN-lua` | Lua | Less mature headless docs than Reaper |
| Bitwig | Controller API (JS/Java), reported `--headless` flag | JavaScript | Least-verified CLI story of the three DAWs |
| ffmpeg / matchering | Full CLI | N/A | Trivially scriptable, no MCP needed |
| Suno / Udio | **None official** | N/A | Disqualifying for an agent-first pipeline |

MCP: no first-party MCP servers exist yet for these audio tools (Sept 2026); all integration is via their REST APIs or CLIs, which is sufficient for agent orchestration without extra tooling.

## 6. Licensing, Commercial Rights & Steam AI-Disclosure

- **Steam policy (rewritten Jan 17, 2026):** any AI-generated content shipped with the game (music, SFX, voice) must be disclosed via the Steamworks Content Survey as **"Pre-Generated AI Content"**, describing what was generated and confirming no copyright infringement; this appears publicly under "About This Game." **Runtime-generated audio would additionally require "Live-Generated AI Content"** disclosure with stated guardrails — not applicable if Violet's audio is baked at build time (recommended). Dev-tool use (e.g., agents writing engine code) is explicitly exempt.
- **Steam Music** (a separate sync-licensing marketplace, not the store policy) states it will not represent fully AI-generated tracks without human involvement — irrelevant unless pursuing separate music-sync placements, but a reminder that a **human-in-the-loop mixing/composition pass is good practice regardless of engine policy.**
- **Recordkeeping:** every vendor (Suno, Stability, ElevenLabs) independently recommends keeping prompts/generation dates/model versions for legal defensibility — this doubles as the Steam disclosure paperwork; maintain one manifest file per generated asset.
- **Voice cloning consent:** cloning your own voice is unrestricted; cloning anyone else's requires explicit consent (ElevenLabs enforces this contractually); the EU AI Act (effective Aug 2, 2026) adds labeling requirements for synthetic voice content in some contexts.

## 7. Costs (indicative, monthly unless noted)

| Item | Cost |
|---|---|
| ElevenLabs Starter (commercial-capable) | $6/mo, credits shared across Music/SFX/Voice |
| ElevenLabs Music API PAYG | $0.15/min |
| ElevenLabs SFX API PAYG | $0.12/min |
| Google Lyria (Vertex AI) | $0.04–0.08/song, $0.06/30 s, no subscription |
| Stable Audio 2.5 Pro | $12/mo (500 gens) or $0.20/API generation |
| Stable Audio Open, ACE-Step, YuE (self-hosted) | $0 (compute only) |
| Reaper indie license | $60 one-time (<$20k annual rev) |
| Ardour | Free / pay-what-you-want |
| FMOD/Wwise (not adopted) | $0 at indie thresholds, else $2k–$50k/title |
| ffmpeg, matchering, FluidSynth, Csound, SuperCollider, Godot | $0 |

Realistic monthly spend for the research/prototype phase: **under $50/month** using free tiers + pay-as-you-go credits, scaling with production volume.

## 8. Risks / Unknowns

- **ROCm on the 890M is a moving target** — behavior observed in threads spans "unsupported" to "preview" across 2025–2026; re-verify before any local-GPU-dependent commitment.
- **Music-industry licensing landscape is still settling** — Udio's "walled garden" terms and Sony's ongoing litigation could still change API availability/export rights before Violet ships; Suno's Sept 2026 ToS rewrite ("rights attach on download") shows terms are actively in flux.
- **Third-party Suno/Udio API aggregators (kie.ai, Sonauto/Treblo, etc.)** are unofficial, carry ToS risk, and have inconsistent reliability (2.5★ support reports for kie.ai) — usable for disposable prototyping only, never for shipped assets.
- **LLM/diffusion symbolic composition quality**: 2026 benchmarks (MSU-Bench, MusICA-MetaBench) show strong technical/structural competence but a persistent gap in emotional phrasing and long-form development — budget for human composer review, especially given the mindfulness/oneness themes that hinge on emotional nuance.
- **Stable Audio Open's free-tier revenue cap ($1M/yr)** requires registration and reassessment if the studio scales — track this as a compliance item, not a one-time check.
- [INFERENCE] ROCm 10.0.0 "stable Aug 27 2026" claim comes from a single secondary source (rocm-handbook.amd.com) not cross-verified against AMD's own release notes; treat as unconfirmed until checked against amd.com/en/products/software/rocm/whats-new.html directly.
