# Lane G-A: Godot 4.7.2 2D, painted world (THROWAWAY)

THROWAWAY: this project exists only to run the Phase 1 bake-off ([docs/bakeoff/README.md](../../docs/bakeoff/README.md)). Mechanics are undecided (decision 0009); nothing here is canon.

- `bash game/g-a/ci.sh` runs every check and writes `bakeoff/g-a/reports/`.
- Play: `godot --path game/g-a` (keys in [mechanic.md](../../docs/bakeoff/mechanic.md#controls)).
- Replay with a trace: `godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace`.
- Art: `bash bakeoff/g-a/gen-art.sh` generates the painted pieces into `art/` (prompts inside), then `bash bakeoff/g-a/edit-art.sh` makes the backdrops repeat; both run from the repository root. `art/lane_art.tres` is the PaintedArt the game and captures use.
- Character: `bakeoff/rig.gd` reads the protagonist rig (the Spine 4.3 JSON subset in [character-rig.md](../../docs/bakeoff/character-rig.md), no Spine runtime) and `art/rig_character_2d.gd` draws it, one Sprite2D per part, with the animation `bakeoff/rig_animator.gd` picks from the player's state. `attach_character` uses it once `protagonist/violet.rig.json`, its `violet.rig.meta.json` and its part PNGs (`skeleton.images`) are in the project; until then the character is the STAND-IN capsule.
- Rig reader tests: `godot --headless --path game/g-a res://tests/rig_test.tscn` (in `ci.sh`). `bash game/g-a/tests/rig/make-fixture.sh` regenerates their fixture with `spinerig generate` and `spinerig render`'s own code (set `SPINERIG=` to a `tools/spinerig` that has `render.py`).
- `ci-tools` lists the mise tools the bakeoff workflow installs for this lane.
