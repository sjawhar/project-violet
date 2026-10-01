# Violet mechanics lab — design contract (THROWAWAY prototype)

## Why this exists
Sami (project owner), 2026-10-01: "I'm more interested in us getting the mechanics really good and making something that's actually fun to play." Decision 0009: mechanics, abilities and feel are designed in a brainstorm WITH Sami; nothing here is canon. This lab is brainstorm material: short playable rooms, each answering one question, that Sami plays in a browser and reacts to. Every file header says THROWAWAY. It lives on branch `proto/mechanics-lab` in repo sjawhar/project-violet and never merges (same convention as the `bakeoff/<lane>` branches).

Background reading (read-only, in any workspace): `docs/bakeoff/mechanic.md` (the bake-off's throwaway test mechanic), `docs/research/2026-09/archive-digest.md` §2 "Mechanics" and §7B (the 2019 Unity prototype's `Resonator`), `docs/archive/2017-2019/scarlet-wasteland/scarlet-game-design-document.md` "# Mechanics", `docs/research/2026-09/market-design.md` "Movement-ability design lessons".

The 2019 design in one paragraph: each color is an ability (red = dash, green = double jump, yellow = stomp, blue = undecided: swing or teleport were the options; the 2019 code bound blue to a ground slam). After using an ability, the world "resonates" that color for a short time (1.5 s in the 2019 code): same-color walls become passable, same-color platforms vanish ("a red wall can be walked through (yay!) but a red platform can't be landed on (no!)"). The bake-off instead uses a persistent active color switched with Q. These are different designs; the lab lets Sami feel both, plus a third.

