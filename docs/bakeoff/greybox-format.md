# `violet-greybox` v1 (THROWAWAY bake-off level format)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). Phase 2 picks the real level pipeline — this format is scoped to the bake-off's one greybox level.

## Shape

```json
{
  "format": "violet-greybox",
  "version": 1,
  "tile_size_px": 64,
  "legend": {"<char>": "<kind>"},
  "rows": ["<row string>", "..."]
}
```

- `tile_size_px` is one of `32`, `64`, `128`.
- `legend` maps a single character to a cell kind.
- `rows` are top-to-bottom, one character per cell; every row must be the same length as row 0.

## Kinds

`empty solid wall_red wall_green platform_red platform_green start goal orb_red orb_green hazard`

- Exactly one `start` and one `goal` cell.
- A tagged color (`wall_red`/`platform_red` need `orb_red`; `wall_green`/`platform_green` need `orb_green`) requires the matching orb to be present somewhere in the level.

## Coordinates

Cell `(col, row)` (0-indexed, `row` counting down from the top of `rows`) converts to a world-space cell center as:

- Godot 2D: `((col + 0.5) · tile_size_px, (row + 0.5) · tile_size_px)`, y down.
- Godot 3D and Unity: `(col + 0.5, H − row − 0.5, 0)` in metres, y up, where `H` is the number of rows.

## Why JSON, not LDtk or YAML

Both engines parse JSON natively (`JSON.parse_string` in Godot, `Newtonsoft.Json` in Unity); neither parses YAML without adding a library. LDtk's JSON needs `defs`, `layerInstances`, and `intGridCsv`, its Linux build is labeled experimental by its own maintainer, and its Godot importer (`godot-ldtk-importer`) is effectively unmaintained (see `docs/research/2026-09/README.md` corrections). Phase 2 picks the real level pipeline; this format only has to carry one throwaway bake-off level.
