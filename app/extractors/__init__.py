from typing import Optional
from app.extractors.base import BaseExtractor
from app.extractors.mock_extractor import MockExtractor
from app.config import settings


def get_extractor(provider: Optional[str] = None) -> BaseExtractor:
    """
    Factory resolving the active extractor implementation based on settings or runtime override.
    """
    selected_provider = (provider or settings.VLM_PROVIDER).lower()

    if selected_provider == "mock":
        return MockExtractor()
    elif selected_provider == "openai":
        from app.extractors.openai_vlm import OpenAIVLMExtractor
        return OpenAIVLMExtractor()
    elif selected_provider == "qwen":
        from app.extractors.qwen_vlm import QwenVLMExtractor
        return QwenVLMExtractor()
    else:
        raise ValueError(f"Unknown VLM provider '{selected_provider}'. Valid choices: 'mock', 'openai', 'qwen'.")


__all__ = ["BaseExtractor", "MockExtractor", "get_extractor"]
