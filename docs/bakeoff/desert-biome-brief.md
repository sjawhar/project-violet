# Desert biome brief (THROWAWAY)

Part of the Phase 1 bake-off shared inputs; see [README.md](README.md). This brief describes the bake-off's one biome only — Violet's final setting is undecided ([decision 0009](../decisions/0009-mechanics-undecided.md)).

## Mood

Golden-hour high desert; ochre dunes, layered sandstone mesas, wind-cut arches, dry acacia and saguaro silhouettes; sky peach → teal.

## Palette

| Element | Color |
|---|---|
| Sand | `#d9b27c` |
| Rock | `#a86f46` |
| Shadow | violet `#5a4a7a` |
| Sky | `#f2c49b` / `#3f7f8c` |

Tagged elements are crystal: ember red `#e04a3a`, verdant green `#3fbf6a`, gray `#8c8c8c` until acquired.

## Kit lists

- **3D** (`assets/bakeoff/desert-kit-3d/`): `mesa-large`, `mesa-small`, `arch`, `boulder-a`, `boulder-b`, `saguaro`, `acacia`, `dune-ridge`, `ruin-column`, `ruin-wall`, `sand-tile`, `rock-tile`, `crystal-cluster` (untinted), `orb-pedestal`, `goal-gate`, `hazard-spikes`.
- **2D painted** (G-A): `ground-tile`, `wall-tile`, `platform-tile`, `crystal-wall`, `crystal-platform`, `orb`, `goal-gate`, `hazard-tile`, `backdrop-far`, `backdrop-mid`, `backdrop-near`.
- **SVG** (G-C): the same eleven as flat vector.

The hazard pieces (`hazard-spikes` in 3D, `hazard-tile` in 2D) dress the level's `hazard` cells. They are jagged sandstone spikes in rock `#a86f46` and shadow violet `#5a4a7a`: they have to read as dangerous at a glance, and they never use the tag red or green, which are reserved for tagged crystals.
