#!/usr/bin/env bash
# THROWAWAY (bake-off lane G-A, plan Task 7 Step 18): generates the desert biome brief's eleven 2D painted pieces into
# game/g-a/art/ with `gen image` (gpt-image-2), logging each response's token usage to bakeoff/g-a/reports/gen-usage.jsonl.
# No --input: the protagonist concept is not approved and the 3D kit turntable does not exist, so every prompt carries
# the brief's hex palette instead (lead's decision). gen sends quality=high; the orb, the goal gate, the hazard tile and the mid
# and near backdrops use --background transparent. Run bakeoff/g-a/edit-art.sh afterwards to make the backdrops repeat.
#   bash bakeoff/g-a/gen-art.sh [PIECE...]   # default: every piece whose PNG is missing; naming a piece regenerates it
# Run from the repository root.
set -euo pipefail
art=game/g-a/art
usage=bakeoff/g-a/reports/gen-usage.jsonl
mkdir -p "$art" "$(dirname "$usage")"

style="Fine-art hand-painted 2D game art in soft gouache and watercolor washes: large simple shapes, low detail, muted atmospheric golden-hour color, gentle gradients, soft edges, visible brush texture; a serene illustrated indie-game look, not cartoon and not mobile-game style. Brief palette: sand #d9b27c, rock #a86f46, shadow violet #5a4a7a, sky peach #f2c49b and teal #3f7f8c; tag colors ember red #e04a3a, verdant green #3fbf6a, gray #8c8c8c (these belong only to the tagged walls and platforms, which are painted neutral light gray and tinted in the game)."
avoid="text, letters, numbers, watermark, signature, black outlines, ink line art, cel shading, cartoon, mobile-game style, bricks, crystals, gems, faceted gemstones, anime, pixel art, photorealism, 3D render, frame, border, vignette, drop shadow"
clear="The background is fully transparent."
declare -A size prompt background
tile() { size[$1]=1024x1024; prompt[$1]="$2 $style"; }
back() { size[$1]=1536x1024; prompt[$1]="$2 $style"; }

