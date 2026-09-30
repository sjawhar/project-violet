# Bake-off shared costs (THROWAWAY)

Money spent on bake-off inputs that serve every lane, not one. Lane-specific spend, such as G-A's painted tiles, is in that lane's `bakeoff/<lane>/LOG.md` under `costs` (the format is `docs/bakeoff/lane-log-format.md`).

`tools/gen` records no cost, and there is no billing export. So a dollar figure appears only where the provider reported per-call usage, priced at the model's published rates. Anything else is a count of calls, and every derived figure is marked as an estimate.

| Item | Calls | USD | Evidence |
|---|---|---|---|
| Phase 0 smoke-test concept (#13) | 1 gpt-image-2 at 1024x1024, quality low; 1 gemini-3.1-flash-image at 1024x1024 | not measured | The lead's account of the run, 2026-09-28 |
| `tools/gen` live tests (#10, #20) | about 10 OpenAI and 4 Gemini, mostly 1024x1024 at quality low, one at high | not measured | The lead's account of the runs, 2026-09-28 |
| Protagonist concept, `violet-turnaround.png` (#19) | 3 gpt-image-2 at 1536x1024: 2 at quality low (the first concept and a regeneration, 2026-09-27 ~06:40Z), 1 at quality high (the merged regeneration, 09:19Z) | not measured | The lead's account; the merged image's provenance record shows quality high |
| Protagonist parts (#28), first two rounds (2026-09-27) | 19 gpt-image-2 at quality high | about 4.25, estimated | Usage wasn't logged. The estimate is 19 calls at the $0.22 per call measured in the third round |
| Protagonist arms (#28), third round (2026-09-28) | 6 gpt-image-2 at quality high: 4 kept, 2 rejected | 1.34 measured: 0.89 kept, 0.45 rejected | Token usage as OpenAI reported it for each call |
| 3D desert kit (#31) | none | 0 | One agent-written Blender script, `build_kit.py`; no API calls |
| Violet glow-up rounds 0-2, technique A | 3 gpt-image-2 at 1024x1024, quality high (head repaints, including one rejected image) | about 0.66, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; $0.22 per image call; no per-call usage logged |
| Violet glow-up round 3 (#4, Task 11b, PR #36), technique A's calibration round: repainted torso/hips/sleeves for value structure, recolored the thigh-wrap legs | 14 gpt-image-2 at 1024x1024, quality high: 9 charged (6 kept: torso, hips, both lower arms, both upper arms after retries; 3 off-model/redundant rejected), 5 OpenAI safety rejections (no charge) | about 1.98, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; estimated at the $0.22 per call measured in #28's arm round (no per-call usage logged for this run) |
| Technique trial B (#38), `run` only, blind-compared against technique A's round 2 | 18 gpt-image-2 at 1024x1024, quality high: 16 kept, 2 rejected (both frame-0 pose retries) | about 3.96, estimated | `assets/bakeoff/protagonist/glow-up/technique-trial.md`; estimated at the $0.22 per call measured in #28's arm round |
| Violet glow-up round 4, remaining painted animations and run-scarf correction | 70 gpt-image-2 calls: idle 16, jump/land 22, dash/run-scarf correction 8, fall/double_jump 24 | about 15.40, estimated | Animation notes under `assets/bakeoff/protagonist/glow-up/trial-b/`; excludes the separate 18-call run trial above |
| Violet glow-up round 6 (#4, Task 11b), fixed round 5's gap 1 ("the loops aren't built as loops"): `run`/`idle` placement-only torso-lock and head-rhythm fix ($0, data only), `idle`'s 8 scarf layers repainted, `fall` frame 4's held pose repainted | 17 gpt-image-2 at 1024x1024, quality high: 13 for idle's scarves (4 rejected on a spatial-alignment miss, 9 kept), 4 for fall frame 4's body+scarf (2 initial + 2 regenerated after a `finalize_anim.py` bug corrupted the first pair before any of it reached the critic) | about 3.74, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; estimated at the $0.22 per call measured in #28's arm round (no per-call usage logged for this run) |
| Violet glow-up round 7 (#4, Task 11b), fixed round 6's gap 3 ("too few drawings... and double_jump frames 3-4's scarf a flat gray ghost"): `dash` and `land` each 3-to-6 frames (3 painted in-betweens per animation, old frames kept/reindexed), `double_jump`'s scarf-02/03 repainted | 15 gpt-image-2 at 1024x1024, quality high: 2 for double_jump's scarf-02/03 (both kept), 7 for dash's 3 new frames (1 scarf rejected on a flat/low-shading miss, 6 kept), 6 for land's 3 new frames (all kept) | about 3.30, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; estimated at the $0.22 per call measured in #28's arm round (no per-call usage logged for this run) |
| Violet glow-up round 9, scarf consistency | 11 gpt-image-2 calls: 9 kept, 2 rejected | about 2.42, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; $0.22 per image call |
| Violet glow-up rounds 5, 8 and 10 | No generation; deterministic image transforms | 0 generation spend | Grading and idle-motion scripts in `assets/bakeoff/protagonist/glow-up/trial-b/` |

**Violet glow-up total, including its run-technique trial: about $31.46, estimated.**
This covers 148 attempts, of which worker reports count 143 as charged, at $0.22 each.
Earlier running totals omitted the run trial's $3.96. The reported zero charge for five
safety rejections was not checked against billing. This total excludes the previously
approved concept/parts, environment-lane generation, and agent/model-review usage.
