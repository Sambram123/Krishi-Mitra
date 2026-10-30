"""
Krishi Mitra — NLU Provider Abstraction & Factory
"""

import os
from typing import Protocol, Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from backend.nlu.schemas import ExtractOut


class NLUProvider(Protocol):
    def extract(
        self,
        transcript: str,
        known: Dict[str, Any],
        missing: List[str],
        correction: Optional[str] = None,
    ) -> ExtractOut:
        """Extracts structured entities matching ExtractOut."""
        ...

    def phrase(self, prompt: str) -> str:
        """Phrases concise Kannada speech output."""
        ...


def get_provider(provider_name: Optional[str] = None) -> NLUProvider:
    """Factory creating configured NLU provider."""
    name = (provider_name or os.getenv("NLU_PROVIDER", "gemini")).lower()
    if name == "ollama":
        from backend.nlu.providers.ollama import OllamaProvider
        return OllamaProvider()
    elif name == "gemini":
        from backend.nlu.providers.gemini import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown NLU_PROVIDER: '{name}'. Supported: 'gemini', 'ollama'.")
