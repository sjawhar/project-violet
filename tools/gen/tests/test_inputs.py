from pathlib import Path

from conftest import sidecar_path


def test_refuses_an_input_with_no_provenance_record(repo: Path, run, tmp_path_factory):
    reference = repo / "game/art/reference.png"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"reference pixels")
    # Deliberately no reference.png.provenance.json.

    out = repo / "circle.png"
    code, _, err = run(
        "image",
        "--provider",
        "openai",
        "--model",
        "gpt-image-2",
        "--prompt",
        "a single red circle on a white background",
        "--input",
        str(reference),
        "--out",
        str(out),
    )

    assert code != 0
    assert "provenance record" in err
    assert not out.exists()
    assert not sidecar_path(out).exists()


def test_refuses_an_input_outside_the_repository(repo: Path, run, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere") / "reference.png"
    outside.write_bytes(b"reference pixels")

    out = repo / "circle.png"
    code, _, err = run(
        "image",
        "--provider",
        "openai",
        "--model",
        "gpt-image-2",
        "--prompt",
        "a single red circle on a white background",
        "--input",
        str(outside),
        "--out",
        str(out),
    )

    assert code != 0
    assert "inside the repository" in err
    assert not out.exists()
    assert not sidecar_path(out).exists()
