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
| Violet glow-up rounds 0-2 (#4, Task 11b), technique A stopped at round 2 (kept) | 3 gpt-image-2 at 1024x1024, quality high (head repaints: round 1's 2 calls (1 rejected), round 2's 1 call) | about 0.66, estimated | `assets/bakeoff/protagonist/glow-up/rounds.md`; estimated at the $0.22 per call measured in #28's arm round (no per-call usage logged for this run) |
