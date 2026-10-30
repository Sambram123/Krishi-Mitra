# Reference Dataset & Free Open-Source Architecture Research

This document analyzes the exact reference dataset specified by the hackathon problem statement, how to structure it cleanly, and how to utilize **100% free, high-performance, and verifiable tools and APIs** across the 3 phased milestones.

---

## 1. Deep Dive: Hackathon Reference Dataset Analysis

The hackathon guidelines mandate a hybrid test dataset of **2 Real Official Schemes** and **3 Synthetic/Fictional Benchmark Schemes**:

```
+--------------------------------------------------+---------------------------------------------------------------------------------+
| Scheme Name                                      | Use in the Prototype                                                            |
+--------------------------------------------------+---------------------------------------------------------------------------------+
| 1. PM-KISAN (real)                               | Income assistance for eligible landholding farmer families; verify official      |
|                                                  | exclusions and enrollment requirements.                                         |
| 2. PMFBY (real)                                  | Crop insurance subject to crop, notified area, season, and applicable gov rules.|
| 3. Demo Micro-Irrigation Support (fictional)     | Synthetic test case for drip irrigation support; no real entitlement implied.    |
| 4. Demo Agricultural Equipment Assistance (fict) | Synthetic test case for equipment subsidy decision rules.                       |
| 5. Demo Soil Improvement Support (fictional)     | Synthetic test case for additional rule-based recommendation paths.             |
+--------------------------------------------------+---------------------------------------------------------------------------------+
```

### Why Did the Organizers Include Fictional / Synthetic Schemes?
1. **Rule Engine Robustness Testing:** Judges use synthetic schemes to test if your rule engine actually evaluates *arbitrary, strict rule branches* or if your LLM is merely regurgitating web-scraped real-world PM-KISAN summaries.
2. **Exclusion / Boundary Condition Auditing:** Fictional schemes allow edge-case testing (e.g., specific drip pipe diameter limits, soil pH ranges, or tractor HP brackets) without getting caught up in evolving real-world gazette debates.
3. **Guardrails & Disclaimer Validation:** Demonstrates ethical AI—your assistant must explicitly signal: *"This is a demonstration scheme for testing eligibility logic"*.

---

## 2. Proper Structural Modeling of the Dataset

We structure this dataset in a clean, versioned, machine-readable JSON schema (`data/schemes_dataset.json`). Each scheme contains:
- `id`: Unique slug.
- `type`: `"real"` vs `"synthetic_demo"`.
- `eligibility_rules`: Strict machine-evaluable boolean conditions.
- `official_exclusions`: Hard disqualifiers.
- `required_documents`: Mandatory and optional proofs.
- `kannada_metadata`: Pre-translated names, benefit summaries, and conversational explanation templates.

### Canonical Schema Representation (`data/schemes_dataset.json`):

