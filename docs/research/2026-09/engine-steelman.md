# Violet engine re-evaluation: steelmanning Unity 6 and Unreal 5 against Godot 4.7

*Written 2026-09-26. Where I fetched a primary source, I link it. Claims marked [INFERENCE] are my own reasoning. Claims marked (>12 mo) rely on a source older than 12 months.*

## Verdict

| Art direction | #1 | #2 | #3 |
|---|---|---|---|
| **2D (default)** | **Godot 4.7.2**, but only narrowly ahead | **Unity 6.3 LTS**, close behind; not the 7th place the earlier report gave it | Unreal 5.8: don't use it |
| **2.5D** (a 3D world with 2D gameplay, like Ori, Planet of Lana, or Inside) | **Unity 6.3 LTS** | Godot 4.7 | Unreal 5.8. It has the best renderer, but it's the worst fit for this devbox and agent workflow |

Godot is still the right default, but for different reasons than the earlier report gave. It wins on two things: agents can read and edit its files as plain text, and it iterates cheaply on this machine. Unity wins on everything genre-specific: its 2D toolset, its track record, and first-party consoles. Unreal fails for Violet on disk space, GPU, binary assets, and 2D support.

---

## 1. 2D and 2.5D capability

**Unity 6 (steelman):** Unity has the most complete first-party 2D stack of the three:
- Tilemap with Rule Tiles
- Sprite Shape
- 2D Animation (skeletal) with the PSD Importer
- URP 2D lights (spot, freeform, sprite, global) with Shadow Caster 2D and normal and mask maps
- Cinemachine
- Shader Graph

