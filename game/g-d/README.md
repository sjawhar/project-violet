# Lane G-D: Godot 4.7.2 3D hybrid (THROWAWAY)

THROWAWAY: this project exists only to run the Phase 1 bake-off ([docs/bakeoff/README.md](../../docs/bakeoff/README.md)). Mechanics are undecided (decision 0009); nothing here is canon.

- `bash game/g-d/ci.sh` runs every check and writes `bakeoff/g-d/reports/`.
- Play: `godot --path game/g-d` (keys in [mechanic.md](../../docs/bakeoff/mechanic.md#controls)).
- Replay with a trace: `godot --headless --fixed-fps 60 --path game/g-d res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace`.
- `bakeoff/{actions,resonance,greybox,replay,resonance_tag,tag_validator}.gd` and `tests/*.gd` are lane G-A's, copied with `jj file show -r bakeoff/g-a game/g-a/<path>` (the tests with `Game2D`/`Node2D` renamed to `Game3D`/`Node3D`). A G-A fix is re-copied the same way.
- The world is 1 m per tile on the z = 0 plane (docs/bakeoff/greybox-format.md); `GreyboxArt3D` draws toon-shaded cubes until the desert kit lands, and the STAND-IN capsule until the protagonist rig is in the project.
- Character: `bakeoff/rig.gd` and `bakeoff/rig_animator.gd` are lane G-A's, copied unchanged the same way; `bakeoff/rig.gd` reads the protagonist rig (the Spine 4.3 JSON subset in [character-rig.md](../../docs/bakeoff/character-rig.md), no Spine runtime) and `art/rig_character_3d.gd` draws it, one shaded Sprite3D per part in the player's XY plane, 1.6 m tall. `attach_character` uses it once `assets/bakeoff/protagonist/` (`rig/violet.json`, `rig/violet.meta.json`, `parts/*.png` with their sidecars) is copied to `protagonist/`; a rig that is there but does not load stops the game with exit 1 and the error, never falling back to the STAND-IN. Facing left mirrors each sprite rather than the root (character-rig.md's negative root x scale turns the shaded sprites black).
- Rig reader tests: `godot --headless --path game/g-d res://tests/rig_test.tscn` (in `ci.sh`; `tests/rig_test.gd` and `tests/rig/` are G-A's). `bash game/g-d/tests/rig/make-fixture.sh` regenerates their fixture (set `SPINERIG=` to a `tools/spinerig` that has `render.py`).
- `ci-tools` lists the mise tools the bakeoff workflow installs for this lane.
