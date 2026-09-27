# Lane G-D: Godot 4.7.2 3D hybrid (THROWAWAY)

THROWAWAY: this project exists only to run the Phase 1 bake-off ([docs/bakeoff/README.md](../../docs/bakeoff/README.md)). Mechanics are undecided (decision 0009); nothing here is canon.

- `bash game/g-d/ci.sh` runs every check and writes `bakeoff/g-d/reports/`.
- Play: `godot --path game/g-d` (keys in [mechanic.md](../../docs/bakeoff/mechanic.md#controls)).
- Replay with a trace: `godot --headless --fixed-fps 60 --path game/g-d res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace`.
- `bakeoff/{actions,resonance,greybox,replay,resonance_tag,tag_validator}.gd` and `tests/*.gd` are lane G-A's, copied with `jj file show -r bakeoff/g-a game/g-a/<path>` (the tests with `Game2D`/`Node2D` renamed to `Game3D`/`Node3D`). A G-A fix is re-copied the same way.
- The world is 1 m per tile on the z = 0 plane (docs/bakeoff/greybox-format.md); `GreyboxArt3D` draws toon-shaded cubes and a STAND-IN capsule until the desert kit and the Spine rig land.
- `ci-tools` lists the mise tools the bakeoff workflow installs for this lane.
