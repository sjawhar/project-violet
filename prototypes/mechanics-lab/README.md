<!-- THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md. -->
# Violet mechanics lab

Brainstorm prototype on `proto/mechanics-lab`; never merges. Full contract: `DESIGN.md`.

## Play it

```
/home/sami/.local/share/mise/installs/godot/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64 --path prototypes/mechanics-lab
```

Menu: Up/Down to choose an experiment, Jump (Space/K/gamepad A) to play. In a room: Esc back to
menu, R restart, **Tab compares the bake-off's movement live** (no accel/decel curves, no
coyote/buffer/corner-correction), H/F1/M are presentation-owned no-ops for now (hints overlay,
tuning panel, mute — drop in later from `lab/juice`/`lab/ui`).

## Rooms

| room | experiment(s) | one-line |
|---|---|---|
| `feel-ground` | feel | Run/jump a 3-step staircase, a long gap, a low-ceiling short-hop gap. |
| `feel-air` | feel | Dash a 3-tile pit, then jump + double-jump up through a ceiling gap onto a ledge. |
| `red-wall` | res-window/pick/hold | A red `wall_red` blocks the floor; resonate red to pass through. |
| `red-bridge` | res-window/pick/hold | Red `platform_red` bridges a hazard pit, then a `wall_red`: resonating red *on the bridge* drops you (the 2019 "no!"); resonate only at the wall. |
| `high-wall` | res-window/pick/hold | Double-jump a plain wall, then resonate red through a `wall_red` beyond it. |
| `feel-flow` | feel | A 70-tile flowing run: varied gaps, a short-hop under a low roof, a double-jump vault, a long fall into a run, then a dash-jump-dash chain. |
| `stomp-drop` | stomp | Fall, then hold down to stomp through a cracked floor. |
| `stomp-vault` | stomp | A `platform_yellow` looks solid; stomp before you land so yellow resonance drops you through it. |
| `stomp-chain` | stomp | Double-jump a wall, dash under a low roof, then stomp a yellow platform mid-air to fall to the goal. |
| `blink-gauntlet` | blink | Double-jump a wall, dash under a low roof, blink through a thick wall, then ride the same blue resonance down through a `platform_blue`. |
| `swing-chain` | swing | Double-jump to grab the first anchor, release into the second, then dash the last stretch without ever touching ground. |

## Tests

`bash ci.sh` imports the project, runs every `replays/*.replay.json` via
`tests/replay_runner.tscn`, and for each `must_fail_without` entry re-runs with that ability
disabled and requires failure. Author new replays with a throwaway Python helper that composes
`{"from","to","hold"}`/`{"at","press"}` input segments and iterates against
`res://tests/replay_runner.tscn -- --replay=... --trace` (prints position/velocity/state every tick
to stderr).

## Core/presentation split

`lab/` is core (room loader, `LabPlayer`, abilities, resonance models, scene flow). `lab/juice/`
and `lab/ui/` don't exist yet — they're presentation's drop-in slots. Until then, core's own plain
placeholders stand in: `lab/room_view.gd` (colored-rectangle rooms), `lab/camera_plain.gd`,
`lab/hud_plain.gd`, `lab/menu_plain.gd`, `lab/player_placeholder_body.gd`. Each one's header names
the exact file/class that replaces it. `lab/abilities/ability_registry.gd`'s `REGISTRY` dict is the
extension point for new abilities (stomp/blink/swing): one line + one file, no dispatch changes.
