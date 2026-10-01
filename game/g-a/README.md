# Lane G-A: Godot 4.7.2 2D, painted world (THROWAWAY)

THROWAWAY: this project exists only to run the Phase 1 bake-off ([docs/bakeoff/README.md](../../docs/bakeoff/README.md)). Mechanics are undecided (decision 0009); nothing here is canon.

- `bash game/g-a/ci.sh` runs every check and writes `bakeoff/g-a/reports/`.
- Play: `godot --path game/g-a` (keys in [mechanic.md](../../docs/bakeoff/mechanic.md#controls)).
- Replay with a trace: `godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace`.
- Art: `bash bakeoff/g-a/gen-art.sh` generates the painted pieces into `art/` (prompts inside), then `bash bakeoff/g-a/edit-art.sh` makes the backdrops repeat; both run from the repository root. `art/lane_art.tres` is the PaintedArt the game and captures use.
- Character: `bakeoff/violet_sprites.gd` reads the painted Violet (violet-sprites v1, [character-rig.md](../../docs/bakeoff/character-rig.md#painted-sprite-sequences-violet-sprites-v1)) and `art/sprite_character_2d.gd` draws it, a body Sprite2D with the scarf Sprite2D over it, each layer's anchor on the player's ground point, showing the frame `bakeoff/character_animator.gd` picks from the player's state. `attach_character` uses it once `assets/bakeoff/protagonist/sprites/violet.sprites.json` and the frames it names (`glow-up/trial-b/frames/*.png` with their sidecars) are copied to `protagonist/`, keeping their relative paths; until then the character is the STAND-IN capsule. A file that is there but does not load stops the game with exit 1 and the error; it never falls back to the STAND-IN. The frames' provenance inputs live at their original paths under `assets/bakeoff/protagonist/` (and `assets/concept/`) so `provenance check` can follow them.
- Sprite reader tests: `godot --headless --path game/g-a res://tests/sprite_test.tscn` (in `ci.sh`): frame timing at boundaries, anchors on the ground point facing either way, the scarf over the body, and malformed files refused (the game exits 1).
- `ci-tools` lists the mise tools the bakeoff workflow installs for this lane.
