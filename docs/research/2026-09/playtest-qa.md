# AI-Agent Automated Playtesting & QA — Research Report
Research phase for Project Violet. Current as of 2026-09-26.

## 1. Ranked Recommendation

**Recommendation: Godot 4 (4.7.x) as the QA-tooling substrate, with a seven-layer pipeline: gdUnit4/GUT unit tests → gdUnit4 `SceneRunner` scripted-input integration tests → a custom BFS/A\* ability-gated reachability solver → VLM visual review over Xvfb/software-rendered screenshots → an MCP runtime bridge (Godot Runtime Bridge, "GRB") for exploratory agent playtesting and RL-agent exploration (godot-rl-agents) → GameAnalytics/telemetry heatmaps → human playtests.**

Godot 4 wins for this project not because its AI-QA tooling is the most mature of the four candidates surveyed — it isn't; Bevy's `bevy_brp_mcp`/BRP combo and the web stack's Playwright are both architecturally cleaner for headless-agent control — but because Godot is the only one of the four that simultaneously (a) has a first-party, battle-tested 2D toolchain suitable for shipping a multi-year narrative platformer, (b) has *two* mature, actively-maintained unit/integration test frameworks (GUT 2,738★, gdUnit4 1,242★, both MIT, both tracking Godot 4.7.x) with real scripted-input scene runners, (c) has a maintained RL-playtesting toolkit whose own stated goal is "automated gameplay testing" (godot-rl-agents, 1,589★, MIT, commits through mid-2026), and (d) is free/open-source with zero licensing exposure, unlike Unity's per-seat Pro pricing. Bevy's superior AI-tooling primitive is undercut by pre-1.0 API churn and a thin 2D ecosystem that would slow the actual game; the web stack's superior QA tooling is undercut by a genuinely weak, community-patched path to a native Steam release (Electron + unmaintained `steamworks.js`-class bridges). Godot is the pragmatic center of the trade-off triangle.

## 2. Comparison Table

| Dimension | **Godot 4** | Unity 6/7 | Bevy 0.16+ | Web (Phaser+Playwright) |
|---|---|---|---|---|
| Headless test execution | `--headless` CLI, GUT/gdUnit4 native runners | `-batchmode -nographics` + official Test Framework, GameCI Action (266★) | `MinimalPlugins`+`app.update()` loop — cleanest of all four | Playwright headless Chromium — turnkey, zero engine plumbing |
| Determinism for replay | Stock physics **not** cross-platform deterministic (float ops); fixed-point add-ons (SG Physics 2D) exist but unmaintained-looking | Same caveat, explicitly documented by Unity devs | `FixedUpdate` schedule native; ECS state easy to snapshot | Single-threaded JS + fixed-step Arcade Physics — structurally easiest |
| Screenshot/visual QA | `--headless` **cannot** render; needs Xvfb+Mesa llvmpipe/lavapipe software rendering or real GPU; built-in Movie Maker (`--write-movie`) works only with real rendering | Needs "Linux Headless Simulation" build target or Xvfb+RenderTexture readback | Built-in screenshot module unreliable headless; use `bevy_capture` crate | `page.screenshot()`/`toHaveScreenshot()` — official, first-class |
| Agent/MCP runtime bridge | Godot Runtime Bridge (GRB, MIT, 11★, Godot 4.5+) — screenshot+input+state, purpose-built for AI agents | None found specific to runtime QA (mcp-unity/CoplayDev unity-mcp are editor-focused, though mcp-unity exposes `run_tests`+play-mode control) | `bevy_brp_mcp`+`bevy_brp_extras` (~70★) — architecturally the cleanest of all four | Generic Playwright-MCP (accessibility-tree based); canvas games need custom instrumentation |
| RL playtest agent | **godot-rl-agents** (1,589★, MIT, SB3/RLlib/CleanRL, ONNX export) | Unity ML-Agents (still shipping, v4.0.x, but Unity governance/ToS shifting) | None found | None found |
| Licensing/cost | Free, MIT | Personal free to $200k rev; Pro $2,200/seat/yr, +5% Jan 2026 | Free (MIT/Apache-2.0) | Free engine; Electron/steamworks.js overhead for Steam |
| Steam-shipping risk | Low (GodotSteam, mature) | Low | Low | **High** — Electron bundling + historically flaky Overlay via community bridge |
| Overall fit for a multi-year narrative 2D platformer | **High** | High | Medium-low (pre-1.0 churn) | Medium (weak native-shipping story) |

