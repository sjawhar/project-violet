# Violet

Violet is a story-driven puzzle-platformer about light and color, first designed in 2017–2019 and now being rebuilt from scratch for a commercial Steam release. AI agents produce most of the work; Sami Jawhar directs it and approves everything that ships.

## Where things live

| Path | What it is |
|---|---|
| `docs/superpowers/specs/` | Approved designs. Start with [the studio design](docs/superpowers/specs/2026-09-26-violet-studio-design.md). |
| `docs/superpowers/plans/` | Implementation plans for each phase |
| `docs/decisions/` | One record per settled decision, with its source |
| `docs/research/` | Research behind the decisions, with corrections noted |
| `docs/archive/` | The 2017–2019 design documents and prototype media |
| `tools/` | Studio tooling (provenance records, asset generation, review previews) |
| `AGENTS.md` | Conventions every agent working here follows |

The 2019 Unity prototype is kept at tag [`unity-2019-prototype`](https://github.com/sjawhar/project-violet/tree/unity-2019-prototype). Work that was staged but never committed is on branch [`unity-2019-wip`](https://github.com/sjawhar/project-violet/tree/unity-2019-wip).

## Setup

```bash
mise install                 # pinned toolchain from mise.toml
git lfs install --local      # binary assets are stored in Git LFS
```

## How work lands

Every change goes through a pull request that Sami approves. Every asset carries a provenance record (see `AGENTS.md`).
