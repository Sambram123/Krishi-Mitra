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

---

## 5. Authentication & Authorization Endpoints

Krishi Mitra secures all core conversational endpoints using JWT Bearer authentication and rotating refresh tokens.

### `POST /api/auth/request-otp`
Generates and delivers a 6-digit OTP code to the farmer's mobile number.
* **Rate Limits**: Max 5 requests per 10 minutes per phone number; max 10 requests per IP.
* **Request Body**:
  ```json
  {
    "phone": "+919876543210"
  }
  ```
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "OTP sent successfully",
    "phone": "+91******3210"
  }
  ```

### `POST /api/auth/verify-otp`
Validates 6-digit OTP (5-minute lifetime, max 5 attempts), provisions or updates user account, and issues credentials.
* **Request Body**:
  ```json
  {
    "phone": "+919876543210",
    "otp": "123456",
    "name": "Basavaraj",
    "preferred_language": "kn"
  }
  ```
* **Response (`200 OK`)**:
  * Set-Cookie: `krishi_refresh_token=<opaque_token>; HttpOnly; Secure; SameSite=Lax; Path=/api/auth`
  * Body:
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "user": {
        "id": "c1f7b022-7f28-4e55-8732-cf12e4e1320f",
        "phone": "+919876543210",
        "name": "Basavaraj",
        "preferred_language": "kn",
        "role": "farmer"
      }
    }
    ```

### `POST /api/auth/refresh`
Rotates the refresh token and issues a fresh 15-minute access token. If a previously revoked refresh token is presented, the system detects compromise and automatically revokes all tokens within that token family.
* **Headers/Cookies**: Cookie `krishi_refresh_token`
* **Response (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### `POST /api/auth/logout`
Revokes active refresh token and invalidates the session cookie.
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "Logged out successfully"
  }
  ```

### `GET /api/auth/me`
Retrieves currently authenticated farmer profile.
* **Headers**: `Authorization: Bearer <access_token>`
* **Response (`200 OK`)**:
  ```json
  {
    "id": "c1f7b022-7f28-4e55-8732-cf12e4e1320f",
    "phone": "+919876543210",
    "name": "Basavaraj",
    "preferred_language": "kn",
    "role": "farmer"
  }
  ```

### `GET /api/admin/stats`
Admin-only monitoring and metrics endpoint.
* **Headers**: `Authorization: Bearer <admin_access_token>`
* **Response (`200 OK` / `403 Forbidden` for farmers)**:
  ```json
  {
    "total_users": 142,
    "active_refresh_tokens": 89,
    "admin_caller": "+919000000002"
  }
  ```

### Conversation Session IDOR Protection
Calls to `POST /api/chat` and `POST /api/voice-turn` require a valid `Authorization: Bearer <access_token>`. Sessions are bound to `user_id`. Any attempt to access or modify a session belonging to another user returns `403 Forbidden`.
### 5.2 Voice Privacy & Informed Consent Endpoints (DPDP 2023)

Every audio processing request requires active, unrevoked consent for the active policy version. If consent is absent, revoked, or outdated, `/api/voice-turn` returns `403 Forbidden` with error code `CONSENT_REQUIRED`.

#### `GET /api/consent/policy`
Returns the current versioned privacy policy text in Kannada and English.
* **Response (`200 OK`)**:
  ```json
  {
    "version": "1.0",
    "effective_date": "2026-10-31",
    "policy_name": "Krishi Mitra Voice & Data Privacy Consent Policy",
    "purposes": {
      "voice_recording": { ... },
      "save_history": { ... }
    }
  }
  ```

#### `POST /api/consent`
Records an explicit consent grant or preference update. Follows an append-only audit trail.
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "purpose": "voice_recording",
    "policy_version": "1.0",
    "granted": true,
    "save_history": false
  }
  ```
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "Consent recorded successfully",
    "voice_consent_active": true,
    "save_history": false
  }
  ```

#### `DELETE /api/consent/voice`
Revokes/withdraws voice recording consent immediately. Releases microphone tracks and appends an immutable revocation row to the audit trail.
* **Headers**: `Authorization: Bearer <access_token>`
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "Voice recording consent has been withdrawn successfully",
    "voice_consent_active": false
  }
  ```

#### `GET /api/me/consents`
Returns the caller's active consent status, current policy version, history-saving preference, and immutable audit trail. Strictly isolated to the authenticated user.
* **Headers**: `Authorization: Bearer <access_token>`
* **Response (`200 OK`)**:
  ```json
  {
    "user_id": "c1f7b022-7f28-4e55-8732-cf12e4e1320f",
    "voice_consent_active": true,
    "policy_version": "1.0",
    "save_history": false,
    "audit_trail": [
      {
        "id": "...",
        "purpose": "voice_recording",
        "policy_version": "1.0",
        "granted": true,
        "granted_at": "2026-10-31T05:30:00Z",
        "revoked_at": null
      }
    ]
  }
  ```

#### `PUT /api/me/history-preference`
Updates user opt-in preference for retaining conversation transcripts (default off).
* **Headers**: `Authorization: Bearer <access_token>`
* **Request Body**:
  ```json
  {
    "save_history": true
  }
  ```
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "save_history": true
  }
  ```

#### `DELETE /api/me/data`
DPDP Right to Erasure: Permanently purges user's conversation sessions, transcripts, and records consent revocation.
* **Headers**: `Authorization: Bearer <access_token>`
* **Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "message": "All user sessions, transcripts, and session data have been deleted.",
    "purged_sessions": 1,
    "voice_consent_active": false,
    "save_history": false
  }
  ```

#### Consent Gatekeeper (`require_voice_consent`) Error Contract
When calling `/api/voice-turn` without active consent for the current policy version:
* **Response (`403 Forbidden`)**:
  ```json
  {
    "detail": {
      "code": "CONSENT_REQUIRED",
      "error": "CONSENT_REQUIRED",
      "message": "Explicit consent for voice recording and processing is required.",
      "policy_version": "1.0"
    }
  }
  ```
