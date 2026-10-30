# Knowledge Base & Scheme Rules Catalog — Krishi Mitra

This document outlines the curated Karnataka State and Government of India agricultural schemes, their eligibility formulas, localized aliases, and required documentation.

---

## 1. Scheme Definitions & Deterministic Logic

### Scheme 1: Raitha Siri Yojana (ರೈತ ಸಿರಿ ಯೋಜನೆ)
* **Issuing Authority:** Department of Agriculture, Government of Karnataka.
* **Objective:** Encourage minor millet cultivation (Ragi, Navane, Same, Haraka, Korale, Baragu) in rainfed tracts.
* **Financial Assistance:** Direct Benefit Transfer (DBT) of **₹10,000 per hectare** (maximum up to 2 hectares / ~5 acres).
* **Deterministic Rules:**
  - `Crop IN ["Ragi", "Foxtail Millet (Navane)", "Little Millet (Same)", "Kodo Millet (Haraka)", "Barnyard Millet", "Proso Millet"]`
  - `IrrigationType == "Rainfed" OR "Dryland"`
  - `LandSizeAcres > 0.0 AND LandSizeAcres <= 10.0`
  - `State == "Karnataka"`
* **Required Documents:**
  1. Pahani / RTC (Record of Rights, Tenancy and Crops) showing millet crop entry.
  2. Aadhaar Card linked to Mobile Number.
  3. Aadhaar-seeded Bank Account (NPCI mapping).
  4. FRUITS ID (Farmer Registration and Unified Beneficiary Information System).

---

### Scheme 2: Krishi Bhagya Yojana (ಕೃಷಿ ಭಾಗ್ಯ ಯೋಜನೆ)
* **Issuing Authority:** Government of Karnataka.
* **Objective:** Sustainable rainfed agriculture through in-situ rainwater conservation and farm ponds (*Krishi Honda*).
* **Financial Assistance:** 80% to 90% subsidy for constructing polyhouse/shade net, farm ponds, and diesel/solar pump sets (General: 80%, SC/ST: 90%).
* **Deterministic Rules:**
  - `Region IN ["Dryland", "Rainfed Taluks of Karnataka"]`
  - `LandSizeAcres >= 1.0`
  - `NeedCategory IN ["Farm Pond", "Water Storage", "Borewell Alternative", "Sprinkler", "Drip"]`
* **Required Documents:**
  1. RTC / Pahani.
  2. Caste Certificate (for 90% subsidy if SC/ST).
  3. Bank Passbook.
  4. Soil and water test certificate (optional, verified by RSK).

---

