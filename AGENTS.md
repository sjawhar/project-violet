# Violet studio: agent conventions

Violet is a story-driven puzzle-platformer being built for a commercial Steam release, mostly by AI agents. Sami Jawhar directs the work and approves everything that ships. Read the [studio design](docs/superpowers/specs/2026-09-26-violet-studio-design.md) and the [decisions](docs/decisions/README.md) before starting work.

## Where things live

| Path | Contents |
|---|---|
| `docs/superpowers/specs/` | Approved designs. A new subsystem gets its own spec before code. |
| `docs/superpowers/plans/` | Implementation plans, one per phase |
| `docs/decisions/` | Settled decisions, each quoting its source. Add a record when Sami settles something; never edit an old record to change a decision. |
| `docs/research/` | Research reports; its README lists known corrections |
| `docs/archive/` | The 2017–2019 design documents (two conceptions: the space version "Resonate" and the wasteland version "Scarlet") |
| `tools/` | Studio tools, each a standalone uv project |
| GitHub issues | Specs for work in flight; the root issue is #4 |

## Rules

1. **Nothing ships without Sami's approval on a pull request.** Every change lands through a PR. The PR body states what was run and what was observed. After Sami approves, the agent that owns the PR squash-merges it.
2. **Every asset carries a provenance record.** An asset under a root in `provenance.toml` has a sidecar `<asset>.provenance.json`:
   - Generated assets: `tools/gen` writes the record itself.
   - Anything else: `uv run --project tools/provenance provenance record ASSET --kind ... --origin ... --license ...`.
   - A manual edit to an asset: `provenance edit ASSET --by NAME --description TEXT`.
   - CI runs `provenance check` and `provenance lfs-check` on every PR.
3. **The repository is public.** Never commit secrets, credentials, or third-party art. Third-party references are links with a one-line description. Generation inputs must be files in the repo; never feed third-party images into generation.
4. **Code never calls an LLM.** Tools may call image, 3D, or audio generation APIs. Review "by a model" means an agent session looks at captured output; CI never calls a model API.
5. **Mechanics are undecided.** The resonance rules, colors, abilities, feel, structure, protagonist, and ending are designed in a separate brainstorm with Sami. Don't encode a mechanic in shared infrastructure. Prototypes and bake-off lanes label theirs as throwaway.
6. **API keys come only from `secrets KEY -- command`.** Sami approved `OPENAI_API_KEY` and `GEMINI_API_KEY` for art generation. No other paid key or account is approved for Violet yet; ask before using one.

## Version control

- jj, not git. Commit identity is `sami@thecybermonk.com`.
- Binary assets go through Git LFS (`.gitattributes`). jj runs no git hooks, so push LFS objects first, then the bookmark:

  ```bash
  git lfs push origin <bookmark>
  jj git push --bookmark <bookmark>
  ```

- Open PRs with `gh api repos/sjawhar/project-violet/pulls -f title=... -f head=<bookmark> -f base=<base> -F body=@<file>`. On this setup, `gh pr create` can hang while it inspects a large local diff.
- Stack dependent work as stacked PRs rather than waiting for merges.

## Machines

- **sami:** Sami's laptop. Radeon 890M integrated GPU, about 80 GB free disk. Keep large caches and heavy renders elsewhere.
- **oryx:** RTX 3070 (8 GB) available offscreen for CUDA, Vulkan, and Blender Cycles; 2.6 TB free disk. Heavy lanes run here. Agents must never reboot oryx or trigger anything that needs a reboot.

## Toolchain

`mise install` installs the pinned tools in `mise.toml`: Godot 4.7.2, ffmpeg, ImageMagick, git-lfs, uv, and Blender 5.2.2. Blender comes from the Clarkson University mirror through mise's `http` backend, checked against the sha256 that Blender publishes, because `download.blender.org` answers scripted downloads with a 403.
