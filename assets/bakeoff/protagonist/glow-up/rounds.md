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
| 2 | 2026-09-29T01:15:00Z | 2026-09-29T01:44:00Z | Retried round 0's gap 2 (no face), materially differently from round 1 per round 1's own critic: recovered round 1's uncommitted successor `gen image` edit call (`--input` the reverted `head.round-01.png` plus `violet-turnaround.png`) that keeps round 1's bigger, flatter, higher-contrast eye/brow shape and size exactly but adds back a small (1–2 px) soft specular catchlight inside the eye and lightens the iris slightly, then trimmed/rescaled it into `head.png` exactly as round 1 did, regenerated the rig, and reshot. | ~$0.22 est. (1 gpt-image-2 call, quality high, 1024x1024) | A = round 2 (new), B = round 0 (kept) | same on all three axes (better on none, worse on none) | A: 3, 2, 3 — B: 3, 2, 3 | (identical for A and B — the critic found the two sets visually indistinguishable, the eye/iris change too subtle to register against GIF re-encoding noise) 1) the face never changes expression across any of the eight poses — the same neutral eye/mouth in every animation, unlike Lana's reactive face or GRIS's pose-driven compensation for a hidden face; 2) hands are blank cone shapes with a single skin-toned point and no fingers/thumb, most visible in the jump/double_jump/dash reach poses; 3) the robe body sits within ~1% luminance of the neutral-gray backdrop (measured 124 vs. 127) and a lighter tan patch on the mid-right skirt cuts across the fabric folds at a hard edge that doesn't follow the drape. | kept (worse on none) — but see Stop reason: this is the second round in a row the critic called better on no axis |
| 3 | 2026-09-29T02:00:00Z | 2026-09-29T02:50:00Z | Fixed round 2's gap 3 (robe body ~1% luminance from the neutral-gray backdrop, plus a hard-edged lighter tan patch on the mid-right skirt) — a different gap from rounds 1-2's retried "no face" gap, per #37's amendment. Repainted `torso.png`, `hips.png` and all four sleeve parts (`arm_back_upper`, `arm_front_upper`, `arm_back_lower`, `arm_front_lower`) via `gen image` edits (`--input` each reverted `*.round-02.png` plus `violet-turnaround.png`) for a noticeably deeper, richer base tone and much stronger painterly value structure (dark cast shadows in every fold, a few highlight ridges, visible cloth-grain), keeping the exact silhouette/crop/palette family. Traced the "tan patch" to `leg_front_upper.png`/`leg_back_upper.png` (the thigh-wrap fabric that shows through the skirt's front slit in raised-leg poses) sitting at a lighter, flatter tone than the surrounding robe; fixed with a per-channel levels match (mean/std of R/G/B) to the newly repainted hips/torso, not a new `gen` call. Regenerated the rig and reshot. | ~$1.98 est. (14 gpt-image-2 calls: 9 charged, 5 OpenAI safety rejections at no charge — see the round table's own call-by-call notes below) | A = round 3 (new), B = round 2 (kept) | better: **color_readability**; same: visual_quality, character_appeal; worse: none. The critic measured about 14-16% of the character's pixels within 8 luminance units of the gray backdrop in round 3, against 24-26% in round 2 | A (round 3): 2, 2, 3 — B (round 2): 2, 2, 2. This critic scored round 2 lower than round 2's own critic did (3, 2, 3); absolute scores move by about a point between critic instances, the blind A/B verdict is the steadier signal | (round 3's own three gaps) 1) about a sixth of the silhouette still sits within 8 luminance units of a neutral gray, in the cloak's deep folds and the leggings: darken the darkest folds a further 15-20 units, or add a cool rim light on the trailing edge; 2) the hood hides the face to a 2-3 px eye dot, identical across idle, land and fall, with no acting; 3) cloak, hood and leggings are one brown-gray hue family separated only by value, with no fabric texture or warm/cool temperature shift. Full reply: [round-03/critic.md](round-03/critic.md) | **kept** (better on color_readability) |

## Running spend

