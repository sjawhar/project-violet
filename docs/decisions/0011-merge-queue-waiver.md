# Tooling and docs PRs merge through the pr-queue organizer without the six gates

- **Date:** 2026-09-27
- **Status:** settled; the queue organizer is waiting on Sami's one-line confirmation before merging on it again

## Decision

Pull requests that change tooling, docs, or infrastructure are merged by the pr-queue organizer, the session on machine sami-agents that holds the `pr-queue` Envoy role. The owner sends it a READY packet: head sha, base, file count, CI state at that head, and the evidence in the PR body. The bar is CI green at the head plus that evidence. The six-gate process used on other repositories (thermonuclear review pair, oracle red-team, and the rest) does not apply here.

## Source

Sami, typed into the lead session (omp session `01a0df9a-4873-7525-9b00-bfa1425e13e5`, machine sami, transcript line 844, record `c3a8dc82`, 2026-09-27T05:22:40.788Z): "work with the queue organizer on sami-agents to merge. you dont need to go through the six gates, this is lower stakes"

## Consequences

- PRs that ship generated art, audio, or other player-facing content still need Sami's own approval, per decision 0002 ("I'll give lots of feedback and final approval").
- The queue organizer merged PRs #7, #11, #6 and #10 on this ruling. It then paused further project-violet merges until Sami confirms the ruling himself, because it can't read the lead session's transcript.
- Branch protection on `master`, requiring the `provenance` check, lets the queue's normal machinery run here. That's on Sami's list in issue #4.
