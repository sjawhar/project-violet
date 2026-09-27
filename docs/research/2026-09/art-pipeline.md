# Violet — AI-Assisted 2D Art Pipeline Research
Research phase only. Current as of **2026-09-26**. Devbox: Pop!_OS 24.04, Ryzen AI 9 HX PRO 370 / Radeon 890M (gfx1150) iGPU, no NVIDIA.

## 1. Ranked Recommendation

**Primary style: low-poly 3D authored in Blender, rendered to 2D ("3D-rendered-to-2D"), with vector (Recraft) for UI/icons/VFX and pixel-art AI tools reserved for greybox prototyping only.** The mechanic requires every world element be *discretely and permanently* taggable red/yellow/green/blue-or-neutral, so the engine can toggle visibility/collision and QA can verify the channel mapping. Hand-painted/illustrated art (GRIS-style) best fits "light-based, mindfulness" thematically but is the *worst* mechanical fit: painted washes blend hue continuously, undermining unambiguous per-object color reads — a real legibility/accessibility risk (c.f. *Hue*, the closest existing comp for a color reveal/hide mechanic, which uses flat, saturated, unambiguous blocking for this reason). Low-poly-3D reconciles the two seemingly-contradictory phrases in the old docs ("vibrant and light-based" + "low-poly"): tag each mesh/material with a custom `resonance_color` property, group into Blender collections per color, and render (a) a flat/toon-shaded grayscale beauty pass plus (b) one clean per-color matte per collection via View Layers — *authored* separation, not reconstructed-after-the-fact, and free (Blender is FOSS, scriptable via CLI + `bpy`, zero per-asset cost). Colored/directional lighting and bloom in the toon pass deliver the "vibrant, light-based" mood. Use **Recraft** for anything purely 2D (HUD, icons, VFX shapes, marketing) since SVG shapes are trivially parseable/re-taggable by an agent. Use **PixelLab + Retro Diffusion + Aseprite CLI** only for early greyboxing (cheapest, most mature AI-native tooling, indexed palettes built in) — not shipped assets, given the legibility case above. Frontier multimodal models (Nano Banana Pro, FLUX.2, GPT-Image-2) are right for concept art and reference sheets feeding the Blender/Recraft pipeline, not for final in-engine assets needing per-element color tags.

## 2. Style-Fit Comparison

| Style | Mechanic fit (discrete per-color tagging) | Thematic fit (light/mindfulness) | AI tooling maturity (2026) | Verdict |
|---|---|---|---|---|
| Pixel art (indexed palette) | Excellent — palette index *is* a channel | Good, but "vibrant light" reads as retro, not painterly | Most mature (PixelLab, Retro Diffusion, Ludo.ai, Aseprite ecosystem) | Prototyping / fallback |
| Hand-painted / illustrated | Poor — continuous color blending defeats channel tagging | Best (GRIS/Ori comp) | Weakest for consistency across hundreds of assets | Backgrounds/wash layers only, not interactive elements |
| Vector / flat (Recraft) | Excellent — shapes are discrete objects with explicit fill color | Good for bold saturated color; "light" needs added glow layers | Strong (Recraft is purpose-built for this) | UI/icons/VFX, secondary asset class |
| 3D-rendered-to-2D, low-poly | Excellent — author true per-object color tags in the DCC tool | Best combination with "low-poly" note in old docs; colored lighting is native to 3D | Strong (Blender is free, scriptable, mature); AI used for concept refs only | **Primary recommendation** |
| 2.5D (parallax 2D over depth) | Moderate — depends on underlying 2D technique | Good | No dedicated tooling advantage over vector/3D | Not recommended as primary |

## 3. Tool Comparison