| Round | Calls | Est. USD | Running total |
|---|---|---|---|
| 0 | 0 gen calls | $0 | $0 |
| 1 | 2 gpt-image-2 calls (quality high, 1024x1024, one rejected) | ~$0.44 est. ($0.22 per call, the rate `docs/bakeoff/shared-costs.md` measured from OpenAI's own reported usage in #28's arm round) | ~$0.44 |
| 2 | 1 gpt-image-2 call (quality high, 1024x1024) | ~$0.22 est. | ~$0.66 |
| 3 | 14 gpt-image-2 calls (quality high, 1024x1024): 9 charged (6 kept, 3 off-model/redundant rejected after generation), 5 OpenAI safety rejections (no charge) | ~$1.98 est. | ~$2.64 |

## Stop reason

**Technique A (the cutout rig) stops at round 3 — not the two-rounds-in-a-row condition, but because
the separate technique trial (#38) picked technique B.** #38 blind-compared technique B (frame-by-frame
painted sprites, `run` only) against technique A's round 2 and the critic called B better on
`character_appeal` (4 vs. 2) and `visual_quality` (4 vs. 3); A won only `color_readability` (3 vs. 2),
driven by B's own scarf-rendering artifact in 2 of 8 frames, not a limit of the technique. Per
`glow-up.md`'s rule ("tries at least two animation techniques, and keeps whichever the critic prefers
on `character_appeal`"), technique B is the one Task 12 carries forward — see
[technique-trial.md](technique-trial.md) for the critic's full reasoning. Round 3 is technique A's
**last round regardless of its own result**: a calibration data point for what a fully-committed cutout
pass gets to, per Sami's original ask to "get calibrated on what we could expect if we really, really
tried hard."

**The two-rounds-in-a-row history, corrected under #37's amendment.** Round 1 (vs. kept round 0): worse
on `character_appeal`, better on none. Round 2 retried round 1's exact gap (no face), materially
differently, and the critic called it the same on all three axes — better on none. Under #37's
amendment to `glow-up.md` ("a round whose record row says it retries the previous round's gap, and
that the critic calls better on no axis, leaves the streak where it was... only the first retry of a
gap does this"), round 2's retry does not extend round 1's streak, so the streak stood at 1 after round
2, not 2 — the track was never actually stopped by that condition, and this rounds.md's earlier "stops
here at round 2" wording was wrong under the amendment (correct as of when it was written, since #37
hadn't merged yet).

**Round 3, vs. kept round 2, fixed a different gap** (round 2's gap 3: robe-body luminance/skirt seam,
not round 1-2's retried "no face" gap), so it is not a retry and the amendment's retry exception does
not apply to it. **Round 3's critic called it better on `color_readability` and the same on the other two axes, so round 3 is kept, and technique A ends on an improvement.** Its robe now separates from the backdrop: about 14-16% of its pixels nearly vanish into the gray, against 24-26% in round 2. Its critique is in [round-03/critic.md](round-03/critic.md), recovered by the lead from the critic's transcript after the round-3 agent hit its request budget.


Total spend: ~$2.64 confirmed (17 `gpt-image-2` calls across rounds 1-3: round 1's 2 calls, round 2's 1
call, round 3's 14 calls, 9 of them charged), well under the $40 cap; this is round 3, not round 10; and
there is no wall needing a paid tool or a human's skill — technique A stops here purely because
technique B won the trial.

Round 3's gaps are recorded above, but there is no round 4 for
technique A regardless of what they turn out to be: the workstream now carries technique B forward per
the trial's result. Round 2's untried gaps (the face never changing expression, blank/fingerless hands)
stay untried for technique A; technique B's own three gaps (`technique-trial.md`: the `run` cycle not
cycling, featureless hands, a hard-edged frayed scarf tail) are technique B's problem to fix as it
extends to the other six animations.

**Not done:** technique B's other six animations (four agents are painting them now, per the lead);
`character-rig.md`/`tools/spinerig` needs a new sprite-sequence contract for technique B to ship
(`technique-trial.md`'s "What the lanes would need" section has the shape of it, not yet built); the
review gallery and this PR's final body are not yet built, and depend on technique B's full run across
all seven animations.


