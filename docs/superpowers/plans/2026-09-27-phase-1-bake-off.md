# Phase 1 Bake-off Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the one-week agent bake-off that decides Violet's art direction and engine from measured output: five lanes build the same throwaway slice, every lane delivers (or records a blocker for) a playable Linux build, a 60–90 s capture with stills, an automated completability test plus color-tag check, and a log of agent-hours, dollars and human interventions; Sami scores the lanes on a gallery page and the result becomes the next decision record (0013 at the time of writing; 0011 records Sami's merge-queue waiver, 0012 the no-purchase ruling).

**Architecture:**
- Shared inputs land on `master` through PRs Sami approves: the throwaway mechanic, one greybox level as JSON, the protagonist and desert briefs, the judging sheet, the Spine protagonist rig, and the 3D desert kit. Each lane then branches from `master` onto `bakeoff/<lane>` and never merges.
- A lane branch holds one engine project under `game/<lane>/` and its evidence under `bakeoff/<lane>/` (`LOG.md`, `replays/`, `reports/`, `capture/` in LFS). `.github/workflows/bakeoff.yml` runs `game/<lane>/ci.sh` on every push to `bakeoff/**`.
- `tools/greybox`, `tools/bakeoff` and `tools/spinerig` are uv projects like `tools/provenance` and `tools/gen`. `tools/gen` gains `--background`. The 3D desert kit (Task 6) and the Control protagonist (Task 11) are agent-authored Blender Python, and G-C's kit (Task 10) is hand-written SVG — none of them a `tools/gen` adapter (decision 0012). `tools/bakeoff gallery` assembles the judging page on top of `preview build/publish`; `tools/bakeoff decide` applies the decision rule.

**Tech Stack:** Godot 4.7.2 (mise); Unity 6.3 LTS (6000.3, Unity Hub) with URP, glTFast and Unity's official MCP; OpenAI `gpt-image-2` and Gemini `gemini-3.1-flash-image` through `gen image`; Blender from `tools/preview/README.md` (agent-authored Python builds the 3D desert kit and the Control protagonist — decision 0012); ffmpeg, ImageMagick, uv/pytest; jj with Git LFS.

