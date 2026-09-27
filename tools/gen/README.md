# gen

Calls an image-generation provider's REST API and writes the result, plus its
[provenance](../provenance) sidecar, next to it. This is the only way generated art
should enter the repo: it is what makes `provenance check` and the Steam AI-disclosure
report accurate.

## Usage

```bash
secrets OPENAI_API_KEY -- uv run --project tools/gen gen image \
  --provider openai --model gpt-image-2 \
  --prompt "a violet head scarf, painted, transparent background" \
  --size 1024x1024 \
  --out game/art/scarf.png

secrets GEMINI_API_KEY -- uv run --project tools/gen gen image \
  --provider gemini --model gemini-3.1-flash-image \
  --prompt "recolor the scarf indigo, keep everything else the same" \
  --input game/art/scarf.png \
  --size 1024x1024 \
  --out game/art/scarf-indigo.png
```

Run from inside the repository (or a subdirectory): `gen` finds `provenance.toml` the
same way `provenance` does, by walking up from the current directory, so `--out` can
point anywhere the resulting sidecar should live.

```
gen image --provider {openai|gemini} --model MODEL --prompt TEXT
          [--negative-prompt TEXT] [--size WxH] [--seed N]
          [--input PATH ...] [--background {transparent,opaque}]
          [--quality {low,medium,high}]
          [--license proprietary] [--force]
          --out PATH
```

- `--force` is required to replace an existing `--out` (and its sidecar); otherwise `gen`
  refuses rather than silently overwriting art.
- `--input PATH` (repeatable) passes a reference image to the provider's edit /
  multimodal-input mechanism. Every input must already be **inside the repository** and
  **already have its own valid provenance record** (`provenance check` verifies input
  records transitively) — `gen` refuses with a clear error otherwise, rather than writing
  a record `provenance check` would go on to reject.
- On any provider error (bad model name, missing API key, rejected request, network
  failure), `gen` exits non-zero, prints the provider's message, and leaves **no** output
  file and **no** sidecar — even if the image had already been written to `--out` before
  the sidecar step failed.
- The written image is always a real PNG (`--out`'s extension is not consulted): Gemini's
  API returns JPEG by default, so `gen` decodes and re-encodes it before writing; OpenAI's
  API already returns PNG.
- `--background {transparent,opaque}` (OpenAI only; bake-off body parts use `transparent`)
  sends the Images API's `background` parameter and forces `output_format: "png"` (in both
  `/images/generations` and `/images/edits`), so a transparent PNG actually carries an
  alpha channel rather than a flattened white background. Gemini's `generateContent` has no
  equivalent parameter, so `gen` refuses `--background` for `--provider gemini` with a clear
  error rather than silently ignoring it.
- `--quality {low,medium,high}` (OpenAI only) sends the Images API's `quality` parameter.
  Without the flag `gen` sends `high`. Left unset, the API chooses per request: it chose `low`
  for every piece of bake-off art made before this flag existed, and `medium` for one
  transparent test image. Art that gets judged or shipped shouldn't depend on that choice.
  Pass `--quality low` for drafts and tests. Gemini has no quality parameter, so `gen` refuses
  `--quality` for `--provider gemini`.

### Provenance recorded

For every successful run, `gen` calls `provenance.record.write_record` itself (there is no
separate `provenance record` step) with:

- `tool="gen"`, `tool_version` = this package's version, `origin="generated"`, `kind="image"`
- `provider`, `model`, and `model_version` when the API reports one (OpenAI's Images API
  does not; Gemini's `generateContent` does, in `modelVersion`)
- `prompt` and `negative_prompt` exactly as given on the command line — even though neither
  provider has a native negative-prompt field (see below), the sidecar keeps them separate
  from what was actually sent to the API
- `seed`, when given and accepted (OpenAI's Images API has no seed parameter; `gen` refuses
  `--seed` for `--provider openai` rather than silently ignoring it and recording a seed
  that had no effect)
- `params.size`, the `--size` actually used; for OpenAI, `params.quality` and
  `params.background` as the response echoes them back, which is what the API actually used
- `inputs`, each resolved to a repo-relative path and content hash

### Neither provider has a negative-prompt or (for OpenAI) a seed parameter

- OpenAI's Images API (`/v1/images/generations`, `/v1/images/edits`) accepts `model`,
  `prompt`, `size`, `n`, and (for edits) `image[]` — no `negative_prompt`, no `seed`
  (confirmed against the live API 2026-09-26: both return `unknown_parameter`).
- Gemini's `generateContent` accepts a `seed` field in `generationConfig` but no
  `negativePrompt` field (confirmed against the live API 2026-09-26: `Unknown name
  "negativePrompt"`).

Both adapters fold `--negative-prompt` into the prompt text actually sent to the provider
(`"{prompt}\n\nAvoid: {negative_prompt}"`); this is a real, working transformation, not a
silent no-op, and the sidecar still records the original fields separately.

### `--size` is provider-specific

- **OpenAI**: `--size` is passed straight through as `WxH`. The live API accepts arbitrary
  width/height as long as both are divisible by 16 and the total pixel count is above a
  minimum floor; `1024x1024` (1,048,576 px) works, `800x800` and smaller do not
  ("Requested resolution is below the current minimum pixel budget", confirmed 2026-09-26).
- **Gemini**: `imageConfig` only accepts a fixed set of `(aspectRatio, imageSize)`
  combinations, not an arbitrary pixel size. `gen` translates `--size WxH` through the
  table in `providers/gemini.py`, transcribed from the
  [Gemini image-generation docs](https://ai.google.dev/gemini-api/docs/generate-content/image-generation)
  (accessed 2026-09-26) for `gemini-3.1-flash-image`. A `--size` outside that table is a
  clear error listing the supported sizes, not a silent nearest-match guess. `1024x1024`
  (`aspectRatio="1:1"`, `imageSize="1K"`) is in the table and is what the live tests and
  the smoke run below use. Gemini's absolute smallest documented size is `512x512`
  (`imageSize="512"`), but repeated verification calls at that size occasionally returned
  `finishReason: IMAGE_RECITATION` with no image (a transient content-safety rejection,
  not specific to the prompt used here) — `1024x1024` was reliable across every attempt,
  so that is the size this tool recommends and tests against for both providers.
- If `--size` is omitted entirely, `gen` does not send any size configuration and the
  provider picks its own default (OpenAI defaults to a model-chosen size; Gemini returned
  a non-table `1408x768` in testing).

### Costs

Neither API reports a dollar cost directly. What each reports is recorded in `params` /
observable in testing, but not stored per-sidecar since it varies run to run:

- OpenAI's `/v1/images/generations` and `/v1/images/edits` responses include a `usage`
  object (`input_tokens`, `output_tokens`, with an `image_tokens` breakdown). A
  `1024x1024` generation where the API chose `low` used ~200 output tokens in testing.
- Gemini's `generateContent` responses include `usageMetadata`
  (`promptTokenCount`, `candidatesTokenCount`, with a per-modality breakdown). A
  `1024x1024` generation used ~1,100–1,500 candidate tokens in testing.

See each provider's own pricing page for current per-token rates
(`https://openai.com/api/pricing/`, `https://ai.google.dev/gemini-api/docs/pricing`).

## Verified model IDs (2026-09-26)

Discovered via each provider's model-list endpoint; do not guess new ones without
re-checking these. Models this tool is verified against are **bold**.

### OpenAI — `GET https://api.openai.com/v1/models`, image-capable models

| Model | Created | Shutdown date |
|---|---|---|
| **`gpt-image-2`** | 2026-04-17 | none scheduled |
| `gpt-image-2-2026-04-21` | 2026-04-17 | none scheduled |
| `gpt-image-2.5-flare` | 2026-09-04 | none scheduled |
| `gpt-image-2.5-flare-2026-09-08` | 2026-09-08 | none scheduled |
| `gpt-image-2.5-sunburst` | 2026-09-04 | none scheduled |
| `gpt-image-2.5-sunburst-2026-09-08` | 2026-09-08 | none scheduled |
| `gpt-image-1.5` | 2025-11-25 | 2026-12-01 |
| `gpt-image-1-mini` | 2025-09-26 | 2026-12-01 |
| `chatgpt-image-latest` | 2025-12-16 | 2026-12-01 |
| `gpt-image-1` | 2025-04-24 | **2026-10-23** |

`gpt-image-1`, the previous default, sunsets next month (2026-10-23); `gpt-image-2` is its
stable, undated successor and is what this tool uses by default. The `2.5-flare` /
`2.5-sunburst` pair are newer, still-unnamed preview variants with no shutdown date set;
re-verify before switching to either.

### Gemini — `GET https://generativelanguage.googleapis.com/v1beta/models`, image-capable models

| Model | Display name | Notes |
|---|---|---|
| `gemini-2.5-flash-image` | Nano Banana | legacy; Google recommends migrating off it |
| `gemini-3-pro-image` | Nano Banana Pro | premium tier, higher cost |
| `gemini-3-pro-image-preview` | Nano Banana Pro | preview channel of the above |
| **`gemini-3.1-flash-image`** | Nano Banana 2 | general-purpose; multi-reference-input capable |
| `gemini-3.1-flash-image-preview` | Nano Banana 2 | preview channel of the above |
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | fastest/cheapest; **not** optimized for `--input` |

`gemini-3.1-flash-image` is what this tool uses by default: it is the current
general-purpose tier and, unlike the Lite variant, is documented as handling reference
inputs well — relevant since `--input` is a supported flag.

## Smoke-tested

Both providers were run end-to-end (`gen image ... --out /tmp/gen-smoke/<provider>-circle.png`
with `--prompt "a single red circle on a white background" --size 1024x1024`), from the
repository root so `gen` and `provenance check` shared the same `provenance.toml`. Both
produced a 1024x1024 PNG, a sidecar next to it, and `provenance check <path>` (run
explicitly against the absolute `/tmp` path) exited 0 for both. The `/tmp` output was not
under any `provenance.toml` root, and `provenance check` did not need it to be: an
explicit file argument is checked directly, without requiring root/extension membership.
The smoke-run files were deleted afterward and were never committed.

`--background transparent` was also smoke-tested against the live OpenAI API
(`gpt-image-2`, `--size 1024x1024`): the result loaded as `RGBA` and
`Image.open(p).getchannel("A").getextrema()` was `(0, 254)` — a real alpha channel, not a
flattened background — and the sidecar's `params.background` recorded `"transparent"`.
`gpt-image-2` accepted `--background` directly; the plan's `gpt-image-1.5` fallback (for a
model that rejects the parameter) was not needed.
