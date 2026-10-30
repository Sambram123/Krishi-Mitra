# System Architecture (ARCHITECTURE)

## 1. High-Level Architectural Philosophy

Krishi Mitra uses a **Hexagonal (Ports & Adapters) Neuro-Symbolic Architecture**:
* **The Neural Layer (LLM + ASR/TTS)** handles what neural networks excel at: understanding messy, regional, code-mixed Kannada speech/text and generating warm, natural spoken Kannada explanations.
* **The Symbolic Layer (Deterministic JSON Rule Engine + Unit Normalizer)** handles what requires $100\%$ precision and auditability: land unit conversion, statutory eligibility verification, exclusion logic, and document checklists.
* **The Modality Adapter Pattern** allows **Phase 1 (Text Interaction)** and **Phase 2 (Voice Interaction)** to share $100\%$ of the core brain without rewriting business or dialogue logic.

---

## 2. End-to-End Pipeline Diagram

    +-----------------------------------------------------------------------------------+
    |                        CLIENT LAYER (Next.js / React Web App)                     |
    |                                                                                   |
    |  [Phase 1: Text & Dialect Simulator]     [Phase 2: Voice Orb, VAD & Audio Player] |
    +------------------+---------------------------------------------+------------------+
                       | REST / SSE (Text)                           | WebSocket (Audio/Events)
                       v                                             v
    +------------------+---------------------------------------------+------------------+
    |                        MODALITY INGRESS ADAPTER (FastAPI)                         |
    |                                                                                   |
    |  Text Ingress (Kannada / Kanglish)  <---  [Phase 2: Kannada ASR + Vocabulary Boost]|
    +------------------------------------------+----------------------------------------+
                                               | Canonical UTF-8 / Transliterated Turn
                                               v
    +-----------------------------------------------------------------------------------+
    |                         CORE CONVERSATIONAL AGENT BRAIN                           |
    |                                                                                   |
    |  1. Linguistic & Dialect Pre-Processor                                            |
    |     (Maps "20 gunte" -> 0.5 acre, "Mungaru" -> KHARIF, "Togari" -> PIGEON_PEA)    |
    |                                                                                   |
    |  2. Contextual NLU & Slot Extractor (Structured Output LLM)                       |
    |     (Updates Session FarmerProfile JSON + Detects Intent & Follow-up Focus)       |
    |                                                                                   |
    |  3. Deterministic Scheme Eligibility Engine (Symbolic Rule Evaluator)             |
    |     (Evaluates 5 Reference Schemes -> Outputs Audit Trace + Missing Slots)        |
    |                                                                                   |
    |  4. Dialogue Policy & Next-Action Planner                                         |
    |     (Decides: Ask Missing Slot vs. Recommend Schemes vs. Explain Docs/Steps)      |
    |                                                                                   |
    |  5. Spoken Kannada Response Synthesizer                                           |
    |     (Generates conversational, ear-friendly Kannada without markdown clutter)     |
    +------------------------------------------+----------------------------------------+
                                               | Spoken Kannada Text + Structured Audit Payload
                                               v
    +------------------------------------------+----------------------------------------+
    |                        MODALITY EGRESS ADAPTER                                    |
    |                                                                                   |
    |  [Phase 1: Stream Text + Audit JSON] ---> [Phase 2: Sentence Chunker + Kannada TTS]|
    +-----------------------------------------------------------------------------------+

---

## 3. Component Deep Dive

### 3.1 Dialect & Agricultural Pre-Processor (`normalizer.py`)
Before and after LLM slot extraction, a deterministic dictionary + regex normalizer resolves regional Karnataka terms:
* **Land Area Conversion**:
  * $\text{Acres} = \text{Ekare} + \frac{\text{Gunte}}{40} + \frac{\text{Cent}}{100} + (\text{Hectare} \times 2.471)$
* **Seasonal Mapping**:
  * *Mungaru* / *Kharif* / *Malegala* $\rightarrow$ `KHARIF`
  * *Hingaru* / *Rabi* / *Chaligala* $\rightarrow$ `RABI`
  * *Besige* / *Summer* / *Zaid* $\rightarrow$ `SUMMER`
* **Regional Crop Lexicon**:
  * *Togari* / *Tur* $\rightarrow$ `PIGEON_PEA`
  * *Jola* / *Jowar* $\rightarrow$ `SORGHUM`
  * *Bhatta* / *Nellu* $\rightarrow$ `PADDY`
  * *Ragi* $\rightarrow$ `FINGER_MILLET`
  * * ಮೆಕ್ಕೆಜೋಳ* / *Ganjomi* / *Makka* $\rightarrow$ `MAIZE`
  * *Adike* $\rightarrow$ `ARECANUT`
  * *Kabbina bele* / *Kabbu* $\rightarrow$ `SUGARCANE`
  * *Shenga* / *Kadalekai* $\rightarrow$ `GROUNDNUT`

### 3.2 Deterministic Eligibility Rule Engine (`rule_engine.py`)
* Loads declarative rule trees from `data/schemes/schemes_catalog.json`.
* Evaluates predicates (`EQUALS`, `IN`, `GTE`, `LTE`, `NOT_EQUALS`, `CONTAINS_ANY`) against the current `FarmerProfile`.
* Computes three lists per scheme:
  * `passed_conditions`: List of rules satisfied with exact farmer values.
  * `failed_conditions`: List of rules violated (making the farmer `INELIGIBLE`).
  * `missing_slots`: List of required profile fields that are currently `null`.

### 3.3 Dialogue Policy & Slot Question Prioritizer (`dialogue_manager.py`)
* Ranks `missing_slots` across all `POTENTIALLY_ELIGIBLE_MISSING_INFO` schemes by **Information Gain**:
  1. `assistance_needs` / `crops` (if completely empty)
  2. `land_area_acres` & `ownership_type` (unlocks PM-KISAN, Micro-Irrigation, Equipment)
  3. `location_district` & `season` (unlocks PMFBY notification checks)
  4. `irrigation_source` / `equipment_needed` / `exclusion_flags` (unlocks specific scheme tiers)
* Passes only the top 1–2 missing slots and/or verified eligible schemes to the Spoken Kannada Response Generator so the farmer is never bombarded with questions.

### 3.4 Phase 2 Voice Pipeline Adapter (`voice_pipeline.py`)
* **VAD & Barge-In**: Uses WebRTC / Silero VAD on the client to detect speech onset within $150\text{ ms}$, immediately halting active TTS playback and clearing the audio queue.
* **ASR**: Supports dual provider configuration (Sarvam AI `saaras / saarika` or Google Cloud Speech-to-Text `kn-IN` / Azure Speech `kn-IN` with custom phrase list boosting for Kannada agricultural terms).
* **TTS**: Streams sentences segmented on Kannada punctuation (`।`, `.`, `?`, `!`) to Sarvam AI `bulbul` or Azure Neural TTS (`kn-IN-SapnaNeural` / `kn-IN-GaganNeural`) for natural prosody.