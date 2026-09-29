# Violet glow-up rounds (THROWAWAY bake-off process)

Part of the Phase 1 bake-off glow-up round; see [glow-up.md](../../../../docs/bakeoff/glow-up.md). This
workstream improves Violet's painted parts and all seven animations (`idle`, `run`, `jump`, `fall`,
`double_jump`, `dash`, `land`), keeping her the character Sami approved in #19
(`assets/bakeoff/protagonist/concept/violet-turnaround.png`), the same seven animation names and
loop/hold behavior `docs/bakeoff/character-rig.md` defines, soles on the floor on ground frames, and a
tintable (neutral-gray) scarf.

## Fixed layout

Fixed at round 0 and reused byte-for-byte every later round (`shoot.py`), so the critic's comparison is
fair:

- **Reference box** (skeleton space, rig units, root at the feet): `x=-763.6, y=-40.0, width=1316.9,
  height=1434.7` — the union of `spinerig.render.animation_bounds` over all seven animations (120
  samples each), padded 150 rig px left/right, 250 up, and down to at least `y=-40` (the setup box is
  `990 px` crown to sole; this gives generous headroom for bigger secondary motion or a longer scarf in
  later rounds without moving the box).
- **Scale**: `0.22` canvas px per rig unit. **Margin**: `0` (the box's own padding is the margin). Cell
  size: `290×316` px (`spinerig.render.canvas_size(REFERENCE_BOX, 0.22, 0)`).
- **Background**: neutral gray, `#808080`, composited under `spinerig.render.render_frame`'s transparent
  output (it does not touch the character's own parts, so the scarf stays tintable).
- **Frame sampling**, six per row: looping animations (`idle`, `run`) sample `t = i·duration/6` for
  `i = 0..5` (their last keyframe already matches their first, so `t=duration` would repeat `t=0`);
  held animations (`jump`, `fall`, `double_jump`, `dash`, `land`) sample `t = i·duration/5` for
  `i = 0..5`, both endpoints inclusive, so the row shows the held final pose.
- **Row order**: `idle, run, jump, fall, double_jump, dash, land`, one row each, a label column on the
  left.
- **GIFs**: one per animation, every frame at 30 fps, same box/scale/background as the contact sheet.
- **In-game-scale sheet** (added at round 1, from cross-lane feedback that at the lanes' fixed camera
  she reads muddy/unlit, her face is unreadable at ~95-120 px, and the scarf is a thin ~8 px streak):
  `contact-sheet-ingame.png`, the same reference box and frame sampling, but at
  `character-rig.md`'s own scale formula, `(1.6 tiles · 64 px/tile) / height_px`, recomputed from each
  round's own rig height rather than frozen — that formula is what a lane actually applies at runtime,
  and it self-normalizes her to 1.6 tiles regardless of small height_px drift. Backfilled for round 0.
  **Not shown to the critic**: the critic's inputs stay exactly `contact-sheet.png` plus the seven
  GIFs, unchanged since round 0.

Regenerate with `uv run --project tools/spinerig python assets/bakeoff/protagonist/glow-up/shoot.py --rig
assets/bakeoff/protagonist/rig/violet.json --parts assets/bakeoff/protagonist/parts --out
assets/bakeoff/protagonist/glow-up/round-NN`.

## The bar and extra games

Scored against GRIS and Planet of Lana only (official press screenshots:
<https://www.devolverdigital.com/games/gris>, <https://planetoflana.com/>). Two extra games, named for
gaps only, not scored, chosen for character animation in Violet's painted/soft-edged register — one per
candidate technique:

- **Ori and the Blind Forest** (Moon Studios, 2015) — <https://www.orithegame.com/screenshot_category/ori-and-the-blind-forest/> — skeletal/cutout-rigged 2D character animation with fluid secondary motion; the reference for technique A (polished cutout).
- **Hollow Knight** (Team Cherry, 2017) — <https://www.hollowknight.com/> — hand-painted, frame-by-frame 2D character sprites; the reference for technique B (frame-by-frame painted).

## The critic prompt

Verbatim from `glow-up.md`, filled in and reused every round:

> You are judging art for a 2D puzzle-platformer. The bar is GRIS and Planet of Lana. You may open
> these official press screenshots of them: https://www.devolverdigital.com/games/gris,
> https://planetoflana.com/. To name gaps, but not to score, you may also compare against Ori and the
> Blind Forest (https://www.orithegame.com/screenshot_category/ori-and-the-blind-forest/) and Hollow
> Knight (https://www.hollowknight.com/).
>
> {Round 0: Here is one set of screenshots, A: {files}.} {Later rounds: Here are two sets, A: {files}
> and B: {files}. They are in a random order, and nothing about them says which is newer.}
>
> Judge on three axes. visual_quality: how beautiful and finished it looks. character_appeal: how
> appealing and alive the character looks. color_readability: whether the red and green walls and
> platforms, and the character's scarf and silhouette, read at a glance. For a sheet showing only the
> character, color_readability covers the scarf and silhouette alone.
>
> Return: {later rounds: for each axis, A, B or same;} for each set, a score from 1 to 5 on each axis,
> where 5 means as good as GRIS or Planet of Lana; and for each set, the three biggest gaps between it
> and the bar, each concrete enough to act on ("the ground tiles repeat every 4 m", not "needs polish").

Before each call the workstream copies the round's `contact-sheet.png` and seven GIFs to neutral names
(`A-contact.png`, `A-<anim>.gif`, and for later rounds `B-contact.png`, `B-<anim>.gif`) in a scratch
directory outside the repo, assigns the letters with Python's `random` module, and records the mapping
below. The critic is a fresh `astra` subagent each round; its full reply is saved as `round-NN/critic.md`.

**Frozen inputs.** `provenance check` verifies every input's *current* hash, so once a round
overwrites a live shared file (`parts/*.png`, `rig/violet.json[.meta]`, `rig-src/rig.json`), every
earlier round's shot provenance that cited it by that path goes stale. Before overwriting, this
workstream freezes the outgoing content at `<name>.round-NN.<ext>` beside the live file (same
generator metadata as the live file's own record, since it's the same pixels/bytes, just parked at a
path nothing will touch again), then re-points the superseded round's own shot records at the frozen
copy with `provenance record --force`.

## Round table

| Round | Start (UTC) | End (UTC) | What changed | Spend (est.) | Letter map | Axes: new round better / worse | Scores (A / B): visual_quality, character_appeal, color_readability | Gaps (new round) | Kept? |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-09-29T00:40:00Z | 2026-09-29T00:52:00Z | Baseline: the current rig (README.md), unchanged. | $0 | A = round 0 (only set) | — (nothing to compare) | A: 2, 2, 3 (no B) | 1) jump/fall/double_jump read as almost one pose (arms up, one knee bent) — a player can't tell which air-state she's in; 2) no face — every frame is a flat smudge with no eyes/brow, killing "alive" appeal; 3) scribble-texture legs/ankles break the silhouette exactly at the feet, where platforming footing/landing cues need to read cleanest. | kept (round 0 is always kept) |
| 1 | 2026-09-29T01:05:00Z | 2026-09-29T01:35:00Z | Fixed round 0's gap 2 (no face): repainted `head.png` (technique A, cutout) with a bigger, flatter, higher-contrast eye/brow so it survives the fixed render scale — but the prompt also banned the small specular catchlight the original head had, to avoid drifting into anime style. 1st candidate drifted into anime line art/eyelashes/blush and was rejected before commit (not counted as a round of its own). | ~$0.44 est. (2 gpt-image-2 calls, quality high, 1024x1024, one rejected pre-commit) | A = round 0 (kept), B = round 1 (new) | none better; **worse: character_appeal** | A: 3, 3, 3 — B: 3, 2, 3 | (B's own three gaps) 1) same flat-shading/no-rim-light gap as A; 2) same cloth-edge anti-aliasing halo as A; 3) the bigger/bolder eye lost its catchlight and reads "dead"/asleep even in dash and double_jump — critic's own fix: "add a 1-2px highlight and lighten the iris value slightly." | **not kept — reverted.** `parts/head.png`, `rig/violet.json`, `rig/violet.meta.json` restored to round 0's content; round 1's shots and this critique stay as the historical record. |

## Running spend

| Round | Calls | Est. USD | Running total |
|---|---|---|---|
| 0 | 0 gen calls | $0 | $0 |
| 1 | 2 gpt-image-2 calls (quality high, 1024x1024, one rejected) | ~$0.44 est. ($0.22 per call, the rate `docs/bakeoff/shared-costs.md` measured from OpenAI's own reported usage in #28's arm round) | ~$0.44 |

## Stop reason

_Not yet stopped._
