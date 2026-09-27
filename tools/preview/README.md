# preview

Turns a PR's assets into something Sami can judge from his phone: inline PNG/GIF thumbnails for the PR description, and a review gallery on GitHub Pages that also plays audio and 3D turntables.

## Setup

`mise install` in the repository installs the pinned `ffmpeg`, `magick` (ImageMagick) and `blender`. Run the commands below through mise (`mise exec -- ...`, or an activated shell) so those versions are on `PATH`.

Blender is pinned in `mise.toml` through mise's `http` backend: `download.blender.org` answers scripted downloads with a Cloudflare 403, so the archive comes from the Clarkson University mirror, and mise verifies it against the SHA-256 that Blender publishes. To move to another release, change `version` and replace `checksum` with the `linux-x64.tar.xz` line of `https://mirror.clarkson.edu/blender/release/Blender<major.minor>/blender-<version>.sha256` (the same file is on `download.blender.org`).

Turntables render with Cycles. `--render-device auto` uses OptiX, then CUDA, then the CPU, and prints which one it used. On oryx the RTX 3070 works only while the `nvidia` and `nvidia_uvm` kernel modules are loaded.

## Use

Run from the repository root.

```sh
uv run --project tools/preview preview build 12 game/art/scarf.png game/anim/walk/ game/audio/theme.ogg game/props/lantern.glb
uv run --project tools/preview preview publish 12      # prints the Markdown for the PR description
uv run --project tools/preview preview unpublish 12    # removes the gallery from gh-pages
```

`build` writes `out/review/pr-<n>/`: `index.html`, a contact sheet of the images, and per asset
- an image scaled to at most 1600 px;
- for a frame-sequence directory, GIF, or video: an MP4 and a GIF;
- for audio: the file for an HTML5 player and a waveform PNG;
- for a 3D model (`.glb`, `.gltf`, `.fbx`, `.blend`): a 6-second turntable MP4 and GIF.

Each item shows its provenance summary from `<asset>.provenance.json`. A missing tool, a corrupt input, or a failed render exits non-zero naming the asset, and leaves any earlier build of that PR untouched.

`publish` checks through the GitHub API that Pages serves the root of `gh-pages`, then replaces only `review/pr-<n>/` on that branch from a temporary jj workspace and pushes. It refuses to push if the commit would touch anything else or would miss any file of the build. The gallery is at `https://sjawhar.github.io/project-violet/review/pr-<n>/` once Pages rebuilds, usually within a minute.

## Tests

```sh
mise exec -- uv run --project tools/preview pytest tools/preview/tests
```

The tests generate every fixture with the pinned tools and publish to a local bare repository; they need `jj`, `git`, and the mise toolchain.
