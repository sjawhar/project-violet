# Research, September 2026

Research gathered for the Violet studio restart. The design built on it is in [`docs/superpowers/specs/2026-09-26-violet-studio-design.md`](../../superpowers/specs/2026-09-26-violet-studio-design.md).

| Report | Question |
|---|---|
| [engine.md](engine.md) | Which engine suits development led by AI agents on Linux (first pass) |
| [engine-steelman.md](engine-steelman.md) | Independent re-evaluation that makes the strongest case for Unity and Unreal against Godot |
| [engine-2.5d.md](engine-2.5d.md) | How well agents can operate Unity and Godot for a 2.5D side-scroller on this machine |
| [playtest-qa.md](playtest-qa.md) | Automated and agent-driven playtesting and QA |
| [art-pipeline.md](art-pipeline.md) | AI-assisted 2D art tools, styles, and licensing |
| [art-feasibility.md](art-feasibility.md) | Whether agents can deliver 2.5D, painted 2D, or flat vector art today |
| [audio.md](audio.md) | Music, sound-effect, and voice pipelines |
| [swarm-workflow.md](swarm-workflow.md) | Repo layout and operating model for a multi-agent studio |
| [market-design.md](market-design.md) | Comparable games, design lessons, and the 2026 market |
| [archive-digest.md](archive-digest.md) | Digest of the 2019 design archive and the Unity prototype |
| [archive-supplement.md](archive-supplement.md) | The 2017–18 space version ("Resonate") and a comparison of the two conceptions |

## Corrections found during review

Each report is kept as written. These claims in them were checked against primary sources and are wrong or overstated:

- **Godot version** (engine.md): recommends Godot 4.5.x with 4.6 "in RC". The current stable release is **4.7.2** (2026-08-18), per the GitHub releases API.
- **Git LFS under jj** (swarm-workflow.md): says Git LFS cannot work with jj. Upstream jj issue #80 is still open, but the jj build used here includes gitattributes filter drivers (jj-vcs/jj#8719), and git-lfs clean/smudge are configured. jj runs no git hooks, so LFS objects are pushed explicitly.
- **Steam "training data disclosure"** (swarm-workflow.md): claims a September 2026 rule requiring disclosure of training data. The Steamworks Content Survey page has no such rule. It covers Pre-Generated and Live-Generated player-facing AI content, and treats efficiency tools as out of scope.
- **Unity 7 date and several Unity claims** (engine.md): corrected in engine-steelman.md §8. The main ones:
  - Unity 7 was announced 2026-07-21; its beta is due December 2026.
  - Unity scenes are text YAML, not binary.
  - W4 Games console pricing is public.
  - Unity's Linux editor became official in 2019.1, not 2015.
- **Unity terms of service** (engine-2.5d.md): verified on unity.com. Section 17.2, updated 2026-06-30, says AI agents and MCP clients or servers "may only interact with the platform through a framework operated or designated by Unity."
- **Godot shader stutter** (engine-steelman.md vs engine-2.5d.md): the reports conflict. The Godot 4.7 docs settle it: 3D pipelines are precompiled at load time since 4.4, but "the engine does not currently feature precompilation for 2D elements."
- **`spine-animation-ai`** (art-feasibility.md): described as "MIT-adjacent" in one place. Its LICENSE is **PolyForm Noncommercial 1.0.0**, so the tool cannot be used in a commercial pipeline; its technique can be reimplemented.
- **`godot-ldtk-importer`**: last pushed 2025-02-02, so the importer is effectively unmaintained.
