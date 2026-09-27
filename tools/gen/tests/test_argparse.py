import pytest

from gen.cli import main


def test_missing_prompt_is_an_argparse_error(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        main(["image", "--provider", "openai", "--model", "gpt-image-2", "--out", "out.png"])
    assert excinfo.value.code == 2
    assert "--prompt" in capsys.readouterr().err


def test_unknown_provider_is_an_argparse_error(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "image",
                "--provider",
                "not-a-real-provider",
                "--model",
                "whatever",
                "--prompt",
                "a circle",
                "--out",
                "out.png",
            ]
        )
    assert excinfo.value.code == 2
    assert "--provider" in capsys.readouterr().err


def test_missing_out_is_an_argparse_error(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        main(["image", "--provider", "openai", "--model", "gpt-image-2", "--prompt", "a circle"])
    assert excinfo.value.code == 2
    assert "--out" in capsys.readouterr().err
