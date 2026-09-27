# Phase 1 bake-off (THROWAWAY)

> Everything under `docs/bakeoff`, `assets/bakeoff`, `bakeoff/` and the `bakeoff/*` branches exists only to run the Phase 1 bake-off. Mechanics are undecided ([decision 0009](../decisions/0009-mechanics-undecided.md)); nothing here is canon.

The bake-off runs five lanes of the same throwaway slice — one greybox level, one test mechanic, one protagonist and biome brief — through five engine/art combinations, then Sami scores the results and the next decision record picks the stack. Plan: `docs/superpowers/plans/2026-09-27-phase-1-bake-off.md`.

## Lanes

| Lane | Engine | World |
|---|---|---|
| G-A | Godot 2D | Painted world with parallax layers |
| G-D | Godot 3D | AI-generated 3D kit, painterly or toon shading, real colored lights |
| U-D | Unity 6.3 URP, official MCP only | Same as G-D |
| G-C | Godot 2D | Recraft SVG kit; environment only |
| Control | Blender | Full 3D protagonist |

## Directory conventions

- `docs/bakeoff/` — the shared inputs every lane consumes: this README, the throwaway mechanic, the greybox level and its format, the replay format, the protagonist and desert-biome briefs, the judging sheet, and the lane-log format. All files here are read-only inputs to every lane; nothing here is lane-specific.
- `game/<lane>/` — each lane's engine project (created when its lane task starts), holding its own copy of `level01.greybox.json` (unchanged; each lane's `ci.sh` runs `cmp` against the `docs/bakeoff` copy) and its `ci.sh`.
- `bakeoff/<lane>/` — each lane's evidence: `LOG.md` (format in [lane-log-format.md](lane-log-format.md)), `replays/*.replay.json` (format in [replay-format.md](replay-format.md); Godot lanes also keep a copy under `game/<lane>/replays/` because `res://` cannot leave the project), `reports/` (CI-readable results), `capture/capture.mp4` + `still-*.png` (Git LFS).
- `assets/bakeoff/` — shared generated assets (the Spine protagonist rig, the 3D desert kit) built once and used by every lane that needs them.
- Lane branches are named `bakeoff/<lane>`; they branch from `master` and never merge.

## Files

- [mechanic.md](mechanic.md) — the throwaway test mechanic every lane implements identically.
- [greybox-format.md](greybox-format.md) — the `violet-greybox` v1 level JSON format.
- [level01.greybox.json](level01.greybox.json) — the one greybox level every lane builds.
- [replay-format.md](replay-format.md) — the `violet-replay` v1 recorded-input format used for the completability test and captures.
- [protagonist-brief.md](protagonist-brief.md) — the protagonist art brief (THROWAWAY).
- [desert-biome-brief.md](desert-biome-brief.md) — the desert biome art brief (THROWAWAY).
- [judging.md](judging.md) — how Sami scores each lane and the decision rule.
- [lane-log-format.md](lane-log-format.md) — the `bakeoff/<lane>/LOG.md` front matter every lane keeps.

`tools/greybox` (a standalone uv project, laid out like `tools/gen` and `tools/provenance`) validates and renders `level01.greybox.json`: `uv run --project tools/greybox greybox check LEVEL` and `greybox render LEVEL --out PNG`.