| Tool | Category | Pricing (2026) | Commercial rights | Agent-ops | Linux/AMD note |
|---|---|---|---|---|---|
| PixelLab | Pixel art platform | Free trial; $12/$24/$50 mo tiers; API pay-per-image (~$0.10–0.19/sprite) | User owns output, commercial+non-commercial, no training-other-models clause | REST API (`api.pixellab.ai`), Aseprite plugin; no confirmed official MCP | Cloud SaaS, OS-agnostic |
| Retro Diffusion | Pixel art model + API | Credits from $5; $0.015–$0.18/image, $0.10 tilesets, ~$0.07–0.25/animation | User owns IP on generated art; models trained on artist-licensed data | REST API + **hosted MCP server** (`mcp.retrodiffusion.ai`) | Cloud SaaS |
| Scenario.gg | Game-asset platform + LoRA | Free 50 credits/day; $15/$45/$75 mo tiers; LoRA train 100–500+ CU/run | Private by default (paid tiers), SOC2 II | REST API, dry-run cost estimate | Cloud SaaS |
| Layer.ai | Multi-modal asset platform | Consumption "Creative Units"; $10/mo=300 CU, $60/1000 CU | Enterprise IP-safety controls available | REST API, CLI, JS/TS SDK | Cloud SaaS |
| Ludo.ai | Asset studio (2D/3D/audio/video) | Free 30 credits; $20/$50 mo + Studio | Standard commercial terms | API + **MCP** (Pro plan+), Unity plugin | Cloud SaaS |
| OpenAI GPT-Image-2 | Frontier image API | $0.03/$0.05/$0.08 per image (1K/2K/4K) | Full commercial rights; C2PA metadata; indemnification with caveats | REST API only | Cloud SaaS |
| Google Gemini "Nano Banana" (2/Pro/Lite) | Frontier image API | $0.03–$0.24/image depending on tier/res; batch −50% | Commercial use allowed; SynthID watermark mandatory, cannot be removed | REST API | Cloud SaaS |
| Black Forest Labs FLUX.2 / Kontext | Frontier image + editing API | ~$0.03–0.05/megapixel; batch-4 from $0.12 | Open-weight variants + hosted API; check per-model license | REST API | Cloud SaaS; open weights (FLUX.1 dev/schnell) runnable locally |
| Recraft | Vector/SVG + raster API | $0.022–$0.30/image depending on model/mode | **Paid plans only**: full commercial rights; Free tier = personal use only, public gallery; no train-other-models clause | REST API | Cloud SaaS |
| Stability AI (SD 3.5 / SDXL) | Open + hosted diffusion | API credits $0.01=1cr, $0.025–0.08/image; Membership $20/mo | Free commercial use <$1M revenue (Community License); Enterprise license required above | REST API; open weights self-hostable | **Self-hostable on Radeon 890M** via ComfyUI/SD.cpp |
| Midjourney | Image generation | $10–$120/mo subscriptions | Paid subscribers get commercial rights (revenue-gated above $1M); no IP indemnification | **No broadly-available official API as of Sept 2026** — unofficial wrappers violate ToS | Not recommended for agent pipeline |
| Meshy AI | Image/text-to-3D | Free 100–200cr; $20/$40/$100 mo; ~20–30cr/model | Paid-plan output = private commercial license; free tier = CC BY 4.0 | REST API | Cloud SaaS |
| Tripo3D | Image/text-to-3D | Pay-as-you-go, 1cr=$0.01; ~20–95cr/model (~$0.20–0.65) | Standard commercial terms per plan | REST API | Cloud SaaS |
| Aseprite | Pixel editor | One-time ~$20 | Your assets, your rights | **Full CLI + Lua scripting**, fully headless (`-b`) | Native Linux build |
| LibreSprite | FOSS Aseprite fork | Free | N/A (FOSS, MIT) | Lua-based scripting API; CLI automation less documented than Aseprite | Native Linux |
| Pixelorama | FOSS 2D editor (Godot-built) | Free | N/A (FOSS, MIT) | **Documented CLI** for headless batch export, spritesheets, scaling, JSON | Native Linux |
| Krita | FOSS painting app | Free | N/A (FOSS, GPL) | Python (PyKrita) scripting; no dedicated pixel-art CLI | Native Linux; Krita 6 (Qt6, 2026) adds Wayland support |
| Inkscape 1.4.4 | FOSS vector editor | Free | N/A (FOSS, GPL) | **Full CLI**: `--export-id`, `--actions`, `--batch-process`, shell mode | Native Linux |
| Blender | FOSS 3D suite | Free | N/A (FOSS, GPL) | **Full CLI + `bpy` Python API**, headless `--background --python` | Native Linux; EEVEE viable on Radeon 890M |
| ComfyUI | Local/cloud diffusion UI | Free (local); Comfy Cloud usage-based | Depends on underlying model | **Official "Comfy MCP" (beta, June 2026)** + community MCP servers | ROCm on gfx1150 (official as of ROCm 7.2.1/10.0.0) or Vulkan backend |
| stable-diffusion.cpp | Local inference | Free | Depends on underlying model | CLI only | Vulkan backend works on any AMD iGPU without ROCm; good VRAM efficiency via quantization |

