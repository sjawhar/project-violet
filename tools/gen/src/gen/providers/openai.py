"""OpenAI image-generation adapter: gpt-image-* models via the REST Images API.

Verified 2026-09-26 against `GET https://api.openai.com/v1/models`; see ../../README.md
for the full list of image models this key can see and their shutdown dates. No `--seed`
support: the Images API has no seed parameter, so passing one is a clear error rather than
a silently ignored value. No `negative_prompt` parameter either; it is folded into the
prompt text (see `combine_prompt`), but the sidecar still records the original, separate
fields.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import httpx

from gen.providers import PNG_MIME, GeneratedImage, ProviderError, combine_prompt, ensure_png, require_env

API_BASE = "https://api.openai.com/v1"
TIMEOUT = httpx.Timeout(180.0, connect=10.0)


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "application/octet-stream"


def generate(
    prompt: str,
    *,
    model: str,
    size: str | None,
    seed: int | None,
    negative_prompt: str | None,
    inputs: list[Path],
) -> GeneratedImage:
    if seed is not None:
        raise ProviderError("openai: --seed is not supported by the Images API; omit it for this provider")
    for path in inputs:
        if not path.is_file():
            raise ProviderError(f"openai: --input {path}: no such file")

    api_key = require_env("OPENAI_API_KEY")
    combined_prompt = combine_prompt(prompt, negative_prompt)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with httpx.Client(base_url=API_BASE, headers=headers, timeout=TIMEOUT) as client:
            if inputs:
                data = {"model": model, "prompt": combined_prompt}
                if size is not None:
                    data["size"] = size
                files = [("image[]", (path.name, path.read_bytes(), _guess_mime(path))) for path in inputs]
                response = client.post("/images/edits", data=data, files=files)
            else:
                payload: dict[str, object] = {"model": model, "prompt": combined_prompt, "n": 1}
                if size is not None:
                    payload["size"] = size
                response = client.post("/images/generations", json=payload)
    except httpx.HTTPError as error:
        raise ProviderError(f"openai: {error}") from error

    try:
        body = response.json()
    except ValueError:
        raise ProviderError(f"openai: non-JSON response (HTTP {response.status_code}): {response.text[:500]}") from None

    if "error" in body:
        raise ProviderError(f"openai: {body['error'].get('message', body['error'])}")
    if response.status_code >= 400:
        raise ProviderError(f"openai: HTTP {response.status_code}: {body}")

    items = body.get("data") or []
    if not items or "b64_json" not in items[0]:
        raise ProviderError("openai: response did not include image data")

    raw = base64.b64decode(items[0]["b64_json"])
    mime = f"image/{body.get('output_format', 'png')}"
    png = ensure_png(raw, mime)

    params = {"size": body.get("size", size or "auto")}
    if "quality" in body:
        params["quality"] = body["quality"]
    if "background" in body:
        params["background"] = body["background"]

    return GeneratedImage(data=png, mime=PNG_MIME, model_version=None, params=params)
