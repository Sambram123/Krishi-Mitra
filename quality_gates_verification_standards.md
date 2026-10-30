# Quality Gates & Definition of Done (QUALITY_GATE)

Every feature across Phase 1 and Phase 2 must pass four strict automated and manual quality gates before merging.

---

## Gate 1: Deterministic Rule Engine Accuracy ($100\%$ Required)
* **Criterion**: All unit tests in `backend/tests/test_rule_engine.py` must pass with $100\%$ accuracy.
* **Checks**:
  * Land conversions (`Gunte`, `Ekare`, `Cent`, `Hectare`) compute accurate floating-point Acre values within $\pm 0.001\text{ Acres}$.
  * Each of the 5 schemes transitions accurately between `ELIGIBLE`, `POTENTIALLY_ELIGIBLE_MISSING_INFO`, and `INELIGIBLE` across boundary values.
  * Synthetic schemes always emit `is_synthetic: true`.

## Gate 2: Zero-Hallucination & Grounding Audit ($0\%$ Tolerance)
* **Criterion**: Spoken Kannada responses must never invent a scheme name, alter a subsidy figure, or declare a farmer eligible when the rule engine status is `INELIGIBLE` or `POTENTIALLY_ELIGIBLE_MISSING_INFO`.
* **Verification**: Automated post-generation validator checks that only scheme IDs present in `eligibility_results` with status `ELIGIBLE` or `POTENTIALLY_ELIGIBLE_MISSING_INFO` are recommended as applicable.

## Gate 3: Spoken Kannada Register & Prosody Check
* **Criterion**: Responses sent to the TTS engine must contain:
  * $0$ markdown characters (`*`, `#`, `-`, `` ` ``).
  * $0$ raw un-verbalized English abbreviations that break Kannada TTS (e.g., `Rs.`, `Ha.`, `slash`).
  * Average turn length $\le 45\text{ words}$ (approx. 3–4 short spoken sentences).

## Gate 4: Multi-Turn Context Retention Gate
* **Criterion**: In a 5-turn conversation where the farmer states location in Turn 1, land/ownership in Turn 2, crop/season in Turn 3, asks about documents in Turn 4, and modifies the crop in Turn 5, the `FarmerProfile` must retain $100\%$ of prior slots without asking the farmer to repeat already provided details.