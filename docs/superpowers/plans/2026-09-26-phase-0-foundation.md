# Phase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get the project-violet repo, tools, and review loop ready for agents: repo cut over from Unity, canon and archive docs, provenance and CI, generation and preview tools, a pinned toolchain, and the GitHub-era Legion trial. Phase 0 ends with the smoke test.

**Architecture:**
- **Monorepo on GitHub.** `docs/` is canon. `tools/` holds standalone uv projects: `provenance`, `gen`, `preview`. The engine project arrives in Phase 1 lanes.
- **Every asset has a provenance sidecar.** CI checks sidecars and LFS pointers.
- **Every change lands through a PR that Sami approves.** Branch protection enforces it.

**Tech Stack:**
- jj colocated with git; Git LFS through the jj fork's filter drivers.
- GitHub Actions; uv with Python 3.12 and pytest.
- mise-pinned Godot 4.7.2, Blender, ffmpeg, ImageMagick, git-lfs.

**Spec:** `docs/superpowers/specs/2026-09-26-violet-studio-design.md` (root issue: https://github.com/sjawhar/project-violet/issues/4)

## Global Constraints

- The repo is public. No secrets, no third-party art, no internal tooling credentials in any commit or fixture. Third-party references are links.
- Nothing ships without Sami's approval on a PR (branch protection plus CODEOWNERS `* @sjawhar`).
- Code never calls LLM APIs. Model review of output means an agent session looks at the captures.
- Mechanics, abilities, and feel are undecided. No task encodes a mechanic.
- jj, not git, for version control. Commits use `sami@thecybermonk.com`.
- jj runs no git hooks: push LFS objects with `git lfs push origin <bookmark>` before `jj git push`.
- Generation tools write a provenance sidecar for every output via `provenance record`.
- Provider API keys come only from `secrets <KEY> -- <cmd>`. Sami approved the existing `OPENAI_API_KEY` and `GEMINI_API_KEY` for art generation on 2026-09-26 ("Yes, you can use those keys for art generation"). Audio keys are not yet approved.

## Owners and order

| Task | Owner | Depends on | Issue |
|---|---|---|---|
| 1. Repo cutover | lead (machine sami) | none | this plan |
| 2. Archive, decisions log, AGENTS.md, spec fixes | lead | 1 | this plan |
| 3. Provenance records, Steam report, CI checks | oryx agent | none | #5 |
| 4. Generation tool (`tools/gen`), image first | lead | 3's `provenance record` | new issue |
| 5. Preview tool and Pages review gallery | oryx agent | 3 | new issue |
| 6. Branch protection and CODEOWNERS | lead (CODEOWNERS file); Sami enables protection | 1 | this plan |
| 7. Toolchain on each machine | each machine's agent | 1 | this plan |
| 8. GitHub-era Legion instance | oryx agent, after #5. oryx runs no Legion today, so nothing live collides | 1 | new issue |
| 9. Smoke test (Phase 0 gate) | lead | 1–7 | #4 |

---

### Task 1: Repo cutover

**Files:**
- Delete: `Assets/`, `ProjectSettings/`, `Packages/`, `Logs/`, `project-violet.sublime-project`, `.editorconfig` (Unity/C# formatting only)
- Replace: `.gitignore`
- Create: `.gitattributes`, `mise.toml`, `README.md`

**Interfaces:**
- Produces: the LFS patterns in `.gitattributes` that Task 3's `provenance lfs-check` reads. The pinned tools in `mise.toml` for Task 7.

- [ ] **Step 1:** Branch from master: `jj new master -m "Cut over from the 2019 Unity prototype to the studio layout"`, then `jj bookmark create phase0/cutover -r @`.
- [ ] **Step 2:** Delete the Unity project: `rm -rf Assets ProjectSettings Packages Logs project-violet.sublime-project .editorconfig`. The Unity state stays reachable through tag `unity-2019-prototype` (3c632cc) and bookmark `unity-2019-wip` (2c82167).
- [ ] **Step 3:** Write `.gitignore`:

```gitignore
# OS / editors
*~
.DS_Store
.directory
.Trash-*
*.swp
.idea/
.vscode/

# Python / uv
__pycache__/
*.pyc
.venv/
.pytest_cache/

# Godot
.godot/
*.import.tmp
export_presets.cfg.bak

# Unity (bake-off lanes)
[Ll]ibrary/
[Tt]emp/
[Oo]bj/
[Bb]uild/
[Bb]uilds/
[Ll]ogs/
[Uu]ser[Ss]ettings/
*.csproj
*.sln

# Tool outputs
/out/
/previews/
.superpowers/
```

- [ ] **Step 4:** Write `.gitattributes`:

```gitattributes
# Binary assets live in Git LFS. jj's filter drivers run git-lfs clean/smudge;
# jj runs no hooks, so push objects with `git lfs push origin <bookmark>` before `jj git push`.
*.png  filter=lfs diff=lfs merge=lfs -text
*.jpg  filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.webp filter=lfs diff=lfs merge=lfs -text
*.gif  filter=lfs diff=lfs merge=lfs -text
*.psd  filter=lfs diff=lfs merge=lfs -text
*.kra  filter=lfs diff=lfs merge=lfs -text
*.wav  filter=lfs diff=lfs merge=lfs -text
*.ogg  filter=lfs diff=lfs merge=lfs -text
*.mp3  filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text
*.mp4  filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text
*.glb  filter=lfs diff=lfs merge=lfs -text
*.fbx  filter=lfs diff=lfs merge=lfs -text
*.blend filter=lfs diff=lfs merge=lfs -text
*.spine filter=lfs diff=lfs merge=lfs -text
*.pdf  filter=lfs diff=lfs merge=lfs -text
*.zip  filter=lfs diff=lfs merge=lfs -text
```

- [ ] **Step 5:** Write `mise.toml` pinning `godot = "4.7.2"`, `blender` (the latest 4.x LTS or 5.x release in the aqua registry at the time; record the exact version), `ffmpeg`, `imagemagick`, `git-lfs`, `uv`. Run `mise install` and record the resolved versions in the file. No floating versions.
- [ ] **Step 6:** Write `README.md`: what Violet is (two sentences), where canon, research, spec and plans live, how to set up (`mise install`, `git lfs install --local`), and the PR and approval rule.
- [ ] **Step 7: Verify.** `jj st` shows only the intended deletions and new files. `git check-attr filter -- test.png` prints `filter: lfs`. `mise ls --current` shows every pinned tool installed.
- [ ] **Step 8:** Describe, `git lfs push origin phase0/cutover` (a no-op for now), `jj git push --bookmark phase0/cutover`, open a PR against master, and link it from #4.

### Task 2: Archive, decisions log, AGENTS.md, spec fixes

**Files:**
- Create: `docs/archive/2017-2019/README.md`, plus one Markdown file per Violet-relevant source document (listed below), an `images/` directory with Sami-owned images, and the 2018 illustration.
- Create: `docs/decisions/0001-*.md` … one per settled decision.
- Create: `AGENTS.md`.
- Modify: `docs/superpowers/specs/2026-09-26-violet-studio-design.md` (decisions answered; vision-review wording), `docs/research/2026-09/README.md` (digest correction).

**Archive sources** (from Sami's personal Drive; the exports are on machine sami under `/tmp/violet-drive`). Include:
- **Space version (2017–18):** Resonate GDD (deck text plus page renders of Sami's own content), Capstone Assignment 4 (the latest iteration; state that 1–3 are earlier drafts of it).
- **Violet folder:** Character Design (Violet; Violet and Slate; Violet Inspiration), World Design (Inspiration; First Level; Level Map).
- **Scarlet/wasteland (2019):** Scarlet Game Design Document, Scarlet Story Bible, Scarlet High Concept, Violet High Concept, Scarlet Pitch, Scarlet Competitive Analysis, Scarlet Production Schedule.
- **Sami-made media:** Violet idle/run/jump GIFs, Ideation.pdf (hand-drawn mind map), dash-phase.mp4 (prototype capture), and the 2018 Violet illustration. Sami confirmed on 2026-09-26 that its artist is fine with it being public.
- **Excluded:**
  - Third-party inspiration images (pixiv, ArtStation, warosu, Vatican photo): replace each with its source URL and a one-line description.
  - Scarlet-Prototype.zip: it contains a course template's third-party assets; describe it in words only.
  - Course exercises unrelated to Violet (Matrix and western story analyses, board-game prototypes, the Portal SWOT, Nomadly, Project Buffalo, Project Moonlark).

- [ ] **Step 1:** `jj new phase0/cutover -m "Add design archive, decisions log, and AGENTS.md"`, then `jj bookmark create phase0/docs -r @`.
- [ ] **Step 2:** Convert each included document from its `.text.md` export into `docs/archive/2017-2019/<version>/<slug>.md`, where `<version>` is `space-resonate`, `violet-folder`, or `scarlet-wasteland`. Keep the text verbatim. Rewrite image references so Sami-owned images point at `images/` and third-party ones become links.
- [ ] **Step 3:** Write `docs/archive/2017-2019/README.md`. It covers the chronology (space version 2017–18, then Scarlet 2019, then this restart), a table of every file with a one-line summary, and the comparison table from `docs/research/2026-09/archive-supplement.md`.
- [ ] **Step 4:** Write the decision records. Each gets a title, the date 2026-09-26, the decision, Sami's words verbatim as the source, and what it rules out:
  1. Commercial Steam release.
  2. AI produces most content; Sami approves; Steam disclosure is filed.
  3. Art-direction rule: D if agents can, else A; C acceptable.
  4. Bake-off first.
  5. GitHub over Dispatch.
  6. Engine choice ignores cost; Unity lanes included.
  7. Public repo.
  8. Legion from the pre-Dispatch commit.
  9. Mechanics and feel are undecided and go to the design brainstorm.
  10. The 2018 illustration is included.
- [ ] **Step 5:** Write `AGENTS.md`:
  - Where canon, research, specs, plans and decisions live.
  - The approval rule.
  - The provenance rule, with the `provenance record` usage once Task 3 lands.
  - The public-repo rule.
  - The no-LLM-calls-from-code rule.
  - jj and LFS push conventions.
  - That mechanics are undecided until the design brainstorm's spec lands.
- [ ] **Step 6: Spec fixes.**
  - The illustration decision moves to Requirements as answered, citing Sami: "Include it".
  - The purchases decision stays open, recording Sami: "I'm not going to do all of those sign-ups tonight".
  - The QA line becomes "CI captures screenshots; an agent session reviews them".
- [ ] **Step 7:** Research README: add the correction that `origin/master` has one later commit, 3c632cc (2020-05-07). It is a Unity version upgrade: 1,083 modified files, no new files, no `.cs` or `.unity` changes.
- [ ] **Step 8: Verify.**
  - `jj diff --stat` shows only docs and images.
  - `git check-attr filter` reports `lfs` for every image, PDF and MP4.
  - No file under `docs/archive` contains a third-party image. Check: list every image and confirm each one is Sami-made or the approved illustration.
- [ ] **Step 9:** Push LFS objects (`git lfs push origin phase0/docs`), then `jj git push --bookmark phase0/docs`. Open a PR stacked on the cutover PR and link it from #4.

### Task 3: Provenance records, Steam report, CI checks

Owner: oryx agent. Full specification: https://github.com/sjawhar/project-violet/issues/5.

**Interfaces:**
- **Produces:** the sidecar format `<asset>.provenance.json` (schema v1) and a CLI:
  - `provenance record ASSET --kind K --origin O [--tool --tool-version --provider --model --model-version --prompt --negative-prompt --seed --param k=v --input PATH --author NAME]`
  - `provenance check [PATH...]`
  - `provenance steam-report`
  - `provenance lfs-check`
- **Consumed by:** Task 4 calls `provenance record` for every output. Task 9 runs `check`, `lfs-check` and `steam-report`.

### Task 4: Generation tool, image first

**Files:**
- Create: `tools/gen/` (uv project; console script `gen`)
- Test: `tools/gen/tests/`

**Interfaces:**
- **Consumes:** `provenance record` from Task 3, run as a subprocess.
- **Produces:** `gen image --provider {openai|gemini} --model MODEL --prompt TEXT [--size WxH] [--seed N] [--input PATH ...] --out PATH`. It writes the image and its sidecar and exits non-zero with the provider's error on failure, writing no file.
- Provider adapters sit behind one interface: `generate(prompt, size, seed, inputs) -> bytes, model_version`. Swapping a provider is one module.

- [ ] **Step 1:** Build adapters only for the approved providers (OpenAI and Gemini image generation, approved by Sami on 2026-09-26), against the real APIs. No provider is stubbed or faked.
- [ ] **Step 2: Tests.**
  - Argument validation: a missing prompt, an unknown provider, and an existing output file without `--force` each exit non-zero.
  - An output always has a valid sidecar: `provenance check` passes on the output directory after a real generation run with an approved key.
  - A failed provider call leaves no file behind: point the adapter at an invalid model name and assert both the error and the absence of a file.
- [ ] **Step 3:** Implement the OpenAI (`gpt-image` family) and Gemini image adapters, running under `secrets OPENAI_API_KEY -- ...` and `secrets GEMINI_API_KEY -- ...`.
- [ ] **Step 4:** Push, open a PR, and link it from its issue.

### Task 5: Preview tool and Pages review gallery

Owner: oryx agent after Task 3. The issue is opened when Task 3's PR is up.

**Interfaces:**
- **Produces:** `preview build PR_NUMBER PATH...`, which renders:
  - image grids (ImageMagick `montage`),
  - animation GIFs from frame sequences or MP4 (ffmpeg),
  - audio player pages (HTML5 `<audio>`, plus a waveform PNG from ffmpeg `showwavespic`),
  - 3D turntables (Blender `--background` script to MP4).

  The output goes to `out/review/pr-<n>/`, with an `index.html`.
- **Also produces:** `preview publish PR_NUMBER`, which commits `out/review/pr-<n>/` to the `gh-pages` branch under `review/pr-<n>/` without touching existing files, and prints the Markdown snippet for the PR description. The snippet has inline PNG/GIF thumbnails (raw.githubusercontent URLs) and the gallery URL `https://sjawhar.github.io/project-violet/review/pr-<n>/`.
- Pages must serve from `gh-pages`: check that the repo's Pages source is that branch before publishing, and fail loudly if not.

### Task 6: Branch protection and CODEOWNERS

- [ ] **Step 1:** In the cutover PR, add `.github/CODEOWNERS` containing `* @sjawhar`.
- [ ] **Step 2:** Ask Sami to enable a master branch rule: require a pull request, require review from Code Owners, require the provenance workflow status check, and block force pushes. The GitHub App has no administration permission, so this is his step. It takes one ask with the exact settings.
- [ ] **Step 3: Verify.** `gh api repos/sjawhar/project-violet/branches/master/protection` shows the rule. After that, a direct `jj git push --bookmark master` is rejected.

### Task 7: Toolchain on each machine

- [ ] **Step 1:** In a checkout that has Task 1 merged: `mise install`, then `mise ls --current`. Record the output in a comment on #4.
- [ ] **Step 2:** `git lfs install --local`, then clone fresh and confirm that LFS files materialize as real files, not pointers.
- [ ] **Step 3: Machine sami.** Install Unity Hub (official Linux .deb repo) and Unity 6.3 LTS. Sami signs in once; that's an auth step, asked when he is at the keyboard. Record the Unity editor version and whether the editor opens under COSMIC.
- [ ] **Step 4:** Install FluidSynth (apt) and LDtk (GitHub release AppImage; record the version) where lanes need them. They're only needed by Phase 1 lanes, so this can wait for Phase 1 planning.

### Task 8: GitHub-era Legion instance

Owner: the oryx agent after #5. oryx runs no Legion daemon today (checked 2026-09-26), so the instance runs there with no live Legion to collide with; only the globally installed Legion plugin's skills need a separate omp profile. Scope, from the spec:
- A `github-era` branch in `sjawhar/legion` from `32f4f7d0`, plus the PR #883 startup-deadlock fix.
- An isolated instance: its own jj workspace, state directory and ports, an `ompo violet` profile whose plugin tree pins that branch's SHA, and project key `VIOLET`.
- The old GitHub-backed ask service, plus a GitHub Projects board for project-violet.
- Acceptance: a trivial issue flows architect → implementer → tester → reviewer to merge-ready, and the current Legion is undisturbed. The current Legion's `main` is never touched.

### Task 9: Smoke test (Phase 0 gate)

- [ ] **Step 1:** `gen image` makes one head-scarf concept for the protagonist into `assets/concept/`, with its sidecar.
- [ ] **Step 2:** `preview build` and `preview publish` run for the PR.
- [ ] **Step 3:** Open the PR with the inline preview and gallery link. CI passes: provenance check and LFS check.
- [ ] **Step 4:** Sami approves and the PR merges.
- [ ] **Step 5:** A fresh clone contains the real PNG, not a pointer, and `provenance steam-report` lists the concept under AI-generated art. Post the evidence on #4.
