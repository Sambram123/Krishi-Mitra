"""
Integration tests for DialogueManager, Guardrails, and CLI Benchmark validation.
Verifies multi-turn slot filling, brevity clamping, payout redaction, and CLI-01 benchmark execution.
"""

import unittest
from unittest.mock import MagicMock

from backend.rules_engine import SchemeEvaluator, FarmerProfile
from backend.nlu.schemas import ExtractOut, LandSize
from backend.nlu.extractor import NLUExtractor
from backend.conversation.state import ConversationState
from backend.conversation.dialogue import DialogueManager, KannadaTemplates
from cli_chat_prototype import run_benchmark_test


class MockDialogueProvider:
    def __init__(self, extract_responses=None, phrase_responses=None):
        self.extract_responses = extract_responses or []
        self.phrase_responses = phrase_responses or []

    def extract(self, transcript, known, missing, correction=None):
        if self.extract_responses:
            return self.extract_responses.pop(0)
        return ExtractOut()

    def phrase(self, prompt):
        if self.phrase_responses:
            return self.phrase_responses.pop(0)
        return "ನಿಮ್ಮ ವಿವರಗಳು ಪರಿಶೀಲನೆಯಾಗಿವೆ, ಫಲಿತಾಂಶ ಗಮನಿಸಿ."


class TestDialogueAndCLI(unittest.TestCase):
    def setUp(self):
        self.evaluator = SchemeEvaluator()
        self.state = ConversationState(session_id="dialogue_test_session")

    def test_cli_01_benchmark_test_function(self):
        """Verifies the CLI-01 acceptance test runner succeeds."""
        success = run_benchmark_test()
        self.assertTrue(success)

    def test_multi_turn_proactive_follow_up(self):
        """Turn 1 gives land only -> manager asks for crops. Turn 2 gives crops/district -> completes."""
        turn1_extract = ExtractOut(
            land_size=LandSize(value=3.0, unit="acre"),
            ownership_type="Owner",
        )
        turn2_extract = ExtractOut(
            crops_local=["ragi"],
            district="Mandya",
            irrigation_source="Rainfed",
        )

        provider = MockDialogueProvider(
            extract_responses=[turn1_extract, turn2_extract],
            phrase_responses=["ಧನ್ಯವಾದಗಳು, ನೀವು ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಅರ್ಹರಾಗಿದ್ದೀರಿ."],
        )
        extractor = NLUExtractor(provider=provider)
        dialogue = DialogueManager(extractor=extractor, evaluator=self.evaluator, provider=provider)

        # Turn 1
        res1 = dialogue.process_turn(self.state, "ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ")
        self.assertEqual(len(res1["evaluation_results"]), 0)
        self.assertIn("crops", res1["missing_slots"])
        self.assertEqual(res1["reply_kn"], KannadaTemplates.SLOT_QUESTIONS["crops"])

        # Turn 2
        res2 = dialogue.process_turn(res1["state"], "ಮಂಡ್ಯ ಜಿಲ್ಲೆ, ರಾಗಿ ಬೆಳೆದಿದ್ದೇವೆ, ಮಳೆಯಾಶ್ರಿತ")
        self.assertEqual(len(res2["missing_slots"]), 0)
        self.assertGreater(len(res2["evaluation_results"]), 0)
        eligible_ids = [r.scheme_id for r in res2["evaluation_results"] if r.status == "ELIGIBLE"]
        self.assertIn("pm_kisan", eligible_ids)

    def test_payout_guardrail_triggers_fallback(self):
        """When LLM attempts to promise a rupee payout, dialogue manager reverts to template."""
        complete_extract = ExtractOut(
            district="Kalaburagi",
            land_size=LandSize(value=3.0, unit="acre"),
            ownership_type="Owner",
            crops_local=["togari"],
            irrigation_source="Rainfed",
        )
        # LLM attempts to promise ₹15,000 compensation
        bad_llm_phrase = "ನಿಮಗೆ PMFBY ಅಡಿಯಲ್ಲಿ ₹15,000 ಪರಿಹಾರ ಖಚಿತವಾಗಿ ಸಿಗಲಿದೆ."

        provider = MockDialogueProvider(
            extract_responses=[complete_extract],
            phrase_responses=[bad_llm_phrase],
        )
        extractor = NLUExtractor(provider=provider)
        dialogue = DialogueManager(extractor=extractor, evaluator=self.evaluator, provider=provider)

        res = dialogue.process_turn(self.state, "ಕಲಬುರಗಿ 3 ಎಕರೆ ತೊಗರಿ ಒಣಭೂಮಿ")
        # Assert the response does NOT contain ₹15,000 and falls back to template
        self.assertNotIn("₹15,000", res["reply_kn"])
        self.assertIn("ಅರ್ಹರಾಗಿದ್ದೀರಿ", res["reply_kn"])

    def test_brevity_guardrail_triggers_fallback(self):
        """When LLM response exceeds 25 words, dialogue manager reverts to template."""
        complete_extract = ExtractOut(
            district="Belagavi",
            land_size=LandSize(value=2.0, unit="acre"),
            ownership_type="Owner",
            crops_local=["sugarcane"],
            irrigation_source="Borewell",
        )
        # 30-word long reply
        long_llm_phrase = " " .join(["ನಮಸ್ಕಾರ"] * 30)

        provider = MockDialogueProvider(
            extract_responses=[complete_extract],
            phrase_responses=[long_llm_phrase],
        )
        extractor = NLUExtractor(provider=provider)
        dialogue = DialogueManager(extractor=extractor, evaluator=self.evaluator, provider=provider)

        res = dialogue.process_turn(self.state, "ಬೆಳಗಾವಿ 2 ಎಕರೆ ಕಬ್ಬು ಬೋರ್ವೆಲ್")
        # Template response is short
        words = res["reply_kn"].split()
        self.assertLessEqual(len(words), 25)

    def test_template_fallback_on_provider_exception(self):
        """When provider phrase raises an error, template is safely returned."""
        complete_extract = ExtractOut(
            district="Mandya",
            land_size=LandSize(value=2.0, unit="acre"),
            ownership_type="Owner",
            crops_local=["ragi"],
            irrigation_source="Rainfed",
        )

        provider = MockDialogueProvider(
            extract_responses=[complete_extract],
            phrase_responses=[RuntimeError("API Network Timeout")],
        )
        extractor = NLUExtractor(provider=provider)
        dialogue = DialogueManager(extractor=extractor, evaluator=self.evaluator, provider=provider)

        res = dialogue.process_turn(self.state, "ಮಂಡ್ಯ 2 ಎಕರೆ ರಾಗಿ")
        self.assertIn("ಅರ್ಹರಾಗಿದ್ದೀರಿ", res["reply_kn"])


if __name__ == "__main__":
    unittest.main()
