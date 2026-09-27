from pathlib import Path

from conftest import sidecar_path


def test_refuses_to_overwrite_an_existing_out_without_force(repo: Path, run):
    out = repo / "circle.png"
    out.write_bytes(b"already here")

    code, _, err = run(
        "image",
        "--provider",
        "openai",
        "--model",
        "gpt-image-2",
        "--prompt",
        "a single red circle on a white background",
        "--out",
        str(out),
    )

    assert code != 0
    assert "already exists" in err
    assert "--force" in err
    # Untouched: the provider was never called because the check runs first.
    assert out.read_bytes() == b"already here"
    assert not sidecar_path(out).exists()
