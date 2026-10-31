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
│   ├── auth/                     # Authentication & authorization module
│   │   ├── config.py             # JWT & rate limit configuration
│   │   ├── dependencies.py       # get_current_user & require_role RBAC
│   │   ├── rate_limiter.py       # Sliding-window rate limiting per phone & IP
│   │   ├── router.py             # Phone+OTP, refresh rotation & user routes
│   │   ├── security.py           # JWT creation, HMAC hashing & OTP generation
│   │   └── sms.py                # Pluggable SMSProvider & dev ConsoleProvider
│   ├── db/                       # Database persistence & migrations
│   │   ├── alembic/              # Alembic migration revisions & environment
│   │   ├── database.py           # SQLAlchemy 2.0 engine & session factory
│   │   └── models.py             # Users, OTPCode & RefreshToken models
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

---

## 🔐 Authentication, Authorization & Security

Krishi Mitra provides a production-grade, privacy-first authentication layer:
- **Phone + OTP Login**: 6-digit OTP hashed at rest with HMAC-SHA256, 5-minute expiry, max 5 attempts.
- **Rate-Limiting**: Sliding-window rate limiter per phone number and IP address to prevent SMS abuse.
- **Short-Lived Access Tokens (15 min)**: Kept in memory by the vanilla JS frontend to mitigate XSS attacks.
- **Rotating Refresh Tokens (7 days)**: Stored in `httpOnly`, `SameSite=Lax`, `Secure` cookies with automatic compromise detection (reuse of a revoked token revokes the entire token family).
- **IDOR Protection**: Conversation sessions are bound to `user_id`; cross-user reads/writes are blocked with `403 Forbidden`.
- **Role-Based Access Control**: `require_role('admin')` dependency protects administrative metrics and routes.
- **Zero Secret Logging**: Production mode suppresses all raw phone numbers, OTP codes, and tokens.
- **Database & Migrations**: Backed by SQLAlchemy 2.0 and Alembic (default SQLite, PostgreSQL ready via `DATABASE_URL`).

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

## 🛡️ Privacy & Compliance Notice (DPDP Act 2023)

Krishi Mitra implements **Digital Personal Data Protection (DPDP Act 2023)** compliance by design:
- **No Microphone Access Without Consent**: The browser never prompts for `getUserMedia` until the farmer explicitly reviews the bilingual consent modal and clicks "Allow". Declining leaves text chat completely usable with no nagging.
- **Server-Side Consent Enforcement (`require_voice_consent`)**: Every voice turn and audio upload endpoint is gated by a server-side dependency. Without active consent for the active policy version, the server rejects the request with HTTP `403` and error code `CONSENT_REQUIRED`.
- **Transient In-Memory Audio Processing**: Audio clips are processed strictly in-memory (using `BytesIO`), routed to Sarvam AI / Groq, and discarded immediately. Raw audio is **never written to disk or database**.
- **Transcript Storage Opt-in (Default OFF)**: In-memory session history and transcripts are only saved if the farmer explicitly toggles on *"Save conversation history"*.
- **Zero Audio & Transcript Logging**: The system logs only audio payload byte lengths and transcript character counts. Raw audio bytes and transcript texts are never printed to logs.
- **Append-Only Immutable Audit Trail**: All consent grants, withdrawals, and updates are recorded as new rows in the `consents` table, preserving an immutable compliance record.
- **Right to Erasure & Immediate Withdrawal**: Farmers can withdraw voice consent at any time in the settings panel (which immediately cuts active recording and releases the microphone tracks) or click *"Delete My Data"* (`DELETE /api/me/data`) to purge all active sessions and transcripts.
- **Decision-Support Disclaimer**: Krishi Mitra is an informational decision-support tool. Final eligibility and disbursement depend on verified government records at Grama One / Raitha Samparka Kendras.