## 4. Evidence List (primary sources, dated; ⚠ = >12mo old / re-verify)

- Steam AI disclosure — steamcommunity.com/groups/steamworks/announcements/detail/3862463747997849619 (Jan 2026)
- OpenAI pricing/terms — developers.openai.com/api/docs/pricing, openai.com/policies/service-terms (Sept 2026)
- Google Gemini image pricing/ToS — curlscape.com/blog/google-gemini-api-pricing-guide-2026, support.google.com threads (2026)
- Black Forest Labs FLUX — bfl.ai/pricing, docs.bfl.ml/quick_start/pricing, docs.bfl.ml/guides/usecases_editing_character_consistency (2026)
- Recraft pricing/rights — recraft.ai/pricing?tab=api, recraft.ai/docs/plans-and-billing/commercial-rights-and-ownership (2026)
- Stability AI license — stability.ai/license, stability.ai/news-updates/introducing-stability-ai-membership ⚠ (membership terms 2023, AUP re-confirmed 2025-07-31)
- Midjourney API status — updates.midjourney.com/enterprise-api-survey (survey Jul 2025, no shipped API as of Aug 2026)
- PixelLab API/ToS — pixellab.ai/pixellab-api, pixellab.ai/termsofservice (2026)
- Retro Diffusion API/MCP — github.com/Retro-Diffusion/api-examples, mcp.retrodiffusion.ai (2026)
- Scenario.gg — scenario.com/pricing (2026); Layer.ai — layer.ai/pricing, layer.ai/docs (2026); Ludo.ai — ludo.ai/pricing, ludo.ai/features (2026)
- Meshy AI — meshy.ai/pricing, meshy.ai/api (2026); Tripo3D — developers.tripo3d.ai/en/pricing, platform.tripo3d.ai/docs/billing (2026)
- AMD ROCm gfx1150 matrix — rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html (2026, ROCm 7.2.1/10.0.0)
- ComfyUI-on-ROCm guide — rocm.docs.amd.com/.../installcomfyui.html (2026)
- stable-diffusion.cpp Vulkan — go.backend.ai/en/manual/acceleration/stable-diffusion-cpp ⚠ (7840U benchmark Jan 2024, RX580 benchmark late 2025; no gfx1150-specific first-party benchmark found — treat perf as directional)
- Aseprite CLI/Lua — community.aseprite.org threads (ongoing 2024–2026)
- Pixelorama CLI — pixelorama.org/user_manual/cli (2026); Krita 6/Wayland — krita.org/en/posts/2026/monthly-report-2608 (Aug 2026)
- Inkscape 1.4.4 CLI — wiki.inkscape.org/wiki/Using_the_Command_Line (stable since 1.0/1.2, release May 2026)
- Blender headless/bpy — blender.stackexchange.com/questions/1365 ⚠ (core CLI mechanism, unchanged for years, low staleness risk)
- VideoGameQA-Bench (VLM QA limits) — arxiv.org/html/2505.15952v1 ⚠ (May 2025), asgaardlab.github.io/videogameqa-bench (2025)
- Adobe Research VLM specialist-assessment — research.adobe.com/publication/vision-language-models-learn-to-assess-images-with-specialists (Mar 2026)
- Normal-map tools (Sprite-AI, Laigter, AwesomeBump) — vendor sites, Aug 2026 comparison ⚠ (Laigter/AwesomeBump base code is several years old, still maintained)
- **⚠ Low-confidence cluster**: Tilewise, SpriteForge.tech, PixExact, SpriteCook, AnnoMotion, SpriteLab — surfaced only via near-identical SEO/vendor copy across "independent" domains; unverified beyond marketing claims until hands-on trial.