**Spec:** `docs/superpowers/specs/2026-09-26-violet-studio-design.md` (phase0/docs version; root issue https://github.com/sjawhar/project-violet/issues/4). Binding: "Phase 1: Bake-off", Acceptance 3, Errors, Requirements. Research: `docs/research/2026-09/art-feasibility.md` §4, `engine-2.5d.md` §4, `engine-steelman.md`, `art-pipeline.md`, `playtest-qa.md`, `README.md` corrections. Decisions: `docs/decisions/0003`, `0004`, `0006`, `0009`, `0012`.

## Global Constraints

- Phase 0 is merged before Task 1 starts: PRs #7, #11, #6, #10, and `preview` from issue #8 (`preview build PR PATH...`, `preview publish PR`) on `master`. `provenance check` and `lfs-check` run in CI.
- Lanes are fixed: **G-A** Godot 4.7.2 2D painted world; **G-D** Godot 4.7.2 3D hybrid (AI 3D desert kit, toon/painterly shading, real colored lights, Spine character lit in 3D); **U-D** Unity 6.3 LTS URP hybrid, agents drive the editor through Unity's official MCP only; **G-C** Godot 2D flat-vector desert kit, environment only; **Control** full-3D protagonist (agent-authored Blender Python: model, rig, motion) rendered in Blender. No third-party Unity MCP, ever (Unity ToS §17.2, decision 0006).
- Mechanics are undecided (decision 0009). The test mechanic in `docs/bakeoff/mechanic.md` is **THROWAWAY**; every bake-off file carries the word THROWAWAY in its header or README and nothing from it is promoted to canon.
- The protagonist is built once as a Spine-4.3-JSON cutout rig (one painted image per body part via `gen image`; skeleton and animations authored by an agent, generated with `spinerig generate` and proven with `spinerig render` — no Spine editor or runtime, per decision 0012). `spine-animation-ai` (PolyForm Noncommercial) is not used; its technique is reimplemented in `tools/spinerig`.
- Public repo: no secrets, no third-party art. Generation inputs are in-repo files with their own provenance records (`gen` enforces this). Every asset under `game/` or `assets/` has a sidecar; lane CI runs `provenance check`.
- jj, not git. Commit identity `sami@thecybermonk.com`. LFS: `git lfs push origin <bookmark>` before `jj git push --bookmark <bookmark>`. PRs open with `gh api repos/sjawhar/project-violet/pulls -f title=... -f head=... -f base=master -F body=@body.md`. Lane bookmarks `bakeoff/<lane>` never merge and are never deleted.
- Code never calls an LLM. "Review" means an agent session looks at stills and captures. CI calls no model.
- Accounts: only `OPENAI_API_KEY` and `GEMINI_API_KEY` are approved (image generation). No other account is bought for the bake-off (decision 0012): Spine, Meshy and Recraft are not purchased. Unity Hub sign-in + Unity AI subscription is still Sami's sign-up, and U-D waits only on it (see the gating table). Keys come only from `secrets KEY -- command`.
- Machines: **sami** (laptop, Radeon 890M, COSMIC, ~79 GB free) runs what needs its GUI or its GPU: Unity and G-D's short RADV check. **oryx** (RTX 3070 8 GB offscreen, 62 GB RAM, 2.6 TB) runs the Godot lanes' development, tests and captures, and Blender. Captures render in software under Xvfb, as CI does: sami has no Xvfb, and a capture must not open a window on Sami's desktop. Never reboot oryx from an agent session.
- **oryx GPU:** unusable until Sami reboots (nvidia_uvm crashes in the kernel when CUDA programs exit). After the reboot the oryx agent loads `nvidia_uvm` with `uvm_disable_hmm=1`. Nothing GPU-dependent runs until Task 0 passes; GPU jobs on oryx run **one at a time** through `flock /tmp/oryx-gpu.lock` (concurrent CUDA processes triggered the crash). Every GPU-dependent step names its no-GPU fallback.
- Disk guard: before starting a lane, `df --output=avail -BG / | tail -1`; below 20 GB, stop starting lanes and clean `~/.cache`, `out/`, finished lane workspaces first.
- Determinism: physics at 60 Hz fixed ticks everywhere; replays are per-tick input sets; tests assert "goal reached by tick N", never exact positions. Units: 1 tile = 64 px (Godot 2D) = 1 m (Godot 3D, Unity).

## Accounts and what each unblocks

| Account (Sami signs up) | Unblocks | Until then |
|---|---|---|
| none needed | Tasks 0, 1, 2, 3, 4, 5, 6, 7 (greybox + stand-in), 8 (greybox + stand-in), 10, 12 | — |
| Unity Hub sign-in + Unity AI subscription (MCP) | Task 9 | 9's C# is written and reviewed as text; nothing runs |
| oryx reboot by Sami (GPU) | Task 0 → Blender Cycles in 6 (kit turntables) and 11 | Blender runs Cycles on CPU (`--cycles-device CPU`, fewer samples) or Eevee under Xvfb |

## Owners and order

| Task | Owner / machine | Depends on | Account |
|---|---|---|---|
| 0. oryx GPU healthy precondition | oryx agent (after Sami reboots) | none | oryx reboot |
| 1. Shared inputs: docs, level, formats, `tools/greybox` | lead / sami | Phase 0 merged | none |
| 2. `tools/bakeoff`: log-check, decide, gallery, results-md | oryx agent | 1 | none |
| 3. Bake-off CI, `scripts/godot-fetch.sh`, capture scripts | oryx agent | 1 | none |
| 4. Protagonist concept + body parts; `gen image --background` | lead / sami | 1 | none (approved keys) |
| 5. Spine rig: `tools/spinerig`, `assets/bakeoff/protagonist/rig/` | lead / sami | 4 | none |
| 6. `assets/bakeoff/desert-kit-3d/build_kit.py` (agent-authored Blender Python) | oryx agent | 1 (turntables also 0) | none |
| 7. Lane G-A | oryx agent (captures on oryx, software) | 1, 3 (final look: 5) | none |
| 8. Lane G-D | oryx agent (captures on oryx, software; RADV check on sami) | 1, 3 (final look: 5, 6) | none |
| 9. Lane U-D | sami agent | 1, 3, Sami's Unity checklist (final look: 5, 6) | Unity Hub + Unity AI |
| 10. Lane G-C | oryx agent (captures on oryx, software) | 7 (branches from it), hand-written SVGs | none |
| 11. Lane Control | oryx agent | 4 (concept), 0 (GPU; CPU fallback) | waiting (decision 0012) |
| 12. Judging gallery, scores, decision record 0013 | lead / sami | 2, all lanes delivered or blocked | none |

Parallel waves: Task 1 first (one PR). Then 2, 3, 4 in parallel; 7 and 8 start as soon as 1 and 3 are on `master` (greybox visuals, stand-in character). 5, 6 and 10 start once their own inputs are ready (Task 4 for 5; Task 1 for 6; the G-A branch for 10) — none of them wait on an account. 9 starts the day Sami's Unity account exists. 11 waits (decision 0012). 12 starts when the last lane reports `status: delivered` or `blocked`.

## Conventions used by every task

- `$VIOLET` = the machine's repo checkout root (on sami `/home/sami/Code/personal/project-violet`; on oryx the checkout Phase 0's provenance work used). All paths and commands are relative to it.
- A tool or docs PR: `jj new master -m "<title>"`, edit, `jj describe -m "<title>"`, `jj new`, `jj bookmark create phase1/<topic> -r @-`, `git lfs push origin phase1/<topic>` (when binaries changed), `jj git push --bookmark phase1/<topic>`, then `gh api repos/sjawhar/project-violet/pulls -f title="<title>" -f head=phase1/<topic> -f base=master -F body=@/tmp/body.md`. The body states what was run and what was observed.
- A lane: `jj workspace add --name <lane> -r master ~/src/violet-<lane>` (its own working copy so lanes on one machine do not collide), `cd ~/src/violet-<lane>`, `jj bookmark create bakeoff/<lane> -r @`, commit often (`jj describe -m ...; jj new; jj bookmark set bakeoff/<lane> -r @-`), push with `git lfs push origin bakeoff/<lane> && jj git push --bookmark bakeoff/<lane>`. Lane branches get no PR; CI runs on push and the gallery links the runs.
- Lane layout: `game/<lane>/` (engine project, `ci.sh`), `bakeoff/<lane>/LOG.md` (format in `docs/bakeoff/lane-log-format.md`), `bakeoff/<lane>/replays/*.replay.json` (the lane's own replay; Godot lanes also keep a copy at `game/<lane>/replays/` because `res://` cannot leave the project), `bakeoff/<lane>/reports/` (CI-readable results), `bakeoff/<lane>/capture/capture.mp4` + `still-*.png` (LFS).
- Every lane copies `docs/bakeoff/level01.greybox.json` into its project unchanged; `ci.sh` runs `cmp` against the docs copy.
- Every generated image: `secrets OPENAI_API_KEY -- uv run --project tools/gen gen image ...` (or `GEMINI_API_KEY`). Every manual asset edit: `uv run --project tools/provenance provenance edit ASSET --by NAME --description TEXT`.

---

### Task 0: oryx GPU healthy precondition

**Files:**
- Create: `scripts/oryx-gpu-check.sh`
- Modify: `AGENTS.md` (Machines section: the one-at-a-time rule and the module parameter)

**Interfaces:**
- Consumes: the Blender install from `tools/preview/README.md` (`blender` on PATH).
- Produces: `scripts/oryx-gpu-check.sh` exits 0 only when `nvidia-smi` lists the RTX 3070, `nvidia_uvm` carries `uvm_disable_hmm=1`, and a CUDA render process exits cleanly; every GPU step in Tasks 6 and 11 starts with `scripts/oryx-gpu-check.sh && flock /tmp/oryx-gpu.lock <command>`.

- [ ] **Step 1:** Wait for Sami's reboot (his call; ask once on issue #4 (this project uses GitHub, not Dispatch), keep working on Tasks 1–5 and the greybox lanes). After it: `sudo modprobe nvidia_uvm uvm_disable_hmm=1` and persist it in `/etc/modprobe.d/nvidia-uvm.conf` with `options nvidia_uvm uvm_disable_hmm=1`. Record in `AGENTS.md`.
- [ ] **Step 2:** Write `scripts/oryx-gpu-check.sh`:

```bash
#!/usr/bin/env bash
# oryx only: proves the RTX 3070 is usable before a GPU job. GPU jobs run one at a time: flock /tmp/oryx-gpu.lock <cmd>.
set -euo pipefail
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | grep -q "RTX 3070"
[ "$(cat /sys/module/nvidia_uvm/parameters/uvm_disable_hmm 2>/dev/null)" = "1" ] || { echo "nvidia_uvm is not loaded with uvm_disable_hmm=1" >&2; exit 1; }
# CUDA smoke: a real CUDA process (Cycles) that allocates on the device and exits. The exit path is what crashed before.
rm -f /tmp/oryx-gpu-smoke.png
flock /tmp/oryx-gpu.lock blender --background --factory-startup --python-expr "
import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='CUDA'; p.get_devices()
for d in p.devices: d.use = d.type == 'CUDA'
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='GPU'; s.cycles.samples=8; s.render.resolution_percentage=10
s.render.filepath='/tmp/oryx-gpu-smoke.png'; bpy.ops.render.render(write_still=True)"
test -s /tmp/oryx-gpu-smoke.png
journalctl -k --since -2min --no-pager 2>/dev/null | grep -qiE 'BUG:|Oops|nvidia_uvm.*fault' && { echo "kernel fault after the CUDA process exited" >&2; exit 1; }
echo "oryx GPU OK"
```

- [ ] **Step 3: Verify.** Run it twice in a row; both print `oryx GPU OK` and `nvidia-smi` afterwards shows no lingering process. Post the output on issue #4.
- [ ] **Step 4:** If the check fails after the reboot, Tasks 6 and 11 use their CPU fallbacks (stated in each) and `bakeoff/control/LOG.md` records the blocker. Commit the script and the AGENTS.md line on `phase1/oryx-gpu`; open the PR.

### Task 1: Shared inputs — docs, level, formats, `tools/greybox`

**Files:**
- Create: `docs/bakeoff/README.md`, `docs/bakeoff/mechanic.md`, `docs/bakeoff/greybox-format.md`, `docs/bakeoff/level01.greybox.json`, `docs/bakeoff/replay-format.md`, `docs/bakeoff/protagonist-brief.md`, `docs/bakeoff/desert-biome-brief.md`, `docs/bakeoff/judging.md`, `docs/bakeoff/lane-log-format.md`
- Create: `tools/greybox/pyproject.toml`, `tools/greybox/src/greybox/__init__.py`, `tools/greybox/src/greybox/cli.py`, `tools/greybox/tests/test_greybox.py`

**Interfaces:**
- Produces: the level file and the three formats (`violet-greybox` v1, `violet-replay` v1, lane log front matter) every lane and Task 2 consume; `uv run --project tools/greybox greybox check LEVEL` (exit 1 with one problem per line) and `greybox render LEVEL --out PNG [--scale 8]`.

- [ ] **Step 1:** `jj new master -m "Bake-off shared inputs: throwaway mechanic, greybox level, briefs, judging sheet"`.
- [ ] **Step 2:** Write `docs/bakeoff/README.md`: a THROWAWAY banner ("Everything under docs/bakeoff, assets/bakeoff, bakeoff/ and the bakeoff/* branches exists only to run the Phase 1 bake-off. Mechanics are undecided (decision 0009); nothing here is canon."), the lane table from the spec, the directory conventions above, and links to every file below.
- [ ] **Step 3:** Write `docs/bakeoff/mechanic.md` (THROWAWAY test mechanic, exactly this):
  - Colors: `red`, `green`. Neutral geometry is always solid.
  - Touching an orb acquires its color and makes it **active**. `Q` cycles the active color through the acquired ones. Active is `""` until the first orb.
  - Red active grants **dash**: `Shift`, 30 tiles/s for 12 ticks (0.2 s, 6 tiles) in the facing direction, gravity suspended during the dash, one air-dash per airborne period (resets on landing; ground dashes unlimited). Green active grants **double-jump**: one extra jump per airborne period at full jump speed.
  - Tagged geometry (`wall_red`, `wall_green`, `platform_red`, `platform_green`): while its color is active it has no collision (walls are passed through, platforms cannot be landed on); otherwise solid. Only one color is active, so red and green are never passable at once.
  - Reveal: tagged elements of an unacquired color render grayscale; acquired → their color; active → brighter, pulsing. World saturation (a global post effect) is 0.35 with no color, 0.7 with one, 1.0 with both. The scarf shows the active color (gray when none).
  - Hazard cells (`^`) reset the player to the start (colors kept) in play; in a replay they fail the run. Goal cell: the run is complete.
  - Tuning (tiles and seconds; all lanes use these numbers): gravity 40 t/s²; run speed 8 t/s; jump speed 15.5 t/s (apex 3.0 t, running jump clears ≤ 6 t); dash 30 t/s × 0.2 s; player box 0.8 × 1.6 t with origin at the feet; 60 Hz ticks; velocity integrated per tick.
  - Controls: `A`/`←` left, `D`/`→` right, `Space` jump, `Shift` dash, `Q` switch, `R` restart, `Esc` quit. Camera keeps the whole level height in view at 1920×1080 (30 × 17 tiles visible), clamped to the level.
- [ ] **Step 4:** Write `docs/bakeoff/greybox-format.md`: `violet-greybox` v1 = `{"format","version":1,"tile_size_px":64,"legend":{char:kind},"rows":[string]}`; rows are top-to-bottom, equal length, one char per cell; kinds: `empty solid wall_red wall_green platform_red platform_green start goal orb_red orb_green hazard`; exactly one `start` and one `goal`; a tagged color requires its orb. Cell (col,row) → Godot 2D center `((col+0.5)·ts, (row+0.5)·ts)` (y down); Godot 3D and Unity center `(col+0.5, H−row−0.5, 0)` in metres (y up). Why this and not LDtk or YAML: both engines parse JSON natively (`JSON.parse_string`, Newtonsoft), neither parses YAML without a library; LDtk's JSON needs `defs`, `layerInstances`, `intGridCsv` and a Linux editor its author calls experimental, and its Godot importer is unmaintained (research README). Phase 2 picks the real level pipeline.
- [ ] **Step 5:** Write `docs/bakeoff/level01.greybox.json` (72 × 16; ground at rows 13–15; a 9-tile dash pit at cols 19–27; a full-height red wall at col 33; a 5-tile double-jump step at col 43; a green wall at col 48; a 3-tile gap at 50–52; red platforms at 53–56 that must be stood on with green active; a red wall at col 57 passed mid-air with red active; goal at col 69):

```json
{
  "format": "violet-greybox", "version": 1, "tile_size_px": 64,
  "legend": {".": "empty", "#": "solid", "R": "wall_red", "G": "wall_green", "r": "platform_red", "g": "platform_green",
             "S": "start", "E": "goal", "1": "orb_red", "2": "orb_green", "^": "hazard"},
  "rows": [
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R..............G........R.............#",
    "#................................R.........#######...rrrr#######.......#",
    "#................................R.........#######......#######.......#",
    "#.............1..................R.........#######......#######.......#",
    "#.............##.................R.........#######......#######.......#",
    "#.S.....##....##.................R.....2...#######......#######.....E.#",
    "###################.........######################.......###############",
    "###################.........######################.......###############",
    "###################^^^^^^^^^######################^^^^^^^###############"
  ]
}
```

- [ ] **Step 6:** Write `docs/bakeoff/replay-format.md`: `violet-replay` v1 = `{"format","version":1,"tick_hz":60,"level":"<path inside the lane project>","inputs":[{"from":T1,"to":T2,"hold":[action...]} | {"at":T,"press":[action...]}],"asserts":[{"cell":[c,r],"active_color":"red","passable":"wall_red"}],"expect":{"goal_by_tick":N}}`. Actions: `left right jump dash switch`. A tick's pressed set is the union of segments covering it; the runner presses an action on the first tick it appears and releases it on the first tick it is absent (so two `press` entries on consecutive ticks merge; leave a gap tick). An assert fires the first time the player's feet cell equals `cell`; `active_color` must match then; `passable` names a tagged legend kind, and every tagged body of that kind's color (wall and platform alike) must have collision disabled at that moment while every tagged body of the other color is enabled, as the mechanic says; an assert that never fires is a failure. The run passes when the goal is reached by `goal_by_tick` with no hazard touch and no failed assert. `--disable=dash|double_jump` makes the named ability a no-op so a lane can prove its replay depends on the mechanic. In capture mode the runner keeps going to the last input tick (pad idle segments so captures reach 60–90 s).
- [ ] **Step 7:** Write `docs/bakeoff/protagonist-brief.md` (THROWAWAY): Violet, a slight traveller about 4.5 heads tall in a long hooded robe in muted warm gray (`#8a8078`) with darker hem, bare feet or soft wraps, and a long scarf (three segments, ends trailing 1.5× head length) that is the only saturated element: gray when no color is active, the active color otherwise. Painted, soft-edged, GRIS / Planet of Lana register; no outlines, no anime line work, no pixel art. Silhouette must read at 100 px tall. Body parts painted once each, all facing right, on transparent background: `head`, `torso`, `hips`, `arm_back_upper`, `arm_back_lower`, `arm_front_upper`, `arm_front_lower`, `leg_back_upper`, `leg_back_lower`, `leg_front_upper`, `leg_front_lower`, `scarf1`, `scarf2`, `scarf3`. The Phase 0 head-scarf concept in `assets/concept/` is the reference input.
- [ ] **Step 8:** Write `docs/bakeoff/desert-biome-brief.md` (THROWAWAY): golden-hour high desert; ochre dunes, layered sandstone mesas, wind-cut arches, dry acacia and saguaro silhouettes; sky peach → teal; palette sand `#d9b27c`, rock `#a86f46`, shadow violet `#5a4a7a`, sky `#f2c49b`/`#3f7f8c`; tagged elements are crystal: ember red `#e04a3a`, verdant green `#3fbf6a`, gray `#8c8c8c` until acquired. Kit lists: **3D** (`assets/bakeoff/desert-kit-3d/`): `mesa-large`, `mesa-small`, `arch`, `boulder-a`, `boulder-b`, `saguaro`, `acacia`, `dune-ridge`, `ruin-column`, `ruin-wall`, `sand-tile`, `rock-tile`, `crystal-cluster` (untinted), `orb-pedestal`, `goal-gate`, `hazard-spikes`; **2D painted** (G-A): `ground-tile`, `wall-tile`, `platform-tile`, `crystal-wall`, `crystal-platform`, `orb`, `goal-gate`, `hazard-tile`, `backdrop-far`, `backdrop-mid`, `backdrop-near`; **SVG** (G-C): the same eleven as flat vector. The hazard pieces dress `hazard` cells: jagged sandstone spikes in rock and shadow violet, never the tag red or green.
- [ ] **Step 9:** Write `docs/bakeoff/judging.md`: Sami scores each lane 1–5 against the GRIS / Planet of Lana bar on `visual_quality`, `character_appeal`, `color_readability`, and answers `would_ship` yes/no ("would you ship this direction?"); if no D lane gets yes he also answers `prefers_c_over_a`. Control is scored for information and does not enter the rule. Decision rule verbatim from the spec: D wins if Sami answers yes for at least one D lane; otherwise A wins, and C instead only if Sami prefers it. The engine is whichever lane Sami scored higher for the winning direction (sum of the three scores, among that direction's lanes with yes); a tie goes to Godot. Scoring happens as one comment on the judging PR in the block format `lane: g-a | visual_quality: 4 | character_appeal: 3 | color_readability: 4 | would_ship: no | notes: ...`; the lead transcribes it into `docs/bakeoff/scores.json` (schema in Task 2) citing the comment URL.
- [ ] **Step 10:** Write `docs/bakeoff/lane-log-format.md`: `bakeoff/<lane>/LOG.md` starts with YAML front matter `lane, direction (A|C|D|control), engine (godot|unity|blender), machine, status (in-progress|delivered|blocked), sessions: [{start, end, purpose}] (ISO-8601 UTC), costs: [{item, usd, evidence}], interventions: [{at, who, what, minutes}] (anything a human did or was asked), friction: [{at, what, workaround}] (engine/MCP/tool trouble), blockers: [{what, since, waiting_on}], deliverables: {build, capture, stills: [], tests}` followed by free-form notes. Agent-hours = Σ(end − start). Shared costs (Spine, the kit, the rig) go in `docs/bakeoff/shared-costs.md` on master, not in a lane.
- [ ] **Step 11:** Create `tools/greybox` (copy `tools/gen/pyproject.toml` shape: `requires-python>=3.12`, deps `pillow>=11`, script `greybox = "greybox.cli:main"`, `uv_build`). `cli.py`:

```python
"""greybox check|render: validate and picture a violet-greybox level (docs/bakeoff/greybox-format.md). THROWAWAY bake-off tooling."""
import argparse, json, sys
from pathlib import Path
from PIL import Image, ImageDraw
KINDS = {"empty", "solid", "wall_red", "wall_green", "platform_red", "platform_green", "start", "goal", "orb_red", "orb_green", "hazard"}
COLORS = {"empty": (245, 240, 230), "solid": (90, 80, 70), "wall_red": (200, 60, 50), "wall_green": (60, 170, 90), "platform_red": (230, 120, 110),
          "platform_green": (120, 210, 150), "start": (40, 120, 220), "goal": (240, 200, 40), "orb_red": (255, 30, 30), "orb_green": (30, 220, 80), "hazard": (20, 20, 20)}
NEEDS_ORB = {"wall_red": "orb_red", "platform_red": "orb_red", "wall_green": "orb_green", "platform_green": "orb_green"}

def load(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("format") != "violet-greybox" or data.get("version") != 1:
        raise SystemExit(f"{path}: not a violet-greybox v1 file")
    return data

def check(level: dict) -> list[str]:
    problems, rows, legend = [], level["rows"], level["legend"]
    width = len(rows[0]); counts: dict[str, int] = {}
    for r, row in enumerate(rows):
        if len(row) != width:
            problems.append(f"row {r}: {len(row)} columns, expected {width}")
        for c, ch in enumerate(row):
            kind = legend.get(ch)
            if kind is None: problems.append(f"row {r} col {c}: character {ch!r} is not in the legend"); continue
            if kind not in KINDS: problems.append(f"legend {ch!r}: unknown kind {kind}")
            counts[kind] = counts.get(kind, 0) + 1
    for single in ("start", "goal"):
        if counts.get(single, 0) != 1: problems.append(f"expected exactly one {single}, found {counts.get(single, 0)}")
    for tagged, orb in NEEDS_ORB.items():
        if counts.get(tagged) and not counts.get(orb): problems.append(f"{tagged} is used but there is no {orb}")
    if level["tile_size_px"] not in (32, 64, 128): problems.append("tile_size_px must be 32, 64 or 128")
    return problems

def render(level: dict, out: Path, scale: int) -> None:
    rows, legend = level["rows"], level["legend"]
    img = Image.new("RGB", (len(rows[0]) * scale, len(rows) * scale), COLORS["empty"]); draw = ImageDraw.Draw(img)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            draw.rectangle([c * scale, r * scale, (c + 1) * scale - 1, (r + 1) * scale - 1], fill=COLORS[legend[ch]])
    out.parent.mkdir(parents=True, exist_ok=True); img.save(out)

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="greybox"); sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("level", type=Path)
    r = sub.add_parser("render"); r.add_argument("level", type=Path); r.add_argument("--out", type=Path, required=True); r.add_argument("--scale", type=int, default=8)
    a = p.parse_args(argv); level = load(a.level)
    if a.cmd == "check":
        problems = check(level); print(*problems, sep="\n", file=sys.stderr); print(f"greybox check: {len(problems)} problem(s)"); return 1 if problems else 0
    if check(level): return main(["check", str(a.level)])
    render(level, a.out, a.scale); print(f"wrote {a.out}"); return 0
```

- [ ] **Step 12:** Tests `tools/greybox/tests/test_greybox.py` (pytest, in-memory dicts via `check`/`render`): ragged rows → "columns" problem; a character missing from the legend → problem naming it; two goals → problem; `wall_red` without `orb_red` → problem; the real `docs/bakeoff/level01.greybox.json` → zero problems; `render` writes a PNG of `(72·4) × (16·4)` at `--scale 4`. Run `uv run --project tools/greybox pytest tools/greybox/tests -v`: all pass.
- [ ] **Step 13: Verify.** `uv run --project tools/greybox greybox check docs/bakeoff/level01.greybox.json` prints `0 problem(s)`; `greybox render ... --out out/level01.png` then look at the PNG: the pit, the two walls, the step, the platforms and the goal sit where Step 5 says.
- [ ] **Step 14:** Commit, push `phase1/shared-inputs`, open the PR. Body: the THROWAWAY statement, the rendered level PNG inline (via `preview build`/`publish` for this PR), the tuning table, and "approve to unblock every lane". Sami's approval is the go signal for Tasks 7–8.

### Task 2: `tools/bakeoff` — log-check, decide, gallery, results-md

**Files:**
- Create: `tools/bakeoff/pyproject.toml` (deps `pyyaml>=6`), `tools/bakeoff/src/bakeoff/{__init__,cli,log,decide,gallery}.py`, `tools/bakeoff/tests/{test_decide,test_log}.py`, `tools/bakeoff/tests/fixtures/scores-*.json`, `docs/bakeoff/lane-log-template.md`, `docs/bakeoff/scores.schema.json`

**Interfaces:**
- Consumes: lane logs per `docs/bakeoff/lane-log-format.md`; `bakeoff/<lane>/reports/` files written by each lane's `ci.sh` (Tasks 7–11); `preview build|publish` (issue #8).
- Produces: `bakeoff log-check LOG...` (exit 1 on schema problems); `bakeoff decide SCORES` (prints `{"direction","engine","winning_lane","reason"}`); `bakeoff gallery --pr N [--lanes-dir DIR]` (lanes read from `DIR/<lane>/`, default `bakeoff/`; writes `out/review/pr-N/bakeoff.html` next to `preview build`'s `index.html`; caller publishes); `bakeoff results-md --pr N [--lanes-dir DIR] > docs/bakeoff/results.md`.

- [ ] **Step 1:** `log.py`: `parse(path) -> dict` splits `---` front matter with `yaml.safe_load`; `problems(front) -> list[str]` checks every field of the format doc (required keys, enums, ISO timestamps parse with `datetime.fromisoformat`, `end >= start`, numeric `usd`/`minutes`); `metrics(front) -> dict` returns `agent_hours` (Σ sessions), `usd` (Σ costs), `interventions` and `intervention_minutes`, `friction`, `blockers`, `status`.
- [ ] **Step 2:** `decide.py`, the rule verbatim:

```python
D_LANES = {"g-d": "godot", "u-d": "unity"}
def total(s): return s["visual_quality"] + s["character_appeal"] + s["color_readability"]
def decide(scores: dict) -> dict:
    lanes = scores["lanes"]
    d_yes = {lane: s for lane, s in lanes.items() if lane in D_LANES and s["would_ship"]}
    if d_yes:
        lane = max(d_yes, key=lambda l: (total(d_yes[l]), l == "g-d"))  # tie goes to Godot
        return {"direction": "D", "engine": D_LANES[lane], "winning_lane": lane, "reason": f"would_ship=yes for {sorted(d_yes)}; highest total {total(d_yes[lane])} ({lane})"}
    if scores.get("prefers_c_over_a") is True:
        return {"direction": "C", "engine": "godot", "winning_lane": "g-c", "reason": "no D lane got yes; Sami prefers C over A"}
    return {"direction": "A", "engine": "godot", "winning_lane": "g-a", "reason": "no D lane got yes; A is the default"}
```

`docs/bakeoff/scores.schema.json`: object with `scored_by`, `scored_at`, `source` (URL of Sami's comment), `prefers_c_over_a` (bool|null), `lanes` {lane → `{visual_quality, character_appeal, color_readability: int 1–5, would_ship: bool, notes: str}`}; `decide` validates against it (`jsonschema`, as `tools/provenance` does) before applying the rule.

- [ ] **Step 3:** `gallery.py`: `build(pr, lanes_dir, repo_root, out)` gathers for each `<lanes_dir>/<lane>/`: metrics, reports (Godot: last JSON line of `reports/replay.json` must have `ok: true`, `reports/replay-no-dash.json` `ok: false`, `reports/tags.txt` last line `tag-check: 0 problem(s)`, `reports/tags-mutated.txt` a positive count, `reports/build.txt` present; Unity: `reports/playmode.xml` parsed as NUnit3, `failed == 0` and the four required test names present, `reports/build.log` contains `Build succeeded`; Control: `reports/render.json`), copies `capture/capture.mp4` and `capture/still-*.png` to `out/lanes/<lane>/`, reads `docs/bakeoff/scores.json` if present, and writes `bakeoff.html`: one row per lane — direction, engine, machine, status, build ✓/✗, replay ✓/✗, no-dash-fails ✓/✗, tags ✓/✗, mutation-fails ✓/✗, agent-hours, USD, interventions (count/min), friction, blockers, `<video controls>` capture, stills, then Sami's four scores or "unscored", then notes; a header links the lane branch tree `https://github.com/sjawhar/project-violet/tree/bakeoff/<lane>`, its latest Actions run (`gh api repos/sjawhar/project-violet/actions/runs?branch=bakeoff/<lane>&per_page=1`), and `docs/bakeoff/judging.md`. Then it runs `uv run --project tools/preview preview build <pr> <every capture and still>` so `index.html` (GIFs, contact sheets) sits beside it. `results-md` renders the same table as Markdown with the gallery URL `https://sjawhar.github.io/project-violet/review/pr-<n>/bakeoff.html`.
- [ ] **Step 4:** `docs/bakeoff/lane-log-template.md`: the front matter with every key present, `status: in-progress`, empty lists, and a one-line example per list in a comment.
- [ ] **Step 5:** Tests. `test_decide.py` over fixtures: yes only for `u-d` → Unity/D; yes for both with equal totals (`scores-d-tie.json`) → Godot/D; yes for both, `u-d` higher → Unity/D; both no + `prefers_c_over_a: true` → C/godot/`g-c`; both no + `false`/missing → A/godot/`g-a`; a lane score of 6 fails schema validation. `test_log.py`: the template passes `problems`; a missing `sessions` key, a non-ISO `start`, `end < start`, and `status: done` each produce one named problem; `metrics` on two sessions of 90 min = `agent_hours == 3.0` and sums `usd`. `uv run --project tools/bakeoff pytest tools/bakeoff/tests -v` all pass.
- [ ] **Step 6: Verify.** `uv run --project tools/bakeoff bakeoff decide tools/bakeoff/tests/fixtures/scores-d-tie.json` prints `"engine": "godot"`. `bakeoff log-check docs/bakeoff/lane-log-template.md` prints `0 problem(s)`. Commit, push `phase1/bakeoff-tool`, open the PR.

### Task 3: Bake-off CI, Godot fetch script, capture scripts

**Files:**
- Create: `.github/workflows/bakeoff.yml`, `scripts/godot-fetch.sh`, `scripts/capture-godot.sh`, `scripts/capture-unity.sh`
- Modify: `.gitignore` (add `game/*/bin/` — the spine GDExtension binaries are fetched, not committed)

**Interfaces:**
- Produces: `scripts/godot-fetch.sh PROJECT_DIR` (idempotent: export templates into `~/.local/share/godot/export_templates/4.7.2.stable/`, spine-godot GDExtension 4.3 for Godot 4.7.2 into `PROJECT_DIR/bin/`); `scripts/capture-godot.sh LANE [ART]` and `scripts/capture-unity.sh` (Task 9 defines the Unity player flags); the CI contract: `game/<lane>/ci.sh` exits 0 and writes `bakeoff/<lane>/reports/*`.

- [ ] **Step 1:** `scripts/godot-fetch.sh`:

```bash
#!/usr/bin/env bash
# Installs what a Godot bake-off lane needs beyond mise's godot 4.7.2: export templates and the spine-godot GDExtension.
set -euo pipefail
GODOT=4.7.2; SPINE=4.3; project="${1:?usage: godot-fetch.sh PROJECT_DIR}"
tpl="$HOME/.local/share/godot/export_templates/$GODOT.stable"
if [ ! -f "$tpl/linux_release.x86_64" ]; then
  tmp=$(mktemp -d); curl -fsSL -o "$tmp/t.tpz" "https://github.com/godotengine/godot/releases/download/$GODOT-stable/Godot_v$GODOT-stable_export_templates.tpz"
  mkdir -p "$tpl"; unzip -q -j "$tmp/t.tpz" 'templates/*' -d "$tpl"; rm -rf "$tmp"; fi
if [ ! -f "$project/bin/spine_godot_extension.gdextension" ]; then
  tmp=$(mktemp -d); curl -fsSL -o "$tmp/s.zip" "https://spine-godot.s3.eu-central-1.amazonaws.com/$SPINE/$GODOT-stable/spine-godot-extension-$SPINE-$GODOT-stable.zip"
  unzip -q "$tmp/s.zip" -d "$tmp/s"; mkdir -p "$project/bin"; cp -r "$tmp"/s/bin/. "$project/bin/"; rm -rf "$tmp"; fi
echo "godot-fetch: templates in $tpl; spine-godot in $project/bin"
```

(The S3 URL pattern and the 4.7.2-stable build are what esotericsoftware.com/spine-godot's download script and `spine-runtimes/.github/workflows/spine-godot-extension-v4-all.yml` on branch 4.3 publish; if the zip's top level is not `bin/`, adjust the `cp` to whatever `unzip -l` shows and note it in the script.)

- [ ] **Step 2:** `.github/workflows/bakeoff.yml`:

```yaml
name: bakeoff
on:
  push:
    branches: ['bakeoff/**']
permissions:
  contents: read
jobs:
  lane:
    runs-on: ubuntu-24.04
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { lfs: true, persist-credentials: false }
      - uses: jdx/mise-action@<sha of the current v2 tag: gh api repos/jdx/mise-action/git/ref/tags/v2 --jq .object.sha>
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
      - name: Provenance and LFS
        run: uv run --locked --project tools/provenance provenance check && uv run --locked --project tools/provenance provenance lfs-check
      - name: Lane log
        run: uv run --locked --project tools/bakeoff bakeoff log-check "bakeoff/${GITHUB_REF_NAME#bakeoff/}/LOG.md"
      - name: Lane checks
        run: bash "game/${GITHUB_REF_NAME#bakeoff/}/ci.sh"
      - uses: actions/upload-artifact@<sha of the current v4 tag>
        if: ${{ !cancelled() }}
        with: { name: "${{ github.ref_name }}", path: "out/\nbakeoff/*/reports/" }
```

(`tools/bakeoff` is on master before any lane pushes, so `--locked` resolves.)

- [ ] **Step 3:** `scripts/capture-godot.sh LANE [ART]`: renders on the display when `$DISPLAY` is set, otherwise in software under Xvfb, which is how CI and the oryx captures run:

```bash
#!/usr/bin/env bash
# Records a lane's replay with Godot's Movie Maker (offline, frame-exact) and cuts stills. Run on machine sami.
set -euo pipefail
lane="${1:?usage: capture-godot.sh LANE [ART_TRES]}"; art="${2:-res://art/lane_art.tres}"
proj="game/$lane"; out="bakeoff/$lane/capture"; mkdir -p "$out" "out/$lane"
runner=(godot --path "$proj" --write-movie "../../out/$lane/capture.avi" --fixed-fps 60 --resolution 1920x1080
        res://tests/replay_runner.tscn -- "--replay=res://replays/level01.replay.json" --capture "--art=$art")
if [ -z "${DISPLAY:-}" ]; then LIBGL_ALWAYS_SOFTWARE=1 VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json xvfb-run -a -s "-screen 0 1920x1080x24" "${runner[@]}"; else "${runner[@]}"; fi
ffmpeg -y -i "out/$lane/capture.avi" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "$out/capture.mp4"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/capture.mp4"); echo "capture: ${dur}s (must be 60-90)"
for t in 05 20 40 60; do ffmpeg -y -ss "$t" -i "$out/capture.mp4" -frames:v 1 "$out/still-$t.png"; done
```

- [ ] **Step 4: Verify** on machine sami with the Phase 0 tree: `scripts/godot-fetch.sh /tmp/gf-test` creates `/tmp/gf-test/bin/spine_godot_extension.gdextension` and the templates directory; a second run prints only the summary line. Push a throwaway `bakeoff/ci-smoke` bookmark containing `game/ci-smoke/ci.sh` (`echo ok`) plus a template `bakeoff/ci-smoke/LOG.md`; the workflow goes green (`gh run list --branch bakeoff/ci-smoke`); then `jj bookmark delete bakeoff/ci-smoke && jj git push --bookmark bakeoff/ci-smoke` (an agent-made smoke branch, not a lane). Commit `.gitignore`, scripts and workflow on `phase1/bakeoff-ci`; open the PR.

### Task 4: Protagonist concept and body parts (`gen image --background`)

**Files:**
- Modify: `tools/gen/src/gen/cli.py` (add `--background {transparent,opaque}`), `tools/gen/src/gen/providers/__init__.py` (Protocol gains `background: str | None`), `tools/gen/src/gen/providers/openai.py` (pass `background` and `output_format: "png"` in both the generations JSON and the edits form), `tools/gen/src/gen/providers/gemini.py` (raise `ProviderError("gemini: --background is not supported ...")` when set), `tools/gen/README.md`, `tools/gen/tests/test_argparse.py`, `tools/gen/tests/test_live.py`
- Create: `assets/bakeoff/protagonist/concept/violet-turnaround.png` (+ sidecar), `assets/bakeoff/protagonist/parts/<part>.png` × 14 (+ sidecars), `assets/bakeoff/protagonist/README.md`

**Interfaces:**
- Consumes: `gen image` (PR #10), `assets/concept/*.png` from the Phase 0 smoke test as `--input`.
- Produces: the 14 part PNGs with alpha, named exactly as the brief lists, which Task 5's `rig.json` references by file name.

- [ ] **Step 1:** `gen` change. Add the flag and kwarg; OpenAI: `payload["background"] = background` (JSON) / `data["background"] = background` (multipart), plus `output_format: "png"`; the adapter already records `body["background"]` into `params`. Argparse test: `--background transparent` parses; `--background pink` exits 2. Unit test: gemini with `background="transparent"` raises. Live test (`-m live`): OpenAI `--background transparent` result satisfies `Image.open(p).getchannel("A").getextrema()[0] < 255`. Run: `uv run --project tools/gen pytest` and `secrets OPENAI_API_KEY GEMINI_API_KEY -- uv run --project tools/gen pytest -m live -v`. If the live API rejects `background` for `gpt-image-2`, use `--model gpt-image-1.5` (listed in `tools/gen/README.md`, sunset 2026-12-01) for the parts and say so in the README. PR `phase1/gen-background`, stacked on master.
- [ ] **Step 2:** Concept: `secrets OPENAI_API_KEY -- uv run --project tools/gen gen image --provider openai --model gpt-image-2 --input assets/concept/<the merged smoke-test PNG> --prompt "Character turnaround sheet, front and right-side view, of Violet: <the brief's first paragraph verbatim>, painted soft-edged style like GRIS and Planet of Lana, plain warm gray background, no text" --size 1536x1024 --out assets/bakeoff/protagonist/concept/violet-turnaround.png`. Repeat with `--force` and prompt tweaks until the two views agree in proportions (check by eye at 100 px: `magick violet-turnaround.png -resize x100 /tmp/small.png`). `preview build`/`publish` for the PR; open PR `phase1/protagonist-concept` titled "Bake-off protagonist concept (THROWAWAY) — approve the look before the rig is built". **Sami's approval here is the taste gate.**
- [ ] **Step 3:** Parts (after approval), one command per part, e.g. `secrets OPENAI_API_KEY -- uv run --project tools/gen gen image --provider openai --model gpt-image-2 --background transparent --input assets/bakeoff/protagonist/concept/violet-turnaround.png --prompt "Only the <part description> of the character in the reference, side view facing right, same painted style and palette, centred, nothing else, transparent background" --size 1024x1024 --out assets/bakeoff/protagonist/parts/<part>.png`, with descriptions: head "hooded head and neck", torso "robe torso from shoulders to waist", hips "robe skirt from waist to knee line", `arm_*_upper` "upper arm shoulder to elbow", `arm_*_lower` "forearm and hand", `leg_*_upper` "thigh under the robe hem", `leg_*_lower` "shin and foot", `scarf1..3` "one straight segment of the scarf, gray". Check each: `magick <part>.png -format '%[opaque]\n' info:` prints `False`; `uv run --project tools/provenance provenance check assets/bakeoff/protagonist` OK.
- [ ] **Step 4:** `assets/bakeoff/protagonist/README.md`: THROWAWAY, the part list with sizes (`magick identify`), which model made them, and that Task 5 consumes them. Commit (`git lfs push origin phase1/protagonist-parts` first), open PR `phase1/protagonist-parts` stacked on the concept PR, with the `preview` contact sheet inline.

### Task 5: Spine rig — `tools/spinerig` and the shared protagonist export

**Files:**
- Create: `tools/spinerig/pyproject.toml` (deps `pillow>=11`, `provenance` path dep), `tools/spinerig/src/spinerig/{__init__,cli,generate,render,scarf}.py`, `tools/spinerig/tests/{test_generate,test_render}.py`, `tools/spinerig/README.md`, `docs/bakeoff/character-rig.md`
- Create: `assets/bakeoff/protagonist/rig-src/rig.json` (agent-authored), `assets/bakeoff/protagonist/rig/{violet.json,violet.meta.json}` (+ sidecars), `assets/bakeoff/protagonist/preview/<anim>/*.png`

**Interfaces:**
- Consumes: Task 4's parts.
- Produces: `rig/violet.json` (a Spine-4.3-JSON subset skeleton — no Spine editor, no atlas, no packed texture; the exact shape is `docs/bakeoff/character-rig.md`'s contract — animations `idle run jump fall double_jump dash land`, slots `scarf1..3`), `rig/violet.meta.json` = `{"height_px", "feet_y_px", "facing"}` (`spinerig generate`'s `--out`'s stem + `.meta.json`) read by every engine to compute scale = 1.6 tiles / H. Every lane reads `violet.json` and the part PNGs directly with its own small reader, per `docs/bakeoff/character-rig.md`.

- [ ] **Step 1:** `spinerig generate RIG.json --out OUT.json [--print-parts]` (`generate.py`). `rig.json` (`violet-rig` v1): `parts_dir`, `bones: [{name, parent?, x?, y?, rotation?, length?}]` (Spine conventions: y up, degrees, parent before child), `parts: [{slot, bone, image, pivot: [px, py], rotation}]` where `pivot` is the point of the image (0–1, origin bottom-left) that sits on the bone origin and `rotation` is the image's up-axis relative to the bone, `draw_order: [slot...]`, `scarf: {bones: [...], trail_deg: {anim: deg}, flutter_deg, flutter_hz, lag_frames, gain: [1.0, 0.75, 0.5]}`, `animations: {name: {"duration": s, "bones": {bone: {"rotate": [{time, angle}], "translate": [{time, x, y}]}}}}`. The generator reads each image's size with Pillow, emits Spine JSON `{skeleton: {spine: "4.3.00", x, y, width, height, images: "../parts/"}, bones, slots (attachment = slot name), skins: [{name: "default", attachments: {slot: {slot: {x, y, rotation, width, height}}}}], animations}` where the attachment offset is the image centre relative to the pivot rotated into bone space: `dx = (0.5 - px) * w, dy = (0.5 - py) * h; x = dx*cos(rot) - dy*sin(rot); y = dx*sin(rot) + dy*cos(rot)`. It adds scarf rotate keys per animation (`scarf.py`): for bone *i* of the chain, `angle_i(t) = -gain_i * trail_deg[anim] + gain_i * flutter_deg * sin(2π·flutter_hz·(t - i·lag_frames/30))`, sampled every 2 frames at 30 fps, looped for loop animations — the delayed, damped follow-through `spine-animation-ai` produces, reimplemented. It also writes `violet.meta.json` with the setup-pose height from the attachment bounds. `--print-parts` prints each part's file, width and height so the author can pick bone lengths.
- [ ] **Step 2:** Tests: a two-bone rig with one 100×200 part at pivot `[0.5, 0]` and rotation 0 places the attachment at `x=0, y=100`; rotation 90 gives `x=-100, y≈0`; scarf keys for a 3-bone chain have decreasing amplitude and increasing phase; a part whose image file is missing raises with the file name; every animation in `rig.json` appears in the output. `uv run --project tools/spinerig pytest -v` passes.
- [ ] **Step 3:** Author `assets/bakeoff/protagonist/rig-src/rig.json`: bones `root; hips(root, y=+leg length); torso(hips, rotation 90, length ≈ torso image height); head(torso, x=torso length, length ≈ head height); scarf1(head, rotation -150, length ≈ scarf segment); scarf2(scarf1, x=length); scarf3(scarf2, x=length); arm_back_upper/lower(torso, rotation -160, then x=length); arm_front_upper/lower(same, drawn in front); leg_back_upper/lower(hips, rotation -95, then x=length); leg_front_upper/lower(hips, rotation -85, ...)` with lengths taken from `--print-parts`; draw order back-arm, back-leg, hips, torso, front-leg, head, scarf1..3, front-arm. Animations (all bone keys, angles in degrees): `idle` 1.0 s loop (torso ±2, head ∓2, hips y ±3); `run` 0.6 s loop (legs swing ±35 alternating, arms ∓25, hips y −4 at 0.15/0.45); `jump` 0.5 s (legs tuck +45/−20, arms up −60, torso +8); `fall` 0.6 s loop (legs spread, arms out); `double_jump` 0.5 s (a 360° `hips` rotate over 0.35 s then settle); `dash` 0.2 s (torso −25 lean, arms back, legs stretched); `land` 0.25 s (torso +15 crouch, hips y −10, back to 0). `scarf.trail_deg`: idle 5, run 35, jump 20, fall −15, double_jump 40, dash 70, land 10; `flutter_deg` 8, `flutter_hz` 2.5, `lag_frames` 2. Run `uv run --project tools/spinerig spinerig generate assets/bakeoff/protagonist/rig-src/rig.json --out /tmp/violet.draft.json --print-parts` first, on a draft, to read each part's actual pixel width/height and pick the bone lengths above.
- [ ] **Step 4:** Once the rig reads right: `uv run --project tools/spinerig spinerig generate assets/bakeoff/protagonist/rig-src/rig.json --out assets/bakeoff/protagonist/rig/violet.json` writes `rig/violet.json` and `rig/violet.meta.json` — no Spine editor, no atlas, no texture packing. Check: `uv run --project tools/spinerig spinerig render assets/bakeoff/protagonist/rig/violet.json --parts assets/bakeoff/protagonist/parts --anim <anim> --out assets/bakeoff/protagonist/preview/<anim>` for every animation name in `rig.json` plays it back with Pillow (no Spine editor or runtime involved) to `preview/<anim>/frame_*.png` and `preview/<anim>/<anim>.gif` — the proof the rig actually animates before any engine touches it. Look at every GIF: parts do not detach, the scarf lags the torso, `land` squashes. Iterate on `rig.json` and re-run Step 3 until they read as motion, not as sliding cards. Commit `assets/bakeoff/protagonist/rig/violet.json`, `violet.meta.json`, and the part PNGs (`git lfs push` first).
- [ ] **Step 5:** Provenance: `provenance record assets/bakeoff/protagonist/rig-src/rig.json --kind animation --origin generated --license proprietary --tool omp --tool-version "$(omp --version)" --provider anthropic --model "<your model id from the harness>" --prompt "Authored from docs/bakeoff/protagonist-brief.md and docs/bakeoff/mechanic.md"`; `rig/violet.json` and `violet.meta.json` as `--origin derived --tool spinerig --no-model --input assets/bakeoff/protagonist/rig-src/rig.json` (`spinerig generate` is deterministic code, not a model). `provenance check assets/bakeoff/protagonist` OK.
- [ ] **Step 6:** Push, open PR `phase1/protagonist-rig` with the animation GIFs from `preview/` inline. Sami approves the rig; lanes swap the stand-in for it the same day.
- [ ] **Step 7 (optional):** Sami opens `assets/bakeoff/protagonist/rig/violet.json` in the Spine trial already installed on machine sami (`~/Applications/SpineTrial`, free, can't save or export) via **File > Import Data**, once, as a cross-check that the generated JSON is valid Spine 4.3 data. This is not a purchase and no lane's build depends on it succeeding.

### Task 6: `assets/bakeoff/desert-kit-3d/build_kit.py` — agent-authored 3D desert kit (Blender Python)

**Files:**
- Create: `assets/bakeoff/desert-kit-3d/build_kit.py`, `assets/bakeoff/desert-kit-3d/<piece>.glb` × 16 (every piece in the brief's 3D list, `hazard-spikes` included; + sidecars), `assets/bakeoff/desert-kit-3d/README.md`

**Interfaces:**
- Consumes: `docs/bakeoff/desert-biome-brief.md`'s 3D list and palette; Blender from `tools/preview/README.md`.
- Produces: one low-poly GLB per piece, modeled entirely with Blender's Python API (`bpy` primitives, modifiers and booleans — no external 3D generation API) in the biome palette, with `crystal-cluster` left pale gray and untinted (the lane's own shader tints it); each GLB's sidecar `origin derived`, `build_kit.py` itself `origin generated`.

- [ ] **Step 1:** Write `assets/bakeoff/desert-kit-3d/build_kit.py` (`blender --background --python build_kit.py -- --out assets/bakeoff/desert-kit-3d`): one function per piece in the brief's 3D list (`mesa_large`, `mesa_small`, `arch`, `boulder_a`, `boulder_b`, `saguaro`, `acacia`, `dune_ridge`, `ruin_column`, `ruin_wall`, `sand_tile`, `rock_tile`, `crystal_cluster`, `orb_pedestal`, `goal_gate`, `hazard_spikes`), each building a low-poly mesh from primitives and modifiers (`bpy.ops.mesh.primitive_*`, bevel, a low-level subdivision surface, boolean cuts for the arch and the ruin pieces) and a `Principled BSDF` material colored from `docs/bakeoff/desert-biome-brief.md`'s palette — `crystal_cluster()` gets a pale gray base color, untinted, since the engine's reveal shader tints it; every mesh kept low-poly (target ≤ 2000 triangles, a game-prop budget). `bpy.ops.export_scene.gltf(filepath=..., export_format="GLB")` per piece, wiping the scene between pieces (`bpy.ops.wm.read_factory_settings(use_empty=True)`). Provenance for the script itself: `provenance record assets/bakeoff/desert-kit-3d/build_kit.py --kind other --origin generated --license proprietary --tool omp --tool-version "$(omp --version)" --provider anthropic --model "<your model id from the harness>" --prompt "Built from docs/bakeoff/desert-biome-brief.md's 3D list and palette"`.
- [ ] **Step 2:** Run headless on CPU (agent-authored geometry needs no CUDA, so Task 0 does not gate this): `blender --background --python assets/bakeoff/desert-kit-3d/build_kit.py -- --out assets/bakeoff/desert-kit-3d` on oryx (or sami). Sanity: every GLB's first four bytes are `glTF`; each stays under the triangle target.
- [ ] **Step 3:** Turntables for the PR: `uv run --project tools/preview preview build <pr> assets/bakeoff/desert-kit-3d/*.glb --render-device cpu` (Eevee/Cycles CPU). Review the contact sheet: reject and regenerate pieces whose silhouette or palette breaks the set (edit the piece's function in `build_kit.py`, re-run Step 2; log the count).
- [ ] **Step 4:** Provenance for the GLBs: each `--origin derived --tool blender --tool-version "$(blender --version | head -1 | awk '{print $2}')" --no-model --input assets/bakeoff/desert-kit-3d/build_kit.py` (running an agent-authored script is not a model call). README (THROWAWAY, piece table, regeneration counts), `provenance check assets/bakeoff/desert-kit-3d` OK, `git lfs push`, PR `phase1/desert-kit-3d` with turntable GIFs inline.

### Task 7: Lane G-A — Godot 4.7.2 2D, painted world

**Files:**
- Create under `game/g-a/`: `project.godot`, `export_presets.cfg`, `ci.sh`, `levels/level01.greybox.json` (copy), `replays/level01.replay.json`, `bakeoff/{actions,resonance,greybox,replay,resonance_tag,greybox_builder_2d,greybox_art,player_2d,game_2d,tag_validator}.gd`, `tests/{replay_runner.gd,replay_runner.tscn,validate_tags.gd,validate_tags.tscn}`, `scenes/main.tscn`, `art/{painted_art.gd,lane_art.tres,spine_reader.gd,spine_character_2d.gd,saturation.gdshader,reveal.gdshader}`, `art/*.png` (generated), `protagonist/{violet.json,violet.meta.json,<part>.png × 14}` (+ sidecars, copied from `assets/bakeoff/protagonist/rig/` and `parts/`)
- Create: `bakeoff/g-a/LOG.md`, `bakeoff/g-a/replays/level01.replay.json`, `bakeoff/g-a/reports/`, `bakeoff/g-a/capture/`
- Create: `game/g-a/ci-tools` containing `godot`: the `mise.toml` tools the `bakeoff` workflow installs for this lane besides uv (`docs/bakeoff/README.md`, from Task 3). A missing file fails the workflow's first step.

**Interfaces:**
- Consumes: Task 1 formats and level; Task 3 scripts and CI contract; Task 5 rig (`assets/bakeoff/protagonist/rig/violet.json`, read directly — no Spine runtime, per `docs/bakeoff/character-rig.md`); `gen image` for the painted tiles and parallax backdrops.
- Produces: `GreyboxArt` (`extends Resource`; `make_cell(kind: String, cell: Vector2i, ts: float) -> Node2D`, `make_backdrop(level: Greybox) -> Node2D`, `attach_character(player: Node) -> void`) that Task 10 subclasses; the dimension-agnostic scripts (`greybox.gd`, `replay.gd`, `resonance.gd`, `resonance_tag.gd`, `tag_validator.gd`, `tests/replay_runner.gd`, `tests/validate_tags.gd`) that Task 8 copies with `jj file show -r bakeoff/g-a game/g-a/<path>`.

- [ ] **Step 1:** Workspace and skeleton: `jj workspace add --name g-a -r master ~/src/violet-g-a; cd ~/src/violet-g-a; jj bookmark create bakeoff/g-a -r @; mkdir -p game/g-a bakeoff/g-a/{replays,reports,capture}`; `cp docs/bakeoff/lane-log-template.md bakeoff/g-a/LOG.md` and fill `lane: g-a, direction: A, engine: godot, machine: oryx` and the first session; `cp docs/bakeoff/level01.greybox.json game/g-a/levels/`; `scripts/godot-fetch.sh game/g-a`.
- [ ] **Step 2:** `project.godot`:

```ini
config_version=5
[application]
config/name="violet bake-off lane G-A (THROWAWAY)"
run/main_scene="res://scenes/main.tscn"
config/features=PackedStringArray("4.7", "GL Compatibility")
[autoload]
Actions="*res://bakeoff/actions.gd"
Resonance="*res://bakeoff/resonance.gd"
[display]
window/size/viewport_width=1920
window/size/viewport_height=1080
[editor]
movie_writer/mjpeg_quality=1.0
[physics]
common/physics_ticks_per_second=60
common/physics_jitter_fix=0.0
common/physics_interpolation=false
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
[shader_globals]
world_saturation={"type": "float", "value": 0.35}
```

- [ ] **Step 3:** `bakeoff/actions.gd` (autoload): in `_enter_tree`, for `{"left": [KEY_A, KEY_LEFT], "right": [KEY_D, KEY_RIGHT], "jump": [KEY_SPACE], "dash": [KEY_SHIFT], "switch": [KEY_Q], "restart": [KEY_R], "quit": [KEY_ESCAPE]}` call `InputMap.add_action(name)` (if absent) and `InputMap.action_add_event(name, ev)` with `var ev := InputEventKey.new(); ev.physical_keycode = key`.
- [ ] **Step 4:** `bakeoff/resonance.gd` (autoload; THROWAWAY state):

```gdscript
extends Node
signal changed
const COLORS := ["red", "green"]
var acquired: Array[String] = []
var active := ""
var abilities_disabled: PackedStringArray = []
func acquire(color: String) -> void:
	if color not in acquired: acquired.append(color)
	active = color; _emit()
func cycle() -> void:
	if acquired.size() < 2: return
	active = acquired[(acquired.find(active) + 1) % acquired.size()]; _emit()
func reset() -> void:
	acquired.clear(); active = ""; abilities_disabled = []; _emit()
func has(color: String) -> bool: return color in acquired
func can_dash() -> bool: return active == "red" and not abilities_disabled.has("dash")
func can_double_jump() -> bool: return active == "green" and not abilities_disabled.has("double_jump")
func world_saturation() -> float: return [0.35, 0.7, 1.0][acquired.size()]
func _emit() -> void:
	RenderingServer.global_shader_parameter_set("world_saturation", world_saturation()); changed.emit()
```

- [ ] **Step 5:** `bakeoff/greybox.gd` — `class_name Greybox extends RefCounted` with `const KINDS`, `const TAGGED := {"wall_red": ["red", "wall"], "wall_green": ["green", "wall"], "platform_red": ["red", "platform"], "platform_green": ["green", "platform"]}`, `var tile_px: int, width: int, height: int, cells: Array[String]`, `static func load_file(path) -> Greybox` (`FileAccess.get_file_as_string`, `JSON.parse_string`, asserts on `format`/`version`, equal row lengths, legend kinds ∈ KINDS), `func kind_at(col, row) -> String` (out of range → `"solid"`), `func cells_of(kind) -> Array[Vector2i]`, `func single(kind) -> Vector2i` (asserts exactly one).
- [ ] **Step 6:** `bakeoff/replay.gd` — `class_name Replay extends RefCounted`: `var tick_hz: int, level_path: String, goal_by_tick: int, pressed: Array[PackedStringArray], asserts: Array[Dictionary]`; `static func load_file(path) -> Replay` sizes `pressed` to `max(goal_by_tick, last segment tick) + 1` and fills each covered tick from `hold`/`press` segments, asserting actions ∈ `["left","right","jump","dash","switch"]` and ticks in range.
- [ ] **Step 7:** `bakeoff/resonance_tag.gd`:

```gdscript
class_name ResonanceTag
extends Node
## Marks the parent body (CollisionObject2D or 3D) as color-tagged geometry. THROWAWAY.
@export var color: String
@export var kind: String
@export var cell: Vector2i
func _ready() -> void:
	add_to_group("resonance"); Resonance.changed.connect(_apply); _apply()
func _apply() -> void:
	var body := get_parent()
	var passable := Resonance.active == color
	body.collision_layer = 0 if passable else 1
	body.set_meta("resonance_passable", passable)
	for child in body.get_children():
		if child.has_method("set_resonance_look"): child.set_resonance_look(Resonance.has(color), passable)
```

- [ ] **Step 8:** `bakeoff/greybox_builder_2d.gd` — `class_name GreyboxBuilder2D`, `static func build(level: Greybox, root: Node2D, art: GreyboxArt) -> Dictionary`: for every non-empty cell at `pos = Vector2((c + 0.5) * ts, (r + 0.5) * ts)`: solids and tagged kinds → `StaticBody2D` named `"%s_%d_%d"`, `collision_layer = 1, collision_mask = 0`, a `CollisionShape2D` with `RectangleShape2D.size = Vector2(ts, ts)`, `art.make_cell(kind, cell, ts)` as child, and for tagged kinds a `ResonanceTag` child with `color/kind/cell` from `Greybox.TAGGED`; `start` → `info["start"] = Vector2(pos.x, (r + 1) * ts)` (feet on the cell floor); `goal/orb_red/orb_green/hazard` → `Area2D` with `collision_layer = 0, collision_mask = 2`, the same shape, `set_meta("kind", kind)`, `add_to_group(kind)`, the art child. Returns `info`.
- [ ] **Step 9:** `bakeoff/player_2d.gd` — `class_name Player2D extends CharacterBody2D`, constants `TILE := 64.0; GRAVITY := 40.0 * TILE; RUN_SPEED := 8.0 * TILE; JUMP_SPEED := 15.5 * TILE; DASH_SPEED := 30.0 * TILE; DASH_TICKS := 12`; `var facing := 1, dash_ticks_left := 0, air_dash_used := false, double_jump_used := false, died := false`; `signal reached_goal; signal touched_hazard`; `_ready`: `collision_layer = 2; collision_mask = 1;` a `CollisionShape2D` with `RectangleShape2D.size = Vector2(0.8 * TILE, 1.6 * TILE)` at `position = Vector2(0, -0.8 * TILE)` (origin at the feet); `_physics_process(delta)`:

```gdscript
	var dir := int(Input.is_action_pressed("right")) - int(Input.is_action_pressed("left"))
	if dir != 0: facing = dir
	if Input.is_action_just_pressed("switch"): Resonance.cycle()
	if is_on_floor(): air_dash_used = false; double_jump_used = false
	if dash_ticks_left > 0:
		dash_ticks_left -= 1; velocity = Vector2(facing * DASH_SPEED, 0)
	else:
		velocity.x = dir * RUN_SPEED
		velocity.y = minf(velocity.y + GRAVITY * delta, 3.0 * JUMP_SPEED)
		if Input.is_action_just_pressed("jump"):
			if is_on_floor(): velocity.y = -JUMP_SPEED
			elif Resonance.can_double_jump() and not double_jump_used: double_jump_used = true; velocity.y = -JUMP_SPEED
		if Input.is_action_just_pressed("dash") and Resonance.can_dash() and (is_on_floor() or not air_dash_used):
			if not is_on_floor(): air_dash_used = true
			dash_ticks_left = DASH_TICKS; velocity = Vector2(facing * DASH_SPEED, 0)
	move_and_slide()
```

plus `func cell() -> Vector2i: return Vector2i(floori(global_position.x / TILE), floori((global_position.y - 1.0) / TILE))` and `func on_area(area: Area2D)`: `orb_red` → `Resonance.acquire("red"); area.queue_free()`, `orb_green` likewise, `goal` → `reached_goal.emit()`, `hazard` → `died = true; touched_hazard.emit()`.

- [ ] **Step 10:** `bakeoff/greybox_art.gd` — `class_name GreyboxArt extends Resource`: `make_cell` returns a `Polygon2D` square (`polygon = PackedVector2Array([...four corners at ±ts/2])`) colored by kind (use Task 1's `COLORS`), with an inner script (`extends Polygon2D`, `var base: Color`, `func set_resonance_look(revealed, active)`: `color = base.lightened(0.35) if active else base if revealed else Color(0.55, 0.55, 0.55)`) attached to tagged kinds; `make_backdrop` returns a `ColorRect` (sand color) sized to the level behind everything (`z_index = -10`); `attach_character` adds a `Polygon2D` capsule (0.8 × 1.6 tiles, violet) and a `Label` reading `STAND-IN` above it — this is what runs until the rig lands.
- [ ] **Step 11:** `bakeoff/game_2d.gd` — `class_name Game2D extends Node2D`, `@export var level_path := "res://levels/level01.greybox.json"`, `@export var art: GreyboxArt`, `var level: Greybox, player: Player2D`; `_ready`: `Resonance.reset()`, load level, `if art == null: art = GreyboxArt.new()`, `add_child(art.make_backdrop(level))`, a `World` `Node2D` filled by `GreyboxBuilder2D.build(level, world, art)`, `player = Player2D.new(); player.position = info["start"]; add_child(player)`, connect every area in groups `goal/orb_red/orb_green/hazard`: `area.body_entered.connect(func(b): if b == player: player.on_area(area))`, `art.attach_character(player)`, a `Camera2D` child of the player (`position_smoothing_enabled = false`, `limit_left = 0, limit_top = 0, limit_right = level.width * 64, limit_bottom = level.height * 64`), a `CanvasLayer` with a full-screen `ColorRect` using `art/saturation.gdshader` (`shader_type canvas_item; uniform sampler2D screen : hint_screen_texture; global uniform float world_saturation; void fragment() { vec4 c = texture(screen, SCREEN_UV); float g = dot(c.rgb, vec3(0.299, 0.587, 0.114)); COLOR = vec4(mix(vec3(g), c.rgb, world_saturation), 1.0); }`), and `_unhandled_input`: `restart` → `get_tree().reload_current_scene()`, `quit` → `get_tree().quit()`; on `reached_goal` show a `Label` "GOAL — R to restart". `scenes/main.tscn` = root `Node2D` with `script = ExtResource("res://bakeoff/game_2d.gd")` and `art = ExtResource("res://art/lane_art.tres")`.
- [ ] **Step 12:** `bakeoff/tag_validator.gd` — the color-tag check (same logic Task 9 writes in C#):

```gdscript
class_name TagValidator
extends RefCounted
## Every tagged cell in the level has exactly one tagged body with the right color and kind; no body is
## tagged where the level has none; every tagged body has a visual that reacts. Empty result = OK.
static func validate(level: Greybox, tree: SceneTree) -> PackedStringArray:
	var problems: PackedStringArray = []; var seen := {}
	for tag in tree.get_nodes_in_group("resonance"):
		var body: Node = tag.get_parent(); var actual := "%s_%s" % [tag.kind, tag.color]
		var expected := level.kind_at(tag.cell.x, tag.cell.y)
		if expected != actual: problems.append("%s: tagged %s but the level has %s at %s" % [body.get_path(), actual, expected, tag.cell])
		var key := "%d,%d" % [tag.cell.x, tag.cell.y]
		if seen.has(key): problems.append("%s: second tag for cell %s" % [body.get_path(), tag.cell])
		seen[key] = true
		if body.get_children().filter(func(c): return c.has_method("set_resonance_look")).is_empty():
			problems.append("%s: no visual implements set_resonance_look" % body.get_path())
	for kind in Greybox.TAGGED:
		for cell in level.cells_of(kind):
			if not seen.has("%d,%d" % [cell.x, cell.y]): problems.append("cell %s: level has %s but the scene has no tagged body there" % [cell, kind])
	return problems
```

- [ ] **Step 13:** `tests/replay_runner.gd` (root of `tests/replay_runner.tscn`, a `Node2D`) — the completability test:

```gdscript
extends Node2D
## godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json [--trace] [--disable=dash,double_jump] [--capture] [--art=res://art/lane_art.tres]
## Exit 0: goal reached by expect.goal_by_tick, no hazard, every assert fired and held. Exit 1 otherwise. Last stdout line is a JSON report.
var replay: Replay; var game: Game2D; var tick := 0; var goal_tick := -1
var failures: PackedStringArray = []; var fired := {}; var args := {}
func _ready() -> void:
	process_physics_priority = -100
	args = parse_args(OS.get_cmdline_user_args()); assert(args.has("replay"), "--replay=PATH is required")
	replay = Replay.load_file(args["replay"])
	game = Game2D.new(); game.level_path = replay.level_path
	if args.has("art"): game.art = load(args["art"])
	add_child(game)
	Resonance.abilities_disabled = PackedStringArray(String(args.get("disable", "")).split(",", false))
	game.player.reached_goal.connect(func(): if goal_tick < 0: goal_tick = tick)
	game.player.touched_hazard.connect(func(): failures.append("tick %d: touched a hazard at %s" % [tick, game.player.cell()]))
func _physics_process(_delta: float) -> void:
	var now := replay.pressed[tick] if tick < replay.pressed.size() else PackedStringArray()
	var before := replay.pressed[tick - 1] if tick > 0 and tick - 1 < replay.pressed.size() else PackedStringArray()
	for a in before: if not now.has(a): Input.action_release(a)
	for a in now: if not before.has(a): Input.action_press(a)
	_check_asserts()
	if args.has("trace") and tick % 10 == 0: print("tick %d cell %s active=%s acquired=%s floor=%s" % [tick, game.player.cell(), Resonance.active, Resonance.acquired, game.player.is_on_floor()])
	var done := (goal_tick >= 0 or tick > replay.goal_by_tick or not failures.is_empty()) if not args.has("capture") else tick >= replay.pressed.size() - 1
	if done: _finish()
	tick += 1
func _check_asserts() -> void:
	var cell := game.player.cell()
	for i in replay.asserts.size():
		var a: Dictionary = replay.asserts[i]
		if fired.has(i) or Vector2i(int(a["cell"][0]), int(a["cell"][1])) != cell: continue
		fired[i] = tick
		if a.has("active_color") and Resonance.active != a["active_color"]: failures.append("tick %d at %s: active %s, expected %s" % [tick, cell, Resonance.active, a["active_color"]])
		if a.has("passable"):
			for tag in get_tree().get_nodes_in_group("resonance"):
				var expect: bool = tag.color == String(a["passable"]).get_slice("_", 1)  # the named kind's color: walls and platforms of it are passable
				if bool(tag.get_parent().get_meta("resonance_passable")) != expect: failures.append("tick %d: %s passable should be %s" % [tick, tag.get_parent().name, expect])
func _finish() -> void:
	for i in replay.asserts.size(): if not fired.has(i): failures.append("assert %d at cell %s never fired" % [i, replay.asserts[i]["cell"]])
	if goal_tick < 0: failures.append("goal not reached by tick %d (player at %s)" % [replay.goal_by_tick, game.player.cell()])
	var ok := failures.is_empty()
	print(JSON.stringify({"ok": ok, "goal_tick": goal_tick, "ticks": tick, "disabled": Resonance.abilities_disabled, "failures": failures}))
	get_tree().quit(0 if ok else 1)
static func parse_args(list: PackedStringArray) -> Dictionary:
	var out := {}
	for arg in list:
		if arg.begins_with("--"): var kv := arg.substr(2).split("=", true, 1); out[kv[0]] = kv[1] if kv.size() > 1 else true
	return out
```

(In capture mode the goal does not end the run; the JSON report still says whether it was reached.)

- [ ] **Step 14:** `tests/validate_tags.gd` (root of `tests/validate_tags.tscn`): builds `Game2D` (default art), then if `--mutate` is present removes the first `resonance` tag (`victim.get_parent().remove_child(victim); victim.free()`) and prints which; runs `TagValidator.validate(game.level, get_tree())`, prints each problem to stderr and `tag-check: N problem(s)`, quits 0 iff N == 0. The mutated run must exit 1 — that proves the validator is not a tautology.
- [ ] **Step 15:** First replay `game/g-a/replays/level01.replay.json` (also copied to `bakeoff/g-a/replays/`). The ticks below come from the tuning numbers (8 tiles/s = 0.133 tiles per tick; a jump lasts ~46 ticks): hold right from tick 60, hop the bump at col 8, jump onto the orb pillar at col 14, jump at the pit edge (col 19) and air-dash, run through the red wall, pick up green at col 39, double-jump the step at col 43, walk through the green wall, jump the gap onto the red platforms, jump off them and switch to red mid-air to pass the wall at col 57, drop to the goal. It is a starting skeleton the lane tunes with `--trace`:

```json
{"format": "violet-replay", "version": 1, "tick_hz": 60, "level": "res://levels/level01.greybox.json",
 "inputs": [
  {"from": 60, "to": 640, "hold": ["right"]},
  {"at": 95, "press": ["jump"]}, {"at": 143, "press": ["jump"]},
  {"at": 199, "press": ["jump"]}, {"at": 214, "press": ["dash"]},
  {"at": 342, "press": ["jump"]}, {"at": 365, "press": ["jump"]},
  {"at": 428, "press": ["jump"]}, {"at": 486, "press": ["jump"]}, {"at": 490, "press": ["switch"]},
  {"from": 641, "to": 3900, "hold": []}],
 "asserts": [
  {"cell": [33, 12], "active_color": "red", "passable": "wall_red"},
  {"cell": [44, 7], "active_color": "green"},
  {"cell": [48, 7], "active_color": "green", "passable": "wall_green"},
  {"cell": [55, 7], "active_color": "green"},
  {"cell": [58, 7], "active_color": "red", "passable": "wall_red"}],
 "expect": {"goal_by_tick": 4000}}
```

(`[58, 7]` is the landing cell right after the col-57 wall, which spans rows 0–7 and cannot be jumped over, so reaching it with red active proves the pass-through.) Tune: `godot --headless --fixed-fps 60 --path game/g-a res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --trace` and move ticks until the JSON says `"ok": true`. Then pad with idle/back-and-forth segments so the capture lasts 60–90 s (3600–5400 ticks) and set `goal_by_tick` ≤ 5400.

- [ ] **Step 16:** `export_presets.cfg` (one preset `name="Linux"`, `platform="Linux"`, `runnable=true`, `export_filter="all_resources"`, `export_path="../../out/g-a/violet-g-a.x86_64"`, options `binary_format/embed_pck=true`, `binary_format/architecture="x86_64"`) and `ci.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")"; lane=g-a; rep="../../bakeoff/$lane/reports"; mkdir -p "$rep" "../../out/$lane"
cmp ../../docs/bakeoff/level01.greybox.json levels/level01.greybox.json
../../scripts/godot-fetch.sh .
godot --headless --path . --import
run() { godot --headless --fixed-fps 60 --path . "$@"; }
run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json > "$rep/replay.json"
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=dash > "$rep/replay-no-dash.json"; then echo "ci.sh: replay without dash reached the goal" >&2; exit 1; fi
if run res://tests/replay_runner.tscn -- --replay=res://replays/level01.replay.json --disable=double_jump > "$rep/replay-no-double-jump.json"; then echo "ci.sh: replay without double jump reached the goal" >&2; exit 1; fi
run res://tests/validate_tags.tscn > "$rep/tags.txt" 2>&1
if run res://tests/validate_tags.tscn -- --mutate > "$rep/tags-mutated.txt" 2>&1; then echo "ci.sh: tag validator passed a mutated level" >&2; exit 1; fi
godot --headless --path . --export-release Linux "../../out/$lane/violet-$lane.x86_64" > "$rep/export.log" 2>&1
test -x "../../out/$lane/violet-$lane.x86_64" && timeout 90 "../../out/$lane/violet-$lane.x86_64" --headless --quit-after 120 && ls -l "../../out/$lane/violet-$lane.x86_64" > "$rep/build.txt"
```

(Godot's `--export-release` can exit 0 on failure — playtest-qa.md risk 5 — hence `test -x` and the headless smoke run.)

(An expected failure is written `if run ...; then exit 1; fi`, not `! run ...`: bash's `set -e` ignores a command negated with `!`, so `! run` can never fail the script.)

- [ ] **Step 17: Verify the greybox milestone** on oryx: `bash game/g-a/ci.sh` exits 0; `bakeoff/g-a/reports/replay.json` ends with `"ok": true`; `replay-no-dash.json` says `"ok": false` with "goal not reached"; `tags.txt` ends `0 problem(s)`; `tags-mutated.txt` shows one `no tagged body` problem. Commit (`.uid` files included), push `bakeoff/g-a`; the `bakeoff` workflow is green.
- [ ] **Step 18:** Painted world (account-free): generate each 2D piece in the biome brief with `gen image` (`--input` the biome brief's approved kit turntable or the protagonist concept for palette; tiles `--size 1024x1024`, backdrops `--size 1536x1024`) into `game/g-a/art/`. Check tiles tile: `magick ground-tile.png -roll +512+512 /tmp/roll.png` and look at the seam. `art/painted_art.gd` (`class_name PaintedArt extends GreyboxArt`, `@export` textures) returns `Sprite2D`s (`texture`, `scale = ts / texture.get_width()`), tagged cells get `art/reveal.gdshader` (`uniform float saturation; uniform float glow; ...` grayscale mix and additive glow) via `ShaderMaterial` and a `set_resonance_look` that sets `saturation = 1.0 if revealed else 0.0`, `glow = 0.6 if active else 0.0` and tweens `glow` for the pulse; `make_backdrop` stacks three `Parallax2D` layers (`scroll_scale` 0.2 / 0.5 / 0.8, `repeat_size.x` = texture width) with the backdrop PNGs; `attach_character` adds `SpineCharacter2D` when `res://protagonist/violet.json` exists, else the stand-in. Save as `art/lane_art.tres`. `provenance check game/g-a` OK.
- [ ] **Step 19:** Rig (after Task 5): copy `assets/bakeoff/protagonist/rig/violet.json`, `violet.meta.json`, and the 14 part PNGs (+ sidecars) into `game/g-a/protagonist/`. `art/spine_reader.gd` (`class_name SpineReader extends RefCounted`; generic, shared with Task 8's 3D reader): parses the subset (bones, slots, skins, animations) exactly as `docs/bakeoff/character-rig.md` defines it, refusing and naming anything outside it (a `curve` keyframe, a non-`rotate`/`translate` timeline, a non-region attachment, a slot with no attachment, an attachment without a `path`, a `skeleton.spine` that isn't 4.3.x); `static func bone_world(skeleton, anim_name, t) -> Dictionary` walks the bone hierarchy in the file's own parent-before-child order, applying each bone's setup pose plus its `rotate`/`translate` timeline's linearly-interpolated value at `t`, and returns each attachment's world centre and rotation per the contract's placement math. `art/spine_character_2d.gd` (`class_name SpineCharacter2D extends Node2D`): `_ready` loads the skeleton with `SpineReader`, builds one `Sprite2D` per slot in `slots` order (back to front) with `texture = load("res://protagonist/%s.png" % attachment.path)`, and sets `scale` to `(1.6 * 64.0) / meta.height_px` (the contract's Scale section — one factor, applied uniformly, offset by `meta.feet_y_px`); `_process` picks the animation the same way the stand-in did (`dash_ticks_left > 0` → `dash`; airborne → `double_jump` while `double_jump_used` else `jump` while `velocity.y < 0` else `fall`; landing → `land`; `|velocity.x| > 1` → `run`; else `idle`), advances `t`, looping only `idle`/`run` and holding the last frame of the rest until the state machine above picks the next animation (the contract's per-name rule, not a stored duration), and every frame sets each slot's `Sprite2D.position` (skeleton y flipped to Godot's y-down, per the contract) and `rotation` from `SpineReader.bone_world`; `scale.x = |scale.x| * facing` (mirrors left-facing, per the contract — `facing` in the meta file is always `right`); on `Resonance.changed` sets the `scarf1`/`scarf2`/`scarf3` sprites' `modulate` to the active color (`Color("#e04a3a")`/`Color("#3fbf6a")`/gray when none) — the tint `character-rig.md` leaves to the lane.
- [ ] **Step 20:** Captures (oryx agent, software under Xvfb): `scripts/capture-godot.sh g-a` → `bakeoff/g-a/capture/capture.mp4` (60–90 s) and four stills; look at them: the reveal at the red orb, the dash across the pit, the scarf color flip at the green orb, the mid-air switch at col 57. Playable check: `bash game/g-a/ci.sh` passes, including the export's headless smoke run. Keyboard play to the goal (`R` restarts, `Esc` quits) is Sami's, from the build artifact, when he judges; an agent can't play with a keyboard.
- [ ] **Step 21:** `LOG.md` complete (`status: delivered`, deliverables filled, every session, cost, intervention and friction entry), `git lfs push origin bakeoff/g-a`, push; CI green; the run URL goes in `LOG.md`.

### Task 8: Lane G-D — Godot 4.7.2 3D hybrid

**Files:**
- Create under `game/g-d/`: `project.godot` (as G-A but `config/features=PackedStringArray("4.7", "Forward Plus")`, `rendering/renderer/rendering_method="forward_plus"`, and G-A's `[shader_globals]` `world_saturation` entry kept: the shared `resonance.gd` sets that global on every color change, and without the declaration every rendered run logs `!global_shader_uniforms.variables.has(p_name)`, which headless CI never shows), `export_presets.cfg` (`export_path="../../out/g-d/violet-g-d.x86_64"`), `ci.sh` (G-A's with `lane=g-d`), `levels/`, `replays/level01.replay.json`, `bakeoff/{actions,resonance,greybox,replay,resonance_tag,tag_validator}.gd` (copied), `bakeoff/{greybox_builder_3d,greybox_art_3d,player_3d,game_3d}.gd`, `tests/{replay_runner.gd,replay_runner.tscn,validate_tags.gd,validate_tags.tscn}` (copied; `Game2D` → `Game3D`, `Node2D` → `Node3D`), `scenes/main.tscn`, `art/{kit_art_3d.gd,lane_art.tres,spine_reader.gd (copied),spine_character_3d.gd}`, `kit/*.glb` (copied from `assets/bakeoff/desert-kit-3d/` with sidecars), `protagonist/` (as G-A)
- Create: `bakeoff/g-d/{LOG.md,replays/,reports/,capture/}`
- Create: `game/g-d/ci-tools` containing `godot`

**Interfaces:**
- Consumes: `jj file show -r bakeoff/g-a game/g-a/bakeoff/<file>.gd > game/g-d/bakeoff/<file>.gd` for the six shared scripts and the two test scripts, and the same for `art/spine_reader.gd` (the rig reader's FK math is dimension-agnostic, so both lanes use the identical file); Task 6 kit; Task 5 rig.
- Produces: the D-direction Godot lane; `Player3D.cell()` has the same signature as `Player2D.cell()` so the copied runner works unchanged.

- [ ] **Step 1:** Workspace `~/src/violet-g-d` on `bakeoff/g-d` from master; LOG (`direction: D, engine: godot, machine: oryx`); copy the level; `scripts/godot-fetch.sh game/g-d`; copy the shared scripts with `jj file show -r bakeoff/g-a ...` (the files are byte-identical; a later G-A fix is re-copied the same way and logged).
- [ ] **Step 2:** `bakeoff/player_3d.gd` — `class_name Player3D extends CharacterBody3D`; constants in metres (`GRAVITY := 40.0`, `RUN_SPEED := 8.0`, `JUMP_SPEED := 15.5`, `DASH_SPEED := 30.0`, `DASH_TICKS := 12`); `var level_height := 16`; `_ready`: `collision_layer = 2; collision_mask = 1; axis_lock_linear_z = true;` a `CollisionShape3D` with `BoxShape3D.size = Vector3(0.8, 1.6, 0.8)` at `position.y = 0.8`; `_physics_process` is G-A's with `velocity.y -= GRAVITY * delta` (clamped at `-3 * JUMP_SPEED`), jumps set `velocity.y = JUMP_SPEED`, dash sets `Vector3(facing * DASH_SPEED, 0, 0)`; `func cell() -> Vector2i: return Vector2i(floori(global_position.x), level_height - 1 - floori(global_position.y + 0.01))`; `on_area(area: Area3D)` as in 2D.
- [ ] **Step 3:** `bakeoff/greybox_builder_3d.gd` — `build(level, root: Node3D, art: GreyboxArt3D)`: `pos = Vector3(c + 0.5, level.height - r - 0.5, 0)`; solids/tagged → `StaticBody3D` (`collision_layer = 1, collision_mask = 0`) + `CollisionShape3D` (`BoxShape3D.size = Vector3.ONE`) + `art.make_cell(kind, cell)` + `ResonanceTag`; `start` → `info["start"] = Vector3(pos.x, pos.y - 0.5, 0)`; triggers → `Area3D` (`collision_mask = 2`) + shape + meta/group. `bakeoff/greybox_art_3d.gd` (`class_name GreyboxArt3D extends Resource`): `make_cell` = `MeshInstance3D(BoxMesh)` with `StandardMaterial3D` (`diffuse_mode = DIFFUSE_TOON`, `specular_mode = SPECULAR_TOON`, albedo by kind) plus, for tagged kinds, an `OmniLight3D` child (`light_color` red/green, `omni_range = 4`, `light_energy = 0`) and a script implementing `set_resonance_look(revealed, active)` → `albedo = gray|color`, `emission_enabled = active`, `light_energy = 0 | 0.6 | 2.0` (pulsed by a tween when active); `make_backdrop` = a `WorldEnvironment` (sky gradient from the brief, `tonemap_mode = ACES`, `adjustment_enabled = true`, `adjustment_saturation` bound to `Resonance.world_saturation()` on `changed`), a `DirectionalLight3D` (warm, `rotation_degrees = Vector3(-50, 30, 0)`, shadows on), and a sand `PlaneMesh` floor at `y = 0`; `attach_character` = STAND-IN `CapsuleMesh` + `Label3D` until the rig exists.
- [ ] **Step 4:** `bakeoff/game_3d.gd` — `class_name Game3D extends Node3D`, same flow as `Game2D`: `player.level_height = level.height`, `Camera3D` (`fov = 30`, which is vertical, 32 m from the level plane: 2 · 32 · tan 15° ≈ 17.2 m of height, so the level's full 16 m stays framed and about 30 × 17 tiles show at 16:9, as `mechanic.md` says. At 22 m it would frame only 11.8 m. The camera follows the player on x only, clamped to `[15, width - 15]`, with y fixed near mid-height (about 8) and looking straight at the level plane. Put it under a `Node3D` that follows the player in `_process`). `scenes/main.tscn`: root `Node3D` with `game_3d.gd` and `art = res://art/lane_art.tres`.
- [ ] **Step 5:** Replay: start from G-A's file (`jj file show -r bakeoff/g-a game/g-a/replays/level01.replay.json`), run with `--trace`, retune ticks (3D `move_and_slide` differs slightly), assert cells unchanged. `bash game/g-d/ci.sh` on oryx passes with greybox cubes; push; CI green.
- [ ] **Step 6:** Kit dressing (after Task 6): copy the agent-authored GLBs + sidecars from `assets/bakeoff/desert-kit-3d/` into `game/g-d/kit/`; `art/kit_art_3d.gd` (`class_name KitArt3D extends GreyboxArt3D`): `make_cell` for `solid` returns `sand-tile.glb`/`rock-tile.glb` instances (normalise scale so the AABB's largest side = 1 m: `var aabb := (inst.find_child("*", true) as MeshInstance3D).get_aabb()`), tagged cells keep the toon box tinted plus `crystal-cluster.glb` at 0.5 m; `make_backdrop` adds mesas/arches/saguaros/acacias at `z ∈ [-3, -12]` from a `RandomNumberGenerator` seeded `20260927` (deterministic captures), toon materials applied to every kit mesh (`get_surface_override_material`); `attach_character` → `SpineCharacter3D` (`extends Node3D`, same reader as 2D via `SpineReader`, one `Sprite3D` per slot billboarded toward the camera, `scale = 1.6 / meta.height_px`, lit by the scene lights).
- [ ] **Step 7:** Captures on oryx via `scripts/capture-godot.sh g-d` (software, as G-A). Separately, the RADV check on machine sami while Sami is at the keyboard: run the export binary for 30 s on his display (Forward+ on the 890M). Playable check as G-A; `LOG.md` delivered; push with LFS; CI green. Note in `friction` anything Vulkan/RADV did.

### Task 9: Lane U-D — Unity 6.3 LTS URP hybrid, official MCP only

**Files:**
- Create under `game/u-d/` (Unity project): `Packages/manifest.json` additions, `Assets/Bakeoff/Scripts/{Greybox,Replay,Resonance,ResonanceTag,Trigger,GreyboxBuilder3D,IGreyboxArt,GreyboxArt,KitArt,Player3D,IInputSource,KeyboardInput,ReplayRunner,TagValidator,Game3D,FollowCamera,WorldSaturationDriver,SpineReader,SpineCharacter3D}.cs`, `Assets/Bakeoff/Editor/{Build.cs,Violet.Bakeoff.Editor.asmdef}`, `Assets/Bakeoff/Tests/PlayMode/{ReplayTests,TagValidatorTests}.cs` + `Violet.Bakeoff.Tests.asmdef` (`testAssemblies: true`, references `UnityEngine.TestRunner`, `UnityEditor.TestRunner`), `Assets/StreamingAssets/bakeoff/{level01.greybox.json,level01.replay.json}`, `Assets/Bakeoff/Scenes/Level01.unity` (built through MCP), `Assets/Bakeoff/Rig/{violet.json,violet.meta.json,<part>.png × 14}` (+ sidecars, copied from `assets/bakeoff/protagonist/rig/` and `parts/`), `Assets/Bakeoff/Kit/*.glb` (+ sidecars), `ci.sh`
- Create: `bakeoff/u-d/{LOG.md,replays/,reports/,capture/}`; `game/u-d/ci-tools`, empty (CI only checks the committed reports; Unity runs on machine sami). Captures use Task 3's `scripts/capture-unity.sh`.
- Modify: `~/.dotfiles/omp/mcp.json` on machine sami (a lazy `unity` server entry; pushed to dotfiles main per its README)

**Interfaces:**
- Consumes: Sami's Unity checklist (below); `com.unity.ai.assistant` MCP relay `~/.unity/relay/relay_linux --mcp`; packages `com.unity.nuget.newtonsoft-json`, `com.unity.cloud.gltfast`; `Assets/Bakeoff/Rig/violet.json`, read directly by `SpineReader.cs` — no Spine package, no spine-unity, per `docs/bakeoff/character-rig.md`.
- Produces: the D-direction Unity lane; `bakeoff/u-d/reports/playmode.xml` (NUnit3) and `build.log` that CI verifies (CI cannot run a licensed Unity Editor; the tests and build run on machine sami and the report is committed).

- [ ] **Step 1: Sami's checklist** (one ask on issue #4; every item is an intervention in `LOG.md` with minutes): install Unity Hub from Unity's apt repo; sign in; install Unity **6000.3 LTS** with **Linux Build Support (Mono)**; New project → **Universal 3D** template → name `u-d`, location `$VIOLET/game/`; Project Settings → Services → link a Unity Cloud project; start the Unity AI trial/subscription; Window → Package Manager → Unity Registry → install **AI Assistant** (`com.unity.ai.assistant`); Edit → Project Settings → AI → Unity MCP → Bridge **Running**; when the agent first connects, **Accept** the pending connection; tell the agent the editor path (`~/Unity/Hub/Editor/6000.3.<x>f1/Editor/Unity`) and the `cosmic-comp` version (`dpkg -s cosmic-comp | grep Version`; the Inspector-refresh bug is fixed in 1.1). Record `m_EditorVersion` from `ProjectSettings/ProjectVersion.txt` in `LOG.md`.
- [ ] **Step 2:** MCP wiring on machine sami: add to `~/.dotfiles/omp/mcp.json` → `"unity": {"lazy": true, "command": "/home/sami/.unity/relay/relay_linux", "args": ["--mcp"]}` (the relay exists after Unity has started once); the lane session lists Unity tools and runs "read the console" as the connection test. Every editor action goes through these tools; C# files, `manifest.json` and StreamingAssets are edited as text (that is source editing, not platform interaction); Unity's own command line (`-batchmode -runTests`, `-executeMethod`) is Unity's interface. No other automation.
- [ ] **Step 3:** `Packages/manifest.json`: add `"com.unity.nuget.newtonsoft-json": "3.2.1"`, `"com.unity.cloud.gltfast"` at the version Package Manager lists for 6000.3 (record it in `LOG.md`), and `com.unity.test-framework` if the template lacks it (no spine-unity package — the rig is read directly by `SpineReader.cs`, per decision 0012). Open the editor once so it resolves; MCP "read console" is clean.
- [ ] **Step 4:** Core C# (namespace `Violet.Bakeoff`, all THROWAWAY-headed). `Greybox.cs`: `Parse(string json)` with Newtonsoft (`format`/`version` check, equal row lengths, legend kinds), `KindAt(col,row)` (out of range → `"solid"`), `IEnumerable<Vector2Int> CellsOf(kind)`, `Vector3 CellCenter(cell) => new(cell.x + 0.5f, Height - cell.y - 0.5f, 0)`, `static Tagged` dictionary as in GDScript. `Replay.cs`: `Parse(json)` → `HashSet<string>[] Pressed`, `int GoalByTick`, `JArray Asserts`, `string Level`. `Resonance.cs` (static): `Acquired`, `Active`, `Disabled`, `event Action Changed`, `Acquire`, `Cycle`, `Reset`, `Has`, `CanDash => Active == "red" && !Disabled.Contains("dash")`, `CanDoubleJump`, `WorldSaturation => new[]{0.35f,0.7f,1f}[Acquired.Count]`. `ResonanceTag.cs`:

```csharp
public sealed class ResonanceTag : MonoBehaviour {
    public string Color, Kind; public Vector2Int Cell; public bool Passable { get; private set; }
    void OnEnable() { Resonance.Changed += Apply; Apply(); }
    void OnDisable() { Resonance.Changed -= Apply; }
    void Apply() {
        Passable = Resonance.Active == Color;
        foreach (var c in GetComponents<Collider>()) c.enabled = !Passable;
        foreach (var look in GetComponents<IResonanceLook>()) look.SetResonanceLook(Resonance.Has(Color), Passable);
    }
}
public interface IResonanceLook { void SetResonanceLook(bool revealed, bool active); }
```

`Trigger.cs` (`public string Kind`). `GreyboxBuilder3D.cs`: `Build(Greybox level, Transform root, IGreyboxArt art) -> BuildInfo{Start}`: solids/tagged → GameObject at `CellCenter` on layer 0 with `BoxCollider(size 1)`, `art.MakeCell(kind, cell, go)`, `ResonanceTag` for tagged kinds; `start` → `Start = center + (0,-0.5,0)`; triggers → `BoxCollider{isTrigger=true}` + `Trigger`. `GreyboxArt.cs` (default `IGreyboxArt`): a cube mesh child (`GameObject.CreatePrimitive(PrimitiveType.Cube)` with its collider removed) with a `MaterialPropertyBlock` `_BaseColor` per kind and, for tagged kinds, a `ResonanceLook` component setting gray/color/emission and a `Light` (point, colored, `intensity` 0/0.6/2) — plus a STAND-IN capsule with a `TextMesh` for the character. `Player3D.cs`:

```csharp
[RequireComponent(typeof(Rigidbody))] public sealed class Player3D : MonoBehaviour {
    public const float Gravity = 40f, RunSpeed = 8f, JumpSpeed = 15.5f, DashSpeed = 30f; public const int DashTicks = 12;
    public IInputSource Input; public int LevelHeight = 16; public event System.Action ReachedGoal, TouchedHazard; public bool Died { get; private set; }
    Rigidbody _rb; int _facing = 1, _dash; bool _airDash, _doubleJump; InputFrame _prev;
    void Awake() {
        gameObject.layer = 8; _rb = GetComponent<Rigidbody>(); _rb.useGravity = false; _rb.interpolation = RigidbodyInterpolation.None;
        _rb.constraints = RigidbodyConstraints.FreezeRotation | RigidbodyConstraints.FreezePositionZ; _rb.collisionDetectionMode = CollisionDetectionMode.Continuous;
        var col = gameObject.AddComponent<BoxCollider>(); col.size = new Vector3(0.8f, 1.6f, 0.8f); col.center = new Vector3(0, 0.8f, 0);
        col.material = new PhysicsMaterial { dynamicFriction = 0, staticFriction = 0, frictionCombine = PhysicsMaterialCombine.Minimum };
    }
    public bool OnGround => Physics.CheckBox(transform.position + new Vector3(0, -0.05f, 0), new Vector3(0.38f, 0.06f, 0.38f), Quaternion.identity, 1 << 0, QueryTriggerInteraction.Ignore);
    void FixedUpdate() {
        var f = Input.Read(); var dir = (f.Right ? 1 : 0) - (f.Left ? 1 : 0); if (dir != 0) _facing = dir;
        if (f.Switch && !_prev.Switch) Resonance.Cycle();
        var g = OnGround; if (g) { _airDash = false; _doubleJump = false; }
        var v = _rb.linearVelocity;
        if (_dash > 0) { _dash--; v = new Vector3(_facing * DashSpeed, 0, 0); }
        else {
            v.x = dir * RunSpeed; v.y = Mathf.Max(v.y - Gravity * Time.fixedDeltaTime, -3f * JumpSpeed); if (g && v.y < 0) v.y = 0;
            if (f.Jump && !_prev.Jump) { if (g) v.y = JumpSpeed; else if (Resonance.CanDoubleJump && !_doubleJump) { _doubleJump = true; v.y = JumpSpeed; } }
            if (f.Dash && !_prev.Dash && Resonance.CanDash && (g || !_airDash)) { if (!g) _airDash = true; _dash = DashTicks; v = new Vector3(_facing * DashSpeed, 0, 0); }
        }
        v.z = 0; _rb.linearVelocity = v; _prev = f;
    }
    public Vector2Int Cell() => new(Mathf.FloorToInt(transform.position.x), LevelHeight - 1 - Mathf.FloorToInt(transform.position.y + 0.01f));
    void OnTriggerEnter(Collider other) { var t = other.GetComponent<Trigger>(); if (t == null) return;
        switch (t.Kind) { case "orb_red": Resonance.Acquire("red"); Destroy(other.gameObject); break; case "orb_green": Resonance.Acquire("green"); Destroy(other.gameObject); break;
                          case "goal": ReachedGoal?.Invoke(); break; case "hazard": Died = true; TouchedHazard?.Invoke(); break; } }
}
public struct InputFrame { public bool Left, Right, Jump, Dash, Switch; }
public interface IInputSource { InputFrame Read(); }
```

`KeyboardInput.cs` reads `UnityEngine.Input.GetKey(KeyCode.A|LeftArrow ...)` (legacy Input Manager — no setup). `Game3D.cs`: `Build(string levelJson, IGreyboxArt art)` → `Level`, `World` (root Transform), `Player` (new GameObject + `Rigidbody` + `Player3D`, `Input = new KeyboardInput()`, `LevelHeight = Level.Height`, at `info.Start`), `art.MakeBackdrop(Level, World)`, `art.AttachCharacter(Player)`; `Awake` in the scene calls `Build(File.ReadAllText(Path.Combine(Application.streamingAssetsPath, "bakeoff/level01.greybox.json")), new KitArt())` unless a test built it first, handles `R` (reload scene) and `Escape` (quit) in `Update`. `ReplayRunner.cs` (`[DefaultExecutionOrder(-100)]`, implements `IInputSource`): `Bind(player, level, replay)` stores them, sets `player.Input = this`, and subscribes `player.ReachedGoal += () => { if (GoalTick < 0) GoalTick = Tick; }` and `player.TouchedHazard += () => Failures.Add($"tick {Tick}: touched a hazard at {player.Cell()}")`; `FixedUpdate` sets `_frame` from `Replay.Pressed[Tick]`, fires cell asserts exactly as the GDScript runner (first entry of `cell`, `active_color`, `passable` over all `ResonanceTag`s, never-fired asserts fail at finish), `Trace` logs every 10 ticks, `Finished` when goal/timeout/failure (or last input tick in capture mode), `Report()` → the same JSON shape. Capture mode (player build args `--replay PATH --capture DIR`): `Time.captureFramerate = 60` and a coroutine calling `ScreenCapture.CaptureScreenshot($"{dir}/frame_{n:D6}.png")` after `WaitForEndOfFrame` each frame, quitting at the end. `TagValidator.cs`: the GDScript logic over `root.GetComponentsInChildren<ResonanceTag>(true)` and `GetComponent<IResonanceLook>() == null`. `FollowCamera.cs`: camera at `(clamp(px, 15, W-15), 8.5, -32)`, `fieldOfView = 30` (vertical, so 32 m frames about 17.2 m and the full 16 m level height; -22 would frame 11.8 m), looking at `(x, 8.5, 0)`. `WorldSaturationDriver.cs`: on `Resonance.Changed`, `volumeProfile.TryGet(out ColorAdjustments ca); ca.saturation.value = Mathf.Lerp(-100f, 0f, Resonance.WorldSaturation)`.

- [ ] **Step 5:** Tests (`Assets/Bakeoff/Tests/PlayMode`):

```csharp
public class ReplayTests {
    [UnityTest] public IEnumerator Level01ReplayReachesTheGoal() => Run(new string[0], true);
    [UnityTest] public IEnumerator Level01ReplayFailsWithoutDash() => Run(new[] { "dash" }, false);
    static IEnumerator Run(string[] disabled, bool expectGoal) {
        Resonance.Reset(); foreach (var d in disabled) Resonance.Disabled.Add(d);
        Time.fixedDeltaTime = 1f / 60f; Time.timeScale = 20f; Time.maximumDeltaTime = 1f;
        var scene = SceneManager.CreateScene("replay-" + System.Guid.NewGuid()); SceneManager.SetActiveScene(scene);
        var go = new GameObject("Game"); var game = go.AddComponent<Game3D>();
        var sa = Application.streamingAssetsPath;
        game.Build(File.ReadAllText(Path.Combine(sa, "bakeoff/level01.greybox.json")), new GreyboxArt());
        var runner = go.AddComponent<ReplayRunner>(); runner.Bind(game.Player, game.Level, Replay.Parse(File.ReadAllText(Path.Combine(sa, "bakeoff/level01.replay.json"))));
        while (!runner.Finished) yield return new WaitForFixedUpdate();
        Time.timeScale = 1f; Debug.Log(runner.Report());
        Assert.AreEqual(expectGoal, runner.GoalTick >= 0, string.Join("\n", runner.Failures));
        if (expectGoal) Assert.IsEmpty(runner.Failures);
        yield return SceneManager.UnloadSceneAsync(scene);
    }
}
public class TagValidatorTests {
    [UnityTest] public IEnumerator TagValidatorPassesOnTheBuiltLevel() { var (game, scene) = Build(); yield return null;
        Assert.IsEmpty(TagValidator.Validate(game.Level, game.World)); yield return SceneManager.UnloadSceneAsync(scene); }
    [UnityTest] public IEnumerator TagValidatorFailsWhenATagIsRemoved() { var (game, scene) = Build(); yield return null;
        Object.DestroyImmediate(game.World.GetComponentInChildren<ResonanceTag>());
        var problems = TagValidator.Validate(game.Level, game.World); Assert.That(problems, Has.Some.Contains("no tagged body")); yield return SceneManager.UnloadSceneAsync(scene); }
    static (Game3D, Scene) Build() { Resonance.Reset(); var scene = SceneManager.CreateScene("tags-" + System.Guid.NewGuid()); SceneManager.SetActiveScene(scene);
        var game = new GameObject("Game").AddComponent<Game3D>(); game.Build(File.ReadAllText(Path.Combine(Application.streamingAssetsPath, "bakeoff/level01.greybox.json")), new GreyboxArt()); return (game, scene); }
}
```

- [ ] **Step 6:** Scene through MCP: create `Assets/Bakeoff/Scenes/Level01.unity` with `Game` (`Game3D`), `Main Camera` (`FollowCamera`), `Directional Light` (warm, shadows), `Global Volume` (URP Volume, profile with Color Adjustments + Bloom, `WorldSaturationDriver`); add the scene to Build Settings; console clean. Editor script `Assets/Bakeoff/Editor/Build.cs`: `public static void Linux()` → `BuildPipeline.BuildPlayer(new[]{"Assets/Bakeoff/Scenes/Level01.unity"}, "../../out/u-d/violet-u-d.x86_64", BuildTarget.StandaloneLinux64, BuildOptions.None)`; `EditorApplication.Exit(1)` unless `summary.result == BuildResult.Succeeded`, else log `Build succeeded`.
- [ ] **Step 7:** Replay: start from G-A's file (`jj file show -r bakeoff/g-a game/g-a/replays/level01.replay.json > game/u-d/Assets/StreamingAssets/bakeoff/level01.replay.json`; set `"level"` to `bakeoff/level01.greybox.json`), tune with the runner's trace (run the PlayMode test with `Trace` on and read `playmode.log`). Run on machine sami: `UNITY=~/Unity/Hub/Editor/6000.3.<x>f1/Editor/Unity; "$UNITY" -batchmode -projectPath game/u-d -runTests -testPlatform PlayMode -testResults "$PWD/bakeoff/u-d/reports/playmode.xml" -logFile "$PWD/bakeoff/u-d/reports/playmode.log"` (exit 0; the XML lists the four tests Passed) and `"$UNITY" -batchmode -quit -projectPath game/u-d -executeMethod Violet.Bakeoff.Editor.Build.Linux -logFile "$PWD/bakeoff/u-d/reports/build.log"`. `game/u-d/ci.sh` (what CI runs, no Unity): `cmp` the level, parse `playmode.xml` with `python3` (`total`, `failed`, the four names `Passed`), `grep -q "Build succeeded" ../../bakeoff/u-d/reports/build.log`, and `provenance`-checked assets; exits 1 if a report is missing. Copy `playmode.xml`, `playmode.log`, `build.log` into `bakeoff/u-d/reports/` and commit them.
- [ ] **Step 8:** Kit + rig: copy the agent-authored GLBs (+ sidecars) to `Assets/Bakeoff/Kit/` (glTFast imports them as prefabs), `KitArt.cs` mirrors `KitArt3D` (deterministic backdrop from `new System.Random(20260927)`, toon look via URP Lit with `_Smoothness 0` and the Bloom/Color Adjustments volume; a Shader Graph toon ramp if time allows); copy `violet.json`, `violet.meta.json`, and the part PNGs (+ sidecars) to `Assets/Bakeoff/Rig/` as `TextAsset`/`Texture2D` imports (no Spine package). `SpineReader.cs` (`static Skeleton Parse(string json)`, `static (Vector3 pos, float rotDeg) BoneWorld(Skeleton, string anim, string bone, float t)`) implements the FK and placement math in `docs/bakeoff/character-rig.md`, refusing and naming anything outside the subset. `SpineCharacter3D.cs` builds one `SpriteRenderer`-backed child `GameObject` per slot from the part PNGs (in `slots` order), sets `transform.localScale = 1.6f / height_px`, drives the same idle/run/jump/fall/double_jump/dash/land state machine as Godot by advancing `t` through `SpineReader.BoneWorld` every `FixedUpdate`, and sets the `scarf1..3` renderers' color on `Resonance.Changed` (gray when no color active).
- [ ] **Step 9:** Capture, on machine sami. It needs Xvfb there first: `sudo apt install xvfb` is a one-time step for Sami, because it needs his password, and it's listed on issue #4. Without it, and with no `$DISPLAY`, `render` stops with "no DISPLAY and no xvfb-run". `scripts/capture-unity.sh` runs `out/u-d/violet-u-d.x86_64 --replay "$PWD/game/u-d/Assets/StreamingAssets/bakeoff/level01.replay.json" --capture "$PWD/out/u-d/frames" -screen-width 1920 -screen-height 1080` then `ffmpeg -y -framerate 60 -i out/u-d/frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -crf 18 bakeoff/u-d/capture/capture.mp4` and the same four stills as Godot. Playable check: run the binary and play to the goal.
- [ ] **Step 10:** Blockers are results: if the editor misbehaves under COSMIC (Inspector not refreshing, choppy play mode), the Hub refuses the license, the AI trial cannot be started, or the MCP bridge never connects, record `{what, since, waiting_on}` with the exact symptom, `cosmic-comp` version, screenshot path, and what still ran (batchmode tests do not need the GUI); set `status: blocked` if the build or tests cannot run; never install a third-party MCP or a nested compositor. The only official alternative — logging into a GNOME session — is Sami's call and is asked once on issue #4 without waiting.
- [ ] **Step 11:** `LOG.md` delivered/blocked, `git lfs push origin bakeoff/u-d`, push; CI green (the report check).

### Task 10: Lane G-C — Godot 2D flat-vector desert kit (environment only)

**Files:**
- Create on `bakeoff/g-c` (branched from `bakeoff/g-a`): `game/g-c/` (G-A's project directory moved), `game/g-c/art/vector_art.gd`, `game/g-c/art/lane_art.tres`, `game/g-c/art/*.svg` (+ sidecars, hand-written), `bakeoff/g-c/{LOG.md,replays/,reports/,capture/}`
- `game/g-c/ci-tools` comes over from G-A with the project directory and stays `godot`.

**Interfaces:**
- Consumes: `docs/bakeoff/desert-biome-brief.md`'s 2D/SVG list and palette; the SVG spec (plain `<svg>` documents, flat `<path>`/`<rect>`/`<polygon>` fills, no gradients, no filters — hand-authored, not generated by an external vector API).
- Produces: the eleven hand-written SVGs (`ground-tile`, `wall-tile`, `platform-tile`, `crystal-wall`, `crystal-platform`, `orb`, `goal-gate`, `hazard-tile`, `backdrop-far`, `backdrop-mid`, `backdrop-near`) under `game/g-c/art/`, each recorded `origin generated`; the G-C lane.

- [ ] **Step 1:** Write the eleven SVGs by hand in `game/g-c/art/`: flat fills only (no gradients, no filters, no strokes-as-outline), 4–6 colors each, the biome brief's palette (sand `#d9b27c`, rock `#a86f46`, shadow violet `#5a4a7a`, sky `#f2c49b`/`#3f7f8c`); `crystal-wall`, `crystal-platform` and `orb` are drawn neutral light gray (`#8c8c8c`), per `docs/bakeoff/desert-biome-brief.md` — the engine's reveal shader multiplies them by the tag color, so pre-colored art would come out wrong. Each tile a 64×64 (or its multiple) `viewBox`, backdrops sized for the parallax layers. Provenance: `provenance record game/g-c/art/<piece>.svg --kind image --origin generated --license proprietary --tool omp --tool-version "$(omp --version)" --provider anthropic --model "<your model id from the harness>" --prompt "Hand-drawn flat-vector <piece> from docs/bakeoff/desert-biome-brief.md"` for each.
- [ ] **Step 2:** Lane: `jj workspace add --name g-c -r bakeoff/g-a ~/src/violet-g-c; cd ~/src/violet-g-c; jj bookmark create bakeoff/g-c -r @`; `mv game/g-a game/g-c` (jj snapshots the rename); edit `export_presets.cfg` (`export_path` → `g-c`) and `ci.sh` (`lane=g-c`); create `bakeoff/g-c/` from the template with `direction: C` (G-A's `bakeoff/g-a/` stays on the branch untouched — it is G-A's evidence, not G-C's).
- [ ] **Step 3:** `art/vector_art.gd` (`class_name VectorArt extends PaintedArt`) points the same slots at the SVG textures (Godot imports SVG through ThorVG; set `svg/scale` in the `.import` to 1.0 and check `godot --headless --path game/g-c --import` produces no import errors); the character stays the shared rig, read the same way G-A reads it (the lane is environment-only by definition — say so in the gallery notes). Reveal shader unchanged (flat colors desaturate cleanly — art-pipeline §2 argued C is the easiest to tag).
- [ ] **Step 4:** `bash game/g-c/ci.sh` passes (the replay and tags are G-A's — the level and physics are identical); captures via `scripts/capture-godot.sh g-c` on oryx (software); playable check; `LOG.md`; LFS push; CI green.

### Task 11: Control lane — full-3D protagonist in Blender

**Files:**
- Create on `bakeoff/control`: `game/control/ci.sh` (verifies `bakeoff/control/reports/render.json` and that `capture/capture.mp4` decodes with `ffprobe`), `game/control/render_reel.py` (Blender script), `game/control/reel.json`, `assets` under `game/control/character/{violet.glb,violet.rigged.glb,motions/*.fbx,anims/*.glb}` (+ sidecars), `bakeoff/control/{LOG.md,reports/render.json,capture/}`
- Create on `bakeoff/control`: `game/control/ci-tools` containing `ffmpeg` (for `ffprobe`; Blender renders run on oryx, not in CI)

**Interfaces:**
- Consumes: Task 6's `gen model3d/rig/motion/animate`; Task 4's concept as the image-to-3D input; Blender from `tools/preview/README.md`; Task 0 for CUDA.
- Produces: a 60–90 s reel (`idle, run, jump, fall, double_jump, dash, land` clips, then a turntable) and stills; `render.json` = `{"clips": [...], "frames": N, "device": "CUDA|CPU", "seconds": T}`. No playable build and no completability test by construction — recorded in `LOG.md` as the lane's structural blocker, not a failure.

**Status: waiting (decision 0012, `docs/decisions/0012-no-purchases-until-agents-prove-it.md`).** This lane's full-3D protagonist needs Meshy's image-to-3D and auto-rig; the bake-off buys no tools. The steps below stay as written for if that ever changes; until then this lane does not run — `bakeoff/control/LOG.md` records the wait as its blocker, not a failure.

- [ ] **Step 1:** Character: `secrets MESHY_API_KEY -- uv run --project tools/gen gen model3d --provider meshy --model meshy-7.1 --input assets/bakeoff/protagonist/concept/violet-turnaround.png --pbr --pose a-pose --out game/control/character/violet.glb` (image-to-3D from the approved concept, so the lanes compare the same character); `gen rig --provider meshy --input game/control/character/violet.glb --height-m 1.6 --out game/control/character/violet.rigged.glb` (Meshy requires a textured humanoid facing +Z; on `422` retry once with `--pose t-pose` regeneration and log it). Within 3 days: `gen motion --provider meshy --mode prime --duration 3 --prompt "<clip>"` for `idle` ("standing, breathing, slight sway"), `run` ("running forward in place"), `jump` ("jumping up from standing"), `fall` ("falling with arms out"), `double_jump` ("a second jump mid-air with a forward somersault"), `dash` ("a sudden horizontal dash lunge with arms back"), `land` ("landing from a jump into a crouch and standing"), each `--out game/control/character/motions/<clip>.fbx`; then `gen animate --provider meshy --input violet.rigged.glb --input motions/<clip>.fbx --out anims/<clip>.glb` ×7. `provenance check game/control` OK; costs to `LOG.md`.
- [ ] **Step 2:** `render_reel.py` (`blender --background --python game/control/render_reel.py -- game/control/reel.json out/control/frames [--gpu]`): factory settings; Cycles, `scene.cycles.device = "GPU"` with `compute_device_type = "OPTIX"` (fallback `"CUDA"`) when `--gpu` is in the args, else `CPU`; 1920×1080, 30 fps, 64 samples GPU / 24 samples CPU; desert world color, a warm sun, a red and a green point light either side, a sand plane; camera at `(0, -7, 1.6)` pitched 85°; for each clip in `reel.json` (`{"clips": [{"name", "glb", "seconds"}], "turntable_seconds": 8}`): `bpy.ops.import_scene.gltf`, find the armature's action, render `seconds × 30` frames cycling `frame_range`, then delete the imported objects; finally the rigged character rotating 360° for the turntable; write `frames/frame_%06d.png` and `render.json`. Run: `scripts/oryx-gpu-check.sh && flock /tmp/oryx-gpu.lock blender --background --python game/control/render_reel.py -- game/control/reel.json out/control/frames --gpu`. **No-GPU fallback:** the same command without `--gpu` (CPU Cycles, 24 samples; ~2–4× slower on oryx's cores; still finishes overnight) — record `device` in `render.json`.
- [ ] **Step 3:** `ffmpeg -y -framerate 30 -i out/control/frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p -crf 18 bakeoff/control/capture/capture.mp4`; stills at 5/20/40/60 s; duration 60–90 s (adjust `seconds` in `reel.json`). Look at the reel: does the character keep its identity across clips, do dash and double-jump read as those moves (art-feasibility §4 task 2 expects them not to — record what you see).
- [ ] **Step 4:** `LOG.md` (`direction: control, engine: blender, machine: oryx`; blockers: "no playable build/completability test by design"), `git lfs push`, push `bakeoff/control`; CI green (`ci.sh` verifies the report and the mp4).

### Task 12: Judging gallery, scores, decision record 0013

**Files:**
- Create: `docs/bakeoff/results.md`, `docs/bakeoff/scores.json`, `docs/bakeoff/logs/<lane>.md` × 5 (copies of each lane's final `LOG.md`), `docs/decisions/0013-art-direction-and-engine.md`
- Modify: `docs/decisions/README.md` (row 0013), `docs/bakeoff/README.md` (link results)

**Interfaces:**
- Consumes: `bakeoff decide`, `bakeoff gallery --lanes-dir`, `bakeoff results-md`, `preview publish`; every lane's `bakeoff/<lane>/` (read from the lane branches with `jj file show -r bakeoff/<lane> ...` into a temporary directory).
- Produces: the judging page `https://sjawhar.github.io/project-violet/review/pr-<N>/bakeoff.html`, Sami's scores as data, decision 0013.

- [ ] **Step 1:** Open the judging PR early: `jj new master -m "Bake-off results and decision (Phase 1 gate)"`, `docs/bakeoff/results.md` from `bakeoff results-md` (status table; lanes still in progress show as such), bookmark `phase1/judging`, push, `PR=$(gh api ... --jq .number)`. Re-run Steps 2–3 whenever a lane delivers.
- [ ] **Step 2:** Gather: `for lane in g-a g-d u-d g-c control; do for f in $(jj file list -r bakeoff/$lane bakeoff/$lane); do mkdir -p /tmp/lanes/$(dirname $f); jj file show -r bakeoff/$lane $f > /tmp/lanes/$f; done; done` (LFS media: check the branch out in a temporary workspace instead when `jj file show` yields pointer text), then `uv run --project tools/bakeoff bakeoff gallery --pr $PR --lanes-dir /tmp/lanes/bakeoff` → `out/review/pr-$PR/bakeoff.html` + `index.html`. If `preview build` refuses a capture because it has no sidecar, add `--allow-unrecorded` to `tools/preview` (renders the item with the caption "review media, not a shipped asset") in a small PR to master and use it — captures are documentation of a build, not assets.
- [ ] **Step 3:** `uv run --project tools/preview preview publish $PR`; open the URL on a phone: every delivered lane shows a playing capture, four stills, the measured numbers, links to its branch and CI run; blocked lanes show their blocker text. Put the URL and the scoring block format in the PR body; ask Sami on the judging PR and issue #4 to score (≤ 1 h: five captures, judging.md).
- [ ] **Step 4:** Transcribe Sami's comment into `docs/bakeoff/scores.json` (`source` = comment URL), `uv run --project tools/bakeoff bakeoff decide docs/bakeoff/scores.json`, re-run `gallery` + `publish` so the page shows scores beside numbers, regenerate `results.md`.
- [ ] **Step 5:** `docs/decisions/0013-art-direction-and-engine.md` in the format of the existing records: Decision = direction and engine from `decide`; Source = Sami's scoring comment quoted, with the rule applied step by step (which lanes got yes, totals, tie-break); Consequences = Phase 2 builds on that stack, the losing lanes' branches stay as reference, and what the Control lane showed about a full-3D protagonist (if it ran; decision 0012 has it waiting). Add the README row. Copy each lane's `LOG.md` to `docs/bakeoff/logs/`.
- [ ] **Step 6:** Push, ask for approval, squash-merge after Sami approves. Phase 1 gate check (spec Acceptance 3): the gallery page, each lane's CI run, the decision record — all linked from issue #4 in a closing comment.

## Acceptance surfaces (the pass over every deliverable)

| Deliverable | Surface a human touches | What drives it |
|---|---|---|
| Shared mechanic, level, briefs | Sami reads the `phase1/shared-inputs` PR with the rendered level PNG inline | `greybox render` + `preview build/publish` (Task 1) |
| Playable Linux build (G-A, G-D, G-C) | Sami runs `out/<lane>/violet-<lane>.x86_64` on his laptop and plays to the goal with WASD/Space/Shift/Q | `bash game/<lane>/ci.sh` on machine sami (export + headless smoke), CI artifact |
| Playable Linux build (U-D) | Sami runs `out/u-d/violet-u-d.x86_64` on his laptop | `Build.Linux` via `-executeMethod` on machine sami (Task 9 Step 7) |
| Completability test + color-tag check | Green `bakeoff` workflow run per lane branch in GitHub Actions; `bakeoff/<lane>/reports/*` | `ci.sh` → replay runner (+ `--disable` negative), tag validator (+ `--mutate` negative); Unity: NUnit XML checked by `ci.sh` |
| Capture + stills | The gallery page on Sami's phone; `bakeoff/<lane>/capture/` on the branch | `scripts/capture-godot.sh`, `scripts/capture-unity.sh`, `render_reel.py`; `bakeoff gallery` + `preview publish` |
| Lane log (hours, dollars, interventions, friction, blockers) | Numbers on the gallery row; `docs/bakeoff/logs/<lane>.md` on master | `bakeoff log-check` in CI; `bakeoff gallery` |
| Decision | `docs/decisions/0013-...md` merged; the judging PR | `bakeoff decide` over `scores.json`, Sami's approval |
| oryx GPU | `scripts/oryx-gpu-check.sh` prints `oryx GPU OK`; issue #4 comment | Task 0; every GPU step is gated on it and serialized with `flock` |

## Week plan (guidance; accounts move things)

Day 0: Task 1 PR + approval; Tasks 2–3 in parallel. Day 1: G-A and G-D greybox milestones green in CI; Task 4 concept PR. Day 2: parts; the rig, the kit and G-C's SVGs start as soon as their own inputs are ready; Unity starts the day Sami's account exists; G-A painted world. Day 3–4: rig lands → lanes swap in the character; kit lands → D lanes dress; U-D tests + build on sami. Day 5: captures on oryx; Control reel (waiting on decision 0012, unless it changes). Day 6: gallery published, Sami scores. Day 7: decision 0013 merged.

## Top risks

1. **Agent-authored art quality.** The rig, the 3D kit, and G-C's SVGs are all agent-authored instead of bought (Spine, Meshy, Recraft — decision 0012); they may look worse than a paid tool's equivalent would have. That is exactly what the bake-off measures: `character_appeal` and `visual_quality` scoring captures it, and a bad result here is evidence for a later purchase decision, not a plan failure.
2. **Unity lane.** COSMIC is unsupported (GNOME only), the MCP needs a Unity Cloud project plus a paid AI subscription, and the editor needs Sami at the keyboard several times. The spec makes a blocker a valid result; the C# and tests are written first so a single good day suffices.
3. **Agent-authored animation quality.** No verified example exists of an agent producing a platformer moveset (research); `spinerig`'s generated scarf follow-through and the keyed animations may read robotic. Iterate on the GIF previews before lanes integrate; the same rig goes to every lane, so the comparison stays fair.
4. **oryx GPU.** Unusable until Sami reboots; concurrency crashed it. Only Blender renders depend on it (the kit's `build_kit.py` and its turntables, and the Control reel, if it ever runs) and all have CPU fallbacks; everything else — the image APIs — runs on machine sami or is cloud and GPU-independent.
5. **Headless/offline capture friction.** Godot Movie Maker under XWayland on the 890M, Unity PlayMode tests in batchmode, PhysX/Godot replay drift between ticks. Replays assert cells and "goal by tick", never positions; captures are offline-rendered (frame-exact); each lane's `friction` list is part of what Sami sees.

## Hardening ledger
