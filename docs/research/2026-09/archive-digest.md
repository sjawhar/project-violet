# Violet / Scarlet Design Archive Digest

Source: `/tmp/violet-drive` (Google Drive export, folders `violet/` and `scarlet/`, 25 files) + the live Unity repo at `/home/sami/Code/personal/project-violet`. All Google Docs are read from the `*.text.md` exports per instructions; the `*.md` twins and per-doc image sub-folders were opened only for embedded images. Every file was opened; nothing was skipped.

## 0. Population accounting — 25 files, all opened

**`violet/` (9 Drive files: 6 Docs + 3 images)**
1. `World Design - Level Map` (Doc) — text + 1 embedded flowchart image
2. `World Design - Inspiration` (Doc) — text + 4 embedded mood images
3. `World Design - First Level` (Doc) — script only, no images
4. `Character Design - Violet` (Doc) — text only (image references are broken external URLs, not embedded)
5. `Character Design - Violet and Slate` (Doc) — text + 1 embedded sketch image
6. `Character Design - Violet Inspiration` (Doc) — text + 1 embedded screenshot image
7. `Animations/Violet_Idle.gif`
8. `Animations/Violet_Run.gif`
9. `Animations/Violet_Jump.gif`

**`scarlet/` (16 Drive files: 13 Docs + 3 standalone files)**
10. `Capstone/Nomadly High Concept` (Doc)
11. `Capstone/Scarlet High Concept` (Doc)
12. `Scarlet Production Schedule` (Doc)
13. `Portal SWOT Analysis` (Doc)
14. `Scarlet Pitch` (Doc)
15. `Scarlet Game Design Document` (Doc) — text + 5 embedded images
16. `Scarlet Competitive Analysis` (Doc)
17. `Principles of Game Design Notes` (Doc) — text + 2 embedded diagram images
18. `Design Doc Templates/High Concept Template` (Doc, blank)
19. `Design Doc Templates/Story Bible Template` (Doc, blank)
20. `Scarlet Story Bible` (Doc)
21. `Violet High Concept` (Doc, filed inside `scarlet/`)
22. `Project Buffalo/Brainstorming` (Doc)
23. `Ideation.pdf` — 1-page scanned/handwritten mind map (created 2019‑02‑09)
24. `Scarlet-Prototype.zip` — compiled Unity WebGL build (10.8MB, 22 members) + screenshot
25. `dash-phase.mp4` — 10.9s, 1676×888, H.264/Vorbis screen capture (rendered via `gst-discoverer`/`openh264dec` since no `ffmpeg` was on PATH)

Every one of the 25 is summarized individually below.

---

## 1. Per-artifact summaries

### `violet/`

**1. World Design – Level Map.** One paragraph ("mostly linear game... traveling between levels via space ship... levels are not consistent with each other because each is a different world in the galaxy") plus a large hand-drawn flowchart with ~19 named scenes spanning a full space-opera arc (raid → capture → escape → homecoming → final boss). This is the **space-pirate** version's level map, wildly more elaborate than anything in the Scarlet docs. **Keep:** the flowchart's structural idea (hub-and-spoke optional levels converging back to a spine) and the recurring Academy/Library-as-antagonist motif.

**2. World Design – Inspiration.** Establishes the Academy as "an institution of both religion and science... a colorless world, literally," with 4 mood images: a magic/tech fantasy scene, St. Peter's Square (real-world referent for the Academy's scale/architecture), a bright coastal high-tech city (the "outside" world), and a bleak snow-mountain ruin (an abandoned Academy site). **Keep:** the Vatican-as-Academy analogy and the grayscale-vs-vibrant color contrast are exactly the mechanic's visual thesis, stated here before the mechanic itself existed.

**3. World Design – First Level.** A full script for a **space-pirate heist** opening: Violet breaches an enemy ship, evades laser turrets (this is literally where "dash" and "double-jump" are introduced as boarding-maneuver abilities), loots a cargo hold, finds a glowing Artifact, reaches for it, is blasted and captured by "soldiers in gleaming gray." **Keep:** the pattern of teaching abilities diegetically through an action sequence before the "real" premise (Academy/color) kicks in. This exact script is later preserved verbatim as "Appendix B: Discarded Level 1 Concept Script" in the Scarlet GDD, explicitly labeled "a previous version of the game called Violet, set in space" — direct proof of the Violet→Scarlet→Violet naming loop (see §3).

**4. Character Design – Violet.** "Violet is a space pirate... She's rough, she's ruthless, she has swords." Three sketch concepts: shaved-head-with-tattoo knife-fighter, butterfly-sword user with a holographic helmet, and a violin-themed jacket/rocket-boots look. No Academy, no meditation, no color mechanic — pure swashbuckling. **Keep:** nothing story-wise; the "rocket boots that let her float/dash" detail is a nice physical justification for the dash ability if a sci-fi reskin is ever wanted.

