# Data Model & Agricultural Normalization Specification (DATA_MODEL)

## 1. Farmer Profile Slot Model (`FarmerProfile`)

The `FarmerProfile` is the canonical state object maintained across all turns in a conversation session. Every slot tracks its normalized value, raw spoken phrase, confidence, and turn number when last updated.

    {
      "session_id": "sess_98a7bc65",
      "dialect_region_detected": "NORTH_KARNATAKA",
      "slots": {
        "location_district": {
          "value": "DHARWAD",
          "raw_spoken": "ಧಾರವಾಡ",
          "updated_at_turn": 1
        },
        "location_taluk": {
          "value": "HUBBALLI",
          "raw_spoken": "ಹುಬ್ಬಳ್ಳಿ ತಾಲೂಕು",
          "updated_at_turn": 1
        },
        "land_area_acres": {
          "value": 2.5,
          "raw_spoken": "ಎರಡು ಎಕರೆ ಇಪ್ಪತ್ತು ಗುಂಟೆ",
          "calculation_note": "2 Ekare + (20 Gunte / 40) = 2.5 Acres",
          "updated_at_turn": 1
        },
        "ownership_type": {
          "value": "OWNED",
          "raw_spoken": "ಸ್ವಂತ ಜಮೀನು, ಪಹಣಿ ನನ್ನ ಹೆಸರಲ್ಲೇ ಇದೆ",
          "updated_at_turn": 2
        },
        "crops": [
          {
            "crop_id": "PIGEON_PEA",
            "kannada_name": "ತೊಗರಿ",
            "category": "PULSE",
            "raw_spoken": "ತೊಗರಿ ಬೆಳೆ"
          }
        ],
        "season": {
          "value": "KHARIF",
          "raw_spoken": "ಮುಂಗಾರು ಹಂಗಾಮು",
          "updated_at_turn": 2
        },
        "assistance_needs": ["CROP_INSURANCE", "INCOME_SUPPORT"],
        "irrigation_source": {
          "value": "RAINFED",
          "raw_spoken": "ಮಳೆ ಆಶ್ರಿತ",
          "updated_at_turn": 3
        },
        "equipment_interest": null,
        "exclusion_flags": {
          "is_institutional_landholder": false,
          "pays_income_tax": false,
          "is_govt_employee_or_pensioner_above_10k": false
        }
      }
    }

---

## 2. Deterministic Land Area Normalization Formula

Farmers in Karnataka express land area using regional units (*Ekare*, *Gunte*, *Cent*, *Hectare*). The normalizer converts all inputs to canonical `land_area_acres` (float) and `land_area_hectares` (float) using:

$$\text{Acres} = \text{Ekare} + \frac{\text{Gunte}}{40} + \frac{\text{Cent}}{100} + (\text{Hectares} \times 2.47105)$$

$$\text{Hectares} = \frac{\text{Acres}}{2.47105}$$

### Farmer Category Classification by Landholding
* **Marginal Farmer (*ಅತಿ ಸಣ್ಣ ರೈತ*)**: $\text{Land} < 1.0\text{ Hectare}$ ($< 2.47\text{ Acres}$)
* **Small Farmer (*ಸಣ್ಣ ರೈತ*)**: $1.0\text{ Hectare} \le \text{Land} \le 2.0\text{ Hectares}$ ($2.47\text{ to } 4.94\text{ Acres}$)
* **Semi-Medium / Medium / Large Farmer**: $\text{Land} > 2.0\text{ Hectares}$ ($> 4.94\text{ Acres}$)

---

## 3. Reference Scheme Rule Model (`SchemeDefinition`)

Each of the 5 reference schemes in `data/schemes/schemes_catalog.json` adheres to a transparent rule structure:

### 3.1 Summary of Rules for the 5 Prototype Schemes

