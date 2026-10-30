# SPEC.md — Project Specification: Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)

> **Status**: `FINALIZED`
> **Version**: v1.1
> **Prototyping Strategy**: Phased 3-Stage Delivery (Text-to-Text $\rightarrow$ Voice-Out $\rightarrow$ Full Voice AI)

---

## Vision
To bridge the digital and linguistic divide for Indian farmers by creating **Krishi Mitra**, a hyper-localized, voice-first AI assistant in **Kannada**. Rather than jumping straight into an uncalibrated complex voice app, Krishi Mitra follows an evolutionary 3-stage architecture:
1. **Stage 1 (Text-to-Text Prototype):** Validates dialect NLU, entity slot filling, and deterministic rule evaluation across the hackathon reference dataset.
2. **Stage 2 (Voice-Output Prototype):** Adds high-cadence spoken Kannada synthesis (TTS) to test natural acoustic rhythm and brevity.
3. **Stage 3 (Full Voice AI Application):** Integrates live Kannada speech recognition (ASR) and a high-contrast bimodal web interface for the final hackathon demo.

---

## Reference Dataset Scope
The system explicitly models and evaluates the 5 benchmark schemes mandated by the problem statement:
1. **PM-KISAN (Real):** Direct income assistance for landholding farmer families; strict official exclusions (taxpayers, constitutional posts) and enrollment criteria.
2. **PMFBY (Real):** Crop insurance covering notified crops (Ragi, Togari, Jola, Paddy) across seasons (Kharif/Rabi) against weather calamities.
3. **Demo Micro-Irrigation Support (Fictional Synthetic):** Drip & sprinkler subsidy decision logic (70-90% subsidy for small/marginal farmers with water sources).
4. **Demo Agricultural Equipment Assistance (Fictional Synthetic):** Equipment mechanization subsidy (power tiller, rotavator, tractor).
5. **Demo Soil Improvement Support (Fictional Synthetic):** Soil fertility enhancement based on Soil Health Card deficiencies.

*Note on Synthetic Schemes: The prototype explicitly marks fictional schemes with a clear demonstration badge to maintain algorithmic transparency.*

---

## Goals
1. **100% Deterministic & Auditable Scheme Evaluation:** Zero-hallucination rule engine for the 5 reference schemes.
2. **Rural Kannada Dialect & Agri Jargon Handling:** Accurately parse North Karnataka (*-aitri*) and Mysore (*-kanri*) dialects, crop colloquia (*Togari, Kabbu, Jola*), and land units (*Gunta* to Acre).
3. **Progressive Prototyping:**
   - Text CLI / Playground for rapid logic verification.
   - Spoken Kannada audio generation (<25 words per turn).
   - Low-latency (<2.0s) full voice-in, voice-out web application.
4. **Free & Open-Source Tooling:** Leverage free tier and open tools (Gemini 2.5 Flash free tier, Edge-TTS, Groq Whisper) ensuring zero cost and infinite repeatability.

---

## Non-Goals (Out of Scope for Hackathon)
- Direct transactional write-backs to live government databases.
- Multi-state language expansion beyond Kannada / code-mixed Kannada-English.
- Computer vision pest diagnostics.

---

## Success Criteria
- [ ] Automated test suite verifies 100% accuracy on all 5 reference schemes, including negative exclusion cases.
- [ ] Text-to-Text prototype correctly fills missing slots over multi-turn conversation.
- [ ] Spoken Kannada audio is synthesized with natural rural cadence using free neural TTS.
- [ ] Final voice-to-voice end-to-end loop executes within 2.0 seconds.
- [ ] High-contrast visual interface renders scheme cards, audit reasons, and document checklists.
