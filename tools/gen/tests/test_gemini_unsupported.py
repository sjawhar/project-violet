import pytest

from gen.providers import ProviderError
from gen.providers import gemini as gemini_provider


@pytest.mark.parametrize(
    ("option", "background", "quality"),
    [("--background", "transparent", None), ("--quality", None, "high")],
    ids=["background", "quality"],
)
def test_gemini_refuses_an_option_its_api_does_not_have(option: str, background: str | None, quality: str | None):
    with pytest.raises(ProviderError, match=option):
        gemini_provider.generate(
            "a circle",
            model="gemini-3.1-flash-image",
            size=None,
            seed=None,
            negative_prompt=None,
            inputs=[],
            background=background,
            quality=quality,
        )
