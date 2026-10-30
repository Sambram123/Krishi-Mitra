# Acceptance Test Suite (ACCEPTANCE_TESTS)

These end-to-end test scenarios validate all six hackathon objectives across both Phase 1 (Text) and Phase 2 (Voice).

---

## Scenario AT-01: North Karnataka Dialect, Land Unit Conversion (*Gunte*), and Multi-Scheme Match
* **Objective Tested**: Regional accent/vocabulary, land conversion, rule evaluation, and missing-slot follow-up.
* **Turn 1 (Farmer - Dharwad Kannada)**:
  *"ನಮಸ್ಕಾರ ರೀ, ನಂದು ಧಾರವಾಡ ತಾಲೂಕು. ನನ್ನ ಕಡೆ ಎರಡು ಎಕರೆ ಇಪ್ಪತ್ತು ಗುಂಟೆ ಸ್ವಂತ ಹೊಲ ಐತಿ. ಈ ಸಲ ಮುಂಗಾರಿಗೆ ತೊಗರಿ ಬಿತ್ತೇನಿ."*
* **Expected Slot Extraction**:
  * `location_district`: `"DHARWAD"`
  * `land_area_acres`: `$2.5$` ($2 + \frac{20}{40}$)
  * `ownership_type`: `"OWNED"`
  * `season`: `"KHARIF"`
  * `crops`: `["PIGEON_PEA"]`
* **Expected Rule Engine Output**:
  * `PMFBY`: `ELIGIBLE` (Dharwad + Kharif + Pigeon Pea notified)
  * `PM_KISAN`: `POTENTIALLY_ELIGIBLE_MISSING_INFO` (Needs confirmation of tax/institutional exclusion)
  * `DEMO_SOIL_IMPROVEMENT`: `ELIGIBLE`
* **Expected Assistant Action**: Confirms `PMFBY` eligibility for $2.5\text{ Acres}$ of *Togari*, mentions `PM-KISAN` potential, and asks if the farmer pays income tax or needs irrigation/equipment support.

---

## Scenario AT-02: Code-Mixed English & Kannada for Micro-Irrigation & Equipment (Synthetic Schemes)
* **Objective Tested**: Code-mixing, follow-up slot gathering (`irrigation_source`), and synthetic scheme disclaimer.
* **Turn 1 (Farmer - Mandya Code-Mixed)**:
  *"Sir, Mandya district nalli 1.5 acre ಸ್ವಂತ land ide. Tomato ಮತ್ತೆ ತೆಂಗು ಬೆಳಿತೀನಿ. Drip irrigation ಮತ್ತೆ weed cutter machine ge subsidy ಬೇಕಿತ್ತು."*
* **Expected Assistant Follow-up**: Extracts `location_district: MANDYA`, `land_area_acres: 1.5`, `ownership_type: OWNED`, `crops: [TOMATO, COCONUT]`, `assistance_needs: [IRRIGATION, EQUIPMENT]`. Sees `DEMO_MICRO_IRRIGATION` is missing `irrigation_source` (water availability). Asks in Kannada: *"ಹನಿ ನೀರಾವರಿ (Drip irrigation) ಅಳವಡಿಸಲು ನಿಮ್ಮ ಜಮೀನಿನಲ್ಲಿ ಬೋರ್‌ವೆಲ್ ಅಥವಾ ಬಾವಿ ನೀರಿನ ವ್ಯವಸ್ಥೆ ಇದೆಯೇ?"*
* **Turn 2 (Farmer)**:
  *"ಹೌದು, ಬೋರ್‌ವೆಲ್ ಇದೆ."*
* **Expected Result**: Both `DEMO_MICRO_IRRIGATION` and `DEMO_AGRI_EQUIPMENT` evaluate to `ELIGIBLE` with explicit spoken and visual confirmation that these two are prototype demonstration schemes (`[DEMO / SYNTHETIC]`), alongside real `PM-KISAN`.

---

## Scenario AT-03: Tenant Farmer Exclusion & Transparent Explanation
* **Objective Tested**: Auditable exclusion rules and helpful alternative routing.
* **Turn 1 (Farmer)**:
  *"ನಾನು ಶಿವಮೊಗ್ಗದಲ್ಲಿ 3 ಎಕರೆ ಗುತ್ತಿಗೆ (ಬಾಡಿಗೆ) ಜಮೀನು ಮಾಡ್ತಾ ಇದ್ದೀನಿ. ಮುಂಗಾರಿನಲ್ಲಿ ಭತ್ತ ಬೆಳಿತೀನಿ. ನನಗೆ ಪಿಎಂ-ಕಿಸಾನ್ ಹಣ ಬರುತ್ತಾ?"*
* **Expected Slot Extraction**: `ownership_type: "LEASED_TENANT"`, `land_area_acres: 3.0`, `crops: ["PADDY"]`, `season: "KHARIF"`.
* **Expected Rule Engine Output**:
  * `PM_KISAN`: `INELIGIBLE` (Failed rule: Land must be held in farmer's own/family name in *Pahani*/RTC).
  * `PMFBY`: `ELIGIBLE` (Subject to tenant cultivation proof/notification).
  * `DEMO_SOIL_IMPROVEMENT`: `ELIGIBLE`.
* **Expected Spoken Explanation**: Respectfully explains in Kannada *why* `PM-KISAN` requires land ownership (*ಸ್ವಂತ ಪಹಣಿ*) while highlighting that they can still explore `PMFBY` crop insurance for their paddy crop and `Demo Soil Improvement Support`.

---

## Scenario AT-04: Multi-Turn Context Retention for Documents & Application Steps
* **Objective Tested**: Retaining context across follow-up questions in the same session.
* **Turn 3 (Farmer, continuing from AT-01)**:
  *"ಸರಿ, ಆ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆಗೆ ಅರ್ಜಿ ಹಾಕೋಕೆ ಏನೇನು ಡಾಕ್ಯುಮೆಂಟ್ಸ್ ತಗೊಂಡು ಹೋಗ್ಬೇಕು? ಎಲ್ಲಿ ಹೋಗ್ಬೇಕು?"*
* **Expected Result**: Without asking the farmer for their district or crop again, Krishi Mitra references their Dharwad *Togari* crop from Turn 1 and lists the exact required documents in spoken Kannada (*ಪಹಣಿ ಪತ್ರ / RTC*, *ಬೆಳೆ ಬಿತ್ತನೆ ದೃಢೀಕರಣ ಪತ್ರ*, *ಆಧಾರ್ ಕಾರ್ಡ್*, *ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್*, *ಫ್ರೂಟ್ಸ್ ಐಡಿ*) and directs them to their local *Raitha Samparka Kendra*, bank, or *Grama One* center before the seasonal cut-off date.