tile ground-tile "A square texture tile of desert ground seen from the side, filling the whole square edge to edge: the top fifth is a band of golden sand with soft painted wind ripples, below it sandstone rock in a few broad horizontal bands. Paint it loosely in oil and gouache, like a painted desert backdrop's mesas: broad flat planes of warm sandstone and cool violet shadow laid in with big simple brushstrokes, a few large soft cracks and ledges, no small repeated stones, no brick or masonry courses, no photographic detail. This is a seamless repeating texture: it wraps around horizontally, so the left edge continues exactly into the right edge, with even lighting and nothing cut at the sides. Flat side view, no perspective, no horizon, no sky. No plants, no grass, no crystals, no gems."
tile wall-tile "A square texture tile of solid sandstone rock seen from the side, filling the whole square edge to edge. Paint it loosely in oil and gouache, like a painted desert backdrop's mesas: broad flat planes of warm sandstone and cool violet shadow laid in with big simple brushstrokes, a few large soft cracks and ledges, no small repeated stones, no brick or masonry courses, no photographic detail. This is a seamless repeating texture: it wraps around in both directions, so the left edge continues exactly into the right edge and the top edge into the bottom edge, with no lighting falloff and nothing cut at an edge. Flat, no perspective, no sky, no sand surface. No plants, no grass, no crystals, no gems."
tile platform-tile "A square texture tile of the top of a raised sandstone ledge seen from the side, filling the whole square edge to edge: a weathered, gently rounded slab top dusted with golden sand along the top, a darker rock body below. Paint it loosely in oil and gouache, like a painted desert backdrop's mesas: broad flat planes of warm sandstone and cool violet shadow laid in with big simple brushstrokes, a few large soft cracks and ledges, no small repeated stones, no brick or masonry courses, no photographic detail. This is a seamless repeating texture: it wraps around horizontally, so the left edge continues exactly into the right edge, with even lighting and nothing cut at the sides. Flat side view, no perspective, no sky. No plants, no grass, no crystals, no gems."
tile tag-wall "A square texture tile of an ordinary solid stone wall seen from the side: the same kind of layered stone with horizontal strata, subtle cracks and blocky ledges as a sandstone wall, but painted entirely in neutral light grays (no hue at all, from #b4b4b4 to #e6e6e6), with soft shading in the crevices and a gentle painterly stone texture, filling the whole square edge to edge. This is a seamless repeating texture: it wraps around in both directions, so the left edge continues exactly into the right edge and the top edge into the bottom edge, with even lighting and no stratum cut at an edge. Flat, no perspective. Plain stone only: no crystal, no facets, no gems, no glow, no plants."
tile tag-platform "A square texture tile of the top of an ordinary raised stone ledge seen from the side: the same kind of weathered flat slab as a sandstone ledge, with a flat top edge along the top and a thick slab body below with worn horizontal strata, but painted entirely in neutral light grays (no hue at all, from #b4b4b4 to #e6e6e6), filling the whole square edge to edge. This is a seamless repeating texture: it wraps around horizontally, so the left edge continues exactly into the right edge, with even lighting and nothing cut at the sides. Flat side view, no perspective, no sky. Plain stone only: no crystal, no facets, no gems, no glow, no plants."
tile orb "A single softly glowing orb of light: a smooth round sphere in neutral light gray and white (no hue at all) with a soft inner glow and a faint halo, centered, filling the middle two thirds of the square. Smooth and round: no crystal, no facets, no gems, no cracks. $clear"
tile goal-gate "A small weathered sandstone arch gateway seen straight from the side, standing on its base at the bottom edge of the square and filling most of it, with a warm golden light glowing inside the arch opening. Plain carved stone only: no gems, no crystals, no colored jewels, no plants, no grass, no moss; no green anywhere. $clear"
tile hazard-tile "A square texture tile of a row of jagged sandstone spikes seen straight from the side: sharp, dangerous points standing up from a broken rock base along the bottom edge and reaching nearly to the top edge, in rock #a86f46 with deep shadow violet #5a4a7a between the spikes and a few pale highlights on the points. This is a seamless repeating texture: it wraps around horizontally, so the left edge continues exactly into the right edge, with even lighting and no spike cut in half at the sides. No red, no green; no crystals, no gems, no plants. $clear"
back backdrop-far "A wide background painting for the farthest parallax layer: a golden-hour sky that fades from peach near the horizon to teal at the top, soft painterly clouds, and very distant pale layered mesa silhouettes in hazy violet along the lower third. The left and right edges match exactly so the painting repeats seamlessly side by side. No foreground, no sand, no plants. The clouds and the mesa line continue across the left and right edges without any break or mirrored shape."
back backdrop-mid "A wide painting for a middle parallax layer: a row of layered sandstone mesas and one wind-cut rock arch in warm rock tones with violet shadows, spanning the full width and occupying the lower half of the image; the mesa bases run off the bottom edge. The left and right edges match exactly so the row repeats seamlessly side by side. Everything above the mesas is empty, with no sky. The mesa silhouette meets both side edges at the same height so the join is invisible. No crystals, no gems, no plants. $clear"
back backdrop-near "A wide painting for the nearest parallax layer: low golden sand dunes across the bottom third of the image with dry acacia trees and saguaro cactus silhouettes on them; the dunes run off the bottom edge. The left and right edges match exactly so the strip repeats seamlessly side by side. Everything above the dunes and plants is empty, with no sky. The dune line meets both side edges at the same height so the join is invisible, and the outer eighth of the image at each side edge holds only low dunes and small grass, no trees or cacti. The acacia trees, saguaro cacti and grass are desaturated silhouettes in shadow violet #5a4a7a against the sky; no green foliage, no green cacti, no green anywhere. No crystals, no gems, no rocks with color. $clear"

for p in orb goal-gate hazard-tile backdrop-mid backdrop-near; do background[$p]=transparent; done

pieces=("$@")
if [ ${#pieces[@]} -eq 0 ]; then
  for p in ground-tile wall-tile platform-tile tag-wall tag-platform orb goal-gate hazard-tile backdrop-far backdrop-mid backdrop-near; do
    [ -f "$art/$p.png" ] || pieces+=("$p")
  done
fi
pids=()
for p in "${pieces[@]}"; do
  [ -n "${size[$p]:-}" ] || { echo "gen-art.sh: unknown piece $p" >&2; exit 1; }
  force=(); [ -f "$art/$p.png" ] && force=(--force)
  bg=(); [ -n "${background[$p]:-}" ] && bg=(--background "${background[$p]}")
  echo "gen-art.sh: $p (${size[$p]})"
  secrets OPENAI_API_KEY -- uv run --project tools/gen python bakeoff/g-a/gen_usage.py "$usage" image \
    --provider openai --model gpt-image-2 --size "${size[$p]}" \
    --prompt "${prompt[$p]}" --negative-prompt "$avoid" "${bg[@]}" "${force[@]}" --out "$art/$p.png" &
  pids+=("$!")
done
failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
exit "$failed"
