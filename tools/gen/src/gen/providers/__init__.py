"""Provider adapters: one module per image-generation backend behind a common interface.

Each provider module (``openai``, ``gemini``) exposes a single function::

    def generate(
        prompt: str,
        *,
        model: str,
        size: str | None,
        seed: int | None,
        negative_prompt: str | None,
        inputs: list[Path],
    ) -> GeneratedImage: ...

that calls the provider's REST API over plain HTTPS and returns the resulting
image, or raises `ProviderError` with a message safe to show the user as-is.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, field
from typing import Protocol

from PIL import Image

PNG_MIME = "image/png"


class ProviderError(RuntimeError):
    """A provider rejected the request, failed, or is missing required setup (e.g. an API key).

    The message is shown to the user as-is, so it should already say what went wrong.
    """


@dataclass(frozen=True)
class GeneratedImage:
    """The bytes and metadata returned by a provider's `generate()` call."""

    data: bytes
    """Always PNG-encoded, regardless of what the provider returned; see `ensure_png`."""
    mime: str
    model_version: str | None
    params: dict[str, str] = field(default_factory=dict)
    """Reproducibility details worth recording (e.g. the actual size used), beyond prompt/model/seed."""


class Provider(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        model: str,
        size: str | None,
        seed: int | None,
        negative_prompt: str | None,
        inputs: list,
    ) -> GeneratedImage: ...


def combine_prompt(prompt: str, negative_prompt: str | None) -> str:
    """Neither provider's image API has a dedicated negative-prompt field; fold it into the prompt text.

    The original, separate `prompt` and `negative_prompt` are still what gets recorded in the
    provenance sidecar; this combined string is only what is sent to the provider.
    """
    if not negative_prompt:
        return prompt
    return f"{prompt}\n\nAvoid: {negative_prompt}"


def ensure_png(data: bytes, mime: str) -> bytes:
    """Normalize provider output to PNG bytes, so `--out` always holds a real PNG regardless of provider."""
    if mime == PNG_MIME:
        return data
    with Image.open(io.BytesIO(data)) as image:
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()


def require_env(name: str) -> str:
    """The named environment variable, or a `ProviderError` telling the user how to set it."""
    value = os.environ.get(name)
    if not value:
        raise ProviderError(f"{name} is not set; export it or run under `secrets {name} -- <command>`")
    return value
