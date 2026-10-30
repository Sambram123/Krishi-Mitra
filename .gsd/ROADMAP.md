# ROADMAP.md — Krishi Mitra

> **Milestone Strategy**: 3-Stage Evolutionary Prototyping  
> **Stage 1**: Text-to-Text Prototype (NLU + Rule Engine)  
> **Stage 2**: Voice Output Prototype (Text In $\rightarrow$ Kannada Audio Out)  
> **Stage 3**: Full Voice AI Application (Kannada Voice In $\rightarrow$ Dialect NLU $\rightarrow$ Rule Engine $\rightarrow$ Kannada Voice + Visual Cards Out)

---

## Must-Haves
- [ ] Strict schema modeling of official reference dataset (PM-KISAN, PMFBY, Demo Micro-Irrigation, Demo Agri Equipment, Demo Soil Improvement).
- [ ] 100% deterministic rule verification without generative hallucination.
- [ ] Natural conversational slot extraction in rural Kannada dialects.
- [ ] Free/open-source tools integration (Gemini Flash free tier, Edge-TTS/Sarvam, Groq Whisper).
- [ ] End-to-end low latency voice interaction loop (< 2.0s).

---

## Phases

### Phase 1: Reference Dataset & Deterministic Rule Engine (Stage 1 Core)
**Status**: ✅ Complete  
**Objective**: Model the 5 target schemes (2 real, 3 synthetic) into structured JSON and build the pure Python deterministic rule engine with unit test coverage.  
**Deliverables**:
- `data/schemes_dataset.json`: Structured representation of PM-KISAN, PMFBY, Demo Drip Irrigation, Demo Equipment, and Demo Soil Improvement.
- `backend/rules_engine.py`: Pure Python rule evaluator checking eligibility, exclusions, benefit calculation, and required documents.
- `backend/test_rules.py`: Automated test cases validating all 5 schemes including exclusion edge cases.

---

### Phase 2: Text-to-Text Conversational Prototype (Stage 1 Completion)
**Status**: ⬜ Not Started  
**Objective**: Build the text-to-text dialogue loop in Kannada. Parse farmer inputs into structured agricultural profiles, ask follow-up questions for missing slots, and output audited scheme results in text.  
**Deliverables**:
- `backend/nlu_extractor.py`: Gemini Flash / local LLM entity extraction handling Kannada crop names and dialect terms (*Togari*, *Kushki*, *Gunta*).
- `backend/conversation_state.py`: Session context memory to handle multi-turn conversations.
- `cli_chat_prototype.py`: Interactive CLI to test multi-turn text conversations without audio overhead.

---

### Phase 3: Voice Output Prototype (Stage 2)
**Status**: ⬜ Not Started  
**Objective**: Enable spoken Kannada voice output for the text assistant using free, high-cadence neural TTS.  
**Deliverables**:
- `backend/tts_service.py`: Free Kannada TTS engine using Edge-TTS (`kn-IN-GaganNeural`/`kn-IN-SapnaNeural`) or Sarvam AI Bulbul.
- Audio response synthesizer formatting concise rural Kannada spoken responses (<25 words) alongside full text output.
- `test_voice_output.py`: Automated testing script generating playable audio files.

---

### Phase 4: Full Voice AI Application & Bimodal UI (Stage 3)
**Status**: ⬜ Not Started  
**Objective**: Integrate Kannada Speech Recognition (ASR), build the bimodal web interface with audio visualizer, live transcript, and interactive scheme cards.  
**Deliverables**:
- `backend/asr_service.py`: Sarvam AI / Groq Whisper Large-v3 Kannada streaming ASR.
- `frontend/`: React + Vite web application with animated microphone visualizer, live Kannada transcription, and color-coded scheme eligibility cards.
- Complete voice-in, voice-out loop benchmarked under 2 seconds.
- Final hackathon rehearsal with realistic persona scripts.
