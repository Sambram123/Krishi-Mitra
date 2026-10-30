# Reference Dataset & Scheme Rules Catalog — Krishi Mitra

This document outlines the official 5 reference schemes mandated by the problem statement, their structured parameters, and their exact evaluation logic.

---

## 1. Scheme Definitions

### 1. PM-KISAN (Real Official Scheme)
* **Type:** Real
* **Issuing Authority:** Central Government of India
* **Purpose:** Income support for landholding farmer families.
* **Benefit:** ₹6,000 per annum paid in three 4-monthly installments of ₹2,000 directly into bank accounts via DBT.
* **Eligibility Rules:**
  - `is_landholder == True` (Owns cultivable land in their name)
  - `land_size_acres > 0.0`
* **Exclusions (Mandatory Check):**
  - Institutional landholders.
  - Farmer or family member holding or held constitutional posts.
  - Former/present Ministers, MPs, MLAs, Mayors, Chairpersons of District Panchayats.
  - Serving or retired officers/employees of Central/State Gov departments.
  - All persons who paid Income Tax in the last assessment year.
  - Professionals (Doctors, Engineers, Lawyers, CA) registered with professional councils.
* **Mandatory Documents:**
  1. Pahani / RTC (Land Ownership Record)
  2. Aadhaar Card
  3. Aadhaar-seeded Bank Account (NPCI active)

---

### 2. PMFBY (Pradhan Mantri Fasal Bima Yojana — Real Official Scheme)
* **Type:** Real
* **Issuing Authority:** Ministry of Agriculture & Farmers Welfare / Karnataka Samrakshane
* **Purpose:** Financial support and comprehensive crop risk insurance against non-preventable natural disasters.
* **Benefit:** Claim payout based on calculated yield shortfall or localized damage.
* **Eligibility Rules:**
  - `crop IN ["Ragi", "Pigeon Pea (Togari)", "Jowar", "Paddy", "Cotton", "Groundnut", "Sugarcane", "Maize"]`
  - `season IN ["Kharif", "Rabi", "Summer"]`
  - `is_notified_area == True` (Karnataka notified taluks/hoblis)
  - `risk_type IN ["Drought", "Excess Rainfall", "Pest Attack", "Flood", "Hailstorm"]`
* **Mandatory Documents:**
  1. Pahani / RTC
  2. Sowing Certificate (issued by Village Accountant / self-declaration)
  3. Bank Passbook

---

### 3. Demo Micro-Irrigation Support (Fictional / Synthetic Test Case)
* **Type:** Synthetic Demo
* **Purpose:** Synthetic test case for drip & sprinkler irrigation subsidy decision rules.
* **Benefit:**
  - Small/Marginal Farmers ($\le$ 5.0 acres): **90% subsidy**
  - Other Farmers (> 5.0 acres and $\le$ 12.5 acres): **70% subsidy**
* **Eligibility Rules:**
  - `land_size_acres >= 0.5 AND land_size_acres <= 12.5`
  - `has_water_source == True` (Borewell, Open Well, or Canal connection available)
  - `availed_drip_subsidy_last_3_years == False`
* **Disclaimer:** *Demonstration test scheme for hackathon rule validation.*
* **Mandatory Documents:**
  1. Pahani / RTC
  2. Borewell / Water Source certificate
  3. Small/Marginal Farmer Certificate (if claiming 90%)

---

### 4. Demo Agricultural Equipment Assistance (Fictional / Synthetic Test Case)
* **Type:** Synthetic Demo
* **Purpose:** Synthetic test case for farm mechanization equipment subsidy decision rules.
* **Benefit:** **50% subsidy** up to a maximum cap of **₹1,00,000** for approved agricultural implements.
* **Eligibility Rules:**
  - `land_size_acres >= 1.0`
  - `requested_equipment IN ["Power Tiller", "Rotavator", "Sprayer", "Weeder", "Small Tractor"]`
  - `dealer_is_authorized == True`
* **Disclaimer:** *Demonstration test scheme for hackathon rule validation.*
* **Mandatory Documents:**
  1. Pahani / RTC
  2. Aadhaar Card
  3. Quotation from authorized equipment dealer

---

### 5. Demo Soil Improvement Support (Fictional / Synthetic Test Case)
* **Type:** Synthetic Demo
* **Purpose:** Synthetic test case for soil health and organic enrichment incentives.
* **Benefit:** Incentive of **₹5,000 per hectare** (max 2 hectares / 5 acres) for applying green manure, gypsum, and bio-fertilizers.
* **Eligibility Rules:**
  - `has_soil_health_card == True`
  - `soil_deficiency IN ["Low Organic Carbon", "Saline", "Alkaline", "Acidic", "Micronutrient Deficient"]`
  - `land_size_acres <= 5.0`
* **Disclaimer:** *Demonstration test scheme for hackathon rule validation.*
* **Mandatory Documents:**
  1. Official Soil Health Card (SHC)
  2. Pahani / RTC
  3. Bank Account details

---

## 2. Dialectal & Colloquial Extraction Mapping

| Spoken Rural Phrase | Canonical Standard Key | Mapped Value |
| :--- | :--- | :--- |
| **ತೊಗರಿ (Togari)** | `crop` | Pigeon Pea (Red Gram) |
| **ಕಬ್ಬು (Kabbu)** | `crop` | Sugarcane |
| **ರಾಗಿ (Ragi)** | `crop` | Ragi (Finger Millet) |
| **ಜೋಳ (Jola)** | `crop` | Sorghum (Jowar) |
| **ಕುಷ್ಕಿ (Kushki) / ಒಣಭೂಮಿ** | `irrigation_type` | Rainfed / Dryland |
| **ತರಿ (Tari) / ನೀರಾವರಿ** | `irrigation_type` | Irrigated |
| **ಗುಂಟೆ (Gunta)** | `land_size` | Converts to `0.025 * guntas` acres |
| **ಹನಿ ನೀರಾವರಿ / ಡ್ರಿಪ್ (Drip)** | `assistance_intent` | Micro-Irrigation |
| **ಟಿಲ್ಲರ್ / ರೋಟವೇಟರ್** | `assistance_intent` | Agricultural Equipment |
| **ಮಣ್ಣು ಪರೀಕ್ಷೆ (Mannu Pareekshe)** | `assistance_intent` | Soil Improvement |
| **ಬೆಳೆ ಹಾನಿ / ಒಣಗಿ ಹೋತು** | `assistance_intent` | Crop Insurance (PMFBY) |
