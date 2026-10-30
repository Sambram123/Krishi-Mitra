"""
Unit tests for NLUExtractor orchestrator, retries, and online guardrails.
Uses mock providers to verify deterministic behavior, error recovery, and security invariants.
"""

import unittest
from unittest.mock import MagicMock
from pydantic import ValidationError

from backend.nlu.schemas import ExtractOut, LandSize
from backend.nlu.extractor import NLUExtractor, redact_pii
from backend.conversation.state import ConversationState


class MockProvider:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0

    def extract(self, transcript, known, missing, correction=None):
        self.call_count += 1
        if not self.responses:
            return ExtractOut()
        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def phrase(self, prompt):
        return "ನಮಸ್ಕಾರ, ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."


class TestNLUExtractor(unittest.TestCase):
    def setUp(self):
        self.state = ConversationState(session_id="test_session")

    def test_redact_pii_utility(self):
        text = "ನನ್ನ ಆಧಾರ್ ಸಂಖ್ಯೆ 1234 5678 9012 ಮತ್ತು ಫೋನ್ 9876543210"
        redacted = redact_pii(text)
        self.assertNotIn("1234 5678 9012", redacted)
        self.assertIn("[REDACTED_12_DIGIT_ID]", redacted)

    def test_successful_extraction_turn(self):
        expected_extract = ExtractOut(
            dialect_region="North_Karnataka",
            district="Kalaburagi",
            land_size=LandSize(value=3.0, unit="acre"),
            ownership_type="Owner",
            crops_local=["togari"],
            irrigation_source="Borewell",
            assistance_intent="scheme_discovery",
        )
        provider = MockProvider([expected_extract])
        extractor = NLUExtractor(provider=provider)

        transcript = "ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಕಲಬುರಗಿ, ತೊಗರಿ ಹಾಕಿದ್ದೇವೆ"
        extract, fields, warnings = extractor.process_turn(transcript, self.state)

        self.assertEqual(extract.land_size.value, 3.0)
        self.assertEqual(fields["land_acres"], 3.0)
        self.assertEqual(fields["crops"], ["Pigeon Pea (Togari)"])
        self.assertEqual(fields["irrigation_type"], "Borewell")
        self.assertTrue(fields["has_water_source"])
        self.assertEqual(len(warnings), 0)

    def test_retry_on_first_validation_failure(self):
        # First call fails with ValueError, second succeeds
        valid_extract = ExtractOut(
            land_size=LandSize(value=2.0, unit="acre"),
        )
        provider = MockProvider([ValueError("Invalid JSON from LLM"), valid_extract])
        extractor = NLUExtractor(provider=provider)

        res = extractor.extract_with_retry("2 acres", {}, ["land_acres"])
        self.assertEqual(res.land_size.value, 2.0)
        self.assertEqual(provider.call_count, 2)

    def test_both_retries_fail_returns_empty_extract(self):
        provider = MockProvider([ValueError("Error 1"), ValueError("Error 2")])
        extractor = NLUExtractor(provider=provider)

        res = extractor.extract_with_retry("sample", {}, [])
        self.assertIsInstance(res, ExtractOut)
        self.assertIsNone(res.land_size)
        self.assertEqual(provider.call_count, 2)

    def test_guardrail_unit_sanity_rejects_excessive_acres(self):
        insane_extract = ExtractOut(
            land_size=LandSize(value=500.0, unit="acre"),
        )
        provider = MockProvider([insane_extract])
        extractor = NLUExtractor(provider=provider)

        extract, fields, warnings = extractor.process_turn("500 acres", self.state)
        self.assertIsNone(extract.land_size)
        self.assertNotIn("land_acres", fields)
        self.assertTrue(any("UNIT_INSANE" in w for w in warnings))

    def test_guardrail_evidence_check_flags_ungrounded_district(self):
        ungrounded_extract = ExtractOut(
            district="Dharwad",
        )
        provider = MockProvider([ungrounded_extract])
        extractor = NLUExtractor(provider=provider)

        # Transcript does not mention Dharwad
        extract, fields, warnings = extractor.process_turn("ನಮ್ಮ ಹೊಲ 2 ಎಕರೆ", self.state)
        self.assertTrue(any("UNGROUNDED_SLOT" in w for w in warnings))

    def test_guardrail_pii_detection(self):
        normal_extract = ExtractOut(
            land_size=LandSize(value=4.0, unit="acre"),
        )
        provider = MockProvider([normal_extract])
        extractor = NLUExtractor(provider=provider)

        transcript = "ನನ್ನ ಆಧಾರ್ 123456789012, 4 ಎಕರೆ ಹೊಲ ಇದೆ"
        extract, fields, warnings = extractor.process_turn(transcript, self.state)
        self.assertTrue(any("PII_DETECTED" in w for w in warnings))

    def test_gunta_conversion_integration(self):
        gunta_extract = ExtractOut(
            land_size=LandSize(value=40.0, unit="gunta"),
        )
        provider = MockProvider([gunta_extract])
        extractor = NLUExtractor(provider=provider)

        extract, fields, warnings = extractor.process_turn("40 ಗುಂಟೆ", self.state)
        self.assertEqual(fields["land_acres"], 1.0)

    def test_crop_canonicalization_integration(self):
        crop_extract = ExtractOut(
            crops_local=["ಜೋಳ", "ಕಬ್ಬು"],
        )
        provider = MockProvider([crop_extract])
        extractor = NLUExtractor(provider=provider)

        extract, fields, warnings = extractor.process_turn("ಜೋಳ ಕಬ್ಬು", self.state)
        self.assertEqual(fields["crops"], ["Jowar", "Sugarcane"])

    def test_guardrail_eligibility_firewall_blocks_leak(self):
        # A mock model output attempting to inject an extra leak field
        class LeakedExtract(ExtractOut):
            eligible: bool = True

        leaked = LeakedExtract(
            land_size=LandSize(value=3.0, unit="acre")
        )
        extractor = NLUExtractor(provider=MockProvider())
        cleaned, warnings = extractor.apply_guardrails(leaked, "3 acres")
        self.assertIsNone(cleaned.land_size)
        self.assertTrue(any("FIREWALL_BLOCKED" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
