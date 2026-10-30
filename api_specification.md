# API Specification (API_SPEC)

Base URL: `/api/v1`

---

## 1. Session Management Endpoints

### `POST /api/v1/sessions`
Creates a new conversation session with an initialized empty `FarmerProfile`.

* **Request Body**:
    {
      "modality_mode": "PHASE1_TEXT",
      "preferred_dialect_hint": "AUTO"
    }
* **Response (`201 Created`)**:
    {
      "session_id": "sess_f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "greeting_spoken_kn": "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! ನಾನು ಕೃಷಿ ಮಿತ್ರ. ಸರ್ಕಾರದ ಕೃಷಿ ಯೋಜನೆಗಳ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಲು ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ನೀವು ಯಾವ ಜಿಲ್ಲೆಯವರು ಮತ್ತು ಏನು ಬೆಳೆ ಬೆಳೆಯುತ್ತೀರಿ ಎಂದು ಹೇಳುತ್ತೀರಾ?",
      "farmer_profile": {
        "location_district": null,
        "land_area_acres": null,
        "ownership_type": null,
        "crops": [],
        "season": null,
        "assistance_needs": []
      }
    }

---

## 2. Phase 1 & Hybrid Conversational Turn Endpoint

### `POST /api/v1/chat/turn`
Processes a farmer utterance (in Kannada script, Kanglish, or English code-mix), updates session slots, runs the deterministic rule engine across all 5 reference schemes, and returns the spoken-style Kannada response plus the full eligibility audit trail.

* **Request Body**:
    {
      "session_id": "sess_f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "user_input": "ನಮಸ್ಕಾರ ರೀ, ನಂದು ಧಾರವಾಡ ಜಿಲ್ಲೆ. 2 ಎಕರೆ 20 ಗುಂಟೆ ಸ್ವಂತ ಹೊಲ ಐತಿ. ಮುಂಗಾರಿಗೆ ತೊಗರಿ ಹಾಕೇನಿ. ಇನ್ಶೂರೆನ್ಸ್ ಮತ್ತೆ ಏನಾದ್ರೂ ಸಹಾಯಧನ ಸಿಗ್ತದಾ?",
      "input_source": "TEXT"
    }

* **Response (`200 OK`)**:
    {
      "turn_index": 1,
      "normalized_entities": {
        "location_district": "DHARWAD",
        "land_area_acres": 2.5,
        "raw_land_conversion": "2 Ekare + 20 Gunte = 2.5 Acres",
        "ownership_type": "OWNED",
        "season": "KHARIF",
        "crops": [{"crop_id": "PIGEON_PEA", "kannada_name": "ತೊಗರಿ"}],
        "assistance_needs": ["CROP_INSURANCE", "INCOME_SUPPORT"]
      },
      "spoken_response_kn": "ಧನ್ಯವಾದಗಳು ಯಜಮಾನರೇ. ಧಾರವಾಡ ಜಿಲ್ಲೆಯಲ್ಲಿ ನಿಮ್ಮ 2.5 ಎಕರೆ ಸ್ವಂತ ಜಮೀನಿನಲ್ಲಿ ಮುಂಗಾರು ತೊಗರಿ ಬೆಳೆಗೆ 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ'ಯಡಿ ಬೆಳೆ ವಿಮೆ ಸೌಲಭ್ಯ ಇದೆ. ಜೊತೆಗೆ 'ಪಿಎಂ-ಕಿಸಾನ್' ಯೋಜನೆಯಡಿ ವರ್ಷಕ್ಕೆ 6,000 ರೂಪಾಯಿ ಸಹಾಯಧನಕ್ಕೂ ನೀವು ಅರ್ಹರಾಗಬಹುದು. ಪಿಎಂ-ಕಿಸಾನ್ ಖಚಿತಪಡಿಸಲು ಒಂದು ಸಣ್ಣ ಪ್ರಶ್ನೆ: ನೀವು ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿಸುತ್ತೀರಾ ಅಥವಾ ಸರ್ಕಾರಿ ನೌಕರಿಯಲ್ಲಿದ್ದೀರಾ?",
      "dialogue_action": "RECOMMEND_AND_CLARIFY_EXCLUSION",
      "follow_up_slot_requested": "exclusion_flags.pays_income_tax",
      "eligibility_results": [
        {
          "scheme_id": "PMFBY",
          "scheme_name_kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ (PMFBY)",
          "is_synthetic": false,
          "status": "ELIGIBLE",
          "passed_rules": [
            "ಜಿಲ್ಲೆ: ಧಾರವಾಡ (ಅಧಿಸೂಚಿತ ಪ್ರದೇಶ)",
            "ಹಂಗಾಮು: ಮುಂಗಾರು (Kharif)",
            "ಬೆಳೆ: ತೊಗರಿ (ಅಧಿಸೂಚಿತ ಬೆಳೆ)"
          ],
          "failed_rules": [],
          "missing_slots": []
        },
        {
          "scheme_id": "PM_KISAN",
          "scheme_name_kn": "ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (PM-KISAN)",
          "is_synthetic": false,
          "status": "POTENTIALLY_ELIGIBLE_MISSING_INFO",
          "passed_rules": [
            "ಸ್ವಂತ ಕೃಷಿ ಭೂಮಿ ಹೊಂದಿದ್ದಾರೆ (2.5 ಎಕರೆ)"
          ],
          "failed_rules": [],
          "missing_slots": ["exclusion_flags.pays_income_tax"]
        }
      ],
      "latency_ms": 640
    }

---

## 3. Phase 2 Streaming Voice WebSocket Endpoint

### `WS /api/v1/voice/stream/{session_id}`
Full-duplex WebSocket connection for Phase 2 real-time voice interaction.

* **Client $\rightarrow$ Server Events**:
  * `audio.chunk`: Base64-encoded $16\text{ kHz}$ PCM audio frame.
  * `audio.speech_end`: Client VAD trigger indicating end of farmer utterance.
  * `audio.barge_in`: Immediate signal that the farmer started speaking while TTS was playing.
* **Server $\rightarrow$ Client Events**:
  * `asr.partial`: Live partial Kannada transcript as the farmer speaks.
  * `asr.final`: Final recognized Kannada utterance + normalized dialect tags.
  * `audit.update`: Immediate JSON push of updated `FarmerProfile` slots and `eligibility_results` ($< 20\text{ ms}$ after NLU).
  * `tts.audio_chunk`: Streamed audio frames of the spoken Kannada response with sentence-level sync markers.

---

## 4. Scheme Catalog & Direct Rule Simulator Endpoints

### `GET /api/v1/schemes`
Returns all 5 reference schemes, their deterministic rule definitions, document requirements, and real/synthetic classification.

### `POST /api/v1/schemes/evaluate-direct`
Stateless endpoint allowing developers or automated tests to pass any `FarmerProfile` JSON payload and inspect the exact deterministic rule output without invoking the LLM.