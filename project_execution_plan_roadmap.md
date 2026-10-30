# Project Execution Plan & Phased Migration Roadmap (PLAN)

## 1. Strategic Development Milestones

We execute the build in 4 disciplined sprints so that at every stage we have a working, testable artifact.

---

### Milestone 1: Auditable Knowledge Base & Deterministic Rule Engine (Hours 0–6)
* **Goal**: Build the 100% deterministic foundation before writing any LLM prompt.
* **Deliverables**:
  1. `data/schemes/schemes_catalog.json` encoding all 5 Reference Schemes (`PM-KISAN`, `PMFBY`, `Demo Micro-Irrigation Support`, `Demo Agricultural Equipment Assistance`, `Demo Soil Improvement Support`) with Kannada explanations, benefits, conditions, required documents, and application steps.
  2. `data/lexicons/` containing Karnataka districts/taluks, regional crop names (*Togari*, *Jola*, *Bhatta*, *Ragi*, *Adike*, *Kabbu*, *Shenga*), and land unit conversions (*Ekare*, *Gunte*, *Cent*).
  3. `backend/app/core/normalizer.py` and `backend/app/core/rule_engine.py` with $100\%$ unit test coverage.

---

### Milestone 2: Phase 1 Core Conversational Agent — Text & Kanglish Modality (Hours 6–14)
* **Goal**: Complete the multi-turn conversational brain using text interaction.
* **Deliverables**:
  1. `nlu_extractor.py`: Extracts structured `FarmerProfile` updates from Kannada script, Kanglish, and code-mixed English while preserving existing session slots.
  2. `dialogue_manager.py`: Computes missing slots across potentially applicable schemes and prioritizes the single best follow-up question.
  3. `response_generator.py`: Generates natural, spoken-style Kannada responses grounded strictly in the `EligibilityAuditResult`.
  4. FastAPI endpoints (`/api/v1/sessions`, `/api/v1/chat/turn`, `/api/v1/schemes`) verified against multi-turn context retention tests.

---

### Milestone 3: Frontend Workbench & Transparency Inspector (Hours 14–20)
* **Goal**: Build the visual interface showcasing both the farmer experience and the auditable rule engine.
* **Deliverables**:
  1. Split-pane Next.js web application with `ConversationStream`, `ExtractedSlotsView`, and `SchemeCard` components.
  2. **Dialect Quick-Test Bar** for instant 1-click testing of regional accents/vocabulary and follow-up turns.
  3. Explicit `[REAL SCHEME]` vs. `[DEMO / SYNTHETIC SCHEME]` visual badges and document checklists.

---

### Milestone 4: Phase 2 Migration — Voice-First Streaming Pipeline (Hours 20–30)
* **Goal**: Upgrade from text interaction to a seamless, voice-first spoken Kannada assistant.
* **Deliverables**:
  1. Integrate Kannada ASR (`asr_service.py`) with agricultural phrase boosting and regional accent tolerance.
  2. Integrate Spoken Kannada TTS (`tts_service.py`) with Kannada number/currency verbalization and sentence-level chunking.
  3. Implement client-side microphone capture, live audio waveform (`VoiceOrb.tsx`), VAD end-of-speech detection, and instant **Barge-In** interruption handling.
  4. Conduct end-to-end voice acceptance testing across all 5 reference schemes.