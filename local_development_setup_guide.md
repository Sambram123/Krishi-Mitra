# Local Development & Setup Guide (SETUP)

## 1. Prerequisites
* **Python**: `3.11+`
* **Node.js**: `20+` (with `npm` or `pnpm`)
* **Docker & Docker Compose**: (Optional, for running PostgreSQL + Redis or full containerized stack)
* **API Keys**:
  * **Phase 1 (Core Agent)**: Gemini API Key (`GEMINI_API_KEY`) or OpenAI API Key for structured NLU slot extraction and Kannada response generation.
  * **Phase 2 (Voice Pipeline)**: Sarvam AI API Key (`SARVAM_API_KEY`) or Google Cloud / Azure Speech credentials for Kannada ASR (`kn-IN`) and TTS (`kn-IN`), with Web Speech API fallback built-in for zero-key browser testing.

---

## 2. Environment Configuration (`.env`)

Create a `.env` file in the root directory:

    # Core Mode Configuration
    DEFAULT_MODALITY_MODE=PHASE1_TEXT   # Switch to PHASE2_VOICE when ready
    LOG_LEVEL=INFO

    # LLM Provider (NLU Slot Extraction & Spoken Kannada NLG)
    GEMINI_API_KEY=your_gemini_api_key_here
    LLM_MODEL_NAME=gemini-2.5-flash

    # Phase 2 Voice Providers (ASR & TTS)
    VOICE_PROVIDER=SARVAM               # Options: SARVAM | GOOGLE | AZURE | BROWSER_FALLBACK
    SARVAM_API_KEY=your_sarvam_key_here
    TTS_VOICE_ID=kn-IN-sapna

    # Persistence
    DATABASE_URL=postgresql+asyncpg://krishi:krishi_pass@localhost:5432/krishi_mitra
    REDIS_URL=redis://localhost:6379/0
    USE_IN_MEMORY_STORE=true            # Set true for zero-dependency rapid hackathon run

---

## 3. Running the Project Locally

### Step 1: Start Backend (FastAPI)
    cd backend
    python -m venv .venv
    source .venv/bin/activate           # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m app.db.seed               # Loads the 5 reference schemes & Kannada lexicons
    uvicorn app.main:app --reload --port 8000

### Step 2: Run Deterministic Rule & Normalizer Tests
    cd backend
    pytest tests/ -v

### Step 3: Start Frontend (Next.js Workbench)
    cd frontend
    npm install
    npm run dev

Open `http://localhost:3000` in Chrome or Edge to access the Krishi Mitra interface and Audit Workbench.