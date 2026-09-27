# preview

Turns a PR's assets into something Sami can judge from his phone: inline PNG/GIF thumbnails for the PR description, and a review gallery on GitHub Pages that also plays video, audio and 3D turntables.

## Setup

`mise install` in the repository installs the pinned `ffmpeg`, `magick` (ImageMagick) and `blender`. Run the commands below through mise (`mise exec -- ...`, or an activated shell) so those versions are on `PATH`.

Blender is pinned in `mise.toml` through mise's `http` backend: `download.blender.org` answers scripted downloads with a Cloudflare 403, so the archive comes from the Clarkson University mirror, and mise verifies it against the SHA-256 that Blender publishes. To move to another release, change `version` and replace `checksum` with the `linux-x64.tar.xz` line of `https://mirror.clarkson.edu/blender/release/Blender<major.minor>/blender-<version>.sha256` (the same file is on `download.blender.org`).

Turntables render with Cycles. With `--render-device auto` (the default), a short-lived Blender first checks for OptiX, then CUDA; if neither works, or the check errors or hangs for 60 s, the render runs on the CPU and the build says so. `--render-device optix|cuda|cpu` skips the check. A 144-frame 720 px turntable takes about 20 s on the RTX 3070 on oryx and about 5 minutes on its CPU.

## Use

Run anywhere inside the repository; output goes to `out/review/pr-<n>/` at the root (git-ignored).

```sh
uv run --project tools/preview preview build 12 game/art/scarf.png game/anim/walk/ game/audio/theme.ogg game/props/lantern.glb
uv run --project tools/preview preview publish 12      # prints the Markdown for the PR description
uv run --project tools/preview preview unpublish 12    # removes the gallery from gh-pages
```

`build` writes `index.html`, a contact sheet of the images, and per asset
- an image as WebP, at most 1600 px on its long side;
- for a frame-sequence directory (frames ordered by the numbers in their names, all one size and file type), a video, or an animated GIF: an H.264 MP4, a poster frame, and a GIF thumbnail (360 px; frame sequences and GIFs keep every frame, videos and turntables drop to 10 fps);
- for audio: AAC for the page's player, and a waveform PNG;
- for a 3D model (`.glb`, `.gltf`, `.fbx`, `.blend`): a 6-second turntable MP4, poster and GIF.

Each item shows its provenance record (read and checked with `tools/provenance`): origin, tool, model, prompt, inputs, human edits, license, and the source file's sha256. A missing record or one that no longer matches the file is shown in red; an invalid record, a missing tool, a corrupt input, an LFS pointer in place of an asset, or a failed render stops the build, naming the file, and leaves any earlier build of that PR untouched. Unchanged inputs produce byte-identical output.

`publish` checks through the GitHub API that Pages serves the root of `gh-pages`, then replaces only `review/pr-<n>/` on that branch and pushes. It never touches your checkout or jj store: it works in a private blobless clone under `$PREVIEW_CACHE_DIR` (default `~/.cache/preview`; the first publish downloads the current site once, about 50 MB today), commits the build as plain blobs whatever `.gitattributes` says, pushes without force, and redoes the step on the new tip if someone else pushed first. It refuses to push a commit that would touch anything else or miss any file of the build. The thumbnails in the printed Markdown point at that commit, so they keep showing what was reviewed after a republish or `unpublish`. The gallery itself is at `https://sjawhar.github.io/project-violet/review/pr-<n>/` once Pages rebuilds, usually within a minute.

## Tests

```sh
mise exec -- uv run --project tools/preview pytest tools/preview/tests
```

The tests generate every fixture with the pinned tools, render on the CPU, and publish to a local bare repository; they need `git` and the mise toolchain.
