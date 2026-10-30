import base64
import httpx
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.web_server import (
    APIError,
    _deterministic_extract,
    _eligibility_results,
    _is_scheme_query,
    _missing_chat_slots,
    _sarvam_request,
    handle_chat,
    handle_voice_turn,
    merge_profile,
    normalize_profile_patch,
)


class TestWebServer(unittest.TestCase):
    def test_extracts_kannada_and_english_farmer_facts(self):
        profile = _deterministic_extract(
            "ನಮಸ್ಕಾರ, ಕಲಬುರಗಿ ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ತೊಗರಿ ಬೆಳೆದಿದ್ದೇನೆ, ಬರಗಾಲ."
        )
        self.assertEqual(profile["district"], "Kalaburagi")
        self.assertEqual(profile["land_acres"], 3.0)
        self.assertEqual(profile["crops"], ["Pigeon Pea (Togari)"])
        self.assertEqual(profile["risk_type"], "Drought")

    def test_profile_merge_preserves_known_facts_and_ignores_null(self):
        profile = merge_profile(
            {"district": "Mandya", "land_acres": 2.5},
            {"district": None, "crops": ["Sugarcane"]},
        )
        self.assertEqual(profile["district"], "Mandya")
        self.assertEqual(profile["land_acres"], 2.5)
        self.assertEqual(profile["crops"], ["Sugarcane"])

    def test_rejects_non_boolean_exclusion_answers(self):
        with self.assertRaises(APIError):
            normalize_profile_patch({"is_income_tax_payee": "no"})

    def test_voice_turn_runs_stt_chat_and_tts_without_exposing_provider_key(self):
        transcribe = Mock(return_value=SimpleNamespace(
            transcript="I have 3 acres in Mandya and grow sugarcane.",
            language_code="en-IN",
        ))
        completions = Mock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="I can help you review irrigation support options."
            ))]
        ))
        synthesize = Mock(return_value=SimpleNamespace(audios=["d2F2"]))
        fake_client = SimpleNamespace(
            speech_to_text=SimpleNamespace(transcribe=transcribe),
            text_to_speech=SimpleNamespace(convert=synthesize),
        )
        groq_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=completions)),
        )
        audio = base64.b64encode(b"sample webm audio").decode("ascii")
        with patch.dict("os.environ", {
            "SARVAM_API_KEY": "configured-key",
            "GROQ_API_KEY": "groq-configured-key",
        }, clear=True):
            with patch("backend.web_server.SarvamAI", return_value=fake_client) as client_factory:
                with patch("backend.web_server.Groq", return_value=groq_client):
                    with self.assertLogs("krishi_mitra", level="INFO") as captured_logs:
                        result = handle_voice_turn({
                            "audio": audio,
                            "mime_type": "audio/webm",
                            "language": "en",
                            "history": [
                                {"role": "user", "content": "I want help with my farm."},
                                {"role": "assistant", "content": "What crop are you growing?"},
                            ],
                            "profile": {},
                        }, request_id="test-request")

        client_factory.assert_called_once_with(
            api_subscription_key="configured-key",
            timeout=15,
        )
        self.assertEqual(transcribe.call_args.kwargs["model"], "saaras:v4")
        self.assertEqual(transcribe.call_args.kwargs["language_code"], "unknown")
        self.assertNotIn("mode", transcribe.call_args.kwargs)
        self.assertEqual(completions.call_args.kwargs["model"], "openai/gpt-oss-120b")
        self.assertEqual(
            completions.call_args.kwargs["messages"][1:3],
            [
                {"role": "user", "content": "I want help with my farm."},
                {"role": "assistant", "content": "What crop are you growing?"},
            ],
        )
        self.assertEqual(synthesize.call_args.kwargs["model"], "bulbul:v4-flash")
        self.assertEqual(synthesize.call_args.kwargs["speaker"], "simran_en_conversation")
        self.assertEqual(result["transcript"], "I have 3 acres in Mandya and grow sugarcane.")
        self.assertEqual(result["audio"], "d2F2")
        self.assertEqual(result["profile"]["district"], "Mandya")
        self.assertEqual(len(result["evaluations"]), 5)
        self.assertFalse(result["show_evaluations"])
        self.assertNotIn("configured-key", json.dumps(result))
        logs = "\n".join(captured_logs.output)
        self.assertIn("request_id=test-request", logs)
        self.assertNotIn("I have 3 acres in Mandya", logs)
        self.assertNotIn("configured-key", logs)

    def test_sarvam_request_reports_provider_timeout(self):
        request = Mock(side_effect=httpx.TimeoutException("timed out"))
        with self.assertRaisesRegex(APIError, "timed out"):
            _sarvam_request(
                "timeout-request",
                "speech recognition",
                request,
            )

    def test_voice_turn_reports_empty_transcript_and_uses_language_for_error(self):
        transcribe = Mock(return_value=SimpleNamespace(transcript="", language_code=None))
        fake_client = SimpleNamespace(
            speech_to_text=SimpleNamespace(transcribe=transcribe),
            chat=SimpleNamespace(completions=Mock()),
            text_to_speech=SimpleNamespace(convert=Mock()),
        )
        audio = base64.b64encode(b"sample webm audio").decode("ascii")
        with patch.dict("os.environ", {"SARVAM_API_KEY": "configured-key"}, clear=True):
            with patch("backend.web_server.SarvamAI", return_value=fake_client):
                with self.assertLogs("krishi_mitra", level="INFO") as captured_logs:
                    with self.assertRaisesRegex(APIError, "No speech was recognized"):
                        handle_voice_turn({
                            "audio": audio,
                            "mime_type": "audio/webm",
                            "language": "en",
                            "recording_duration_ms": 25_100,
                            "profile": {},
                        }, request_id="empty-transcript")

        self.assertEqual(transcribe.call_args.kwargs["language_code"], "unknown")
        self.assertIn("status=empty_transcript", "\n".join(captured_logs.output))
        self.assertIn("recording_duration_ms=25100", "\n".join(captured_logs.output))
        fake_client.chat.completions.assert_not_called()
        fake_client.text_to_speech.convert.assert_not_called()

    def test_voice_turn_detects_kannada_and_replies_in_kannada(self):
        transcribe = Mock(return_value=SimpleNamespace(
            transcript="ನನ್ನ ಟೊಮೇಟೊ ಗಿಡದ ಎಲೆಗಳು ಹಳದಿಯಾಗಿವೆ.",
            language_code="kn-IN",
        ))
        completions = Mock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="ನಿಮ್ಮ ಗಿಡಗಳಿಗೆ ನೀರು ಸರಿಯಾಗಿ ಸಿಗುತ್ತಿದೆಯೇ?"
            ))]
        ))
        synthesize = Mock(return_value=SimpleNamespace(audios=["d2F2"]))
        fake_client = SimpleNamespace(
            speech_to_text=SimpleNamespace(transcribe=transcribe),
            chat=SimpleNamespace(completions=completions),
            text_to_speech=SimpleNamespace(convert=synthesize),
        )
        audio = base64.b64encode(b"sample webm audio").decode("ascii")
        with patch.dict("os.environ", {
            "SARVAM_API_KEY": "configured-key",
            "GROQ_API_KEY": "groq-configured-key",
        }, clear=True):
            with patch("backend.web_server.SarvamAI", return_value=fake_client):
                with patch("backend.web_server.Groq", return_value=SimpleNamespace(
                    chat=SimpleNamespace(
                        completions=SimpleNamespace(create=completions),
                    ),
                )):
                    result = handle_voice_turn({
                        "audio": audio,
                        "mime_type": "audio/webm",
                        "language": "en",
                        "profile": {},
                    })

        self.assertEqual(transcribe.call_args.kwargs["language_code"], "unknown")
        self.assertEqual(result["detected_language"], "kn-IN")
        self.assertIn("Kannada", completions.call_args.kwargs["messages"][0]["content"])
        self.assertEqual(synthesize.call_args.kwargs["language_code"], "kn-IN")
        self.assertEqual(synthesize.call_args.kwargs["speaker"], "chaitra_kn_conversation")

    def test_voice_turn_requires_sarvam_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(APIError, "SARVAM_API_KEY"):
                handle_voice_turn({})

    def test_voice_turn_rejects_unsupported_audio_format(self):
        with patch.dict("os.environ", {"SARVAM_API_KEY": "configured-key"}, clear=True):
            with self.assertRaisesRegex(APIError, "WebM, Ogg, MP4, or WAV"):
                handle_voice_turn({
                    "audio": base64.b64encode(b"audio").decode("ascii"),
                    "mime_type": "audio/aac",
                })

    def test_missing_government_information_is_conditional_not_approval(self):
        results = {
            result["scheme_id"]: result
            for result in _eligibility_results({
                "land_acres": 3,
                "district": "Mandya",
                "crops": ["Sugarcane"],
            })
        }
        self.assertEqual(results["pm_kisan"]["status"], "CONDITIONALLY_ELIGIBLE")
        self.assertIn("is_income_tax_payee", results["pm_kisan"]["missing_information"])
        self.assertEqual(results["pmfby"]["status"], "CONDITIONALLY_ELIGIBLE")
        self.assertIn("disclaimer_en", results["pm_kisan"])

    def test_api_returns_only_source_linked_real_programs_and_nonapproval_statuses(self):
        results = _eligibility_results({"land_acres": 2, "irrigation_type": "Borewell"})
        self.assertEqual(len(results), 5)
        self.assertTrue(all(not result["is_demo"] for result in results))
        indexed = {result["scheme_id"]: result for result in results}
        self.assertEqual(indexed["pmksy_pdmc"]["status"], "CONDITIONALLY_ELIGIBLE")
        self.assertEqual(indexed["smam"]["status"], "CONDITIONALLY_ELIGIBLE")
        self.assertEqual(indexed["soil_health_card"]["status"], "INFORMATIONAL")
        for result in results:
            self.assertTrue(result["sources"])
            self.assertEqual(result["last_researched"], "2026-10-30")
        self.assertIn("not a", indexed["soil_health_card"]["benefit_summary_en"])

    def test_known_pm_kisan_exclusion_is_ineligible(self):
        results = _eligibility_results({
            "land_acres": 3,
            "ownership": "Owner",
            "is_income_tax_payee": True,
            "is_institutional_landholder": False,
            "is_constitutional_post_holder": False,
            "is_government_employee": False,
        })
        pm_kisan = next(result for result in results if result["scheme_id"] == "pm_kisan")
        self.assertEqual(pm_kisan["status"], "INELIGIBLE")

    def test_complete_positive_pm_kisan_screen_still_requires_official_verification(self):
        results = _eligibility_results({
            "land_acres": 3,
            "ownership": "Owner",
            "is_income_tax_payee": False,
            "is_institutional_landholder": False,
            "is_constitutional_post_holder": False,
            "is_government_employee": False,
        })
        pm_kisan = next(result for result in results if result["scheme_id"] == "pm_kisan")
        self.assertEqual(pm_kisan["status"], "CONDITIONALLY_ELIGIBLE")
        self.assertIn("Official land records", pm_kisan["benefit_summary_en"])

    def test_chat_returns_rule_evaluations_and_local_fallback_mode_without_key(self):
        with patch.dict("os.environ", {"SARVAM_API_KEY": ""}, clear=True):
            response = handle_chat({
                "message": "I have 3 acres in Mandya and grow sugarcane.",
                "language": "en",
                "profile": {},
            })
        self.assertEqual(response["profile"]["land_acres"], 3.0)
        self.assertTrue(response["evaluations"])
        self.assertIn("Local assistant", response["model_mode"])
        self.assertTrue(response["reply"])

    def test_chat_followups_match_the_scheme_the_farmer_asks_about(self):
        with patch.dict("os.environ", {"SARVAM_API_KEY": ""}, clear=True):
            response = handle_chat({
                "message": "Am I eligible for drip irrigation?",
                "language": "en",
                "profile": {},
            })
        self.assertIn("district", response["reply"])
        self.assertNotIn("official", response["reply"].lower())
        self.assertTrue(response["show_evaluations"])

    def test_chat_uses_natural_groq_reply_and_recent_conversation(self):
        completions = Mock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="For sugarcane, drip irrigation can help use water efficiently. Which district is your farm in?"
            ))]
        ))
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=completions)),
        )
        history = [
            {"role": "user", "content": "I grow sugarcane."},
            {"role": "assistant", "content": "Which district is your farm in?"},
        ]
        with patch.dict("os.environ", {"GROQ_API_KEY": "configured-key"}, clear=True):
            with patch("backend.web_server.Groq", return_value=fake_client):
                response = handle_chat({
                    "message": "Mandya.",
                    "language": "en",
                    "profile": {"crops": ["Sugarcane"]},
                    "history": history,
                }, request_id="natural-chat")

        self.assertEqual(response["reply"], completions.return_value.choices[0].message.content)
        self.assertEqual(response["model_mode"], "Groq openai/gpt-oss-120b")
        messages = completions.call_args.kwargs["messages"]
        self.assertEqual(messages[1:3], history)
        self.assertIn("Mandya.", messages[-1]["content"])
        self.assertIn("Answer the farmer's actual question first", messages[0]["content"])
        self.assertFalse(response["show_evaluations"])
        self.assertIn("Do not introduce government schemes", messages[-1]["content"])
        self.assertTrue(response["evaluations"])

    def test_general_chat_does_not_force_scheme_intake_questions(self):
        self.assertEqual(_missing_chat_slots(
            {"district": None, "land_acres": None, "crops": []},
            "How can I make compost at home?",
        ), [])
        self.assertFalse(_is_scheme_query("How can I make compost at home?"))
        self.assertFalse(_is_scheme_query("When should I apply fertilizer to tomatoes?"))
        self.assertTrue(_is_scheme_query("Can I get a subsidy for drip irrigation?"))
        self.assertTrue(_is_scheme_query("How do I apply for PM-KISAN?"))
        self.assertTrue(_is_scheme_query("ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಅರ್ಹತೆ ಇದೆಯೇ?"))

    def test_kannada_chat_generates_sarvam_speech(self):
        completions = Mock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="ನಮಸ್ಕಾರ, ನಿಮ್ಮ ಬೆಳೆ ಯಾವುದು?"
            ))]
        ))
        synthesize = Mock(return_value=SimpleNamespace(audios=["a2FubmFkYQ=="]))
        groq_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=completions)),
        )
        sarvam_client = SimpleNamespace(
            text_to_speech=SimpleNamespace(convert=synthesize),
        )
        with patch.dict("os.environ", {
            "GROQ_API_KEY": "groq-configured-key",
            "SARVAM_API_KEY": "sarvam-configured-key",
        }, clear=True):
            with patch("backend.web_server.Groq", return_value=groq_client):
                with patch("backend.web_server.SarvamAI", return_value=sarvam_client):
                    response = handle_chat({
                        "message": "ನಮಸ್ಕಾರ",
                        "language": "kn",
                        "profile": {},
                    }, request_id="kannada-chat")

        self.assertEqual(response["reply"], "ನಮಸ್ಕಾರ, ನಿಮ್ಮ ಬೆಳೆ ಯಾವುದು?")
        self.assertEqual(response["audio"], "a2FubmFkYQ==")
        self.assertEqual(response["mime_type"], "audio/wav")
        self.assertIn("Kannada speech", response["model_mode"])
        self.assertEqual(synthesize.call_args.kwargs["language_code"], "kn-IN")
        self.assertEqual(synthesize.call_args.kwargs["speaker"], "chaitra_kn_conversation")

    def test_chat_falls_back_when_groq_is_unavailable(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "configured-key"}, clear=True):
            with patch(
                "backend.web_server.Groq",
                side_effect=APIError(503, "Groq is unavailable."),
            ):
                with self.assertLogs("krishi_mitra", level="WARNING") as captured_logs:
                    response = handle_chat({
                        "message": "I want help with my farm.",
                        "language": "en",
                        "profile": {},
                    })

        self.assertIn("Local assistant", response["model_mode"])
        self.assertIn("Groq unavailable", response["model_mode"])
        self.assertTrue(response["evaluations"])
        self.assertIn("status=local_fallback", "\n".join(captured_logs.output))


if __name__ == "__main__":
    unittest.main()
