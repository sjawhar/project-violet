<!-- THROWAWAY: Violet mechanics lab prototype. Not canon; see DESIGN.md. -->
# Violet mechanics lab

Brainstorm prototype on `proto/mechanics-lab`; never merges. Full contract: `DESIGN.md`.

## Play it

```
/home/sami/.local/share/mise/installs/godot/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64 --path prototypes/mechanics-lab
```

Menu: the chapter and wall-jump trial listed first, then the nine round-1 experiments under a
"Round 1 experiments" heading, Up/Down (or stick/mouse) to choose, Enter/Space/gamepad A
to play. In a room: Esc back to menu, R restart, **Tab compares the bake-off's movement live**
(no accel/decel curves, no coyote/buffer/corner-correction) with a brief toast naming the
profile, H toggles the control-hints overlay, F1 opens the live tuning panel, M mutes.

## How to play

| action | keyboard | gamepad |
|---|---|---|
| left/right/up/down | A/D/W/S and arrows | left stick + d-pad |
| jump | Space, K | A (bottom) |
| dash | Shift, J | X (left) |
| ability | L, C | B (right) |
| switch | Q, I | Y (top) |
| resonate (hold) | E, O | RB |
| restart | R | Back/Select |
| menu | Esc | Start |
| compare (profile toggle) | Tab | LB |
| tune (panel) | F1 | — |
| hints | H | — |
| mute | M | — |

The HUD's top-left shows the active resonance model (large) plus profile/state/deaths/time; the
ring/swatch/bar below it mirrors whichever model is active. A color resonating also tints the
whole screen faintly at the edges — a glance anywhere on screen, not just at the HUD, tells you
something is resonating.

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
| `ch-01-warmup` … `ch-10-finale` | chapter | The linear chapter route: warm-up, then each color's teach room (orb + one obstacle), a recombine room, through to `ch-10-finale` (double jump, swing chain, dash, stomp in one longer sequence). Orbs and unacquired-color geometry start grayscale per `DESIGN.md`'s round-2 reveal. |
| `ch-side-red` / `ch-side-rg` / `ch-side-ryg` / `ch-side-quad` | chapter | Optional harder side rooms (amber diamond exit) off `ch-02`/`ch-04`/`ch-06`/`ch-09`: the same abilities already taught, chained tighter, rejoining the main route one room later. |

## Tests

`bash ci.sh` imports the project, runs every `replays/*.replay.json` via
`tests/replay_runner.tscn`, and for each `must_fail_without` entry re-runs with that ability
disabled and requires failure. Author new replays with a throwaway Python helper that composes
`{"from","to","hold"}`/`{"at","press"}` input segments and iterates against
`res://tests/replay_runner.tscn -- --replay=... --trace` (prints position/velocity/state every tick
to stderr).

## Core/presentation split

`lab/` is core (room loader, `LabPlayer`, abilities, resonance models, scene flow). `lab/juice/`
(`player_juice.gd`, `scarf.gd`, `camera_rig.gd`, `sfx.gd`) and `lab/ui/` (`menu.gd`, `hud.gd`,
`tuning_panel.gd`) are presentation's drop-in replacements for core's plain placeholders, already
wired in `lab/main.gd`/`main.tscn`. `lab/room_view.gd` (colored-rectangle rooms) is the one
placeholder still standing in for real per-tile art. `lab/abilities/ability_registry.gd`'s
`REGISTRY` dict is the extension point for new abilities (stomp/blink/swing): one line + one
file, no dispatch changes.

## Publish the review page

From the repository root, with the GitHub App routing set (see AGENTS.md):

```
bash prototypes/mechanics-lab/export.sh prototypes/mechanics-lab out/mechanics-lab
python3 prototypes/mechanics-lab/build_site.py prototypes/mechanics-lab out/mechanics-lab out/mechanics-lab-site --issue 41 --commit "$(jj log --no-graph -r @- -T commit_id)"
bash prototypes/mechanics-lab/publish.sh out/mechanics-lab-site --dry-run   # then without --dry-run
```

It goes live at https://sjawhar.github.io/project-violet/review/pr-0-prelim/mechanics-lab/ (the play link, a Linux zip, the experiment list). `publish.sh` replaces only `review/pr-0-prelim/mechanics-lab/` on `gh-pages`.