**5. Character Design – Violet and Slate.** Establishes the **paired-protagonist Academy** version: Slate is "the Academy's star... decked out in armor, holo-shield, beam-sword," big/slow/heroic; Violet is "a red shirt, nobody of significance... all light, flowing cloth... where Slate fights, Violet explores." Embedded sketch shows a wide-eyed, ponytailed girl in a robe next to a helmeted, sworded, shielded boy. **Keep:** the fighter/explorer foil dynamic and "Violet is defined by contrast to Slate" framing — cleaner and more visual than the Story Bible's later version of the same relationship.

**6. Character Design – Violet Inspiration.** A third, distinct framing: Violet as "a young student at the Academy... tasked to accompany... a party of Scholars," unsure of herself. Three inspiration images (ceremonial-robed warrior, cartoony purple-eyed girl, teal pixel-art fighter). **Keep:** the "novice searching for her calling" characterization is closer to the eventual Scarlet than either of the other two Violet docs.

**7–9. `Animations/` (Idle, Run, Jump GIFs).** Three-to-four-frame 64×64 pixel-art side-view sprite: brown skin, a long purple ponytail/mohawk, white robe, brown boots. **Keep — this is real, shippable art.** It is the exact sprite used in the live Unity repo's Idle/Run/Jump animations (pixel-identical), i.e. genuine continuity between the Drive archive and the codebase, not just a design document.

### `scarlet/`

