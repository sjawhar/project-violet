"""Gemini image-generation adapter: Gemini's native multimodal ("Nano Banana") image models
via `generateContent`.

Verified 2026-09-26 against `GET https://generativelanguage.googleapis.com/v1beta/models`;
see ../../README.md for the full list of image models this key can see. Unlike OpenAI,
Gemini's `imageConfig` only accepts a fixed set of (aspectRatio, imageSize) combinations, not
an arbitrary pixel size, so `--size WxH` is translated through `_SIZE_TABLE`, transcribed from
https://ai.google.dev/gemini-api/docs/generate-content/image-generation (accessed 2026-09-26)
for `gemini-3.1-flash-image`. A `--size` outside that table is a clear error rather than a
silent nearest-match guess. There is no dedicated `negativePrompt` field either; it is folded
into the prompt text (see `combine_prompt`), but the sidecar still records the original,
separate fields.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import httpx

from gen.providers import GeneratedImage, ProviderError, combine_prompt, ensure_png, require_env

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
TIMEOUT = httpx.Timeout(180.0, connect=10.0)

# (aspectRatio, imageSize) -> the exact "WxH" pixel dimensions Gemini documents for
# gemini-3.1-flash-image. Keyed by "WxH" so `--size` can be looked up directly.
_SIZE_TABLE: dict[str, tuple[str, str]] = {
    "512x512": ("1:1", "512"), "1024x1024": ("1:1", "1K"), "2048x2048": ("1:1", "2K"), "4096x4096": ("1:1", "4K"),
    "256x1024": ("1:4", "512"), "512x2048": ("1:4", "1K"), "1024x4096": ("1:4", "2K"), "2048x8192": ("1:4", "4K"),
    "192x1536": ("1:8", "512"), "384x3072": ("1:8", "1K"), "768x6144": ("1:8", "2K"), "1536x12288": ("1:8", "4K"),
    "424x632": ("2:3", "512"), "848x1264": ("2:3", "1K"), "1696x2528": ("2:3", "2K"), "3392x5056": ("2:3", "4K"),
    "632x424": ("3:2", "512"), "1264x848": ("3:2", "1K"), "2528x1696": ("3:2", "2K"), "5056x3392": ("3:2", "4K"),
    "448x600": ("3:4", "512"), "896x1200": ("3:4", "1K"), "1792x2400": ("3:4", "2K"), "3584x4800": ("3:4", "4K"),
    "1024x256": ("4:1", "512"), "2048x512": ("4:1", "1K"), "4096x1024": ("4:1", "2K"), "8192x2048": ("4:1", "4K"),
    "600x448": ("4:3", "512"), "1200x896": ("4:3", "1K"), "2400x1792": ("4:3", "2K"), "4800x3584": ("4:3", "4K"),
    "464x576": ("4:5", "512"), "928x1152": ("4:5", "1K"), "1856x2304": ("4:5", "2K"), "3712x4608": ("4:5", "4K"),
    "576x464": ("5:4", "512"), "1152x928": ("5:4", "1K"), "2304x1856": ("5:4", "2K"), "4608x3712": ("5:4", "4K"),
    "1536x192": ("8:1", "512"), "3072x384": ("8:1", "1K"), "6144x768": ("8:1", "2K"), "12288x1536": ("8:1", "4K"),
    "384x688": ("9:16", "512"), "768x1376": ("9:16", "1K"), "1536x2752": ("9:16", "2K"), "3072x5504": ("9:16", "4K"),
    "688x384": ("16:9", "512"), "1376x768": ("16:9", "1K"), "2752x1536": ("16:9", "2K"), "5504x3072": ("16:9", "4K"),
    "792x168": ("21:9", "512"), "1584x672": ("21:9", "1K"), "3168x1344": ("21:9", "2K"), "6336x2688": ("21:9", "4K"),
}


def _supported_sizes() -> str:
    return ", ".join(sorted(_SIZE_TABLE, key=lambda size: tuple(int(n) for n in size.split("x"))))


def _image_config(model: str, size: str) -> dict[str, str]:
    try:
        aspect_ratio, image_size = _SIZE_TABLE[size]
    except KeyError:
        raise ProviderError(
            f"gemini: --size {size} is not one of the fixed sizes {model} supports: {_supported_sizes()}"
        ) from None
    return {"aspectRatio": aspect_ratio, "imageSize": image_size}


def generate(
    prompt: str,
    *,
    model: str,
    size: str | None,
    seed: int | None,
    negative_prompt: str | None,
    inputs: list[Path],
    background: str | None,
) -> GeneratedImage:
    if background is not None:
        raise ProviderError(
            "gemini: --background is not supported by Gemini's generateContent API; omit it for this provider"
        )
    parts: list[dict] = [{"text": combine_prompt(prompt, negative_prompt)}]
    for path in inputs:
        if not path.is_file():
            raise ProviderError(f"gemini: --input {path}: no such file")
        mime, _ = mimetypes.guess_type(path.name)
        parts.append(
            {"inline_data": {"mime_type": mime or "application/octet-stream", "data": base64.b64encode(path.read_bytes()).decode("ascii")}}
        )

    generation_config: dict[str, object] = {"responseModalities": ["IMAGE"]}
    if seed is not None:
        generation_config["seed"] = seed
    if size is not None:
        generation_config["imageConfig"] = _image_config(model, size)

    api_key = require_env("GEMINI_API_KEY")
    body = {"contents": [{"parts": parts}], "generationConfig": generation_config}

    try:
        response = httpx.post(
            f"{API_BASE}/models/{model}:generateContent",
            params={"key": api_key},
            json=body,
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as error:
        raise ProviderError(f"gemini: {error}") from error

    try:
        payload = response.json()
    except ValueError:
        raise ProviderError(f"gemini: non-JSON response (HTTP {response.status_code}): {response.text[:500]}") from None

    if "error" in payload:
        raise ProviderError(f"gemini: {payload['error'].get('message', payload['error'])}")
    if response.status_code >= 400:
        raise ProviderError(f"gemini: HTTP {response.status_code}: {payload}")

    candidates = payload.get("candidates") or []
    image_part = next(
        (
            part["inlineData"]
            for candidate in candidates
            for part in candidate.get("content", {}).get("parts", [])
            if "inlineData" in part
        ),
        None,
    )
    if image_part is None:
        reason = candidates[0].get("finishReason", "unknown") if candidates else "no candidates"
        raise ProviderError(f"gemini: response had no image data (finishReason={reason})")

    raw = base64.b64decode(image_part["data"])
    png = ensure_png(raw, image_part["mimeType"])
    params = {"size": size} if size is not None else {}

    return GeneratedImage(data=png, mime="image/png", model_version=payload.get("modelVersion"), params=params)
