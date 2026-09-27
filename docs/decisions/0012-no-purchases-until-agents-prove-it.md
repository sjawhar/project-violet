# No tool purchases in the bake-off until agents prove they need one

- **Date:** 2026-09-27
- **Status:** settled

## Decision

The bake-off buys no tools. It runs on what's already in the repo or already approved,
not on Spine, Meshy, or Recraft:

- No Spine: the protagonist rig is `tools/spinerig`'s generated Spine-4.3-JSON subset,
  and each lane reads that exact subset with its own small reader, per
  [`docs/bakeoff/character-rig.md`](../bakeoff/character-rig.md).
- No Meshy: the 3D desert kit is agent-authored Blender Python, exported as GLB.
- No Recraft: G-C's art is hand-written SVG.

The Control lane waits, since its full-3D character needed Meshy.

Any tool purchase comes later, and only when a lane's results show that tool is the
bottleneck — not ahead of that evidence.

Unity is not covered by this ruling: U-D still waits on Sami's own Unity sign-in, as
before.

Agent-authored assets (the Blender kit, the SVG) are recorded in provenance as origin
`generated` with the authoring model, so the Steam AI disclosure includes them.

## Source

Sami, in the lead session, when told the Spine purchase was the longest pole
(2026-09-27, ~16:55Z): "I really don't think that you should be blocked on me buying
spine. You haven't actually proven that you can develop anything yet, why should I
purchase some professional tool"

Sami, answering the lead's question "Buy Meshy and Recraft now, or have agents make
that art themselves first? I recommend agents first" (2026-09-27, ~17:25Z): "If you
recommend agents first then fucking do it already"

## Consequences

- `docs/superpowers/plans/2026-09-27-phase-1-bake-off.md` drops spine-godot,
  spine-unity, the Spine editor, Meshy, and Recraft: Task 5 stops at `spinerig
  generate` and `spinerig render` (no Spine editor, atlas, or packing); Task 6
  replaces the Meshy adapter with agent-authored Blender Python
  (`assets/bakeoff/desert-kit-3d/build_kit.py`); Task 10 replaces the Recraft adapter
  with hand-written SVG; Task 11 (Control) is marked waiting; Tasks 7–9 read the
  protagonist rig through their own reader instead of a Spine runtime.
- The bake-off's result, tracked in the plan as decision 0012 at the time it was
  written, is renumbered 0013 — this ruling took 0012.
- The Spine trial already installed on machine sami (free, can't save or export) stays
  usable for a one-off cross-check — Sami opening a generated rig with Import Data —
  without this counting as a purchase.
