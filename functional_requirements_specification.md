# Functional Requirements (FUNCTIONAL_REQUIREMENTS)

## 1. Speech & Text Input Processing
* **FR-01**: In Phase 1, the system shall accept user input via UTF-8 Kannada script, Romanized Kannada (Kanglish), and English text.
* **FR-02**: In Phase 2, the system shall capture microphone audio (`16 kHz`, mono PCM/WebM), detect end-of-speech via VAD, and transcribe spoken Kannada/code-mixed audio into text with confidence scores.
* **FR-03**: The system shall allow the user to interrupt (barge-in) active TTS audio playback at any time by speaking or tapping the microphone control.

## 2. Agricultural Slot Extraction & Normalization
* **FR-04**: The NLU layer shall extract the following core profile slots from every conversational turn:
  1. `location_district` and `location_taluk` (mapped to canonical Karnataka districts/taluks).
  2. `land_area_acres` (normalized from *Ekare*, *Gunte*, *Cent*, or *Hectare* using $1\text{ Acre} = 40\text{ Gunte} = 100\text{ Cents}$ and $1\text{ Hectare} = 2.471\text{ Acres}$).
  3. `ownership_type` (`OWNED`, `LEASED_TENANT`, `JOINT_FAMILY`, `UNKNOWN`).
  4. `crops` (mapped from colloquial Kannada names to canonical crop IDs and categories: `CEREAL`, `PULSE`, `OILSEED`, `COMMERCIAL`, `HORTICULTURE`).
  5. `season` (`KHARIF` / *Mungaru*, `RABI` / *Hingaru*, `SUMMER` / *Besige*).
  6. `assistance_needs` (`INCOME_SUPPORT`, `CROP_INSURANCE`, `IRRIGATION`, `EQUIPMENT`, `SOIL_HEALTH`, `GENERAL_ALL`).
  7. `exclusion_flags` (e.g., `is_income_tax_payer`, `is_institutional_landholder`, `has_ availed_recent_subsidy`).
* **FR-05**: When a farmer updates a previously stated slot (e.g., *"ಬೆಳೆ ತೊಗರಿ ಅಲ್ಲ, ಜೋಳ ಅಂತ ಇಟ್ಟುಕೊಳ್ಳಿ"* / "Change crop from red gram to sorghum"), the system shall overwrite the slot and immediately re-run the eligibility rule engine.

## 3. Deterministic Scheme Eligibility Evaluation
* **FR-06**: The Rule Engine shall evaluate the farmer's current `FarmerProfile` against all 5 reference schemes on every turn.
* **FR-07**: For each scheme, the Rule Engine shall output one of four deterministic statuses:
  * `ELIGIBLE`: All mandatory rules satisfied and no exclusion rules triggered.
  * `POTENTIALLY_ELIGIBLE_MISSING_INFO`: No current rules violated, but 1 or more mandatory slots are `null`.
  * `INELIGIBLE`: At least one hard condition failed or an exclusion rule triggered.
  * `NOT_RELEVANT_TO_INTENT`: Filtered out only if the farmer explicitly asked for a single narrow category, though still visible in the full eligibility summary.
* **FR-08**: Specifically for **PM-KISAN (real)**, the engine shall verify cultivable land ownership (`ownership_type == OWNED` or `JOINT_FAMILY`), check exclusion criteria (income tax payer, government employee/pensioner $> ₹10,000/\text{month}$, institutional landholder), and state the benefit (`₹6,000/year` in 3 installments).
* **FR-09**: Specifically for **PMFBY (real)**, the engine shall verify season (`KHARIF`, `RABI`, `SUMMER`), crop notification status in the given district, and explain premium rates ($2\%$ Kharif, $1.5\%$ Rabi, $5\%$ Commercial/Horticultural crops).
* **FR-10**: Specifically for **Demo Micro-Irrigation Support (fictional)**, **Demo Agricultural Equipment Assistance (fictional)**, and **Demo Soil Improvement Support (fictional)**, the engine shall execute their synthetic rule trees and append a mandatory disclaimer that the scheme is a synthetic test case with no real entitlement implied.

## 4. Follow-Up Question Generation & Dialogue Management
* **FR-11**: If high-priority schemes have status `POTENTIALLY_ELIGIBLE_MISSING_INFO`, the Dialogue Manager shall select the highest-information-gain missing slot (e.g., asking for `ownership_type` or `land_area_acres` before asking secondary exclusion questions) and formulate a natural follow-up question in Kannada.
* **FR-12**: Once sufficient information is gathered, the assistant shall clearly explain in spoken Kannada:
  1. **Why** the farmer is eligible or ineligible (citing their specific land, crop, or ownership).
  2. **Benefits** offered by the scheme.
  3. **Key conditions** and cut-off awareness.
  4. **Required documents** (e.g., *Pahani*/RTC, Aadhaar linked to bank account, FRUITS ID).
  5. **Application steps** (e.g., visiting the local *Raitha Samparka Kendra* (RSK), *Grama One* center, or portal).