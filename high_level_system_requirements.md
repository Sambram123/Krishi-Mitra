# System & Business Requirements

## 1. Linguistic & Cultural Requirements
* **REQ-LING-01 (Regional Dialect Tolerance)**: The system must comprehend vocabulary variations across major Karnataka regions:
  * *Old Mysuru* (e.g., Mandya, Mysuru, Hassan)
  * *Uttara Karnataka / Kittur & Kalyana Karnataka* (e.g., Dharwad, Belagavi, Kalaburagi, Raichur)
  * *Malnad & Coastal* (e.g., Shivamogga, Dakshina Kannada, Udupi)
* **REQ-LING-02 (Code-Mixing)**: Farmers frequently use English nouns inside Kannada sentences (e.g., *"Insurance", "Subsidy", "Drip", "Borewell", "Tractor", "2 Acres", "Aadhaar link"*). The system must parse code-mixed utterances seamlessly without requiring pure literary Kannada.
* **REQ-LING-03 (Colloquial Number & Unit Parsing)**: Support spoken Kannada numbers and fractions (e.g., *onduuvare ekare* = $1.5\text{ Acres}$, *ippattu gunte* = $20\text{ Gunte} = 0.5\text{ Acres}$, *ardha ekare* = $0.5\text{ Acres}$).
* **REQ-LING-04 (Voice-First Register)**: Spoken output must use respectful, warm everyday Kannada (*"ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ"*, *"ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಜಮೀನು ಇದೆ?"*) avoiding overly Sanskritized bureaucratic jargon unless explaining an official term in simple words.

---

## 2. Eligibility & Auditability Requirements
* **REQ-AUD-01 (Symbolic Rule Separation)**: Eligibility decisions must be computed by a deterministic rule engine, never by free-form LLM inference.
* **REQ-AUD-02 (Rule Traceability)**: Every scheme recommendation must produce an auditable JSON trace listing:
  * Which rules passed (with the exact farmer slot value that satisfied the rule).
  * Which rules failed (if ineligible).
  * Which required slots are still unknown (`MISSING_INFO`).
* **REQ-AUD-03 (Real vs. Synthetic Distinction)**: The system must explicitly distinguish between real schemes (`PM-KISAN`, `PMFBY`) and synthetic test schemes (`Demo Micro-Irrigation Support`, `Demo Agricultural Equipment Assistance`, `Demo Soil Improvement Support`) in both the visual UI badge and spoken disclaimers.

---

## 3. Conversational Experience Requirements
* **REQ-CONV-01 (Progressive Slot Gathering)**: Never overwhelm the farmer by asking 5 questions at once. Ask at most 1 to 2 logically related questions per turn.
* **REQ-CONV-02 (Context Persistence)**: Maintain full session memory across follow-up turns so farmers can ask about required documents, application steps, exclusion criteria, or "what-if" changes to their crop/season without repeating their profile.