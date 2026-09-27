# Phase 1 bake-off (THROWAWAY)

> Everything under `docs/bakeoff`, `assets/bakeoff`, `bakeoff/` and the `bakeoff/*` branches exists only to run the Phase 1 bake-off, as do `tools/bakeoff`, `scripts/godot-fetch.sh`, `scripts/capture-*.sh` and `.github/workflows/bakeoff.yml`. Mechanics are undecided ([decision 0009](../decisions/0009-mechanics-undecided.md)); nothing here is canon.

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
- Lane branches are named `bakeoff/<lane>`; they branch from `master` and never merge. Every push to one runs `.github/workflows/bakeoff.yml`: provenance and LFS checks, `bakeoff log-check` on the lane's `LOG.md`, then `game/<lane>/ci.sh`. Its `out/` and `bakeoff/<lane>/reports/` are uploaded as the run's `bakeoff-<lane>` artifact, failed runs included.

## Files

- [mechanic.md](mechanic.md) — the throwaway test mechanic every lane implements identically.
- [greybox-format.md](greybox-format.md) — the `violet-greybox` v1 level JSON format.
- [level01.greybox.json](level01.greybox.json) — the one greybox level every lane builds.
- [replay-format.md](replay-format.md) — the `violet-replay` v1 recorded-input format used for the completability test and captures.
- [protagonist-brief.md](protagonist-brief.md) — the protagonist art brief (THROWAWAY).
- [desert-biome-brief.md](desert-biome-brief.md) — the desert biome art brief (THROWAWAY).
- [judging.md](judging.md) — how Sami scores each lane and the decision rule.
- [lane-log-format.md](lane-log-format.md) — the `bakeoff/<lane>/LOG.md` front matter every lane keeps.
- [lane-log-template.md](lane-log-template.md) — the `LOG.md` a lane copies to `bakeoff/<lane>/LOG.md` and fills in.
- [scores.schema.json](scores.schema.json) — the schema of `docs/bakeoff/scores.json`, the lead's transcription of Sami's judging comment.

`tools/greybox` (a standalone uv project, laid out like `tools/gen` and `tools/provenance`) validates and renders `level01.greybox.json`: `uv run --project tools/greybox greybox check LEVEL` and `greybox render LEVEL --out PNG`.

`tools/bakeoff` (the same layout) runs the lanes' paperwork and the judging, from anywhere inside the repository:

- `uv run --project tools/bakeoff bakeoff log-check bakeoff/<lane>/LOG.md` checks a lane log against the format, including that it names its own lane directory and that lane's direction and engine.
- `bakeoff gallery --pr N` builds `out/review/pr-N/bakeoff.html`: one row per lane with its checks from `bakeoff/<lane>/reports/`, its log totals, its capture and stills (through `tools/preview`'s `preview build`, whose `index.html` sits beside it), its latest CI run and Sami's scores once they exist. Publish it with `uv run --project tools/preview preview publish N`.
- `bakeoff results-md --pr N > docs/bakeoff/results.md` writes the same table without the media.
- `bakeoff decide docs/bakeoff/scores.json` applies the rule in [judging.md](judging.md) and prints the direction, engine and winning lane.

Exit codes: 0 ok, 1 a content problem (a log or the scores), 2 a usage, configuration or I/O error.

Three scripts serve the Godot and Unity lanes, run from the repository root with the mise tools on `PATH`:

- `scripts/godot-fetch.sh game/<lane>` installs Godot 4.7.2's export templates (checksum-verified) and the spine-godot 4.3 GDExtension into `game/<lane>/bin/` (gitignored), and registers the extension in `.godot/extension_list.cfg`: without that, a fresh project's first `godot --headless --import` aborts once the extension is present. Every Godot lane's `ci.sh` runs it before importing.
- `scripts/capture-godot.sh <lane> [ART_TRES]` records the lane's replay with Godot's Movie Maker, and `scripts/capture-unity.sh` runs the U-D player with frame capture. Both write `bakeoff/<lane>/capture/capture.mp4` and `still-{05,20,40,60}.png` only when the capture is 60-90 s at 1920x1080; a rejected one stays in `out/<lane>/capture/` and the last good capture is kept. With `$DISPLAY` empty they render in software under Xvfb (they need the `xvfb` and `mesa-vulkan-drivers` packages).
