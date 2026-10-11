# Violet sessions leave sami-agents alone; authors merge their own tooling and docs PRs

- **Date:** 2026-10-11
- **Status:** settled

## Decision

Violet sessions don't send messages or requests to any session on machine sami-agents. Those are Sami's work agents, and that includes whichever session holds the `pr-queue` Envoy role.

Tooling, docs and infrastructure PRs are now merged by the session that opened them, with the same bar decision 0011 set: CI green at the head, plus the evidence in the PR body. The merge is a squash, done as the repository's GitHub App, with the head sha pinned. The six-gate process still doesn't apply. This replaces decision 0011's rule that the pr-queue organizer merges these PRs; the rest of 0011 stands.

## Source

Sami, typed into the lead session (omp session `01a0df9a-4873-7525-9b00-bfa1425e13e5`, machine sami, transcript line 5812, record `01890585`, 2026-10-11T02:01:40.489Z). He asked why the lead had sent PR #44's merge request to the "legion po" session, the `pr-queue` holder at the time, and ruled that sessions on sami-agents are his work agents and Violet sessions must not bother them. Who merges in the queue's place is the lead's own call, made under his standing instruction that agents merge their own approved work.

## Consequences

- `AGENTS.md` rule 1 now says the author merges, and tells sessions not to contact sami-agents.
- PR #44 was the first PR merged this way.
- PRs that ship generated art, audio or other player-facing content still need Sami's own approval (decision 0002).
