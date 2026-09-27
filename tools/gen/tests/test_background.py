import pytest

from gen.providers import ProviderError
from gen.providers import gemini as gemini_provider


def test_gemini_raises_when_background_is_set():
    with pytest.raises(ProviderError, match="--background"):
        gemini_provider.generate(
            "a circle",
            model="gemini-3.1-flash-image",
            size=None,
            seed=None,
            negative_prompt=None,
            inputs=[],
            background="transparent",
        )
