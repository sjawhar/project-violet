# AI-assisted story writing without slop (research, October 2026)

Sami asked for this on 2026-10-04, before reworking Violet's story, which he judged trite and rushed: find the current best practice for using AI in brainstorming and writing fiction without producing AI slop, starting from Joel Borgen's *The Receipt Horizon*. The process it found is now the `story-development` skill; [Running Violet's story sessions](#running-violets-story-sessions) lists what Violet's sessions start from.

Three research agents read the sources below on 2026-10-04. Quotes from Borgen were checked against the episode transcript; podcast speech is lightly cleaned of repeated words. Repository star counts and licenses were checked against the GitHub API the same day.

## What works, in one paragraph

Every source that reports decent results splits the work the same way: the human writes the premise, theme, characters and beats before the model is involved, and keeps every decision; the model asks questions, drafts from tight briefs, and critiques as a list the human rules on point by point; deterministic checks and a separate critic catch what the drafting model can't see in its own work; and the last pass is a human cutting, mostly over-explanation. The two documented risks are structural, not lexical: AI ideas pull different writers' stories toward each other (measured), and writers' own ratings of their work don't register any change (measured). Violet's game-story precedents (GRIS, Journey, Celeste) add one rule on top: fix the feeling and theme first, and make the mechanic carry it.

## Joel Borgen, *The Receipt Horizon*

Borgen is a pathologist and violinist; this is his first novel, released July 2026, written over more than a year with ChatGPT Pro as the main drafting model and Claude as the second. His only process interview is on Nathan Labenz's AI:AM, 2026-10-01 ([transcript](https://www.cognitiverevolution.ai/ai-am-was-trump-xi-anything-what-counts-as-utopia-aws-gpus-cost-3x-ai-diagnoses-rare-diseases/), about 47:30 to 55:20). He has published no prompts, code or skills.

- He fixed the architecture before touching a model: "I started the project knowing more or less what I wanted to have made. I sketched it out myself, especially the first half or so of the book was pretty well set before engaging the models." Then "a large scale architecture for the story and a lot of beats," drafted "chapter by chapter."
- Model drafts are raw material: "even if you tell it exactly what you want and you have a plan for a chapter, you often get something that's unreadable unless you know how to scaffold it and then edit it yourself."
- Editing is mostly subtraction: "I edited it down about 14% or so mostly manually and through AI helping me deciding what to cut... take away some of the stuff that AI does particularly badly, the text, the overexplanation."
- His review tool: give a model the whole novel, get back "a list of, like, these are things you should consider... and then you can decide for yourself kind of point by point."
- No character speaks for the author: "I didn't want anything in the book or any character to be a mouthpiece for me," and he steelmans the opposing views.
- He still paid human professionals for copyediting, art and layout.

Reception is mixed, and that is useful calibration. Labenz, the producer: "The text has a few AI ticks, but the book is legitimately good." On [Astral Codex Ten](https://www.astralcodexten.com/p/open-thread-443) (2026-07-20), one reader's first impression was "this reads like it was written by AI," but he paused on one image: "I'm not sure how to feel about it, which is arguably the marker of good writing." Borgen replied that he was "90%+" sure that line was his own. Another reader stalled on "the prose's rhythm" and objected to a character choice on the first page.

## Practices that recur across sources

1. **Human first and last; model in the middle.** Peter Yang's rule (creatoreconomy.so, 2026-07-22): write the first 25% without AI, use AI in the middle 50%, do the last 25% by hand, line by line. Stephen Marche, who wrote a novella mostly by prompting: "Generative models are fundamentally cliche machines... The key is to control the machine, rather than having the machine controlling you" ([Guardian, 2026-04-02](https://www.theguardian.com/commentisfree/2026/apr/02/artificial-intelligence-writers-powerful-language)).
2. **The model interviews; it doesn't propose.** addyosmani/clarity's interview mode opens with "Talk to me for three to five minutes, or stream-type one take. Do not organize it first," never writes "a memory, preference, or experience for the author," and ends each draft with a provenance note: what came from the author, what the model added, open questions.
3. **Challenge the author's confident choices.** The Spec Kit game-narrative preset's brainstorm loop puts each settled element to the author with "what is the strongest argument this is wrong?" and writes nothing until the session ends.
4. **Triage an existing draft row by row.** zenstory-ai/novel-to-game tags every source fact "immutable, adaptable, open, or conflicted," cites where it came from, and requires named vetoes before discarding a direction.
5. **Staged outlining, each stage reviewed by the human before the next.** Premise, then synopsis, then chapter beats, then scene briefs (Sudowrite's documented workflow; story-skills; Claude-Book).
6. **A story bible that persists across sessions, separate from scratch work,** plus a decisions log, so later sessions don't re-propose what was rejected (story-skills, author-toolkit, Claude-Book).
7. **Voice as samples, not adjectives.** Example lines per character and situation (Novelcrafter voice sheets: "We're wanting to get an essence of the character, not bits of dialogue for the AI to insert verbatim").
8. **A separate critic with a capped number of rounds,** returning a list for the author, compared head to head rather than scored 1 to 10 ("Standard 1-10 scoring collapses to a 2-point band," NousResearch/autonovel). Simulated readers are labeled simulated.
9. **Slop is structural more than lexical.** autonovel's list of failures that "survive prompt engineering": the over-explain (their number one problem), reflexive groups of three, "not X but Y" antithesis, uniform paragraph length, beats landing exactly where the outline put them, every chapter ending the same way. haowjy/creative-writing-skills adds resolving tension too early and collapsing deliberate ambiguity, both traced to helpfulness training. Banned-word lists work on density, not single words: "the problem is density and reflex, not any single occurrence," and "the fix is never just deleting tics; it's reinstating the concrete detail the slop displaced" (the de-slopify skill in [Dicklesworthstone/agent_flywheel_clawdbot_skills_and_integrations](https://github.com/Dicklesworthstone/agent_flywheel_clawdbot_skills_and_integrations/blob/main/skills/de-slopify/SKILL.md)).

## Evidence on quality

- **Homogenization is measured.** In Doshi and Hauser, *Science Advances*, 2024 ([full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/)), AI story ideas made individual stories rated more novel and better written, but stories with AI help were measurably more similar to each other (an increase equal to 8.9 to 10.7% of the spread among human-only stories) and closer to the AI's idea. Writers' ratings of their own stories' novelty and usefulness showed no difference between the groups. The study used one-shot, single-voice idea prompts.
- **The fix is diversity on purpose.** Wan and Kalman ([arXiv:2504.13868](https://arxiv.org/abs/2504.13868), 2025) gave writers plots from ten deliberately different AI personas and story diversity held at or above the human-only baseline.
- **Experienced readers can tell.** Russell, Karpinska and Iyyer ([arXiv:2501.15654](https://arxiv.org/abs/2501.15654), 2025) found that "annotators who frequently use LLMs for writing tasks excel at detecting AI-generated text"; five of them together misclassified 1 of 300 articles. Readers did it as a crowd when Hachette pulled *Shy Girl* in March 2026 ([Guardian](https://www.theguardian.com/books/2026/mar/20/hachette-horror-novel-shy-girl-suspected-ai-use-mia-ballard)). Disclosure is the low-risk path; Violet already plans Steam's AI disclosure.

## Game story specifically

- **Feeling and theme first, mechanic as the carrier.** GRIS is a wordless platformer about grief in which color returns to the world as you progress, a close precedent to Violet's resonance mechanic. Nomada Studio avoided dialogue to leave "room to project their own thoughts and interpretations" ([Vice, 2024-12-20](https://www.vice.com/en/article/nomada-studio-lets-me-in-to-learn-how-gris-and-neva-deliver-a-beautiful-and-touching-message-interview/)), and its creative director said "the complete elimination of death and violence" was "in part" for pacing ([Conrad Roset, 2019](https://thatgamersasylum.wordpress.com/2019/01/26/gris-creative-director-conrad-roset-interview/)). Jenova Chen on Journey: "We build our games like a Japanese garden, where the design is perfect when you cannot remove anything else" (Game Developer, 2012).
- **Story as the level-design anchor.** Celeste's "fractal story" gives the whole game, each area and each screen its own arc, and pacing follows the emotional curve (Maddy Thorson, GDC 2017). Violet's settled structure, linear chapters with side paths, fits this directly.
- **A one-page frame before any lore.** Blind Squirrel's 2025 narrative-design series ([part 2](https://blindsquirrelentertainment.com/news/Narrative-Design-Part-2)): logline, core fantasy, narrative pillars tied to mechanics, one or two themes ("Having too much to say results in not saying much at all"), tone, then a lore bible with each character's want versus need.
- **Human editors stay.** GDC 2026's editing microtalks: "you cannot replace the touch of a human. Editing is [...] emotional consistency" ([Game Developer, 2026-03-12](https://www.gamedeveloper.com/design/making-the-case-for-strong-human-narrative-editors)).

## Tools

The `story-development` skill borrows patterns from these rather than installing anything. If a session wants the tools themselves:

| Tool | Use | License (checked) |
|---|---|---|
| [addyosmani/clarity](https://github.com/addyosmani/clarity) | interview mode, provenance note | MIT |
| [zenstory-ai/novel-to-game](https://github.com/zenstory-ai/novel-to-game) | immutable/adaptable/open/conflicted triage | MIT |
| [danjdewhurst/story-skills](https://github.com/danjdewhurst/story-skills) | story bible layout, deterministic continuity checks | MIT |
| [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | tiered anti-slop pass | MIT |
| [haowjy/creative-writing-skills](https://github.com/haowjy/creative-writing-skills) | critic and failure-mode lists | Apache-2.0 |
| [adaumann/speckit-preset-game-narrative-writing](https://github.com/adaumann/speckit-preset-game-narrative-writing) | game-narrative question banks, challenge mode | none detected by GitHub; read only |
| [NousResearch/autonovel](https://github.com/NousResearch/autonovel) | structural anti-pattern list | none detected; read only |

## Running Violet's story sessions

The process is the `story-development` skill in Sami's dotfiles ([plugins/sjawhar/skills/story-development](https://github.com/sjawhar/dotfiles/tree/main/plugins/sjawhar/skills/story-development)). It keeps the story's state in `docs/story/`: a bible of settled facts, a decisions log, open questions, and one note per session. Violet's sessions start from:

- **Settled:** [decision 0015](../../decisions/0015-story-direction.md) (Scarlet, her hair, Slate as pursuer turned ally, "Memories of Others" as a few fragments per chapter, no combat, the desert world) and [decision 0014](../../decisions/0014-mechanics-round-1.md) (mechanics). Everything else is open, including the ending.
- **The 2019 draft to triage:** [archive-digest.md](../2026-09/archive-digest.md), element by element: the Academy, the Artifact, the accident, Kuluun, Slate, the Library, the ending.
- **The mechanic to test the theme against:** color resonance, as settled in decision 0014.

To start, open a new session in the project-violet checkout and type `/skill:story-development` followed by what you want to work on.

## Gaps

- Borgen's X account and a Reddit thread on the episode couldn't be read. He hasn't said what changed in his process for book two.
- GDC Vault talks (Lauren Bond's 2025 "Creating Playable Stories", Celeste, Ori) are paywalled beyond abstracts; Celeste and GRIS findings rest on public videos and interviews.
- Hollow Knight and Playdead process claims are secondhand and are not used in the skill.