```json
{
  "schemes": [
    {
      "id": "pm_kisan",
      "type": "real",
      "name_en": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
      "name_kn": "ಪಿಎಂ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ",
      "category": "Income Support",
      "benefit": {
        "amount_inr": 6000,
        "frequency": "annual_3_installments",
        "description_kn": "ವರ್ಷಕ್ಕೆ ₹6,000 ಮೂರು ಕಂತುಗಳಲ್ಲಿ (ಪ್ರತಿ ಕಂತಿಗೆ ₹2,000) ನೇರ ಬ್ಯಾಂಕ್ ವರ್ಗಾವಣೆ."
      },
      "eligibility_rules": {
        "is_landholder": true,
        "min_acres": 0.01,
        "max_acres": null,
        "required_crops": []
      },
      "exclusions": [
        "institutional_landholders",
        "holding_constitutional_posts",
        "income_tax_payee",
        "retired_pensioners_above_10000"
      ],
      "required_documents": [
        {"name_kn": "ಆಧಾರ್ ಕಾರ್ಡ್ (Aadhaar)", "mandatory": true},
        {"name_kn": "ಪಹಣಿ / ಆರ್.ಟಿ.ಸಿ (RTC / Pahani)", "mandatory": true},
        {"name_kn": "ಆಧಾರ್ ಲಿಂಕ್ ಆದ ಬ್ಯಾಂಕ್ ಖಾತೆ (NPCI seeded)", "mandatory": true}
      ]
    },
    {
      "id": "pmfby",
      "type": "real",
      "name_en": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
      "name_kn": "ಕರ್ನಾಟಕ ಸಂರಕ್ಷಣೆ - ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ",
      "category": "Crop Insurance",
      "benefit": {
        "description_kn": "ಬರ, ಅಕಾಲಿಕ ಮಳೆ ಅಥವಾ ಕೀಟಬಾಧೆಯಿಂದ ಬೆಳೆ ನಷ್ಟವಾದರೆ ವಿಮಾ ರಕ್ಷಣೆ ಮತ್ತು ಆರ್ಥಿಕ ಪರಿಹಾರ."
      },
      "eligibility_rules": {
        "seasons": ["Kharif", "Rabi", "Summer"],
        "notified_crops": ["Ragi", "Pigeon Pea (Togari)", "Jowar", "Paddy", "Cotton", "Groundnut", "Sugarcane"],
        "risk_types": ["Drought", "Excess Rain", "Pest", "Localized Calamity"]
      },
      "exclusions": [
        "unnotified_crops",
        "post_harvest_loss_after_14_days"
      ],
      "required_documents": [
        {"name_kn": "ಪಹಣಿ / ಆರ್.ಟಿ.ಸಿ (RTC)", "mandatory": true},
        {"name_kn": "ಬಿತ್ತನೆ ದೃಢೀಕರಣ ಪತ್ರ (Sowing Certificate)", "mandatory": true},
        {"name_kn": "ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್", "mandatory": true}
      ]
    },
    {
      "id": "demo_micro_irrigation",
      "type": "synthetic_demo",
      "name_en": "Demo Micro-Irrigation Support",
      "name_kn": "ಡೆಮೊ ಸೂಕ್ಷ್ಮ ನೀರಾವರಿ (ಹನಿ ನೀರಾವರಿ) ಯೋಜನೆ",
      "category": "Irrigation Infrastructure",
      "disclaimer_kn": "ಇದು ಪ್ರಾಯೋಗಿಕ ಪರೀಕ್ಷಾ ಯೋಜನೆ (ಡೆಮೊ).",
      "benefit": {
        "subsidy_percentage": {
          "small_marginal_farmer": 90,
          "other_farmers": 70
        },
        "description_kn": "ಹನಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಉಪಕರಣಗಳಿಗೆ ಶೇಕಡಾ 70 ರಿಂದ 90 ರವರೆಗೆ ಸಬ್ಸಿಡಿ."
      },
      "eligibility_rules": {
        "min_acres": 0.5,
        "max_acres": 12.5,
        "has_water_source": true,
        "preferred_irrigation": ["Borewell", "Open Well", "Canal"]
      },
      "exclusions": [
        "availed_drip_subsidy_in_last_3_years",
        "no_existing_water_source"
      ],
      "required_documents": [
        {"name_kn": "ಪಹಣಿ / ಆರ್.ಟಿ.ಸಿ (RTC)", "mandatory": true},
        {"name_kn": "ಬೋರ್ವೆಲ್ / ನೀರಿನ ಮೂಲ ಪ್ರಮಾಣಪತ್ರ", "mandatory": true},
        {"name_kn": "ಸಣ್ಣ/ಅತಿ ಸಣ್ಣ ರೈತರ ಪ್ರಮಾಣಪತ್ರ (ಅನ್ವಯಿಸಿದರೆ)", "mandatory": false}
      ]
    },
    {
      "id": "demo_agri_equipment",
      "type": "synthetic_demo",
      "name_en": "Demo Agricultural Equipment Assistance",
      "name_kn": "ಡೆಮೊ ಕೃಷಿ ಯಂತ್ರೋಪಕರಣ ಸಹಾಯ ಯೋಜನೆ",
      "category": "Farm Mechanization",
      "disclaimer_kn": "ಇದು ಪ್ರಾಯೋಗಿಕ ಪರೀಕ್ಷಾ ಯೋಜನೆ (ಡೆಮೊ).",
      "benefit": {
        "subsidy_percentage": 50,
        "max_subsidy_inr": 100000,
        "description_kn": "ಟ್ರ್ಯಾಕ್ಟರ್, ಟಿಲ್ಲರ್ ಮತ್ತು ಕಳೆ ಕೀಳುವ ಯಂತ್ರಗಳ ಖರೀದಿಗೆ ಗರಿಷ್ಠ ₹1,00,000 ವರೆಗೆ ಶೇಕಡಾ 50 ಸಬ್ಸಿಡಿ."
      },
      "eligibility_rules": {
        "min_acres": 1.0,
        "max_acres": 25.0,
        "target_equipment": ["Power Tiller", "Rotavator", "Sprayer", "Tractor (Small)"]
      },
      "exclusions": [
        "purchased_without_department_approval",
        "non_registered_implement_dealer"
      ],
      "required_documents": [
        {"name_kn": "ಪಹಣಿ / RTC", "mandatory": true},
        {"name_kn": "ಆಧಾರ್ ಕಾರ್ಡ್", "mandatory": true},
        {"name_kn": "ಯಂತ್ರೋಪಕರಣಗಳ ಅಧಿಕೃತ ಕೊಟೇಶನ್ (Quotation)", "mandatory": true}
      ]
    },
    {
      "id": "demo_soil_improvement",
      "type": "synthetic_demo",
      "name_en": "Demo Soil Improvement Support",
      "name_kn": "ಡೆಮೊ ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಫಲವತ್ತತೆ ಯೋಜನೆ",
      "category": "Soil Health & Organic Farming",
      "disclaimer_kn": "ಇದು ಪ್ರಾಯೋಗಿಕ ಪರೀಕ್ಷಾ ಯೋಜನೆ (ಡೆಮೊ).",
      "benefit": {
        "amount_inr": 5000,
        "description_kn": "ಹಸಿರೆಲೆ ಗೊಬ್ಬರ, ಜಿಪ್ಸಮ್ ಮತ್ತು ಜೈವಿಕ ಗೊಬ್ಬರ ಖರೀದಿಗೆ ಹೆಕ್ಟೇರಿಗೆ ₹5,000 ಪ್ರೋತ್ಸಾಹಧನ."
      },
      "eligibility_rules": {
        "has_soil_health_card": true,
        "soil_deficiencies": ["Low Organic Carbon", "Saline", "Alkaline", "Acidic"],
        "max_acres": 5.0
      },
      "exclusions": [
        "commercial_polyhouse_farms"
      ],
      "required_documents": [
        {"name_kn": "ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ (Soil Health Card)", "mandatory": true},
        {"name_kn": "ಪಹಣಿ / RTC", "mandatory": true}
      ]
    }
  ]
}
```

