Note: canvas pixel-diffing across all seven contact-sheet rows shows **A and B are byte-identical except for one small crop of the head/face region in every frame** (confirmed via a full-image diff heatmap — every other pixel of robe, scarf, hands, feet, and silhouette matches exactly). The findings below reflect that: differences concentrate entirely on how the visible eye reads under the hood.

## Visual quality — same

Robe, scarf, hood, cloth-fold shading, and rendering fidelity are pixel-identical between the two sets outside the tiny eye region, so overall "how beautiful and finished" the character looks is not meaningfully different.

- **A: 3/5**
- **B: 3/5**

Both fall short of the bar on the same points: flat, single-direction shading with no rim light or color bounce (GRIS's blue god-rays and Planet of Lana's warm key light both wrap the character in the scene's palette; this character floats on neutral gray with no light integration), soft/fuzzy anti-aliased edges on the hood brim and hem rather than a crisp painted line, and a fairly narrow, desaturated brown-on-gray palette that reads as competent but plain next to the two bar games' rich, atmospheric color work.

## Character appeal — A

- **A: 3/5** — B: 2/5

Zoomed crops of every row (idle, run, jump, fall, double_jump, dash, land) show the same distinction each time: A's visible eye carries a small bright catchlight/highlight, giving the face a spark of life even in profile under the hood. B's eye is a flat, dark smudge with no catchlight in any of the seven poses — most noticeably in the high-energy dash and double_jump frames, where the body language says "alert" but the face reads inert/half-asleep. Since the hood already hides most of the face, that one visible eye is doing all the expressive work, so its absence in B is a proportionally large appeal loss.

## Color readability — same

Confirmed via pixel diff: the scarf and silhouette are literally identical images between A and B (the only rendering difference is inside the ~45×47px head region, and it doesn't touch the scarf or body outline).

- **A: 3/5**
- **B: 3/5**

The white/cream scarf (~RGB 202,202,202) contrasts well against the neutral gray backdrop (128,128,128) and reads instantly as the character's signature accent, much like GRIS's dress or Ori's light trail. But the robe itself (~RGB 128,112,102) is nearly luminance-matched to the gray background (delta of roughly 12 in brightness, mostly separated by hue, not value), so the torso/leg silhouette has weak value contrast and can start to melt into a neutral backdrop — especially in overlapping-limb poses (fall, double_jump) where the scarf is the only element keeping the pose legible at a glance.

---

## Three biggest gaps vs. the bar

### Set A
1. **No rim light or environmental color bounce.** The hood and robe are shaded with flat, single-source diffuse shadow only; there's no rim/backlight or color bleed from an implied scene, unlike GRIS's blue-lit water shots or Lana's warm-lit forest, where the character visibly sits inside the light of its world.
2. **Soft anti-aliasing halo on cloth edges.** At 3–6x zoom, the hood brim, sleeve cuffs, and hem show a gray-fringed transition rather than a clean painted outline — reads as a compositing artifact, not intentional linework.
3. **Underdetailed hands and feet.** Hands are plain skin-toned mitts with no finger separation, and the bare feet are thin, spindly, and doll-like with no toe/shading detail — next to Lana's or Ori's expressive hand and foot posing, these read as simplified placeholders rather than characterful anatomy, most visible in the dash and land frames where they're prominent.

### Set B
1. **Same rim-light/flat-shading gap as A** — hood, robe, and shoulder need a directional light + bounce-color pass to integrate with any scene, rather than reading as a flat cutout on gray.
2. **Same cloth-edge anti-aliasing halo as A** — hood brim/hem/cuffs need cleaner alpha edges or an intentional outline stroke.
3. **Dead eye across all seven animations.** The visible eye is a near-solid dark shape with no catchlight or iris highlight in idle, run, jump, fall, double_jump, dash, or land — the face reads asleep/expressionless even mid-dash, where GRIS and Lana both keep a small readable glint in the eye even in profile or fast motion. This is the single highest-value, most concrete fix: add a 1–2px highlight and lighten the iris value slightly.
