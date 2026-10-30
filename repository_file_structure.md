# Project File Structure (FILE_STRUCTURE)

The Krishi Mitra repository is organized as a clean, modular monorepo supporting both Phase 1 (Core Agent + Web Workbench) and Phase 2 (Voice Pipeline).

    krishi-mitra/
    ├── docs/                                  # Complete Project Documentation Suite
    │   ├── ARCHITECTURE.md
    │   ├── PLAN.md
    │   ├── PRD.md
    │   ├── REQUIREMENTS.md
    │   ├── FUNCTIONAL_REQUIREMENTS.md
    │   ├── NON_FUNCTIONAL_REQUIREMENTS.md
    │   ├── SCOPE.md
    │   ├── DATA_MODEL.md
    │   ├── DATABASE.md
    │   ├── API_SPEC.md
    │   ├── DOCUMENT_MANAGEMENT.md
    │   ├── DESIGN_SYSTEM.md
    │   ├── UI_UX.md
    │   ├── WEB_UX.md
    │   ├── DECISIONS.md
    │   ├── PERFORMANCE.md
    │   ├── QUALITY_GATE.md
    │   ├── ACCEPTANCE_TESTS.md
    │   ├── SETUP.md
    │   └── DEPLOYMENT_AND_OPERATIONS.md
    │
    ├── data/                                  # Auditable Knowledge Base & Lexicons
    │   ├── schemes/
    │   │   ├── schemes_catalog.json           # Master rule definitions for the 5 schemes
    │   │   └── documents_master.json          # KYC/Land document metadata (RTC, FRUITS, etc.)
    │   ├── lexicons/
    │   │   ├── kannada_crops.json             # Regional crop names -> Canonical Crop IDs
    │   │   ├── karnataka_locations.json       # Districts, taluks, agro-climatic zones
    │   │   └── units_and_seasons.json         # Gunte/Ekare/Mungaru/Hingaru mappings
    │   └── test_personas/
    │       └── sample_conversations.json      # Dialect test scripts for Phase 1 & Phase 2
    │
    ├── backend/                               # FastAPI Python Backend
    │   ├── app/
    │   │   ├── main.py                        # FastAPI entry point & CORS/WebSocket setup
    │   │   ├── config.py                      # Environment & provider configuration
    │   │   ├── api/
    │   │   │   ├── routes_chat.py             # Phase 1: Text & simulated voice turn APIs
    │   │   │   ├── routes_voice.py            # Phase 2: Streaming ASR/TTS & WebSocket APIs
    │   │   │   ├── routes_schemes.py          # Auditable rule catalog & inspection APIs
    │   │   │   └── routes_sessions.py         # Session state, reset, and audit log APIs
    │   │   ├── core/
    │   │   │   ├── normalizer.py              # Kannada dialect, unit (Gunte/Acre), & crop mapper
    │   │   │   ├── nlu_extractor.py           # LLM structured slot & intent extraction
    │   │   │   ├── rule_engine.py             # Deterministic symbolic eligibility evaluator
    │   │   │   ├── dialogue_manager.py        # Missing-slot prioritizer & policy planner
    │   │   │   └── response_generator.py      # Spoken-Kannada response generator
    │   │   ├── voice/                         # Phase 2 Voice Adapters
    │   │   │   ├── asr_service.py             # Kannada ASR wrapper (Sarvam / GCP / Azure)
    │   │   │   ├── tts_service.py             # Spoken Kannada TTS wrapper & number verbalizer
    │   │   │   └── vad_barge_in.py            # Audio frame state & interruption handler
    │   │   ├── models/
    │   │   │   ├── farmer_profile.py          # Pydantic schemas for FarmerProfile & Slots
    │   │   │   ├── scheme_models.py           # Pydantic schemas for Rules & Audit Traces
    │   │   │   └── database_models.py         # SQLAlchemy ORM models
    │   │   └── db/
    │   │       ├── session.py                 # Database & Redis connection management
    │   │       └── seed.py                    # Seeds the 5 reference schemes & lexicons
    │   ├── tests/
    │   │   ├── test_normalizer.py             # Unit tests for Gunte/Ekare & dialect crops
    │   │   ├── test_rule_engine.py            # Deterministic tests for all 5 schemes
    │   │   └── test_multi_turn_context.py     # Multi-turn context retention acceptance tests
    │   ├── requirements.txt
    │   └── Dockerfile
    │
    ├── frontend/                              # Next.js (App Router) + Tailwind CSS Frontend
    │   ├── src/
    │   │   ├── app/
    │   │   │   ├── layout.tsx                 # Noto Sans Kannada + Inter font setup
    │   │   │   └── page.tsx                   # Main Krishi Mitra Assistant & Audit Workbench
    │   │   ├── components/
    │   │   │   ├── voice/
    │   │   │   │   ├── VoiceOrb.tsx           # Animated voice state orb (Idle/Listening/Speaking)
    │   │   │   │   └── AudioPlayerBar.tsx     # TTS playback & barge-in controller
    │   │   │   ├── chat/
    │   │   │   │   ├── ConversationStream.tsx # Bilingual/Kannada transcript & turn cards
    │   │   │   │   └── DialectQuickBar.tsx    # One-click regional Kannada sample utterances
    │   │   │   ├── schemes/
    │   │   │   │   ├── SchemeCard.tsx         # Visual eligibility card with audio summary button
    │   │   │   │   └── DocumentChecklist.tsx  # Visual RTC/Aadhaar/FRUITS ID checklist
    │   │   │   └── audit/
    │   │   │       ├── ExtractedSlotsView.tsx # Live view of normalized FarmerProfile slots
    │   │   │       └── RuleTraceDrawer.tsx    # Transparent rule-by-rule verification tree
    │   │   ├── hooks/
    │   │   │   ├── useVoiceSession.ts         # WebRTC mic capture, VAD, & WebSocket stream
    │   │   │   └── useChatSession.ts          # Phase 1 text & Phase 2 hybrid state hook
    │   │   └── lib/
    │   │       └── api.ts                     # Typed API client
    │   ├── package.json
    │   └── Dockerfile
    │
    ├── docker-compose.yml                     # One-command stack (Frontend, Backend, Postgres, Redis)
    └── README.md