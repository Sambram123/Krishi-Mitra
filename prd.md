# Product Requirements Document (PRD) — Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)
**Voice-First Conversational AI for Farmer Scheme Eligibility & Assistance**

---

## 1. Executive Summary & Vision

### 1.1 Vision
To bridge the digital and linguistic divide for Indian farmers by creating **Krishi Mitra**, a hyper-localized, voice-first AI assistant in **Kannada**. Rather than acting as a standard text chatbot with a microphone overlay, Krishi Mitra functions as an empathetic, proactive digital Grama Sevak (village agricultural officer). It conducts natural two-way spoken dialogues, understands regional dialects and agricultural colloquia, extracts farm profiles organically, and executes transparent, auditable eligibility evaluations against Karnataka State and Central Government schemes.

### 1.2 The Problem
1. **Information Fragmentation:** Central (PM-KISAN, PMFBY, KCC) and State (Raitha Siri, Krishi Bhagya, Surya Raitha) schemes are scattered across disparate portals (Seva Sindhu, Fruits Karnataka, Bhoomi, Samrakshane).
2. **Linguistic & Literacy Barriers:** Portals require structured Kannada/English formal text entry. Farmers speak in regional colloquialisms, mixing Kannada with English loanwords (e.g., *borewell*, *subsidy*, *acre*, *RTC/Pahani*), and use non-standard units (e.g., *gunta*, *bigha*).
3. **Dialectal Diversity:** Kannada spoken in North Karnataka (Hubli-Dharwad/Kalaburagi), Old Mysore (Mandya/Hassan), and Coastal regions (Mangalore/Udupi) differs significantly in phonetics, vocabulary, and cadence.
4. **The Hallucination Danger in AI:** Generative LLMs hallucinate government policies. Advising a marginal farmer that they qualify for a ₹50,000 subsidy when they do not causes severe financial harm and destroys trust.
5. **Shallow Voice Implementations:** Most hackathon projects use "Speech-to-Text -> Text Chatbot -> Text-to-Speech" with 8-second latency, unnatural robotic inflection, and zero conversational turn-taking.

---

## 2. Target Personas

### Persona A: Basavaraj Gowda (Mysore/Mandya Belt)
* **Demographics:** 52 years old, 2.5 acres dryland, Mandya district.
* **Crop & Context:** Grows Sugarcane (*Kabbu*) and Ragi. Has borewell failure, facing power issues.
* **Behavior:** Speaks Southern Karnataka dialect. Uses terms like *Pahani*, *Gunta*, *Current problem*, *Drip subsidy*.
* **Pain Point:** Cannot navigate Samrakshane or Seva Sindhu; intimidated by computer kiosks charging hefty commission fees.

### Persona B: Sharanappa Patil (Kalyana-Karnataka / Kalaburagi)
* **Demographics:** 45 years old, 6 acres rainfed black soil, Afzalpur, Kalaburagi.
* **Crop & Context:** Grows Red Gram (*Togari*) and White Jowar (*Bili Jola*). Hit by erratic monsoon.
* **Behavior:** Speaks North Karnataka dialect (*Kalyana Kannada*) with distinct verb endings (*-aitri*, *-nodri*, *-hogi-baddi*).
* **Pain Point:** Existing speech recognizers fail completely on his accent; unaware of insurance claim deadlines.

---

## 3. Core Value Propositions & Hackathon USPs

1. **Truly Voice-Native Interaction:**
   - Low-latency turn-taking (<1.5s audio response).
   - Interruptible listening with Voice Activity Detection (VAD).
   - Conversational slot filling (feels like talking to a village elder, not filling a tax form).
2. **Dialect & Colloquial Handling:**
   - Normalization of regional crop terms (*Togari* = Pigeon pea / Arhar, *Kabbu* = Sugarcane, *Jola* = Sorghum).
   - Regional land units (*1 Acre = 40 Guntas*).
3. **Deterministic, Auditable Eligibility Engine (Zero-Hallucination Policy):**
   - LLM is used **strictly** for Intent & Entity Extraction and Spoken Response Generation.
   - Scheme matching is done by a deterministic **Python Rule Engine** verifying explicit criteria (Landholding, Irrigation, Caste/Category, Crop type, Tenancy).
   - Generates an **Audit Trail** explaining *why* the farmer qualifies or *what exact criteria* is missing.
