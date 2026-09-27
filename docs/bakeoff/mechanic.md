# Bake-off test mechanic (THROWAWAY)

This mechanic exists only to give every bake-off lane the same measurable slice to build. Mechanics, abilities, and feel are undecided ([decision 0009](../decisions/0009-mechanics-undecided.md)); nothing here is promoted to canon. See [README.md](README.md).

## Colors

- Colors: `red`, `green`. Neutral geometry is always solid.
- Touching an orb acquires its color and makes it **active**. `Q` cycles the active color through the acquired ones. Active is `""` until the first orb.

## Abilities

- Red active grants **dash**: `Shift`, 30 tiles/s for 12 ticks (0.2 s, 6 tiles) in the facing direction, gravity suspended during the dash, one air-dash per airborne period (resets on landing; ground dashes unlimited).
- Green active grants **double-jump**: one extra jump per airborne period at full jump speed.

## Tagged geometry

- Tagged geometry (`wall_red`, `wall_green`, `platform_red`, `platform_green`): while its color is active it has no collision (walls are passed through, platforms cannot be landed on); otherwise solid. Only one color is active, so red and green are never passable at once.

## Reveal

- Tagged elements of an unacquired color render grayscale; acquired → their color; active → brighter, pulsing.
- World saturation (a global post effect) is 0.35 with no color, 0.7 with one, 1.0 with both.
- The scarf shows the active color (gray when none).

## Hazards and goal

- Hazard cells (`^`) reset the player to the start (colors kept) in play; in a replay they fail the run.
- Goal cell: the run is complete.

## Tuning

All lanes use these numbers (tiles and seconds unless noted):

| Quantity | Value |
|---|---|
| Gravity | 40 t/s² |
| Run speed | 8 t/s |
| Jump speed | 15.5 t/s (apex 3.0 t, running jump clears ≤ 6 t) |
| Dash | 30 t/s × 0.2 s |
| Player box | 0.8 × 1.6 t, origin at the feet |
| Tick rate | 60 Hz, velocity integrated per tick |

## Controls

`A`/`←` left, `D`/`→` right, `Space` jump, `Shift` dash, `Q` switch, `R` restart, `Esc` quit. Camera keeps the whole level height in view at 1920×1080 (30 × 17 tiles visible), clamped to the level.
