# Glow-up round (THROWAWAY bake-off process)

Part of the Phase 1 bake-off; see [README.md](README.md). Sami approved Violet and the 3D kit as stand-ins, as "not great ... kinda janky, but it's fine", and asked for "a glow-up pass that really tries to make them as beautiful as possible", to "get calibrated on what we could expect if we really, really tried hard".

The round answers one question per direction: how good does agent-made art get when the agents keep improving it, and what does each step cost? The judging captures (Task 12) are taken after this round, so Sami scores each direction at its best. The captures from before the round stay published, for comparison.

## Workstreams

| Workstream | What it improves | Owner / machine | Record |
|---|---|---|---|
| Violet | Her painted parts and every animation | lead / sami | `assets/bakeoff/protagonist/glow-up/rounds.md` on `master`, by PR |
| G-A | The painted world, and how Violet reads in it | oryx agent | `bakeoff/g-a/glow-up.md` on the lane branch |
| G-D | The 3D world, and how Violet reads in it | oryx agent | `bakeoff/g-d/glow-up.md` on the lane branch |
| G-C | The vector world, and how Violet reads in it | oryx agent | `bakeoff/g-c/glow-up.md` on the lane branch |

U-D and Control have not run, so they have nothing to improve.

## What stays fixed

- The greybox level, the mechanic, and the replay. Each lane's `ci.sh` stays green and still reaches the goal by `expect.goal_by_tick`.
- The camera framing the plan sets for each lane.
- The desert biome, and the tag rule: only tagged walls and platforms use the tag red and green ([desert-biome-brief.md](desert-biome-brief.md)).
- No purchases ([decision 0012](../decisions/0012-no-purchases-until-agents-prove-it.md)). Image generation through `tools/gen` on the approved keys is allowed.

Everything else about the look is the workstream's to change. That includes lighting, shading, post-processing, colour grading, parallax, particles and ambient motion, tile variation and edges, props and set dressing, foreground framing, and, for Violet, how she is drawn and animated. The Violet workstream tries at least two animation techniques, and keeps whichever the critic prefers on `character_appeal`: the cutout rig polished (eased keyframes, overlap and follow-through, secondary motion on the robe and scarf, repainted or added parts) and frame-by-frame painted sprites.

## The bar

The bar is the one in [judging.md](judging.md): GRIS and Planet of Lana. Each workstream may add up to two shipped games in its own direction, such as Alto's Odyssey for flat vector, and names them by title and link in its record. The critic may be shown the games' official press screenshots by link, to compare against. They are never committed, because this repository is public, and never fed into generation.

## Rounds

Round 0 is the look before the round, shot as below. Each later round:

1. Takes the critic's list of gaps from the previous round, and fixes the one expected to improve the look most.
2. Shoots the fixed shots again.
3. Asks the critic to compare, and records the round.

**Fixed shots.** A lane's shots are the `scripts/capture-godot.sh` stills at 5, 20, 40 and 60 s, copied to `bakeoff/<lane>/glow-up/round-NN/`. The replay is fixed, so every round shows the same moments. Violet's shots go in `assets/bakeoff/protagonist/glow-up/round-NN/`: a contact sheet of all seven animations, six evenly spaced frames each, on neutral gray, plus one GIF per animation.

**The critic** is a subagent from a different model family than the one doing the work (in omp, `astra`). It sees only the two latest rounds' shots, labelled A and B in a random order, the bar, and the three axes in `judging.md`. It returns:

- for each axis, which of A and B is better, or "same";
- a 1-5 score on each axis for each of A and B;
- the three biggest gaps between the better set and the bar, each concrete enough to act on. "The ground tiles repeat every 4 m" is usable; "needs polish" isn't.

The workstream records which of A and B was the new round.

**The record** has one row per round: round number, start and end time (UTC), what changed, dollars spent, the axes the critic called better, its scores for the new round, and its three gaps. Lane costs and sessions also go in the lane's `LOG.md` as usual, with the purpose "glow-up round N". Violet's costs go in [shared-costs.md](shared-costs.md).

## When a workstream stops

It stops at the first of these:

- two rounds in a row where the critic calls no axis better;
- $40 of generation spent in the workstream;
- round 10;
- a wall: the next gap needs a paid tool or a human's skill. The workstream records it under `blockers` with the evidence, which is how a lane asks for a purchase under decision 0012.

The record ends with the reason it stopped.

## Violet's rig contract

If Violet's winning technique needs something [character-rig.md](character-rig.md) lacks, such as eased keyframes, meshes or frame-by-frame sprite sheets, the Violet workstream changes the contract and `tools/spinerig` in a PR, and each lane owner ports its reader. The glowed-up Violet is generated art, so she replaces the current one only after Sami approves her (decision 0002). Until then the lanes keep the current Violet.

## What Sami gets

Once every workstream has stopped, the lead publishes one gallery. For each workstream it shows round 0 next to the final round, a strip with every round in order, the critic's scores per round, the dollars and hours spent, and why the workstream stopped. For each lane it also shows the final look's frame time at 1920x1080 on machine sami's Radeon 890M, the low-end target, measured by the lead. A look that can't hold 60 fps there is reported, not hidden.
