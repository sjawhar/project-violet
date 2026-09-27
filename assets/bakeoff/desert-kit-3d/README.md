# 3D desert kit (THROWAWAY)

> Phase 1 bake-off content only ([../../../docs/bakeoff/README.md](../../../docs/bakeoff/README.md)). Nothing here is canon.

Sixteen low-poly pieces for the bake-off's desert biome ([desert-biome-brief.md](../../../docs/bakeoff/desert-biome-brief.md)), for lanes G-D and U-D. An agent wrote [build_kit.py](build_kit.py), a Blender Python script, and every piece is built from that script and its seed alone. No purchased tool, generation API or third-party art went into the kit. The provenance records say the same thing: each GLB is `generated` by `blender` 5.2.2 from `build_kit.py`, seed `20260927`.

## Rebuild

From the repository root, with the pinned Blender on `PATH`:

```sh
blender -b --factory-startup --python assets/bakeoff/desert-kit-3d/build_kit.py -- assets/bakeoff/desert-kit-3d
```

A rebuild is byte-identical. The script prints each piece's triangle count and size, and it fails when a piece goes over 5,000 triangles, when its base isn't at height 0, or when a cell piece doesn't fit its 1 m cell. After a change, re-record the provenance of the script and of every GLB (`provenance record ... --force`).

[preview/kit-at-32m.png](preview/kit-at-32m.png) shows all sixteen pieces laid out as a side-scroller camera 32 m away sees them. To re-render it on the CPU (it takes about 35 s):

```sh
blender -b --factory-startup --python assets/bakeoff/desert-kit-3d/preview/render_scene.py -- assets/bakeoff/desert-kit-3d assets/bakeoff/desert-kit-3d/preview/kit-at-32m.png
```

## Conventions

- glTF binary, +Y up, meters, modifiers applied, no cameras or lights. The origin is at the base center, and the front faces +Z (toward a side-scroller camera).
- Colors are named Principled BSDF materials in the biome palette. `sand` `#d9b27c`, `rock` `#a86f46`, `shadow` `#5a4a7a` and `portal` (sky teal `#3f7f8c`, emissive) come from the brief. `sand_deep`, `sand_shade`, `rock_light`, `rock_dark` and `stone` are mixes of those colors.
- A neutral gray vertex color (`COLOR_0`) multiplies the base color to add painterly variation. It is gray, so a lane can still tint a material.
- `crystal` and `orb` are untinted neutral light gray (`#d4d4d4`). Lanes tint them red, green or gray per [mechanic.md](../../../docs/bakeoff/mechanic.md). No piece uses the tag red or green, and there is no vegetation green anywhere: saguaro and acacia are silhouettes in shadow violet.
- In `orb-pedestal`, the orb is a child node named `orb`, so a lane can bob or spin it.
- Godot 4.7's glTF importer never applies `COLOR_0` to the material of a mesh's first primitive (in `modules/gltf/gltf_document.cpp`, the primitive's material is set up before its colors are read). To make that harmless, the first material slot is always a flat one (`shadow`, `sand_deep` or `sand_shade`) whose vertex colors are all white. The pieces with a single material (`saguaro`, `acacia`, `crystal-cluster` and the `orb` node) lose their subtle vertex shading in Godot unless the lane sets `vertex_color_use_as_albedo` on them.

## Pieces

Sizes are width (X) × depth (Z) × height (Y) in meters, as `build_kit.py` prints them.

| Piece | Triangles | Size (m) | What it is |
|---|---:|---|---|
| `mesa-large` | 2352 | 35.2 × 17.7 × 20.0 | Layered sandstone mesa with a butte tier, violet strata grooves and a talus apron |
| `mesa-small` | 1110 | 12.1 × 9.8 × 9.7 | Butte with an overhanging cap rock |
| `arch` | 1720 | 21.6 × 12.5 × 11.4 | Wind-cut arch on a slickrock base, dipping strata, violet inner rim |
| `boulder-a` | 62 | 2.4 × 1.9 × 1.7 | Rounded faceted boulder |
| `boulder-b` | 66 | 2.5 × 1.6 × 1.7 | Chipped tabular slab tipped up on a smaller rock |
| `saguaro` | 1760 | 1.9 × 1.2 × 5.4 | Ribbed saguaro silhouette, shadow violet |
| `acacia` | 696 | 7.2 × 2.7 × 4.2 | Flat-topped acacia silhouette, shadow violet |
| `dune-ridge` | 1672 | 40.0 × 15.0 × 5.0 | Dune with a sharp crest and a shaded slip face at the back |
| `ruin-column` | 560 | 1.6 × 1.1 × 3.4 | Broken fluted column on a plinth, with a fallen fragment |
| `ruin-wall` | 384 | 5.5 × 1.9 × 2.8 | Crumbling block wall with a window and fallen blocks |
| `sand-tile` | 386 | 1.0 × 1.0 × 1.02 | 1 m sand block; rippled top, wavy strata; tiles seamlessly side by side and stacked |
| `rock-tile` | 410 | 1.0 × 1.0 × 1.03 | 1 m layered sandstone block with violet strata lines; tiles seamlessly |
| `crystal-cluster` | 288 | 0.9 × 0.9 × 0.95 | Dense crystal cluster that fills its cell; untinted gray |
| `orb-pedestal` | 240 | 0.7 × 0.7 × 0.96 | Carved pedestal with a floating untinted orb |
| `goal-gate` | 394 | 1.0 × 0.5 × 2.95 | Sandstone gate with a glowing sky-teal pointed-arch portal and a sun disc |
| `hazard-spikes` | 159 | 0.9 × 0.9 × 0.94 | Jagged sandstone spikes in rock and shadow violet |

The tiles are exactly 1 m on every side. Their top surface detail rises at most 3.5 cm above the cell. Its height and the strata boundaries are periodic, so neighbouring tiles meet without a seam.
