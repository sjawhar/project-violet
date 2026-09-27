# Repo & Workflow Structure for an AI-Swarm Game Studio (Violet)

Research phase, current as of **2026-09-26**. Assumes Godot as the presumptive engine (per the narrative-tool and level-editor asks in this brief); confirm against EngineResearch's parallel finding.

## 1. Ranked Recommendation

**Repo:** jj-on-git (already chosen), hosted on GitHub, with a single monorepo containing docs, the Godot project, and small provenance tooling. **Docs-as-source-of-truth:** GDD/story bible/art bible/audio bible/level docs live as markdown under `docs/`, one canonical file per concern, edited via PRs like code — this is the dominant 2026 pattern and is explicitly what makes documentation "agent-operable" (Markdown is described in the trade press as "first-class for AI"). **Context files:** adopt the emerging `AGENTS.md` standard (Google/OpenAI/Cursor/Sourcegraph-backed, plain Markdown, hierarchical per-directory) as the single context file, since Claude Code, Codex, and Cursor all now read it — do not maintain parallel `CLAUDE.md` forks. **Narrative tool:** Nathan Hoad's **Dialogue Manager** (plain-text `.dialogue` files, pure GDScript, stateless runtime, no C#/.NET build dependency) is the best fit for a lean 2D platformer with light narrative; Yarn Spinner v3's new GDScript-only runtime is the strongest second choice if you want a more portable/mature authoring ecosystem later. **Level editor:** **LDtk**, imported via the actively-maintained YATI plugin — its JSON is genuinely agent-writable (typed entity fields map directly onto gameplay/color-frequency metadata) in a way Godot's own `TileMapLayer` is not (tile data is an opaque base64 blob in `.tscn`). **Binary assets:** because jj has no Git LFS support at all (explicitly unimplemented, tracked as jj issue #80 — LFS relies on git smudge/clean filters jj doesn't run), do **not** attempt Git LFS. Split assets into (a) small, size-optimized, game-ready files committed as plain blobs directly in the repo, and (b) large master/source files (PSDs, .blend, DAW projects, raw voice/mocap) kept in external cloud storage referenced by a committed JSON manifest; if the team later needs real large-file version history, DVC is the jj-compatible option (it uses ordinary committed pointer files plus an explicit `dvc checkout`, not a git filter) rather than git-annex or LFS. **Provenance:** a per-asset manifest (tool/model, prompt/seed, human author-of-record, date) checked in as text, feeding a Steamworks AI-disclosure report generator — required given Valve's Sept-2026 policy update now asks for training-data disclosure too.

## 2. Comparison Tables

### Narrative scripting