**10. Capstone/Nomadly High Concept.** A completely unrelated pitch under the same "VoidFlow" team name: a satirical digital-nomad survival sim (à la Don't Starve) balancing budget/fitness/stress while traveling the world, scoped to "Europe only" for v1, solo dev. **Keep:** nothing directly — different genre, different theme, abandoned after this one document (no further Nomadly artifacts exist anywhere in the archive).

**11. Capstone/Scarlet High Concept.** The formal high-concept pitch: "Oneness is the truth of the Academy... Scarlet jumps, dashes, slams, swings, and slides." First explicit statement of the 4-ability/4-color mapping (dash-red-fire, stomp-yellow-earth, double-jump-green-air, TBD-blue-water) and the "world fills in with color" mechanic. Also the first explicit, heavily hedged scope-management paragraph (see §5). **Keep:** this is the cleanest single statement of the whole pitch — should be the seed document for the reboot's high concept.

**12. Scarlet Production Schedule.** Budget ($500 max), timeline (3 months / 32 estimated days with a 3x part-time buffer), team roles (Designer/Programmer/Artist, artist role vacant), and a 22-row task dependency table producing exactly 6 levels (Academy, Desert, Mines, Forest, Sunken Academy, The Library). **Keep:** the level list and dependency structure are a clean skeleton for a real production plan; the budget/timeline numbers are pure scope-hedges to be revisited (§5).

**13. Portal SWOT Analysis.** Unrelated coursework: a SWOT analysis of Valve's Portal franchise arguing for an open-world, persistent, community-content Portal 3. **Keep:** nothing content-wise; it documents that this whole archive originates from a formal game-design curriculum (high concept → SWOT → competitive analysis → GDD progression), which explains the paired blank templates (#18–19) and the process notes (#17).

**14. Scarlet Pitch.** A tight two-paragraph elevator pitch: "There is only Being... Now on the run from the one and only church, school, and government in the known land... Pursued by the Academy's enforcers." **Keep:** best prose hook in the archive, though it oversells a "manhunt" that the actual Story Bible plot (#20) never dramatizes (see §4).

**15. Scarlet Game Design Document.** The most complete document in the archive: philosophy (mindfulness/"stories we tell ourselves"/oneness), full world writeup (Academy, Desert, Fallen Library, other locations), the complete plot (see §2), character bios, the mechanics section (identical ability/color/element table as #11), the same budget/timeline/task table as #12, and two appendices: the discarded space-pirate Level-1 script (#3, verbatim) and 3 inspiration images (desert city, snowy-mountain resonance shot, low-poly forest lake). **Keep: this is the canonical spine document** — everything else is a fragment or earlier draft of what's fully assembled here.

**16. Scarlet Competitive Analysis.** Positions Scarlet against GRIS ($16.99, "no death, no stress," 3-hour runtime, praised art/story) and Celeste ($19.99, praised platforming+mental-health story), argues for PWYW distribution on itch.io/Humble/GOG to "gain the trust of the gaming public" as a first-time studio. **Keep:** the GRIS/Celeste positioning and target-audience description ("not dedicated platformer players... To the Moon, Never Alone, Life is Strange, Journey, Ori") is still an accurate, useful audience definition for the reboot.

**17. Principles of Game Design Notes.** Course notes on the Imagine→Define→Describe→Transmit→Implement design process, documentation types (high concept/treatment/GDD), and ideation techniques (Idea Tree, Idea Cards, 4-phase brainstorming) with 2 diagram images (Design/Play/Experience framework; Design Process flowchart with QA/playtesting loop). **Keep:** context for how/why the archive is structured the way it is; not game content itself. This is literally the technique used to produce artifact #23 (Ideation.pdf).

**18–19. Design Doc Templates (High Concept, Story Bible).** Blank fill-in-the-blank templates from the same course. No original content. **Keep:** none — these are scaffolding, not canon, though they're a fine reference for how to structure future docs.

**20. Scarlet Story Bible.** The dedicated narrative document: settings (Academy, Desert, Fallen Library, + a one-line list of Mines/Forest/Sunken temple), the full plot beat-by-beat (see §2), character write-ups for Scarlet, Slate, and Kuluun, and an explicitly-flagged unbuilt idea: "Memories of Others... Haven't had a chance to work this in yet... In the Library observatory, the memories drown out her identity. That's what leads to her awakening." **Keep:** the plot and the Memories-of-Others idea (unbuilt but promising — see §6).

**21. Violet High Concept.** A near-twin of #11 but as a **solo fugitive** rather than paired with Slate, with a more overt "Pursued by the Academy's enforcers" chase framing and a "team is still being formed" section implying this is *earlier* than the Scarlet docs (roles not yet filled at all, vs. Scarlet's "Designer and Programmer already filled"). Same 4-color ability list, same "Combat is probably off the table" scope hedges (word-for-word identical paragraph to #11's, only pronoun-swapped). **Keep:** confirms Violet (Academy-fugitive) and Scarlet are the *same* concept mid-rename, not two independent pitches.

**22. Project Buffalo/Brainstorming.** Totally unrelated satirical brainstorm: a moon-based research institute, "something cataclysmic happens on Earth," Metroidvania-style ability unlocks (start "completely inept," build an exoskeleton), silly weapons ("Doritos and mountain dew to distract the nerds"). **Keep:** nothing content-wise — but the name "Buffalo" is *not* coincidental: git history shows the actual Unity repo (this reboot's ancestor) was internally named "Buffalo" from its first commit until the very last commit, which renamed it to "Violet." Same codename, two unrelated ideas — a naming collision worth knowing about, not a hidden design link.

**23. Ideation.pdf.** A single hand-drawn "idea tree" mind map (Qt-app scan, dated 2019‑02‑09) radiating from two trunks: "Run, Nomad!" (feeding the Nomadly pitch: budget/fitness/instagram/digital-nomad branches) and "Platformer" (feeding Surfing/Food/**Meditation→Awareness→Calm**/Music branches). **Keep:** this is the literal origin point where the "meditation/calm/awareness" seed that became Scarlet's whole thematic premise first appears, sitting right next to the abandoned Nomadly branch — direct evidence of the brainstorming session that forked into both games.

**24. Scarlet-Prototype.zip.** A compiled Unity WebGL build (`companyName: VoidFlow`, `productName: Scarlet`) with an `index.html` that reads "Super Sparty Bros." (a Michigan State University class template — confirms MSU game-design-course origin) and states: "Game Description: Collect coins, avoid enemies, and go for the rose! Game Modifications: Level 2! / Dash: new ability available in level 2 / Phasing: lets player pass through certain objects / Added post-processing volume and layers for phasing VFX." No source files are included, only the compiled `webgl/Build/*.unityweb` payload, loader JS, and a `screenshot.png` showing a generic platformer (ninja-sword enemy sprites, coin bars, a tall red spike-pillar labeled as passable via phasing, a floating "rose" goal). **This is the very first working proof of the resonance/phasing concept, pre-dating the full narrative design.** **Keep:** the "dash unlocks phasing through red obstacles" pairing is the literal ability→visibility rule later formalized in the design docs and the real Unity `Resonator.cs`.

**25. dash-phase.mp4.** A 10.9s Unity Editor Play-mode screen capture (visible chrome: "Display 1 / Free Aspect / Scale / Maximize On Play / Mute Audio / Stats / Gizmos," "Score: 0 Highscore: 14," "Level 1"). Shows a small green sprite character standing near a red obelisk on a repeating platform-and-ninja-enemy tileset; partway through, the **entire screen tints red/magenta** (the world-resonance filter), the platform recolors, and the coin pickups morph from solid yellow bars into red-outlined rings, before fading back to the normal blue-tinted view. **Keep:** direct video proof that the "resonate → screen recolors → object visibility/collectible state changes" rule was working and readable, at least in a placeholder scene, in 2019.

---

## 2. Consolidated canon (built primarily from the Scarlet GDD/Story Bible, the fullest and most internally consistent version)

### Characters
- **Scarlet / Violet** (protagonist, renamed across drafts — see §3): raised in the Academy, "dark-skinned, bald, and with barely a visual indication of gender" per written canon (contradicted by all concept art and the actual sprite — see §4). Starts content/passive; an accidental brush with the Artifact grants her the resonance power and forces an emotional awakening (fear, joy, anger, excitement) she's never had inside the Academy's meditative flatness.
- **Slate**: an Academy agent sent to retrieve Scarlet/the Artifact. Rigid, armored, "sees danger in everything foreign," refuses to remove his suit even when it costs him (can't swim, too heavy to climb trees). Becomes a reluctant, then genuine, ally over the course of the journey. (Note: his introductory characterization differs meaningfully between docs — see §4.)
- **Kuluun**: an aging Traveler/desert farmer/cactus merchant who takes Scarlet in after her collapse; gruff but kind; the first person outside the Academy she bonds with.
- **The Artifact**: a small, glowing, silent sphere; source of all resonance power; literally *is* the thing Scarlet disappears into / merges with at the story's end.
- Space-pirate-era-only characters (not carried into the Academy version): **The Captain**, **The Pilot**, **Scratch** (a fellow pirate who abandons Violet when she's captured).

### World / locations
- **The Academy**: "the one and only church, school, and government in the known land"; androgynous, bald, uniform population; doctrine of Oneness/Being; secretly built around the Artifact, whose energy sustains it.
- **Desert**: home of the nomadic **Travelers**, who ring the Academy with power stations feeding off its excess energy; a small merchant town; element = **fire**; first ability learned here = **Dash (red)**.
- **Mines**: element = **earth**; ability learned = **Stomp (yellow)** — per docs only; never implemented in the prototype (see §4/§7).
- **Forest**: element = **wind/air**; ability learned = **Double-jump (green)**.
- **Sunken temple / Sunken Academy**: a smaller, flooded ruin resembling the Academy; element = **water**; ability learned = the undecided **4th ability (blue)**.
- **The Fallen Library**: the true point of origin — a pre-Academy city of science where the Artifact was originally built; abandoned once the Artifact made further discovery "pointless"; Scarlet's final destination and the site of her disappearance/apotheosis.
- Space-pirate-era-only locations (from the Level Map flowchart, not carried into Scarlet): a pirate raiding ship, an asteroid-belt hideout, an island-town fence, lava caves, a floating sky-city, a "water planet," a mining colony, a home planet, and "The Old Academy" (site of the final boss, "The Dark Librarian").

### Plot beats, in order (Scarlet/Academy version — the fullest, most complete draft)
1. On her way to morning meditation, the protagonist finds a hidden door and an Artifact chamber; Academy leaders approach; she backs into the Artifact and is blasted with color.
2. She flees through what is now a passable (red) wall, emerges near a desert power station, and collapses.
3. Travelers take her in; she recovers among them, decides to stay, and helps out — discovering she can **dash**. They give her a scarf with the same color-property as the Academy wall; she names herself **Scarlet** after its color, and begins to perceive red (everything else still gray).
4. A metal-suited Academy agent, **Slate**, corners her in the mines demanding the Artifact back; in her frustration she **stomps**, causing a cave-in that traps them both; she uses her dash to save him from a collapsing ledge, forcing an uneasy alliance.
5. They emerge into a forest; she climbs a tree for a vantage (Slate, in his suit, cannot follow), spots a sunken structure resembling the Academy, and gains the color **green** (the text names the ability but does not explicitly restate "double-jump" at this exact beat — it's established earlier in the mechanics section).
6. At the sunken temple, she explores alone (Slate can't swim) and finds records of "the Library"; she gains the color **blue**.
7. They travel to the ruined **Library**; inside, they learn the true history of the Artifact and the philosophy of Oneness. In the observatory, Scarlet pulls a lever, the ceiling opens to starlight, she speaks the Academy's own creed back at reality ("There is only Being...") and **disappears** as the Library collapses around Slate.
8. Slate returns alone to the Academy, hailed as a hero because the Artifact has reappeared in its chamber. Alone with it, he asks: **"Scarlet?"** — implying she has become, or merged with, the Artifact itself. (End is deliberately ambiguous — see §4.)

### Mechanics and the color↔ability↔element mapping
Per every design document (consistent across Scarlet HC, Violet HC, Story Bible, and GDD):

| Color | Ability | Element | Location taught |
|---|---|---|---|
| Red | Dash | Fire | Desert |
| Yellow | Stomp | Earth | Mines |
| Green | Double-jump | Air/wind | Forest |
| Blue | **Undecided** — "swinging or teleporting... further prototyping needed" | Water | Sunken temple |

Core rule, stated identically everywhere: while resonating a color, world elements of that color are revealed/hidden — "a red platform is invisible if the world is red. That means a red wall can be walked through (yay!) but a red platform can't be landed on (no!)." The world starts grayscale and colors permanently "fill in" as abilities are gained (a lasting global-state change, distinct from the temporary per-use color-vision window).

**What the actual 2019 prototype implemented instead** (see §7 for full detail): Dash→Red and Double-jump→Green match the docs exactly, but the docs' Yellow/Stomp/Earth ability was never coded at all (despite full engine plumbing existing for it), and Blue was bound to a **Ground Slam** — not the "swing or teleport" option the docs list as under consideration. This is a live, unresolved fork between written canon and built code (§4).

### Level list
**Scarlet/Academy version (canonical, matches the Production Schedule task table exactly):** 6 levels — Academy (intro) → Desert (fire/dash) → Mines (earth/stomp) → Forest (air/double-jump) → Sunken Academy/temple (water/4th ability) → The (Fallen) Library (finale/boss-equivalent).

**Violet/space-pirate version (from the `World Design - Level Map` flowchart — an entirely separate, much larger level graph, not reconcilable with the 6-level list above):** a linear opening chain — *Raiding the Academy Ship → Captured at the Academy → Back at the Hideout (asteroid belt) → Finding the Fence (island town) → Into the Fire (lava caves)* — feeding into a hub, *On the Ship ⇄ Chats with a Warden*, which branches to three optional/parallel levels — *City in the Sky (floating city)*, *Darkest Depths (water planet)*, *In the Mines (mining colony)* — that reconverge at *From Nothing, Power (space station)*, then continues linearly: *Recaptured (The Academy) → Escape! (The Academy) → Nightmares (home planet) → Home World Bound (home planet) → Reunion of Strangers (home planet) → The Final Clue (your ship) → Private Archives (The Old Academy) → The Dark Librarian (The Old Academy, boss) → Unveiling the Mask (The Old Academy)*.

---

## 3. Competing versions and how they differ

| Version | Genre/tone | Protagonist framing | Core mechanic present? | Status |
|---|---|---|---|---|
| **Violet, space pirate** (earliest — `Character Design - Violet`, `World Design - First Level`, `World Design - Level Map`) | Swashbuckling sci-fi heist | Solo antihero pirate, no Academy backstory at time of writing | No — ability learning is diegetic ship-boarding (dash/double-jump as rocket-boot maneuvers), no color-world-visibility rule yet | Superseded; its Level-1 script was explicitly preserved as a "discarded" appendix in the later Scarlet GDD |
| **Violet & Slate, Academy duo** (`Character Design - Violet and Slate`) | Fantasy/sci-fi fusion, buddy adventure | Violet = "red shirt" explorer foil to Slate's armored prodigy-hero | Not described — pure character-design doc | Early; folded into the Academy-fugitive premise but the "fighter vs. explorer" foil framing of Slate/Violet here is cleaner than the later Story Bible's "captor becomes ally" framing |
| **Violet, Academy novice** (`Character Design - Violet Inspiration`) | Coming-of-age fantasy | Unsure student sent on a Scholars' quest | Not described | Early; the "novice searching for her calling" characterization is the one that actually survives into Scarlet |
| **Scarlet, MSU capstone prototype** (`Scarlet-Prototype.zip`, "Super Sparty Bros" template, studio name "VoidFlow") | Generic arcade platformer | Not characterized at all — default template hero sprite | **Yes, partially** — this is the very first working build of "dash unlocks phasing through red objects," with zero story | First runnable proof-of-concept; purely mechanical |
| **Scarlet, Academy fugitive, with Slate** (Story Bible, GDD — the fullest version) | Contemplative parable / puzzle-platformer | Solo protagonist, but Slate is a major secondary character/travel companion for most of the journey | Yes, fully specified (4-color/4-element/4-location table) | Most complete written design; this is the de facto canon baseline |
| **Violet, Academy fugitive, solo** (`Violet High Concept`, filed in `scarlet/`) | Same as above, more chase-thriller framed ("Pursued by the Academy's enforcers") | Same premise, no Slate mentioned; team "still being formed" (earlier draft state than the Scarlet docs) | Same 4-color table, word-for-word | A rename-in-progress snapshot of the Scarlet doc — same design, different working title, likely the transition point back toward "Violet" |
| **Violet, 2019 Unity prototype** (this repo, internally named "Buffalo" until its last commit) | N/A (mechanics-only sandbox) | Purple-ponytailed pixel sprite (matches the Drive GIFs), no story content in-scene | **Yes, 3 of 4 abilities working** (Dash=Red, Double-jump=Green, Ground Slam=Blue); Yellow/Stomp never wired up | Most technically advanced artifact in the archive; see §7 |
| **Nomadly / VoidFlow** (`Capstone/Nomadly High Concept`) | Satirical survival sim | N/A — unrelated game entirely | No | A sibling capstone pitch under the same team name, abandoned after one document; irrelevant to Violet/Scarlet content but explains the "VoidFlow" studio name baked into the Scarlet prototype build |
| **Project Buffalo** (`Project Buffalo/Brainstorming`) | Sci-fi comedy | N/A — unrelated game (moon research station, Metroidvania) | No | A separate abandoned brainstorm; its name was independently reused as the Unity repo's working codename before the "Violet" rename — a naming coincidence, not a design link |

**Chronology, as evidenced in the documents themselves:** the Scarlet GDD explicitly labels the space-pirate Level-1 script as "a previous version of the game called Violet, set in space" — i.e., **Violet (space pirate) came first, Scarlet (Academy fugitive) is the pivot/refinement that added the resonance mechanic and the mindfulness theme, and the current reboot's choice to call it "Violet" again is a return to the original name while keeping Scarlet's Academy-fugitive premise and mechanic.** The Academy/Library-as-antagonist and "artifact grants light-based powers" ideas are the throughline that survived every genre pivot.

---

## 4. Inconsistencies and unresolved design questions

1. **The blue ability was never chosen, in either docs or code, and the code's choice doesn't match either doc option.** Every design doc lists blue as "swinging or teleporting... further prototyping needed." The actual Unity code binds Blue to a brand-new third option, **Ground Slam**, which is thematically closer to earth than water and isn't one of the two options the docs floated. This needs a decision, not more prototyping-in-place.
2. **Yellow/Stomp/Earth is fully plumbed in code (dedicated Unity physics layer `ResonateYellow`, a `YellowProfile` post-processing asset, full crossfade/collision logic in `Resonator.cs`) but zero gameplay ever calls `Resonator.Resonate(ResonateColor.Yellow)`.** It's an inert 4th color — infrastructure for an ability that was never designed at the code level, even though the docs describe it in as much detail as the other three.
3. **Protagonist appearance directly contradicts written canon.** The Story Bible/GDD state Academics (including Scarlet) are "dark-skinned, bald, and with barely a visual indication of gender." Every piece of concept art (`Character Design - Violet and Slate`, `Character Design - Violet Inspiration`) and the one real, shipped sprite (Drive GIFs = repo's Idle/Run/Jump animation) show a character with a full head of hair (purple ponytail/mohawk). This was never reconciled.
4. **Renaming "Scarlet" back to "Violet" breaks a stated piece of internal logic.** The Story Bible has her name herself after the color of the desert scarf she's given ("She takes the color of the scarf as her name: Scarlet") — and "Scarlet" plausibly reads as a shade of red, her first ability color. "Violet" is not one of the four resonance colors (red/yellow/green/blue) at all, so the reboot needs either a new naming justification or an acceptance that the title is now decorative rather than diegetic.
5. **Slate's introduction is characterized two different ways.** `Character Design - Violet and Slate` frames him as "the Academy's star, their prodigy," sent on a heroic quest of his own from the start. The Story Bible/GDD instead have him arrive later, specifically as an agent sent *to retrieve Scarlet and the Artifact* — a pursuer, not a co-protagonist from page one. Both can't be true of the same character simultaneously; pick one.
6. **The "manhunt" framing oversells the actual plot.** The Pitch and the Violet High Concept both promise Scarlet is "on the run," "pursued by the Academy's enforcers" (plural, active, ongoing threat). The Story Bible's actual plot has exactly one pursuer (Slate) who, after the mine collapse, becomes an ally — there is no depicted manhunt for the rest of the story. Either the plot needs an actual sustained threat to earn the pitch's promise, or the pitch copy needs to stop promising a chase-thriller it doesn't deliver.
7. **The ending is deliberately ambiguous and was never resolved as apotheosis vs. tragedy.** Scarlet dissolves into the Artifact/Being at the climax; Slate later finds the Artifact restored and asks "Scarlet?" — is she gone, transformed, or literally *is* the Artifact now (and if so, is that a triumphant merging-with-oneness or a quiet horror-story ending)? The docs never state an intended reading.
8. **"Memories of Others" is a load-bearing narrative-delivery mechanic that was never designed**, per the Story Bible's own appendix note: "Haven't had a chance to work this in yet... In the Library observatory, the memories drown out her identity. That's what leads to her awakening." This is how the game was supposed to deliver world backstory to the player, and it's a placeholder.
9. **Two incompatible inciting incidents survive in the archive**, both involving an Artifact and both ending in the protagonist being caught/blasted: the Academy version (an accidental bump during a moment of curiosity, a devout novice's mistake) and the space-pirate version (a professional thief overreaching on a heist). They cannot both be canon; the space-pirate one is explicitly marked "discarded" in the GDD, but its DNA (protagonist reaches for a glowing orb, is blasted, is captured) visibly carried over into the Academy version's inciting incident.
10. **Whether the reboot keeps a Slate-equivalent companion at all is unresolved** — the standalone `Violet High Concept` (arguably the most recent pre-Unity draft) doesn't mention a second named character, while the fuller Story Bible/GDD treat Slate as essential.
11. **PWYW (pay-what-you-want) as the release strategy was chosen specifically to compensate for being a first-time, unproven studio** — worth an explicit yes/no now that budget is not a constraint and the studio is not first-time in the same way.

---

## 5. Every constraint traceable to novice/scope-hedging (explicit candidates to lift)

Quoted or closely paraphrased from the documents, each one an artifact of "amateur, first game, side project" framing rather than a creative choice:

- **"Design a game that can be built and released in three months."** (Production Schedule / GDD) — and the actual 2019 Unity prototype's git history runs exactly Feb 26–May 26, 2019, i.e. the team hit this deadline to the day and then stopped.
- **"We have a maximum $500 budget for art assets or Unity plugins."**
- **"All team members are working on the game on the side"** — with an explicit 3× time multiplier applied to every estimate specifically because of part-time availability.
- **Team of exactly three, roles barely differentiated** ("Designer... Programmer... Artist... all personnel must be cross-functional... no specific experience is required beyond the basics of the roles, i.e. Artist can make pretty pictures") — and the Artist seat is stated as still vacant at time of writing.
- **"No more than four core mechanics."**
- **Exactly six levels, no more** ("one introductory level, one level for each mechanic, and one final level").
- **"Combat is probably off the table, and possibly enemies or damage as well."** (word-for-word in both Scarlet and Violet high concepts) — the hedge word "probably" signals this was never a confident thematic choice.
- **"Open world design is probably beyond our abilities at the moment, so the levels will be very linear."** — an explicit admission that linearity was a skill-ceiling retreat, not a deliberate design choice in service of the puzzle/parable focus (worth separating: linearity may still be the *right* call for this game, but it should be re-derived from the theme, not inherited from this sentence).
- **"Inventory is unlikely."**
- **"We will not be developing mechanics more complex than acrobatics-based platforming."**
- **Levels explicitly static to cut scope**: "Each level is static: no time passes, weather doesn't change."
- **No exploration, by design-for-budget rather than design-for-theme**: "little to no exploration... presented with snapshots of the world... progress through linearly."
- **PWYW distribution chosen "to gain the trust of the gaming public"** as a hedge against being an unknown first-time studio, not because it's judged the best commercial model for this specific game.
- **Self-labeling as amateur throughout**: "the first game of an amateur studio," "As my first game," "this is our first game, so no specific experience is required."
- **The inherited 2D Game Kit combat stack (melee/ranged attack, bullet pool, inventory-gated unlocks, Enemy/EnemyWeapon/BossWeakPoint/Bullet physics layers) was never stripped out of the player character/input classes** — a byproduct of building fast on a stock kit under time pressure rather than a considered decision to keep or cut combat.

---

## 6. Strongest ideas to carry forward, and the weakest parts to leave behind

**Strongest, worth protecting in the reboot:**
- The resonance mechanic itself — ability-use as a temporary, readable world-visibility filter (pass through same-color walls, can't land on same-color platforms) — is genuinely novel, thematically tight (color = expanding awareness), and **already proven to work** in both the MSU class prototype and the fuller Unity build.
- The grayscale-fills-in-with-color-as-you-grow structure is an elegant, wordless way to show character growth, and it is rare among puzzle-platformers.
- The oneness/mindfulness theme and "the stories we tell ourselves" framing is a genuinely underserved angle (their own competitive analysis found no direct mindfulness-themed competitor as of 2019), distinct from GRIS's grief and Celeste's anxiety/depression focus.
- The Academy/Library duality (institutional control over knowledge vs. the older, freer pursuit of truth that preceded it) is the one idea that survived every single genre pivot across 2019's brainstorming, including the discarded space-pirate version's own boss ("The Dark Librarian") — this is the most load-bearing piece of world lore in the whole archive.
- A tight 1:1 mapping of ability↔element↔location↔color is extremely easy to brief to art/level/narrative agents individually — a strong scaffold for a swarm-based production pipeline.
- Slate's arc (rigid antagonist-emissary → earned ally) is an efficient two-hander that needs only one major secondary character to carry the whole emotional throughline.
- The unbuilt "Memories of Others" idea — environmental storytelling through inherited/found memories that culminates in an identity-dissolving climax — is a strong, unbuilt narrative-delivery mechanic worth actually designing this time.

**Weakest, safe to cut or must be re-decided:**
- The undecided blue ability (3+ years unresolved) and the entirely unbuilt yellow/stomp ability — these are not "almost done," they are open design debt.
- The inherited Game Kit combat/inventory/enemy framework sitting dormant in the player classes — dead weight that actively contradicts the "no combat" premise and should be excised at the codebase level for the reboot, not just left uninstantiated in scenes.
- The bald/androgynous written-canon description of the protagonist, which no art asset actually honors — pick one and update the other.
- The tonal whiplash between the space-pirate and Academy-fugitive premises sharing a name and some beats without ever being reconciled — a sign of premise-shopping, not a settled world; the reboot should consciously choose (or explicitly graft) rather than silently inherit both.
- The "Academy's enforcers" pursuit that the pitch promises but the plot never delivers — either write the chase or stop promising it.
- The pervasive apologetic scope language ("probably," "unlikely," "beyond our abilities") — worth an explicit pass to distinguish which limits (e.g., linearity, no combat) are genuinely good creative choices for a mindfulness-themed parable vs. which were purely capitulations to a $500/3-month/amateur-team box that no longer applies.
- The mismatched Dash animation art (four frames of an unrelated, much higher-fidelity vector sci-fi character with a cybernetic arm, dropped into an otherwise consistent low-res pixel sprite set) — visible seam, not real IP, safe to discard entirely.

---

## 7. What the prototype(s) actually implemented

Two separate, unconnected prototypes exist in the archive/repo; neither should be conflated with the other.

### A. `Scarlet-Prototype.zip` — MSU capstone-course build (earliest, ~Feb 2019)
A Unity WebGL build of a generic template ("Super Sparty Bros," a Michigan State University class asset), rebranded `companyName: VoidFlow`, `productName: Scarlet`. Its own changelog states the entire scope of "Level 2": **"Dash: new ability available in level 2 / Phasing: lets player pass through certain objects / Added post-processing volume and layers for phasing VFX."** This is the literal first working proof that "an ability triggers a world-visibility/collision change with a post-processing color shift" is buildable in Unity. No story, no custom art (stock ninja-enemy sprites, a generic hero sprite, coin/gem pickups, a scoreboard/highscore HUD), no color-cycling between four states — just one dash-triggered "phase red" state proven out.

### B. The Unity 2019 repo (this checkout) — the real narrative-mechanic prototype
Built directly on Unity's official **2D Game Kit** sample (Ellen character controller, Cinemachine, Post-Processing v2) under Unity **2019.1.3f1**, subclassed into a dedicated `Violet` C# namespace (commit discipline: "Moved all custom code to separate packages and namespace," "Last game kit modification reverted" — deliberately kept the vendored kit clean of edits). Git history runs **Feb 26 – May 26, 2019**, exactly the docs' own "three months," internally named **"Buffalo"** until the literal final commit renamed it to **"Violet."**

**Abilities implemented and wired to input** (`PlayerCharacter.cs`, `PlayerInput.cs`, `InputComponent.cs`):
- **Dash → Red** (`LeftShift`/Xbox Right Bumper), `dashSpeed = 30`, works grounded and airborne (`AirborneDashSMB`).
- **Double-jump → Green**, reusable at any height once airborne ("Can double jump at any time" commit), no separate keybind — reuses Jump.
- **Ground Slam → Blue**, triggered by a custom **double-tap** input (`DoubleTapButton`: tap-release-tap within a 0.25s window, on `S`/Xbox Left Bumper), `groundSlamSpeed = 30`, forces the character straight down.
- **Yellow**: fully wired at the infrastructure level (its own Unity physics layer `ResonateYellow`, its own `YellowProfile` post-processing asset, full crossfade/collision logic in `Resonator.cs`) but **no ability anywhere in the codebase ever triggers it** — a fourth color built and never used.

**The `Resonator` mechanic itself** (singleton `MonoBehaviour`): calling `Resonate(color)` crossfades a screen-space post-processing Color Grading volume for that color in over 0.2s, holds it for `resonateTime` (1.5s in the shipped prefab), then fades it back out while the previous color's volume fades away; simultaneously it (a) calls `Physics2D.IgnoreLayerCollision` between the player and that color's dedicated physics layer so same-color obstacles become passable, and (b) rewrites the character controller's ground-detection `LayerMask` to XOR out that color's layer so same-color platforms can no longer register as ground. This is a precise, generalized, working implementation of the docs' "red wall walkable / red platform not landable" rule — confirmed visually in `dash-phase.mp4`, where the whole screen tints red/pink (matching the tuned `RedProfile` color-filter value of roughly `{1, 0.47, 0.46}` with post-exposure pushed to 1.5) and a platform + coin row visibly recolor and change collectible state mid-clip.

**Art status:** Idle/Run/Jump reuse the real, custom 64×64 pixel sprite from the Drive `Animations/` GIFs (purple ponytail, brown skin, white robe) — genuine continuity between design archive and code. The Dash animation, by contrast, uses 4 frames of an entirely unrelated, much higher-fidelity vector illustration (a red-haired sci-fi character with a cybernetic arm) — an obvious placeholder swap, not canon art. The dash trail VFX (`DashSwish.prefab`) is an unmodified, flipped variant of the Game Kit's stock particle "swish" effect — no bespoke VFX was authored for any ability.

**Levels:** exactly two populated scenes, `Prototype.unity` (~640KB, includes two narrative-flavored trigger objects, `SlamDialogTrigger` and `DashDoorDialogTrigger`, implying at least a planned dialogue beat around each ability) and `Beta1.unity` (a trimmed variant without those triggers). Both reuse Unity's stock "floating sky islands" sample art wholesale (parallax clouds, background rocks, a tilemap ground, a water mesh) — this matches **none** of the described settings (no Academy, no desert, no Library, no space-pirate ship). It is a pure mechanics sandbox in borrowed art, never a real level for either narrative version. No enemies are placed in either scene (confirmed by grep for enemy-named objects), even though the inherited Game Kit combat stack (melee attack, ranged/gun attack with a bullet pool and fire rate, an inventory system gating those unlocks, and `Enemy`/`EnemyWeapon`/`BossWeakPoint`/`Bullet` physics layers) still ships live on the player character and input classes with default keybindings (`O` = ranged attack, `K` = melee attack) — inherited-but-unused, not deliberately removed.

**Bottom line:** development stopped, per the final commit ("Finished playtest level" → same-day rename Buffalo→Violet), right at the self-imposed three-month deadline, with one working sandbox level, three of four abilities functioning and visually confirmed, one ability (yellow/stomp) fully plumbed but never triggered, zero narrative content in-scene, and no further commits since May 2019.