Unity 6.3 LTS (released Dec 4, 2025, supported to Dec 2027) added Box2D v3 through a new LowLevelPhysics2D API. Unity says it brings multithreading, "enhanced determinism," and visual debugging ([6.3 LTS blog](https://unity.com/blog/unity-6-3-lts-is-now-available), [2D physics API docs](https://docs.unity.com/en-us/engine/6000.3/manual/unity2d/2d-physics-api)). Determinism matters for automated playtests.

**Unity critique:** The Box2D v3 API sits *beside* Rigidbody2D, not in place of it, so there are two physics paradigms. The existing prototype (Unity 2019.1.3f1, 2D Game Kit, Post-Processing v2, which only runs on the legacy Built-in pipeline) won't upgrade cleanly, so either engine means a rewrite. Its 1,183 lines of custom C# (233 in `Resonator.cs`) port anywhere.

**Godot 4.7 (steelman):** Godot 4.7 went stable on Jun 18, 2026, and 4.7.2 is current ([consoles page download link](https://godotengine.org/consoles/)). Its 2D is native, not a 3D engine with a flat camera:
- TileMapLayer
- CharacterBody2D
- PointLight2D and LightOccluder2D
- CanvasItem shaders that can read the screen, which is exactly what the grayscale-to-color effect needs
- Physics interpolation (4.3+)
- New in 4.7: one-way collision direction that you can configure

**Godot critique (concrete gaps):**
- **No pipeline precompilation for 2D.** The 4.7 docs say: "The engine does not currently feature precompilation for 2D elements and stutters will show up when the 2D node is drawn for the first time" ([docs](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html)). The resonance effect swaps color shaders mid-jump, which is precisely where that stutter would show. The fix is to warm shaders up at load time.
- **No Cinemachine equivalent built in.** You need an addon such as Phantom Camera.
- **Basic 2D skeletal animation.** You'd use Skeleton2D or the Spine runtime.
- **Less artist-oriented 2D lighting.** It supports normal maps and LightOccluder2D shadows, but has less tooling than URP 2D.
- **Its own physics solver, not Box2D.** Addons such as Rapier exist.
- **Few peers in this genre** (see §2).

**Unreal 5.8** (Jun 2026): Epic's 2D system is Paper2D. I found no Epic statement on its status; community sources say it's in maintenance mode. It has no 2D lighting pipeline and no skeletal animation, so you'd need the PaperZD or Spine plugins. Unreal's strength is 2.5D, and Epic's "Parrot" sample is a 2.5D platformer ([Epic](https://www.unrealengine.com/news/parrot-game-sample-a-new-practical-resource-for-game-devs-switching-to-unreal-engine)).

**If the art direction goes 2.5D:**
- **Unity** becomes #1: URP, Shader Graph, VFX Graph, Cinemachine, plus the strongest set of peer games (Ori, Inside, Planet of Lana I/II, Cocoon).
- **Unreal** has the best raw lighting (Lumen, MegaLights) but loses on this box (§4).
- **Godot** handles stylized 3D but has thinner VFX and lighting tooling.

## 2. Track record (verified attributions)

| Game | Engine | Source |
|---|---|---|
| Hollow Knight, **Silksong** | Unity (Silksong shipped on Unity 6) | [unity.com case](https://unity.com/made-with-unity/hollow-knight) |
| Ori (Blind Forest, Will of the Wisps) | Unity (Moon Studios' custom fork, "Moonity") | [Wikipedia](https://en.wikipedia.org/wiki/Ori_and_the_Will_of_the_Wisps) |
| GRIS, **Neva** | Unity | [Wikipedia: Gris](https://en.wikipedia.org/wiki/Gris), [Neva](https://en.wikipedia.org/wiki/Neva_(video_game)) |
| Inside | Unity (started on the Limbo engine, then switched) | [Wikipedia](https://en.wikipedia.org/wiki/Inside_(video_game)) |
| Cocoon | Unity | [Wikipedia](https://en.wikipedia.org/wiki/Cocoon_(video_game)) |
| Planet of Lana (I and II) | Unity | [Wikipedia](https://en.wikipedia.org/wiki/Planet_of_Lana) |
| Celeste | **Neither**: a custom C# engine (Monocle, on XNA/FNA) | [Wikipedia](https://en.wikipedia.org/wiki/Celeste_(video_game)) |
| Dome Keeper, Brotato, Cassette Beasts, Until Then, Case of the Golden Idol | Godot | [godotengine.org showcase](https://godotengine.org/showcase/) |
| Slay the Spire 2 | Godot, after 2+ years in Unity. Early Access Mar 5, 2026, PC only; consoles planned for 1.0 | [Wikipedia](https://en.wikipedia.org/wiki/Slay_the_Spire_II), [Mega Crit FAQ](https://www.megacrit.com/faq/) |
| Little Nightmares I–II (UE4), III (UE5); Bloodstained: RotN (UE4) | Unreal | [Wikipedia](https://en.wikipedia.org/wiki/Little_Nightmares_III), [Bloodstained](https://en.wikipedia.org/wiki/Bloodstained:_Ritual_of_the_Night) |

**This is the strongest argument against Godot.** Every acclaimed 2D or 2.5D story platformer in Violet's comparison set (GRIS, Ori, Neva, Hollow Knight) is on Unity, and I found **no** Godot game at that tier in the genre. Godot's hits (roguelites, RPGs, visual novels) do prove it ships on consoles: Brotato is on Switch, PS, and Xbox; Cassette Beasts on Switch and Xbox; Dome Keeper on Xbox; Until Then on PS5, Switch, and Xbox.

## 3. How well AI agents can operate each engine (the decisive axis)

### Serialization

- **Unity:** Scenes and prefabs are **text** (YAML), not binary as the earlier report said. The problem is indirection. The existing `Prototype.unity` is **23,878 lines, with 3,422 `fileID` refs, 355 `guid:` refs, and 161 YAML documents** (measured). A Sep 2026 paper notes that code-only agent tools "cannot answer basic cross-file questions, because these relationships live in `.meta` files and YAML assets." Its index cut agent tokens by 53% ([arXiv 2609.27585](https://arxiv.org/abs/2609.27585)). In practice, Unity agents drive the editor through MCP or C# editor scripts rather than editing YAML.
- **Godot:** `.tscn` and `.tres` files are compact text with `ext_resource` path and `uid://` references. The one catch: since 4.4, every script and shader has a companion `.uid` file that must be moved and committed together with it ([Godot article, Jan 2025](https://godotengine.org/article/uid-changes-coming-to-godot-4-4/), >12 mo). Agents can edit scenes by hand; that's the whole advantage.
- **Unreal:** `.uasset`/`.umap` files are binary, and Blueprints compile to bytecode. Agents can only act through the live editor.

### Headless mode, CI, and licensing

- **Godot:** `--headless` works with no license.
- **Unity:** `-batchmode` works, but "For Unity Personal, the Unity Hub is the only method for activating and returning licences" ([Unity docs](https://docs.unity.com/en-us/engine/6000.7/manual/get-started/install-and-upgrade/licenses-and-activation/license-activation-methods)). GameCI's workaround stores a `.ulf` license file plus the account email and password as CI secrets ([GameCI](https://game.ci/docs/github/activation/); unity-builder has 1,096★, pushed Sep 16, 2026).
- **Unreal:** Cooks and C++ builds are heavy [INFERENCE: minutes to tens of minutes, versus seconds in Godot].

### Iteration speed

- **Godot:** GDScript reloads without a compile step. 4.7 added live scene editing.
- **Unity:** Domain reload remains on Unity 6.x. The editor still runs on Mono in 6.7; the CoreCLR editor, which ends full domain reloads, lands in 6.8 or Unity 7 (Unity forums via secondary coverage). Fast Enter Play Mode became the default in 6.6.
- **Unreal:** **Live Coding is Windows-only.** On Linux, most C++ changes need a full editor restart ([Epic forum, 2022](https://forums.unrealengine.com/t/ue5-live-coding-hot-reload-on-linux/645512), >12 mo, still unchanged in current docs).

### MCP and first-party AI (GitHub stats pulled with `gh api` on 2026-09-26)

| Engine | First-party | Community (★, last push) |
|---|---|---|
| Unity | **Official Unity MCP** (Unity 6+, `com.unity.ai.assistant`). The FAQ says it's "free, with no concurrency limits" ([unity.com/features/ai](https://unity.com/features/ai)); the getting-started blog still lists Unity Cloud and an AI-beta trial as requirements. The AI Assistant costs $10/mo on Personal. Unity 7 promises a CLI and public API with "no full Editor access required" | **CoplayDev/unity-mcp 14,510★ (Sep 22, 2026)**; IvanMurzak/Unity-MCP 4,343★ (Sep 26); CoderGamester/mcp-unity 1,910★ (Sep 3) |
| Unreal | **Official Unreal MCP in 5.8, marked Experimental.** It's an in-editor HTTP server with Python/C++ toolsets and generates configs for Claude Code and Codex ([Epic docs](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US)) | chongdashu/unreal-mcp 2,087★ (**last push Apr 2025, stale**); ChiR24/Unreal_mcp 888★ (Sep 25) |
| Godot | **None** | Coding-Solo/godot-mcp 5,844★ (last push Apr 16, 2026, slowing); Godot-MCP-Native 805★; godot-mcp-pro 608★ |

So on first-party agent tooling, Godot is the *weakest* of the three. The earlier report had this backwards.

### Code-generation quality

I found no head-to-head benchmark across C#, C++/Blueprints, and GDScript. The only rigorous game-dev agent benchmark, GameDevBench, is built on Godot. Its best agent solves 53.8% of tasks, falling from 51.4% on gameplay tasks to 33.0% on 2D-graphics tasks. Visual feedback raised GPT-5.4 from 41.1% to 52.0% ([arXiv 2602.11103](https://arxiv.org/abs/2602.11103)). That shows agents can work in Godot, not that they work better there. [INFERENCE] C# has the larger training corpus and compile-time type checks. GDScript suffers from Godot 3 vs Godot 4 API confusion in training data.

## 4. Fitness for this Linux devbox (observed: `XDG_CURRENT_DESKTOP=COSMIC`, Wayland session, 79 GB free)

- **Godot:** A small single binary. It runs under XWayland by default; native Wayland is opt-in (`prefer_wayland`) and still has bugs in 4.7.x. **Best fit.**
- **Unity:** Ubuntu 24.04 is supported, but only on the **GNOME** desktop, with Wayland running through XWayland ([system requirements](https://docs.unity3d.com/6000.6/Documentation/Manual/system-requirements.html)). **This box runs COSMIC, which Unity doesn't support.** [INFERENCE] It will probably work under XWayland, but it's unsupported.
- **Unreal:**
  - Epic recommends Ubuntu 22.04, 32 GB RAM, **an RTX 2080-class GPU with 8 GB+ VRAM**, and RADV ≥24.2.8 ([Epic Linux requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine?lang=en-US)). The 890M iGPU has no dedicated VRAM and falls far below that [INFERENCE].
  - The binary editor takes ~43–65 GB installed and grows past 100 GB with projects (Arch wiki, forums). A source build needs 250–500 GB. **With 79 GB free, Unreal barely fits and a source build is impossible.**

## 5. Commercial

| | Godot | Unity 6 | Unreal 5 |
|---|---|---|---|
| Engine cost | MIT, $0 | Personal is free under $200K revenue plus funding. **Pro is required above that, and for consoles: $2,310/seat/yr** from Jan 12, 2026 ([pricing](https://unity.com/products/pricing-updates)) | 5% of lifetime gross above $1M; 3.5% if you launch on the Epic Games Store at the same time ("Launch Everywhere", from secondary coverage, Oct 2024, >12 mo; unrealengine.com/license returned 403) |
| Consoles | Third-party. **W4 Consoles Starter: $800/platform/yr or $2,000/yr for all platforms (<$300K revenue, ≤30 staff); Pro: $4K / $10K** ([w4games.com](https://www.w4games.com/w4consoles)). Switch 2 port in beta. Godot's site lists 8 porting houses | First-party, Pro plan required | First-party |
| Steam integration | GodotSteam: GitHub repo archived, development moved to Codeberg; 4.4+ GDExtension released Sep 4, 2026 | Steamworks.NET 3,622★ (pushed Aug 2026) | Online Subsystem Steam (built in) |
| Asset store | Small | Largest | Fab (large, 3D-heavy) |

[INFERENCE] For a solo developer, a Godot console SKU costs *less* per year than Unity Pro. Platform devkit fees apply in every engine.

## 6. Risk

- **Unity:** The Runtime Fee was announced in Sep 2023 and cancelled in Sep 2024 ([Unity blog](https://unity.com/blog/unity-is-canceling-the-runtime-fee), >12 mo). Unity now commits to "predictable, annual price adjustments" (5% in 2026; Havok dropped from Pro in 6.3). Unity 7 (Q1 2027) promises "no major breaking changes." The remaining risk is trust and subscription creep, not a per-install fee.
- **Godot maturity gaps that bite a commercial 2D game:**
  1. First-draw stutter on 2D shaders.
  2. No in-house console support: you depend on W4 and porting houses, and W4's C# console support is still beta.
  3. No first-party MCP.
  4. Native Wayland editor is buggy.
  5. No 2D skeletal animation or camera rig at Unity's level.
  6. No precedent at the Ori or GRIS tier in this genre.
- **Unreal:**
  - It's overkill for 2D.
  - Its assets are opaque to agents.
  - Its Linux iteration is poor.
  - **UE6 churn:** Blueprints and Actors will "eventually be deprecated" in favor of Verse, and UE6 Early Access is due late 2027 ([Game Developer](https://www.gamedeveloper.com/programming/unreal-engine-6-will-merge-ue5-and-uefn-into-a-single-unified-engine-)). That lands mid-production [INFERENCE].

## 7. What would change the ranking

**Switch the 2D pick to Unity if any of these happen:**
1. The art direction goes 2.5D.
2. A one-week agent-only bake-off (build the Resonator mechanic in both engines) shows Unity-via-MCP success within about 10% of Godot's, with play-mode entry under 5 s on this box.
3. Godot's 2D shader-swap stutter can't be hidden by warming shaders up at load.
4. A publisher requires Unity or a day-one console launch.
5. You hire a human technical artist or animator who knows Unity.
6. Unity 7's CLI and public API ship (Q1 2027) and work headless on Linux.

**Switch to Unreal only if both of these happen:**
1. Photoreal or cinematic 2.5D (Little Nightmares-grade lighting) becomes an art pillar.
2. Development moves to a Windows workstation with a discrete GPU and 500 GB+ free disk.

**Drop Godot if:** W4 console ports prove unreliable, or agents' success on your own 2D-graphics tasks stays far below their success on gameplay tasks even with visual feedback.

## 8. Earlier Godot recommendation: claims I found wrong or overstated

1. **"Unity 7 announced Dec 2026."** Wrong. It was announced Jul 21, 2026 at Unite Seoul. Early beta is December 2026 and full release Q1 2027 ([Unity press release](https://unity.com/news/unity-7-roadmap-revealed-at-unite-seoul)).
2. **"Unity-7-native Claude/Codex support."** Not in the primary source. Unity says a "free-to-use MCP will connect coding agents." An official Unity MCP already exists on Unity 6.
3. **"Godot 4.5.2 current, 4.6 in RC."** Stale. 4.6 shipped Jan 2026, 4.7 on Jun 18, 2026, and 4.7.2 is current.
4. **"Unity: No text scene format (binary/YAML hybrid)."** Wrong. Unity scenes are text YAML. The real cost is GUID and fileID indirection.
5. **"W4 pricing not public."** Wrong. It's published ($800/platform or $2,000/yr for all platforms at Starter).
6. **"Unity Linux editor officially supported since 2015."** Wrong. The 2015 build was experimental; official support came with 2019.1.
7. **"$2,200/seat Pro."** Stale. It's $2,310/yr from Jan 12, 2026.
8. **"Many MCP servers (300+ tools), official-adjacent" as a Godot advantage.** Overstated. Godot is the only one of the three with *no* first-party MCP. Unity's biggest community server (14.5K★) is 2.5× Godot's (5.8K★).
9. **"Jolt default in 4.6" and "Compositor" listed as 2D strengths.** Both are 3D features. The report also left out the documented lack of 2D pipeline precompilation.
10. **"Unity via XWayland should be fine on Pop!_OS 24.04."** Missed that this box runs COSMIC, which Unity doesn't support (it supports GNOME only).
11. **Ranking Unity 7th, behind MonoGame, Bevy, GameMaker, and the web stack.** Indefensible: Unity owns this genre's track record.
12. **Console flip condition "→ Unity 6 or MonoGame."** It missed that Unity consoles need Pro ($2,310/seat/yr) while W4 Starter costs $2,000/yr for all platforms.
13. **Unreal was never evaluated.** It is now: wrong fit for 2D and for this box.
14. **Vendor and anecdotal evidence** (the summerengine.com blog, the "Somnia" post) was used as support. GameDevBench shows Godot is *workable* for agents, not *better* than Unity.
