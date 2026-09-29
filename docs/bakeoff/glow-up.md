# Glow-up round (THROWAWAY bake-off process)

Part of the Phase 1 bake-off; see [README.md](README.md). Sami approved Violet and the 3D kit as stand-ins, as "not great ... kinda janky, but it's fine". He had just seen them in all three lanes on the preliminary judging page, and asked for "a glow-up pass that really tries to make them as beautiful as possible", to "get calibrated on what we could expect if we really, really tried hard". So the round covers the character and all three lanes' worlds.

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

The bar is the one in [judging.md](judging.md): GRIS and Planet of Lana. Every score is against those two. A workstream may also name up to two shipped games in its own direction, such as Alto's Odyssey for flat vector, which the critic uses only to name gaps, not to score. The record lists each game with a link and a one-line description.

The critic may be shown the games' official press screenshots by link. They are never committed, because this repository is public, and never fed into generation.

## Rounds

Round 0 is the look before the round, shot as below. Each later round:

1. Starts from the latest kept round, and fixes the one gap from that round's critique expected to improve the look most.
2. Shoots the fixed shots again.
3. Has the critic compare it with the latest kept round, and records the round.

**Kept rounds.** Round 0 is kept. A later round is kept unless the critic calls it worse on at least one axis and better on none. A round that isn't kept is reverted, so the next round starts from the latest kept round again and is compared against it. A workstream ends at its latest kept round. That is the final round the gallery shows, and the look Task 12 captures.

**Fixed shots.** A lane's shots are the `scripts/capture-godot.sh` stills at 5, 20, 40 and 60 s, copied to `bakeoff/<lane>/glow-up/round-NN/`. The replay is fixed, so every round shows the same moments. Violet's shots go in `assets/bakeoff/protagonist/glow-up/round-NN/`: a contact sheet of all seven animations, six evenly spaced frames each, on neutral gray, plus one GIF per animation. The layout stays identical every round.

**The critic** is a fresh subagent each round, from a different model family than the one doing the work (in omp, `astra`). Before calling it, the workstream copies the two sets to neutral file names, such as `A-1.png` to `A-4.png` and `B-1.png` to `B-4.png`, assigns the letters at random, and records which letter was the new round. Round 0 has nothing to compare against, so its critic sees one set, named `A`. Every workstream gives its critic this prompt, filling in the braces, so that scores compare across workstreams:

> You are judging art for a 2D puzzle-platformer. The bar is GRIS and Planet of Lana. You may open these official press screenshots of them: {links}. {If the workstream names extra games: To name gaps, but not to score, you may also compare against {games, with links}.}
>
> {Round 0: Here is one set of screenshots, A: {files}.} {Later rounds: Here are two sets, A: {files} and B: {files}. They are in a random order, and nothing about them says which is newer.}
>
> Judge on three axes. visual_quality: how beautiful and finished it looks. character_appeal: how appealing and alive the character looks. color_readability: whether the red and green walls and platforms, and the character's scarf and silhouette, read at a glance. For a sheet showing only the character, color_readability covers the scarf and silhouette alone.
>
> Return: {later rounds: for each axis, A, B or same;} for each set, a score from 1 to 5 on each axis, where 5 means as good as GRIS or Planet of Lana; and for each set, the three biggest gaps between it and the bar, each concrete enough to act on ("the ground tiles repeat every 4 m", not "needs polish").

The critic's full reply is saved as `round-NN/critic.md`.

**The record** has one row per round:
- round number, and start and end time (UTC);
- what changed, and dollars spent;
- the letter mapping;
- the axes the critic called the new round better and worse on;
- its scores for both sets, and the new round's three gaps;
- whether the round was kept.

Lane costs and sessions also go in the lane's `LOG.md` as usual, with the purpose "glow-up round N". Violet's costs go in [shared-costs.md](shared-costs.md). `tools/gen` records no cost, so dollars are counted the way shared-costs.md counts them: provider-reported usage where there is any, otherwise calls at the measured per-call price, labelled as estimates.

## When a workstream stops

It stops at the first of these:

- two rounds in a row where the critic calls the new round better on no axis;
- $40 of generation spent in the workstream, counted as above;
- round 10;
- a wall: the next gap needs a paid tool or a human's skill. A lane records it under `blockers` in its `LOG.md`, and Violet in `rounds.md`, with the evidence. That is how a workstream asks for a purchase under decision 0012.

The record ends with the reason it stopped.

## Violet's rig contract

If Violet's winning technique needs something [character-rig.md](character-rig.md) lacks, such as eased keyframes, meshes or frame-by-frame sprite sheets, the Violet workstream changes the contract and `tools/spinerig` in a PR, and each lane owner ports its reader. The glowed-up Violet is generated art, so she replaces the current one only after Sami approves her (decision 0002). Until then the lanes keep the current Violet.

## What Sami gets

Once every workstream has stopped, the lead publishes one gallery. For each workstream it shows:
- round 0 next to the final round;
- a strip with every round in order, reverted ones marked;
- the critic's scores per round;
- the dollars and hours spent, and why the workstream stopped.

For each lane it also shows the final look's frame time at 1920x1080 on machine sami's Radeon 890M, the low-end target, measured by the lead. A look that can't hold 60 fps there is reported, not hidden.