### Scheme 3: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) + Karnataka CM Kisan
* **Issuing Authority:** Central Government + Govt of Karnataka top-up.
* **Objective:** Income support to all landholding farmers' families.
* **Financial Assistance:** **₹6,000/year** (Central) + **₹4,000/year** (Karnataka State DBT top-up) = Total **₹10,000/year** in quarterly tranches.
* **Deterministic Rules:**
  - `OwnershipStatus == "Owner"` (Cultivable land in applicant's name).
  - `IsInstitutionalLandholder == False`
  - `IsIncomeTaxPayee == False`
  - `IsGovernmentEmployee == False`
* **Required Documents:**
  1. Aadhaar Card (mandatory e-KYC).
  2. RTC / Land Registry Mutation extract.
  3. Active Bank Account seeded with NPCI.

---

### Scheme 4: Pradhan Mantri Fasal Bima Yojana (PMFBY) / Karnataka Samrakshane
* **Issuing Authority:** Ministry of Agriculture & Farmers Welfare + Karnataka Agriculture Dept.
* **Objective:** Comprehensive crop insurance against non-preventable natural risks (drought, flood, pest, unseasonal rain).
* **Farmer Premium Share:**
  - Kharif Crops: 2.0% of Sum Insured.
  - Rabi Crops: 1.5% of Sum Insured.
  - Annual Commercial / Horticultural Crops: 5.0%.
* **Deterministic Rules:**
  - `SownSeason IN ["Kharif", "Rabi", "Summer"]`
  - `NotifiedCrop IN ["Paddy", "Sugarcane", "Red Gram (Togari)", "Groundnut", "Cotton", "Maize", "Ragi", "Soybean"]`
  - `RiskCategory IN ["Drought", "Excess Rainfall", "Pest Attack", "Hailstorm"]`
* **Required Documents:**
  1. Land Possession Certificate / RTC.
  2. Sowing Certificate issued by Village Accountant / Self-declaration.
  3. Bank Passbook.

---

### Scheme 5: Surya Raitha / PM-KUSUM Component B
* **Issuing Authority:** KREDL (Karnataka Renewable Energy Development Ltd) & MNRE.
* **Objective:** Installation of stand-alone Solar Powered Agriculture Pumps.
* **Subsidy:** Up to 60% capital subsidy (30% Central + 30% State).
* **Deterministic Rules:**
  - `NeedCategory IN ["Solar Pump", "Electricity Issue", "Borewell Pump", "Irrigation Power"]`
  - `HasElectricGridConnection == False OR SeekingReplacement`
  - `WaterSourceAvailable == True` (Open well or Borewell).
* **Required Documents:**
  1. RTC / Pahani.
  2. Borewell yield certificate / Water source certificate.
  3. Aadhaar and Bank Details.

---

### Scheme 6: Kisan Credit Card (KCC) & Interest Subvention Scheme
* **Issuing Authority:** NABARD & Scheduled Commercial / Grameena Banks.
* **Objective:** Short-term credit for crop cultivation at 4% effective interest (3% prompt repayment incentive).
* **Deterministic Rules:**
  - `NeedCategory IN ["Crop Loan", "Short Term Loan", "Seed/Fertilizer Purchase"]`
  - `ApplicantAge >= 18 AND ApplicantAge <= 75`
* **Required Documents:**
  1. Land Title Records (RTC / Mutation).
  2. Aadhaar & PAN / Voter ID.
  3. No Due Certificate (NDC) from local cooperative.

---

## 2. Agricultural Colloquial Lexicon & Mapping Dictionary

For natural voice understanding, the system maps localized terms into formal ontology:

| Spoken Rural Kannada (Kannada / Transliteration) | English Equivalent | Canonical Ontology Key |
| :--- | :--- | :--- |
| **ತೊಗರಿ (Togari)** / *Thogari* | Red Gram / Pigeon Pea / Arhar | `crops: ["Pigeon Pea"]` |
| **ಕಬ್ಬು (Kabbu)** | Sugarcane | `crops: ["Sugarcane"]` |
| **ರಾಗಿ (Ragi)** | Finger Millet | `crops: ["Ragi"]` |
| **ಜೋಳ (Jola / Bili Jola)** | Sorghum / Jowar | `crops: ["Jowar"]` |
| **ಹತ್ತಿ (Hatti)** | Cotton | `crops: ["Cotton"]` |
| **ಶೇಂಗಾ (Shenga) / ಕಡಲೆಕಾಯಿ** | Groundnut / Peanut | `crops: ["Groundnut"]` |
| **ಕುಷ್ಕಿ (Kushki) / ಒಣಭೂಮಿ** | Rainfed / Dryland | `irrigation: "Rainfed"` |
| **ತರಿ (Tari) / ನೀರಾವರಿ** | Wetland / Irrigated land | `irrigation: "Canal/Borewell"` |
| **ಗುಂಟೆ (Gunta)** | 1/40th of an Acre | `land_unit: 0.025 acre` |
| **ಪಹಣಿ / ಆರ್.ಟಿ.ಸಿ (Pahani / RTC)** | Land ownership document | `doc_req: "RTC"` |
| **ಬೆಳೆ ಹಾನಿ (Bele Haani)** | Crop Loss / Damage | `intent: "crop_insurance"` |
| **ಕರೆಂಟು ಬರ್ತಿಲ್ಲ (Current bartilla)** | No power for pump set | `intent: "solar_pump"` |
| **ಸಾಲ ಮನ್ನಾ / ಸಾಲ ಬೇಕು** | Loan waiver / Farm loan | `intent: "kcc_credit"` |
| **ಸಣ್ಣ ರೈತ (Sanna Raita)** | Small / Marginal Farmer (< 5 acres) | `category: "Small/Marginal"` |

---

## 3. Sample Auditable Decision Tree Example

```python
# Evaluator Logic Snippet for Raitha Siri
def evaluate_raitha_siri(farmer):
    audit = []
    is_millet = any(c in MILLET_LIST for c in farmer.crops)
    is_dryland = farmer.irrigation == "Rainfed"
    has_valid_size = 0 < farmer.land_acres <= 10.0

    if not is_millet:
        return Ineligible(reason="Raitha Siri is exclusively for minor millets (Ragi, Navane, Same).")
    
    if not is_dryland:
        audit.append("Warning: Land must be categorized as rainfed/dryland in RTC.")
    
    if has_valid_size:
        benefit_amount = min(farmer.land_acres * 4000, 10000) # In rupees
        return Eligible(
            scheme="Raitha Siri Yojana",
            benefit=f"₹{benefit_amount:,.0f} Direct Benefit Transfer",
            audit=f"Matches millet crop ({farmer.crops[0]}) on {farmer.land_acres} acres rainfed land."
        )
```