## 3. Evidence List (primary sources, dated; 🕒 = possibly stale, pre-Sept-2025 or undated)

- Godot `--headless`, `DisplayServer` dummy-values behavior — docs.godotengine.org/en/stable/classes/class_displayserver.html (fetched 2026-09-26, 4.7 docs)
- Godot Movie Maker mode, `--write-movie`, `--fixed-fps` — docs.godotengine.org/en/stable/tutorials/animation/creating_movies.html (4.7 docs, current)
- Godot physics determinism caveat — github.com/godotengine/godot-proposals/discussions/14936 (open discussion, undated 🕒 but content current)
- GUT (bitwes/Gut) — github.com/bitwes/Gut, 2,738★, MIT, v9.7.1 tracks Godot 4.7 (fetched 2026-09-26)
- gdUnit4 (godot-gdunit-labs/gdUnit4) — github.com/godot-gdunit-labs/gdUnit4, 1,242★, MIT, master tracks Godot 4.5–4.7.1, ships `GdUnitSceneRunner` (fetched 2026-09-26)
- godot-rl-agents — github.com/edbeeching/godot_rl_agents, 1,589★, MIT, commits through mid-2026; underlying paper arXiv:2112.03636 🕒(2021, stale as paper, repo itself current)
- barichello/godot-ci Docker image — github.com/abarichello/godot-ci, 1,131★, MIT (fetched 2026-09-26)
- chickensoft-games/setup-godot Action — github.com/chickensoft-games/setup-godot, 180★
- Godot Runtime Bridge (GRB) — github.com/Aesthetic-Engine/godot-runtime-bridge, 11★, MIT, requires Godot 4.5+ (fetched 2026-09-26); active CI (`grb-release-smoke.yml`), proof/mission workflow — small but purpose-built, low community traction
- Coding-Solo/godot-mcp — github.com/Coding-Solo/godot-mcp, 5,844★, MIT (fetched 2026-09-26) — **editor-only**, no screenshot/input-simulation despite third-party summaries claiming otherwise; verified directly against README
- NPGameDev/godot-mcp-toolkit — github.com/NPGameDev/godot-mcp-toolkit, 49★, MIT-per-README (fetched 2026-09-26) — "Playtests: start/stop game, capture screenshots, simulate input including typed text" — second viable runtime-bridge candidate
- CoderGamester/mcp-unity — github.com/CoderGamester/mcp-unity, 1,910★, MIT, includes `run_tests` (Unity Test Runner) and play-mode control (fetched 2026-09-26)
- Unity Runtime Fee cancellation / current pricing — unity.com/blog/unity-is-canceling-the-runtime-fee (2024-09, carried into current pricing), unity.com/products/pricing-updates (2025-11 update, +5% Jan 2026)
- Bevy 0.16 release — bevy.org/news/bevy-0-16/ (2025-04-24) 🕒 — could not confirm newer version this pass, flag as gap
- `bevy_brp_mcp` / `natepiano/bevy_brp` — github.com/natepiano/bevy_brp, 70★ (fetched 2026-09-26)
- VideoGameQA-Bench — arxiv.org/abs/2505.15952 (2025-05-21, Taesiri et al., verified via arXiv API)
- Human-AI Collaborative Game Testing — arxiv.org/abs/2501.11782 (2025-01-20, verified)
- "Do VLMs Understand Human Engagement in Games?" — arxiv.org/abs/2603.18480 (2026-03-19, verified via arXiv API)
- GameUIAgent — arxiv.org/abs/2603.14724 (2026-03-16, verified via arXiv API)
- OpenAI CUA on NYT Wordle, color-recognition failure (5.36% success) — arxiv.org/abs/2504.15434 (2025-04) — directly relevant to color-mechanic reliability risk
- Vals AI CUA-bench on commercial games — vals.ai/benchmarks/cua_bench (updated Sept 2026, current)
- Steam AI-disclosure policy + Jan 2026 "efficiency tools exempt" clarification — partner.steamgames.com/doc/gettingstarted/contentsurvey (official, live); gamedeveloper.com/business/valve-tweaks-and-clarifies-ai-disclosure-rules-for-steam (2026-01, within freshness window)
- Claude Opus 5.5 / Sonnet 5 API pricing — anthropic.com/claude/opus, anthropic.com/claude/sonnet, anthropic.com/news/claude-sonnet-5 (Opus 5.5 launched 2026-09-22, current)
- OpenAI GPT-5.x family pricing — cloudzero.com/blog/openai-pricing/ (current Sept 2026 snapshot, cross-referenced across 5 sources)
- AMD RADV/Mesa Linux driver status — docs.mesa3d.org/drivers/radv.html; amd.com RN-AMDGPU-UNIFIED-LINUX-25-20-3.html (Nov 2025, AMD went fully open-source on Linux)
- Colorblind Python tooling — pypi.org/project/daltonize/, github.com/DaltonLens/DaltonLens-Python (undated but current PyPI listings)
- Modl.ai black-box playtesting, no confirmed Godot support — modl.ai/game-testing-tools (undated marketing page) 🕒
- Regression Games, Unity-exclusive, no Godot support — regression.gg (undated) 🕒
- Baba Is Y'all automated solvability solver (closest published analog) — arxiv.org/pdf/2003.14294 (2020) 🕒 stale, no reusable library extracted
- EA SEED DRL-augmented game testing — arxiv.org/abs/2103.15819 (2020) 🕒 stale but most-cited industry paper in the space