4. **Bimodal Interface (Voice + High-Contrast Visual Cards):**
   - Farmer hears crisp, friendly Kannada audio.
   - Screen displays large, visual, color-coded scheme eligibility cards with document checklists (Pahani, Aadhaar, Bank Passbook) and direct Seva Sindhu application links.

---

## 4. Key Functional Requirements

### 4.1 Speech-to-Text & Dialect Normalization (ASR)
- Ingest live audio streams (Opus/WebM/PCM) from browser/mobile.
- Transcribe natural, colloquial Kannada with code-mixed English words.
- Contextual acoustic hints for agricultural terms (e.g., *PM-Kisan, KCC, RTC, Pahani, Bagar Hukku, Krishi Bhagya*).

### 4.2 Conversational State & Slot Filling Engine
- Maintain dynamic session profile:
  - **Location:** District, Taluk (optional).
  - **Land Size:** Extent (in Acres/Guntas) and Ownership (Owner, Tenant/Pattadar).
  - **Crops & Season:** Kharif, Rabi, Summer; specific crops (Ragi, Paddy, Cotton, etc.).
  - **Irrigation Source:** Rainfed (*Kushki*), Borewell, Canal (*Tari*).
  - **Category/Demographics:** Small/Marginal Farmer (SF/MF), General/OBC/SC/ST, Woman farmer.
  - **Core Need:** Solar pump, insurance payout, equipment subsidy, seed subsidy, loan waiver.
- **Proactive Inquiry:** If land area or crop is missing, ask naturally in the next conversational turn without breaking flow.

### 4.3 Auditable Eligibility Matching Engine
- Match farmer profile against pre-indexed scheme definitions.
- Status categorization:
  - **Eligible:** All criteria met.
  - **Conditionally Eligible:** Missing 1-2 criteria or documentation.
  - **Not Eligible:** Clear constraint violation (e.g., >5 acres for small-farmer-only schemes).
- Generate human-readable reasons (e.g., *"Eligible because landholding is less than 2 hectares and crop is rainfed"*).

### 4.4 Spoken Response Synthesis (TTS)
- Translate verified scheme results into warm, natural Kannada dialogue.
- Pronunciation tuned for natural rhythm (avoiding robotic, staccato phrasing).
- Summary structure:
  1. Empathetic validation.
  2. Top 1 or 2 matching schemes with clear financial benefit (e.g., ₹10,000/year or 90% subsidy).
  3. Actionable next step & documents required.

### 4.5 Multimodal UI (Visual Transparency & Accessibility)
- Massive, thumb-friendly mic button with visual ripple animation during speech.
- Live audio waveform and Kannada transcription display.
- Visual Scheme Cards:
  - Scheme Name (Kannada + English).
  - Benefit badge (e.g., ₹4,000 Subsidy).
  - "Why you are eligible" bulleted checklist in green.
  - Required documents icons (Aadhaar, Pahani/RTC, Bank Passbook).
  - Direct offline helpline & Seva Sindhu kiosk guidance.

---

## 5. Non-Functional Requirements

| Metric | Target | Rationale |
| :--- | :--- | :--- |
| **End-to-End Latency** | < 2.0 seconds | A voice conversation dies if dead air exceeds 2.5s. |
| **Kannada ASR Word Error Rate (WER)** | < 18% on Agri Kannada | Needs to recognize localized dialect terms without failure. |
| **Eligibility Accuracy** | 100% Deterministic | Zero tolerance for AI hallucination on financial benefits. |
| **Bandwidth Tolerance** | Operates on 2G/3G networks | Low-bitrate audio compression (Opus 16kbps). |
| **Browser Compatibility** | Chrome/Edge on Mobile & Desktop | Works without requiring high-end native app installation. |

---

## 6. Success Metrics for Hackathon Evaluation

1. **Voice Fluidity Score:** Can a judge speak a mixed Kannada sentence and get an intelligent voice reply within 2 seconds?
2. **Dialect Robustness:** Does it correctly interpret North Karnataka phrase *"ನಮ್ಮ ಹೊಲ ಮೂರ್ ಎಕರೆ ಐತ್ರಿ, ಜೋಳ ಹಚ್ಚೇವಿ"* (Our field is 3 acres, we have sown Jowar)?
3. **Auditable Decision Explainability:** Does the app clearly display the logical rule evaluated rather than a vague LLM summary?
4. **Empathy & Simplicity:** Are the instructions clear enough for a 60-year-old farmer who has never used a smartphone app?
