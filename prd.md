# Product Requirements Document (PRD) — Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)

---

## 1. Executive Summary & Prototyping Strategy

### 1.1 Progressive 3-Stage Delivery Model
To ensure bulletproof reliability and zero wasted effort during the hackathon, development is structured into three progressive prototypes:

```
[ Stage 1: Text-to-Text Prototype ]
   ├── Kannada Text Input
   ├── Dialect & Jargon Slot Extraction (Gemini Flash Free Tier / Local LLM)
   ├── Deterministic Scheme Evaluation (5 Reference Schemes)
   └── Auditable Text Recommendations & Follow-up Questions

[ Stage 2: Voice Output Prototype ]
   ├── Text Input -> Dialogue Logic -> Spoken Kannada Voice Output
   ├── Natural Rural Cadence Tuning (Edge-TTS / Sarvam Bulbul)
   └── Brevity Constraint (<25 words per spoken turn)

[ Stage 3: Full Voice AI Application ]
   ├── Spoken Kannada Voice In (Sarvam Saaras / Groq Whisper v3)
   ├── Bimodal High-Contrast Web UI (Audio visualizer + live cards)
   └── Full sub-2-second conversational turn-taking loop
```

---

## 2. Stored Government Scheme Catalogue

The application uses a locally stored catalogue researched against official portals, not a live web-search response or synthetic scheme branches:

| Scheme | Type | Purpose & Scope |
| :--- | :--- | :--- |
| **PM-KISAN** | Central Government scheme | Income support programme for eligible farmer families. Final beneficiary status and exclusions require official verification. |
| **PMFBY / Karnataka Samrakshane** | Central scheme / Karnataka implementation | Crop insurance; current notified crop, area, enrollment, and claim must be confirmed for the relevant season. |
| **PMKSY — Per Drop More Crop** | Central scheme / state implementation | Supports farm-level water-use efficiency through drip and sprinkler irrigation. Current Karnataka criteria/rates are not hardcoded. |
| **Sub-Mission on Agricultural Mechanization (SMAM)** | Central scheme / state implementation | Machinery assistance may be available; current equipment list, rates, applicant category, and allocation require official confirmation. |
| **Soil Health Card Programme** | Government soil testing/advisory service | Provides soil test and nutrient recommendations. It is not represented as a cash grant. |

Catalogue entries include official source links and a research date. Time-sensitive local conditions are referred to current government portals instead of being inferred or invented.

---

## 3. Technology Stack & Free Tooling Blueprint

### Milestone 1 (Text-to-Text)
- **Language / Runtime:** Python 3.10+
- **LLM / NLU Engine:** Google Gemini 2.5 Flash (via free API tier from Google AI Studio: 15 RPM / 1M TPM free) or local Ollama (Llama 3.2 / Qwen 2.5).
- **Rule Engine:** Pure Python deterministic evaluation engine.
- **Testing Interface:** Interactive Terminal CLI + JSON test harness.

### Milestone 2 (Voice Output)
- **Kannada TTS (100% Free / Open):**
  - **Edge-TTS:** Free high-quality neural Kannada voices (`kn-IN-GaganNeural`, `kn-IN-SapnaNeural`). Requires zero API keys and has zero cost.
  - **Sarvam AI (Bulbul):** Generous hackathon free tier credits for expressive rural cadence.

### Milestone 3 (Full Voice AI App)
- **Kannada ASR (Speech-to-Text):**
  - **Groq Cloud Whisper-large-v3:** Sub-300ms ultra-fast transcription on free tier, conditioned with Kannada agricultural prompt terms.
  - **Sarvam AI Saaras:** Tailored for code-mixed Kannada audio.
- **Frontend:** React + Vite + TailwindCSS with Web Audio API.

---

## 4. Success Criteria Across Prototypes

1. **Stage 1 Success:** Text input like *"ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?"* returns source-linked PMKSY information without claiming a fixed subsidy or approval.
2. **Stage 2 Success:** The recommendation is converted into natural, warm, spoken Kannada audio in under 500ms, strictly limited to 2-3 clear sentences.
3. **Stage 3 Success:** A user speaks into the browser microphone; the system transcribes live, computes eligibility, plays spoken audio, and updates interactive scheme cards in < 2.0 seconds.
