# Technique trial critic (fresh `astra` subagent, blind)

Verbatim prompt given (from `rounds.md`/`glow-up.md`), with the neutral file paths filled in:

> You are judging art for a 2D puzzle-platformer. The bar is GRIS and Planet of Lana. You may open
> these official press screenshots of them: https://www.devolverdigital.com/games/gris,
> https://planetoflana.com/. To name gaps, but not to score, you may also compare against Ori and the
> Blind Forest (https://www.orithegame.com/screenshot_category/ori-and-the-blind-forest/) and Hollow
> Knight (https://www.hollowknight.com/).
>
> Here are two sets, A: /tmp/violet-technique-trial-critic/A-contact.png (a six-frame contact sheet of
> one running animation, on neutral gray) and /tmp/violet-technique-trial-critic/A-run.gif (the same
> running animation as a looping GIF), and B: /tmp/violet-technique-trial-critic/B-contact.png and
> /tmp/violet-technique-trial-critic/B-run.gif (same format). They are in a random order, and nothing
> about them says which is newer.
>
> Judge on three axes. visual_quality: how beautiful and finished it looks. character_appeal: how
> appealing and alive the character looks. color_readability: whether the red and green walls and
> platforms, and the character's scarf and silhouette, read at a glance. For a sheet showing only the
> character, color_readability covers the scarf and silhouette alone.
>
> Return: for each axis, A, B or same; for each set, a score from 1 to 5 on each axis, where 5 means as
> good as GRIS or Planet of Lana; and for each set, the three biggest gaps between it and the bar, each
> concrete enough to act on ("the ground tiles repeat every 4 m", not "needs polish").

Letter map (recorded by the workstream, never shown to the critic): **A = technique A (cutout rig,
round 2, kept)**, **B = technique B (frame-by-frame painted, this trial)**.

## The critic's full reply

### Method note

I read both contact sheets and both GIFs directly. Because the `read` tool only returned a single
static frame for each GIF, I decoded the actual GIF frame sequences (via `gifuct-js`/`pngjs`) into
individual PNGs, composited them correctly over the neutral gray, and built full-cycle contact strips
plus zoomed crops (face, hands, legs) for both sets — that's the evidence behind the animation-cycle
findings below, not just the six-frame sheets. GRIS's press page 429'd and Planet of Lana's site is
mostly video/marketing copy, so the bar judgment leans on the still frames plus well-established
knowledge of both games' character-animation quality (high figure-ground contrast, full-body weight
shift, continuous cloth ribbons, articulated hands/faces).

### Per-axis verdict

| Axis | Winner |
|---|---|
| visual_quality | **B** |
| character_appeal | **B** |
| color_readability | **A** |

### Scores (1-5, 5 = GRIS/Planet of Lana bar)

| | visual_quality | character_appeal | color_readability |
|---|---|---|---|
| **A** | 3 | 2 | 3 |
| **B** | 4 | 4 | 2 |

### Why

The decisive finding: isolating just the leg region across all 18 frames of A's GIF shows the legs and
torso barely move at all - front/back leg placement is essentially frozen in the same "one leg up, one
leg back" pose for the entire loop; only the scarf flutters and the arm sways slightly. It reads as
gliding/floating, not running. B's leg strip (8 frames) shows a genuine alternating stride with real
contact/passing poses and a body bob. This alone drives most of the character_appeal and visual_quality
gap, since a "running animation" that doesn't run is a finishing problem, not a taste call.

On color_readability I went the other way: A's scarf is one coherent white ribbon in every frame, so
the silhouette reads cleanly at a glance despite low body-to-background contrast. B's scarf, in 2 of
its 8 frames (indices 1 and 5), renders as three overlapping semi-transparent copies at different
offsets - it looks like a ghosting glitch rather than one flowing ribbon, and that's visible even in
B's original six-panel contact sheet (panels 2 and 5), not just the GIF.

### Set A — three biggest gaps vs. the bar

1. The run cycle doesn't cycle. Leg and torso pose are nearly identical across all 18 frames (confirmed
   by cropping the leg region and comparing frames 0, 6, 9, 15 side by side) - only the scarf and a
   slight arm swing animate. Needs an actual contact/passing/recoil leg cycle before anything else here
   matters.
2. Hands are a featureless flesh wedge. Zoomed crop shows no finger/knuckle separation at all where the
   arm meets the sleeve cuff - flat blob, not an articulated fist like B's.
3. Scarf tail is a hard-edged frayed/tattered fringe, not a continuous soft-tapering ribbon - reads as a
   torn flag rather than flowing cloth, and slightly muddies an otherwise clean silhouette.

### Set B — three biggest gaps vs. the bar

1. Scarf ghosting in 2 of 8 frames. The trailing cloth renders as three stacked semi-transparent copies
   at different offsets/opacities instead of one continuous ribbon - reads as a rendering glitch rather
   than intentional motion blur; this is the direct cause of its lower color_readability score.
2. Low figure-to-background value contrast. The robe's mid-brown sits close in luminance to the neutral
   gray backdrop; without the scarf doing the work, the body silhouette itself doesn't pop the way
   GRIS's higher-contrast figures do - needs a stronger rim-light or a value-separated base tone.
3. One pose reads as a stumble. Frame index 6 (front knee pulled in tight near the torso with the legs
   nearly crossed) looks more like a crouch/stumble than a clean running passing-position - worth an
   added in-between or a wider knee drive so every frame in the loop reads unambiguously as "running."
