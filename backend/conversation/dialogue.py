"""
Krishi Mitra — Dialogue Management & Response Synthesis
Orchestrates multi-turn slot filling, follow-up inquiry, deterministic scheme evaluation,
and safety-guarded concise Kannada response phrasing with template fallbacks.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from backend.rules_engine import SchemeEvaluator, FarmerProfile, EvaluationResult
from backend.nlu.extractor import NLUExtractor
from backend.nlu.prompts import build_phrasing_prompt
from backend.nlu.providers import NLUProvider
from backend.conversation.state import (
    ConversationState,
    merge_extraction,
    get_missing_slots,
    is_profile_complete,
    add_turn,
)

logger = logging.getLogger(__name__)

# Currency and payout patterns prohibited in phrasing
PAYOUT_REGEX = re.compile(r"₹\s*[\d,]+|ರೂ\.?\s*[\d,]+|\b\d+\s*ರೂಪಾಯಿ|\b\d+\s*ಸಾವಿರ")


class KannadaTemplates:
    SLOT_QUESTIONS: Dict[str, str] = {
        "land_acres": "ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಎಕರೆ ಅಥವಾ ಗುಂಟೆ ಜಮೀನು ಇದೆ ತಿಳಿಸಿ.",
        "crops": "ನಿಮ್ಮ ಹೊಲದಲ್ಲಿ ಯಾವ ಬೆಳೆಗಳನ್ನು ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ ತಿಳಿಸಿ.",
        "irrigation_type": "ನಿಮ್ಮ ಜಮೀನಿಗೆ ನೀರಾವರಿ ಸೌಲಭ್ಯ (ಬೋರ್ವೆಲ್, ಕಾಲುವೆ) ಇದೆಯೇ ಅಥವಾ ಮಳೆಯಾಶ್ರಿತವೇ?",
        "district": "ನಿಮ್ಮ ಜಿಲ್ಲೆ ಅಥವಾ ತಾಲೂಕು ಯಾವುದು ಎಂದು ತಿಳಿಸಿ.",
    }

    DEFAULT_FOLLOW_UP = "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಕೃಷಿ ವಿವರಗಳನ್ನು ಇನ್ನಷ್ಟು ಸ್ಪಷ್ಟವಾಗಿ ತಿಳಿಸಿ."

    @classmethod
    def get_slot_question(cls, slot: str) -> str:
        return cls.SLOT_QUESTIONS.get(slot, cls.DEFAULT_FOLLOW_UP)

    @classmethod
    def format_evaluation_summary(cls, results: List[EvaluationResult]) -> str:
        eligible = [r.scheme_name_kn for r in results if r.status == "ELIGIBLE"]
        if eligible:
            # Concise top-2 to guarantee strict brevity <= 20 words
            top_schemes = eligible[:2]
            names = ", ".join(top_schemes)
            more = " ಇತ್ಯಾದಿ" if len(eligible) > 2 else ""
            return f"ನಿಮ್ಮ ವಿವರಗಳ ಪ್ರಕಾರ {names}{more} ಯೋಜನೆಗೆ ನೀವು ಅರ್ಹರಾಗಿದ್ದೀರಿ. ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."

        cond = [r.scheme_name_kn for r in results if r.status == "CONDITIONALLY_ELIGIBLE"]
        if cond:
            names = ", ".join(cond[:2])
            return f"ನಿಮ್ಮ ವಿವರಗಳ ಪ್ರಕಾರ {names} ಯೋಜನೆಗೆ ಷರತ್ತುಬದ್ಧ ಅರ್ಹತೆ ಇದೆ."

        return "ನಿಮ್ಮ ವಿವರಗಳ ಪ್ರಕಾರ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಯೋಜನೆಗೆ ಪೂರ್ಣ ಅರ್ಹತೆ ಕಂಡುಬಂದಿಲ್ಲ."


class DialogueManager:
    def __init__(
        self,
        extractor: NLUExtractor,
        evaluator: Optional[SchemeEvaluator] = None,
        provider: Optional[NLUProvider] = None,
    ):
        self.extractor = extractor
        self.evaluator = evaluator or SchemeEvaluator()
        self.provider = provider or extractor.provider

    def select_follow_up_question(self, missing_slots: List[str]) -> str:
        """Selects proactive Kannada follow-up question for the first missing mandatory slot."""
        if not missing_slots:
            return ""
        return KannadaTemplates.get_slot_question(missing_slots[0])

    def phrase_response(
        self,
        results: List[EvaluationResult],
        missing_slots: List[str],
    ) -> str:
        """
        Phrases Kannada conversational reply.
        Enforces:
          1. Slot question if profile incomplete.
          2. LLM phrasing if complete.
          3. Hard length check (<= 25 words).
          4. Zero payout guarantee check.
          5. Fallback to deterministic template on failure.
        """
        if missing_slots:
            return self.select_follow_up_question(missing_slots)

        template_fallback = KannadaTemplates.format_evaluation_summary(results)

        try:
            results_dicts = [
                {
                    "scheme_id": r.scheme_id,
                    "scheme_name_kn": r.scheme_name_kn,
                    "status": r.status,
                }
                for r in results
            ]
            phrasing_prompt = build_phrasing_prompt(results_dicts, missing_slots, is_follow_up=False)
            llm_text = self.provider.phrase(phrasing_prompt)

            if not llm_text:
                return template_fallback

            # Guardrail 1: Payout check
            if PAYOUT_REGEX.search(llm_text):
                logger.warning("Phrasing violated payout guardrail. Falling back to template.")
                return template_fallback

            # Guardrail 2: Word count limit (<= 25 words)
            words = llm_text.strip().split()
            if len(words) > 25:
                logger.warning(f"Phrasing exceeded 25 words ({len(words)}). Falling back to template.")
                return template_fallback

            return llm_text

        except Exception as e:
            logger.error(f"Reply phrasing error: {e}. Using deterministic template.")
            return template_fallback

    def process_turn(
        self,
        state: ConversationState,
        user_utterance: str,
    ) -> Dict[str, Any]:
        """
        Full conversational turn:
        1. Extract & normalize entities from user utterance.
        2. Merge into conversation state with conflict quarantine.
        3. Determine missing slots.
        4. If complete, run deterministic rules engine.
        5. Synthesize brief Kannada spoken response.
        6. Update turn history.
        """
        extract, new_fields, warnings = self.extractor.process_turn(user_utterance, state)
        updated_state = merge_extraction(state, new_fields)
        missing = get_missing_slots(updated_state)

        evaluation_results: List[EvaluationResult] = []
        if is_profile_complete(updated_state):
            # Map confirmed fields to FarmerProfile
            prof = updated_state.confirmed_profile
            farmer_profile = FarmerProfile(
                district=prof.get("district", "General"),
                land_acres=prof.get("land_acres", 0.0),
                ownership=prof.get("ownership", "Owner"),
                crops=prof.get("crops", []),
                irrigation_type=prof.get("irrigation_type", "Rainfed"),
                has_water_source=prof.get("has_water_source", False),
            )
            evaluation_results = self.evaluator.evaluate_all(farmer_profile)

        reply_kn = self.phrase_response(evaluation_results, missing)

        # Update state turn history
        final_state = add_turn(updated_state, "user", user_utterance)
        final_state = add_turn(final_state, "assistant", reply_kn)

        return {
            "reply_kn": reply_kn,
            "evaluation_results": evaluation_results,
            "missing_slots": missing,
            "state": final_state,
            "warnings": warnings,
        }
