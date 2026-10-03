# Mechanics round 1: color trigger, movement, blue, yellow, wall jump, difficulty, structure

- **Date:** 2026-10-02
- **Status:** settled

## Decision

Round 1 of the mechanics and feel brainstorm (decision 0009) settles six of its open questions, and sends a seventh, wall jump, to a round-2 trial:

- **What makes the world change color:** using an ability does it. This is the 2019 design: using a color's ability makes the world resonate that color briefly (1.5 s in the 2019 code), and while it resonates, same-color walls are passable and same-color platforms vanish.
- **Baseline movement:** the tuned version (grace period, early jump buffering, short hop versus full jump, jump hang, faster falling, corner nudges), not the bake-off's plain movement.
- **Blue's ability:** swing.
- **Yellow's ability:** stomp (unchanged). Red keeps dash and green keeps double jump, as before.
- **Wall jump:** not decided yet. It goes into round 2 of the lab as a trial, not as a shipped mechanic.
- **Difficulty:** a gentle main path with hard rooms optional.
- **Structure:** linear chapters with side paths.

## Source

Sami's answers, given in his own session on 2026-10-02 after he played the mechanics lab, posted as this comment ([issue #41, comment](https://github.com/sjawhar/project-violet/issues/41#issuecomment-5961808862)):

| Question | Sami's answer |
|---|---|
| 1. What makes the world change color? | Using an ability does it (the 2019 design) |
| 2. Baseline movement | Tuned |
| 3. What is blue? | Swing |
| Yellow | Keep stomp |
| 4. Wall jump | Try it in round 2 |
| 5. Difficulty | Gentle path, hard optional rooms |
| 6. Structure | Linear chapters with side paths |

## Consequences

This narrows decision 0009 for these seven questions (six settled here, wall jump sent to a round-2 trial); it doesn't edit that record. 0009's other open items stay open: the ending, and the parts of the protagonist that decision 0015 does not settle. Round 2 of the lab builds real rooms around these answers: red dash, green double jump, yellow stomp, and blue swing, all under the ability-triggers-resonance rule, with tuned movement. Wall jump stays a trial in round 2, not a decision; level design can't yet assume it. Nothing here fixes tuning numbers (grace period length, resonance window, swing physics); those are round 2's job.
