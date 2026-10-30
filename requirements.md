# System & Technical Requirements Specification — Krishi Mitra

This document specifies the exact technical dependencies, interface contracts, environmental requirements, and error-handling protocols for Krishi Mitra.

---

## 1. System Requirements & Interfaces

### 1.1 Audio Ingestion & Acoustic Specifications
* **Audio Format:** Opus / WebM / Linear PCM 16-bit.
* **Sampling Rate:** Minimum 16 kHz (recommended 44.1 kHz client capture downsampled to 16 kHz mono).
* **VAD (Voice Activity Detection):**
  - Web Audio API / Silero VAD on browser client.
  - Silence threshold: 900ms of continuous silence triggers auto-submission.
  - Max utterance limit: 30 seconds per turn.

### 1.2 Entity Extraction Data Schema
The NLP layer must parse Kannada dialogue into this standardized JSON contract:

```typescript
interface FarmerAgriculturalProfile {
  session_id: string;
  language: "kn-IN";
  dialect_region?: "North_Karnataka" | "Old_Mysore" | "Coastal" | "General";
  district?: string;
  taluk?: string;
  land_size: {
    value: number;
    unit: "acre" | "gunta" | "hectare";
    normalized_acres: number; // 1 gunta = 0.025 acre, 1 hectare = 2.471 acres
  };
  ownership_type: "Owner" | "Tenant" | "Joint Family" | "Unknown";
  crops: Array<{
    local_name_kn: string; // e.g., "ತೊಗರಿ"
    standard_name_en: string; // e.g., "Pigeon Pea"
    season?: "Kharif" | "Rabi" | "Summer";
  }>;
  irrigation_source: "Rainfed" | "Borewell" | "Canal" | "Open Well" | "None";
  farmer_category?: "Marginal (<2.5 acres)" | "Small (2.5-5 acres)" | "Large (>5 acres)";
  assistance_intent: "scheme_discovery" | "crop_loss_compensation" | "solar_pump" | "loan_waiver" | "fertilizer_seed_subsidy" | "general_inquiry";
  missing_required_slots: Array<"land_size" | "crops" | "irrigation_source" | "district">;
}
```

---

## 2. Auditable Scheme Evaluation Engine Contract

The Rule Engine operates deterministically on the schema above without calling any external LLM:

```typescript
interface SchemeEvaluationResult {
  scheme_id: string;
  scheme_name_kn: string;
  scheme_name_en: string;
  department: string;
  status: "ELIGIBLE" | "CONDITIONALLY_ELIGIBLE" | "INELIGIBLE";
  estimated_benefit: {
    type: "Direct_Cash_Transfer" | "Subsidy_Percentage" | "Insurance_Payout" | "Low_Interest_Loan";
    amount_in_inr?: number;
    description_kn: string;
  };
  audit_trail: {
    rule_evaluated: string;
    criteria_matched: string[];
    criteria_failed: string[];
    official_gazette_ref: string;
  };
  required_documents: Array<{
    document_name_kn: string;
    document_name_en: string;
    is_mandatory: boolean;
    how_to_obtain_kn: string;
  }>;
  application_channels: Array<"Grama One" | "Raitha Samparka Kendra (RSK)" | "Seva Sindhu Online" | "Samrakshane Portal">;
}
```

---

## 3. Recommended Technology Package List

### Backend Dependencies (`requirements.txt`)
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
python-multipart>=0.0.9
google-genai>=0.1.0        # For Gemini 2.5 Flash slot extraction
requests>=2.31.0           # For Sarvam AI / Bhashini API calls
soundfile>=0.12.1
pydub>=0.25.1
python-dotenv>=1.0.1
aiofiles>=23.2.1
```

### Frontend Dependencies (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.364.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.2"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.1",
    "vite": "^5.2.0"
  }
}
```

---

## 4. Error Handling & Edge Cases

| Edge Case | Failure Mode | Mitigation Strategy |
| :--- | :--- | :--- |
| **Heavy Wind / Tractor Noise** | ASR produces gibberish or zero tokens. | Detect low confidence score (< 0.4); respond with polite audio nudge: *"ಕ್ಷಮಿಸಿ, ಧ್ವನಿ ಸ್ಪಷ್ಟವಾಗಿ ಕೇಳಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಇನ್ನೊಮ್ಮೆ ಹೇಳಿ."* |
| **Mixed English/Kannada Jargon** | Example: *"Nanage borewell ge loan subsidy bekittu"*. | Few-shot system prompt teaches LLM to map "borewell", "subsidy", "loan" to Kannada agricultural context. |
| **Incomplete Land Information** | Farmer mentions crop but not land size. | Rule engine tags `missing_required_slots: ["land_size"]`. Dialogue manager generates follow-up question in spoken Kannada. |
| **Tenant Farmer (No RTC in own name)** | Ineligible for land-owner DBT like PM-KISAN. | Engine detects `ownership_type == "Tenant"`, filters out owner-only schemes, redirects to tenant-applicable schemes (e.g., PMFBY via tenancy certificate). |
| **API Rate Limits / Outage** | Third-party ASR or TTS latency spikes. | Automatic fallback to secondary provider or pre-rendered Kannada audio templates for common replies. |
