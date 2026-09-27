# `violet-replay` v1 (THROWAWAY bake-off replay format)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). Every lane's automated completability test and capture is a recorded input set against [`level01.greybox.json`](level01.greybox.json) in this format.

## Shape

```json
{
  "format": "violet-replay",
  "version": 1,
  "tick_hz": 60,
  "level": "<path inside the lane project>",
  "inputs": [
    {"from": 0, "to": 59, "hold": ["right"]},
    {"at": 60, "press": ["jump"]}
  ],
  "asserts": [
    {"cell": [33, 8], "active_color": "red", "passable": "wall_red"}
  ],
  "expect": {"goal_by_tick": 900}
}
```

## Fields

- `tick_hz`: always `60` (matches the mechanic's fixed tick rate).
- `level`: the level file's path inside the lane's own project (each lane copies `level01.greybox.json` unchanged).
- `inputs`: a list of segments, each either `{"from": T1, "to": T2, "hold": [action...]}` (inclusive tick range) or `{"at": T, "press": [action...]}` (single tick). Actions: `left right jump dash switch`.
  - A tick's pressed set is the union of every segment covering it.
  - The runner presses an action on the first tick it appears and releases it on the first tick it is absent, so two `press` entries on consecutive ticks merge into one hold; leave a gap tick between two separate presses of the same action.
- `asserts`: a list of `{"cell": [col, row], "active_color": "red"|"green"|"", "passable": "<tagged kind>"}`. An assert fires the first time the player's feet cell equals `cell`; at that tick `active_color` must match, and `passable` names a tagged legend kind; at that tick every tagged body of that kind's color (wall and platform alike) must have collision disabled, and every tagged body of the other color must be enabled. This follows [mechanic.md](mechanic.md): the active color's tagged geometry has no collision. An assert that never fires is a failure.
- `expect.goal_by_tick`: the run passes when the goal is reached by this tick with no hazard touch and no failed assert.

## Runner flags

- `--disable=dash` or `--disable=double_jump` makes the named ability a no-op, so a lane can prove its replay genuinely depends on the mechanic (a replay that still reaches the goal with the ability disabled is not testing what it claims to).
- In capture mode the runner keeps going to the last input tick (pad idle segments so captures reach 60–90 s), instead of stopping at `goal_by_tick`.
