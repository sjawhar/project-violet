"""Tests that make real calls to a provider's API. Select them explicitly: `pytest -m live`.

They need real credentials: `secrets OPENAI_API_KEY GEMINI_API_KEY -- uv run pytest -m live`.
"""

from pathlib import Path

import pytest
from PIL import Image
from provenance.cli import main as provenance_main

from conftest import sidecar_path

pytestmark = pytest.mark.live

# Verified 2026-09-26 against each provider's model-list endpoint; see README.md.
PROVIDERS = [
    ("openai", "gpt-image-2", "gpt-image-999-this-model-does-not-exist"),
    ("gemini", "gemini-3.1-flash-image", "gemini-99-this-model-does-not-exist"),
]


@pytest.mark.parametrize(("provider", "model", "invalid_model"), PROVIDERS, ids=[p[0] for p in PROVIDERS])
def test_a_provider_error_leaves_no_output_file_and_no_sidecar(repo: Path, run, provider: str, model: str, invalid_model: str):
    out = repo / "circle.png"

    code, _, err = run(
        "image",
        "--provider",
        provider,
        "--model",
        invalid_model,
        "--prompt",
        "a single red circle on a white background",
        "--size",
        "1024x1024",
        "--out",
        str(out),
    )

    assert code != 0
    assert err.strip() != ""
    assert not out.exists()
    assert not sidecar_path(out).exists()


@pytest.mark.parametrize(("provider", "model", "invalid_model"), PROVIDERS, ids=[p[0] for p in PROVIDERS])
def test_generates_a_real_image_with_a_valid_provenance_sidecar(repo: Path, run, provider: str, model: str, invalid_model: str):
    out = repo / "circle.png"

    code, out_text, err = run(
        "image",
        "--provider",
        provider,
        "--model",
        model,
        "--prompt",
        "a single red circle on a white background",
        "--size",
        "1024x1024",
        "--out",
        str(out),
    )

    assert code == 0, err

    with Image.open(out) as image:
        image.load()
        assert image.format == "PNG"

    sidecar = sidecar_path(out)
    assert sidecar.is_file()

    check_code = provenance_main(["check", str(out)])
    assert check_code == 0