---

## 3. How to Use Free & Open-Source Tools Across the 3 Milestones

You requested to build the system step-by-step:
1. **Prototype 1:** Text-to-Text Conversational Prototype
2. **Prototype 2:** Voice Output Prototype (Text in $\rightarrow$ Kannada Voice + Text out)
3. **Prototype 3:** Full AI Application (Voice in $\rightarrow$ Dialect NLU $\rightarrow$ Rule Engine $\rightarrow$ Voice + Visual Cards out)

Here is the exact zero-cost, high-performance toolchain:

### Milestone 1: Text-to-Text Prototype (100% Free)
* **LLM Engine:**
  - **Google Gemini 2.5 Flash** (via Google AI Studio free tier: 15 RPM, 1 million TPM free).
  - **Fallback / Local:** **Ollama** running `qwen2.5:7b` or `llama3.2:3b` completely free and offline on local CPU/GPU.
* **Extraction Strategy:**
  - Few-shot structured prompting returning strict Pydantic JSON.
  - Zero hallucination by passing extracted slots into our local deterministic `rules_engine.py`.
* **Interface:**
  - Interactive Terminal CLI (`python test_text_chat.py`) and lightweight Streamlit / React text playground.

### Milestone 2: Voice Output Prototype (Text In $\rightarrow$ Spoken Kannada Out)
* **Kannada TTS Options (Free Tier):**
  - **Sarvam AI (Bulbul TTS):** Generous free sign-up credits (thousands of free characters), producing the most natural rural Indian-accented Kannada cadence.
  - **Google Cloud TTS (`kn-IN-Neural2-A` / `kn-IN-Standard-A`):** Free tier offers 1,000,000 characters per month free.
  - **Edge-TTS (`kn-IN-GaganNeural` / `kn-IN-SapnaNeural`):** Completely **100% FREE, no API key required**, leverages Microsoft Edge's high-quality neural Kannada speech synthesizer via Python `edge-tts`.
* **Testing Tool:** Script `test_tts_output.py` that receives farmer profile in text, runs rules, and plays audio output through speaker.

### Milestone 3: Full Voice-First AI Application (Voice In $\rightarrow$ Voice + UI Out)
* **Kannada Speech Recognition (ASR):**
  - **Sarvam AI (Saaras ASR):** Specifically trained on Indian accents and code-mixed Kannada.
  - **Groq Cloud (Whisper Large v3):** Free tier with extreme sub-second latency (<300ms) with Kannada agricultural prompt conditioning (`"ತೊಗರಿ, ರಾಗಿ, ಕುಷ್ಕಿ, ಪಹಣಿ, ಎಕರೆ, ಬೋರ್ವೆಲ್"`).
* **Frontend:**
  - React + Tailwind with Web Audio API for real-time waveform visualizers and microphone capture.
