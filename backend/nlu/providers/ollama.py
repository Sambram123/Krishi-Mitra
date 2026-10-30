"""
Krishi Mitra — Ollama Local Fallback Provider
Uses local Ollama HTTP API (e.g. qwen2.5:7b-instruct) for offline development and free fallback.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from backend.nlu.schemas import ExtractOut
from backend.nlu.prompts import (
    EXTRACTION_SYSTEM_RULES,
    PHRASING_SYSTEM_RULES,
    build_extraction_prompt,
)


class OllamaProvider:
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    def extract(
        self,
        transcript: str,
        known: Dict[str, Any],
        missing: List[str],
        correction: Optional[str] = None,
    ) -> ExtractOut:
        prompt = build_extraction_prompt(transcript, known, missing)
        if correction:
            prompt += f"\n\nValidation error: {correction}. Output strict valid JSON."

        payload = {
            "model": self.model,
            "system": EXTRACTION_SYSTEM_RULES + "\nRespond with valid JSON only.",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
            },
        }

        try:
            resp = requests.post(f"{self.host}/api/generate", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data.get("response", "{}")
            return ExtractOut.model_validate_json(raw_text)
        except Exception as e:
            raise RuntimeError(f"Ollama local extraction failed: {str(e)}")

    def phrase(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "system": PHRASING_SYSTEM_RULES,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
            },
        }

        try:
            resp = requests.post(f"{self.host}/api/generate", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Ollama local phrasing failed: {str(e)}")
