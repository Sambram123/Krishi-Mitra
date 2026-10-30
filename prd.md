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

## 2. Benchmark Reference Dataset Specification

The problem statement requires testing against a hybrid benchmark dataset of **2 Real Schemes** and **3 Synthetic/Fictional Schemes**:

| Scheme | Type | Purpose & Scope |
| :--- | :--- | :--- |
| **PM-KISAN** | Real Official Scheme | Income support of ₹6,000/yr for landholding farmer families. Requires strict verification of official exclusions (institutional landholders, income tax payees, constitutional posts) and mandatory document criteria (RTC/Pahani, Aadhaar-NPCI seeded bank account). |
| **PMFBY** | Real Official Scheme | Comprehensive crop insurance for notified crops (Ragi, Togari, Jola, Paddy, Cotton) across seasons (Kharif/Rabi) against weather calamities. |
| **Demo Micro-Irrigation Support** | Fictional Synthetic | Test case for drip & sprinkler irrigation subsidy (70% general, 90% small/marginal). Tests water source availability and historical subsidy cooldown constraints. |
| **Demo Agricultural Equipment Assistance** | Fictional Synthetic | Test case for farm mechanization subsidy (power tillers, rotavators, small tractors) capped at ₹1,00,000 / 50%. |
| **Demo Soil Improvement Support** | Fictional Synthetic | Test case for soil health incentive (₹5,000/ha) based on Soil Health Card deficiency indicators. |

*Transparency Guardrail: The application will display a distinct `[DEMO / TEST CASE]` badge alongside synthetic schemes to prevent real-world misinformation.*

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

1. **Stage 1 Success:** Text input like *"ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ, ಬೋರ್ವೆಲ್ ಐತಿ, ಹನಿ ನೀರಾವರಿಗೆ ಸಹಾಯ ಸಿಗ್ತೈತಾ?"* correctly outputs eligibility for `Demo Micro-Irrigation Support` and `PM-KISAN` with audit trail and document list.
2. **Stage 2 Success:** The recommendation is converted into natural, warm, spoken Kannada audio in under 500ms, strictly limited to 2-3 clear sentences.
3. **Stage 3 Success:** A user speaks into the browser microphone; the system transcribes live, computes eligibility, plays spoken audio, and updates interactive scheme cards in < 2.0 seconds.