## 4. Linux + AMD-iGPU Compatibility

Godot 4 runs well on the devbox's Radeon 890M via Mesa RADV (Vulkan) — AMD moved to a fully open-source Linux driver stack in Nov 2025, and RADV supports all RDNA architectures at Vulkan 1.4. For **local** dev-machine screenshot/movie capture, the real iGPU works fine with the default Forward+ renderer. For **headless CI** (GitHub-hosted Linux runners, no GPU), `--headless` disables rendering entirely — there is no shipped `--offscreen` mode (only an open, unmerged proposal, godot-proposals#5790) — so visual-capture CI jobs need Xvfb + Mesa software rasterizer (`llvmpipe`/`lavapipe`, via `LIBGL_ALWAYS_SOFTWARE=1` or Lavapipe ICD) or the `gl_compatibility` renderer, which tolerates software rasterization better than Vulkan Forward+. This recipe is **[INFERENCE]** — synthesized from the engine's documented constraints, not a single confirmed end-to-end Godot 4 tutorial; smoke-test before relying on it in CI. No NVIDIA/CUDA dependency exists anywhere in this stack (Godot, GUT/gdUnit4, godot-rl-agents' SB3 CPU training, Xvfb/Mesa) — the AMD-only devbox is not a blocker for any recommended tool.

## 5. Agent-Operability

- **CLI/headless**: `godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit` (GUT) or `godot --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://test` (gdUnit4) — both exit non-zero on failure, both emit JUnit XML for CI dashboards.
- **API/MCP**: Godot Runtime Bridge and NPGameDev/godot-mcp-toolkit both expose MCP tool surfaces an agent calls directly: launch game, screenshot, simulate keyboard/mouse/typed input, read live node state/logs — no bespoke integration code needed by the calling agent.
- **Text formats**: `.tscn`/`.tres` are UTF-8 text (diffable in `jj diff`), GDScript is plain text, JUnit XML and GRB's "proof bundle" JSON are structured and machine-parseable — a strong fit for the agent-swarm's preference for diffable/text-first tooling.
- **Headless CI**: `barichello/godot-ci` (Docker) or `chickensoft-games/setup-godot` (binary install) both run on GitHub-hosted `ubuntu-latest` runners with no license activation step (unlike Unity, which needs a licensed Editor seat even in batch mode).

## 6. Licensing, Commercial Rights, Steam AI-Disclosure

Godot (MIT), GUT (MIT), gdUnit4 (MIT), godot-rl-agents (MIT), GRB (MIT), godot-mcp-toolkit (MIT-per-README) — no royalty, revenue-share, or seat-licensing exposure anywhere in the recommended stack, unlike Unity Pro's $2,200/seat/yr (rising 5% Jan 2026) above the $200k free-tier ceiling. Per Valve's January 2026 Steamworks clarification, **AI-powered development/QA tooling used purely for workflow efficiency — including an agent-driven playtest pipeline — is explicitly exempt from Steam's AI-content disclosure requirement**, provided no artifact it produces (placeholder dialogue, patch notes, generated art) ships to players or the store page without separate human review; only player-facing AI-generated content (assets, live NPC dialogue) needs the Steamworks "Generative AI Content" survey disclosure. This is a direct, favorable [VERIFIED] answer to a real project risk.

## 7. Costs

All recommended core tools (Godot, GUT/gdUnit4, godot-rl-agents, GRB, GameAnalytics free tier) are $0 in licensing. The only recurring cost is VLM API calls for the visual-review layer: **Claude Opus 5.5** $4/$20 per M input/output tokens (launched 2026-09-22, 20% cheaper than predecessor), **Claude Sonnet 5** $2/$10 per M tokens (good default for volume screenshot review), **GPT-5.6 Terra** $2/M input. A 1024×1024 screenshot costs roughly 765–1,500 tokens depending on provider tokenization; a full-level visual QA pass (dozens of screenshots + colorblind variants, reasoning included) is low-single-digit dollars per run even at Opus rates, negligible at Sonnet rates — batch API halves both. Commercial black-box playtesting vendors (Modl.ai, Regression Games) are enterprise-priced-on-request and **neither has confirmed Godot support** — do not budget for them without a direct vendor confirmation call.

## 8. Risks/Unknowns

1. **Physics non-determinism**: Godot's (and Unity's, and to a lesser extent Bevy's) built-in physics is not guaranteed bit-identical across OS/CPU/engine-version — replay-based regression tests must diff recorded transforms/outcomes with tolerance, not assert frame-perfect physics reproduction.
2. **VLM color-perception unreliability**: OpenAI's CUA scored only 5.36% on a color-dependent Wordle task, and CUA-bench found 10× performance variance across minor UI changes — for a game whose *core mechanic is color*, the VLM visual-review layer must be paired with deterministic instrumentation (position/state logging, programmatic colorblind-contrast checks via DaltonLens-Python) rather than trusted alone for precision judgments.
3. **GRB is small (11★)**: purpose-built and well-tested internally (CI smoke workflow, proof-bundle tooling) but low community traction — validate hands-on before committing; NPGameDev/godot-mcp-toolkit (49★) is a credible fallback with an overlapping feature set.
4. **No off-the-shelf solvability/reachability library** exists for any engine — this must be custom-built (BFS/A* over a position×ability-state graph derived from Godot TileMap/physics data), a well-documented but unimplemented pattern; budget real engineering time here, not a library install.
5. **Godot export-exit-code unreliability**: `--export-release` can return exit code 0 on failure (3 separate open GitHub issues) — CI must grep verbose log output, not trust exit codes alone.
6. **Bevy version currency unconfirmed**: research surfaced Bevy 0.16 (Apr 2025) as latest confirmed but could not verify newer releases through Sept 2026 in this pass — moot for the recommendation since Bevy isn't primary, but flag if reconsidered later.