## Project
- Path: `prototypes/mechanics-lab/` (Godot 4.7.2; binary `/home/sami/.local/share/mise/installs/godot/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64`).
- `project.godot`: renderer `gl_compatibility` (required for the web build); viewport 1920x1080; stretch mode `canvas_items`, aspect `expand`; physics 60 ticks/s; `physics/common/physics_interpolation=true` (smooth on Sami's 165 Hz monitor; call `reset_physics_interpolation()` after teleports/respawns).
- Tile = 64 px. 1920x1080 shows 30 x 16.9 tiles.
- Directory layout:
  - `lab/` core gameplay (owner: core agent)
  - `lab/juice/` and `lab/ui/` presentation components (owner: presentation agent)
  - `rooms/<id>.room.json`, `experiments.json`
  - `tests/replay_runner.gd|.tscn`, `replays/<experiment>--<room>.replay.json`, `ci.sh`
  - `export_presets.cfg` (Web + Linux), `README.md`

## Controls (InputMap; keyboard AND gamepad from day one)
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

## Physics profile
`lab/physics_profile.gd`: `class_name PhysicsProfile extends Resource`. Units are tiles, seconds, ticks. It declares `const TUNABLES := [{name, label, min, max, step, unit}, ...]` listing every numeric field below, so the tuning panel can be generic. `func to_dict()` / `func apply_dict(d)` round-trip all fields.

Fields and the two presets (`lab/profiles/bakeoff.tres` reproduces `docs/bakeoff/mechanic.md` exactly; `lab/profiles/tuned.tres` is the "feels good" baseline):

| field | bakeoff | tuned | meaning |
|---|---|---|---|
| run_speed | 8 | 9 | t/s |
| ground_accel_time | 0 | 0.09 | s from 0 to run_speed (0 = instant) |
| ground_decel_time | 0 | 0.06 | s from run_speed to 0 |
| air_accel_mult | 1 | 0.7 | |
| turn_accel_mult | 1 | 1.6 | accel multiplier when input opposes velocity |
| jump_height | 3.0 | 3.25 | t (apex height of a held ground jump) |
| jump_time_to_apex | 0.3875 | 0.38 | s (bakeoff: 15.5 t/s at 40 t/s² gives 0.3875 s, apex 3.0 t) |
| min_jump_height | 3.0 | 1.1 | t; releasing jump early cuts upward velocity so the jump peaks near this (equal to jump_height = no variable jump) |
| fall_gravity_mult | 1 | 1.7 | gravity multiplier while falling |
| apex_hang_speed | 0 | 2.5 | t/s; while |vy| < this and jump held, gravity × apex_hang_mult |
| apex_hang_mult | 1 | 0.5 | |
| max_fall_speed | 1000 | 18 | t/s |
| fast_fall_speed | 1000 | 26 | t/s, holding down while falling |
| coyote_ticks | 0 | 6 | |
| buffer_ticks | 0 | 7 | |
| corner_correct_px | 0 | 14 | ceiling-corner and ledge-lip nudge |
| box_w | 0.8 | 0.7 | t |
| box_h | 1.6 | 1.45 | t |
| dash_speed | 30 | 24 | t/s |
| dash_ticks | 12 | 10 | |
| dash_freeze_ticks | 0 | 3 | game freezes this many ticks at dash start (hitstop) |
| dash_end_speed | 0 | 9 | t/s horizontal speed kept when the dash ends |
| dash_eight_way | 0 | 0 | 0 = facing direction only (2019 + bakeoff); 1 = 8-way from held direction |
| double_jump_height | 3.0 | 2.4 | t |
| wall_jump | 0 | 0 | 1 enables wall slide + wall jump (an open design question, off by default) |
| wall_slide_speed | 0 | 5 | t/s |
| wall_jump_push | 0 | 9 | t/s horizontal |
| resonance_ticks | 90 | 90 | ability-triggered resonance window (2019 code: 1.5 s) |
| breath_ticks | 120 | 120 | max hold for the hold-to-resonate model |

Gravity and jump velocity derive from jump_height and jump_time_to_apex (g = 2h/t², v = 2h/t). The bakeoff preset must reproduce mechanic.md: gravity 40 t/s², jump 15.5 t/s, run 8 t/s, dash 30 t/s × 12 ticks with gravity suspended, one air dash per airborne period, box 0.8 × 1.6.

## Collision and world
- Custom axis-separated AABB movement against the tile grid (no Godot physics bodies): move X then Y in sub-steps of at most 8 px; the grid answers `is_solid(cell)` using the current resonance state. Deterministic, and replays depend on it.
- Room format `violet-lab-room` v1: same shape as `docs/bakeoff/greybox-format.md` (`format`, `version`, `tile_size_px` = 64, `legend`, `rows`) plus `"title"` and `"hint"` strings. Kinds: `empty solid start goal hazard wall_<c> platform_<c> orb_<c>` for c in red, green, yellow, blue, plus `cracked` (solid until stomped through) and `anchor` (swing point, not solid).
- Wall and platform of a color share one rule: while that color resonates, they have no collision. They differ only in how they are drawn and used (walls block you, so resonance helps; platforms hold you, so resonance hurts).
- If resonance ends while the player overlaps a now-solid cell, push the player to the nearest free position within 1 tile (prefer up, then sideways); if none, the player dies.
- Hazard contact → death → respawn at the room start after a 0.35 s fade; colors acquired in that room are kept. A per-room death counter is shown.
- Orbs: touching acquires the color (only relevant where the experiment says colors start unacquired; most rooms start with their colors acquired via `experiments.json`).
- Goal → next room of the experiment; after the last room, back to the menu with the experiment marked done.

## Player API (core implements; presentation consumes)
`lab/player.gd`, `class_name LabPlayer extends Node2D`:
- Signals: `jumped(kind: StringName)` with kind in ground, coyote, buffered, double, wall; `landed(impact_speed: float)` (px/s); `dash_started(dir: Vector2)`; `dash_ended()`; `ability_used(ability: StringName, color: StringName)`; `resonance_changed(colors: Array)`; `died()`; `respawned()`; `reached_goal()`; `blinked(from: Vector2, to: Vector2)`; `stomp_impact()`; `swing_attached(anchor: Vector2)`; `swing_released()`.
- Properties: `velocity: Vector2` (px/s), `facing: int` (-1 or 1), `on_floor: bool`, `box_size_px: Vector2`, `neck_offset: Vector2` (local, where a scarf attaches), `state: StringName` (idle, run, jump, fall, dash, stomp, swing, dead), `visual_root: Node2D` (presentation adds its body drawing here; core draws a plain placeholder rectangle until then).
- Freeze: `freeze(ticks)` pauses gameplay simulation for N ticks (dash hitstop uses it).

## Resonance models
`lab/resonance/resonance_model.gd`, `class_name ResonanceModel extends RefCounted`:
`setup(player, profile)`, `on_ability_used(color)`, `on_switch_pressed()`, `on_resonate_held(held: bool)`, `tick()`, `is_resonating(color) -> bool`, `can_use(color) -> bool`, `hud_state() -> Dictionary` (keys: `model`, `colors` resonating, `selected`, `timer_frac` 0..1 or -1, `breath_frac` 0..1 or -1).
- `none` (feel experiment): nothing resonates; abilities usable.
- `ability_window` — label "Ability triggers resonance (2019 design)": abilities always usable once acquired; using one makes its color resonate for `resonance_ticks` from that tick (so a dash into a red wall passes through it); a new color replaces the old one.
- `pick_color` — label "Choose your color (bake-off)": `switch` cycles the acquired colors; the selected color always resonates; only its ability is usable.
- `hold_breath` — label "Hold to resonate": abilities always usable; `switch` cycles the selected color; holding `resonate` makes the selected color resonate, draining a breath meter of `breath_ticks`; breath refills at 2x speed when not held.

## Abilities
`lab/abilities/ability.gd` base: `color`, `try_start(player, input) -> bool`, `physics_tick(player) -> bool` (true while it owns movement), `on_landed()`.
- dash (red, `dash`): see profile; one air dash per airborne period; gravity suspended.
- double_jump (green, `jump` in the air outside coyote time): one per airborne period.
- stomp (yellow, press `down` in the air): vertical 30 t/s straight down, horizontal 0; breaks `cracked` cells it hits and keeps falling; small screen shake on impact.
- blink (blue, `ability`): teleports up to 3.5 t in the held direction (8-way; default facing), passing through geometry if a free spot exists along the line (take the farthest free spot); 3-tick freeze; one per airborne period.
- swing (blue, hold `ability` within 4.5 t of an `anchor`): rope attach, pendulum with fixed length, left/right pumps; release keeps velocity plus 10%; resets on landing.

## Experiments (`experiments.json`)
`[{id, title, question, model, profile, abilities: [...], acquired: [...], rooms: [room ids]}]`, shown in this order on the menu with the question under each title.
1. `feel` — "Movement feel" — "Does this feel right as the baseline? Tab compares with the bake-off's movement; F1 tunes it live." model none, profile tuned, abilities dash, double_jump. Rooms: a run-and-jump course with gaps, stairs, a low ceiling with corners (corner correction), a jump that needs short and long hops (variable height), a dash gap, a double-jump shaft.
2. `res-window`, 3. `res-pick`, 4. `res-hold` — the three resonance models on the SAME three rooms: `red-wall` (dash/resonate through red walls), `red-bridge` (red platforms over hazards followed by a red wall: resonating on the bridge drops you), `high-wall` (green double jump over a high wall, then red through a red wall mid-air). Each room must be solvable under all three models; each model×room has its own replay.
5. `stomp`, 6. `blink`, 7. `swing` — candidate third/fourth abilities, under `ability_window`: two rooms each (added in wave 2).
8. `archive-puzzle` — the GDD's own example, under `ability_window` and `pick_color`: "shift to green to double jump over a high wall, then shift to red to dash mid-air through a red wall/opening, and finally shift to yellow before landing to stomp through a weak wooden floor" (wave 2).

## Presentation (presentation agent; drop-in)
- Palette: background #1F2430; solid #3A4150 with a #5A6375 top edge; red #E5553F, green #4CC27A, yellow #F2C94C, blue #4A90E2, neutral #9AA0A6. Walls drawn with a hatch pattern, platforms as solid ledges; each color also has a distinct pattern for colorblind readability. A resonating color's geometry turns into a faint dashed ghost outline. Unacquired colors draw grayscale.
- Player body: a rounded capsule (#E8E3D8) with a face mark showing facing; squash and stretch on jump/land/dash; a verlet scarf from `neck_offset` that trails with velocity and shows the resonating color (neutral when none).
- Particles (CPUParticles2D only; the web build has no compute): run dust, jump puff, landing dust scaled by impact, dash afterimages, stomp debris, blink trail.
- Camera: follow with facing lookahead (~2 t), vertical deadzone, clamped to the room, `shake(strength_px, duration_s)`.
- Sound: procedurally synthesized (AudioStreamWAV built at startup, no audio files): jump, double_jump, land_soft, land_hard, dash, resonate_on, resonate_off, pass_through, death, goal, orb, stomp, blink, swing_attach, ui_move, ui_select. Mute with M.
- UI: menu (keyboard/gamepad/mouse), room title card (title + hint, 1.5 s), HUD (experiment, model label, profile name, deaths, room time, resonance indicator: window ring/timer, selected-color swatch, breath bar), control hints overlay (H), tuning panel (F1; generic over `PhysicsProfile.TUNABLES`; buttons "Tuned", "Bake-off", "Copy settings" → `DisplayServer.clipboard_set(JSON)`).
- Component interfaces: `lab/juice/player_juice.gd` (`class_name PlayerJuice extends Node2D`, `bind(player: LabPlayer)`), `lab/juice/scarf.gd` (`class_name Scarf extends Node2D`, `reset(anchor)`, `step(anchor, velocity, delta)`, `set_resonance_color(c)`), `lab/juice/camera_rig.gd` (`class_name CameraRig extends Camera2D`, `follow(target)`, `set_room_rect(r)`, `shake(strength_px, duration_s)`, `snap()`), autoload `Sfx` (`lab/juice/sfx.gd`, `play(name: StringName, volume_db := 0.0)`), `lab/ui/tuning_panel.gd` (`class_name TuningPanel extends CanvasLayer`, `bind(profile: PhysicsProfile)`, signal `changed`), `lab/ui/hud.gd` (`class_name LabHud extends CanvasLayer`, `show_room(experiment: Dictionary, room: Dictionary)`, `update_state(player: LabPlayer, model_state: Dictionary, deaths: int, time_s: float)`), `lab/ui/menu.gd` (`class_name LabMenu extends Control`, `show_experiments(list: Array, done: Dictionary)`, signal `chosen(experiment_id)`).
- Juice randomness uses its own seeded RandomNumberGenerator and never touches gameplay state.

## Tests
- `tests/replay_runner.tscn`: `godot --headless --fixed-fps 60 --path prototypes/mechanics-lab res://tests/replay_runner.tscn -- --replay=res://replays/<id>.replay.json [--disable=dash,double_jump,stomp,blink,swing]`. Exit 0 iff the goal is reached by `expect.goal_by_tick` with no death; last stdout line is a JSON report.
- Replay format `violet-lab-replay` v1: shape of `docs/bakeoff/replay-format.md` (`tick_hz`, `inputs` with hold/press segments, `expect.goal_by_tick`) plus `experiment`, `room`, `profile`, and `must_fail_without: [ability...]`. Actions: left right up down jump dash ability switch resonate.
- `ci.sh`: import, run every replay, and for each `must_fail_without` entry re-run with that ability disabled and require failure. Exit non-zero on any problem.

## Exports
- Web: single-threaded (`variant/thread_support=false`) so it runs on GitHub Pages without special headers; `out/mechanics-lab/web/index.html`.
- Linux x86_64: `out/mechanics-lab/linux/violet-mechanics-lab.x86_64`.
- Published to `https://sjawhar.github.io/project-violet/review/pr-0-prelim/mechanics-lab/` (the same pr-0-prelim area as the glow-up gallery): a page with what to try, the play link, a Linux download, and per-experiment questions.
