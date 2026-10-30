# SPEC.md — Project Specification: Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)

> **Status**: `FINALIZED`
> **Version**: v1.0
> **Target Event**: National Level Hackathon

---

## Vision
To bridge the digital and linguistic divide for Indian farmers by creating **Krishi Mitra**, a hyper-localized, voice-first AI assistant in **Kannada**. Rather than acting as a standard text chatbot with a microphone overlay, Krishi Mitra functions as an empathetic, proactive digital Grama Sevak. It conducts natural two-way spoken dialogues, understands regional dialects (North Karnataka & Mysore belts) and agricultural colloquialisms, extracts farm profiles organically through conversation, and executes transparent, auditable eligibility evaluations against Karnataka State and Central Government agricultural schemes with zero hallucination.

---

## Goals
1. **True Voice-Native Kannada Interaction:** Deliver a low-latency (<2.0s roundtrip) conversational voice loop featuring interruptible playback, natural rural phrasing, and turn-taking without awkward dead air.
2. **Dialect & Agricultural Jargon Normalization:** Accurately parse rural dialects (e.g., North Karnataka *-aitri*, Mysore *-kanri*), local crop terms (*Togari, Kabbu, Ragi, Jola*), and traditional land units (*Guntas* into Acres).
3. **Deterministic & Auditable Eligibility Engine:** Decouple conversational AI from decision logic to ensure 100% zero-hallucination scheme matching (Raitha Siri, Krishi Bhagya, PM-KISAN, PMFBY, Surya Raitha, KCC) with verifiable gazette criteria and document checklists.
4. **Bimodal High-Contrast Accessibility UI:** Pair the spoken voice conversation with dynamic visual scheme cards, audio waveforms, live Kannada transcripts, and document checklists designed for rural accessibility.

---

## Non-Goals (Out of Scope for v1.0)
- Building direct API submission into official government databases (e.g., Seva Sindhu / Samrakshane automated filing) due to lack of public transactional APIs; will provide direct guidance and kiosk checklists instead.
- Multi-state language expansion (e.g., Marathi, Telugu) beyond Kannada and code-mixed Kannada-English for the initial hackathon delivery.
- Complex satellite remote sensing / computer vision pest diagnostics; focus remains strictly on conversational scheme eligibility and farmer guidance.

---

## Users
1. **Marginal/Small Landholding Farmers in Karnataka:** Individuals with 1–5 acres of dryland or wetland who speak regional Kannada, have limited digital literacy, and are intimidated by complex formal portals.
2. **Village Kiosk Operators & Grama One Facilitators:** Intermediaries seeking a rapid voice discovery tool to consult and advise visiting farmers on qualifying benefits.
3. **Hackathon Evaluation Jury:** Technical and domain judges assessing voice latency, conversational naturalness, dialect handling, and deterministic verification.

---

## Constraints
- **Latency Budget:** Total voice-to-voice turn latency must remain under 2.0 seconds to preserve conversational flow.
- **Audio Reliability:** Must function on varying network bandwidths using compressed audio transmission (WebM / Opus).
- **Zero Hallucination Tolerance:** Financial scheme benefits, eligibility conditions, and required documents must be 100% auditable and rule-backed.
- **Hackathon Timeline:** Working prototype must be complete, testable, and demonstrable within 24 to 36 hours.

---

## Success Criteria
- [ ] End-to-end voice loop (Farmer Kannada Speech -> ASR -> Extraction -> Rule Match -> Spoken Response) executes within 2.0 seconds.
- [ ] Correctly parses and normalizes at least 3 distinct dialectal phrases and crop colloquialisms (e.g., *"ತೊಗರಿ"*, *"ಕುಷ್ಕಿ"*, *"ಗುಂಟೆ"*).
- [ ] Correctly identifies eligibility and lists required documents for all 6 target schemes without generative hallucinations.
- [ ] Live demo seamlessly conducts a multi-turn conversation resolving missing information (e.g., asking for land size if omitted).
- [ ] High-contrast, responsive visual interface renders scheme eligibility cards and audit trails synchronously with speech playback.