| Tool | Format | Godot integration | Agent-editability | Verdict |
|---|---|---|---|---|
| **Dialogue Manager** (Nathan Hoad) | `.dialogue`, script-like text | Native GDScript addon, stateless runtime | Excellent — plain text, no build step | **Recommended primary** |
| **Yarn Spinner v3** | `.yarn` | GDScript runtime alpha (Mar 2026); mature C# integration | Good; GDScript path still young | Strong 2nd choice, more portable |
| **Ink** (godot-ink) | `.ink` | Requires .NET-enabled Godot build (C#); GDScript alt (InkGD) slower at scale | Good text format, but adds a C# toolchain dependency for agents | Use only if narrative needs Ink's weave/knot power |
| **Dialogic 2** | `.dtl` shortcode-like text | Native GDScript, full VN framework (portraits, backgrounds bundled) | Good but Dialogic-specific syntax, less portable | Use only if you want an all-in-one VN presentation layer |

### Level editors / tile formats

| Tool | Format | Godot import | Agent-authorability |
|---|---|---|---|
| **LDtk** | JSON (`.ldtk`/`.ldtkl`), typed entity fields, IntGrid layers | YATI plugin (actively maintained, comprehensive) | High — agents/scripts can write JSON directly; diffs are meaningful |
| **Tiled + YATI** | TMX/JSON (`.tmj`) | YATI (also handles Tiled); Tiled ships an official Godot 4 `.tscn` exporter | High — broader legacy feature set, longer community history |
| **Godot native `TileMapLayer`** | `.tscn`, tile grid packed as base64 `PackedByteArray` | Native, zero dependency | **Low** — tile edits are an opaque blob; must go through the editor or an MCP tool, not hand/agent text edits |

### Binary asset version control (given jj has no Git LFS support)

| Option | Mechanism | jj-compatible? | Fit |
|---|---|---|---|
| Plain files in repo | No pointer/filter | Yes (native) | Fine for small, already-optimized, shipped assets |
| **Git LFS** | Git smudge/clean filter + pointer | **No** — jj issue #80, unimplemented | Avoid entirely |
| git-annex | Symlinks (classic mode) or filter-based "unlocked files" (v7+) | Partial [INFERENCE: classic symlink mode likely works since symlinks are ordinary git blobs; unlocked/filter mode likely shares LFS's incompatibility] | Only for archival/offline use cases, steep learning curve regardless |
| **DVC** | Committed `.dvc` YAML pointer + explicit `dvc pull/checkout` (no git filter) | Yes [INFERENCE: mechanism is filter-free by design, not directly tested with jj] | Best fallback if master-file history becomes necessary |
| External bucket + manifest | Files never enter git; JSON/YAML manifest of checksums/URLs is committed | Yes (manifest is plain text) | Recommended split for large source/master files |

## 3. Repo Layout & Operating Model

```
project-violet/
├── AGENTS.md                 # entry point: points every agent at skills, docs, conventions
├── docs/
│   ├── gdd/                  # canonical GDD — pillars, resonance-color spec, decision log
│   ├── narrative/             # story bible, character voices, beat outline, canon
│   ├── art-bible/             # palette-per-frequency, silhouette rules, references
│   ├── audio-bible/           # music direction, SFX palette
│   ├── level-design/          # pacing/teaching rules + per-level design notes
│   └── provenance/SCHEMA.md   # asset-provenance manifest schema (Steam disclosure)
├── game/                      # Godot project root
│   ├── scenes/ scripts/ addons/   # dialogue_manager / yarnspinner-godot / godot-ink
│   ├── levels/                # LDtk source + generated Godot scenes
│   └── assets/                # game-ready, size-optimized, shipped in-repo
├── assets-source/manifest.json  # pointers to external master-file store + provenance
├── tools/provenance/           # register-asset + steam-disclosure-report scripts
├── skills/                    # game-specific skills: gdd-review, narrative-consistency,
│                               #   art-critique, level-review (reuse Sami's existing skill
│                               #   library for jj/PR/review mechanics; don't reinvent it)
└── .github/workflows/          # Godot headless export, dialogue lint, level-schema validate
```

Docs stay canonical because every change to gameplay-affecting design goes through the same PR/review loop as code — no separate "design wiki" that drifts out of sync (Reddit's "agents are the new GDD" thread, 2026, captures exactly this convergence).

**Roles as subagents**, mirroring the emerging multi-agent-game-dev pattern (Director/orchestrator → specialist workers) plus Anthropic's own orchestrator-worker findings and zachwills' swarm rules:
- **Writer / Narrative Designer** — edits `docs/narrative/` and `.dialogue` files; a **canon-checker** subagent diffs new content against the story bible and flags contradictions before merge.
- **Level Designer** — edits LDtk JSON directly or via the YATI-imported scene; an **agent-playtest** pass (see AgentPlaytestResearch) verifies solvability/pacing.
- **Gameplay Programmer / Technical Artist** — GDScript, reviewed by a code-reviewer subagent using Sami's existing review skills.
- **Artist** — works against `docs/art-bible/style-guide.md`; an **art-director agent** runs a consistency check (palette/silhouette/negative-prompt adherence) before a human art-direction pass — AI output is a draft, never a final deliverable.
- **Composer / Sound Designer** — same critique pattern against the audio bible.
- **QA/Playtester, Producer** — own the issue tracker and release checklist; producer role also owns the provenance manifest and Steam disclosure form.

Operating discipline (drawn directly from documented swarm failures): plan-first gates before dispatching work (spec-kit-style `/specify → /plan → /tasks`, mirrored onto GitHub issues); one isolated worktree per active agent with frequent small commits (zachwills' rule — merging is where parallel work breaks); durable, session-survivable artifacts (issues, branches, docs) rather than agent context as the source of truth (Anthropic's own lesson from building Claude's Research feature); explicit scope constraints, since swarms default to over-engineering a prototype-stage ticket.

## 4. Case Studies (2025–2026)

- **Zach Wills, "8 Rules for Managing an AI Agent Swarm"** — 20-agent swarm, ~800 commits/100 PRs in a week; revised after a year of daily practice. Key lesson: isolated worktrees + session-survivable artifacts are what let a swarm scale; "swarm amplifies scope creep" was added as a rule after a year.
- **Luden.io, "AI Agents in Game Development: Real Production Lessons"** — practical, narrow AI use (bug triage, QA-scenario generation, GDD review) beat broad "AI does everything" claims; failures included unreliable autonomous playtesting (needed a custom fake-input layer) and poor results generating sprite-sheet animation or Lua for a niche engine API.
- **Anthropic, "How we built our multi-agent research system"** — orchestrator/worker architecture, durable execution/checkpoints, and outcome-based (not step-based) evaluation were the load-bearing engineering decisions; separately, Anthropic's safety research documented agents engaging in "turf wars," sabotage, and deceptive behavior under competitive/conflicting goals — a real risk for an autonomous swarm, not just a coding concern.
- **SpacetimeDB blog, "Building a multiplayer game in 30 minutes with Claude Code"** and **r/ClaudeAI "FrogPop" Unity roguelite (2026)** — both show Claude Code as strong at implementation once a human owns design/balance/art-direction and tests extensively; neither is autonomous end-to-end.
- **Failure modes reported broadly**: "AI art drift" (no seed/style linkage across generations), spaghetti code from context-window limits and missing planner/executor separation, and context drift when `AGENTS.md`/spec files aren't updated alongside the codebase.

## 5. Evidence List

*(★ = >12 months old relative to 2026-09; treat as possibly stale)*

- Dialogic 2 text syntax — https://docs.dialogic.pro/timeline-text-syntax.html (current docs, undated but active project)
- Dialogue Manager format/docs — https://dialogue.nathanhoad.net/ , https://github.com/nathanhoad/godot_dialogue_manager (active, current)
- Yarn Spinner v3 release (2025-05-16) and GDScript alpha (2026-03) — https://docs.yarnspinner.dev/readme/ys3 , https://github.com/YarnSpinnerTool/YarnSpinner-Godot-GDScript
- GodotInk addon, updated 2026-06-08 — https://store.godotengine.org/asset/paulloz/godot-ink/
- LDtk JSON format — https://ldtk.io/docs/game-dev/json-overview/ ; Linux "experimental" build — https://deepnight.itch.io/ldtk
- YATI Tiled importer for Godot 4 — https://godotassetlibrary.com/asset/R7VbaK/yati-yet-another-tiled-importer-for-godot-4 ; Tiled official `.tscn` exporter — https://doc.mapeditor.org/en/stable/manual/export-tscn/
- Godot `TileMapLayer` tile data as `PackedByteArray` — https://docs.godotengine.org/en/4.4/contributing/development/file_formats/tscn.html , https://ziva.sh/blogs/godot-tilemap
- jj has no Git LFS support, tracked as issue #80 (filter/smudge mechanism unimplemented) — https://github.com/jj-vcs/jj/issues/80 , https://docs.jj-vcs.dev/latest/git-compatibility/ ; large-file support only "on the roadmap" — https://docs.jj-vcs.dev/latest/roadmap/
- Git LFS pricing 2026 (10 GiB free Free/Pro, 250 GiB Team/Enterprise; $0.07/GiB storage, $0.0875/GiB bandwidth overage) — https://docs.github.com/articles/about-billing-for-git-large-file-storage
- DVC/git-annex/LFS comparison — https://www.anchorpoint.app/blog/5-alternatives-to-git-lfs-for-game-development ; DVC acquired by lakeFS Nov 2025 — https://en.wikipedia.org/wiki/Data_Version_Control_(software)
- AGENTS.md standard, backed by Google/OpenAI/Cursor/Sourcegraph/Factory (2025-08) — https://agents.md/ , https://www.infoq.com/news/2025/08/agents-md/ ★(borderline, watch for drift)
- GitHub Spec Kit, open-sourced 2025-09 — https://github.com/github/spec-kit , https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- Anthropic, multi-agent research system engineering — https://www.anthropic.com/engineering/multi-agent-research-system ★(2025-06, now >12mo, but still the primary authoritative source)
- Anthropic, multi-agent safety findings (turf wars/sabotage/deception) — https://www.anthropic.com/research/multiagent-systems
- Zach Wills, 8 rules for managing an AI agent swarm (2025-08, revised 2026-07) — https://zachwills.net/i-managed-a-swarm-of-20-ai-agents-for-a-week-here-are-the-8-rules-i-learned/
- Luden.io, AI agents in game development, production lessons (2026-06) — https://blog.luden.io/ai-agents-in-game-development-real-production-lessons-failed-experiments-and-workshop-101-7d71e64685fa
- Steam AI disclosure policy: launched 2024-01; clarified 2026-01 (efficiency-tool exemption); training-data disclosure added 2026-09 — https://www.gamesindustry.biz/valve-slightly-relaxes-ai-disclosure-guidelines-on-steam , https://steamcommunity.com/groups/steamworks/announcements/detail/3862463747997849619
- C2PA content-credentials spec and AI-disclosure assertion — https://c2pa.org/ , https://c2pa.org/a-new-implementation-guide-for-content-credentials/
- Godot headless export / CI actions (`chickensoft-games/setup-godot`, `godot-ci`) — https://docs.godotengine.org/en/4.4/tutorials/editor/command_line_tutorial.html
- Godot 4 / AMD RADV Vulkan issues and Sept-2025 AMD driver fix (25.9.2) — https://www.reddit.com/r/godot/comments/1nkftt5/amd_releases_new_driver_2592_which_fixes_vulkan/ ; OpenGL3/Compatibility fallback documented across multiple Godot issues (2022–2026), e.g. https://github.com/godotengine/godot/issues/110152
- Godot AI MCP servers (Godot AI, Godot MCP Pro, GDAI MCP Server, Ziva, Summer Engine) — https://ziva.sh/blogs/best-ai-tools-for-godot-2026 (aggregation of many primary tool pages, dated April 2026–Sept 2026)
- "Agents are the new GDD," r/gamedev, 2026-05 — https://www.reddit.com/r/gamedev/comments/1tsf6lz/agents_are_the_new_gdd/

## 6. Linux + AMD-iGPU Compatibility

Godot 4's editor and 2D games run natively on Linux; the 890M iGPU (RDNA3.5, Mesa RADV) is a well-supported class of hardware but Vulkan-renderer edge cases (crashes/`VK_ERROR_DEVICE_LOST`, unresponsiveness on close) recur across 2022–2026 GitHub issues, with an AMD driver fix (25.9.2, Sept 2025) resolving some. **Recommendation:** run Godot in the **Compatibility (OpenGL3) renderer**, which is standard practice for 2D projects anyway and sidesteps essentially all reported Vulkan/RADV issues; this has no downside for a stylized 2D puzzle-platformer. LDtk ships an "experimental" Linux AppImage (functional but less polished than Windows/macOS builds) — expect occasional rough edges, no Flatpak yet. Tiled has long-standing official Linux support (Qt-based, AppImage/deb). All named narrative-tool addons are pure GDScript except godot-ink, which needs a .NET-enabled Godot build (works on Linux, but adds a C# toolchain to keep current — a real but manageable maintenance cost, and one more reason Dialogue Manager is the lower-friction default).

## 7. Agent-Operability

Markdown docs, `.dialogue`/`.yarn`/`.ink` text, and LDtk JSON are all directly readable/writable by agents via plain file tools — no GUI required for narrative or level content in the LDtk/Dialogue-Manager path. Godot itself is scriptable headlessly (`--headless --export`) for CI, and a maturing ecosystem of **Godot MCP servers** (Godot AI, Godot MCP Pro, GDAI MCP Server, Ziva) lets agents drive the live editor (scene/node ops, error capture, screenshots) when text-only editing isn't enough — useful for TileMapLayer work specifically, since its tile data isn't hand-editable text. `AGENTS.md` is read natively by Claude Code, Codex, Cursor, and others as of 2025–2026, so one file (plus per-directory overrides) covers the whole swarm without per-tool duplication.

## 8. Licensing, Commercial Rights, Steam AI Disclosure

Dialogue Manager, Dialogic 2, godot-ink/InkGD, and Yarn Spinner are all free/open-source with permissive licenses suitable for commercial shipping (verify each addon's exact license file at integration time — not independently re-verified here). LDtk and Tiled are both free with "pay-what-you-want" or fully free commercial use. Valve's Sept-2026 update requires disclosing AI-generated content that ships and is player-consumed (art, audio, narrative, localization, marketing) but explicitly **exempts** AI coding assistants and internal ideation tools (Jan-2026 clarification) — so Claude Code/Codex usage itself needs no disclosure, only AI-generated shipped assets. The newest requirement (training-data source disclosure) means the provenance manifest should capture, per asset, at minimum: tool + model name/version, prompt/seed where applicable, generation date, and human artist/editor of record — C2PA's `c2pa.ai-disclosure` assertion and `digitalSourceType` field are the emerging standard if you want machine-verifiable, embedded provenance rather than a side-manifest, at the cost of needing tools in the pipeline that actually write C2PA manifests (adoption is uneven outside a few vendors like OpenAI/Adobe).

## 9. Costs

GitHub, jj, Godot, LDtk/Tiled, Dialogue Manager/Yarn Spinner/Dialogic/godot-ink, and DVC are all free for this team's scale. The only live cost driver is binary-asset storage/bandwidth if you do end up needing LFS-equivalent hosting for master files: GitHub LFS metered pricing is $0.07/GiB-month storage and $0.0875/GiB bandwidth beyond a 10 GiB (personal) or 250 GiB (Team/Enterprise) free allowance — moot if you keep master files in an external bucket instead (Backblaze B2/S3-class storage runs roughly $5–6/TB-month, negligible at indie scale). Godot MCP Pro is a one-time paid tool (~$tens, exact price not verified here) if editor-level agent automation beyond text-file editing is wanted.

## 10. Risks / Unknowns

- **jj + external tooling gap**: no first-party guidance exists yet for "jj + DVC" or "jj + git-annex" specifically for game asset workflows — the compatibility claims above are architecturally sound but [INFERENCE], not tested in this repo.
- **LDtk Linux build is labeled "experimental"** by its own maintainer; budget time for editor bugs versus the mature Windows/macOS builds.
- **Yarn Spinner's GDScript runtime is brand-new (alpha, March 2026)** — less battle-tested in Godot than its 10-year Unity history; re-evaluate before committing if narrative scope grows.
- **C2PA adoption is uneven**: most indie-friendly generative tools (Stable Diffusion forks, many LoRA pipelines) do not yet emit C2PA manifests by default, so a manual/side-manifest approach is likely necessary regardless of the standard's existence for the near term.
- **Swarm safety**: Anthropic's own research found multi-agent setups can produce sabotage/deception under competitive or conflicting goals — a governance layer (scope constraints, approval gates on destructive actions, human review of anything touching canon/release) is not optional at scale.
- **Steam AI-disclosure policy is still moving** (three revisions in 12 months as of this writing); the provenance-manifest schema should be designed to be extended, not treated as final.