## 5. Linux + AMD-iGPU (Radeon 890M / gfx1150) Compatibility

gfx1150 (RDNA 3.5) is **officially listed** in the ROCm 7.2.1 / 10.0.0 compatibility matrices for Ryzen AI 300-series iGPUs, and AMD publishes a first-party ComfyUI-on-ROCm install guide; kernel support landed by Linux 6.7 (Oct 2023), well before Pop!_OS 24.04. Some 2025 community reports needed `HSA_OVERRIDE_GFX_VERSION` workarounds for RDNA 3.5 iGPUs, but current docs treat gfx1150 as supported. **Recommendation**: use the **Vulkan backend** (stable-diffusion.cpp or ComfyUI's Vulkan path) as the primary local path — no ROCm install needed, works on any AMD GPU, and single-image generation on Vulkan reportedly matches or beats ROCm (ROCm wins only on batched throughput). With 89GB RAM shared as iGPU memory, VRAM isn't the bottleneck; use quantized (Q8/Q4) checkpoints. Treat local generation as **supplementary** (offline ideation, ControlNet/LoRA experiments, free bulk palette tests) — cloud APIs remain faster/higher-quality for shipped assets, and Blender's EEVEE (the actual pipeline renderer) already runs well on the 890M with no ROCm at all.

## 6. Agent-Operability (CLI / API / MCP / text formats / headless)

The pipeline is agent-friendly almost everywhere: **Blender** (`--background --python`, full `bpy`, deterministic, zero per-call cost) and **Aseprite** (`-b` batch, `--script`, Lua, JSON/`.aseprite` export) are the two load-bearing headless tools, both network-free — ideal for regenerating hundreds of frames deterministically when the art bible changes. **Inkscape 1.4.4** adds a mature CLI (`--export-id`, `--actions`, shell mode) for vector/UI work; **Pixelorama** ships a documented CLI as a Godot-native FOSS fallback. **Python/Pillow + ImageMagick** are the universal glue — `Image.quantize(palette=...)` / `magick -remap palette.png` lock art to a fixed master palette, the concrete mechanism for enforcing "each element maps to one of 4 categories," at zero cost. For frontier-model work: **Retro Diffusion ships a hosted MCP server**, **Ludo.ai bundles MCP** (Pro tier), and **ComfyUI got an official "Comfy MCP" beta** (June 2026) plus community servers — turning ComfyUI into an agent-callable tool for ControlNet character-turnarounds or batch tilesets without hand-building node graphs. OpenAI/Gemini/FLUX/Recraft/Stability/Meshy/Tripo are plain REST APIs (agent-trivial, no MCP needed). **Midjourney has no broadly-available official API** as of Sept 2026 — exclude it from automated tooling.

## 7. Licensing, Commercial Rights, and Steam AI Disclosure

Every recommended paid tool grants commercial rights to output. Two traps: **Recraft's free tier is personal-use-only and publicly gallery-visible** (must be paid before shipping); **Stability's Community License caps free commercial use at <$1M annual revenue** (irrelevant pre-launch). Purely AI-generated output is **not independently copyrightable** under current U.S. guidance; routing every AI draft through human-directed compositing (palette-locking, color-tagging, Blender scene assembly) — already mechanically required — makes the shipped asset a human-authored derivative, the practical path to partial copyright. **Steam's AI disclosure policy** (clarified Jan 16–17, 2026) requires a text-box disclosure in the Steamworks Content Survey for AI-assisted content that **ships and is consumed by players** — covering essentially every asset this pipeline produces; concept-ideation/dev-efficiency tooling that never ships is exempt. No live-generated-AI content applies here (no runtime generation), so the simpler "Pre-Generated" track suffices: describe tools/process, affirm no illegal/infringing material. Maintain this disclosure text as a living art-bible section, since Valve reviews it pre-release and a stale disclosure can delay approval.

## 8. Costs (order-of-magnitude, pre-launch indie scale)

- **Per-image cloud generation**: $0.01–$0.25/image across OpenAI/Gemini/FLUX/Recraft/Stability, depending on model and resolution; a few thousand exploratory concept-art generations across a full production ≈ low hundreds of dollars.
- **Per-3D-asset**: Meshy/Tripo ≈ $0.20–0.65/model — relevant only if using them for concept blockouts, not for the primary hand-authored Blender pipeline.
- **Subscriptions** (optional, mostly for the prototyping branch): PixelLab $12–50/mo, Retro Diffusion pay-as-you-go from $5, Ludo.ai $20–50/mo, Scenario $15–75/mo, Layer.ai from $10/mo — pick at most one or two for greybox/prototyping; none are required for the primary Blender+Recraft pipeline.
- **Core pipeline tools**: Aseprite one-time ~$20; Blender, Inkscape, Krita, Pixelorama, LibreSprite, ComfyUI, stable-diffusion.cpp all free/FOSS.
- **Local compute**: effectively $0 marginal (hardware owned); electricity only.
- Net: the *recommended* primary pipeline (Blender + Recraft + Aseprite/Pillow/ImageMagick) has near-zero recurring cost; discretionary spend is concentrated in frontier-API concept art and optional prototyping subscriptions, likely $50–300/month during active production depending on volume.

## 9. Risks / Unknowns

- **Accessibility/legibility risk is the biggest one**: a 4-color mechanic gated on hue alone fails ~8% of players (colorblindness). This is independent of art-style choice and must be solved with redundant coding (distinct value/pattern/shape/icon per color), not flagged as an art-pipeline problem alone — a cross-cutting design decision, not fully resolved by tool choice.
- **Model churn**: OpenAI has already deprecated DALL-E 2/3 (May 2026) and is sunsetting GPT-Image-1/1.5 by Dec 2026; do not hard-pin a pipeline to one model ID — wrap every provider behind a thin adapter.
- **AI copyrightability**: purely-generated output is likely uncopyrightable standalone; the human-compositing step this pipeline already requires (for color-tagging) is also the practical fix.
- **Midjourney exclusion**: no official broad API exists; do not build agent tooling against unofficial wrappers.
- **Low-confidence tool cluster**: several "AI tileset generator" sites (Tilewise, SpriteForge, PixExact, SpriteCook, AnnoMotion, SpriteLab) surfaced only via uniform SEO content, no primary docs found — verify hands-on; prefer Retro Diffusion's/PixelLab's/Ludo.ai's built-in tileset features, which have primary documentation.
- **ROCm/gfx1150 maturity**: official support is recent (2026); some historical reports needed `HSA_OVERRIDE_GFX_VERSION` workarounds specific to RDNA 3.5 iGPUs. No first-party gfx1150 ComfyUI/SD.cpp benchmark was found — test locally before relying on it for anything pipeline-critical; Vulkan is the safer default.
- **VLM art-critique limits**: documented ~20–25 percentage-point gap between glitch *detection* and accurate *description*, plus documented cultural/aesthetic scoring bias (Western-art bias in cross-cultural evaluation, Jan 2026 study). Use VLM review as a fast first-pass checklist (palette compliance, silhouette clarity, obvious artifacts), never as the sole or final art-direction gate — keep a human review step.
- **Art bible + agent context**: no single "art bible" tool exists; the evidence-backed pattern is a Markdown art bible (mood board, palette system, per-color asset rules, naming conventions, Steam-disclosure text) committed to the repo like a `CLAUDE.md`-style context file, kept current as a living document the agents read before generating or reviewing assets — version-controlled via jj alongside code, not a separate binary format.
