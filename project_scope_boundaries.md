# Project Scope Definition (SCOPE)

## 1. Strategic Phasing Scope

Because building a high-reliability voice assistant requires a rock-solid conversational brain first, the project scope is partitioned into two sequential phases.

### Phase 1 Scope: Core Conversational Brain & Deterministic Rule Engine (Text Modality)
1. **Multi-Turn Dialogue Manager**: Stateful conversation orchestrator maintaining `FarmerProfile` slots across turns.
2. **Kannada & Code-Mixed NLU**: Extraction of location, land size, ownership status, crop type, cultivation season, and assistance need from Kannada script, Kanglish, and English-mixed text.
3. **Agricultural Entity Normalizer**: Conversion of *Gunte*/*Cent*/*Ekare* to canonical Acres/Hectares, regional crop names (*Togari*, *Jola*, *Bhatta*, *Ragi*, *ippattu gunte*) to standard codes, and seasonal terms (*Mungaru*, *Hingaru*, *Besige*) to `KHARIF`, `RABI`, `SUMMER`.
4. **Auditable Rule Engine**: Declarative JSON rule evaluation for all 5 Reference Schemes (`PM-KISAN`, `PMFBY`, `Demo Micro-Irrigation Support`, `Demo Agricultural Equipment Assistance`, `Demo Soil Improvement Support`).
5. **Spoken-Style Kannada Generator**: Generation of ear-friendly Kannada text responses (designed for spoken delivery even when viewed as text in Phase 1) alongside structured UI cards.
6. **Preset Persona Simulator**: One-click test utterances in the UI for judges and developers to test regional dialects and multi-turn edge cases rapidly.

### Phase 2 Scope: Voice-First Modality Migration
1. **Kannada ASR Integration**: Streaming or chunked speech-to-text recognition supporting regional Karnataka accents and code-mixed English vocabulary.
2. **Voice Activity Detection (VAD) & Barge-In**: Client-side silence detection and immediate interruption handling when a farmer speaks over the assistant.
3. **Spoken Kannada TTS Synthesis**: Low-latency neural text-to-speech generating clear, warm Kannada audio with proper pronunciation of scheme acronyms and numbers.
4. **Voice-First UI Mode**: Large central microphone orb, visual state cues (Listening, Thinking, Speaking), and simplified visual scheme cards with audio replay buttons.

---

## 2. Out of Scope (Non-Goals for Prototype)
* **Direct Government Portal Submission**: The prototype will not submit live applications or authenticate directly against production government APIs (such as live UIDAI Aadhaar e-KYC or live Karnataka *Bhoomi* / *FRUITS* production databases).
* **Legal Entitlement Guarantee**: All recommendations clearly state they are preliminary eligibility assessments subject to official verification at the *Raitha Samparka Kendra* (RSK) or official portal. Synthetic schemes (`Demo Micro-Irrigation`, `Demo Agricultural Equipment`, `Demo Soil Improvement`) are explicitly badged as `[DEMO / SYNTHETIC SCHEME]`.
* **Languages Other Than Kannada (+ English Code-Mixing)**: While the architecture is extensible to other Indic languages, this prototype focuses strictly on Kannada and Kannada-English code-mixing.