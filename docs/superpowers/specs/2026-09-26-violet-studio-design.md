# Violet studio: foundation, art-direction bake-off, and build-out

Status: design approved by Sami section by section on 2026-09-26; the two decisions below are open · research behind this spec: `docs/research/2026-09/` · each phase gets its own implementation plan, starting with Phase 0

## Summary

Violet, a story-driven color-resonance platformer first designed in 2017–2019, is being restarted from scratch for a commercial Steam release. AI agents will produce most of the work, and Sami gives feedback throughout and final approval. This spec sets up the studio in three steps:
1. **Foundation:** repo, tools, provenance, and the pull-request review loop.
2. **One-week bake-off:** decides the art direction and the engine from measured agent output.
3. **Build-out:** the infrastructure on the winning stack, while the story and mechanics are brainstormed separately under their own spec.

It has worked when each phase's gate below passes on this machine and Sami approves the result.

## Decisions needed

**1. Can your friend's 2018 illustration go in the public repo?** The 2018 "Resonate" deck includes a full-body illustration of Violet drawn by your artist friend. Committing it publishes their drawing.
- *Include it:* you've confirmed they're fine with it being public.
- *Keep it out:* the archive describes the drawing in words and includes no image of it.

**2. Approve the accounts and purchases for Phases 0–1?** Strike any you don't want.
- Spine Professional: $379 once, for the cutout-rigged protagonist.
- Unity AI subscription: about $10/mo, the only channel Unity's terms allow for agents.
- Meshy or Tripo: about $20/mo, 3D generation for the D lanes.
- Recraft paid plan: about $12/mo; the free tier is personal-use only.
- OpenAI and Google image APIs: usage-based.

A Unity Pro seat (about $2,310/yr) is needed only if Unity wins the bake-off.

## New since we talked

