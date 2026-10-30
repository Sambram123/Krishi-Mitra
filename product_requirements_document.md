# Product Requirements Document (PRD): Krishi Mitra

## 1. Executive Summary
Farmers across Karnataka have access to vital Central and State agricultural schemes covering income support, crop insurance, micro-irrigation, farm equipment, and soil health. However, discovery and eligibility verification remain inaccessible to many small and marginal farmers due to scattered web portals, dense bureaucratic terminology, and text-heavy forms requiring formal language.

**Krishi Mitra** is a voice-first AI assistant designed for natural spoken Kannada interaction. It conducts a warm, multi-turn conversation with the farmer, extracts key agricultural profile attributes, evaluates eligibility against an auditable rule engine, and explains benefits, conditions, required documents, and application steps in plain spoken Kannada.

---

## 2. Target User Personas

### Persona 1: Mallikarjun (North Karnataka Dryland Farmer)
* **Location**: Dharwad / Kalaburagi region
* **Dialect**: Uttara Karnataka (Dharwad/Kalaburagi Kannada with regional vocabulary like *Jola*, *Togari*, *Mungaru*, *Hola*)
* **Landholding**: $3.5\text{ Acres}$ ($3\text{ Ekare } 20\text{ Gunte}$), owned
* **Digital Literacy**: Uses voice notes on WhatsApp and YouTube; uncomfortable typing Kannada script on a phone keyboard.
* **Goal**: Wants to know if he can get crop insurance for his red gram (*Togari*) crop this monsoon and whether he qualifies for annual financial support.

### Persona 2: Puttaraju (Old Mysuru Smallholder & Horticulture Farmer)
* **Location**: Mandya / Hassan region
* **Dialect**: Old Mysuru Kannada with frequent English code-mixing ("Drip irrigation ge subsidy sigutta?", "2 acre land ide")
* **Landholding**: $1.5\text{ Acres}$ ($1\text{ Ekare } 20\text{ Gunte}$), owned + $1\text{ Acre}$ leased
* **Goal**: Needs subsidy support for installing drip irrigation for coconut/tomato and wants to know what documents (like *Pahani*/RTC) to take to the *Raitha Samparka Kendra* (RSK).

### Persona 3: Kavitha (Tenant / Sharecropper Farmer)
* **Location**: Shivamogga / Davanagere
* **Landholding**: $2\text{ Acres}$ leased (*Guttige* / tenant cultivator)
* **Goal**: Wants to check which schemes apply when the land title (*Pahani*) is not in her name, ensuring the system accurately explains ownership constraints for PM-KISAN while offering eligible alternatives like PMFBY (where applicable) or soil improvement programs.

---

## 3. Problem Statement & Core Objectives

| Objective ID | Objective Description | Success Metric |
| :--- | :--- | :--- |
| **OBJ-1** | Recognize natural Kannada speech, including regional accents and code-mixed phrases. | $\ge 90\%$ intent & entity extraction accuracy across 4 major Karnataka dialect test sets. |
| **OBJ-2** | Extract location, land area, crops, ownership, season, and assistance needs. | $100\%$ normalization of local units (*Gunte*, *Ekare*, *Cent*) and local crop names into canonical schema. |
| **OBJ-3** | Ask meaningful follow-up questions when required information is missing. | Maximum 1–2 missing slots asked per turn in natural conversational order; zero redundant questions. |
| **OBJ-4** | Recommend potentially applicable schemes using a rule-based or auditable eligibility layer. | $100\%$ deterministic match between rule engine output and spoken explanation; $0\%$ hallucinated entitlements. |
| **OBJ-5** | Explain reasons, benefits, conditions, documents, and application steps in spoken Kannada. | Spoken responses average $12\text{--}25\text{ seconds}$ per turn, free of markdown formatting artifacts. |
| **OBJ-6** | Retain context across follow-up questions in the same conversation. | Seamless handling of "What documents do I need for the second one?" or "What if I also grow Maize?" across $6+$ turns. |

---

## 4. Phased Product Evolution

### Phase 1: Core Agent & Rule Engine (Text-First Foundation)
* Interactive web interface allowing text input in Kannada script (`ಕನ್ನಡ`), Romanized Kannada (Kanglish), or mixed English/Kannada.
* Complete dialogue manager, slot extractor, dialect normalizer, and deterministic rule evaluator.
* Live **Eligibility Audit Inspector** panel showing extracted slots, triggered rules, and missing criteria in real time.

### Phase 2: Voice-First Conversational Experience
* Full-duplex microphone interface with push-to-talk and hands-free VAD (Voice Activity Detection).
* Real-time Kannada ASR transcription with regional agricultural vocabulary boosting.
* Spoken Kannada TTS output with natural prosody, barge-in support (stopping playback immediately when the farmer speaks), and visual audio waveform feedback.