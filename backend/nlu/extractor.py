"""
Krishi Mitra — NLU Extraction Orchestrator with Guardrails & Retries
Orchestrates schema extraction, validation retry loop, online guardrails
(eligibility firewall, evidence check, unit sanity, PII redaction), and failover.
"""

import os
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError

from backend.nlu.schemas import ExtractOut
from backend.nlu.normalize import (
    normalize_land_size,
    is_land_size_sane,
    check_district_evidence,
    extraction_to_farmer_profile_fields,
)
from backend.nlu.providers import get_provider, NLUProvider
from backend.conversation.state import ConversationState, get_missing_slots

logger = logging.getLogger(__name__)

# PII pattern: 12-digit continuous or 4-digit grouped numbers (Aadhaar / Bank Accounts)
PII_REGEX = re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b|\b\d{12}\b")

# Leaked eligibility keys blocked by Eligibility Firewall
FORBIDDEN_LEAK_KEYS = {
    "eligible",
    "eligibility",
    "status",
    "benefit",
    "benefit_amount",
    "scheme",
    "schemes",
    "scheme_id",
    "required_documents",
    "documents",
}


def redact_pii(text: str) -> str:
    """Redacts 12-digit Aadhaar/account patterns for DPDP compliance."""
    return PII_REGEX.sub("[REDACTED_12_DIGIT_ID]", text)


class NLUExtractor:
    def __init__(self, provider: Optional[NLUProvider] = None, provider_name: Optional[str] = None):
        if provider:
            self.provider = provider
        else:
            p_name = provider_name or os.getenv("NLU_PROVIDER", "gemini")
            self.provider = get_provider(p_name)
        self.consecutive_failures = 0

    def extract_with_retry(
        self,
        transcript: str,
        known_profile: Dict[str, Any],
        missing_slots: List[str],
    ) -> ExtractOut:
        """
        Attempts extraction with one corrective retry on validation failure.
        Falls back to a safe empty ExtractOut if both attempts fail.
        """
        try:
            res = self.provider.extract(transcript, known_profile, missing_slots)
            self.consecutive_failures = 0
            return res
        except (ValidationError, ValueError) as err:
            logger.warning(f"Initial extraction validation failed: {err}. Retrying once...")
            try:
                res = self.provider.extract(
                    transcript,
                    known_profile,
                    missing_slots,
                    correction=str(err),
                )
                self.consecutive_failures = 0
                return res
            except Exception as retry_err:
                logger.error(f"Secondary extraction retry failed: {retry_err}. Falling back to empty ExtractOut.")
                self.consecutive_failures += 1
                return ExtractOut()
        except Exception as e:
            logger.error(f"Provider extraction error: {e}. Falling back to empty ExtractOut.")
            self.consecutive_failures += 1
            return ExtractOut()

    def apply_guardrails(self, extract: ExtractOut, transcript: str) -> Tuple[ExtractOut, List[str]]:
        """
        Applies online guardrails:
          1. Eligibility Firewall
          2. Evidence Grounding Check
          3. Land Unit Sanity Check
          4. PII Redaction Detection
        """
        warnings: List[str] = []

        # 1. PII Check
        if PII_REGEX.search(transcript):
            warnings.append("PII_DETECTED: 12-digit pattern redacted from transcripts and logs.")

        # 2. Eligibility Firewall (Check raw model dump for forbidden keys)
        raw_dump = extract.model_dump()
        for forbidden in FORBIDDEN_LEAK_KEYS:
            if forbidden in raw_dump:
                warnings.append(f"FIREWALL_BLOCKED: Forbidden key '{forbidden}' detected in extraction. Clearing extract.")
                return ExtractOut(), warnings

        # 3. Land Unit Sanity Check
        cleaned_extract = extract.model_copy()
        if cleaned_extract.land_size:
            try:
                acres = normalize_land_size(cleaned_extract.land_size)
                if not is_land_size_sane(acres):
                    warnings.append(f"UNIT_INSANE: Extracted land {acres} acres is outside [0.01, 100.0]. Discarding.")
                    cleaned_extract.land_size = None
            except Exception as e:
                warnings.append(f"UNIT_ERROR: Failed to normalize land size: {e}")
                cleaned_extract.land_size = None

        # 4. Evidence Grounding Check (fuzzy presence in transcript)
        if cleaned_extract.district:
            if not check_district_evidence(cleaned_extract.district, transcript):
                warnings.append(f"UNGROUNDED_SLOT: District '{cleaned_extract.district}' has no direct evidence in transcript.")

        return cleaned_extract, warnings

    def process_turn(
        self,
        transcript: str,
        state: ConversationState,
    ) -> Tuple[ExtractOut, Dict[str, Any], List[str]]:
        """
        Full NLU turn processing:
        Extracts -> Applies Guardrails -> Normalizes fields for profile merging.
        """
        missing = get_missing_slots(state)
        raw_extract = self.extract_with_retry(transcript, state.confirmed_profile, missing)
        validated_extract, warnings = self.apply_guardrails(raw_extract, transcript)
        profile_fields = extraction_to_farmer_profile_fields(validated_extract)
        return validated_extract, profile_fields, warnings
