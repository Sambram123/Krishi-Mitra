# 🌾 Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ)

> **Context-Aware Agricultural Scheme Intelligence for Karnataka Farmers**  
> *Deterministic Rule Engine + Kannada Conversational NLU + Auditable Benefits Evaluation*

---

## 📖 Overview

**Krishi Mitra** is an intelligent, bilingual (Kannada & English) agricultural decision-support platform designed to help farmers in Karnataka identify government schemes they are eligible for.

It bridges the information gap between complex government gazette notifications and rural farmers through:
- **Deterministic Rules Engine**: Completely auditable, transparent rule evaluation (PM-KISAN, PMFBY, and benchmark schemes) with exact pass/fail reasons.
- **Smart Context-Aware CLI**: Interactive terminal questionnaires that auto-suggest intelligent defaults based on Karnataka agro-climatic zones, soil types, and crop calendars.
- **Groq Chat**: Supports Kannada and English agricultural questions, with session context and deterministic scheme screening.
- **Sarvam Voice**: Records microphone audio in the browser, transcribes Kannada/English speech, and returns generated speech.
- **Web Application & Voice UI**: High-contrast, mobile-friendly interface with audio visualizer, chat interface, and live scheme eligibility cards.

---

## ⚡ Quickstart: Commands to Run the Project

### 1. Prerequisites & Environment Setup

Ensure you have **Python 3.10+** installed.

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/Sambram123/Krishi-Mitra.git
cd Krishi-Mitra

# Optional: Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root by copying the template:

```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

Open `.env` and configure the web chat providers:
```ini
# Required for natural-language web chat
GROQ_API_KEY=your_groq_api_key_here

# Required for voice transcription and spoken responses
SARVAM_API_KEY=your_sarvam_api_key_here

# Optional: legacy NLU/CLI provider
NLU_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
# Optional local fallback for legacy NLU/CLI tools
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

Text chat uses a local guided response if `GROQ_API_KEY` is not configured. Voice chat requires `SARVAM_API_KEY`; speech generation also uses Groq when available.

---

## 🚀 How to Run

### 🌐 Mode 1: Web Application & API Server (Recommended)

Starts the FastAPI server serving both the REST API and the responsive web frontend:

```bash
# Run directly with Python:
python backend/server.py

# Or run using Uvicorn with auto-reload:
uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

Once running, access the web pages in your browser:
- **Main Web Interface**: [http://localhost:8000](http://localhost:8000)
- **Interactive Chat Assistant**: [http://localhost:8000/chat](http://localhost:8000/chat)
- **Stitch Design UI Prototype**: [http://localhost:8000/stitch](http://localhost:8000/stitch)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 💻 Mode 2: Smart Guided Terminal CLI

Interactive questionnaire with smart defaults tailored to Karnataka's agro-climatic zones (Mandya, Kalaburagi, Dharwad, Belagavi, etc.):

```bash
python run_cli.py
```
> **Tip:** You can simply press <kbd>Enter</kbd> on questions to accept the pre-calculated regional smart defaults.

---

### 🗣️ Mode 3: Natural Language Kannada CLI

Test the legacy conversational NLU tools in Kannada with slot filling and eligibility evaluation:

```bash
# Interactive conversation loop:
python cli_chat_prototype.py

# Non-interactive automated benchmark test:
python cli_chat_prototype.py --demo-benchmark
```

---

### 🧪 Mode 4: Run the Automated Test Suite

Run the full pytest suite (rules engine, NLU, dialogue state manager, and API endpoints):

```bash
python -m pytest backend
```

---

## 📂 Project Structure

```text
Krishi-Mitra/
├── backend/                      # Backend application package
│   ├── conversation/             # Multi-turn dialogue management & state tracking
│   │   ├── dialogue.py           # Dialogue orchestration
│   │   └── state.py              # Conversation state & slot tracking
│   ├── nlu/                      # Natural language understanding
│   │   ├── extractor.py          # Slot & intent extraction
│   │   ├── normalize.py          # Kannada unit & term normalization
│   │   ├── prompts.py            # Zero-hallucination extraction prompts
│   │   ├── providers/            # LLM providers (Gemini, Ollama)
│   │   └── schemas.py            # Pydantic schemas for extracted data
│   ├── rules_engine.py           # Deterministic scheme eligibility engine
│   ├── server.py                 # FastAPI application & static file server
│   ├── test_rules.py             # Scheme evaluation unit tests
│   └── tests/                    # Integration & API tests
│
├── run_cli.py                    # Interactive terminal questionnaire with smart defaults
├── cli_chat_prototype.py         # Conversational terminal interface (Kannada NLU)
├── index.html                    # Main web dashboard & voice interaction UI
├── chat.html                     # Web conversational chat interface
├── stitch_design.html            # High-fidelity prototype design
├── assets/                       # Static media assets (icons, styles, audio)
│
├── requirements.txt              # Python package dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Project documentation & run guide
```

---

## 📋 Evaluated Schemes Benchmark

| Scheme ID | Scheme Name | Type | Key Benefit |
| :--- | :--- | :--- | :--- |
| `pm_kisan` | **PM-KISAN** (Pradhan Mantri Kisan Samman Nidhi) | Government programme | ₹6,000 / year via DBT; exclusions and official beneficiary status must be verified |
| `pmfby` | **PMFBY** (Karnataka Samrakshane / Crop Insurance) | Government programme | Insurance support for notified crop loss; enrolment and local notification must be verified |
| `pmksy_pdmc` | **PMKSY - Per Drop More Crop** | Government programme | Micro-irrigation support; current Karnataka rates and criteria require confirmation |
| `smam` | **Sub-Mission on Agricultural Mechanization (SMAM)** | Government programme | Agricultural machinery support; current equipment list, rates, and funds require confirmation |
| `soil_health_card` | **Soil Health Card Programme** | Government programme | Soil testing and nutrient recommendations; not a cash-subsidy programme |

---

## 🛡️ Privacy & Compliance Notice

- **DPDP Act (2023) Alignment**: Data minimisation principles are adhered to. Session data is stored in memory and not permanently retained without explicit user authorization.
- **Decision-Support Disclaimer**: Krishi Mitra is an informational decision-support tool. Final eligibility and disbursement depend on verified government verification at Grama One / Raitha Samparka Kendras.
