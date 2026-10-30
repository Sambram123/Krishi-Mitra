"""
Krishi Mitra — Google Gen AI (Gemini 2.5 Flash) Provider
Uses official `google-genai` SDK with native response_schema=ExtractOut for zero-hallucination extraction.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from backend.nlu.schemas import ExtractOut
from backend.nlu.prompts import (
    EXTRACTION_SYSTEM_RULES,
    PHRASING_SYSTEM_RULES,
    build_extraction_prompt,
)


class GeminiProvider:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Provide a valid key or set NLU_PROVIDER=ollama."
            )
        self.client = genai.Client(api_key=key)
        self.model = "gemini-2.5-flash"

    def extract(
        self,
        transcript: str,
        known: Dict[str, Any],
        missing: List[str],
        correction: Optional[str] = None,
    ) -> ExtractOut:
        prompt = build_extraction_prompt(transcript, known, missing)
        if correction:
            prompt += f"\n\nPrevious extraction attempt failed validation: {correction}. Fix the output."

        config = types.GenerateContentConfig(
            system_instruction=EXTRACTION_SYSTEM_RULES,
            response_mime_type="application/json",
            response_schema=ExtractOut,
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=1024,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        if not response.text:
            raise ValueError("Empty response received from Gemini API.")

        return ExtractOut.model_validate_json(response.text)

    def phrase(self, prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=PHRASING_SYSTEM_RULES,
            temperature=0.5,
            max_output_tokens=256,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        return (response.text or "").strip()