These points are mine, not things you settled:
- **Spec location:** this spec is the body of a root GitHub issue in project-violet, and a copy is committed at `docs/superpowers/specs/2026-09-26-violet-studio-design.md`. Inferred from your rule that specs live in issue bodies, plus the choice of GitHub over Dispatch.
- **LFS file types:** images, audio, video, 3D models, Blender files, Spine exports, and PSDs.
- **LFS push:** a push wrapper runs `git lfs push` before `jj git push`, because jj runs no git hooks.
- **Review gallery:** lives under a new `review/` directory on the existing `gh-pages` branch, so your 2019 web build stays where it is.
- **Awards risk:** some awards exclude any generative AI (the Indie Game Awards revoked Clair Obscur's wins in December 2025), so Violet will be ineligible for those. This follows from the AI-content decision.
- **Old Legion's asks:** at the Sep 9 commit, asks run through the old Dispatch service, which stored everything as GitHub issue comments. That service has to run in the isolated instance.
- **Legion's own repo:** the old Legion runs from a `github-era` branch of the Legion repo, with the startup-deadlock fix (PR #883) cherry-picked. The Legion repo's `main` is not touched.
- **Spine edition:** Professional rather than Essential. Essential lacks the meshes and IK constraints needed for scarf and cloth motion.
- **Disk guard:** below 20 GB free, the lead session stops starting new lanes and cleans caches and finished lane workspaces first.

## Acceptance

1. **Phase 0 gate: the smoke test.** An agent runs the image tool to make one head-scarf concept for the protagonist. A provenance record sits beside the file. A PR shows the image inline and links its gallery page. CI passes. Sami approves and the PR merges. A fresh clone contains the real image, not an LFS pointer file. Check: the merged PR, the green CI run, and the fresh clone.
2. **Legion trial.** It decides who runs Phase 2 and does not block Phase 1. In the isolated GitHub-era instance, a trivial issue on project-violet goes architect → implementer → tester → reviewer and ends merge-ready, while the current Legion keeps running undisturbed. Check: the issue timeline and PR, `legion status` for both instances, and the current instance's open work unaffected.
3. **Phase 1 gate: the bake-off.** Every lane delivers or records a blocker: a playable Linux build, a 60–90 second capture with stills, a passing completability test and color-tag check, and a log of agent hours, dollars and interventions. Sami scores every lane on the gallery page and the winning direction and engine are recorded in `docs/decisions/`. Check: the gallery page, each lane's CI output, and the decision record.
4. **Phase 2 gate: infrastructure.** A throwaway test room goes through every pipeline: generated art and audio with provenance, level text imported into a scene, tests and capture, vision review, colorblind simulation, an agent playtest through the MCP bridge, and approval on a PR. Check: the PR, the CI run, and the capture.

## Requirements

| Requirement | Where it comes from |
|---|---|
| Target a commercial Steam release | Sami selected "Commercial Steam release" |
| Agents produce most of the work; Sami approves everything that ships; Steam's Pre-Generated AI disclosure is filed | "It's going to be collaborative the whole way, I'll give lots of feedback and final approval, but yeah AIs will do most of it" |
| Art direction: D (2.5D) if agents can do it, otherwise A (painted 2D); C (flat vector) acceptable | "It's D if agents can do it, otherwise A. C is also reasonable" |
| Bake-off before committing to a stack | Sami selected "Bake-off first" |
| Specs, planning and asset approval on GitHub, not Dispatch | "should we use dispatch for this? I think I'd rather not. Can't we just use github?" |
| The engine choice ignores license cost | "if you're going with godot because of cost reasons or something, please don't. I have money" |
| The bake-off includes Unity lanes | Sami selected "Yes, add Unity lanes" |
| The repo stays public | Sami selected "Keep it public" |
| Legion runs from a pre-Dispatch commit | "Just checkout an older commit :)" |
| Mechanics, abilities and feel are designed in the separate brainstorm; nothing in this spec fixes them | "You're getting way ahead of youreself on the core and feel. That's still TBD, we need to brainstorm all of that." |
| Agents work in Unity only through Unity's official MCP | Unity Terms of Service §17.2 (June 30, 2026) |
| Every generated asset carries a provenance record; CI blocks unrecorded or unapproved assets | inferred: Steam disclosure requires knowing what was generated and how, and vendors recommend keeping these records |
| Third-party art is linked, never committed | inferred: the repo is public |

## Design

**Phase 0: Foundation** (run by a lead session with subagents)
- **Repo cutover:**
  - Colocate jj.
  - Tag the current `master` (`ca6a5a7`) as `unity-2019-prototype` and push the tag.
  - Remove the Unity project in one commit.
  - Leave the `gh-pages` branch untouched apart from the new `review/` directory.
  - Add `.gitattributes` LFS rules and gitignore rules for Godot, Unity and `.superpowers/`.
- **`docs/archive/2017-2019/`:** both conceptions as Markdown (the Resonate deck and Capstone drafts; the Scarlet design doc and Story Bible), the digest and its supplement, and your own sketches and 2019 sprites. Third-party inspiration images are linked only.
- **`docs/research/2026-09/`:** every research report, with the corrections noted.
- **`docs/decisions/`:** one record per settled decision, citing your words.
- **`AGENTS.md`:** where canon lives, the approval rule, the provenance rule, jj conventions, and the LFS push step.
- **Toolchain:** pinned with mise where available (Godot 4.7.2, Blender, ffmpeg, FluidSynth, ImageMagick, LDtk). Unity Hub plus Unity 6.3 LTS; Sami signs in once.
- **Generation tools:** one command-line tool per modality (image, 3D, music, sound effect), each with a thin adapter per provider. Every output gets a provenance record: tool, model and version, prompt, seed, inputs, date, human edits, approver. API keys live in secretsd.
- **Preview tool:** renders PNG grids, animation GIFs, 3D turntables and audio player pages into the Pages gallery, and writes the PR description snippet.
- **CI (GitHub Actions):**
  - The provenance check.
  - An LFS pointer check.
  - Generation of the Steam disclosure text.
- **Legion (GitHub-era instance):**
  - A `github-era` branch of the Legion repo from `32f4f7d0` (2026-09-09), plus the PR #883 startup-deadlock fix.
  - Its own jj workspace, state directory and ports.
  - An `ompo violet` profile whose plugin tree pins that branch's SHA.
  - Project key `VIOLET`.
  - The old GitHub-backed ask service running beside it.
  - A GitHub Projects board for project-violet.

**Phase 1: Bake-off** (lead session; lanes run in parallel on `bakeoff/<lane>` branches that never merge)
- **Shared inputs:**
  - A throwaway test mechanic: red for dash, green for double-jump, color-tagged walls and platforms, and the grayscale-to-color reveal.
  - One greybox level written as text.
  - The protagonist brief: robe, and a scarf that shows the active color.
  - The desert biome.
- **Shared protagonist:**
  - Built as a Spine cutout rig: one painted image per body part, with the skeleton and animations written by an agent as Spine JSON.
  - Moves: idle, run, jump, dash, double-jump and land, with the scarf trailing behind.
  - Played through the official Spine runtimes in both Godot and Unity.
- **Lanes:**

  | Lane | Engine | World |
  |---|---|---|
  | G-A | Godot 2D | Painted world with parallax layers |
  | G-D | Godot 3D | AI-generated 3D kit, painterly or toon shading, real colored lights |
  | U-D | Unity 6.3 URP, official MCP only | Same as G-D |
  | G-C | Godot 2D | Recraft SVG kit; environment only |
  | Control | Blender | Full 3D protagonist |
- **Judging:** a gallery page with Sami's scores next to the measured numbers.
- **Decision:** D wins if Sami answers "yes, I'd ship this direction" for at least one D lane. Otherwise A wins, and C is chosen instead only if Sami prefers it. The engine is whichever lane Sami scored higher for the winning direction; a tie goes to Godot, because agents can edit its files as text.

**Phase 2: Build-out** (Legion if the GitHub-era instance passed, otherwise the lead session)
- Infrastructure on the winning stack:
  - A prototyping kit that commits to no mechanic.
  - The text-to-scene level pipeline.
  - The QA harness: test runners, replayed-input tests, capture, vision-model review, colorblind simulation, and an MCP bridge for agent playtests. The solver follows once the abilities are designed.
  - The art and audio pipelines with provenance.
  - The studio role skills.
  - CI.
- **The design brainstorm runs in parallel under its own spec:**
  - Story: space, wasteland, or a merge.
  - Mechanics and feel, structure, protagonist and name, and the ending.
- Phase 3, the vertical slice of the game as designed, follows both.

## Errors

| Condition | Behavior |
|---|---|
| A generation provider fails | The command exits non-zero and writes no file; retrying is the caller's decision |
| An asset in the game tree lacks provenance or an approved PR | CI fails |
| An LFS object is missing on the remote | The push wrapper stops; CI's pointer check fails |
| A Unity lane is blocked (license, COSMIC, MCP) | The blocker is recorded as that lane's result; the other lanes continue; no third-party Unity MCP is ever used |
| The GitHub-era Legion fails acceptance | Phase 2 runs with the lead session; Legion is revisited |
| An account or purchase is not yet approved | Only the lanes that need it wait |
| Disk free space falls below 20 GB | The lead session stops new lanes and cleans caches and finished lane workspaces first |

## Testing

- Acceptance 1: run the smoke test live; read the PR, the CI run and the fresh-clone LFS check.
- Acceptance 2: run the Legion trial issue end to end, then check both instances' status.
- Acceptance 3: each lane's CI job, plus the gallery review.
- Acceptance 4: the test-room PR and its CI run.

## Rejected

- **Unreal:** it needs about 43–65 GB against 79 GB free and a GPU with 8 GB+ of video memory, its C++ live coding is Windows-only, and its assets are binary.
- **Dispatch for this project:** Sami would rather use GitHub.
- **Third-party Unity MCP servers:** Unity's terms (§17.2) allow only a framework Unity operates or designates.
- **Committing to one direction before measuring:** Sami chose the bake-off.
- **A full-3D protagonist as the plan:** no agent-produced rigged 3D character with a platformer moveset exists anywhere. It stays as the control lane.
- **Frame-by-frame AI-painted animation:** image models drift in proportions between frames. The cutout rig avoids that by construction.
- **Using `spine-animation-ai` directly:** its PolyForm Noncommercial license forbids commercial use; we reimplement its technique.
- **Suno and Udio:** neither offers an official API for general developers, and Udio's exports are restricted. **MusicGen:** its weights forbid commercial use.
- **Making the repo private:** Sami chose public.
- **Adding GitHub mode to current Legion:** a large change to a repo under active rewrite. Sami chose the old commit instead.
