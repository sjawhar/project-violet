# Judging (THROWAWAY bake-off process)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md).

## Scoring

Sami scores each lane 1–5 against the GRIS / Planet of Lana bar on:

- `visual_quality`
- `character_appeal`
- `color_readability`

and answers `would_ship` yes/no ("would you ship this direction?"). If no D lane gets `yes`, he also answers `prefers_c_over_a`. Control (the full-3D Blender protagonist) is scored for information only and does not enter the decision rule.

## Decision rule (verbatim from the spec)

D wins if Sami answers yes for at least one D lane. Otherwise A wins, and C instead only if Sami prefers it. The engine is whichever lane Sami scored higher for the winning direction (sum of the three scores, among that direction's lanes with `yes`); a tie goes to Godot.

## How scoring happens

Scoring happens as one comment on the judging PR, in this block format:

```
lane: g-a | visual_quality: 4 | character_appeal: 3 | color_readability: 4 | would_ship: no | notes: ...
```

One block per lane. The lead transcribes the comment into `docs/bakeoff/scores.json` (schema: `docs/bakeoff/scores.schema.json`), citing the comment URL as `source`. `uv run --project tools/bakeoff bakeoff decide docs/bakeoff/scores.json` applies the rule above to that file.
