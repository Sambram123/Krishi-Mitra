# ROADMAP.md — Krishi Mitra

> **Current Phase**: Phase 1 (Not Started)
> **Milestone**: v1.0 (Hackathon Working Demo)

---

## Must-Haves (from SPEC.md)
- [ ] Sub-2-second voice-to-voice turn taking in Kannada.
- [ ] Regional dialect and colloquial crop/unit mapping.
- [ ] Multi-turn slot filling for incomplete profile inputs.
- [ ] Auditable, zero-hallucination deterministic rule engine for 6 key schemes.
- [ ] High-contrast, responsive voice UI with live visual scheme cards and document checklists.

---

## Phases

### Phase 1: Knowledge Catalog & Deterministic Rule Engine
**Status**: ⬜ Not Started  
**Objective**: Build and unit-test the Python deterministic scheme evaluator and agricultural ontology knowledge base without any LLM dependencies.  
**Requirements**: REQ-04, REQ-07  
**Deliverables**:
- `backend/schemes_db.json`: Curated definitions for 6 state/central schemes with exact eligibility equations.
- `backend/rules_engine.py`: Pure Python rule matcher returning eligibility status, audit reasons, and required documents.
- `backend/test_rules.py`: Automated tests covering dryland, wetland, tenant, and varied acreage scenarios.

---

### Phase 2: Kannada Voice Pipeline & LLM Slot Extraction
**Status**: ⬜ Not Started  
**Objective**: Establish low-latency Kannada ASR, dialect-aware NLU slot extraction, multi-turn state management, and natural TTS generation.  
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-05  
**Deliverables**:
- Fast Kannada ASR integration (Sarvam AI / Groq Whisper fallback).
- Gemini 2.5 Flash / GPT-4o-mini entity extractor with few-shot dialect normalization.
- Session-based conversation memory tracking farmer profile across multiple turns.
- Kannada TTS synthesizer producing concise spoken summaries.

---

### Phase 3: Bimodal Accessible Frontend & Voice Visualizer
**Status**: ⬜ Not Started  
**Objective**: Build a high-contrast, mobile-friendly web interface with real-time audio interaction, animated visualizer, live transcript, and scheme cards.  
**Requirements**: REQ-06, REQ-07  
**Deliverables**:
- Responsive Web UI with prominent, thumb-friendly microphone and dynamic waveform states.
- Live Kannada transcription banner with transliteration.
- Interactive Scheme Eligibility Cards with color-coded badges, audit dropdowns, and document checklists.
- Audio playback coordinator supporting interruptible audio playback.

---

### Phase 4: Integration, Latency Hardening & Demo Scenarios
**Status**: ⬜ Not Started  
**Objective**: Wire frontend and backend together, benchmark and optimize end-to-end latency (<2.0s), and rehearse live rural persona test cases.  
**Requirements**: REQ-01 through REQ-07  
**Deliverables**:
- Complete end-to-end tested flow.
- Offline backup demo video & scripted evaluation scenarios (North Karnataka drought, Mandya solar pump).
- Hackathon pitch slide deck highlighting voice-first innovations and zero-hallucination architecture.
