# Lane G-A: Godot 4.7.2 2D, painted world (THROWAWAY)

THROWAWAY: this project exists only to run the Phase 1 bake-off ([docs/bakeoff/README.md](../../docs/bakeoff/README.md)). Mechanics are undecided (decision 0009); nothing here is canon.

- `bash game/g-a/ci.sh` runs every check and writes `bakeoff/g-a/reports/`.
- Play: `godot --path game/g-a` (keys in [mechanic.md](../../docs/bakeoff/mechanic.md#controls)).
- Replay with a trace: `godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace`.
- Art: `bash bakeoff/g-a/gen-art.sh` generates the painted pieces into `art/` (prompts inside), then `bash bakeoff/g-a/edit-art.sh` keys out the magenta backgrounds and makes the backdrops repeat; both run from the repository root. `art/lane_art.tres` is the PaintedArt the game and captures use.
- `ci-tools` lists the mise tools the bakeoff workflow installs for this lane.
