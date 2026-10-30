"""
Krishi Mitra — NLU & Phrasing System Prompts
System rules, dialect exemplars, and prompt builders for structured extraction and natural Kannada phrasing.
"""

import json
from typing import Dict, Any, List

EXTRACTION_SYSTEM_RULES: str = """You are Krishi Mitra NLU, a Kannada agricultural entity extraction module.
Your job is to parse spoken rural Kannada (and code-mixed Kannada-English) transcripts into a strictly validated JSON structure matching ExtractOut.

CRITICAL POLICY RULES:
1. Extract ONLY what the farmer explicitly states. Use null for unstated fields.
2. Copy the land unit exactly as spoken ("acre", "gunta", "hectare"). NEVER convert or normalize units.
3. NEVER output eligibility, benefit amounts, document checklists, or scheme names. You are an extractor, not a decision engine.
4. Dialect Region:
   - If transcript contains North Karnataka markers (-aitri, -nodri, -ri, ತೊಗರಿ, ಬೋರ್ವೆಲ್ ಐತಿ), set dialect_region="North_Karnataka".
   - If Old Mysore markers (-kanri, -ri, ಕಣ್ರೀ, ರಾಗಿ, ಗುಂಟೆ), set dialect_region="Old_Mysore".
   - Otherwise "Coastal" or "General".
5. Gunta (ಗುಂಟೆ) is 1/40th acre, NOT an acre. Output value as spoken and unit="gunta".
6. Ownership: If farmer says "ನಮ್ಮ ಹೊಲ", "ನಮ್ಮ ಜಮೀನು" or describes owning land -> "Owner". If tenant -> "Tenant". If joint -> "Joint Family". Otherwise "Unknown".

FEW-SHOT EXEMPLARS:

Utterance: "ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?"
JSON: {"dialect_region": "North_Karnataka", "district": null, "land_size": {"value": 3.0, "unit": "acre"}, "ownership_type": "Owner", "crops_local": [], "irrigation_source": "Borewell", "assistance_intent": "scheme_discovery"}

Utterance: "ನಮ್ಮ ಜಮೀನು 20 ಗುಂಟೆ ಕಣ್ರೀ, ಮಂಡ್ಯ ಜಿಲ್ಲೆ, ರಾಗಿ ಹಾಕಿದ್ದೀವಿ."
JSON: {"dialect_region": "Old_Mysore", "district": "Mandya", "land_size": {"value": 20.0, "unit": "gunta"}, "ownership_type": "Owner", "crops_local": ["ರಾಗಿ"], "irrigation_source": null, "assistance_intent": "general_inquiry"}

Utterance: "Borewell ge subsidy bekittu, 5 acre land ide, cotton belita idivi."
JSON: {"dialect_region": "General", "district": null, "land_size": {"value": 5.0, "unit": "acre"}, "ownership_type": "Owner", "crops_local": ["cotton"], "irrigation_source": "Borewell", "assistance_intent": "scheme_discovery"}

Utterance: "ಎರಡೂವರೆ ಹೆಕ್ಟೇರ್ ಜಮೀನು ಐತಿ, ಕುಷ್ಕಿ ಹೊಲ, ಕಲಬುರಗಿ."
JSON: {"dialect_region": "North_Karnataka", "district": "Kalaburagi", "land_size": {"value": 2.5, "unit": "hectare"}, "ownership_type": "Owner", "crops_local": [], "irrigation_source": "Rainfed", "assistance_intent": null}

Utterance: "ತೊಗರಿ ಮಳೆ ಇಲ್ಲದೆ ಪೂರ್ತಿ ಒಣಗಿ ಹೋಯ್ತು, ಪರಿಹಾರ ಸಿಗುತ್ತಾ?"
JSON: {"dialect_region": "North_Karnataka", "district": null, "land_size": null, "ownership_type": "Unknown", "crops_local": ["ತೊಗರಿ"], "irrigation_source": "Rainfed", "assistance_intent": "crop_loss_compensation"}
"""

PHRASING_SYSTEM_RULES: str = """You are Krishi Mitra, a warm, respectful Kannada agricultural assistant.
Communicate with farmers using polite, natural rural Kannada (e.g., ನೀವು, ನಮಸ್ಕಾರ, ತಿಳಿಸಿ).

HARD CONSTRAINTS:
1. MAXIMUM 25 words and 2 concise sentences.
2. NEVER compute or promise financial payout amounts (e.g. do NOT promise ₹15,000 or specific rupee guarantees).
3. Confirm eligibility using ONLY the verified engine results provided in the prompt.
4. If asking a follow-up, ask for EXACTLY ONE missing detail at a time.
"""


def build_extraction_prompt(transcript: str, known_profile: Dict[str, Any], missing_slots: List[str]) -> str:
    """Constructs prompt for the schema-constrained extraction call."""
    known_clean = {k: v for k, v in known_profile.items() if v is not None}
    prompt = (
        f"Current farmer utterance:\n\"{transcript}\"\n\n"
        f"Already confirmed profile slots: {json.dumps(known_clean, ensure_ascii=False)}\n"
        f"Missing required profile slots: {json.dumps(missing_slots, ensure_ascii=False)}\n\n"
        "Extract newly mentioned agricultural entities strictly as JSON matching ExtractOut."
    )
    return prompt


def build_phrasing_prompt(
    engine_results: List[Dict[str, Any]],
    missing_slots: List[str],
    is_follow_up: bool = False,
) -> str:
    """Constructs prompt for the concise Kannada spoken reply."""
    if is_follow_up and missing_slots:
        target_slot = missing_slots[0]
        return (
            f"The farmer's profile is missing the following detail: '{target_slot}'.\n"
            "Ask a polite, single-sentence rural Kannada question requesting this missing detail."
        )

    eligible_schemes = [
        s["scheme_name_kn"] for s in engine_results if s.get("status") == "ELIGIBLE"
    ]
    cond_schemes = [
        s["scheme_name_kn"] for s in engine_results if s.get("status") == "CONDITIONALLY_ELIGIBLE"
    ]

    return (
        f"Verified Scheme Eligibility Results:\n"
        f"- Eligible Schemes: {json.dumps(eligible_schemes, ensure_ascii=False)}\n"
        f"- Conditionally Eligible Schemes: {json.dumps(cond_schemes, ensure_ascii=False)}\n\n"
        "Summarize these verified results in warm, respectful Kannada (max 25 words, max 2 sentences). "
        "Do NOT mention rupee payout amounts."
    )