| Scheme ID | Real / Synthetic | Required Slots | Eligibility Rules | Key Exclusions |
| :--- | :--- | :--- | :--- | :--- |
| `PM_KISAN` | `REAL` | `ownership_type`, `land_area_acres`, `exclusion_flags.pays_income_tax` | 1. `ownership_type IN ['OWNED', 'JOINT_FAMILY']`<br>2. `land_area_acres > 0`<br>3. `pays_income_tax == false`<br>4. `is_institutional_landholder == false` | Tenant farmers without land title; income tax payers; civil servants/pensioners $> ₹10,000/\text{mo}$. |
| `PMFBY` | `REAL` | `location_district`, `crops`, `season`, `land_area_acres` | 1. `season IN ['KHARIF', 'RABI', 'SUMMER']`<br>2. `crops` contains at least 1 notified crop for the district & season<br>3. `ownership_type IN ['OWNED', 'LEASED_TENANT', 'JOINT_FAMILY']` | Non-notified crops in the selected taluk/district; enrollment after seasonal cut-off date. |
| `DEMO_MICRO_IRRIGATION` | `SYNTHETIC_DEMO` | `ownership_type`, `land_area_acres`, `crops`, `irrigation_source` | 1. `ownership_type IN ['OWNED', 'JOINT_FAMILY']`<br>2. `0.25 <= land_area_acres <= 12.35` ($\le 5\text{ Ha}$)<br>3. `irrigation_source IN ['BOREWELL', 'OPEN_WELL', 'CANAL', 'FARM_POND']` | Purely rainfed land without water source (`irrigation_source == 'RAINFED'`); subsidy claimed on same plot within last 7 years. |
| `DEMO_AGRI_EQUIPMENT` | `SYNTHETIC_DEMO` | `ownership_type`, `land_area_acres`, `assistance_needs` | 1. `ownership_type IN ['OWNED', 'JOINT_FAMILY']`<br>2. `land_area_acres >= 0.5`<br>3. `assistance_needs CONTAINS 'EQUIPMENT'` (or general query) | Already availed same equipment category subsidy in last 5 years. |
| `DEMO_SOIL_IMPROVEMENT` | `SYNTHETIC_DEMO` | `location_district`, `land_area_acres`, `crops`, `ownership_type` | 1. `ownership_type IN ['OWNED', 'LEASED_TENANT', 'JOINT_FAMILY']`<br>2. `land_area_acres >= 0.1` | None (broadly accessible fallback/complementary recommendation path for soil testing, gypsum, and green manure). |

---

## 4. Eligibility Audit Trace Output (`EligibilityAuditResult`)

Every turn produces an array of `EligibilityAuditResult` objects—one per scheme:

    {
      "scheme_id": "PM_KISAN",
      "scheme_name_kn": "ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (PM-KISAN)",
      "is_synthetic": false,
      "status": "ELIGIBLE",
      "passed_rules": [
        {
          "rule_id": "PMK_R1",
          "description_kn": "ರೈತರು ತಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಕೃಷಿ ಭೂಮಿಯನ್ನು ಹೊಂದಿದ್ದಾರೆ (ಸ್ವಂತ ಜಮೀನು: 2.5 ಎಕರೆ).",
          "slot_used": "ownership_type",
          "actual_value": "OWNED"
        },
        {
          "rule_id": "PMK_R2",
          "description_kn": "ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿದಾರರಲ್ಲ.",
          "slot_used": "exclusion_flags.pays_income_tax",
          "actual_value": false
        }
      ],
      "failed_rules": [],
      "missing_slots": [],
      "spoken_summary_kn": "ನೀವು 2.5 ಎಕರೆ ಸ್ವಂತ ಜಮೀನು ಹೊಂದಿರುವುದರಿಂದ ಪಿಎಂ-ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಅರ್ಹರಾಗಿದ್ದೀರಿ. ಇದರಡಿ ವರ್ಷಕ್ಕೆ 6,000 ರೂಪಾಯಿ ಆರ್ಥಿಕ ನೆರವು ಸಿಗುತ್ತದೆ."
    }